package com.deepakmanktala.jobfinderapp.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.deepakmanktala.jobfinderapp.data.model.Job
import com.deepakmanktala.jobfinderapp.data.model.JobSearchRequest
import com.deepakmanktala.jobfinderapp.data.model.PagedJobs
import com.deepakmanktala.jobfinderapp.data.repository.JobRepository
import com.deepakmanktala.jobfinderapp.data.repository.Result
import kotlinx.coroutines.launch

class JobViewModel : ViewModel() {

    private val repository = JobRepository()

    private val _searchResults = MutableLiveData<Result<List<Job>>>()
    val searchResults: LiveData<Result<List<Job>>> = _searchResults

    private val _pagedJobs = MutableLiveData<Result<PagedJobs>>()
    val pagedJobs: LiveData<Result<PagedJobs>> = _pagedJobs

    private val _regions = MutableLiveData<List<String>>()
    val regions: LiveData<List<String>> = _regions

    private val _isSearching = MutableLiveData(false)
    val isSearching: LiveData<Boolean> = _isSearching

    fun loadRegions() {
        viewModelScope.launch {
            when (val r = repository.getRegions()) {
                is Result.Success -> _regions.value = r.data
                else -> _regions.value = listOf("Worldwide (all portals)", "USA", "India", "UK")
            }
        }
    }

    fun searchJobs(roles: List<String>, region: String, dateRange: String) {
        if (roles.isEmpty()) return
        _isSearching.value = true
        _searchResults.value = Result.Loading
        viewModelScope.launch {
            val result = repository.searchJobs(
                JobSearchRequest(roles = roles, region = region, dateRange = dateRange)
            )
            _searchResults.value = result
            _isSearching.value = false
        }
    }

    fun loadJobs(page: Int = 0, keyword: String? = null, region: String? = null) {
        viewModelScope.launch {
            _pagedJobs.value = repository.getJobs(page, keyword = keyword, region = region)
        }
    }
}
