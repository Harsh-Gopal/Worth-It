import React from 'react';

export function ProteinFallback({ className, style }: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
      <path d="M6 5h12M7 5v13a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V5M9 5V3a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2M8 10h8M8 15h8" />
    </svg>
  );
}
