package com.deepakmanktala.jobfinderapp.ui.search

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ArrayAdapter
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.navigation.fragment.findNavController
import com.deepakmanktala.jobfinderapp.R
import com.deepakmanktala.jobfinderapp.data.repository.Result
import com.deepakmanktala.jobfinderapp.databinding.FragmentSearchBinding
import com.deepakmanktala.jobfinderapp.viewmodel.JobViewModel

class SearchFragment : Fragment() {

    private var _binding: FragmentSearchBinding? = null
    private val binding get() = _binding!!
    private val viewModel: JobViewModel by activityViewModels()

    private val suggestedRoles = listOf(
        "TPM", "Technical Program Manager", "AI Engineer",
        "Payments Engineer", "EMV Engineer", "Engineering Manager",
        "Python Developer", "Micro Services", "QA Engineer"
    )

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        _binding = FragmentSearchBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        viewModel.loadRegions()

        viewModel.regions.observe(viewLifecycleOwner) { regions ->
            val adapter = ArrayAdapter(requireContext(), android.R.layout.simple_spinner_item, regions)
            adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
            binding.spinnerRegion.adapter = adapter
        }

        // Add chip buttons for suggested roles
        suggestedRoles.forEach { role ->
            val chip = com.google.android.material.chip.Chip(requireContext()).apply {
                text = role
                isClickable = true
                setOnClickListener { appendRole(role) }
            }
            binding.chipGroupRoles.addView(chip)
        }

        binding.btnSearch.setOnClickListener {
            val rolesText = binding.editTextRoles.text.toString()
            val roles = rolesText.split("\n").map { it.trim() }.filter { it.isNotEmpty() }
            if (roles.isEmpty()) {
                Toast.makeText(requireContext(), "Please enter at least one role", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            val region = binding.spinnerRegion.selectedItem?.toString() ?: "Worldwide (all portals)"
            val dateRange = binding.spinnerDateRange.selectedItem?.toString() ?: "Last 1 week"
            viewModel.searchJobs(roles, region, dateRange)
        }

        viewModel.isSearching.observe(viewLifecycleOwner) { searching ->
            binding.btnSearch.isEnabled = !searching
            binding.progressBar.visibility = if (searching) View.VISIBLE else View.GONE
            binding.btnSearch.text = if (searching) "Searching..." else "Find Jobs"
        }

        viewModel.searchResults.observe(viewLifecycleOwner) { result ->
            when (result) {
                is Result.Success -> {
                    Toast.makeText(requireContext(), "${result.data.size} jobs found!", Toast.LENGTH_SHORT).show()
                    findNavController().navigate(R.id.action_search_to_results)
                }
                is Result.Error -> {
                    Toast.makeText(requireContext(), "Error: ${result.message}", Toast.LENGTH_LONG).show()
                }
                is Result.Loading -> { /* handled by isSearching */ }
            }
        }
    }

    private fun appendRole(role: String) {
        val current = binding.editTextRoles.text.toString().trim()
        val roles = current.split("\n").map { it.trim() }.filter { it.isNotEmpty() }
        if (!roles.contains(role)) {
            binding.editTextRoles.setText(if (current.isEmpty()) role else "$current\n$role")
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}
