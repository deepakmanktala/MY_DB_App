package com.deepakmanktala.jobfinderapp.data.model

import com.google.gson.annotations.SerializedName

data class Job(
    val id: Long = 0,
    val title: String = "",
    val company: String? = null,
    val location: String? = null,
    val description: String? = null,
    val salary: String? = null,
    @SerializedName("jobUrl") val jobUrl: String? = null,
    val source: String? = null,
    val region: String? = null,
    @SerializedName("datePosted") val datePosted: String? = null,
    @SerializedName("crawledAt") val crawledAt: String? = null,
    @SerializedName("roleMatched") val roleMatched: String? = null
)

data class JobSearchRequest(
    val roles: List<String>,
    val region: String = "Worldwide (all portals)",
    val dateRange: String = "Last 1 week",
    val concurrency: Int = 3,
    val dedup: Boolean = true
)

data class JobSearchResult(
    val jobs: List<Job>,
    val total: Int,
    val status: String
)

data class PagedJobs(
    val content: List<Job>,
    val totalElements: Int,
    val totalPages: Int,
    val size: Int,
    val number: Int
)
