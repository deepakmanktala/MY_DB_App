package com.deepakmanktala.jobfinderapp.ui.results

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.recyclerview.widget.LinearLayoutManager
import com.deepakmanktala.jobfinderapp.data.model.Job
import com.deepakmanktala.jobfinderapp.data.repository.Result
import com.deepakmanktala.jobfinderapp.databinding.FragmentResultsBinding
import com.deepakmanktala.jobfinderapp.viewmodel.JobViewModel

class ResultsFragment : Fragment() {

    private var _binding: FragmentResultsBinding? = null
    private val binding get() = _binding!!
    private val viewModel: JobViewModel by activityViewModels()
    private lateinit var adapter: JobAdapter

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentResultsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        adapter = JobAdapter { job ->
            job.jobUrl?.let { url ->
                startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
            }
        }

        binding.recyclerView.layoutManager = LinearLayoutManager(requireContext())
        binding.recyclerView.adapter = adapter

        viewModel.searchResults.observe(viewLifecycleOwner) { result ->
            when (result) {
                is Result.Success -> {
                    binding.tvJobCount.text = "${result.data.size} jobs found"
                    adapter.submitList(result.data)
                }
                is Result.Error -> binding.tvJobCount.text = "Error: ${result.message}"
                is Result.Loading -> binding.tvJobCount.text = "Loading..."
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
