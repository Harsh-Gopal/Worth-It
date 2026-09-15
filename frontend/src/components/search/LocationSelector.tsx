import React, { useState } from 'react';
import { MapPin, Loader2, Search } from 'lucide-react';
import { api } from '../../lib/api';

interface LocationSelectorProps {
  location: any;
  setLocation: (loc: any) => void;
}

export default function LocationSelector({ location, setLocation }: LocationSelectorProps) {
  const [query, setQuery] = useState('');
  const [isResolving, setIsResolving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleResolve = async () => {
    if (!query.trim()) return;
    
    setIsResolving(true);
    setError(null);
    try {
      const res = await api.get(`/location/resolve?address=${encodeURIComponent(query)}`);
      setLocation({
        lat: res.lat,
        lng: res.lng,
        title: res.address || query,
        local_store_id: res.local_store_id
      });
      setQuery(''); // clear query on success to show the resolved badge instead
    } catch (err: any) {
      setError(err.message || 'Could not resolve location');
    } finally {
      setIsResolving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleResolve();
    }
  };

  if (location) {
    return (
      <div className="flex items-center justify-between p-3 bg-[var(--ring-color)] border border-[var(--color-brand-green)] rounded-xl h-[46px] shadow-[0_0_10px_var(--ring-color)]">
        <div className="flex items-center gap-2 overflow-hidden">
          <MapPin className="w-4 h-4 text-[var(--color-brand-green)] shrink-0" />
          <span className="text-sm font-bold text-white truncate">{location.title}</span>
        </div>
        <button
          type="button"
          onClick={() => setLocation(null)}
          className="text-xs text-[var(--color-brand-green)] font-bold uppercase tracking-wider hover:text-white ml-2 shrink-0 transition-colors"
        >
          Change
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="relative flex items-center">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <MapPin className="w-4 h-4 text-[var(--text-secondary)]" />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          className="bg-[var(--bg-main)] border border-[var(--border-color)] text-white text-sm rounded-xl focus:ring-1 focus:ring-[var(--color-brand-green)] focus:border-[var(--color-brand-green)] block w-full pl-9 pr-10 p-2.5 h-[46px] outline-none font-bold placeholder:font-normal placeholder:text-[var(--text-secondary)]"
          placeholder="e.g. 560001, MG Road Bangalore..."
        />
        <button 
          type="button"
          onClick={handleResolve}
          disabled={isResolving || !query.trim()}
          className="absolute inset-y-0 right-0 pr-3 flex items-center disabled:opacity-50 hover:text-[var(--color-brand-green)] transition-colors"
        >
          {isResolving ? <Loader2 className="w-4 h-4 text-[var(--color-brand-green)] animate-spin" /> : <Search className="w-4 h-4 text-[var(--color-brand-green)]" />}
        </button>
      </div>
      {error && <p className="text-xs text-[var(--color-brand-red)] font-bold mt-1">{error}</p>}
    </div>
  );
}
