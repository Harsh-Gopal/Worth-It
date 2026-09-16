/**
 * WorthItLogo — canonical, theme-aware SVG logo component.
 *
 * The SVG uses currentColor for the wordmark and tagline so it adapts
 * to Light/Dark mode automatically. Brand mark colors (green V shapes,
 * red chevron) are hardcoded to preserve identity.
 *
 * Props:
 *   height   — rendered height in px (width scales proportionally)
 *   showTagline — whether to show the tagline (default: false for compact use)
 */

interface WorthItLogoProps {
  height?: number;
  showTagline?: boolean;
  className?: string;
}

export default function WorthItLogo({ height = 32, showTagline = false, className }: WorthItLogoProps) {
  // The SVG viewBox is 1200x360. When showTagline is false we crop to 1200x220 (mark + wordmark).
  const viewBox = showTagline ? "0 0 1200 360" : "0 0 1200 230";
  const aspectRatio = showTagline ? (1200 / 360) : (1200 / 230);
  const width = Math.round(height * aspectRatio);

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox={viewBox}
      width={width}
      height={height}
      role="img"
      aria-label="Worth-It"
      className={className}
      style={{ display: "block", flexShrink: 0 }}
    >
      <title>Worth-It</title>

      <g transform="translate(40 35)">

        {/* Left accent stroke: \ */}
        <path
          d="M 35 35 L 78 102"
          fill="none"
          stroke="currentColor"
          strokeWidth="20"
          strokeLinecap="round"
        />

        {/* Right accent stroke: / */}
        <path
          d="M 315 102 L 358 35"
          fill="none"
          stroke="currentColor"
          strokeWidth="20"
          strokeLinecap="round"
        />

        {/* First green V */}
        <path
          d="M 78 120 L 125 190 L 172 120"
          fill="none"
          stroke="#16a34a"
          strokeWidth="26"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Red upward caret */}
        <path
          d="M 135 92 L 175 40 L 215 92"
          fill="none"
          stroke="#dc2626"
          strokeWidth="24"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Second green V */}
        <path
          d="M 178 120 L 225 190 L 272 120"
          fill="none"
          stroke="#16a34a"
          strokeWidth="26"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Wordmark "orth" */}
        <text
          x="300"
          y="175"
          fontFamily="Inter, ui-sans-serif, system-ui, -apple-system, sans-serif"
          fontSize="112"
          fontWeight="700"
          letterSpacing="-5"
          fill="currentColor"
        >
          orth
        </text>

        {/* Hyphen */}
        <text
          x="620"
          y="175"
          fontFamily="Inter, ui-sans-serif, system-ui, -apple-system, sans-serif"
          fontSize="105"
          fontWeight="700"
          fill="currentColor"
        >
          -
        </text>

        {/* "It" */}
        <text
          x="690"
          y="175"
          fontFamily="Inter, ui-sans-serif, system-ui, -apple-system, sans-serif"
          fontSize="112"
          fontWeight="700"
          letterSpacing="-5"
          fill="currentColor"
        >
          It
        </text>

        {/* Tagline — only rendered when showTagline=true */}
        {showTagline && (
          <text
            x="350"
            y="250"
            fontFamily="Inter, ui-sans-serif, system-ui, -apple-system, sans-serif"
            fontSize="28"
            fontWeight="400"
            letterSpacing="8"
            fill="currentColor"
            opacity="0.55"
          >
            Find the price worth buying.
          </text>
        )}
      </g>
    </svg>
  );
}
