const fs = require('fs');
let content = fs.readFileSync('src/components/search/WishlistSection.tsx', 'utf8');

// Add ChevronUp and ChevronDown
content = content.replace(
  'import { Plus, Trash2, Loader2, Bookmark, ChevronLeft, ChevronRight, Check, GripHorizontal } from "lucide-react";',
  'import { Plus, Trash2, Loader2, Bookmark, ChevronLeft, ChevronRight, Check, GripHorizontal, ChevronUp, ChevronDown } from "lucide-react";'
);

// Add state for expanded
content = content.replace(
  'const { requestAuth } = useAuthStore();',
  'const { requestAuth } = useAuthStore();\n  const [expanded, setExpanded] = useState(false);'
);

// Update Header
const headerRegex = /\{\/\* Header \*\/\}([\s\S]*?)<div style=\{\{ width: "100%", height: "1px", background: "var\(--border\)", opacity: 0\.5 \}\} \/>/;
const headerMatch = content.match(headerRegex);

if (headerMatch) {
  let newHeader = headerMatch[0];
  
  newHeader = newHeader.replace(
    /style=\{\{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "12px" \}\}/,
    'className="flex justify-between items-start flex-wrap gap-3 cursor-pointer md:cursor-default" onClick={() => { if (window.innerWidth <= 768) setExpanded(!expanded); }}'
  );
  
  // Make description hidden on mobile
  newHeader = newHeader.replace(
    /<p style=\{\{ margin: 0, fontSize: "13px", color: "var\(--text-secondary\)" \}\}>Track specific products from any supported platform using product URLs\.<\/p>/,
    '<p className="m-0 text-[13px] text-[var(--text-secondary)] hidden md:block">Track specific products from any supported platform using product URLs.</p>'
  );

  // Add chevrons next to "Add from URL" button area
  newHeader = newHeader.replace(
    /<\/button>\s*<\/div>\s*<\/div>/,
    `</button>
          <div className="md:hidden text-[var(--text-muted)] flex items-center ml-2">
            {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </div>
        </div>
      </div>`
  );

  // Replace separator with hidden on mobile unless expanded
  newHeader = newHeader.replace(
    /<div style=\{\{ width: "100%", height: "1px", background: "var\(--border\)", opacity: 0\.5 \}\} \/>/,
    '<div className="h-[1px] bg-[var(--border)] opacity-50 hidden md:block" />'
  );

  content = content.replace(headerMatch[0], newHeader);
}

// Wrap content
const contentRegex = /<div style=\{\{ display: "flex", flexDirection: "column", gap: "16px" \}\}>([\s\S]*?)\{\/\* PENDING PRODUCT MODAL \*\/\}/;
const contentMatch = content.match(contentRegex);

if (contentMatch) {
  let innerContent = contentMatch[1];
  let newContent = `<div className={\`flex-col gap-4 transition-all \${expanded ? 'flex animate-fade-in-fast' : 'hidden md:flex'}\`}>
        <div className="h-[1px] bg-[var(--border)] opacity-50 block md:hidden mb-2" />
        ${innerContent}
      `;
  content = content.replace(contentMatch[0], newContent + '{/* PENDING PRODUCT MODAL */}');
}

// Update the card padding
content = content.replace(
  /style=\{\{\s*padding: "24px",\s*display: "flex",\s*flexDirection: "column",\s*gap: "20px",\s*background: "var\(--bg-card\)",\s*border: "1px solid var\(--border\)",\s*borderRadius: "12px",\s*width: "100%"\s*\}\}/,
  'className="p-4 md:p-6 flex flex-col gap-4 md:gap-5 bg-[var(--bg-card)] border border-[var(--border)] rounded-[12px] w-full"'
);

fs.writeFileSync('src/components/search/WishlistSection.tsx', content);

let historyContent = fs.readFileSync('src/pages/TrackHistory.tsx', 'utf8');

historyContent = historyContent.replace(/padding: "32px 28px 48px"/g, 'padding: "32px 16px 48px"');
historyContent = historyContent.replace(/px-6/g, 'px-4 md:px-6');
historyContent = historyContent.replace(/pl-8/g, 'pl-6 md:pl-8');

fs.writeFileSync('src/pages/TrackHistory.tsx', historyContent);

