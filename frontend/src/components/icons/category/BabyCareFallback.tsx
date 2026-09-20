import React from 'react';

export function BabyCareFallback({ className, style }: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
      <path d="M10 11h4M12 11v6M9 17h6M9 7h6a2 2 0 0 1 2 2v2H7V9a2 2 0 0 1 2-2zM12 7V4M10 4h4" />
    </svg>
  );
}
