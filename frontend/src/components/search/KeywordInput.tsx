import React, { useState, useEffect, useRef } from "react";
import { X, Plus } from "lucide-react";

interface KeywordInputProps {
  keywords: string[];
  setKeywords: (keywords: string[]) => void;
  categories?: string[];
  placeholder?: string;
}

export default function KeywordInput({ keywords, setKeywords, categories = [], placeholder }: KeywordInputProps) {
  const [inputValue, setInputValue] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [keywordCategories, setKeywordCategories] = useState<Record<string, string[]>>({});
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch("/api/keywords")
      .then(res => res.json())
      .then(data => setKeywordCategories(data.categories || {}))
      .catch(console.error);
  }, []);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsFocused(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const allSuggestions = Object.entries(keywordCategories)
    .filter(([cat]) => categories.length === 0 || categories.includes(cat) || cat === "Popular")
    .map(([cat, kws]) => ({
      category: cat,
      keywords: kws.filter(k => !keywords.map(kw => kw.toLowerCase()).includes(k.toLowerCase()))
                   .filter(k => k.toLowerCase().includes(inputValue.toLowerCase()))
    }))
    .filter(c => c.keywords.length > 0);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addKeyword(inputValue);
    } else if (e.key === "Backspace" && !inputValue && keywords.length > 0) {
      setKeywords(keywords.slice(0, -1));
    }
  };

  const addKeyword = (value: string) => {
    const trimmed = value.trim().replace(/,$/, "");
    if (trimmed && !keywords.includes(trimmed)) {
      setKeywords([...keywords, trimmed]);
      setInputValue("");
    } else if (trimmed) {
      setInputValue("");
    }
  };

  const removeKeyword = (keyword: string) => {
    setKeywords(keywords.filter(k => k !== keyword));
  };

  return (
    <div style={{ position: "relative" }} ref={wrapperRef}>
      <div
        style={{
        display: "flex",
        flexWrap: "wrap",
        alignItems: "center",
        gap: "6px",
        padding: "6px 10px",
        background: "var(--bg-input)",
        border: "1px solid var(--border)",
        borderRadius: "8px",
        minHeight: "40px",
        cursor: "text",
        transition: "border-color 0.15s, box-shadow 0.15s",
      }}
      onClick={e => {
        setIsFocused(true);
        const inp = (e.currentTarget as HTMLElement).querySelector("input");
        inp?.focus();
      }}
      onFocusCapture={e => {
        setIsFocused(true);
        const div = e.currentTarget as HTMLElement;
        div.style.borderColor = "var(--color-brand-green)";
        div.style.boxShadow = "0 0 0 3px var(--ring-green)";
      }}
      onBlurCapture={e => {
        // Delay adding keyword on blur so click on suggestion can process first
        if (!wrapperRef.current?.contains(e.relatedTarget as Node)) {
          const div = e.currentTarget as HTMLElement;
          div.style.borderColor = "var(--border)";
          div.style.boxShadow = "none";
          // We don't auto-add on blur anymore, let them explicitly press enter or click, 
          // because it causes race conditions with suggestion clicks.
        }
      }}
    >
      {keywords.map(keyword => (
        <span
          key={keyword}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            fontSize: "12px",
            fontWeight: 500,
            color: "var(--text-primary)",
            background: "var(--bg-surface-hover)",
            border: "1px solid var(--border)",
            borderRadius: "5px",
            padding: "2px 8px 2px 8px",
            flexShrink: 0,
          }}
        >
          {keyword}
          <button
            type="button"
            onClick={e => { e.stopPropagation(); removeKeyword(keyword); }}
            style={{
              background: "none",
              border: "none",
              padding: "0",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              color: "var(--text-muted)",
              marginLeft: "2px",
            }}
          >
            <X className="w-3 h-3" />
          </button>
        </span>
      ))}
      <input
        type="text"
        value={inputValue}
        onChange={e => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={keywords.length === 0 ? (placeholder || "Type and press Enter…") : "Add more…"}
        style={{
          flex: 1,
          minWidth: "120px",
          background: "transparent",
          border: "none",
          outline: "none",
          fontSize: "13px",
          color: "var(--text-primary)",
          fontFamily: "inherit",
          padding: "2px 0",
        }}
      />
      </div>
      {/* Suggestions Dropdown */}
      {isFocused && allSuggestions.length > 0 && (
        <div style={{
          position: "absolute",
          top: "100%",
          left: 0,
          right: 0,
          marginTop: "8px",
          background: "var(--bg-surface)",
          border: "1px solid var(--border)",
          borderRadius: "8px",
          boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
          maxHeight: "300px",
          overflowY: "auto",
          zIndex: 100,
          padding: "8px",
          display: "flex",
          flexDirection: "column",
          gap: "12px"
        }}>
          {allSuggestions.map(group => (
            <div key={group.category}>
              <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "6px", fontWeight: 600, textTransform: "uppercase", padding: "0 4px" }}>
                {group.category}
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", padding: "0 4px" }}>
                {group.keywords.map(suggestion => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => addKeyword(suggestion)}
                    style={{
                      background: "transparent",
                      border: "1px dashed var(--border-strong)",
                      borderRadius: "12px",
                      padding: "3px 10px",
                      fontSize: "12px",
                      color: "var(--text-secondary)",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: "4px",
                      transition: "all 0.15s"
                    }}
                    onMouseEnter={e => {
                      e.currentTarget.style.borderColor = "var(--color-brand-green)";
                      e.currentTarget.style.color = "var(--color-brand-green)";
                      e.currentTarget.style.background = "var(--ring-green)";
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.borderColor = "var(--border-strong)";
                      e.currentTarget.style.color = "var(--text-secondary)";
                      e.currentTarget.style.background = "transparent";
                    }}
                  >
                    <Plus className="w-3 h-3" /> {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
