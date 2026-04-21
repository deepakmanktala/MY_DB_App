import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Job, JobSearchRequest, JobSearchResponse, Page } from '../models/job.model';

@Injectable({ providedIn: 'root' })
export class JobService {

  private baseUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  startSearch(request: JobSearchRequest): Observable<JobSearchResponse> {
    return this.http.post<JobSearchResponse>(`${this.baseUrl}/jobs/search`, request);
  }

  getJobs(page = 0, size = 20, keyword?: string, region?: string, source?: string): Observable<Page<Job>> {
    let params = new HttpParams().set('page', page).set('size', size);
    if (keyword) params = params.set('keyword', keyword);
    if (region)  params = params.set('region', region);
    if (source)  params = params.set('source', source);
    return this.http.get<Page<Job>>(`${this.baseUrl}/jobs`, { params });
  }

  getRegions(): Observable<string[]> {
    return this.http.get<string[]>(`${this.baseUrl}/jobs/regions`);
  }

  clearJobs(): Observable<any> {
    return this.http.delete(`${this.baseUrl}/jobs`);
  }

  getStats(): Observable<{ totalJobs: number; activeCrawls: number }> {
    return this.http.get<any>(`${this.baseUrl}/jobs/stats`);
  }

  // Connect to SSE progress stream
  streamProgress(crawlId: string): EventSource {
    return new EventSource(`${this.baseUrl}/jobs/search/${crawlId}/progress`);
  }
}
