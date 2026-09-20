import React from 'react';

export function FreshFallback({ className, style }: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
      <path d="M12 20a8 8 0 1 0 0-16 8 8 0 0 0 0 16zM12 4v4M12 8s2-3 4-3" />
    </svg>
  );
}
