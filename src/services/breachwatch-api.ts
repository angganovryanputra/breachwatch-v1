
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

  if (body && (method === 'POST' || method === 'PUT' || method === 'DELETE')) { // Ensure body is only added for relevant methods
    options.body = JSON.stringify(body);
  }

  console.debug(`[API Request] ${method} ${url}`, body ? `with body: ${JSON.stringify(body)}` : ''); // Log request details

  try {
    const response = await fetch(url, options);

    console.debug(`[API Response] ${method} ${url} - Status: ${response.status}`); // Log response status

    if (!response.ok) {
      let errorDetails = 'Unknown error';
      try {
        // Try to parse error response as JSON, fallback to text
        const errorData = await response.json();
        errorDetails = errorData.detail || JSON.stringify(errorData);
      } catch (e) {
        try {
            errorDetails = await response.text();
        } catch (textError) {
             errorDetails = 'Failed to parse error response';
        }
      }
      console.error(`API Error: ${response.status} ${response.statusText} for ${method} ${url}`, errorDetails);
      // For 404 on GET preferences, we might want to return null instead of throwing an error.
      if (method === 'GET' && response.status === 404 && (path.includes('/preferences') || path.startsWith('/users/'))) {
        console.warn(`API Info: Received 404 for ${method} ${url}, returning null.`);
        return null as T;
      }
      throw new Error(`API request failed: ${response.status} ${response.statusText}. Details: ${errorDetails}`);
    }
    // Check for No Content response explicitly or zero content length
    if (response.status === 204 || response.headers.get('content-length') === '0') {
        console.debug(`[API Response] ${method} ${url} - Status 204 or 0 length, returning null.`);
        return null as T;
    }

    // Attempt to parse JSON response
    try {
        const data = await response.json();
        console.debug(`[API Response Data] ${method} ${url}`, data); // Log successful data
        return data as T;
    } catch (jsonError) {
        console.error(`API Error: Failed to parse JSON response from ${url}`, jsonError);
        throw new Error(`Failed to parse JSON response from server. Status: ${response.status}`);
    }

  } catch (error: unknown) {
    console.error(`Network or other error during API request to ${url}:`, error);
    // Check if it's a fetch-related TypeError (often wraps NetworkError)
    if (error instanceof TypeError && error.message.toLowerCase().includes('failed to fetch')) {
         const networkError = new Error(`Network Error: Failed to connect to the backend at ${url}. Please ensure the backend service is running and reachable.`);
         (networkError as any).cause = error; // Preserve original error cause if possible
         throw networkError;
    }
    // Re-throw other errors
    if (error instanceof Error) {
        throw error; // Re-throw known Error types
    } else {
         throw new Error(`An unexpected error occurred during the API request: ${String(error)}`); // Wrap unknown errors
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
  // Note: DELETE might not need a body, depending on backend implementation.
  // If the backend requires a body for DELETE (e.g., for options), pass it.
  // Assuming no body needed for DELETE job itself based on common practices.
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
  // Handling 404 specifically within apiRequest now
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
            // Combine date and time. Crucially, DO NOT assume local timezone here.
            // The backend should interpret this based on the provided `timezone` field.
            // Send the date and time components as they are, or construct an ISO string *without* timezone offset
            // if the backend expects UTC or will handle the conversion using the timezone field.
            // A common approach is to construct the ISO string assuming it's in the target timezone,
            // but let the backend confirm/convert. Let's try constructing without explicit offset.
            const combinedDateTimeString = `${runAtDate}T${runAtTime}:00`; // Example: "2024-08-15T14:30:00"
            // If we know the timezone, we *could* try to get an ISO string with offset, but it's complex in JS.
            // Sending the combined string might be safer if the backend handles timezone parsing.
            // Let's default to ISO string assuming UTC for now, but highlight backend dependency.
            runAtISO = new Date(`${combinedDateTimeString}Z`).toISOString(); // Appends Z for UTC assumption
            // **Important**: The backend *must* correctly interpret this, potentially using the `timezone` field
            // to adjust if the user intended a different timezone.

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
            cron_expression: isValidRecurring ? cronExpression : null, // Match backend field name
            run_at: isValidOneTime ? runAtISO : null,                  // Match backend field name
            timezone: timezone,
        };
    } else {
         console.warn(`Schedule config incomplete for type '${type}'. Schedule will not be set.`);
    }
  }


  return {
    keywords: parseStringList(settings.keywords),
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
