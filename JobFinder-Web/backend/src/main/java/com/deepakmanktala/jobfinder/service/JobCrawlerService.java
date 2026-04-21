package com.deepakmanktala.jobfinder.service;

import com.deepakmanktala.jobfinder.dto.JobSearchRequest;
import com.deepakmanktala.jobfinder.model.Job;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;

@Service
@RequiredArgsConstructor
@Slf4j
public class JobCrawlerService {

    private final JobPortalConfig portalConfig;
    private final JobStorageService storageService;

    @Value("${crawler.request-delay-ms:500}")
    private int requestDelayMs;

    @Value("${crawler.timeout-ms:15000}")
    private int timeoutMs;

    private static final List<String> USER_AGENTS = List.of(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0"
    );

    /**
     * Runs the full crawl asynchronously. Progress updates streamed via progressCallback.
     */
    @Async
    public CompletableFuture<List<Job>> crawlAsync(JobSearchRequest request,
                                                    Consumer<String> progressCallback) {
        List<Job> allJobs = Collections.synchronizedList(new ArrayList<>());
        List<JobPortalConfig.Portal> portals = portalConfig.getPortalsForRegion(request.getRegion());
        int total = portals.size() * request.getRoles().size();
        AtomicInteger done = new AtomicInteger(0);

        ExecutorService executor = Executors.newFixedThreadPool(
            Math.min(request.getConcurrency(), 10)
        );
        List<Future<?>> futures = new ArrayList<>();

        for (String role : request.getRoles()) {
            for (JobPortalConfig.Portal portal : portals) {
                futures.add(executor.submit(() -> {
                    try {
                        List<Job> jobs = scrapePortal(portal, role, request.getRegion());
                        allJobs.addAll(jobs);
                        int count = done.incrementAndGet();
                        progressCallback.accept(String.format("[%d/%d] %s — %s: %d results",
                            count, total, portal.name(), role, jobs.size()));
                        Thread.sleep(requestDelayMs);
                    } catch (Exception e) {
                        log.warn("Error scraping {} for role {}: {}", portal.name(), role, e.getMessage());
                    }
                }));
            }
        }

        for (Future<?> f : futures) {
            try { f.get(); } catch (Exception ignored) {}
        }
        executor.shutdown();

        List<Job> result = request.isDedup() ? deduplicate(allJobs) : allJobs;
        storageService.saveAll(result);
        progressCallback.accept("DONE:" + result.size());
        return CompletableFuture.completedFuture(result);
    }

    private List<Job> scrapePortal(JobPortalConfig.Portal portal, String role, String region) {
        List<Job> jobs = new ArrayList<>();
        String encodedRole = URLEncoder.encode(role, StandardCharsets.UTF_8);
        String encodedRegion = URLEncoder.encode(region, StandardCharsets.UTF_8);
        String url = portal.searchUrlTemplate()
            .replace("{ROLE}", encodedRole)
            .replace("{REGION}", encodedRegion);

        try {
            String userAgent = USER_AGENTS.get(new Random().nextInt(USER_AGENTS.size()));
            Document doc = Jsoup.connect(url)
                .userAgent(userAgent)
                .timeout(timeoutMs)
                .get();

            // Generic selectors — works for many job board layouts
            Elements cards = doc.select("div[class*=job], li[class*=job], article[class*=job]");
            for (Element card : cards) {
                String title = extractText(card, "h2,h3,h4,a[class*=title],span[class*=title]");
                String company = extractText(card, "span[class*=company],div[class*=company],a[class*=company]");
                String location = extractText(card, "span[class*=location],div[class*=location]");
                String jobUrl = extractHref(card, url);

                if (title != null && !title.isBlank()) {
                    jobs.add(Job.builder()
                        .title(title.trim())
                        .company(company)
                        .location(location)
                        .jobUrl(jobUrl)
                        .source(portal.name())
                        .region(region)
                        .roleMatched(role)
                        .crawledAt(LocalDateTime.now())
                        .build());
                }
            }
        } catch (Exception e) {
            log.debug("Scrape failed for {} ({}): {}", portal.name(), url, e.getMessage());
        }
        return jobs;
    }

    private String extractText(Element root, String selector) {
        Element el = root.selectFirst(selector);
        return el != null ? el.text() : null;
    }

    private String extractHref(Element card, String baseUrl) {
        Element a = card.selectFirst("a[href]");
        if (a == null) return baseUrl;
        String href = a.attr("abs:href");
        return href.isBlank() ? baseUrl : href;
    }

    private List<Job> deduplicate(List<Job> jobs) {
        Set<String> seen = new HashSet<>();
        List<Job> deduped = new ArrayList<>();
        for (Job job : jobs) {
            String key = (job.getTitle() + "|" + job.getCompany()).toLowerCase();
            if (seen.add(key)) deduped.add(job);
        }
        log.info("Dedup: {} → {}", jobs.size(), deduped.size());
        return deduped;
    }
}
