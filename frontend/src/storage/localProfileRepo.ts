/**
 * Local Profile Repository
 * Handles all IndexedDB operations for anonymous users
 *
 * Uses localStorage as a synchronous cache for instant page loads.
 * IndexedDB is the source of truth, localStorage mirrors it.
 */
import { db } from './database';
import type { LocalProfile, ProfileFormData } from '@/types/profile';
import { STORAGE_KEYS } from '@/constants';

const CACHE_KEY = STORAGE_KEYS.PROFILES_CACHE;

/**
 * localStorage cache for instant synchronous reads.
 * This is the KEY to eliminating the "pop" effect.
 */
export const profileCache = {
  /**
   * Get profiles from localStorage (SYNC - instant!)
   */
  get(): LocalProfile[] {
    try {
      const cached = localStorage.getItem(CACHE_KEY);
      return cached ? JSON.parse(cached) : [];
    } catch {
      return [];
    }
  },

  /**
   * Save profiles to localStorage
   */
  set(profiles: LocalProfile[]): void {
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify(profiles));
    } catch {
      // localStorage full or unavailable, ignore
    }
  },
};

/**
 * Generate a UUID for local profile tracking
 */
function generateLocalId(): string {
  return crypto.randomUUID();
}

/**
 * Local profile repository using Dexie/IndexedDB
 */
export const localProfileRepo = {
  /**
   * Get all profiles from local storage (sorted by creation date, newest first)
   * Also syncs the localStorage cache.
   */
  async getAll(): Promise<LocalProfile[]> {
    const profiles = await db.profiles.orderBy('created_at').reverse().toArray();
    profileCache.set(profiles); // Keep cache in sync
    return profiles;
  },

  /**
   * Get all profiles unsorted (for migration sync)
   */
  async getAllRaw(): Promise<LocalProfile[]> {
    return db.profiles.toArray();
  },

  /**
   * Get a single profile by ID
   */
  async getById(id: number): Promise<LocalProfile | undefined> {
    return db.profiles.get(id);
  },

  /**
   * Get the default profile
   */
  async getDefault(): Promise<LocalProfile | undefined> {
    return db.profiles.where('is_default').equals(1).first();
  },

  /**
   * Create a new profile
   */
  async create(data: ProfileFormData): Promise<LocalProfile> {
    const profile: Omit<LocalProfile, 'id'> = {
      ...data,
      localId: generateLocalId(),
      is_default: false,
      created_at: new Date().toISOString(),
    };

    const id = await db.profiles.add(profile as LocalProfile);

    // If this is the first profile, make it default
    const count = await db.profiles.count();
    let result: LocalProfile;
    if (count === 1) {
      await db.profiles.update(id, { is_default: true });
      result = { ...profile, id, is_default: true } as LocalProfile;
    } else {
      result = { ...profile, id } as LocalProfile;
    }

    // Sync localStorage cache
    await this.getAll();
    return result;
  },

  /**
   * Update an existing profile
   */
  async update(id: number, data: Partial<ProfileFormData>): Promise<LocalProfile | undefined> {
    await db.profiles.update(id, data);
    const result = await db.profiles.get(id);
    await this.getAll(); // Sync cache
    return result;
  },

  /**
   * Delete a profile
   */
  async delete(id: number): Promise<void> {
    const profile = await db.profiles.get(id);
    const wasDefault = profile?.is_default;

    await db.profiles.delete(id);

    // If deleted profile was default, set another as default
    if (wasDefault) {
      const firstProfile = await db.profiles.orderBy('created_at').first();
      if (firstProfile?.id) {
        await db.profiles.update(firstProfile.id, { is_default: true });
      }
    }

    await this.getAll(); // Sync cache
  },

  /**
   * Set a profile as the default
   */
  async setDefault(id: number): Promise<void> {
    // Clear all defaults
    await db.profiles.where('is_default').equals(1).modify({ is_default: false });

    // Set new default
    await db.profiles.update(id, { is_default: true });

    await this.getAll(); // Sync cache
  },

  /**
   * Check if there are any local profiles
   */
  async hasProfiles(): Promise<boolean> {
    const count = await db.profiles.count();
    return count > 0;
  },

  /**
   * Get profile count
   */
  async count(): Promise<number> {
    return db.profiles.count();
  },
};
