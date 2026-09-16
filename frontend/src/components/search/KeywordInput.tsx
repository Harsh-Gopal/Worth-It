import React, { useState } from "react";
import { X } from "lucide-react";

interface KeywordInputProps {
  keywords: string[];
  setKeywords: (keywords: string[]) => void;
  placeholder?: string;
}

export default function KeywordInput({ keywords, setKeywords, placeholder }: KeywordInputProps) {
  const [inputValue, setInputValue] = useState("");

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
        const inp = (e.currentTarget as HTMLElement).querySelector("input");
        inp?.focus();
      }}
      onFocusCapture={e => {
        const div = e.currentTarget as HTMLElement;
        div.style.borderColor = "var(--color-brand-green)";
        div.style.boxShadow = "0 0 0 3px var(--ring-green)";
      }}
      onBlurCapture={e => {
        if (!e.currentTarget.contains(e.relatedTarget as Node)) {
          const div = e.currentTarget as HTMLElement;
          div.style.borderColor = "var(--border)";
          div.style.boxShadow = "none";
          addKeyword(inputValue);
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
  );
}
