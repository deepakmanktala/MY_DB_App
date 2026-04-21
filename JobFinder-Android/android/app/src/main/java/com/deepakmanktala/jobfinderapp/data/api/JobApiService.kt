package com.deepakmanktala.jobfinderapp.data.api

import com.deepakmanktala.jobfinderapp.data.model.JobSearchRequest
import com.deepakmanktala.jobfinderapp.data.model.JobSearchResult
import com.deepakmanktala.jobfinderapp.data.model.PagedJobs
import retrofit2.Response
import retrofit2.http.*

interface JobApiService {

    @POST("jobs/search")
    suspend fun searchJobs(@Body request: JobSearchRequest): Response<JobSearchResult>

    @GET("jobs")
    suspend fun getJobs(
        @Query("page") page: Int = 0,
        @Query("size") size: Int = 20,
        @Query("keyword") keyword: String? = null,
        @Query("region") region: String? = null,
        @Query("source") source: String? = null
    ): Response<PagedJobs>

    @GET("jobs/regions")
    suspend fun getRegions(): Response<List<String>>

    @GET("jobs/stats")
    suspend fun getStats(): Response<Map<String, Any>>
}
