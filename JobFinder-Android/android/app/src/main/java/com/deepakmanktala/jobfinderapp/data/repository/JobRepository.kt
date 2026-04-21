package com.deepakmanktala.jobfinderapp.data.repository

import com.deepakmanktala.jobfinderapp.data.api.RetrofitClient
import com.deepakmanktala.jobfinderapp.data.model.Job
import com.deepakmanktala.jobfinderapp.data.model.JobSearchRequest
import com.deepakmanktala.jobfinderapp.data.model.PagedJobs

sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val message: String) : Result<Nothing>()
    object Loading : Result<Nothing>()
}

class JobRepository {

    private val api = RetrofitClient.instance

    suspend fun searchJobs(request: JobSearchRequest): Result<List<Job>> {
        return try {
            val response = api.searchJobs(request)
            if (response.isSuccessful) {
                Result.Success(response.body()?.jobs ?: emptyList())
            } else {
                Result.Error("Server error: ${response.code()}")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error")
        }
    }

    suspend fun getJobs(page: Int = 0, size: Int = 20,
                        keyword: String? = null, region: String? = null): Result<PagedJobs> {
        return try {
            val response = api.getJobs(page, size, keyword, region)
            if (response.isSuccessful) {
                Result.Success(response.body()!!)
            } else {
                Result.Error("Server error: ${response.code()}")
            }
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error")
        }
    }

    suspend fun getRegions(): Result<List<String>> {
        return try {
            val response = api.getRegions()
            if (response.isSuccessful) Result.Success(response.body()!!)
            else Result.Error("Server error: ${response.code()}")
        } catch (e: Exception) {
            Result.Error(e.message ?: "Network error")
        }
    }
}
