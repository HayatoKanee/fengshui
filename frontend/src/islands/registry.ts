/**
 * React Islands Registry
 *
 * Register all React components that should be available as Islands here.
 * Components registered here can be used in Django templates with:
 *
 * <div data-island="ComponentName" data-props='{"prop": "value"}'></div>
 */

import { registerIsland } from './index';

// Import React components
import { Counter } from '@components/Counter';

// Register components as Islands
export function registerAllIslands(): void {
  registerIsland('Counter', Counter);

  // Add more component registrations here:
  // registerIsland('Calendar', Calendar);
  // registerIsland('BaziChart', BaziChart);
  // registerIsland('WuxingWheel', WuxingWheel);
}
