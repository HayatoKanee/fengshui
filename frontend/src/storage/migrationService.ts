/**
 * Bidirectional Sync Service
 *
 * Syncs profiles between local (IndexedDB) and server when user logs in.
 *
 * Strategy:
 * - Everyone ALWAYS uses local storage (IndexedDB)
 * - When logged in, sync happens bidirectionally:
 *   - Local-only profiles → upload to server
 *   - Server-only profiles → download to local
 * - This gives offline-first capability with cloud backup
 */
import { localProfileRepo } from './localProfileRepo';
import { serverProfileApi } from './serverProfileApi';
import { isAuthenticated } from './profileStorage';
import type { LocalProfile, ServerProfile } from '@/types/profile';

/**
 * Sync status for debugging
 */
export type SyncStatus =
  | 'not_authenticated'
  | 'synced'
  | 'error';

export interface SyncResult {
  status: SyncStatus;
  uploaded: number;
  downloaded: number;
  error?: string;
}

/**
 * Check if two profiles represent the same person (same birth data)
 */
function isSamePerson(a: LocalProfile, b: ServerProfile): boolean {
  return (
    a.birth_year === b.birth_year &&
    a.birth_month === b.birth_month &&
    a.birth_day === b.birth_day &&
    a.birth_hour === b.birth_hour &&
    a.is_male === b.is_male
  );
}

/**
 * Sync service for bidirectional profile sync
 */
export const migrationService = {
  /**
   * Bidirectional sync between local and server.
   * - Uploads local-only profiles to server
   * - Downloads server-only profiles to local
   *
   * Called on page load when user is authenticated.
   */
  async checkAndMigrate(): Promise<SyncResult> {
    if (!isAuthenticated()) {
      return { status: 'not_authenticated', uploaded: 0, downloaded: 0 };
    }

    try {
      // Get both local and server profiles
      const [localProfiles, serverProfiles] = await Promise.all([
        localProfileRepo.getAllRaw(),
        serverProfileApi.getAll(),
      ]);

      let uploaded = 0;
      let downloaded = 0;

      // Find local profiles not on server (upload them)
      const localOnlyProfiles = localProfiles.filter(
        (local) => !serverProfiles.some((server) => isSamePerson(local, server))
      );

      if (localOnlyProfiles.length > 0) {
        await serverProfileApi.batchCreate(localOnlyProfiles);
        uploaded = localOnlyProfiles.length;
        console.debug(`[Sync] Uploaded ${uploaded} profiles to server`);
      }

      // Find server profiles not in local (download them)
      const serverOnlyProfiles = serverProfiles.filter(
        (server) => !localProfiles.some((local) => isSamePerson(local, server))
      );

      for (const serverProfile of serverOnlyProfiles) {
        await localProfileRepo.create({
          name: serverProfile.name,
          birth_year: serverProfile.birth_year,
          birth_month: serverProfile.birth_month,
          birth_day: serverProfile.birth_day,
          birth_hour: serverProfile.birth_hour,
          birth_minute: serverProfile.birth_minute,
          is_male: serverProfile.is_male,
        });
        downloaded++;
      }

      if (downloaded > 0) {
        console.debug(`[Sync] Downloaded ${downloaded} profiles from server`);
      }

      return { status: 'synced', uploaded, downloaded };
    } catch (error) {
      console.error('[Sync] Failed to sync profiles:', error);
      return {
        status: 'error',
        uploaded: 0,
        downloaded: 0,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  },
};
