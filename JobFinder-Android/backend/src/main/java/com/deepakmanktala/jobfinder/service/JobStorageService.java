package com.deepakmanktala.jobfinder.service;

import com.deepakmanktala.jobfinder.model.Job;
import com.deepakmanktala.jobfinder.repository.JobRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class JobStorageService {

    private final JobRepository repo;

    public List<Job> saveAll(List<Job> jobs) { return repo.saveAll(jobs); }
    public Page<Job> findAll(Pageable pageable) { return repo.findAll(pageable); }
    public Optional<Job> findById(Long id) { return repo.findById(id); }
    public Page<Job> search(String keyword, String region, String source, Pageable pageable) {
        return repo.searchJobs(keyword, region, source, pageable);
    }
    public long count() { return repo.count(); }
}
