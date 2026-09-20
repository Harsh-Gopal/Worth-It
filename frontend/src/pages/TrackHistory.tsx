import { useState, useEffect } from "react";
import { History, ExternalLink, MapPin, ChevronDown, ChevronRight } from "lucide-react";
import { useLiveConsole } from "../store/liveConsoleStore";
import { ProductImage } from "../components/common/ProductImage";
interface HistoryEvent {
  id: string;
  triggered_at: string;
  product_name: string;
  product_image?: string;
  platform?: string;
  price: number;
  mrp: number;
  discount_percent: number;
  store_id?: string;
  store_name?: string;
  store_pincode?: string;
  search_pincode?: string;
  distance_km?: number;
  product_url?: string;
  origin_lat?: number;
  origin_lng?: number;
  trigger_reason?: string;
}

// Helper to format date
function formatDayLabel(dateString: string) {
  const d = new Date(dateString);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  
  if (d.toDateString() === today.toDateString()) return "Today";
  if (d.toDateString() === yesterday.toDateString()) return "Yesterday";
  return d.toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
}

// Format time
function formatTime(dateString: string) {
  return new Date(dateString).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}

export default function TrackHistory() {
  const [history, setHistory] = useState<HistoryEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedDates, setExpandedDates] = useState<Record<string, boolean>>({});
  const [expandedDuplicates, setExpandedDuplicates] = useState<Record<string, boolean>>({});

  const { logs } = useLiveConsole();

  // Load history from API
  useEffect(() => {
    fetch("/api/history/recent")
      .then(res => res.json())
      .then((data: HistoryEvent[]) => {
        setHistory(data);
        
        // Auto-expand "Today"
        const todayStr = new Date().toDateString();
        const initialExpanded: Record<string, boolean> = {};
        const uniqueDates = [...new Set(data.map(item => new Date(item.triggered_at).toDateString()))];
        uniqueDates.forEach(date => {
          initialExpanded[date] = (date === todayStr);
        });
        
        setExpandedDates(initialExpanded);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch history", err);
        setLoading(false);
      });
  }, []);

  // Listen for live updates via the global SSE context
  useEffect(() => {
    // get the latest log
    if (logs.length === 0) return;
    const latestLog = logs[logs.length - 1];
    if (latestLog.raw && latestLog.raw.id && latestLog.level === "INFO" && latestLog.message.startsWith("Alert persisted:")) {
       // This is a live event payload from alert_persisted
       const newEvent = latestLog.raw as HistoryEvent;
       setHistory(prev => {
         // Check if already exists to prevent duplicate injection
         if (prev.find(h => h.id === newEvent.id)) return prev;
         return [newEvent, ...prev];
       });
       // Ensure "Today" is expanded if a new event arrives
       setExpandedDates(prev => ({...prev, [new Date().toDateString()]: true}));
    }
  }, [logs]);

  const toggleDate = (date: string) => {
    setExpandedDates(prev => ({ ...prev, [date]: !prev[date] }));
  };
  
  const toggleDuplicate = (id: string) => {
    setExpandedDuplicates(prev => ({ ...prev, [id]: !prev[id] }));
  };

  if (loading) {
    return (
      <div className="flex flex-col gap-6 w-full p-4">
         <div className="flex items-center gap-3 border-b border-[var(--border)] pb-4">
           <History className="w-5 h-5 text-[var(--text-secondary)]" />
           <h2 className="text-lg font-semibold text-[var(--text-primary)] m-0">Deal History</h2>
         </div>
         {/* Skeletons */}
         {[1, 2, 3].map(i => (
           <div key={i} className="flex flex-col gap-4 animate-pulse">
             <div className="h-6 w-32 bg-[var(--bg-card)] border border-[var(--border)] rounded"></div>
             <div className="flex gap-4 ml-4 border-l-2 border-[var(--border)] pl-4 py-2">
               <div className="w-16 h-16 bg-[var(--bg-card)] border border-[var(--border)] rounded-lg"></div>
               <div className="flex flex-col gap-2 flex-1">
                 <div className="h-4 w-3/4 bg-[var(--bg-card)] border border-[var(--border)] rounded"></div>
                 <div className="h-4 w-1/2 bg-[var(--bg-card)] border border-[var(--border)] rounded"></div>
               </div>
             </div>
           </div>
         ))}
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="flex flex-col gap-6 w-full p-4">
        <div className="flex items-center gap-3 border-b border-[var(--border)] pb-4">
           <History className="w-5 h-5 text-[var(--text-secondary)]" />
           <h2 className="text-lg font-semibold text-[var(--text-primary)] m-0">Deal History</h2>
        </div>
        <div className="flex flex-col items-center justify-center py-24 text-center gap-4">
          <History className="w-12 h-12 text-[var(--text-secondary)] opacity-50" />
          <h3 className="text-lg font-medium text-[var(--text-primary)] m-0">No deal history yet</h3>
          <p className="text-[var(--text-secondary)] max-w-md m-0">Once Worth-It discovers a matching deal based on your criteria, it will appear here.</p>
        </div>
      </div>
    );
  }

  // Group by exact date string
  const groupedByDate: Record<string, HistoryEvent[]> = {};
  history.forEach(item => {
    const dStr = new Date(item.triggered_at).toDateString();
    if (!groupedByDate[dStr]) groupedByDate[dStr] = [];
    groupedByDate[dStr].push(item);
  });

  // Helper to deduplicate sequential items
  const buildTimeline = (items: HistoryEvent[]) => {
    const timeline: { primary: HistoryEvent, duplicates: HistoryEvent[] }[] = [];
    
    // Sort descending by time
    const sorted = [...items].sort((a, b) => new Date(b.triggered_at).getTime() - new Date(a.triggered_at).getTime());
    
    for (const item of sorted) {
      if (timeline.length === 0) {
        timeline.push({ primary: item, duplicates: [] });
        continue;
      }
      
      const last = timeline[timeline.length - 1];
      // Define a "duplicate" as same product_name and same store_id
      if (last.primary.product_name === item.product_name && last.primary.store_id === item.store_id && last.primary.price === item.price) {
        last.duplicates.push(item);
      } else {
        timeline.push({ primary: item, duplicates: [] });
      }
    }
    
    return timeline;
  };

  const generateMapLink = (item: HistoryEvent) => {
    if (item.origin_lat && item.origin_lng) {
      return `https://www.google.com/maps/search/?api=1&query=${item.origin_lat},${item.origin_lng}`;
    }
    if (item.store_pincode || item.search_pincode) {
      return `https://www.google.com/maps/search/?api=1&query=${item.store_pincode || item.search_pincode}+${item.store_name || ''}`;
    }
    return null;
  };

  return (
    <div className="flex flex-col gap-6 w-full pb-12 pr-4">
      <div className="flex items-center gap-3 border-b border-[var(--border)] pb-4">
        <History className="w-5 h-5 text-[var(--text-secondary)]" />
        <div>
          <h2 className="text-lg font-semibold text-[var(--text-primary)] m-0 leading-tight">Deal History</h2>
          <p className="text-xs text-[var(--text-secondary)] mt-1 m-0">Track what Worth-It discovered over time.</p>
        </div>
      </div>

      <div className="flex flex-col gap-4">
        {Object.entries(groupedByDate).sort((a, b) => new Date(b[0]).getTime() - new Date(a[0]).getTime()).map(([dateStr, items]) => {
          const isExpanded = expandedDates[dateStr];
          const uniqueProducts = new Set(items.map(i => i.product_name)).size;
          
          return (
            <div key={dateStr} className="flex flex-col rounded-xl overflow-hidden border border-[var(--border)] bg-[var(--bg-page)] shadow-sm">
              {/* Date Header */}
              <button 
                onClick={() => toggleDate(dateStr)}
                className="flex items-center justify-between p-4 bg-[var(--bg-card)] hover:opacity-90 transition-opacity text-left cursor-pointer border-none m-0"
              >
                <div className="flex items-center gap-4">
                  <span className="font-semibold text-[var(--text-primary)] text-sm uppercase tracking-wider">
                    {formatDayLabel(dateStr)}
                  </span>
                  <span className="text-xs text-[var(--text-secondary)] bg-[var(--bg-page)] px-2 py-1 rounded border border-[var(--border)]">
                    {items.length} deals · {uniqueProducts} products
                  </span>
                </div>
                {isExpanded ? <ChevronDown className="w-5 h-5 text-[var(--text-secondary)]" /> : <ChevronRight className="w-5 h-5 text-[var(--text-secondary)]" />}
              </button>

              {/* Timeline content */}
              {isExpanded && (
                <div className="p-6 flex flex-col gap-0 bg-[var(--bg-page)] border-t border-[var(--border)]">
                  {buildTimeline(items).map((group) => {
                    const item = group.primary;
                    const mapLink = generateMapLink(item);
                    
                    return (
                      <div key={item.id} className="relative pl-6 pb-8 last:pb-0">
                        {/* Timeline visual line */}
                        <div className="absolute left-[3px] top-7 bottom-[-7px] w-px bg-[var(--border)] last:hidden"></div>
                        {/* Timeline dot */}
                        <div className="absolute left-0 top-1.5 w-2 h-2 rounded-full bg-[var(--color-brand-green)] border-[1.5px] border-[var(--bg-page)] shadow-[0_0_0_2px_var(--bg-page)]"></div>
                        
                        {/* Time Label */}
                        <div className="text-xs font-semibold text-[var(--text-secondary)] mb-3 flex items-center gap-2">
                          {formatTime(item.triggered_at)}
                          {item.trigger_reason && (
                            <span className="text-[9px] uppercase tracking-wider bg-[var(--color-brand-green)] text-white px-1.5 py-0.5 rounded-sm opacity-80">
                              {item.trigger_reason}
                            </span>
                          )}
                        </div>
                        
                        {/* Deal Card */}
                        <div className="flex flex-col sm:flex-row gap-4 bg-[var(--bg-card)] border border-[var(--border)] p-4 rounded-xl shadow-[0_1px_3px_rgba(0,0,0,0.05)]">
                          
                          {/* Image */}
                          <div className="w-20 h-20 shrink-0 bg-white border border-[var(--border)] rounded-lg flex items-center justify-center overflow-hidden p-1">
                            <ProductImage
                              src={item.product_image}
                              alt="Product"
                              productName={item.product_name}
                              category={undefined}
                              className="w-full h-full object-contain"
                              fallbackClassName="w-10 h-10 text-[var(--border)]"
                            />
                          </div>
                          
                          {/* Content */}
                          <div className="flex flex-col flex-1 min-w-0">
                            <div className="flex flex-wrap items-start justify-between gap-4">
                              <div className="flex flex-col gap-1 pr-4 max-w-[70%]">
                                <h3 className="font-semibold text-sm text-[var(--text-primary)] leading-snug line-clamp-2 m-0">
                                  {item.product_name}
                                </h3>
                                
                                <div className="flex flex-wrap items-center gap-2 mt-2">
                                  <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-secondary)] bg-[var(--bg-page)] px-2 py-0.5 rounded border border-[var(--border)] inline-block">
                                    {item.platform || "Instamart"}
                                  </span>
                                  
                                  <div className="flex flex-wrap items-center gap-1 text-xs text-[var(--text-secondary)]">
                                    <MapPin className="w-3.5 h-3.5 opacity-70" />
                                    <span>
                                      {item.store_pincode && <strong>{item.store_pincode} </strong>}
                                      {item.store_name}
                                      {item.distance_km && ` · ${item.distance_km.toFixed(1)} km`}
                                    </span>
                                  </div>
                                </div>
                              </div>
                              
                              {/* Pricing */}
                              <div className="flex flex-col items-end shrink-0 bg-[var(--bg-page)] px-3 py-2 rounded-lg border border-[var(--border)]">
                                <div className="text-lg font-bold text-[var(--text-primary)] leading-none mb-1.5">
                                  ₹{item.price}
                                </div>
                                <div className="flex items-center gap-2 text-xs">
                                  {item.mrp > item.price && (
                                    <span className="text-[var(--text-secondary)] line-through">₹{item.mrp}</span>
                                  )}
                                  {item.discount_percent > 0 ? (
                                    <span className="text-[var(--color-brand-green)] font-bold">{Math.round(item.discount_percent)}% OFF</span>
                                  ) : (
                                    <span className="text-[var(--text-secondary)]">Price detected</span>
                                  )}
                                </div>
                              </div>
                            </div>
                            
                            {/* Actions & Duplicates */}
                            <div className="flex flex-wrap items-center justify-between gap-4 mt-4 pt-3 border-t border-[var(--border)]">
                              
                              <div className="flex gap-2">
                                {item.product_url && (
                                  <a href={item.product_url} target="_blank" rel="noreferrer" 
                                    className="no-underline text-xs font-medium text-[var(--text-primary)] bg-[var(--bg-page)] hover:bg-[#e2e8f0] border border-[var(--border)] px-3 py-1.5 rounded-md flex items-center gap-1.5 transition-colors">
                                    <ExternalLink className="w-3.5 h-3.5" />
                                    Open Product
                                  </a>
                                )}
                                {mapLink && (
                                  <a href={mapLink} target="_blank" rel="noreferrer"
                                    className="no-underline text-xs font-medium text-[var(--text-secondary)] bg-[var(--bg-page)] hover:bg-[#e2e8f0] border border-[var(--border)] px-3 py-1.5 rounded-md flex items-center gap-1.5 transition-colors">
                                    <MapPin className="w-3.5 h-3.5" />
                                    View Map
                                  </a>
                                )}
                              </div>
                              
                              {group.duplicates.length > 0 && (
                                <button 
                                  onClick={() => toggleDuplicate(item.id)}
                                  className="cursor-pointer border-none m-0 text-xs font-medium text-[var(--color-brand-green)] hover:opacity-80 flex items-center gap-1 bg-green-500/10 px-2 py-1 rounded transition-opacity"
                                >
                                  Detected {group.duplicates.length + 1} times today
                                  {expandedDuplicates[item.id] ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                                </button>
                              )}
                            </div>
                            
                            {/* Expanded Duplicates */}
                            {group.duplicates.length > 0 && expandedDuplicates[item.id] && (
                              <div className="mt-3 bg-[var(--bg-page)] border border-[var(--border)] rounded-lg p-3 text-xs flex flex-col gap-2">
                                <div className="text-[var(--text-secondary)] font-medium mb-1">Earlier detections:</div>
                                {group.duplicates.map(dup => (
                                  <div key={dup.id} className="flex justify-between items-center py-1 border-b border-[var(--border)] last:border-0 last:pb-0">
                                    <span className="text-[var(--text-secondary)] font-mono">{formatTime(dup.triggered_at)}</span>
                                    <span className="text-[var(--text-primary)] font-medium">₹{dup.price} ({Math.round(dup.discount_percent)}% OFF)</span>
                                  </div>
                                ))}
                              </div>
                            )}
                            
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
