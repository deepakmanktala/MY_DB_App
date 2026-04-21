package com.deepakmanktala.jobfinder.dto;

import jakarta.validation.constraints.NotEmpty;
import lombok.Data;

import java.util.List;

@Data
public class JobSearchRequest {

    @NotEmpty(message = "At least one role is required")
    private List<String> roles;

    private String region = "Worldwide (all portals)";

    private String dateRange = "Last 1 week";

    private int concurrency = 5;

    private boolean dedup = true;
}