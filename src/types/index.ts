
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
  // Removed status, as it's not in backend's DownloadedFileSchema
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
  status: 'pending' | 'running' | 'completed' | 'failed' | 'completed_empty';
  created_at: string; // datetime (ISO string)
  updated_at: string; // datetime (ISO string)
  // The settings from backend are flattened into CrawlJob model, but for payload, it's nested.
  // For display, we might receive the full settings object or individual fields.
  // The backend's models.CrawlJob stores settings as individual columns.
  // The schemas.CrawlJobSchema reconstructs the CrawlSettingsSchema for response.
  // So, the response for a CrawlJob should ideally include a nested 'settings' object.
  // Let's assume the API returns a structure where settings are directly accessible 
  // or reconstructable if needed. For POSTing, we use a nested structure.
  // For GET /jobs, the backend returns schema.CrawlJobSchema which nests settings.
  settings: CrawlSettings; 
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

// Deprecated: BreachData was similar to DownloadedFileEntry, using DownloadedFileEntry now.
// export interface BreachData {
//   id: string;
//   sourceUrl: string;
//   fileUrl: string;
//   fileType: string;
//   dateFound: string; 
//   keywords: string[];
//   status?: 'new' | 'reviewed' | 'ignored';
// }
