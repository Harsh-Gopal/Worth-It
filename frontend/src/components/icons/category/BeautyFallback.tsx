import React from 'react';

export function BeautyFallback({ className, style }: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className} style={style}>
      <path d="M8 8h8v12a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2V8zM10 8V5a2 2 0 0 1 2-2h0a2 2 0 0 1 2 2v3M9 13h6M9 17h6" />
    </svg>
  );
}
