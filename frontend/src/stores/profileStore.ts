/**
 * Alpine.js Profile Store
 *
 * Reactive store for managing user profiles.
 * Works with both local (IndexedDB) and server storage transparently.
 *
 * KEY FEATURE: Uses localStorage cache for INSTANT initial load.
 * No "pop" effect because data is available synchronously.
 */
import Alpine from 'alpinejs';
import { profileStorage, isAuthenticated } from '@/storage/profileStorage';
import { migrationService } from '@/storage/migrationService';
import { profileCache } from '@/storage/localProfileRepo';
import type { Profile, ProfileFormData } from '@/types/profile';

/**
 * Profile store state interface
 */
export interface ProfileStoreState {
  profiles: Profile[];
  currentProfile: Profile | null;
  loading: boolean;
  error: string | null;
  isAuthenticated: boolean;

  // Actions
  init(): Promise<void>;
  loadProfiles(): Promise<void>;
  createProfile(data: ProfileFormData): Promise<Profile>;
  updateProfile(id: number, data: Partial<ProfileFormData>): Promise<void>;
  deleteProfile(id: number): Promise<void>;
  setDefault(id: number): Promise<void>;
  selectProfile(id: number): void;
  clearError(): void;
}

/**
 * Create and register the profile Alpine store
 *
 * INSTANT LOAD: Reads from localStorage cache (sync) immediately.
 * No loading state, no skeleton, no pop - data is there from the start.
 */
export function registerProfileStore(): void {
  // Read cached profiles SYNCHRONOUSLY - this is instant!
  const cachedProfiles = profileCache.get() as Profile[];
  const defaultProfile = cachedProfiles.find((p) => p.is_default);

  Alpine.store('profiles', {
    // Pre-populate with cached data - NO LOADING STATE!
    profiles: cachedProfiles,
    currentProfile: defaultProfile || cachedProfiles[0] || null,
    loading: false,  // Data already loaded from cache
    error: null as string | null,
    isAuthenticated: false,

    /**
     * Initialize store - verify cache and run migration if needed
     */
    async init() {
      this.isAuthenticated = isAuthenticated();

      // Run silent migration if authenticated
      if (this.isAuthenticated) {
        await migrationService.checkAndMigrate();
      }

      // Refresh from IndexedDB (source of truth) in background
      // This also syncs the localStorage cache
      await this.loadProfiles();
    },

    /**
     * Load all profiles from storage (IndexedDB).
     * Silent refresh - doesn't show loading state since we have cached data.
     */
    async loadProfiles() {
      // Don't set loading=true - we already have cached data showing
      this.error = null;

      try {
        const freshProfiles = await profileStorage.getAll();
        this.profiles = freshProfiles;

        // Set current profile to default or first available
        const defaultProfile = this.profiles.find((p) => p.is_default);
        this.currentProfile = defaultProfile || this.profiles[0] || null;
      } catch (err) {
        this.error = err instanceof Error ? err.message : 'Failed to load profiles';
        console.error('[ProfileStore] Load error:', err);
      }
      // Don't set loading=false - it's already false
    },

    /**
     * Create a new profile
     */
    async createProfile(data: ProfileFormData): Promise<Profile> {
      this.loading = true;
      this.error = null;

      try {
        const profile = await profileStorage.create(data);
        this.profiles = [...this.profiles, profile];

        // If this is the first profile, set it as current
        if (this.profiles.length === 1) {
          this.currentProfile = profile;
        }

        return profile;
      } catch (err) {
        this.error = err instanceof Error ? err.message : 'Failed to create profile';
        console.error('[ProfileStore] Create error:', err);
        throw err;
      } finally {
        this.loading = false;
      }
    },

    /**
     * Update an existing profile
     */
    async updateProfile(id: number, data: Partial<ProfileFormData>) {
      this.loading = true;
      this.error = null;

      try {
        const updated = await profileStorage.update(id, data);
        if (updated) {
          this.profiles = this.profiles.map((p) =>
            p.id === id ? updated : p
          );

          if (this.currentProfile?.id === id) {
            this.currentProfile = updated;
          }
        }
      } catch (err) {
        this.error = err instanceof Error ? err.message : 'Failed to update profile';
        console.error('[ProfileStore] Update error:', err);
        throw err;
      } finally {
        this.loading = false;
      }
    },

    /**
     * Delete a profile
     */
    async deleteProfile(id: number) {
      this.loading = true;
      this.error = null;

      try {
        await profileStorage.delete(id);
        this.profiles = this.profiles.filter((p) => p.id !== id);

        // If deleted profile was current, select another
        if (this.currentProfile?.id === id) {
          const defaultProfile = this.profiles.find((p) => p.is_default);
          this.currentProfile = defaultProfile || this.profiles[0] || null;
        }
      } catch (err) {
        this.error = err instanceof Error ? err.message : 'Failed to delete profile';
        console.error('[ProfileStore] Delete error:', err);
        throw err;
      } finally {
        this.loading = false;
      }
    },

    /**
     * Set a profile as default
     */
    async setDefault(id: number) {
      this.loading = true;
      this.error = null;

      try {
        await profileStorage.setDefault(id);

        // Update local state
        this.profiles = this.profiles.map((p) => ({
          ...p,
          is_default: p.id === id,
        }));
      } catch (err) {
        this.error = err instanceof Error ? err.message : 'Failed to set default';
        console.error('[ProfileStore] SetDefault error:', err);
        throw err;
      } finally {
        this.loading = false;
      }
    },

    /**
     * Select a profile as current (local only, doesn't persist)
     */
    selectProfile(id: number) {
      const profile = this.profiles.find((p) => p.id === id);
      if (profile) {
        this.currentProfile = profile;
      }
    },

    /**
     * Clear error state
     */
    clearError() {
      this.error = null;
    },
  } as ProfileStoreState);
}

/**
 * Type-safe accessor for the profile store
 */
export function getProfileStore(): ProfileStoreState {
  return Alpine.store('profiles') as ProfileStoreState;
}
