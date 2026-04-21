export interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  description: string;
  salary: string;
  jobUrl: string;
  source: string;
  region: string;
  datePosted: string;
  crawledAt: string;
  roleMatched: string;
}

export interface JobSearchRequest {
  roles: string[];
  region: string;
  dateRange: string;
  concurrency: number;
  dedup: boolean;
}

export interface JobSearchResponse {
  crawlId: string;
  crawlStatus: 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
  totalFound: number;
  totalDeduped: number;
  durationMs: number;
}

export interface Page<T> {
  content: T[];
  totalElements: number;
  totalPages: number;
  size: number;
  number: number;
}