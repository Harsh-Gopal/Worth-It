import React from 'react';
import { Zap, Target, Filter, MapPin, Send } from 'lucide-react';

/* ═══════════════════════════════════════════════════════════════════════
   WORTH-IT HERO — Full-bleed layout
   
   The outer wrapper is width:100% with no max-width constraint — it fills
   the entire main-content area (viewport minus sidebar).
   
   Composition:
   - Background layer: full width gradient glows
   - Absolute floating cards: positioned at left/right edges of hero
   - Center content: flex column, horizontally centered, no max-width cap
   - Feature row: centered, max-width for readability
   
   Cards use clamp()-based positioning so they always stay in their lane
   relative to the hero, not the viewport.
═══════════════════════════════════════════════════════════════════════ */

/* ── Animation keyframes ── */
const HERO_CSS = `
  @keyframes wi-float {
    0%, 100% { transform: rotate(-5deg) translateY(0px);  }
    50%       { transform: rotate(-5deg) translateY(-9px); }
  }
  @keyframes wi-float-r {
    0%, 100% { transform: rotate(3deg) translateY(0px);   }
    50%       { transform: rotate(3deg) translateY(-9px);  }
  }
  @keyframes wi-bob {
    0%, 100% { transform: translateY(0px);  }
    50%       { transform: translateY(-6px); }
  }
  @keyframes wi-sparkle {
    0%, 100% { opacity: 0.3;  transform: scale(1)    rotate(0deg);  }
    50%       { opacity: 0.55; transform: scale(1.2)  rotate(18deg); }
  }
  @media (prefers-reduced-motion: reduce) {
    .wi-float, .wi-float-r, .wi-bob, .wi-sparkle {
      animation: none !important;
    }
  }
  .wi-float   { animation: wi-float   7s ease-in-out infinite; }
  .wi-float-r { animation: wi-float-r 8s ease-in-out 1s infinite; }
  .wi-bob     { animation: wi-bob     5s ease-in-out infinite; }
  .wi-sparkle { animation: wi-sparkle 4s ease-in-out infinite; }

  /* Feature grid responsive */
  .wi-feat-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px 28px;
    width: 100%;
    max-width: 760px;
  }
  @media (max-width: 767px) {
    .wi-feat-grid { grid-template-columns: repeat(2, 1fr); }
  }
  @media (max-width: 430px) {
    .wi-feat-grid { display: none; } /* Hide feature grid on mobile to save vertical space */
  }

  /* Show/hide floating cards at breakpoints */
  .wi-left-card  { display: flex; }
  .wi-right-card { display: flex; }
  @media (max-width: 900px) {
    .wi-left-card, .wi-right-card { display: none !important; }
  }
`;

/* ── Sparkle SVG ── */
function Sparkle({ size = 12, color = '#22c55e', opacity = 0.4, delay = '0s' }: {
  size?: number; color?: string; opacity?: number; delay?: string;
}) {
  return (
    <svg
      width={size} height={size} viewBox="0 0 24 24" fill={color}
      aria-hidden="true" className="wi-sparkle"
      style={{ opacity, pointerEvents: 'none', animationDelay: delay }}
    >
      <path d="M12 2L13.09 8.26L19 6L14.74 10.91L21 12L14.74 13.09L19 18L13.09 15.74L12 22L10.91 15.74L5 18L9.26 13.09L3 12L9.26 10.91L5 6L10.91 8.26L12 2Z"/>
    </svg>
  );
}

/* ── Left floating deal card ── */
function DealCard() {
  return (
    <div
      aria-hidden="true"
      className="wi-float wi-left-card"
      style={{
        flexDirection: 'column',
        gap: '12px',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        borderRadius: '22px',
        boxShadow: '0 16px 48px rgba(0,0,0,0.10), 0 2px 8px rgba(0,0,0,0.06)',
        padding: '18px',
        pointerEvents: 'none',
        width: 'clamp(170px, 16vw, 210px)',
      }}
    >
      {/* Product visual */}
      <div style={{
        width: '100%', height: '100px',
        background: 'linear-gradient(150deg, rgba(34,197,94,0.07) 0%, rgba(34,197,94,0.18) 100%)',
        borderRadius: '14px',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        position: 'relative', overflow: 'hidden',
      }}>
        <svg width="72" height="72" viewBox="0 0 80 80" fill="none" aria-hidden="true">
          <polygon points="40,8 70,24 40,40 10,24" fill="#4ade80" stroke="#16a34a" strokeWidth="1"/>
          <polygon points="10,24 10,56 40,72 40,40" fill="#16a34a" stroke="#15803d" strokeWidth="1"/>
          <polygon points="70,24 70,56 40,72 40,40" fill="#22c55e" stroke="#16a34a" strokeWidth="1"/>
          <ellipse cx="40" cy="22" rx="6" ry="4" fill="#86efac"/>
          <path d="M40 18 Q38 12 32 10" stroke="#86efac" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
          <path d="M40 18 Q42 12 48 10" stroke="#86efac" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
          <path d="M40 20 L40 14" stroke="#86efac" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
        {/* Graph */}
        <svg style={{ position: 'absolute', bottom: 4, left: 0, right: 0, width: '100%' }} height="18" viewBox="0 0 200 18" preserveAspectRatio="none">
          <path d="M0,13 Q50,3 100,11 T200,7" fill="none" stroke="#22c55e" strokeWidth="2" strokeLinecap="round" opacity="0.5"/>
        </svg>
      </div>

      {/* Discount badge */}
      <div style={{
        display: 'inline-flex', alignItems: 'center', gap: '4px',
        background: '#16a34a', color: 'white',
        fontSize: '10.5px', fontWeight: 800,
        padding: '3px 9px', borderRadius: '20px',
        width: 'fit-content', letterSpacing: '0.03em',
      }}>
        <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round">
          <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
          <polyline points="17 6 23 6 23 12"/>
        </svg>
        52% OFF
      </div>

      {/* Pricing */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
        <span style={{ fontSize: 'clamp(18px, 1.5vw, 22px)', fontWeight: 900, color: 'var(--text-primary)', letterSpacing: '-0.03em' }}>₹899</span>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)', textDecoration: 'line-through' }}>₹1,899</span>
      </div>
    </div>
  );
}

/* ── Right floating alert card ── */
function AlertCard() {
  return (
    <div
      aria-hidden="true"
      className="wi-float-r wi-right-card"
      style={{
        flexDirection: 'column',
        gap: '12px',
        background: 'linear-gradient(140deg, #1e2d5a 0%, #1a1f4a 60%, #231840 100%)',
        border: '1px solid rgba(99,102,241,0.3)',
        borderRadius: '22px',
        boxShadow: '0 20px 56px rgba(88,28,135,0.22), 0 4px 16px rgba(0,0,0,0.28)',
        padding: '18px',
        pointerEvents: 'none',
        width: 'clamp(190px, 17vw, 220px)',
        position: 'relative',
      }}
    >
      {/* Orange bell */}
      <div style={{
        position: 'absolute', top: '-8px', right: '-8px',
        width: '22px', height: '22px',
        background: '#f97316', borderRadius: '50%',
        border: '2px solid rgba(255,255,255,0.2)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: '0 2px 8px rgba(249,115,22,0.55)',
      }}>
        <svg width="11" height="11" viewBox="0 0 24 24" fill="white">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
        </svg>
      </div>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{
          width: '34px', height: '34px', background: '#2CA5E0',
          borderRadius: '50%',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0, boxShadow: '0 3px 10px rgba(44,165,224,0.4)',
        }}>
          <Send width={15} height={15} color="white" strokeWidth={2} style={{ transform: 'translateX(1px)' }}/>
        </div>
        <div>
          <div style={{ fontSize: '13px', fontWeight: 800, color: 'white', lineHeight: 1.2 }}>Deal Alert! 🔥</div>
          <div style={{ fontSize: '10px', color: 'rgba(147,197,253,0.85)', fontWeight: 500 }}>Worth-It</div>
        </div>
      </div>

      <div style={{ height: '1px', background: 'rgba(255,255,255,0.08)' }}/>

      {/* Product */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{
          width: '36px', height: '36px',
          background: 'rgba(34,197,94,0.14)',
          border: '1px solid rgba(34,197,94,0.25)',
          borderRadius: '10px',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0,
        }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" fill="rgba(34,197,94,0.35)" stroke="#4ade80" strokeWidth="1.5"/>
            <polyline points="3.27 6.96 12 12.01 20.73 6.96" stroke="#4ade80" strokeWidth="1.5" fill="none" strokeLinecap="round"/>
            <line x1="12" y1="22.08" x2="12" y2="12" stroke="#4ade80" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        </div>
        <div>
          <div style={{ fontSize: '12px', color: 'rgba(219,234,254,0.95)', fontWeight: 600, lineHeight: 1.3 }}>Protein 1kg</div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '5px', marginTop: '2px' }}>
            <span style={{ fontSize: 'clamp(14px, 1.3vw, 16px)', fontWeight: 900, color: 'white', letterSpacing: '-0.02em' }}>₹899</span>
            <span style={{ fontSize: '10px', color: '#4ade80', fontWeight: 700 }}>52% OFF</span>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Feature item ── */
function Feature({ icon, title, desc }: { icon: React.ReactNode; title: string; desc: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', textAlign: 'left' }}>
      <div style={{
        width: '34px', height: '34px', borderRadius: '50%',
        background: 'var(--bg-surface)',
        border: '1px solid var(--border)',
        boxShadow: '0 1px 6px rgba(0,0,0,0.06)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0,
      }}>
        {icon}
      </div>
      <div>
        <div style={{ fontSize: '12.5px', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.3 }}>{title}</div>
        <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px', lineHeight: 1.4 }}>{desc}</div>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════
   MAIN EXPORT
══════════════════════════════════════════════════════════ */
export default function WorthItHero() {
  return (
    <>
      <style>{HERO_CSS}</style>
      <section
        aria-label="Worth-It product hero"
        className="w-full relative overflow-hidden pt-[18px] pb-[20px] md:pt-[28px] md:pb-[36px]"
      >
        {/* ── Background glows ── */}
        <div aria-hidden="true" className="absolute inset-0 pointer-events-none z-0">
          <div style={{
            position: 'absolute', left: 0, top: 0, width: '40%', height: '100%',
            background: 'radial-gradient(ellipse at 10% 55%, rgba(34,197,94,0.13) 0%, transparent 70%)',
          }}/>
          <div style={{
            position: 'absolute', right: 0, top: 0, width: '40%', height: '100%',
            background: 'radial-gradient(ellipse at 90% 45%, rgba(139,92,246,0.10) 0%, transparent 70%)',
          }}/>
          <div style={{
            position: 'absolute', left: '20%', right: '20%', top: '-20%', height: '80%',
            background: 'radial-gradient(ellipse at 50% 0%, rgba(6,182,212,0.07) 0%, transparent 70%)',
          }}/>
        </div>

        <div className="relative z-10 flex items-center w-full px-4 md:px-5 gap-0">
          {/* ── LEFT ZONE ── */}
          <div
            className="wi-left-card flex-1 min-w-0 flex-col items-end justify-center gap-3 pr-[clamp(8px,2vw,32px)]"
          >
            {/* Zepto badge */}
            <div
              className="wi-bob flex items-center justify-center font-black text-white bg-[#d31569] rounded-xl self-end mr-2 pointer-events-none shadow-[0_6px_20px_rgba(211,21,105,0.4)]"
              style={{
                width: 'clamp(34px, 3.5vw, 44px)',
                height: 'clamp(34px, 3.5vw, 44px)',
                fontSize: 'clamp(14px, 1.4vw, 20px)',
                transform: 'rotate(-8deg)',
                animationDelay: '0.3s',
              }}
              aria-hidden="true"
            >Z</div>
            <DealCard />
            <div className="flex gap-3 pr-2">
              <Sparkle size={11} color="#22c55e" opacity={0.38} delay="0s"/>
              <Sparkle size={9}  color="#06b6d4" opacity={0.32} delay="0.9s"/>
            </div>
          </div>

          {/* ── CENTER ZONE ── */}
          <div className="flex-[0_1_clamp(320px,40vw,560px)] flex flex-col items-center text-center mx-auto">
            {/* Top pill */}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 md:px-4 md:py-1.5 rounded-full bg-[var(--bg-surface)] border border-[var(--border)] shadow-sm mb-4 md:mb-6 text-[10px] md:text-xs font-semibold text-[var(--text-secondary)] whitespace-nowrap tracking-wide">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="#8b5cf6" aria-hidden="true">
                <path d="M12 2L13.09 8.26L19 6L14.74 10.91L21 12L14.74 13.09L19 18L13.09 15.74L12 22L10.91 15.74L5 18L9.26 13.09L3 12L9.26 10.91L5 6L10.91 8.26L12 2Z"/>
              </svg>
              <span>Track Smarter · Save Bigger · Shop Better</span>
              <span className="opacity-40 text-[8px] md:text-[10px] tracking-widest">•••</span>
            </div>

            {/* Headline */}
            <h1 className="m-0 flex flex-col items-center">
              <span className="font-extrabold tracking-[-0.035em] text-[var(--text-primary)] text-[clamp(1.5rem,3.5vw,3.5rem)] leading-[1.1] block">
                Find the Price
              </span>

              {/* WORTH BUYING + underline */}
              <span className="relative inline-block mt-1">
                <span className="font-black tracking-[-0.045em] text-[clamp(2rem,4.8vw,5rem)] leading-[1.0] block pb-1 md:pb-2.5 whitespace-nowrap bg-clip-text text-transparent bg-gradient-to-r from-green-600 via-cyan-500 to-violet-500">
                  WORTH BUYING.
                </span>

                {/* SVG swoosh */}
                <svg
                  aria-hidden="true"
                  viewBox="0 0 500 28" fill="none" preserveAspectRatio="none"
                  className="absolute -bottom-1 md:-bottom-1 -left-[4%] w-[108%] h-[20px] md:h-[28px] pointer-events-none"
                >
                  <defs>
                    <linearGradient id="wi-sw" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%"   stopColor="#16a34a"/>
                      <stop offset="42%"  stopColor="#06b6d4"/>
                      <stop offset="100%" stopColor="#8b5cf6"/>
                    </linearGradient>
                    <filter id="wi-blur"><feGaussianBlur stdDeviation="3"/></filter>
                  </defs>
                  <path d="M6,20 Q130,38 250,16 T494,20" stroke="rgba(139,92,246,0.18)" strokeWidth="12" strokeLinecap="round" filter="url(#wi-blur)"/>
                  <path d="M6,20 Q130,38 250,16 T494,20" stroke="url(#wi-sw)" strokeWidth="5" strokeLinecap="round"/>
                  <path d="M6,20 Q130,38 250,16 T494,20" stroke="url(#wi-sw)" strokeWidth="2" strokeLinecap="round" opacity="0.5"/>
                </svg>
              </span>
            </h1>

            {/* Sparkle row below headline */}
            <div className="flex gap-5 mt-4 md:mt-7 mb-0 md:mb-1">
              <Sparkle size={10} color="#22c55e" opacity={0.36} delay="0.5s"/>
              <Sparkle size={8}  color="#8b5cf6" opacity={0.32} delay="1.3s"/>
              <Sparkle size={10} color="#06b6d4" opacity={0.36} delay="0.1s"/>
            </div>

            {/* Feature row */}
            <div className="wi-feat-grid mt-6 md:mt-8">
              <Feature icon={<Zap size={16} color="#f97316" strokeWidth={2.5}/>} title="Track live prices"      desc="Instamart, Zepto, Blinkit & more"/>
              <Feature icon={<Target size={16} color="#ec4899" strokeWidth={2.5}/>} title="Get alerted instantly" desc="When real deals are found"/>
              <Feature icon={<Filter size={16} color="#16a34a" strokeWidth={2.5}/>} title="Filter what matters"   desc="Keywords, categories, wishlist"/>
              <Feature icon={<MapPin size={16} color="#ef4444" strokeWidth={2.5}/>} title="Your local prices"     desc="Scan by pincode or area"/>
            </div>
          </div>

          {/* ── RIGHT ZONE ── */}
          <div
            className="wi-right-card flex-1 min-w-0 flex-col items-start justify-center gap-3 pl-[clamp(8px,2vw,32px)]"
          >
            {/* Blinkit badge */}
            <div
              className="wi-bob flex items-center justify-center font-black text-[#1a1a1a] bg-[#f8cb46] rounded-xl self-start ml-2 pointer-events-none shadow-[0_6px_20px_rgba(248,203,70,0.45)]"
              style={{
                width: 'clamp(34px, 3.5vw, 44px)',
                height: 'clamp(34px, 3.5vw, 44px)',
                fontSize: 'clamp(14px, 1.4vw, 20px)',
                transform: 'rotate(8deg)',
                animationDelay: '1.1s',
              }}
              aria-hidden="true"
            >b</div>
            <AlertCard />
            <div className="flex gap-3 pl-2">
              <Sparkle size={11} color="#a855f7" opacity={0.36} delay="0.4s"/>
              <Sparkle size={9}  color="#f97316" opacity={0.30} delay="1.2s"/>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
