package com.deepakmanktala.jobfinderapp.ui.results

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.deepakmanktala.jobfinderapp.data.model.Job
import com.deepakmanktala.jobfinderapp.databinding.ItemJobBinding

class JobAdapter(private val onJobClick: (Job) -> Unit) :
    ListAdapter<Job, JobAdapter.JobViewHolder>(JobDiffCallback()) {

    inner class JobViewHolder(private val binding: ItemJobBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(job: Job) {
            binding.tvTitle.text = job.title
            binding.tvCompany.text = job.company ?: "Unknown Company"
            binding.tvLocation.text = job.location ?: "Location not specified"
            binding.tvSource.text = job.source ?: ""
            binding.tvRole.text = "Role: ${job.roleMatched ?: ""}"
            binding.tvSalary.text = job.salary ?: ""
            binding.root.setOnClickListener { onJobClick(job) }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): JobViewHolder {
        val binding = ItemJobBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return JobViewHolder(binding)
    }

    override fun onBindViewHolder(holder: JobViewHolder, position: Int) {
        holder.bind(getItem(position))
    }
}

class JobDiffCallback : DiffUtil.ItemCallback<Job>() {
    override fun areItemsTheSame(oldItem: Job, newItem: Job) = oldItem.id == newItem.id
    override fun areContentsTheSame(oldItem: Job, newItem: Job) = oldItem == newItem
}
