/**
 * Example React Island Component - Counter
 *
 * Usage in Django templates:
 * <div data-island="Counter" data-props='{"initialCount": 0, "label": "计数器"}'></div>
 */

import { useState } from 'react';

interface CounterProps {
  initialCount?: number;
  label?: string;
}

export function Counter({ initialCount = 0, label = 'Counter' }: CounterProps) {
  const [count, setCount] = useState(initialCount);

  return (
    <div className="card bg-base-100 shadow-xl p-4">
      <h3 className="text-lg font-bold mb-2">{label}</h3>
      <div className="flex items-center gap-4">
        <button
          className="btn btn-circle btn-outline btn-sm"
          onClick={() => setCount(c => c - 1)}
          aria-label="Decrease"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        </button>
        <span className="text-2xl font-mono tabular-nums w-16 text-center">{count}</span>
        <button
          className="btn btn-circle btn-outline btn-sm"
          onClick={() => setCount(c => c + 1)}
          aria-label="Increase"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </div>
      <button
        className="btn btn-ghost btn-xs mt-2"
        onClick={() => setCount(initialCount)}
      >
        重置
      </button>
    </div>
  );
}

export default Counter;
