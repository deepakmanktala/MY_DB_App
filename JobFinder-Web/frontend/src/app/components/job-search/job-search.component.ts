import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { JobService } from '../../services/job.service';
import { JobSearchRequest } from '../../models/job.model';

@Component({
  selector: 'app-job-search',
  templateUrl: './job-search.component.html',
  styleUrls: ['./job-search.component.css']
})
export class JobSearchComponent implements OnInit {

  @Output() crawlStarted = new EventEmitter<string>();

  searchForm!: FormGroup;
  regions: string[] = [];
  rolesInput = '';
  progressLogs: string[] = [];
  isSearching = false;

  dateRanges = ['Last 1 day', 'Last 3 days', 'Last 1 week', 'Last 2 weeks', 'Last 30 days'];

  suggestedRoles = [
    'TPM', 'Technical Program Manager', 'AI Engineer',
    'Payments Engineer', 'EMV Engineer', 'Engineering Manager',
    'Python Developer', 'Micro Services'
  ];

  constructor(private fb: FormBuilder, private jobService: JobService) {}

  ngOnInit(): void {
    this.searchForm = this.fb.group({
      region: ['Worldwide (all portals)', Validators.required],
      dateRange: ['Last 1 week', Validators.required],
      concurrency: [5, [Validators.min(1), Validators.max(10)]],
      dedup: [true]
    });
    this.jobService.getRegions().subscribe(r => this.regions = r);
  }

  addRole(role: string): void {
    const existing = this.rolesInput.split('\n').map(r => r.trim()).filter(Boolean);
    if (!existing.includes(role)) {
      this.rolesInput = [...existing, role].join('\n');
    }
  }

  getRolesList(): string[] {
    return this.rolesInput.split('\n').map(r => r.trim()).filter(Boolean);
  }

  onSearch(): void {
    const roles = this.getRolesList();
    if (!roles.length) { alert('Please enter at least one role.'); return; }

    const request: JobSearchRequest = {
      roles,
      ...this.searchForm.value
    };

    this.isSearching = true;
    this.progressLogs = [];

    this.jobService.startSearch(request).subscribe(response => {
      const es = this.jobService.streamProgress(response.crawlId);
      es.addEventListener('progress', (event: MessageEvent) => {
        this.progressLogs.unshift(event.data);
        if (event.data.startsWith('DONE:')) {
          this.isSearching = false;
          es.close();
          this.crawlStarted.emit('done');
        }
      });
      es.onerror = () => {
        this.isSearching = false;
        es.close();
      };
    });
  }
}