package com.deepakmanktala.jobfinder.controller;

import com.deepakmanktala.jobfinder.dto.JobSearchRequest;
import com.deepakmanktala.jobfinder.dto.JobSearchResponse;
import com.deepakmanktala.jobfinder.model.Job;
import com.deepakmanktala.jobfinder.service.JobCrawlerService;
import com.deepakmanktala.jobfinder.service.JobPortalConfig;
import com.deepakmanktala.jobfinder.service.JobStorageService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@RestController
@RequestMapping("/api/jobs")
@RequiredArgsConstructor
@Slf4j
public class JobController {

    private final JobCrawlerService crawlerService;
    private final JobStorageService storageService;
    private final JobPortalConfig portalConfig;

    // Stores live SSE emitters keyed by crawlId
    private final Map<String, SseEmitter> emitters = new ConcurrentHashMap<>();

    /**
     * POST /api/jobs/search
     * Starts an async crawl and returns a crawlId. Frontend subscribes to
     * GET /api/jobs/search/{crawlId}/progress for live SSE updates.
     */
    @PostMapping("/search")
    public ResponseEntity<JobSearchResponse> startSearch(@Valid @RequestBody JobSearchRequest request) {
        String crawlId = UUID.randomUUID().toString();
        SseEmitter emitter = new SseEmitter(300_000L); // 5-min timeout
        emitters.put(crawlId, emitter);

        long start = System.currentTimeMillis();
        crawlerService.crawlAsync(request, message -> {
            SseEmitter e = emitters.get(crawlId);
            if (e != null) {
                try {
                    e.send(SseEmitter.event().name("progress").data(message));
                    if (message.startsWith("DONE:")) {
                        e.complete();
                        emitters.remove(crawlId);
                    }
                } catch (IOException ex) {
                    emitters.remove(crawlId);
                }
            }
        });

        return ResponseEntity.accepted().body(
            JobSearchResponse.builder()
                .crawlId(crawlId)
                .crawlStatus("IN_PROGRESS")
                .durationMs(System.currentTimeMillis() - start)
                .build()
        );
    }

    /**
     * GET /api/jobs/search/{crawlId}/progress
     * Server-Sent Events stream for live crawl progress.
     */
    @GetMapping(value = "/search/{crawlId}/progress", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter streamProgress(@PathVariable String crawlId) {
        return emitters.getOrDefault(crawlId, new SseEmitter(0L));
    }

    /**
     * GET /api/jobs?page=0&size=20&keyword=TPM&region=India&source=LinkedIn
     * Returns paginated, filterable job results.
     */
    @GetMapping
    public ResponseEntity<Page<Job>> getJobs(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String region,
            @RequestParam(required = false) String source) {

        PageRequest pageable = PageRequest.of(page, size, Sort.by("crawledAt").descending());
        Page<Job> jobs = storageService.search(keyword, region, source, pageable);
        return ResponseEntity.ok(jobs);
    }

    /**
     * GET /api/jobs/regions
     * Returns list of supported regions for the search form dropdown.
     */
    @GetMapping("/regions")
    public ResponseEntity<List<String>> getRegions() {
        return ResponseEntity.ok(portalConfig.getAllRegions());
    }

    /**
     * DELETE /api/jobs
     * Clears all cached job results.
     */
    @DeleteMapping
    public ResponseEntity<Map<String, String>> clearJobs() {
        storageService.deleteAll();
        return ResponseEntity.ok(Map.of("message", "All jobs cleared"));
    }

    /**
     * GET /api/jobs/stats
     */
    @GetMapping("/stats")
    public ResponseEntity<Map<String, Object>> stats() {
        return ResponseEntity.ok(Map.of(
            "totalJobs", storageService.count(),
            "activeCrawls", emitters.size()
        ));
    }
}
