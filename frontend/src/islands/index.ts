/**
 * React Islands - Mount React components into Django templates
 *
 * Usage in Django templates:
 * <div data-island="Calendar" data-props='{"year": 2025}'></div>
 */

import { createRoot, type Root } from 'react-dom/client';
import { type ComponentType, createElement, StrictMode } from 'react';

// Registry of available React Island components
const islandRegistry: Map<string, ComponentType<Record<string, unknown>>> = new Map();

// Track mounted roots for cleanup
const mountedRoots: Map<Element, Root> = new Map();

/**
 * Register a React component as an Island
 */
export function registerIsland(name: string, component: ComponentType<Record<string, unknown>>): void {
  islandRegistry.set(name, component);
}

/**
 * Mount all React Islands found in the DOM
 */
export function mountIslands(): void {
  const islands = document.querySelectorAll<HTMLElement>('[data-island]');

  islands.forEach((element) => {
    const componentName = element.dataset.island;
    if (!componentName) return;

    const Component = islandRegistry.get(componentName);
    if (!Component) {
      console.warn(`React Island "${componentName}" not found in registry`);
      return;
    }

    // Parse props from data attribute
    let props: Record<string, unknown> = {};
    try {
      const propsJson = element.dataset.props;
      if (propsJson) {
        props = JSON.parse(propsJson);
      }
    } catch (e) {
      console.error(`Failed to parse props for Island "${componentName}":`, e);
    }

    // Mount the component
    try {
      const root = createRoot(element);
      root.render(
        createElement(StrictMode, null,
          createElement(Component, props)
        )
      );
      mountedRoots.set(element, root);
    } catch (e) {
      console.error(`Failed to mount Island "${componentName}":`, e);
    }
  });
}

/**
 * Unmount all React Islands (useful for cleanup)
 */
export function unmountIslands(): void {
  mountedRoots.forEach((root) => {
    root.unmount();
  });
  mountedRoots.clear();
}

/**
 * Remount islands (useful after HTMX swaps)
 */
export function remountIslands(): void {
  // Only mount new islands, don't unmount existing ones
  mountIslands();
}

// Auto-mount islands on DOMContentLoaded
if (typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', mountIslands);

  // Re-mount islands after HTMX swaps new content
  document.addEventListener('htmx:afterSwap', (event) => {
    const target = (event as CustomEvent).detail?.target;
    if (target) {
      // Mount islands within the swapped content
      const newIslands = target.querySelectorAll?.('[data-island]');
      newIslands?.forEach((element: HTMLElement) => {
        if (!mountedRoots.has(element)) {
          const componentName = element.dataset.island;
          if (!componentName) return;

          const Component = islandRegistry.get(componentName);
          if (!Component) return;

          let props: Record<string, unknown> = {};
          try {
            const propsJson = element.dataset.props;
            if (propsJson) props = JSON.parse(propsJson);
          } catch { /* ignore */ }

          const root = createRoot(element);
          root.render(createElement(StrictMode, null, createElement(Component, props)));
          mountedRoots.set(element, root);
        }
      });
    }
  });
}

export { islandRegistry };
