
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
  email: string;
  full_name?: string | null; // Changed from name to full_name to match backend
  role: UserRole;
  is_active: boolean; 
  avatarUrl?: string | null; // Frontend only, not in backend model directly
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

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name?: string | null;
  // role and is_active will be defaulted by backend
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
}


export interface UserPreferences {
  user_id: string; // This will be derived from token on backend for /me/preferences
  default_items_per_page: number;
  receive_email_notifications: boolean;
  updated_at?: string; 
}


export interface ScheduleData {
  type: 'one-time' | 'recurring';
  cron_expression?: string | null; 
  run_at?: string | null; // Should be ISO string (UTC) when sending to backend
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
  // Direct exposure of settings from the model for easier frontend access
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
  settings_proxies?: string[] | null; 
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
  scheduleRunAtDate?: string; // Date part YYYY-MM-DD
  scheduleRunAtTime?: string; // Time part HH:MM
  scheduleTimezone?: string;
}
