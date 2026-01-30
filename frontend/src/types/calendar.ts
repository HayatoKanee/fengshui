/**
 * Calendar Types
 *
 * Types for calendar data received from Django backend.
 */

// Profile from IndexedDB/localStorage
export interface Profile {
  id: number;
  name: string;
  birth_year: number;
  birth_month: number;
  birth_day: number;
  birth_hour: number;
  birth_minute: number;
  is_male: boolean | number | string;
  is_default: boolean | number;
}

// Day reason from server
export interface DayReason {
  type: 'good' | 'bad' | 'neutral';
  text: string;
}

// Config from DOM data attributes
export interface CalendarConfig {
  csrfToken: string;
  initialYear: number;
  initialMonth: number;
  baziDetailUrl: string;
}

// FullCalendar instance (loaded via CDN)
export interface FullCalendarInstance {
  render(): void;
  getDate(): Date;
  gotoDate(date: string): void;
}
