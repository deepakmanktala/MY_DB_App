package com.deepakmanktala.jobfinder.service;

import com.deepakmanktala.jobfinder.model.Job;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.*;

@Service
@RequiredArgsConstructor
@Slf4j
public class JobCrawlerService {

    private final JobStorageService storageService;

    @Value("${crawler.request-delay-ms:500}")
    private int delayMs;

    @Value("${crawler.timeout-ms:15000}")
    private int timeoutMs;

    private static final Map<String, List<String[]>> PORTALS = Map.of(
        "global", List.of(
            new String[]{"LinkedIn", "https://www.linkedin.com/jobs/search/?keywords={ROLE}&location={REGION}"},
            new String[]{"Indeed",   "https://www.indeed.com/jobs?q={ROLE}&l={REGION}"},
            new String[]{"Glassdoor","https://www.glassdoor.com/Job/jobs.htm?sc.keyword={ROLE}"}
        ),
        "India", List.of(
            new String[]{"Naukri",    "https://www.naukri.com/{ROLE}-jobs-in-india"},
            new String[]{"Shine",     "https://www.shine.com/job-search/{ROLE}-jobs"},
            new String[]{"TimesJobs", "https://www.timesjobs.com/candidate/job-search.html?txtKeywords={ROLE}"}
        ),
        "USA", List.of(
            new String[]{"Dice",      "https://www.dice.com/jobs?q={ROLE}&countryCode=US"},
            new String[]{"USAJobs",   "https://www.usajobs.gov/Search/Results?k={ROLE}"}
        )
    );

    public List<Job> crawlSync(List<String> roles, String region, String dateRange,
                               int concurrency, boolean dedup) {
        List<Job> all = Collections.synchronizedList(new ArrayList<>());
        List<String[]> portals = new ArrayList<>(PORTALS.getOrDefault("global", List.of()));
        if (PORTALS.containsKey(region)) portals.addAll(PORTALS.get(region));

        ExecutorService exec = Executors.newFixedThreadPool(Math.min(concurrency, 8));
        List<Future<?>> futures = new ArrayList<>();

        for (String role : roles) {
            for (String[] portal : portals) {
                futures.add(exec.submit(() -> {
                    all.addAll(scrape(portal[0], portal[1], role, region));
                    try { Thread.sleep(delayMs); } catch (InterruptedException ignored) {}
                }));
            }
        }

        futures.forEach(f -> { try { f.get(30, TimeUnit.SECONDS); } catch (Exception ignored) {} });
        exec.shutdown();

        List<Job> result = dedup ? deduplicate(all) : all;
        storageService.saveAll(result);
        return result;
    }

    private List<Job> scrape(String portalName, String urlTemplate, String role, String region) {
        List<Job> jobs = new ArrayList<>();
        String url = urlTemplate
            .replace("{ROLE}", URLEncoder.encode(role, StandardCharsets.UTF_8))
            .replace("{REGION}", URLEncoder.encode(region, StandardCharsets.UTF_8));
        try {
            Document doc = Jsoup.connect(url)
                .userAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                .timeout(timeoutMs).get();
            Elements cards = doc.select("div[class*=job],li[class*=job],article[class*=job]");
            for (Element c : cards) {
                String title = text(c, "h2,h3,h4,a[class*=title],span[class*=title]");
                if (title != null && !title.isBlank()) {
                    jobs.add(Job.builder()
                        .title(title.trim())
                        .company(text(c, "span[class*=company],div[class*=company]"))
                        .location(text(c, "span[class*=location],div[class*=location]"))
                        .jobUrl(href(c, url))
                        .source(portalName)
                        .region(region)
                        .roleMatched(role)
                        .crawledAt(LocalDateTime.now())
                        .build());
                }
            }
        } catch (Exception e) {
            log.debug("Scrape failed {}: {}", portalName, e.getMessage());
        }
        return jobs;
    }

    private String text(Element root, String sel) {
        Element el = root.selectFirst(sel);
        return el != null ? el.text() : null;
    }

    private String href(Element card, String fallback) {
        Element a = card.selectFirst("a[href]");
        if (a == null) return fallback;
        String h = a.attr("abs:href");
        return h.isBlank() ? fallback : h;
    }

    private List<Job> deduplicate(List<Job> jobs) {
        Set<String> seen = new HashSet<>();
        List<Job> out = new ArrayList<>();
        for (Job j : jobs) {
            if (seen.add((j.getTitle() + "|" + j.getCompany()).toLowerCase())) out.add(j);
        }
        return out;
    }
}
