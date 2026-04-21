package com.deepakmanktala.jobfinder.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;

import java.time.LocalDateTime;

@Entity
@Table(name = "jobs")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Job {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String title;

    private String company;
    private String location;

    @Column(length = 2000)
    private String description;

    private String salary;

    @Column(name = "job_url", length = 1000)
    private String jobUrl;

    private String source;
    private String region;
    private String datePosted;

    @Column(name = "crawled_at")
    private LocalDateTime crawledAt;

    @Column(name = "role_matched")
    private String roleMatched;
}
