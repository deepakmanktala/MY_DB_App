package com.deepakmanktala.jobfinder.model;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Entity
@Table(name = "search_preferences")
@Data
@NoArgsConstructor
public class SearchPreferences {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;  // e.g. "default"

    @ElementCollection
    @CollectionTable(name = "pref_roles", joinColumns = @JoinColumn(name = "pref_id"))
    @Column(name = "role")
    private List<String> roles;

    private String region;

    private String dateRange;  // "Last 1 week", "Last 2 weeks", "Last 30 days"

    private int concurrency;

    private boolean dedup;
}