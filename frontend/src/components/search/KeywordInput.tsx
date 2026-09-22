import React, { useState, useEffect, useRef } from "react";
import { X, Plus } from "lucide-react";
import type { TargetRule } from "../../lib/types";
import DiscountPopover from "./DiscountPopover";

interface KeywordInputProps {
  keywords: TargetRule[];
  setKeywords: (keywords: TargetRule[]) => void;
  categories?: string[];
  placeholder?: string;
}

export default function KeywordInput({ keywords, setKeywords, categories = [], placeholder }: KeywordInputProps) {
  const [inputValue, setInputValue] = useState("");
  const [activePopover, setActivePopover] = useState<string | null>(null);
  const [activeAnchor, setActiveAnchor] = useState<HTMLElement | null>(null);
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
      keywords: kws.filter(k => !keywords.map(kw => kw.name.toLowerCase()).includes(k.toLowerCase()))
                   .filter(k => k.toLowerCase().includes(inputValue.toLowerCase()))
    }))
    .filter(c => c.keywords.length > 0);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addKeywordAndConfigure(inputValue);
    } else if (e.key === "Backspace" && !inputValue && keywords.length > 0) {
      setKeywords(keywords.slice(0, -1));
    }
  };

  const addKeywordAndConfigure = (value: string) => {
    const trimmed = value.trim().replace(/,$/, "");
    if (trimmed && !keywords.find(k => k.name.toLowerCase() === trimmed.toLowerCase())) {
      setActivePopover(trimmed);
      setInputValue("");
    } else if (trimmed) {
      setInputValue("");
    }
  };

  const handleConfirmThreshold = (keyword: string, minDiscount: number | null) => {
    if (minDiscount === null) return;
    const existing = keywords.find(k => k.name === keyword);
    if (existing) {
      setKeywords(keywords.map(k => k.name === keyword ? { ...k, minDiscount } : k));
    } else {
      setKeywords([...keywords, { name: keyword, minDiscount }]);
    }
  };

  const removeKeyword = (keyword: string) => {
    setKeywords(keywords.filter(k => k.name !== keyword));
    if (activePopover === keyword) {
      setActivePopover(null);
    }
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
      {(() => {
        const displayKeywords = [...keywords];
        if (activePopover && !keywords.find(k => k.name === activePopover)) {
          displayKeywords.push({ name: activePopover, minDiscount: null });
        }
        return displayKeywords.map(kw => (
        <span
          key={kw.name}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
            fontSize: "12px",
            fontWeight: 500,
            color: "var(--color-brand-green)",
            background: "var(--ring-green)",
            border: "1px solid var(--color-brand-green)",
            borderRadius: "5px",
            padding: "2px 8px 2px 8px",
            flexShrink: 0,
          }}
        >
          {kw.name}
          <span style={{ 
            display: "inline-flex",
            alignItems: "center",
            fontSize: "11px",
            background: kw.minDiscount !== null ? "rgba(34, 197, 94, 0.15)" : "transparent",
            padding: "1px 4px",
            borderRadius: "3px",
            marginLeft: "2px",
            opacity: kw.minDiscount !== null ? 1 : 0.6,
            transition: "opacity 0.2s",
            position: "relative"
          }}>
            <button
              type="button"
              ref={node => {
                if (node && activePopover === kw.name && activeAnchor !== node) {
                  setActiveAnchor(node);
                }
              }}
              onClick={(e) => {
                e.stopPropagation();
                if (activePopover === kw.name) {
                  setActivePopover(null);
                  setActiveAnchor(null);
                } else {
                  setActivePopover(kw.name);
                  setActiveAnchor(e.currentTarget);
                }
              }}
              style={{
                background: "none",
                border: "none",
                padding: 0,
                margin: 0,
                color: "inherit",
                fontWeight: "bold",
                cursor: "pointer",
                outline: "none"
              }}
            >
              {kw.minDiscount !== null ? `≥${kw.minDiscount}%` : 'Set %'}
            </button>
            {activePopover === kw.name && (
              <DiscountPopover
                targetName={kw.name}
                currentDiscount={kw.minDiscount}
                anchorEl={activeAnchor}
                onApply={(val) => {
                  handleConfirmThreshold(kw.name, val);
                  setActivePopover(null);
                  setActiveAnchor(null);
                }}
                onClose={() => {
                  setActivePopover(null);
                  setActiveAnchor(null);
                  if (kw.minDiscount === null) {
                    removeKeyword(kw.name);
                  }
                }}
              />
            )}
          </span>
          <button
            type="button"
            onClick={e => { e.stopPropagation(); removeKeyword(kw.name); }}
            style={{
              background: "none",
              border: "none",
              padding: "0",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              color: "var(--color-brand-green)",
              marginLeft: "4px",
              opacity: 0.8
            }}
          >
            <X className="w-3 h-3" />
          </button>
        </span>
      ))})()}
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
      {isFocused && !activePopover && allSuggestions.length > 0 && (
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
                    onClick={() => addKeywordAndConfigure(suggestion)}
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
