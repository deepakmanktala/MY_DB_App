package com.deepakmanktala.jobfinder.dto;

import com.deepakmanktala.jobfinder.model.Job;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class JobSearchResponse {

    private List<Job> jobs;
    private int totalFound;
    private int totalDeduped;
    private String crawlStatus;   // "COMPLETED", "IN_PROGRESS", "FAILED"
    private String crawlId;       // UUID to poll async status
    private long durationMs;
}