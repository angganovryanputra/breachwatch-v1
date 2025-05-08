
// src/services/breachwatch-api.ts
import type { SettingsFormData, DownloadedFileEntry, CrawlJob, ScheduleData, UserPreferences, User, UserStatusUpdate, UserRoleUpdate, PasswordChangePayload } from '@/types';
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

  if (body && (method === 'POST' || method === 'PUT' || method === 'DELETE')) {
    options.body = JSON.stringify(body);
  }

  console.debug(`[API Request] ${method} ${url}`, body ? `with body: ${JSON.stringify(body)}` : '');

  try {
    const response = await fetch(url, options);

    console.debug(`[API Response] ${method} ${url} - Status: ${response.status}`);

    // Check if the response is not OK (status code outside 200-299 range)
    if (!response.ok) {
      let errorDetails = 'Unknown error';
      let errorTitle = `API request failed: ${response.status} ${response.statusText}`;
      try {
        // Attempt to parse error response as JSON for more details
        const errorData = await response.json();
        if (errorData.detail) {
          // FastAPI often returns errors in a 'detail' field
          errorDetails = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
        } else {
          errorDetails = JSON.stringify(errorData);
        }
      } catch (e) {
        // If parsing JSON fails, try to get the response as text
        try {
          errorDetails = await response.text();
          // Limit the length of the text details to avoid overly long messages
          if (errorDetails.length > 300) {
             errorDetails = errorDetails.substring(0, 300) + '...';
          }
           if (!errorDetails.trim()) {
             errorDetails = 'Server returned an error with no details.';
           }
        } catch (textError) {
          errorDetails = 'Failed to parse error response and could not read response text.';
        }
      }

      // Log the detailed error
      console.error(`API Error: ${response.status} ${response.statusText} for ${method} ${url}`, `Details: ${errorDetails}`);

      // Specific handling for 404 on certain GET requests (e.g., preferences might not exist yet)
      if (method === 'GET' && response.status === 404 && (path.includes('/preferences') || path.startsWith('/users/'))) {
        console.warn(`API Info: Received 404 for ${method} ${url}. This might be expected (e.g., resource not found). Returning null.`);
        return null as T; // Return null as per function signature in these cases
      }

      // Throw a more informative error for other failures
      throw new Error(`${errorTitle}. Details: ${errorDetails}`);
    }

    // Handle successful responses with no content (e.g., 204 No Content)
    if (response.status === 204 || response.headers.get('content-length') === '0') {
      console.debug(`[API Response] ${method} ${url} - Status ${response.status} or 0 length, returning null.`);
      return null as T;
    }

    // Attempt to parse successful JSON response
    try {
      const data = await response.json();
      console.debug(`[API Response Data] ${method} ${url}`, data);
      return data as T;
    } catch (jsonError) {
      // This case means the server responded with 2xx status but the body wasn't valid JSON
      console.error(`API Error: Failed to parse successful JSON response from ${url}. Status: ${response.status}`, jsonError);
      throw new Error(`Server responded successfully (Status: ${response.status}) but failed to parse JSON response.`);
    }

  } catch (error: unknown) {
    // Handle network errors (fetch itself failed) or errors thrown above
    console.error(`API Request Failed: ${method} ${url}`, error);

    // Specifically identify network errors (TypeError often wraps NetworkError)
    if (error instanceof TypeError && error.message.toLowerCase().includes('failed to fetch')) {
      const networkError = new Error(`Network Error: Could not connect to the backend at ${url}. Please check if the backend service is running, the URL is correct, and CORS is configured.`);
      (networkError as any).cause = error; // Preserve original error if possible
      throw networkError;
    }

    // Re-throw other errors (including the ones we constructed above)
    if (error instanceof Error) {
      throw error;
    } else {
      // Wrap unknown errors
      throw new Error(`An unexpected error occurred during the API request: ${String(error)}`);
    }
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
   // Backend expects delete_physical in the body for DELETE request on this specific endpoint
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

export const getUser = async (userId: string): Promise<User | null> => { // Allow null if user not found
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

// --- Password Change Endpoint ---
// The backend expects a specific payload shape defined in its schemas.PasswordChangeSchema
// which typically includes current_password and new_password.
export const changePassword = async (userId: string, currentPassword: string, newPassword: string): Promise<MessageResponse> => {
  const payload: PasswordChangePayload = {
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
    const type = settings.scheduleType;
    const cronExpression = settings.scheduleCronExpression?.trim() || null;
    const runAtDate = settings.scheduleRunAtDate;
    const runAtTime = settings.scheduleRunAtTime;
    const timezone = settings.scheduleTimezone?.trim() || null;

    let runAtISO: string | null = null;
    if (type === 'one-time' && runAtDate && runAtTime) {
        try {
            // Construct the ISO string using the date and time, interpreted in the specified timezone.
            // The backend expects a timezone-aware ISO string (e.g., with offset or 'Z').
            // Creating timezone-aware dates purely in client-side JS is tricky.
            // A robust approach is to send date, time, and timezone separately, but the current backend schema expects ISO.
            // We'll construct an ISO string assuming the date/time *is* in the target timezone,
            // and let the backend handle final conversion if needed. This is slightly ambiguous.
            // Sending as UTC ('Z') might be safer if the backend *always* expects UTC.
            const combinedDateTimeString = `${runAtDate}T${runAtTime}:00`; // Example: "2024-08-15T14:30:00"

            // Let's try sending the date/time string and timezone separately if the backend schema allows, otherwise format to ISO UTC
             // Assuming backend expects ISO string:
             // Convert to Date object, assuming the input IS in the target timezone, then get UTC ISO string.
             // This requires careful handling or a library like date-fns-tz.
             // Simpler approach for now: Assume UTC or let backend handle with provided timezone.
             // We'll send the combined string + timezone if backend supports, else format to ISO UTC.
             // CURRENT BACKEND SCHEMA seems to expect ISO string for run_at. Send as UTC.
            runAtISO = new Date(`${combinedDateTimeString}Z`).toISOString(); // Append Z assuming UTC interpretation is desired

        } catch (e) {
            console.error("Error constructing date from parts:", e);
        }
    }

    // Check if schedule is valid for its type
    const isValidRecurring = type === 'recurring' && !!cronExpression;
    const isValidOneTime = type === 'one-time' && !!runAtISO;

    if (isValidRecurring || isValidOneTime) {
         schedule = {
            type: type,
            // Use snake_case to match Python backend Pydantic schema definition
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
    // Use snake_case for backend compatibility
    file_extensions: parseFileExtensions(settings.fileExtensions),
    seed_urls: parseStringList(settings.seedUrls), // Backend expects strings
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
