package com.deepakmanktala.jobfinder.controller;

import com.deepakmanktala.jobfinder.model.Job;
import com.deepakmanktala.jobfinder.service.JobCrawlerService;
import com.deepakmanktala.jobfinder.service.JobStorageService;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/jobs")
@RequiredArgsConstructor
@CrossOrigin(origins = {"http://10.0.2.2:8081", "http://localhost:8081"})
public class JobController {

    private final JobCrawlerService crawlerService;
    private final JobStorageService storageService;

    /**
     * POST /api/v1/jobs/search
     * Body: { "roles": ["TPM"], "region": "India", "dateRange": "Last 1 week" }
     * Kicks off a synchronous crawl and returns results (suitable for mobile).
     */
    @PostMapping("/search")
    public ResponseEntity<Map<String, Object>> search(@RequestBody Map<String, Object> body) {
        @SuppressWarnings("unchecked")
        List<String> roles = (List<String>) body.getOrDefault("roles", List.of("Software Engineer"));
        String region = (String) body.getOrDefault("region", "Worldwide (all portals)");
        String dateRange = (String) body.getOrDefault("dateRange", "Last 1 week");

        List<Job> jobs = crawlerService.crawlSync(roles, region, dateRange, 3, true);
        return ResponseEntity.ok(Map.of(
            "jobs", jobs,
            "total", jobs.size(),
            "status", "COMPLETED"
        ));
    }

    /**
     * GET /api/v1/jobs?page=0&size=20&keyword=TPM&region=India
     */
    @GetMapping
    public ResponseEntity<Page<Job>> getJobs(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String region,
            @RequestParam(required = false) String source) {

        PageRequest pageable = PageRequest.of(page, size, Sort.by("crawledAt").descending());
        return ResponseEntity.ok(storageService.search(keyword, region, source, pageable));
    }

    /**
     * GET /api/v1/jobs/{id}
     */
    @GetMapping("/{id}")
    public ResponseEntity<Job> getJob(@PathVariable Long id) {
        return storageService.findById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    /**
     * GET /api/v1/jobs/regions
     */
    @GetMapping("/regions")
    public ResponseEntity<List<String>> getRegions() {
        return ResponseEntity.ok(List.of(
            "Worldwide (all portals)", "USA", "India", "UK", "Canada", "Singapore"
        ));
    }

    /**
     * GET /api/v1/jobs/stats
     */
    @GetMapping("/stats")
    public ResponseEntity<Map<String, Object>> stats() {
        return ResponseEntity.ok(Map.of("totalJobs", storageService.count()));
    }
}
