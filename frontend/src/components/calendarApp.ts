/**
 * Calendar App Component
 *
 * Thin Alpine.js component - just fetches data from server and displays it.
 * ALL business logic is handled by Django backend.
 */
import { STORAGE_KEYS, API } from '../constants';
import type {
  Profile,
  DayReason,
  CalendarConfig,
  FullCalendarInstance,
} from '../types/calendar';

// =============================================================================
// Configuration
// =============================================================================

function readConfig(): CalendarConfig {
  const el = document.querySelector('[data-calendar-config]');
  return {
    csrfToken: el?.getAttribute('data-csrf-token') || '',
    initialYear: Number(el?.getAttribute('data-initial-year')) || new Date().getFullYear(),
    initialMonth: Number(el?.getAttribute('data-initial-month')) || new Date().getMonth() + 1,
    baziDetailUrl: el?.getAttribute('data-bazi-detail-url') || '/bazi/detail/',
  };
}

// =============================================================================
// Calendar App Factory
// =============================================================================

export function calendarApp() {
  const config = readConfig();

  return {
    // UI State
    showModal: false,
    modalTitle: '',
    modalContent: '',
    isLoading: false,
    alertMessage: '',
    alertType: 'warning' as 'warning' | 'error',

    // Calendar
    calendar: null as FullCalendarInstance | null,
    isInitializing: true,

    // Data from server (no client-side processing)
    days: {} as Record<string, { quality: string; score: number; reasons: DayReason[] }>,

    // Profile
    profiles: [] as Profile[],
    selectedProfile: null as Profile | null,

    // Computed
    get selectedProfileName() {
      return this.selectedProfile?.name || '选择资料';
    },
    get selectedProfileId() {
      return this.selectedProfile?.id || null;
    },

    // =========================================================================
    // Lifecycle
    // =========================================================================

    async init() {
      this.loadProfiles();
      this.initCalendar();
    },

    // =========================================================================
    // Profiles (from localStorage cache)
    // =========================================================================

    loadProfiles() {
      try {
        const cached = localStorage.getItem(STORAGE_KEYS.PROFILES_CACHE);
        this.profiles = cached ? JSON.parse(cached) : [];
      } catch {
        this.profiles = [];
      }

      // Select default
      const defaultProfile = this.profiles.find(p => p.is_default) || this.profiles[0];
      if (defaultProfile) this.selectProfile(defaultProfile);
    },

    selectProfile(profile: Profile) {
      this.selectedProfile = profile;
      (document.activeElement as HTMLElement)?.blur();

      if (this.calendar && !this.isInitializing) {
        const date = this.calendar.getDate();
        this.fetchMonthData(date.getFullYear(), date.getMonth() + 1);
      }
    },

    // =========================================================================
    // Calendar Setup
    // =========================================================================

    initCalendar() {
      const el = document.getElementById('calendar');
      if (!el) return;

      this.calendar = new FullCalendar.Calendar(el, {
        headerToolbar: { left: 'prev,next today', center: 'title', right: 'dayGridMonth' },
        initialView: 'dayGridMonth',
        locale: 'zh-cn',
        initialDate: `${config.initialYear}-${String(config.initialMonth).padStart(2, '0')}-01`,
        height: 'auto',

        dateClick: (info: { dateStr: string }) => this.showDayDetails(info.dateStr),

        datesSet: () => {
          if (this.isInitializing) {
            this.isInitializing = false;
            return;
          }
          if (!this.calendar) return;
          const date = this.calendar.getDate();
          this.fetchMonthData(date.getFullYear(), date.getMonth() + 1);
        },

        dayCellContent: (args: { dayNumberText: string; date: Date }) => {
          const dateStr = this.formatDate(args.date);
          const day = this.days[dateStr];

          const container = document.createElement('div');
          container.className = 'day-content';

          const dot = document.createElement('span');
          dot.className = `quality-dot ${this.getDotClass(day?.quality)}`;
          container.appendChild(dot);

          const num = document.createElement('span');
          num.className = 'date-number';
          num.textContent = args.dayNumberText;
          container.appendChild(num);

          return { domNodes: [container] };
        },
      });

      this.calendar.render();
      this.isInitializing = false;
      this.fetchMonthData(config.initialYear, config.initialMonth);
    },

    // =========================================================================
    // Data Fetching (Server does all the work)
    // =========================================================================

    async fetchMonthData(year: number, month: number) {
      if (!this.selectedProfile) {
        this.alertMessage = '请先选择一个八字资料';
        this.alertType = 'warning';
        return;
      }

      this.isLoading = true;
      this.alertMessage = '';
      this.days = {};

      // Load current month + adjacent months
      const months = this.getMonthRange(year, month);

      try {
        await Promise.all(months.map(m => this.fetchSingleMonth(m.year, m.month)));
        this.updateDots();
      } catch (e) {
        this.alertMessage = '加载失败，请稍后再试';
        this.alertType = 'error';
      } finally {
        this.isLoading = false;
      }
    },

    async fetchSingleMonth(year: number, month: number) {
      const form = new FormData();
      form.append('year', String(year));
      form.append('month', String(month));
      form.append('csrfmiddlewaretoken', config.csrfToken);

      // Send profile birth data
      const p = this.selectedProfile!;
      form.append('birth_year', String(p.birth_year));
      form.append('birth_month', String(p.birth_month));
      form.append('birth_day', String(p.birth_day));
      form.append('birth_hour', String(p.birth_hour));
      form.append('birth_minute', String(p.birth_minute || 0));
      form.append('is_male', p.is_male ? 'true' : 'false');

      const res = await fetch(API.CALENDAR_DATA, { method: 'POST', body: form });
      if (!res.ok) throw new Error('Failed to fetch');

      const data = await res.json();

      // Store server response directly (no client-side processing)
      for (const day of data.days) {
        const dateStr = this.formatDate(new Date(year, month - 1, day.day));
        this.days[dateStr] = {
          quality: day.overall_quality || 'neutral',
          score: day.score ?? 0,
          reasons: day.reasons || [],
        };
      }
    },

    // =========================================================================
    // UI Updates
    // =========================================================================

    updateDots() {
      document.querySelectorAll('.fc-daygrid-day').forEach(cell => {
        const dateStr = cell.getAttribute('data-date');
        if (!dateStr) return;

        const day = this.days[dateStr];
        const dot = cell.querySelector('.quality-dot');
        if (dot) {
          dot.className = `quality-dot ${this.getDotClass(day?.quality)}`;
        }
      });
    },

    showDayDetails(dateStr: string) {
      if (!this.selectedProfile) {
        this.alertMessage = '请先选择一个八字资料';
        return;
      }

      const day = this.days[dateStr];
      if (!day) return;

      const [y, m, d] = dateStr.split('-');
      const label = this.getQualityLabel(day.quality);

      let html = `
        <div class="text-center">
          <h3 class="text-2xl font-bold">${y}年${Number(m)}月${Number(d)}日</h3>
          <h4 class="text-xl ${label.css} mt-2">${label.text} (评分: ${day.score.toFixed(1)})</h4>
        </div>
      `;

      if (day.reasons.length > 0) {
        html += '<div class="mt-4"><h5 class="font-semibold mb-2">吉凶因素:</h5><ul class="space-y-1">';
        for (const r of day.reasons) {
          const alertClass = r.type === 'good' ? 'alert-success' : r.type === 'bad' ? 'alert-error' : '';
          html += `<li class="alert ${alertClass} py-2 text-sm">${r.text}</li>`;
        }
        html += '</ul></div>';
      }

      this.modalTitle = '日期详情';
      this.modalContent = html;
      this.showModal = true;
    },

    // =========================================================================
    // Helpers (minimal, display-only)
    // =========================================================================

    formatDate(date: Date): string {
      const y = date.getFullYear();
      const m = String(date.getMonth() + 1).padStart(2, '0');
      const d = String(date.getDate()).padStart(2, '0');
      return `${y}-${m}-${d}`;
    },

    getMonthRange(year: number, month: number) {
      const prev = month === 1 ? { year: year - 1, month: 12 } : { year, month: month - 1 };
      const next = month === 12 ? { year: year + 1, month: 1 } : { year, month: month + 1 };
      return [prev, { year, month }, next];
    },

    // Server tells us the quality - we just map to CSS class
    getDotClass(quality?: string): string {
      switch (quality) {
        case 'excellent':
        case 'good': return 'good-dot';
        case 'terrible':
        case 'bad': return 'bad-dot';
        default: return 'neutral-dot';
      }
    },

    // Server tells us quality - we just map to display text
    getQualityLabel(quality: string): { text: string; css: string } {
      switch (quality) {
        case 'excellent': return { text: '大吉', css: 'text-error font-bold' };
        case 'good': return { text: '吉日', css: 'text-error font-bold' };
        case 'terrible': return { text: '大凶', css: 'text-neutral font-bold' };
        case 'bad': return { text: '黑日', css: 'text-neutral font-bold' };
        default: return { text: '平日', css: 'text-base-content/70' };
      }
    },
  };
}

export default calendarApp;
