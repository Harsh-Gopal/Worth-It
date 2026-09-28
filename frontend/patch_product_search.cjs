const fs = require('fs');

let content = fs.readFileSync('src/components/search/ProductSearch.tsx', 'utf8');

// Add ChevronUp and ChevronDown imports
content = content.replace(
  'import { Play, Square, RotateCcw, LayoutGrid, TextSearch, FilterX, Radar, MapPinned, RefreshCw } from "lucide-react";',
  'import { Play, Square, RotateCcw, LayoutGrid, TextSearch, FilterX, Radar, MapPinned, RefreshCw, ChevronUp, ChevronDown } from "lucide-react";'
);

// Replace ConfigCard
const configCardOld = `function ConfigCard({ icon: Icon, iconColor, iconBg, title, description, count, countLabel, children }: any) {
  return (
    <div
      className="card"
      style={{
        padding: "20px",
        display: "flex",
        flexDirection: "column",
        gap: "14px",
        height: "100%",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <div style={{
            width: "34px",
            height: "34px",
            borderRadius: "9px",
            background: iconBg || "var(--bg-input)",
            border: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: iconColor,
            flexShrink: 0,
          }}>
            <Icon size={18} strokeWidth={2} />
          </div>
          <div>
            <h4 style={{ margin: 0, fontSize: "13.5px", fontWeight: 700, color: "var(--text-primary)", lineHeight: 1.3 }}>{title}</h4>
            <p style={{ margin: 0, fontSize: "11.5px", color: "var(--text-muted)", lineHeight: 1.4, marginTop: "2px" }}>{description}</p>
          </div>
        </div>
        {count !== undefined && (
          <span style={{
            fontSize: "11px",
            fontWeight: 700,
            color: count > 0 ? "var(--color-brand-green)" : "var(--text-muted)",
            background: count > 0 ? "var(--ring-green)" : "transparent",
            border: count > 0 ? "1px solid rgba(22,163,74,0.2)" : "1px solid transparent",
            borderRadius: "20px",
            padding: "2px 10px",
            transition: "all 0.2s",
            flexShrink: 0,
          }}>
            {count} {countLabel}
          </span>
        )}
      </div>
      <div style={{ height: "1px", background: "var(--border)", opacity: 0.6 }} />
      <div style={{ flex: 1 }}>
        {children}
      </div>
    </div>
  );
}`;

const configCardNew = `function ConfigCard({ icon: Icon, iconColor, iconBg, title, description, count, countLabel, children, defaultExpanded = false }: any) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  return (
    <div className="card flex flex-col gap-3.5 h-full p-4 md:p-5">
      <div 
        className="flex justify-between items-start cursor-pointer md:cursor-default select-none md:select-text"
        onClick={() => {
          if (window.innerWidth <= 768) {
            setExpanded(!expanded);
          }
        }}
      >
        <div className="flex gap-3 items-center">
          <div className="w-[34px] h-[34px] rounded-[9px] border border-[var(--border)] flex items-center justify-center shrink-0" style={{ background: iconBg || "var(--bg-input)", color: iconColor }}>
            <Icon size={18} strokeWidth={2} />
          </div>
          <div>
            <h4 className="m-0 text-[13.5px] font-bold text-[var(--text-primary)] leading-[1.3]">{title}</h4>
            <p className="m-0 text-[11.5px] text-[var(--text-muted)] leading-[1.4] mt-[2px] hidden md:block">{description}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {count !== undefined && (
            <span className="text-[11px] font-bold px-[10px] py-[2px] rounded-[20px] transition-all shrink-0" style={{
              color: count > 0 ? "var(--color-brand-green)" : "var(--text-muted)",
              background: count > 0 ? "var(--ring-green)" : "transparent",
              border: count > 0 ? "1px solid rgba(22,163,74,0.2)" : "1px solid transparent",
            }}>
              {count} {countLabel}
            </span>
          )}
          <div className="md:hidden text-[var(--text-muted)] flex items-center">
            {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </div>
        </div>
      </div>
      <div className="h-[1px] bg-[var(--border)] opacity-60 hidden md:block" />
      <div className={\`flex-1 transition-all \${expanded ? 'block animate-fade-in-fast' : 'hidden md:block'}\`}>
        <div className="h-[1px] bg-[var(--border)] opacity-60 mb-3.5 block md:hidden" />
        {children}
      </div>
    </div>
  );
}`;

content = content.replace(configCardOld, configCardNew);


// Reorder components in ProductSearch
// The current layout is: 
// - TOP CONTROL BAR
// - SCAN PROGRESS BAR
// - 2x2 CONFIGURATION GRID (Categories, Search Area, Keywords, Exclude)
// - WISHLIST TRACKING
// - ACTIVE TARGETS SUMMARY
// - LIVE CONSOLE

// We need to move ACTIVE TARGETS right after SCAN PROGRESS BAR
const activeTargetsRegex = /\{\/\* ── ACTIVE TARGETS SUMMARY ───────────────────── \*\/\}([\s\S]*?)<\/ConfigCard>/;
const activeTargetsMatch = content.match(activeTargetsRegex);

if (activeTargetsMatch) {
  content = content.replace(activeTargetsMatch[0], ''); // Remove from original position

  // Re-insert after SCAN PROGRESS BAR
  const scanProgressRegex = /<ScanProgress[^>]*\/>/;
  const scanProgressMatch = content.match(scanProgressRegex);
  
  if (scanProgressMatch) {
    const activeTargetsModified = activeTargetsMatch[0].replace('<ConfigCard', '<ConfigCard defaultExpanded={true}');
    content = content.replace(scanProgressMatch[0], scanProgressMatch[0] + '\n\n      ' + activeTargetsModified);
  }
}

// Modify top control bar to be sticky/priority control area on mobile
const topControlBarRegex = /\{\/\* ── TOP CONTROL BAR ─────────────────────────────── \*\/\}([\s\S]*?)<\/div>\s*\{\/\* ── SCAN PROGRESS BAR ─────────────────────────────── \*\/\}/;
const topControlBarMatch = content.match(topControlBarRegex);

if (topControlBarMatch) {
  let modifiedControlBar = topControlBarMatch[1];
  
  // Replace the inline styles of the control bar with tailwind classes
  modifiedControlBar = modifiedControlBar.replace(
    /style=\{\{\s*display: "flex",\s*alignItems: "flex-start",\s*justifyContent: "space-between",\s*gap: "24px",\s*flexWrap: "wrap",\s*padding: "22px 24px",\s*background: "var\(--bg-card\)",\s*border: "1px solid var\(--border\)",\s*borderRadius: "14px",\s*boxShadow: "var\(--shadow-card\)",\s*\}\}/,
    'className="flex flex-col md:flex-row md:items-start justify-between gap-5 md:gap-6 p-4 md:p-6 bg-[var(--bg-card)] border border-[var(--border)] rounded-[14px] shadow-[var(--shadow-card)] sticky md:static top-0 z-30 mb-2"'
  );

  // Modify action buttons container to stack on mobile and span full width
  modifiedControlBar = modifiedControlBar.replace(
    /style=\{\{\s*display: "flex",\s*gap: "10px",\s*alignItems: "flex-end",\s*flexWrap: "wrap",\s*paddingTop: "22px",\s*\}\}/,
    'className="flex flex-row md:flex-row gap-2.5 items-center md:items-end flex-wrap pt-2 md:pt-[22px] w-full md:w-auto"'
  );

  // Modify buttons to take full width on mobile
  modifiedControlBar = modifiedControlBar.replace(/style=\{\{ minWidth: "156px",/g, 'className="btn-primary flex-1 md:flex-none min-w-[156px]" style={{');
  modifiedControlBar = modifiedControlBar.replace(/style=\{\{ minWidth: "130px",/g, 'className="btn-secondary flex-1 md:flex-none min-w-[130px]" style={{');

  content = content.replace(topControlBarMatch[1], modifiedControlBar);
}

// Ensure wishlist is also a config card (it currently is a separate component)
// We need to pass `defaultExpanded={false}` to the ConfigCards inside ProductSearch.tsx? No, ConfigCard defaults to false now.

// Search area grid is responsive via className="search-grid", let's adjust it
content = content.replace(
  /className="search-grid"\s*style=\{\{\s*display: "grid",\s*gridTemplateColumns: "minmax\(0,1fr\) minmax\(0,1fr\)",\s*gap: "16px",\s*\}\}/,
  'className="grid grid-cols-1 md:grid-cols-2 gap-4"'
);

// We should also adjust the layout inside ConfigCards where necessary.
// For example, Search Area & Timing inputs.
content = content.replace(
  /style=\{\{\s*display: "grid",\s*gridTemplateColumns: searchMode === "nearby_area" \? "1fr auto auto" : "1fr auto",\s*gap: "10px",\s*alignItems: "start",\s*\}\}/,
  'className={`grid gap-2.5 items-start ${searchMode === "nearby_area" ? "grid-cols-1 md:grid-cols-[1fr_auto_auto]" : "grid-cols-1 md:grid-cols-[1fr_auto]"}`}'
);

fs.writeFileSync('src/components/search/ProductSearch.tsx', content);
