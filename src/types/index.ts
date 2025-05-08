
import type { LucideIcon } from 'lucide-react';

// Corresponds to backend's DownloadedFileSchema
export interface DownloadedFileEntry {
  id: string; // uuid.UUID
  source_url: string; // HttpUrl string from backend
  file_url: string; // HttpUrl string from backend
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
  is_active: boolean; // Added from backend schema
  avatarUrl?: string | null; // Optional: for displaying user avatar
  created_at?: string; // Added from backend schema
  updated_at?: string; // Added from backend schema
}

// For updating user status (corresponds to backend schema)
export interface UserStatusUpdate {
  is_active: boolean;
}

// For updating user role (corresponds to backend schema)
export interface UserRoleUpdate {
  role: UserRole;
}

// For changing password (corresponds to backend schema)
export interface PasswordChangePayload {
    current_password: string;
    new_password: string;
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
  // Use snake_case to match backend schema
  cron_expression?: string | null; // For recurring jobs, e.g., "0 0 * * *" for daily at midnight
  run_at?: string | null; // ISO string for one-time jobs
  timezone?: string | null; // e.g., "Asia/Jakarta"
}

// Corresponds to backend's CrawlSettingsSchema (used as part of CrawlJob)
// Note: Field names here are camelCase (JS convention), but are mapped
// to snake_case in parseSettingsForBackend when sending to API.
export interface CrawlSettings {
  keywords: string[];
  fileExtensions: string[]; // Renamed from file_extensions for JS convention
  seedUrls: string[]; // Renamed from seed_urls
  searchDorks: string[]; // Renamed from search_dorks
  crawlDepth: number; // Renamed from crawl_depth
  respectRobotsTxt: boolean; // Renamed from respect_robots_txt
  requestDelaySeconds: number; // Renamed from request_delay_seconds
  useSearchEngines: boolean; // Renamed from use_search_engines
  maxResultsPerDork?: number | null; // Renamed from max_results_per_dork
  maxConcurrentRequestsPerDomain?: number | null; // Renamed from max_concurrent_requests_per_domain
  customUserAgent?: string | null; // Renamed from custom_user_agent
  schedule?: ScheduleData | null;
}


// Corresponds to backend's CrawlJobSchema (expecting snake_case from backend API)
export interface CrawlJob {
  id: string; // uuid.UUID
  name?: string | null;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'stopping' | 'completed_empty' | 'scheduled';
  created_at: string; // datetime (ISO string)
  updated_at: string; // datetime (ISO string)
  // Settings nested object - Assuming backend sends snake_case keys for settings within the job object
  settings_keywords: string[];
  settings_file_extensions: string[];
  settings_seed_urls: string[];
  settings_search_dorks: string[];
  settings_crawl_depth: number;
  settings_respect_robots_txt: boolean;
  settings_request_delay_seconds: number;
  settings_use_search_engines: boolean;
  settings_max_results_per_dork?: number | null;
  settings_max_concurrent_requests_per_domain?: number | null;
  settings_custom_user_agent?: string | null;
  settings_schedule_type?: 'one-time' | 'recurring' | null;
  settings_schedule_cron_expression?: string | null;
  settings_schedule_run_at?: string | null; // ISO String
  settings_schedule_timezone?: string | null;

  results_summary?: {
    files_found?: number;
  } | null;
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
  customUserAgent?: string; // Optional custom user agent
  maxResultsPerDork?: number;
  maxConcurrentRequestsPerDomain?: number;
  // Scheduling fields
  scheduleEnabled: boolean;
  scheduleType: 'one-time' | 'recurring';
  scheduleCronExpression?: string; // For recurring
  scheduleRunAtDate?: string; // For one-time date part (YYYY-MM-DD)
  scheduleRunAtTime?: string; // For one-time time part (HH:MM)
  scheduleTimezone?: string;
}
