

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
  is_active: boolean; 
  avatarUrl?: string | null; 
  created_at?: string; 
  updated_at?: string; 
}

export interface UserStatusUpdate {
  is_active: boolean;
}

export interface UserRoleUpdate {
  role: UserRole;
}

export interface PasswordChangePayload {
    current_password: string;
    new_password: string;
}


export interface UserPreferences {
  user_id: string;
  default_items_per_page: number;
  receive_email_notifications: boolean;
  updated_at?: string; 
}


export interface ScheduleData {
  type: 'one-time' | 'recurring';
  cron_expression?: string | null; 
  run_at?: string | null; 
  timezone?: string | null; 
}

export interface CrawlSettings {
  keywords: string[];
  fileExtensions: string[]; 
  seedUrls: string[]; 
  searchDorks: string[]; 
  crawlDepth: number; 
  respectRobotsTxt: boolean; 
  requestDelaySeconds: number; 
  useSearchEngines: boolean; 
  maxResultsPerDork?: number | null; 
  maxConcurrentRequestsPerDomain?: number | null; 
  customUserAgent?: string | null; 
  schedule?: ScheduleData | null;
  proxies?: string[] | null; // List of proxy URLs
}


export interface CrawlJob {
  id: string; 
  name?: string | null;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'stopping' | 'completed_empty' | 'scheduled';
  created_at: string; 
  updated_at: string; 
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
  settings_proxies?: string[] | null; // Added proxies here
  settings_schedule_type?: 'one-time' | 'recurring' | null;
  settings_schedule_cron_expression?: string | null;
  settings_schedule_run_at?: string | null; 
  settings_schedule_timezone?: string | null;

  results_summary?: {
    files_found?: number;
  } | null;
  next_run_at?: string | null; 
  last_run_at?: string | null; 
}


export interface NavItem {
  title: string;
  href: string;
  icon: LucideIcon;
  label?: string;
  disabled?: boolean;
  adminOnly?: boolean; 
  category?: 'main' | 'account'; 
}

export interface SettingsFormData {
  keywords: string; 
  fileExtensions: string; 
  seedUrls: string; 
  searchDorks: string; 
  crawlDepth: number;
  respectRobotsTxt: boolean;
  requestDelay: number; 
  customUserAgent?: string; 
  maxResultsPerDork?: number;
  maxConcurrentRequestsPerDomain?: number;
  proxies?: string; // Newline separated proxy list for textarea input
  scheduleEnabled: boolean;
  scheduleType: 'one-time' | 'recurring';
  scheduleCronExpression?: string; 
  scheduleRunAtDate?: string; 
  scheduleRunAtTime?: string; 
  scheduleTimezone?: string;
}

    