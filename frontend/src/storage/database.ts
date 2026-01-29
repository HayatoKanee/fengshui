/**
 * Dexie.js database for local profile storage
 * Used when user is not authenticated
 */
import Dexie, { type Table } from 'dexie';
import type { LocalProfile } from '@/types/profile';

/**
 * Feng Shui IndexedDB database
 */
class FengshuiDB extends Dexie {
  profiles!: Table<LocalProfile>;

  constructor() {
    super('fengshui');

    this.version(1).stores({
      // id is auto-increment (++), localId and is_default are indexed
      profiles: '++id, localId, is_default, created_at',
    });
  }
}

// Singleton database instance
export const db = new FengshuiDB();
