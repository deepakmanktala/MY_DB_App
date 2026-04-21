package com.deepakmanktala.jobfinder.service;

import com.deepakmanktala.jobfinder.model.Job;
import com.deepakmanktala.jobfinder.repository.JobRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class JobStorageService {

    private final JobRepository jobRepository;

    public List<Job> saveAll(List<Job> jobs) {
        return jobRepository.saveAll(jobs);
    }

    public Page<Job> findAll(Pageable pageable) {
        return jobRepository.findAll(pageable);
    }

    public Page<Job> search(String keyword, String region, String source, Pageable pageable) {
        return jobRepository.searchJobs(keyword, region, source, pageable);
    }

    public void deleteAll() {
        jobRepository.deleteAll();
    }

    public long count() {
        return jobRepository.count();
    }
}
