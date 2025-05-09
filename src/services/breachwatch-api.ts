
// src/services/breachwatch-api.ts
import type { SettingsFormData, DownloadedFileEntry, CrawlJob, ScheduleData, UserPreferences, User, UserStatusUpdate, UserRoleUpdate, PasswordChangePayload, LoginPayload, AuthTokenResponse, RegisterPayload } from '@/types';
import { NEXT_PUBLIC_BACKEND_API_URL } from '@/config/config';

// Helper to construct full API URLs
const getApiUrl = (path: string) => `${NEXT_PUBLIC_BACKEND_API_URL}/api/v1${path}`;

// Helper to get token from localStorage
const getToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('breachwatchAuthToken');
  }
  return null;
};

// Helper for making API requests
async function apiRequest<T>(
  path: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
  body?: any,
  isAuthRequest: boolean = false // Flag to indicate if this is an auth-related request that doesn't need token for itself
): Promise<T> {
  const url = getApiUrl(path);
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  
  const token = getToken();
  if (token && !isAuthRequest) { // Don't add token for login/register requests themselves
    headers['Authorization'] = `Bearer ${token}`;
  }

  const options: RequestInit = {
    method,
    headers,
  };

  if (body && (method === 'POST' || method === 'PUT' || method === 'DELETE')) {
    if (body instanceof FormData) {
      // If body is FormData, don't set Content-Type, browser will do it
      delete headers['Content-Type'];
      options.body = body;
    } else {
      options.body = JSON.stringify(body);
    }
  }


  console.debug(`[API Request] ${method} ${url}`, body && !(body instanceof FormData) ? `with body: ${JSON.stringify(body)}` : (body instanceof FormData ? 'with FormData' : ''));

  try {
    const response = await fetch(url, options);
    console.debug(`[API Response] ${method} ${url} - Status: ${response.status}`);

    if (!response.ok) {
      let errorDetails = 'Unknown error';
      let errorTitle = `API request failed: ${response.status} ${response.statusText}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorDetails = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
        } else {
          errorDetails = JSON.stringify(errorData);
        }
      } catch (e) {
        try {
          errorDetails = await response.text();
          if (errorDetails.length > 300) errorDetails = errorDetails.substring(0, 300) + '...';
          if (!errorDetails.trim()) errorDetails = 'Server returned an error with no details.';
        } catch (textError) {
          errorDetails = 'Failed to parse error response and could not read response text.';
        }
      }
      console.error(`API Error: ${response.status} ${response.statusText} for ${method} ${url}`, `Details: ${errorDetails}`);
      if (method === 'GET' && response.status === 404 && (path.includes('/preferences') || path.startsWith('/users/'))) {
        console.warn(`API Info: Received 404 for ${method} ${url}. Returning null.`);
        return null as T;
      }
      // Handle specific 401 for auth related endpoints
      if (response.status === 401 && (path.includes('/auth/login') || path.includes('/auth/register'))) {
          throw new Error(errorDetails || 'Invalid credentials or user already exists.');
      }
      throw new Error(`${errorTitle}. Details: ${errorDetails}`);
    }

    if (response.status === 204 || response.headers.get('content-length') === '0') {
      console.debug(`[API Response] ${method} ${url} - Status ${response.status} or 0 length, returning null.`);
      return null as T;
    }

    try {
      const data = await response.json();
      console.debug(`[API Response Data] ${method} ${url}`, data);
      return data as T;
    } catch (jsonError) {
      console.error(`API Error: Failed to parse successful JSON response from ${url}. Status: ${response.status}`, jsonError);
      throw new Error(`Server responded successfully (Status: ${response.status}) but failed to parse JSON response.`);
    }

  } catch (error: unknown) {
    console.error(`API Request Failed: ${method} ${url}`, error);
    if (error instanceof TypeError && error.message.toLowerCase().includes('failed to fetch')) {
      const networkError = new Error(`Network Error: Could not connect to the backend at ${url}. Please check if the backend service is running, the URL is correct, and CORS is configured.`);
      (networkError as any).cause = error; 
      throw networkError;
    }
    if (error instanceof Error) throw error;
    else throw new Error(`An unexpected error occurred during the API request: ${String(error)}`);
  }
}


// --- Auth Endpoints ---
export const loginUser = async (payload: LoginPayload): Promise<AuthTokenResponse> => {
  // FormData for OAuth2PasswordRequestForm
  const formData = new FormData();
  formData.append('username', payload.email); // FastAPI's OAuth2PasswordRequestForm uses 'username' for email
  formData.append('password', payload.password);
  return apiRequest<AuthTokenResponse>('/auth/login', 'POST', formData, true);
};

export const registerUser = async (payload: RegisterPayload): Promise<User> => {
  return apiRequest<User>('/auth/register', 'POST', payload, true);
};

export const getCurrentUser = async (): Promise<User | null> => {
  // This endpoint typically requires a token, so isAuthRequest is false
  return apiRequest<User | null>('/auth/me', 'GET');
};


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
  proxies?: string[] | null;
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
  if (jobId) path += `job_id=${jobId}&`;
  path += `skip=${skip}&limit=${limit}`;
  return apiRequest<DownloadedFileEntry[]>(path);
};

export const deleteDownloadedFileRecord = async (fileId: string, deletePhysical: boolean = false): Promise<void> => {
  return apiRequest<void>(`/crawl/results/downloaded/${fileId}`, 'DELETE', { delete_physical: deletePhysical });
};

// --- User Preferences Endpoints ---
// The backend endpoints for preferences are /users/me/preferences
export const getUserPreferences = async (): Promise<UserPreferences | null> => {
  return apiRequest<UserPreferences | null>(`/users/me/preferences`, 'GET');
};

export const updateUserPreferences = async (preferences: Omit<UserPreferences, 'user_id' | 'updated_at'>): Promise<UserPreferences> => {
  return apiRequest<UserPreferences>(`/users/me/preferences`, 'PUT', preferences);
};

// --- User Management Endpoints (Admin) ---
export const getUsers = async (skip: number = 0, limit: number = 100): Promise<User[]> => {
  return apiRequest<User[]>(`/users?skip=${skip}&limit=${limit}`);
};

export const getUser = async (userId: string): Promise<User | null> => { 
  return apiRequest<User | null>(`/users/${userId}`);
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

// --- Password Change Endpoint (for current user) ---
export const changePassword = async (currentPassword: string, newPassword: string): Promise<MessageResponse> => {
  const payload: PasswordChangePayload = {
    current_password: currentPassword,
    new_password: newPassword,
  };
  return apiRequest<MessageResponse>(`/users/me/password`, 'PUT', payload); 
};

// --- Helper Function for parsing settings ---
export const parseSettingsForBackend = (settings: SettingsFormData): BackendCrawlSettings => {
  const parseStringList = (str: string | undefined, separator: RegExp = /,|\n/): string[] => {
    return str ? str.split(separator).map(s => s.trim()).filter(s => s) : [];
  };

  const parseFileExtensions = (str: string | undefined): string[] => {
     return str ? str.split(/,|\n/).map(s => s.trim().replace(/^\./, '')).filter(s => s) : [];
  }
  
  const parseProxies = (str: string | undefined): string[] | null => {
    if (!str || str.trim() === '') return null;
    return str.split('\n').map(p => p.trim()).filter(p => p);
  };


  let schedule: ScheduleData | null = null;
  if (settings.scheduleEnabled) {
    const type = settings.scheduleType;
    const cronExpression = settings.scheduleCronExpression?.trim() || null;
    const runAtDate = settings.scheduleRunAtDate;
    const runAtTime = settings.scheduleRunAtTime;
    const timezone = settings.scheduleTimezone?.trim() || null;

    let runAtISO: string | null = null;
    if (type === 'one-time' && runAtDate && runAtTime) {
        try {
            const combinedDateTimeString = `${runAtDate}T${runAtTime}:00`;
            const dateObj = new Date(combinedDateTimeString); 
            runAtISO = dateObj.toISOString(); 
            if (timezone && timezone !== "UTC") {
                 console.warn("Timezone conversion on client-side for one-time schedule is tricky. Sending local ISO string. Backend should interpret with provided timezone.");
            }
        } catch (e) {
            console.error("Error constructing date from parts:", e);
        }
    }

    const isValidRecurring = type === 'recurring' && !!cronExpression;
    const isValidOneTime = type === 'one-time' && !!runAtISO; 

    if (isValidRecurring || isValidOneTime) {
         schedule = {
            type: type,
            cron_expression: isValidRecurring ? cronExpression : null,
            run_at: isValidOneTime ? runAtISO : null,
            timezone: timezone,
        };
    } else {
         console.warn(`Schedule config incomplete for type '${type}'. Schedule will not be set.`);
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
    use_search_engines: true, 
    max_results_per_dork: settings.maxResultsPerDork || null, 
    max_concurrent_requests_per_domain: settings.maxConcurrentRequestsPerDomain || null, 
    custom_user_agent: settings.customUserAgent?.trim() || null, 
    proxies: parseProxies(settings.proxies), 
    schedule: schedule,
  };
};

// Health Check Function
export const checkBackendHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch(getApiUrl('/'), { 
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    if (response.ok) {
      const data = await response.json();
      console.log('Backend health check successful:', data);
      return data.database_status === "ok" && (data.cache_status === "ok (initialized)" || data.cache_status === "ok");
    } else {
      console.warn('Backend health check failed (response not ok):', response.status, response.statusText);
      try { const errorData = await response.json(); console.warn('Backend health error details:', errorData); }
      catch (e) { console.warn('Could not parse backend health error response.'); }
      return false;
    }
  } catch (error) {
    console.error('Backend health check error (network or other):', error);
    return false;
  }
};
