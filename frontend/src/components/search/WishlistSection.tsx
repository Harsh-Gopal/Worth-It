import React, { useState } from 'react';
import { Plus, Trash2, Tag, Loader2, Bookmark } from 'lucide-react';
import { useWishlist } from '../../hooks/useWishlist';

export default function WishlistSection() {
  const { items, isLoading, error, addUrl, removeUrl, toggleSelection } = useWishlist();
  const [urlInput, setUrlInput] = useState('');

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) return;
    
    const success = await addUrl(urlInput.trim());
    if (success) {
      setUrlInput('');
    }
  };

  const selectedCount = items.filter(i => i.selected).length;

  return (
    <div className="bg-[var(--bg-main)] border border-[var(--border-color)] rounded-xl p-5 md:p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
        <div>
          <h3 className="text-sm font-semibold text-[var(--text-primary)] tracking-wide flex items-center gap-2">
            <Bookmark className="w-4 h-4 text-[var(--color-brand-green)]" />
            Wishlist Tracking
          </h3>
          <p className="text-xs text-[var(--text-secondary)] mt-1">
            Track specific products. Selected items will be prioritized in your search.
          </p>
        </div>
        {items.length > 0 && (
          <div className="text-xs font-bold text-[var(--color-brand-green)] bg-[var(--color-brand-green)]/10 px-3 py-1.5 rounded-lg border border-[var(--color-brand-green)]/20">
            {selectedCount} / {items.length} Tracked
          </div>
        )}
      </div>

      <form onSubmit={handleAdd} className="flex gap-2 mb-6">
        <input
          type="url"
          placeholder="Paste Swiggy Instamart product URL..."
          value={urlInput}
          onChange={(e) => setUrlInput(e.target.value)}
          className="input-field flex-1 text-sm"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !urlInput.trim()}
          className="btn-primary py-2 px-4 shrink-0 flex items-center gap-2"
        >
          {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
          <span className="hidden sm:inline">{isLoading ? 'Adding...' : 'Add'}</span>
        </button>
      </form>

      {error && (
        <div className="mb-4 text-xs font-medium text-[var(--color-brand-red)] bg-[var(--color-brand-red)]/10 p-3 rounded-lg border border-[var(--color-brand-red)]/20">
          {error}
        </div>
      )}

      {items.length > 0 ? (
        <div className="space-y-3 max-h-[300px] overflow-y-auto custom-scrollbar pr-2">
          {items.map(item => (
            <div 
              key={item.id} 
              className={`flex items-center gap-4 p-3 rounded-xl border transition-all ${
                item.selected 
                  ? 'border-[var(--color-brand-green)]/50 bg-[var(--color-brand-green)]/5' 
                  : 'border-[var(--border-color)] bg-[var(--bg-surface)] opacity-70'
              }`}
            >
              <label className="relative flex items-center justify-center cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={item.selected}
                  onChange={() => toggleSelection(item.id)}
                  className="peer sr-only"
                />
                <div className="w-5 h-5 rounded border-2 border-[var(--border-color)] peer-checked:bg-[var(--color-brand-green)] peer-checked:border-[var(--color-brand-green)] transition-colors flex items-center justify-center">
                  <svg className="w-3 h-3 text-[var(--bg-main)] opacity-0 peer-checked:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="3">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              </label>

              <div className="w-12 h-12 bg-white rounded-lg flex items-center justify-center overflow-hidden shrink-0 border border-gray-100">
                {item.image_url ? (
                  <img src={item.image_url} alt={item.name} className="w-full h-full object-contain p-1" />
                ) : (
                  <Tag className="w-5 h-5 text-gray-300" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <p className={`text-sm font-semibold truncate ${item.selected ? 'text-[var(--text-primary)]' : 'text-[var(--text-secondary)]'}`}>
                  {item.name}
                </p>
                <div className="flex items-center gap-2 text-xs mt-0.5">
                  {item.price > 0 ? (
                    <>
                      <span className="font-bold text-[var(--text-primary)]">₹{item.price}</span>
                      <span className="text-[var(--text-muted)] line-through">₹{item.mrp}</span>
                    </>
                  ) : (
                    <span className="text-[var(--text-muted)]">Price unknown</span>
                  )}
                </div>
              </div>

              <button
                type="button"
                onClick={() => removeUrl(item.id)}
                className="p-2 text-[var(--text-muted)] hover:text-[var(--color-brand-red)] hover:bg-[var(--color-brand-red)]/10 rounded-lg transition-colors shrink-0"
                aria-label="Remove item"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 border-2 border-dashed border-[var(--border-color)] rounded-xl">
          <Bookmark className="w-8 h-8 text-[var(--border-color)] mx-auto mb-3" />
          <p className="text-sm font-medium text-[var(--text-secondary)]">Your wishlist is empty</p>
          <p className="text-xs text-[var(--text-muted)] mt-1">Add product URLs above to start tracking</p>
        </div>
      )}
    </div>
  );
}
