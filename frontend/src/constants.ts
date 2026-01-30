/**
 * Frontend Constants
 *
 * Minimal constants for the thin frontend layer.
 * Business logic constants are in Django backend.
 */

// Storage Keys
export const STORAGE_KEYS = {
  PROFILES_CACHE: 'profiles_cache',
  CURRENT_BAZI_PROFILE: 'currentBaziProfileId',
  THEME: 'theme',
  LANG: 'lang',
} as const;

// API Endpoints
export const API = {
  CALENDAR_DATA: '/calendar/data/',
  PROFILES: '/api/profiles/',
  BAZI_DETAIL: '/bazi/detail/',
} as const;
