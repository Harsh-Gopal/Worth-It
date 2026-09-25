import { useState, useEffect } from 'react';
import { useFloating, shift, flip, offset, FloatingPortal, autoUpdate } from '@floating-ui/react';

interface DiscountPopoverProps {
  targetName: string;
  currentDiscount: number | null;
  onApply: (discount: number | null) => void;
  onClose: () => void;
  anchorEl: HTMLElement | null;
}

const PRESETS = [10, 15, 20, 30, 40, 50, 60, 70, 80, 85, 90, 95];

export default function DiscountPopover({
  targetName,
  currentDiscount,
  onApply,
  onClose,
  anchorEl,
}: DiscountPopoverProps) {
  const [customValue, setCustomValue] = useState(
    currentDiscount !== null ? currentDiscount.toString() : ''
  );
  const [errorMsg, setErrorMsg] = useState('');

  const { refs, floatingStyles } = useFloating({
    placement: 'bottom-start',
    elements: { reference: anchorEl },
    middleware: [offset(10), flip(), shift({ padding: 8 })],
    whileElementsMounted: autoUpdate,
  });

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const floatingEl = refs.floating.current;
      if (
        floatingEl && !floatingEl.contains(event.target as Node) &&
        anchorEl && !anchorEl.contains(event.target as Node)
      ) {
        onClose();
      }
    };
    document.addEventListener('mousedown', handleClickOutside, true);
    return () => document.removeEventListener('mousedown', handleClickOutside, true);
  }, [onClose, refs.floating, anchorEl]);

  const handleApplyCustom = () => {
    setErrorMsg('');
    if (customValue.trim() === '') {
      onApply(null);
      return;
    }
    const val = parseInt(customValue, 10);
    if (!isNaN(val) && val > 0 && val <= 99) {
      onApply(val);
    } else {
      setErrorMsg('Enter a number between 1 and 99');
    }
  };

  if (!anchorEl) return null;

  return (
    <FloatingPortal>
      <div
        ref={refs.setFloating}
        style={{
          ...floatingStyles,
          zIndex: 9999,
          width: "276px",
          background: "var(--bg-surface)",
          border: "1px solid var(--border-strong)",
          borderRadius: "12px",
          padding: "16px",
          boxShadow: "var(--shadow-elevated)",
          /* Force solid — no backdrop blur, no transparency */
          opacity: 1,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ marginBottom: "14px" }}>
          <h4 style={{
            margin: 0,
            fontSize: "13.5px",
            fontWeight: 700,
            color: "var(--text-primary)",
            lineHeight: 1.3,
          }}>
            {targetName}
          </h4>
          <p style={{
            margin: "3px 0 0",
            fontSize: "11.5px",
            color: "var(--text-secondary)",
          }}>
            Set minimum discount %
          </p>
        </div>

        {/* Custom value row */}
        <div style={{ marginBottom: "12px" }}>
          <label style={{
            display: "block",
            fontSize: "10.5px",
            fontWeight: 700,
            color: "var(--text-muted)",
            textTransform: "uppercase",
            letterSpacing: "0.07em",
            marginBottom: "7px",
          }}>
            Custom
          </label>
          <div style={{ display: "flex", gap: "8px" }}>
            <div style={{ position: "relative", flex: 1 }}>
              <input
                type="number"
                value={customValue}
                onChange={(e) => { setCustomValue(e.target.value); setErrorMsg(''); }}
                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleApplyCustom(); } }}
                placeholder="e.g. 25"
                min={1}
                max={99}
                style={{
                  width: "100%",
                  padding: "8px 28px 8px 10px",
                  borderRadius: "8px",
                  border: "1px solid var(--border)",
                  background: "var(--bg-input)",
                  color: "var(--text-primary)",
                  fontSize: "13px",
                  outline: "none",
                  fontFamily: "inherit",
                  boxSizing: "border-box",
                  transition: "border-color 0.15s",
                }}
                onFocus={e => {
                  e.target.style.borderColor = "var(--color-brand-green)";
                  e.target.style.boxShadow = "0 0 0 3px var(--ring-green)";
                }}
                onBlur={e => {
                  e.target.style.borderColor = "var(--border)";
                  e.target.style.boxShadow = "none";
                }}
              />
              <span style={{
                position: "absolute",
                right: "9px",
                top: "50%",
                transform: "translateY(-50%)",
                fontSize: "13px",
                color: "var(--text-muted)",
                fontWeight: 500,
                pointerEvents: "none",
              }}>%</span>
            </div>
            <button
              type="button"
              onClick={handleApplyCustom}
              style={{
                background: "var(--color-brand-green)",
                color: "#fff",
                border: "none",
                borderRadius: "8px",
                padding: "0 14px",
                fontWeight: 700,
                fontSize: "13px",
                cursor: "pointer",
                fontFamily: "inherit",
                transition: "background 0.15s",
                flexShrink: 0,
              }}
              onMouseEnter={e => (e.currentTarget.style.background = "var(--color-brand-green-hover)")}
              onMouseLeave={e => (e.currentTarget.style.background = "var(--color-brand-green)")}
            >
              Apply
            </button>
          </div>
          {errorMsg && (
            <p style={{
              margin: "5px 0 0",
              fontSize: "11.5px",
              color: "var(--color-brand-red)",
            }}>
              {errorMsg}
            </p>
          )}
        </div>

        {/* Divider */}
        <div style={{ height: "1px", background: "var(--border)", margin: "12px 0" }} />

        {/* Preset grid */}
        <label style={{
          display: "block",
          fontSize: "10.5px",
          fontWeight: 700,
          color: "var(--text-muted)",
          textTransform: "uppercase",
          letterSpacing: "0.07em",
          marginBottom: "8px",
        }}>
          Quick Presets
        </label>
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, 1fr)",
          gap: "6px",
        }}>
          {PRESETS.map(pct => (
            <button
              key={pct}
              type="button"
              onClick={() => onApply(pct)}
              style={{
                padding: "6px 0",
                background: currentDiscount === pct ? "var(--ring-green)" : "var(--bg-input)",
                border: `1px solid ${currentDiscount === pct ? "var(--color-brand-green)" : "var(--border)"}`,
                borderRadius: "7px",
                fontSize: "12px",
                fontWeight: 600,
                color: currentDiscount === pct ? "var(--color-brand-green)" : "var(--text-secondary)",
                cursor: "pointer",
                textAlign: "center",
                transition: "all 0.15s",
                fontFamily: "inherit",
              }}
              onMouseEnter={e => {
                if (currentDiscount !== pct) {
                  e.currentTarget.style.borderColor = "var(--color-brand-green)";
                  e.currentTarget.style.color = "var(--color-brand-green)";
                  e.currentTarget.style.background = "var(--ring-green)";
                }
              }}
              onMouseLeave={e => {
                if (currentDiscount !== pct) {
                  e.currentTarget.style.borderColor = "var(--border)";
                  e.currentTarget.style.color = "var(--text-secondary)";
                  e.currentTarget.style.background = "var(--bg-input)";
                }
              }}
            >
              {pct}%
            </button>
          ))}
          {/* 99% full width */}
          <button
            type="button"
            onClick={() => onApply(99)}
            style={{
              gridColumn: "1 / -1",
              padding: "6px 0",
              background: currentDiscount === 99 ? "var(--ring-green)" : "var(--bg-input)",
              border: `1px solid ${currentDiscount === 99 ? "var(--color-brand-green)" : "var(--border)"}`,
              borderRadius: "7px",
              fontSize: "12px",
              fontWeight: 600,
              color: currentDiscount === 99 ? "var(--color-brand-green)" : "var(--text-secondary)",
              cursor: "pointer",
              textAlign: "center",
              transition: "all 0.15s",
              fontFamily: "inherit",
            }}
            onMouseEnter={e => {
              if (currentDiscount !== 99) {
                e.currentTarget.style.borderColor = "var(--color-brand-green)";
                e.currentTarget.style.color = "var(--color-brand-green)";
                e.currentTarget.style.background = "var(--ring-green)";
              }
            }}
            onMouseLeave={e => {
              if (currentDiscount !== 99) {
                e.currentTarget.style.borderColor = "var(--border)";
                e.currentTarget.style.color = "var(--text-secondary)";
                e.currentTarget.style.background = "var(--bg-input)";
              }
            }}
          >
            99%
          </button>
        </div>
      </div>
    </FloatingPortal>
  );
}
