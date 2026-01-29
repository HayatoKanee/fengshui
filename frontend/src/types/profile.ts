/**
 * Profile TypeScript interfaces
 * Matches Django UserProfile model for seamless local/server storage
 */

/**
 * Base profile data shared between local and server storage
 */
export interface ProfileData {
  name: string;
  birth_year: number;
  birth_month: number;
  birth_day: number;
  birth_hour: number;
  birth_minute: number;
  is_male: boolean;
  is_default: boolean;

  // Calculated BaZi fields (optional, can be computed)
  is_day_master_strong?: boolean | null;
  day_master_wuxing?: string | null;
  favorable_wuxing?: string | null;
  unfavorable_wuxing?: string | null;
}

/**
 * Local profile stored in IndexedDB (Dexie)
 * Uses auto-incrementing local ID
 */
export interface LocalProfile extends ProfileData {
  id?: number;           // Auto-increment ID from Dexie
  localId: string;       // UUID for migration tracking
  created_at: string;    // ISO date string
}

/**
 * Server profile from Django API
 * Uses server-assigned ID
 */
export interface ServerProfile extends ProfileData {
  id: number;            // Server ID
  created_at: string;    // ISO date string from server
}

/**
 * Unified profile type for the application
 * Can be either local or server profile
 */
export type Profile = LocalProfile | ServerProfile;

/**
 * Profile form data for creating/editing
 */
export interface ProfileFormData {
  name: string;
  birth_year: number;
  birth_month: number;
  birth_day: number;
  birth_hour: number;
  birth_minute: number;
  is_male: boolean;
}

/**
 * API response types
 */
export interface ProfileListResponse {
  profiles: ServerProfile[];
}

export interface ProfileResponse {
  profile: ServerProfile;
}

export interface BatchCreateRequest {
  profiles: ProfileData[];
}

export interface BatchCreateResponse {
  created: number;
  profiles: ServerProfile[];
}
