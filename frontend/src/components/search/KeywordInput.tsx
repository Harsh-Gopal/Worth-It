import React, { useState } from 'react';
import { X } from 'lucide-react';

interface KeywordInputProps {
  keywords: string[];
  setKeywords: (keywords: string[]) => void;
  placeholder?: string;
}

export default function KeywordInput({ keywords, setKeywords, placeholder }: KeywordInputProps) {
  const [inputValue, setInputValue] = useState('');

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addKeyword(inputValue);
    }
  };

  const addKeyword = (value: string) => {
    const trimmed = value.trim();
    if (trimmed && !keywords.includes(trimmed)) {
      setKeywords([...keywords, trimmed]);
      setInputValue('');
    }
  };

  const removeKeyword = (keyword: string) => {
    setKeywords(keywords.filter(k => k !== keyword));
  };

  return (
    <div className="flex flex-wrap items-center gap-2 p-2 bg-[var(--bg-main)] border border-[var(--border-color)] rounded-xl focus-within:ring-1 focus-within:ring-[var(--color-brand-green)] focus-within:border-[var(--color-brand-green)] transition-all min-h-[46px]">
      {keywords.map(keyword => (
        <span key={keyword} className="flex items-center gap-1 bg-[var(--bg-surface-hover)] border border-[var(--border-color)] text-[var(--text-primary)] text-sm px-2.5 py-1 rounded-md shadow-[0_2px_5px_rgba(0,0,0,0.5)]">
          {keyword}
          <button type="button" onClick={() => removeKeyword(keyword)} className="text-[var(--text-secondary)] hover:text-[var(--color-brand-red)] focus:outline-none transition-colors">
            <X className="w-3.5 h-3.5" />
          </button>
        </span>
      ))}
      <input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={() => addKeyword(inputValue)}
        placeholder={keywords.length === 0 ? (placeholder || "Enter keywords (e.g. whey protein, amul butter)...") : "Add more..."}
        className="flex-1 min-w-[150px] bg-transparent border-none focus:ring-0 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] py-1 px-1 outline-none"
      />
    </div>
  );
}
