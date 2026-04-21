package com.deepakmanktala.jobfinder.service;

import org.springframework.stereotype.Component;

import java.util.*;

/**
 * Java equivalent of job_portals.py — defines all portal search URL templates.
 * {ROLE} is replaced with URL-encoded role; {REGION} with location filter.
 */
@Component
public class JobPortalConfig {

    public record Portal(String name, String region, String searchUrlTemplate) {}

    private static final List<Portal> PORTALS = List.of(
        // Global portals
        new Portal("LinkedIn",       "global", "https://www.linkedin.com/jobs/search/?keywords={ROLE}&location={REGION}&f_TPR=r604800"),
        new Portal("Indeed",         "global", "https://www.indeed.com/jobs?q={ROLE}&l={REGION}&fromage=7"),
        new Portal("Glassdoor",      "global", "https://www.glassdoor.com/Job/jobs.htm?sc.keyword={ROLE}&locT=N&jobType=all"),
        new Portal("Monster",        "global", "https://www.monster.com/jobs/search?q={ROLE}&where={REGION}"),
        new Portal("ZipRecruiter",   "global", "https://www.ziprecruiter.com/Jobs/{ROLE}?location={REGION}"),
        new Portal("SimplyHired",    "global", "https://www.simplyhired.com/search?q={ROLE}&l={REGION}"),
        new Portal("CareerBuilder",  "global", "https://www.careerbuilder.com/jobs?keywords={ROLE}&location={REGION}"),
        new Portal("Jooble",         "global", "https://jooble.org/jobs-{ROLE}/{REGION}"),
        new Portal("Adzuna",         "global", "https://www.adzuna.com/search?q={ROLE}&w={REGION}"),

        // USA portals
        new Portal("USAJobs",        "USA",    "https://www.usajobs.gov/Search/Results?k={ROLE}&l={REGION}"),
        new Portal("Dice",           "USA",    "https://www.dice.com/jobs?q={ROLE}&countryCode=US&radius=30"),
        new Portal("Snagajob",       "USA",    "https://www.snagajob.com/jobs?keyword={ROLE}&location={REGION}"),

        // India portals
        new Portal("Naukri",         "India",  "https://www.naukri.com/{ROLE}-jobs-in-india"),
        new Portal("LinkedIn India", "India",  "https://www.linkedin.com/jobs/search/?keywords={ROLE}&location=India&f_TPR=r604800"),
        new Portal("Shine",          "India",  "https://www.shine.com/job-search/{ROLE}-jobs"),
        new Portal("TimesJobs",      "India",  "https://www.timesjobs.com/candidate/job-search.html?searchType=personalizedSearch&from=submit&txtKeywords={ROLE}"),
        new Portal("Freshersworld",  "India",  "https://www.freshersworld.com/jobs/jobsearch/{ROLE}-jobs-in-india"),

        // UK portals
        new Portal("Reed",           "UK",     "https://www.reed.co.uk/jobs/{ROLE}-jobs"),
        new Portal("Totaljobs",      "UK",     "https://www.totaljobs.com/jobs/{ROLE}"),
        new Portal("CWJobs",         "UK",     "https://www.cwjobs.co.uk/jobs/{ROLE}"),

        // Canada portals
        new Portal("Workopolis",     "Canada", "https://www.workopolis.com/jobsearch/find-jobs?ak={ROLE}"),
        new Portal("Job Bank Canada","Canada", "https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring={ROLE}"),

        // Singapore portals
        new Portal("JobStreet SG",   "Singapore", "https://www.jobstreet.com.sg/en/job-search/{ROLE}-jobs/"),
        new Portal("MyCareersFuture","Singapore", "https://www.mycareersfuture.gov.sg/search?search={ROLE}&sortBy=new_posting_date")
    );

    public static final Set<String> REGION_KEYS = Set.of(
        "Worldwide (all portals)", "USA", "India", "UK", "Canada", "Singapore"
    );

    public List<Portal> getPortalsForRegion(String region) {
        if ("Worldwide (all portals)".equalsIgnoreCase(region)) {
            return PORTALS;
        }
        return PORTALS.stream()
            .filter(p -> "global".equalsIgnoreCase(p.region()) || region.equalsIgnoreCase(p.region()))
            .toList();
    }

    public List<String> getAllRegions() {
        return new ArrayList<>(REGION_KEYS);
    }
}