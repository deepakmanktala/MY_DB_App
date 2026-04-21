import { Component, OnInit } from '@angular/core';
import { JobService } from '../../services/job.service';
import { Job } from '../../models/job.model';

@Component({
  selector: 'app-job-list',
  templateUrl: './job-list.component.html',
  styleUrls: ['./job-list.component.css']
})
export class JobListComponent implements OnInit {

  jobs: Job[] = [];
  totalElements = 0;
  currentPage = 0;
  pageSize = 20;
  keyword = '';
  region = '';
  source = '';
  loading = false;

  constructor(private jobService: JobService) {}

  ngOnInit(): void {
    this.loadJobs();
  }

  loadJobs(): void {
    this.loading = true;
    this.jobService.getJobs(
      this.currentPage, this.pageSize,
      this.keyword || undefined,
      this.region || undefined,
      this.source || undefined
    ).subscribe(page => {
      this.jobs = page.content;
      this.totalElements = page.totalElements;
      this.loading = false;
    });
  }

  onSearch(): void {
    this.currentPage = 0;
    this.loadJobs();
  }

  onPageChange(page: number): void {
    this.currentPage = page;
    this.loadJobs();
  }

  get totalPages(): number {
    return Math.ceil(this.totalElements / this.pageSize);
  }
}
