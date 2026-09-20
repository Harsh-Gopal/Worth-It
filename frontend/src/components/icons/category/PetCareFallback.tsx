import React from 'react';

export function PetCareFallback({ className, style }: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
      <path d="M12 11a3.5 3.5 0 0 1-3.5 3.5h-1A3.5 3.5 0 0 1 4 11V9a3.5 3.5 0 0 1 3.5-3.5h1A3.5 3.5 0 0 1 12 9v2zM20 11a3.5 3.5 0 0 1-3.5 3.5h-1A3.5 3.5 0 0 1 12 11V9a3.5 3.5 0 0 1 3.5-3.5h1A3.5 3.5 0 0 1 20 9v2zM12 18.5a4.5 4.5 0 0 1-4.5-4.5v-1a4.5 4.5 0 0 1 4.5-4.5h0a4.5 4.5 0 0 1 4.5 4.5v1a4.5 4.5 0 0 1-4.5 4.5z" />
    </svg>
  );
}
