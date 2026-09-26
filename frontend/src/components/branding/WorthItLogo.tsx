

interface WorthItLogoProps {
  height?: number;
  showTagline?: boolean;
  className?: string;
}

export default function WorthItLogo({ height = 32, showTagline = false, className = "" }: WorthItLogoProps) {
  // The new perfectly cropped SVGs have zero vertical padding.
  // The old inline SVG had massive vertical padding (~45% visual content).
  // To preserve the exact same visual sizing across the app without editing
  // every file that consumes this component, we scale the requested height.
  const effectiveHeight = Math.round(height * 0.5);

  return (
    <div className={`flex flex-col ${className}`} style={{ width: 'fit-content' }}>
      <img 
        src="/logo-light.svg" 
        alt="Worth-It Logo" 
        style={{ height: `${effectiveHeight}px`, width: 'auto' }} 
        className="block dark:hidden"
      />
      <img 
        src="/logo-dark.svg" 
        alt="Worth-It Logo" 
        style={{ height: `${effectiveHeight}px`, width: 'auto', mixBlendMode: 'screen' }} 
        className="hidden dark:block"
      />
      {showTagline && (
        <span className="text-xs tracking-widest opacity-65 font-sans mt-1 text-center">
          Find the price worth buying.
        </span>
      )}
    </div>
  );
}
