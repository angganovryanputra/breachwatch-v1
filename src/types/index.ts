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

export type UserRole = 'user' | 'admin';

export interface User {
  id: string;
  name?: string | null;
  email: string;
  role: UserRole;
  avatarUrl?: string | null; // Optional: for displaying user avatar
}

export interface UserPreferences {
  user_id: string;
  default_items_per_page: number;
  receive_email_notifications: boolean;
  // Add other preferences here
  updated_at?: string; // datetime (ISO string)
}


export interface ScheduleData {
  type: 'one-time' | 'recurring';
  cronExpression?: string | null; // For recurring jobs, e.g., "0 0 * * *" for daily at midnight
  runAt?: string | null; // ISO string for one-time jobs
  timezone?: string | null; // e.g., "Asia/Jakarta"
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
  custom_user_agent?: string | null;
  schedule?: ScheduleData | null; // Added for job scheduling
}

// Corresponds to backend's CrawlJobSchema
export interface CrawlJob {
  id: string; // uuid.UUID
  name?: string | null;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'stopping' | 'completed_empty' | 'scheduled';
  created_at: string; // datetime (ISO string)
  updated_at: string; // datetime (ISO string)
  settings: CrawlSettings; 
  results_summary?: {
    files_found?: number;
  } | null;
  // Optional fields for scheduled jobs, populated by backend based on settings.schedule
  next_run_at?: string | null; // datetime (ISO string)
  last_run_at?: string | null; // datetime (ISO string)
}


export interface NavItem {
  title: string;
  href: string;
  icon: LucideIcon;
  label?: string;
  disabled?: boolean;
  adminOnly?: boolean; // For conditional rendering based on user role
  category?: 'main' | 'account'; // For grouping in sidebar
}

// This is the frontend form data structure for settings
export interface SettingsFormData {
  keywords: string; // Comma/newline separated
  fileExtensions: string; // Comma/newline separated
  seedUrls: string; // Newline separated
  searchDorks: string; // Newline separated
  crawlDepth: number;
  respectRobotsTxt: boolean;
  requestDelay: number; // in seconds
  customUserAgent: string; // Optional custom user agent
  maxResultsPerDork: number;
  maxConcurrentRequestsPerDomain: number;
  // Scheduling fields
  scheduleEnabled: boolean;
  scheduleType: 'one-time' | 'recurring';
  scheduleCronExpression: string; // For recurring
  scheduleRunAtDate: string; // For one-time date part
  scheduleRunAtTime: string; // For one-time time part
  scheduleTimezone: string;
}
