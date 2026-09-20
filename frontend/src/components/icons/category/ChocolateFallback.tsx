import React from 'react';

export function ChocolateFallback({ className, style }: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
      <rect x="6" y="4" width="12" height="16" rx="1" ry="1" />
      <path d="M6 10h12M6 16h12M12 4v16" />
    </svg>
  );
}
