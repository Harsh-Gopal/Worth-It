

interface WorthItLogoProps {
  height?: number;
  showTagline?: boolean;
  className?: string;
}

export default function WorthItLogo({ height = 32, showTagline = false, className = "" }: WorthItLogoProps) {
  return (
    <div className={`flex flex-col ${className}`} style={{ width: 'fit-content' }}>
      <img 
        src="/logo-light.svg" 
        alt="Worth-It Logo" 
        style={{ height: `${height}px`, width: 'auto', display: 'block' }} 
        className="dark:hidden"
      />
      <img 
        src="/logo-dark.svg" 
        alt="Worth-It Logo" 
        style={{ height: `${height}px`, width: 'auto', display: 'block', mixBlendMode: 'screen' }} 
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
