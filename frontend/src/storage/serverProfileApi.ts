/**
 * Server Profile API Client
 * Handles all Django REST API interactions for authenticated users
 */
import type {
  ServerProfile,
  ProfileFormData,
  ProfileListResponse,
  ProfileResponse,
  BatchCreateResponse,
  LocalProfile,
} from '@/types/profile';

/**
 * Get CSRF token from Django cookie
 */
function getCSRFToken(): string {
  const name = 'csrftoken';
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [key, value] = cookie.trim().split('=');
    if (key === name) {
      return value;
    }
  }
  return '';
}

/**
 * Make authenticated API request
 */
async function apiRequest<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCSRFToken(),
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'same-origin',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.error || `API error: ${response.status}`);
  }

  return response.json();
}

/**
 * Server profile API for authenticated users
 */
export const serverProfileApi = {
  /**
   * Get all profiles for the current user
   */
  async getAll(): Promise<ServerProfile[]> {
    const data = await apiRequest<ProfileListResponse>('/api/profiles/');
    return data.profiles;
  },

  /**
   * Get a single profile by ID
   */
  async getById(id: number): Promise<ServerProfile> {
    const data = await apiRequest<ProfileResponse>(`/api/profiles/${id}/`);
    return data.profile;
  },

  /**
   * Create a new profile
   */
  async create(data: ProfileFormData): Promise<ServerProfile> {
    const response = await apiRequest<ProfileResponse>('/api/profiles/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response.profile;
  },

  /**
   * Update an existing profile
   */
  async update(id: number, data: Partial<ProfileFormData>): Promise<ServerProfile> {
    const response = await apiRequest<ProfileResponse>(`/api/profiles/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
    return response.profile;
  },

  /**
   * Delete a profile
   */
  async delete(id: number): Promise<void> {
    await apiRequest<{ success: boolean }>(`/api/profiles/${id}/`, {
      method: 'DELETE',
    });
  },

  /**
   * Set a profile as default
   */
  async setDefault(id: number): Promise<ServerProfile> {
    const response = await apiRequest<ProfileResponse>(
      `/api/profiles/${id}/default/`,
      { method: 'POST' }
    );
    return response.profile;
  },

  /**
   * Batch create profiles (for migration from local storage)
   */
  async batchCreate(profiles: LocalProfile[]): Promise<BatchCreateResponse> {
    // Convert LocalProfile to the format expected by the API
    const profilesData = profiles.map((p) => ({
      name: p.name,
      birth_year: p.birth_year,
      birth_month: p.birth_month,
      birth_day: p.birth_day,
      birth_hour: p.birth_hour,
      birth_minute: p.birth_minute,
      is_male: p.is_male,
    }));

    return apiRequest<BatchCreateResponse>('/api/profiles/batch/', {
      method: 'POST',
      body: JSON.stringify({ profiles: profilesData }),
    });
  },
};
