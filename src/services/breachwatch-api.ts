// src/services/breachwatch-api.ts
import type { SettingsFormData, DownloadedFileEntry, CrawlJob, ScheduleData } from '@/types';
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
    },
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      const errorData = await response.text().catch(() => 'Failed to parse error response');
      console.error(`API Error: ${response.status} ${response.statusText} for ${method} ${url}`, errorData);
      throw new Error(`API request failed: ${response.status} ${response.statusText}. Details: ${errorData}`);
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
  return apiRequest<void>(`/crawl/results/downloaded/${fileId}`, 'DELETE', { delete_physical: deletePhysical });
};


// Helper to parse frontend settings strings into backend-compatible arrays/objects
export const parseSettingsForBackend = (settings: SettingsFormData): BackendCrawlSettings => {
  const parseStringList = (str: string | undefined, separator: RegExp = /,|\n/): string[] => {
    return str ? str.split(separator).map(s => s.trim()).filter(s => s) : [];
  };
  
  const parseFileExtensions = (str: string | undefined): string[] => {
     return str ? str.split(/,|\n/).map(s => s.trim().replace(/^\./, '')).filter(s => s) : [];
  }

  let schedule: ScheduleData | null = null;
  if (settings.scheduleEnabled) {
    schedule = {
      type: settings.scheduleType,
      cronExpression: settings.scheduleType === 'recurring' ? settings.scheduleCronExpression || null : null,
      runAt: settings.scheduleType === 'one-time' && settings.scheduleRunAtDate && settings.scheduleRunAtTime
        ? new Date(`${settings.scheduleRunAtDate}T${settings.scheduleRunAtTime}:00`).toISOString()
        : null,
      timezone: settings.scheduleTimezone || null,
    };
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
    max_results_per_dork: settings.maxResultsPerDork,
    max_concurrent_requests_per_domain: settings.maxConcurrentRequestsPerDomain,
    custom_user_agent: settings.customUserAgent || null,
    schedule: schedule,
  };
};