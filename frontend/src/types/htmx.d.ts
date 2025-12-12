declare module 'htmx.org' {
  interface HtmxConfig {
    historyEnabled?: boolean;
    historyCacheSize?: number;
    refreshOnHistoryMiss?: boolean;
    defaultSwapStyle?: string;
    defaultSwapDelay?: number;
    defaultSettleDelay?: number;
    includeIndicatorStyles?: boolean;
    indicatorClass?: string;
    requestClass?: string;
    addedClass?: string;
    settlingClass?: string;
    swappingClass?: string;
    allowEval?: boolean;
    allowScriptTags?: boolean;
    inlineScriptNonce?: string;
    useTemplateFragments?: boolean;
    wsReconnectDelay?: string;
    wsBinaryType?: string;
    disableSelector?: string;
    withCredentials?: boolean;
    timeout?: number;
    scrollBehavior?: string;
    defaultFocusScroll?: boolean;
    getCacheBusterParam?: boolean;
    globalViewTransitions?: boolean;
    methodsThatUseUrlParams?: string[];
    selfRequestsOnly?: boolean;
    ignoreTitle?: boolean;
    scrollIntoViewOnBoost?: boolean;
    triggerSpecsCache?: unknown;
  }

  interface Htmx {
    config: HtmxConfig;
    process(element: Element): void;
    on(event: string, callback: (event: Event) => void): void;
    off(event: string, callback: (event: Event) => void): void;
    trigger(element: Element, event: string, detail?: object): void;
    ajax(
      method: string,
      url: string,
      options?: {
        source?: Element;
        event?: Event;
        handler?: (element: Element, response: string) => void;
        target?: string | Element;
        swap?: string;
        values?: object;
        headers?: object;
      }
    ): void;
    find(selector: string): Element | null;
    findAll(selector: string): NodeListOf<Element>;
    closest(element: Element, selector: string): Element | null;
    remove(element: Element): void;
    addClass(element: Element, className: string): void;
    removeClass(element: Element, className: string): void;
    toggleClass(element: Element, className: string): void;
    takeClass(element: Element, className: string): void;
    swap(
      target: Element,
      content: string,
      swapSpec?: {
        swapStyle?: string;
        swapDelay?: number;
        settleDelay?: number;
      }
    ): void;
    defineExtension(name: string, extension: object): void;
    removeExtension(name: string): void;
    logAll(): void;
    logNone(): void;
    version: string;
  }

  const htmx: Htmx;
  export = htmx;
}
