package com.deepakmanktala.jobfinder.repository;

import com.deepakmanktala.jobfinder.model.Job;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface JobRepository extends JpaRepository<Job, Long> {

    @Query("""
        SELECT j FROM Job j
        WHERE (:keyword IS NULL OR LOWER(j.title) LIKE LOWER(CONCAT('%', :keyword, '%')))
          AND (:region IS NULL OR LOWER(j.region) LIKE LOWER(CONCAT('%', :region, '%')))
          AND (:source IS NULL OR LOWER(j.source) LIKE LOWER(CONCAT('%', :source, '%')))
        """)
    Page<Job> searchJobs(@Param("keyword") String keyword,
                         @Param("region") String region,
                         @Param("source") String source,
                         Pageable pageable);
}
