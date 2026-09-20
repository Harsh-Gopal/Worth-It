import React from 'react';

export function ElectronicsFallback({ className, style }: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
      <rect x="5" y="3" width="14" height="18" rx="2" ry="2" />
      <path d="M12 17h.01M9 6h6" />
    </svg>
  );
}
