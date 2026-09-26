

interface WorthItLogoProps {
  height?: number;
  showTagline?: boolean;
  className?: string;
}

export default function WorthItLogo({ height, showTagline = false, className = "" }: WorthItLogoProps) {
  // We ignore the legacy 'height' prop and use responsive Tailwind classes
  // to ensure the logo scales correctly on mobile, tablet, and desktop
  // without pushing down page content.
  const isSidebar = height === 26; // Infer context from legacy props
  
  const sizeClasses = isSidebar 
    ? "h-5 md:h-6" // Sidebar logo size (compact)
    : "h-7 sm:h-8 md:h-10"; // Responsive Hero logo size

  return (
    <div className={`flex flex-col justify-center items-center ${className}`} style={{ width: 'fit-content' }}>
      <img 
        src="/logo-light.svg" 
        alt="Worth-It Logo" 
        className={`worthit-logo-light w-auto object-contain ${sizeClasses}`}
      />
      <img 
        src="/logo-dark.svg" 
        alt="Worth-It Logo" 
        className={`worthit-logo-dark w-auto object-contain ${sizeClasses}`}
      />
      {showTagline && (
        <span className="text-xs tracking-widest opacity-65 font-sans mt-1 text-center">
          Find the price worth buying.
        </span>
      )}
    </div>
  );
}
