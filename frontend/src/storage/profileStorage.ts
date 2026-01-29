/**
 * Local-First Profile Storage
 *
 * Architecture: LOCAL-FIRST
 * - Everyone ALWAYS reads/writes to local IndexedDB
 * - Sync happens via migrationService on page load (when authenticated)
 * - This gives offline-first capability with cloud backup
 */
import { localProfileRepo } from './localProfileRepo';
import type { ProfileFormData } from '@/types/profile';

/**
 * Check if the current user is authenticated
 */
export function isAuthenticated(): boolean {
  return document.body.dataset.userAuthenticated === 'true';
}

/**
 * Profile storage - always uses local IndexedDB
 * Sync to server is handled separately by migrationService
 */
export const profileStorage = {
  getAll: () => localProfileRepo.getAll(),
  getById: (id: number) => localProfileRepo.getById(id),
  getDefault: () => localProfileRepo.getDefault(),
  create: (data: ProfileFormData) => localProfileRepo.create(data),
  update: (id: number, data: Partial<ProfileFormData>) => localProfileRepo.update(id, data),
  delete: (id: number) => localProfileRepo.delete(id),
  setDefault: (id: number) => localProfileRepo.setDefault(id),

  async hasProfiles(): Promise<boolean> {
    return (await this.getAll()).length > 0;
  },

  async count(): Promise<number> {
    return (await this.getAll()).length;
  },
};
