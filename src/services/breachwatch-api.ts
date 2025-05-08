// src/services/breachwatch-api.ts
import type { SettingsFormData, DownloadedFileEntry, CrawlJob, ScheduleData, UserPreferences, User, UserStatusUpdate, UserRoleUpdate } from '@/types';
import { NEXT_PUBLIC_BACKEND_API_URL } from '@/config/config';

// Helper to construct full API URLs
const getApiUrl = (path: string) => `${NEXT_PUBLIC_BACKEND_API_URL}/api/v1${path}`;

// Helper for making API requests
async function apiRequest<T>(
  path: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
  body?: any
): Promise<T> {
  const url = getApiUrl(path);
  const options: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      // In a real app, Authorization header with JWT token would be added here
      // 'Authorization': `Bearer ${getToken()}`,
    },
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      let errorDetails = 'Unknown error';
      try {
        // Try to parse error response as JSON, fallback to text
        const errorData = await response.json();
        errorDetails = errorData.detail || JSON.stringify(errorData);
      } catch (e) {
        errorDetails = await response.text().catch(() => 'Failed to parse error response');
      }
      console.error(`API Error: ${response.status} ${response.statusText} for ${method} ${url}`, errorDetails);
      // For 404 on GET preferences, we might want to return null instead of throwing an error.
      if (method === 'GET' && response.status === 404 && path.includes('/preferences')) {
        return null as T;
      }
      throw new Error(`API request failed: ${response.status} ${response.statusText}. Details: ${errorDetails}`);
    }
    if (response.status === 204 || response.headers.get('content-length') === '0') { 
        return null as T; 
    }
    return response.json() as Promise<T>;
  } catch (error) {
    console.error(`Network or other error during API request to ${url}:`, error);
    throw error; 
  }
}

// --- CrawlJob Endpoints ---

export interface BackendCrawlSettings {
  keywords: string[];
  file_extensions: string[];
  seed_urls: string[];
  search_dorks: string[];
  crawl_depth: number;
  respect_robots_txt: boolean;
  request_delay_seconds: number;
  use_search_engines: boolean;
  max_results_per_dork?: number | null;
  max_concurrent_requests_per_domain?: number | null;
  custom_user_agent?: string | null;
  schedule?: ScheduleData | null;
}

export interface CreateCrawlJobPayload {
  name?: string;
  settings: BackendCrawlSettings;
}

export interface MessageResponse {
  message: string;
}

export const createCrawlJob = async (payload: CreateCrawlJobPayload): Promise<CrawlJob> => {
  return apiRequest<CrawlJob>('/crawl/jobs', 'POST', payload);
};

export const getCrawlJobs = async (skip: number = 0, limit: number = 100): Promise<CrawlJob[]> => {
  return apiRequest<CrawlJob[]>(`/crawl/jobs?skip=${skip}&limit=${limit}`);
};

export const getCrawlJob = async (jobId: string): Promise<CrawlJob> => {
  return apiRequest<CrawlJob>(`/crawl/jobs/${jobId}`);
};

export const stopCrawlJob = async (jobId: string): Promise<MessageResponse> => {
  return apiRequest<MessageResponse>(`/crawl/jobs/${jobId}/stop`, 'POST');
};

export const deleteCrawlJob = async (jobId: string): Promise<void> => {
  return apiRequest<void>(`/crawl/jobs/${jobId}`, 'DELETE');
};

export const manuallyRunJob = async (jobId: string): Promise<CrawlJob> => {
  return apiRequest<CrawlJob>(`/crawl/jobs/${jobId}/run`, 'POST');
};

// --- DownloadedFile Endpoints ---

export const getDownloadedFiles = async (jobId?: string, skip: number = 0, limit: number = 100): Promise<DownloadedFileEntry[]> => {
  let path = '/crawl/results/downloaded?';
  if (jobId) {
    path += `job_id=${jobId}&`;
  }
  path += `skip=${skip}&limit=${limit}`;
  return apiRequest<DownloadedFileEntry[]>(path);
};

export const deleteDownloadedFileRecord = async (fileId: string, deletePhysical: boolean = false): Promise<void> => {
   // Backend expects delete_physical in the body
  return apiRequest<void>(`/crawl/results/downloaded/${fileId}`, 'DELETE', { delete_physical: deletePhysical });
};


// --- User Preferences Endpoints ---
export const getUserPreferences = async (userId: string): Promise<UserPreferences | null> => {
  return apiRequest<UserPreferences | null>(`/users/${userId}/preferences`, 'GET');
};

// Note: Backend schema only expects preference fields, not user_id or updated_at in PUT body
export const updateUserPreferences = async (userId: string, preferences: Omit<UserPreferences, 'user_id' | 'updated_at'>): Promise<UserPreferences> => {
  return apiRequest<UserPreferences>(`/users/${userId}/preferences`, 'PUT', preferences);
};

// --- User Management Endpoints ---
export const getUsers = async (skip: number = 0, limit: number = 100): Promise<User[]> => {
  return apiRequest<User[]>(`/users?skip=${skip}&limit=${limit}`);
};

export const getUser = async (userId: string): Promise<User> => {
  return apiRequest<User>(`/users/${userId}`);
};

export const updateUserStatus = async (userId: string, payload: UserStatusUpdate): Promise<User> => {
  return apiRequest<User>(`/users/${userId}/status`, 'PUT', payload);
};

export const updateUserRole = async (userId: string, payload: UserRoleUpdate): Promise<User> => {
  return apiRequest<User>(`/users/${userId}/role`, 'PUT', payload);
};

export const deleteUser = async (userId: string): Promise<void> => {
  return apiRequest<void>(`/users/${userId}`, 'DELETE');
};

// --- Password Change Endpoint ---
export const changePassword = async (userId: string, currentPassword: string, newPassword: string): Promise<MessageResponse> => {
  const payload = {
    current_password: currentPassword,
    new_password: newPassword,
  };
  return apiRequest<MessageResponse>(`/users/${userId}/password`, 'PUT', payload);
};


// --- Helper Function ---
// Helper to parse frontend settings strings into backend-compatible arrays/objects
export const parseSettingsForBackend = (settings: SettingsFormData): BackendCrawlSettings => {
  const parseStringList = (str: string | undefined, separator: RegExp = /,|\n/): string[] => {
    return str ? str.split(separator).map(s => s.trim()).filter(s => s) : [];
  };
  
  const parseFileExtensions = (str: string | undefined): string[] => {
     // Returns extensions *without* the leading dot for backend
     return str ? str.split(/,|\n/).map(s => s.trim().replace(/^\./, '')).filter(s => s) : [];
  }

  let schedule: ScheduleData | null = null;
  if (settings.scheduleEnabled) {
    schedule = {
      type: settings.scheduleType,
      // Use ?. for optional chaining and provide null if undefined/empty
      cronExpression: settings.scheduleType === 'recurring' ? settings.scheduleCronExpression?.trim() || null : null,
      runAt: settings.scheduleType === 'one-time' && settings.scheduleRunAtDate && settings.scheduleRunAtTime
        ? new Date(`${settings.scheduleRunAtDate}T${settings.scheduleRunAtTime}:00`).toISOString() 
        : null,
      timezone: settings.scheduleTimezone?.trim() || null,
    };
     // Validate that required fields for the type are present
     if (schedule.type === 'recurring' && !schedule.cronExpression) {
         console.warn("Recurring schedule enabled but cron expression is missing.");
         // Optionally throw an error or default schedule to null
         // schedule = null; 
     }
     if (schedule.type === 'one-time' && !schedule.runAt) {
         console.warn("One-time schedule enabled but run date/time is missing or invalid.");
         // Optionally throw an error or default schedule to null
         // schedule = null;
     }
  }


  return {
    keywords: parseStringList(settings.keywords),
    file_extensions: parseFileExtensions(settings.fileExtensions),
    seed_urls: parseStringList(settings.seedUrls),
    search_dorks: parseStringList(settings.searchDorks),
    crawl_depth: settings.crawlDepth,
    respect_robots_txt: settings.respectRobotsTxt,
    request_delay_seconds: settings.requestDelay,
    use_search_engines: true, // Assuming this is always true from frontend for now
    max_results_per_dork: settings.maxResultsPerDork || null, // Ensure null if 0 or undefined
    max_concurrent_requests_per_domain: settings.maxConcurrentRequestsPerDomain || null, // Ensure null if 0 or undefined
    custom_user_agent: settings.customUserAgent?.trim() || null, // Ensure null if empty
    schedule: schedule,
  };
};

