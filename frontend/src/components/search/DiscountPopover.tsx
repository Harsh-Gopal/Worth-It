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

export default function DiscountPopover({ targetName, currentDiscount, onApply, onClose, anchorEl }: DiscountPopoverProps) {
  const [customValue, setCustomValue] = useState(currentDiscount !== null ? currentDiscount.toString() : '');
  const [errorMsg, setErrorMsg] = useState('');
  
  const { refs, floatingStyles } = useFloating({
    placement: 'bottom-start',
    elements: {
      reference: anchorEl
    },
    middleware: [offset(8), flip(), shift({ padding: 8 })],
    whileElementsMounted: autoUpdate,
  });

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      // Check if clicking inside the floating element or the reference element
      const floatingEl = refs.floating.current;
      if (
        floatingEl && !floatingEl.contains(event.target as Node) &&
        anchorEl && !anchorEl.contains(event.target as Node)
      ) {
        onClose();
      }
    };
    
    // Use capture phase to prevent click events inside the popover from accidentally propagating and closing it
    document.addEventListener("mousedown", handleClickOutside, true);
    return () => document.removeEventListener("mousedown", handleClickOutside, true);
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
        style={{ ...floatingStyles, zIndex: 1000 }}
        className="bg-[var(--bg-main)] border border-[var(--border-color)] rounded-xl shadow-xl p-4 w-[280px]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4">
          <h4 className="m-0 text-sm font-semibold text-[var(--text-primary)]">{targetName}</h4>
          <p className="m-0 text-xs text-[var(--text-secondary)]">Set minimum discount</p>
        </div>

        <div className="mb-4">
          <label className="block text-[11px] font-semibold text-[var(--text-secondary)] mb-2 uppercase tracking-wide">
            CUSTOM
          </label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <input 
                type="number" 
                value={customValue}
                onChange={(e) => {
                  setCustomValue(e.target.value);
                  setErrorMsg('');
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleApplyCustom();
                  }
                }}
                className="w-full py-2 pl-3 pr-6 rounded-lg border border-[var(--border-color)] bg-[var(--bg-input)] text-[var(--text-primary)] text-sm outline-none focus:border-[var(--color-brand-green)] transition-colors"
                placeholder="e.g. 25"
                min={1}
                max={99}
              />
              <span className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] text-sm font-medium">%</span>
            </div>
            <button 
              type="button"
              onClick={handleApplyCustom}
              className="bg-[var(--color-brand-green)] hover:bg-[var(--color-brand-green)]/90 text-white border-none rounded-lg px-4 font-semibold text-sm cursor-pointer transition-colors"
            >
              Apply
            </button>
          </div>
          {errorMsg && (
            <p className="text-xs text-[var(--color-brand-red)] mt-1.5 mb-0">{errorMsg}</p>
          )}
        </div>

        <div className="grid grid-cols-4 gap-2">
          {PRESETS.map(pct => (
            <button
              key={pct}
              type="button"
              onClick={() => {
                onApply(pct);
              }}
              className="py-1.5 bg-[var(--bg-surface)] border border-[var(--border-color)] rounded-md text-xs font-medium text-[var(--text-primary)] cursor-pointer text-center hover:border-[var(--color-brand-green)] hover:text-[var(--color-brand-green)] transition-colors"
            >
              {pct}%
            </button>
          ))}
          <button
            type="button"
            onClick={() => {
              onApply(99);
            }}
            className="col-span-4 py-1.5 bg-[var(--bg-surface)] border border-[var(--border-color)] rounded-md text-xs font-medium text-[var(--text-primary)] cursor-pointer text-center hover:border-[var(--color-brand-green)] hover:text-[var(--color-brand-green)] transition-colors"
          >
            99%
          </button>
        </div>
      </div>
    </FloatingPortal>
  );
}

