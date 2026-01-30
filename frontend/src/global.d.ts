/**
 * Global type declarations
 */

import type Alpine from 'alpinejs';

// Extend Window with global variables
declare global {
  interface Window {
    Alpine: typeof Alpine;
    htmx: unknown;
    // Calendar app factory function
    calendarApp: () => unknown;
  }

  // FullCalendar loaded via CDN
  const FullCalendar: {
    Calendar: new (el: HTMLElement, options: unknown) => {
      render(): void;
      getDate(): Date;
      gotoDate(date: string): void;
    };
  };
}

export {};
