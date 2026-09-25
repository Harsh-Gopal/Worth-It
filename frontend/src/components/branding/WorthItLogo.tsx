import React from "react";

interface WorthItLogoProps {
  height?: number;
  showTagline?: boolean;
  className?: string;
}

export default function WorthItLogo({ height = 32, showTagline = false, className }: WorthItLogoProps) {
  const vbW = 1200;
  const vbH = 360;
  const aspectRatio = vbW / vbH;
  const computedWidth = Math.round(height * aspectRatio);

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox={`0 0 ${vbW} ${vbH}`}
      width={computedWidth}
      height={height}
      role="img"
      aria-labelledby="worthItTitle worthItDesc"
      className={className}
      style={{ display: "block", flexShrink: 0 }}
    >
      <title id="worthItTitle">Worth-It</title>
      <desc id="worthItDesc">
        Worth-It logo with green downward marks, red upward mark, mirrored black accents, and the tagline Find the price worth buying.
      </desc>

      {/* Brand mark */}
      <g transform="translate(40 35)">
        
        {/* Left mirrored accent: \ */}
        <path
          d="M 35 35 L 78 102"
          fill="none"
          stroke="currentColor"
          strokeWidth="20"
          strokeLinecap="round"
        />

        {/* Right mirrored accent: / */}
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
          stroke="#22C77A"
          strokeWidth="26"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Red upward caret */}
        <path
          d="M 135 92 L 175 40 L 215 92"
          fill="none"
          stroke="#EF4444"
          strokeWidth="24"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Second green V */}
        <path
          d="M 178 120 L 225 190 L 272 120"
          fill="none"
          stroke="#22C77A"
          strokeWidth="26"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Wordmark */}
        <text
          x="300"
          y="175"
          fontFamily="Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
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
          fontFamily="Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
          fontSize="105"
          fontWeight="700"
          fill="currentColor"
        >
          -
        </text>

        {/* It */}
        <text
          x="690"
          y="175"
          fontFamily="Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
          fontSize="112"
          fontWeight="700"
          letterSpacing="-5"
          fill="currentColor"
        >
          It
        </text>

        {/* Tagline */}
        {showTagline && (
          <text
            x="350"
            y="250"
            fontFamily="Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
            fontSize="28"
            fontWeight="400"
            letterSpacing="8"
            fill="currentColor"
            opacity="0.65"
          >
            Find the price worth buying.
          </text>
        )}
      </g>
    </svg>
  );
}
