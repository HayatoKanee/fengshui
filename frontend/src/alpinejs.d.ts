declare module 'alpinejs' {
  interface Alpine {
    version: string;
    store<T>(name: string, value?: T): T;
    data<T>(name: string, callback: () => T): void;
    start(): void;
    plugin(plugin: (Alpine: Alpine) => void): void;
    magic(name: string, callback: (el: Element) => unknown): void;
    directive(
      name: string,
      callback: (
        el: Element,
        directive: { value: string; modifiers: string[]; expression: string },
        utilities: { Alpine: Alpine; effect: (callback: () => void) => void; cleanup: (callback: () => void) => void }
      ) => void
    ): void;
    bind(name: string, callback: () => Record<string, unknown>): void;
    evaluate<T>(el: Element, expression: string, extras?: Record<string, unknown>): T;
    reactive<T extends object>(obj: T): T;
    effect(callback: () => void): void;
    raw<T>(obj: T): T;
    mutateDom(callback: () => void): void;
    prefixed(name: string): string;
    prefix: string;
  }

  const Alpine: Alpine;
  export default Alpine;
  export { Alpine };
}
