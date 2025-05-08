
import type { LucideIcon } from 'lucide-react';

// Corresponds to backend's DownloadedFileSchema
export interface DownloadedFileEntry {
  id: string; // uuid.UUID
  source_url: string; // HttpUrl
  file_url: string; // HttpUrl
  file_type: string;
  date_found: string; // datetime (ISO string)
  keywords_found: string[];
  crawl_job_id: string; // uuid.UUID
  downloaded_at: string; // datetime (ISO string)
  local_path?: string | null;
  file_size_bytes?: number | null;
  checksum_md5?: string | null;
}

// Corresponds to backend's CrawlSettingsSchema (used as part of CrawlJob)
export interface CrawlSettings {
  keywords: string[];
  file_extensions: string[];
  seed_urls: string[]; // HttpUrl strings
  search_dorks: string[];
  crawl_depth: number;
  respect_robots_txt: boolean;
  request_delay_seconds: number;
  use_search_engines: boolean;
  max_results_per_dork?: number | null;
  max_concurrent_requests_per_domain?: number | null;
}

// Corresponds to backend's CrawlJobSchema
export interface CrawlJob {
  id: string; // uuid.UUID
  name?: string | null;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'stopping' | 'completed_empty';
  created_at: string; // datetime (ISO string)
  updated_at: string; // datetime (ISO string)
  settings: CrawlSettings; 
  results_summary?: { // Added to match backend schema
    files_found?: number;
    // other summary fields can be added here
  } | null;
}


export interface NavItem {
  title: string;
  href: string;
  icon: LucideIcon;
  label?: string;
  disabled?: boolean;
}

// This is the frontend form data structure
export interface SettingsData {
  keywords: string; // Comma/newline separated
  fileExtensions: string; // Comma/newline separated
  seedUrls: string; // Newline separated
  searchDorks: string; // Newline separated
  crawlDepth: number;
  respectRobotsTxt: boolean;
  requestDelay: number; // in seconds
}
```