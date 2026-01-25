/**
 * Local Profile Repository
 * Handles all IndexedDB operations for anonymous users
 */
import { db } from './database';
import type { LocalProfile, ProfileFormData } from '@/types/profile';

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
   */
  async getAll(): Promise<LocalProfile[]> {
    return db.profiles.orderBy('created_at').reverse().toArray();
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
    if (count === 1) {
      await db.profiles.update(id, { is_default: true });
      return { ...profile, id, is_default: true } as LocalProfile;
    }

    return { ...profile, id } as LocalProfile;
  },

  /**
   * Update an existing profile
   */
  async update(id: number, data: Partial<ProfileFormData>): Promise<LocalProfile | undefined> {
    await db.profiles.update(id, data);
    return db.profiles.get(id);
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
  },

  /**
   * Set a profile as the default
   */
  async setDefault(id: number): Promise<void> {
    // Clear all defaults
    await db.profiles.where('is_default').equals(1).modify({ is_default: false });

    // Set new default
    await db.profiles.update(id, { is_default: true });
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
