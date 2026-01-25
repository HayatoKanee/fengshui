/**
 * FengShui Frontend - Modern Stack
 *
 * Stack: Vite + TypeScript + HTMX + Alpine.js + Tailwind CSS + DaisyUI
 *
 * This is the main entry point that initializes:
 * - HTMX for hypermedia-driven interactions
 * - Alpine.js for reactive UI components
 * - View Transitions API for smooth navigation
 */

// Import HTMX
import htmx from 'htmx.org';

// Import Alpine.js
import Alpine from 'alpinejs';

// Import styles
import './styles.css';

// Import profile store registration
import { registerProfileStore, getProfileStore } from './stores/profileStore';

// Import React Islands system (lazy loaded to prevent blocking Alpine.js)
import { mountIslands, registerIsland, islandRegistry } from './islands';
// Note: registerAllIslands is loaded dynamically to prevent React errors from blocking Alpine

// ============================================================================
// HTMX Configuration
// ============================================================================

// Make htmx globally available
window.htmx = htmx;

// Configure HTMX
htmx.config.historyCacheSize = 0;
htmx.config.refreshOnHistoryMiss = true;
htmx.config.defaultSwapStyle = 'innerHTML';

// HTMX CSRF Token handling for Django
document.body.addEventListener('htmx:configRequest', (event: Event) => {
  const customEvent = event as CustomEvent;
  const csrfToken = document.querySelector<HTMLInputElement>('[name=csrfmiddlewaretoken]')?.value
    || getCookie('csrftoken');

  if (csrfToken) {
    customEvent.detail.headers['X-CSRFToken'] = csrfToken;
  }
});

// HTMX loading indicators
document.body.addEventListener('htmx:beforeRequest', () => {
  document.body.classList.add('htmx-request');
});

document.body.addEventListener('htmx:afterRequest', () => {
  document.body.classList.remove('htmx-request');
});

// HTMX error handling
document.body.addEventListener('htmx:responseError', (event: Event) => {
  const customEvent = event as CustomEvent;
  console.error('HTMX Error:', customEvent.detail);

  // Show error toast if Alpine store is available
  const toastStore = window.Alpine?.store('toast') as { show: (type: string, message: string) => void } | undefined;
  if (toastStore) {
    toastStore.show('error', 'Request failed. Please try again.');
  }
});

// ============================================================================
// View Transitions API
// ============================================================================

// Enable smooth page transitions for HTMX navigation
if ('startViewTransition' in document) {
  htmx.config.globalViewTransitions = true;

  document.body.addEventListener('htmx:beforeSwap', (event: Event) => {
    const customEvent = event as CustomEvent;
    // Only apply view transitions for larger content swaps
    if (customEvent.detail.target === document.body ||
        customEvent.detail.target.id === 'main-content') {
      customEvent.detail.shouldTransition = true;
    }
  });
}

// ============================================================================
// Alpine.js Configuration
// ============================================================================

// Make Alpine globally available before starting
window.Alpine = Alpine;

// Global Alpine stores
Alpine.store('theme', {
  dark: localStorage.getItem('theme') === 'fengshui-dark',

  toggle() {
    this.dark = !this.dark;
    this.apply();
  },

  apply() {
    const theme = this.dark ? 'fengshui-dark' : 'fengshui-light';
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  },

  init() {
    this.apply();
  }
});

Alpine.store('lang', {
  current: localStorage.getItem('lang') || 'zh',

  set(lang: string) {
    this.current = lang;
    localStorage.setItem('lang', lang);
  }
});

Alpine.store('toast', {
  visible: false,
  message: '',
  type: 'info',
  timeout: null as ReturnType<typeof setTimeout> | null,

  show(type: string, message: string, duration = 5000) {
    this.type = type;
    this.message = message;
    this.visible = true;

    if (this.timeout) clearTimeout(this.timeout);
    this.timeout = setTimeout(() => {
      this.visible = false;
    }, duration);
  },

  hide() {
    this.visible = false;
    if (this.timeout) clearTimeout(this.timeout);
  }
});

// ============================================================================
// Alpine Components
// ============================================================================

// Modal component
Alpine.data('modal', () => ({
  open: false,
  content: '',
  title: '',

  show(title: string, content: string) {
    this.title = title;
    this.content = content;
    this.open = true;
  },

  close() {
    this.open = false;
    this.content = '';
    this.title = '';
  }
}));

// Dropdown component with accessibility
Alpine.data('dropdown', () => ({
  open: false,

  toggle() {
    this.open = !this.open;
  },

  close() {
    this.open = false;
  },

  handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape') {
      this.close();
    }
  }
}));

// BaZi save component - handles async save with proper reactivity
Alpine.data('baziSaveComponent', () => ({
  saved: false,
  saving: false,
  birthData: null as {
    name: string;
    birth_year: number;
    birth_month: number;
    birth_day: number;
    birth_hour: number;
    birth_minute: number;
    is_male: boolean;
  } | null,

  initBirthData(year: number, month: number, day: number, hour: number, minute: number, isMale: boolean) {
    this.birthData = {
      name: '我的八字',
      birth_year: year,
      birth_month: month,
      birth_day: day,
      birth_hour: hour,
      birth_minute: minute,
      is_male: isMale
    };
  },

  async saveProfile() {
    return this.saveProfileWithName('我的八字');
  },

  async saveProfileWithName(name: string) {
    if (this.saving || this.saved || !this.birthData) {
      return;
    }

    this.saving = true;

    try {
      const profileData = { ...this.birthData, name };
      const store = Alpine.store('profiles') as { createProfile: (data: typeof profileData) => Promise<unknown> };
      await store.createProfile(profileData);
      this.saved = true;

      const toast = Alpine.store('toast') as { show: (type: string, msg: string) => void };
      toast.show('success', '已保存八字资料');
    } catch (e) {
      console.error('Profile save failed:', e);
      const toast = Alpine.store('toast') as { show: (type: string, msg: string) => void };
      toast.show('error', '保存失败');
    } finally {
      this.saving = false;
    }
  }
}));

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Get cookie value by name (for CSRF token)
 */
function getCookie(name: string): string | null {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop()?.split(';').shift() || null;
  }
  return null;
}

// ============================================================================
// Initialize
// ============================================================================

// Start Alpine when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
  // Register profile store BEFORE Alpine.start()
  registerProfileStore();

  // Initialize theme
  const themeStore = Alpine.store('theme') as { init: () => void };
  themeStore.init();

  // Start Alpine FIRST (critical for page functionality)
  Alpine.start();
  console.log('Alpine.js initialized');

  // Initialize profile store (runs silent migration if authenticated)
  try {
    const profileStore = getProfileStore();
    await profileStore.init();
    console.log('Profile store initialized');
  } catch (error) {
    console.warn('Profile store initialization failed:', error);
  }

  // Register React Island components (non-blocking, loaded after Alpine)
  try {
    const { registerAllIslands } = await import('./islands/registry');
    registerAllIslands();
    console.log('React Islands registered');
  } catch (error) {
    console.warn('React Islands failed to load (non-critical):', error);
  }

  console.log('FengShui Frontend initialized');
  console.log('Stack: Vite + TypeScript + HTMX + Alpine.js + React Islands');
});

// Export for potential module usage
export { Alpine, htmx, registerIsland, mountIslands, islandRegistry };
export { registerProfileStore, getProfileStore } from './stores/profileStore';
export { profileStorage, isAuthenticated } from './storage/profileStorage';
