import { useState, useEffect } from "react";
import { History, ExternalLink, MapPin, ChevronDown, ChevronRight, Check } from "lucide-react";
import { useLiveConsole } from "../store/liveConsoleStore";
import { ProductImage } from "../components/common/ProductImage";

interface AlertEvent {
  id: string;
  store_id?: string;
  store_name?: string;
  store_pincode?: string;
  search_pincode?: string;
  distance_km?: number;
  price: number;
  mrp: number;
  discount_percent: number;
  product_url?: string;
  origin_lat?: number;
  origin_lng?: number;
  triggered_at: string;
}

interface GroupedHistoryEvent {
  group_id: string;
  instamart_product_id?: string;
  product_name: string;
  product_image?: string | null;
  platform?: string;
  category?: string | null;
  best_price: number;
  mrp: number;
  best_discount_percent: number;
  deal_level?: "EXCEPTIONAL" | "GREAT" | "GOOD" | "NORMAL" | string | null;
  deal_score?: number | null;
  savings_amount?: number | null;
  trigger_reason?: string;
  triggered_at: string;
  local_date: string;
  locations_count: number;
  platforms_count: number;
  offers: AlertEvent[];
}

// Format time
function formatTime(dateString: string) {
  return new Date(dateString).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}

export default function TrackHistory() {
  const [history, setHistory] = useState<GroupedHistoryEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedDates, setExpandedDates] = useState<Record<string, boolean>>({});
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});
  const [deletingDate, setDeletingDate] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const { logs } = useLiveConsole();

  // Load history from API
  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const offsetMins = new Date().getTimezoneOffset();
      const res = await fetch(`/api/history/recent?tz_offset_mins=${offsetMins}`);
      if (res.ok) {
        const data: GroupedHistoryEvent[] = await res.json();
        setHistory(data);
        
        // Group by local_date to find today
        const grouped = data.reduce((acc: Record<string, GroupedHistoryEvent[]>, curr: GroupedHistoryEvent) => {
          const dateStr = curr.local_date;
          if (!acc[dateStr]) acc[dateStr] = [];
          acc[dateStr].push(curr);
          return acc;
        }, {});
        
        // Auto-expand the most recent date (which is usually today)
        const sortedDates = Object.keys(grouped).sort((a, b) => new Date(b).getTime() - new Date(a).getTime());
        const initialExpanded: Record<string, boolean> = {};
        sortedDates.forEach((date, idx) => {
          initialExpanded[date] = (idx === 0);
        });
        
        setExpandedDates(initialExpanded);
      }
    } catch (err) {
      console.error("Failed to load history", err);
    } finally {
      setLoading(false);
    }
  };

  // Listen for live updates via the global SSE context
  useEffect(() => {
    // get the latest log
    if (logs.length === 0) return;
    const latestLog = logs[logs.length - 1];
    if (latestLog.raw && latestLog.level === "INFO" && latestLog.message.startsWith("Grouped Alert persisted:")) {
       // This is a live event payload from alert_group_persisted
       const newGroup = latestLog.raw as GroupedHistoryEvent;
       setHistory(prev => {
         // Check if already exists (by group_id) to prevent duplicate injection
         const exists = prev.find(h => h.group_id === newGroup.group_id);
         if (exists) {
            // Replace the existing group with the new updated group from backend
            return prev.map(h => h.group_id === newGroup.group_id ? newGroup : h);
         }
         return [newGroup, ...prev];
       });
       // Ensure today's date is expanded if a new event arrives
       if (newGroup.local_date) {
         setExpandedDates(prev => ({...prev, [newGroup.local_date]: true}));
       }
    }
  }, [logs]);

  const toggleDate = (date: string) => {
    setExpandedDates(prev => ({ ...prev, [date]: !prev[date] }));
  };
  
  const toggleGroup = (groupId: string) => {
    setExpandedGroups(prev => ({ ...prev, [groupId]: !prev[groupId] }));
  };

  const deleteDateHistory = async (dateStr: string) => {
    setDeleteError(null);
    try {
      const offsetMins = new Date().getTimezoneOffset();
      const res = await fetch(`/api/history/date/${dateStr}?tz_offset_mins=${offsetMins}`, {
        method: "DELETE"
      });
      if (res.ok) {
        // Only remove from UI after confirmed backend deletion
        setHistory(prev => prev.filter(item => item.local_date !== dateStr));
        setDeletingDate(null);
      } else {
        const data = await res.json().catch(() => ({}));
        setDeleteError(data?.detail || "Failed to delete history. Please try again.");
        setDeletingDate(null);
      }
    } catch {
      setDeleteError("Network error. History could not be deleted.");
      setDeletingDate(null);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col gap-8 w-full max-w-[1100px] mx-auto px-6 py-8 md:px-10 md:py-10">
        <div className="flex flex-col mb-2">
          <div className="flex items-center gap-3 mb-6">
            <History className="w-7 h-7 text-[var(--text-secondary)]" />
            <div>
              <h2 className="text-[26px] font-bold text-[var(--text-primary)] m-0 leading-tight tracking-tight">Deal History</h2>
              <p className="text-[14px] text-[var(--text-secondary)] mt-1.5 m-0 leading-relaxed">Track what Worth-It discovered over time.</p>
            </div>
          </div>
          <div className="w-full h-px bg-[var(--border)] opacity-70"></div>
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
      <div className="flex flex-col gap-8 w-full max-w-[1100px] mx-auto px-6 py-8 md:px-10 md:py-10">
        <div className="flex flex-col mb-2">
          <div className="flex items-center gap-3 mb-6">
            <History className="w-7 h-7 text-[var(--text-secondary)]" />
            <div>
              <h2 className="text-[26px] font-bold text-[var(--text-primary)] m-0 leading-tight tracking-tight">Deal History</h2>
              <p className="text-[14px] text-[var(--text-secondary)] mt-1.5 m-0 leading-relaxed">Track what Worth-It discovered over time.</p>
            </div>
          </div>
          <div className="w-full h-px bg-[var(--border)] opacity-70"></div>
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
  const groupedByDate: Record<string, GroupedHistoryEvent[]> = {};
  history.forEach(item => {
    const dStr = item.local_date;
    if (!groupedByDate[dStr]) groupedByDate[dStr] = [];
    groupedByDate[dStr].push(item);
  });

  const formatDayLabel = (dateStr: string) => {
    // dateStr is YYYY-MM-DD
    const parts = dateStr.split('-');
    if (parts.length !== 3) return dateStr;
    
    // Create Date object correctly in local timezone
    const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (d.getTime() === today.getTime()) return "Today";
    if (d.getTime() === yesterday.getTime()) return "Yesterday";

    return d.toLocaleDateString('en-US', { day: 'numeric', month: 'long' });
  };

  const generateMapLink = (item: AlertEvent) => {
    if (item.origin_lat && item.origin_lng) {
      return `https://www.google.com/maps/search/?api=1&query=${item.origin_lat},${item.origin_lng}`;
    }
    if (item.store_pincode || item.search_pincode) {
      return `https://www.google.com/maps/search/?api=1&query=${item.store_pincode || item.search_pincode}+${item.store_name || ''}`;
    }
    return null;
  };

  return (
    <div className="flex flex-col gap-8 w-full max-w-[1100px] mx-auto px-6 py-8 md:px-10 md:py-10">
      
      {/* Header Section */}
      <div className="flex flex-col mb-2">
        <div className="flex items-center gap-3 mb-6">
          <History className="w-7 h-7 text-[var(--text-secondary)]" />
          <div>
            <h2 className="text-[26px] font-bold text-[var(--text-primary)] m-0 leading-tight tracking-tight">Deal History</h2>
            <p className="text-[14px] text-[var(--text-secondary)] mt-1.5 m-0 leading-relaxed">Track what Worth-It discovered over time.</p>
          </div>
        </div>
        <div className="w-full h-px bg-[var(--border)] opacity-70"></div>
      </div>

      {/* Delete error toast */}
      {deleteError && (
        <div className="flex items-center justify-between px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm shadow-sm mb-2">
          <span className="text-red-700 font-medium">{deleteError}</span>
          <button onClick={() => setDeleteError(null)} className="ml-3 text-red-500 hover:text-red-700 border-none bg-transparent cursor-pointer text-base leading-none p-1">×</button>
        </div>
      )}

      {/* History Content */}
      <div className="flex flex-col gap-8">
        {Object.entries(groupedByDate).sort((a, b) => new Date(b[0]).getTime() - new Date(a[0]).getTime()).map(([dateStr, items]) => {
          const isExpanded = expandedDates[dateStr];
          const isDeleting = deletingDate === dateStr;
          
          // Compute accurate counts
          const uniqueProducts = items.length; // one GroupedHistoryEvent per unique product
          const totalDiscoveries = items.reduce((sum, i) => sum + (i.locations_count || 1), 0);
          const totalPlatforms = new Set(items.map(i => i.platform)).size;
          
          // Determine if this date is today (prevent accidental today deletion)
          const dateParts = dateStr.split('-');
          const dateLocal = dateParts.length === 3
            ? new Date(parseInt(dateParts[0]), parseInt(dateParts[1]) - 1, parseInt(dateParts[2]))
            : null;
          const todayLocal = new Date();
          todayLocal.setHours(0, 0, 0, 0);
          const isToday = dateLocal ? dateLocal.getTime() === todayLocal.getTime() : false;
          
          return (
            <div key={dateStr} className="flex flex-col rounded-2xl overflow-hidden border border-[var(--border)] bg-[var(--bg-page)] shadow-[0_2px_8px_rgba(0,0,0,0.04)]">
              {/* Date Header */}
              {isDeleting ? (
                <div className="flex items-center justify-between px-6 py-5 bg-red-50/50 border-b border-red-100">
                  <div className="flex flex-col gap-1.5">
                    <span className="font-bold text-red-800 text-[14px]">Delete {formatDayLabel(dateStr)}'s history?</span>
                    <span className="text-[13px] text-red-600">This will permanently remove {totalDiscoveries} discoveries across {uniqueProducts} product{uniqueProducts !== 1 ? 's' : ''}.</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <button 
                      onClick={() => setDeletingDate(null)}
                      className="px-4 py-2 text-[13px] font-semibold bg-white border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      Cancel
                    </button>
                    <button 
                      onClick={() => deleteDateHistory(dateStr)}
                      className="px-4 py-2 text-[13px] font-semibold bg-red-600 border border-transparent text-white rounded-lg hover:bg-red-700 cursor-pointer shadow-sm transition-colors"
                    >
                      Delete History
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-between px-6 py-5 bg-[var(--bg-card)] hover:bg-[#f8fafc] dark:hover:bg-[#1e293b] transition-colors border-none m-0 group">
                  <button 
                    onClick={() => toggleDate(dateStr)}
                    className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 text-left cursor-pointer border-none bg-transparent m-0 flex-1 outline-none"
                  >
                    <span className="font-bold text-[var(--text-primary)] text-[13px] uppercase tracking-wider">
                      {formatDayLabel(dateStr)}
                    </span>
                    <span className="text-[13px] text-[var(--text-secondary)] font-medium">
                      {totalDiscoveries} {totalDiscoveries === 1 ? 'discovery' : 'discoveries'} · {uniqueProducts} product{uniqueProducts !== 1 ? 's' : ''} · {totalPlatforms} platform{totalPlatforms !== 1 ? 's' : ''}
                    </span>
                  </button>
                  <div className="flex items-center gap-4 pr-1">
                    {!isToday && (
                      <button 
                        onClick={() => setDeletingDate(dateStr)}
                        className="text-[var(--text-muted)] hover:text-red-500 hover:bg-red-50 w-8 h-8 flex items-center justify-center rounded-md transition-colors cursor-pointer border-none bg-transparent opacity-0 group-hover:opacity-100 focus:opacity-100"
                        title="Delete history for this date"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/></svg>
                      </button>
                    )}
                    <button onClick={() => toggleDate(dateStr)} className="cursor-pointer border-none bg-transparent w-8 h-8 flex items-center justify-center rounded-md hover:bg-[#e2e8f0] dark:hover:bg-[#334155] transition-colors outline-none">
                      <ChevronDown className={`w-5 h-5 text-[var(--text-secondary)] transition-transform duration-200 ${isExpanded ? 'rotate-0' : '-rotate-90'}`} />
                    </button>
                  </div>
                </div>
              )}

              {/* Timeline content */}
              {isExpanded && (
                <div className="px-6 py-8 sm:px-10 sm:py-10 flex flex-col gap-0 bg-[var(--bg-page)] border-t border-[var(--border)]">
                  {items.map((group, idx, arr) => {
                    const isLast = idx === arr.length - 1;
                    return (
                      <div key={group.group_id} className="relative pl-8 pb-10 last:pb-0">
                        {/* Timeline visual line */}
                        {!isLast && (
                          <div className="absolute left-[5px] top-7 bottom-[-16px] w-[2px] bg-[var(--border)] opacity-60"></div>
                        )}
                        {/* Timeline dot */}
                        <div className="absolute left-0 top-2 w-3 h-3 rounded-full bg-[var(--color-brand-green)] border-[2px] border-[var(--bg-page)] shadow-[0_0_0_2px_var(--bg-page)] z-10"></div>
                        
                        {/* Time Label */}
                        <div className="text-[12px] font-semibold text-[var(--text-secondary)] mb-4 flex items-center gap-3">
                          {formatTime(group.triggered_at)}
                          <span className="text-[10px] font-bold uppercase tracking-wider bg-[#dcfce7] text-[#166534] dark:bg-[rgba(34,197,94,0.15)] dark:text-[var(--color-brand-green)] px-2 py-1 rounded-md shadow-sm">
                            DEAL DISCOVERED
                          </span>
                        </div>
                        
                        {/* Grouped Deal Card */}
                        <div className="flex flex-col bg-[var(--bg-card)] border border-[var(--border)] p-5 rounded-xl shadow-sm hover:shadow-md transition-shadow">
                          
                          <div className="flex flex-col sm:flex-row gap-4 mb-2">
                            {/* Image */}
                            <div className="w-20 h-20 shrink-0 bg-white border border-[var(--border)] rounded-lg flex items-center justify-center overflow-hidden p-1">
                              <ProductImage
                                src={group.product_image ?? undefined}
                                alt="Product"
                                productName={group.product_name}
                                category={group.category ?? undefined}
                                className="w-full h-full object-contain"
                                fallbackClassName="w-10 h-10 text-[var(--border)]"
                              />
                            </div>
                            
                            {/* Content */}
                            <div className="flex flex-col flex-1 min-w-0">
                              <div className="flex flex-wrap items-start justify-between gap-4">
                                <div className="flex flex-col gap-1.5 flex-1 min-w-0 pr-4">
                                  <h3 className="font-semibold text-sm text-[var(--text-primary)] leading-snug line-clamp-2 m-0">
                                    {group.product_name}
                                  </h3>
                                  
                                  <div className="flex flex-wrap items-center gap-2 mt-1">
                                    <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-secondary)] bg-[var(--bg-page)] px-2 py-0.5 rounded border border-[var(--border)] inline-block">
                                      {group.platform || "Instamart"}
                                      {group.category ? ` • ${group.category}` : ''}
                                    </span>
                                  </div>

                                  {/* Deal Intelligence area */}
                                  {(group.deal_level || group.trigger_reason) && (
                                    <div className="mt-1 flex flex-col gap-1.5 border border-[var(--border)] bg-[#f8fafc] rounded p-2">
                                      <div className="flex items-center flex-wrap gap-2">
                                        <Check className="w-3.5 h-3.5 text-[var(--color-brand-green)]" />
                                        <span className="text-[11px] text-[var(--text-primary)] font-medium">Best price across {group.locations_count} locations</span>
                                      </div>
                                      {group.deal_level && (
                                        <div className="flex items-center flex-wrap gap-2">
                                          <Check className="w-3.5 h-3.5 text-[var(--color-brand-green)]" />
                                          <span className={`text-[11px] font-bold`}>
                                            {group.deal_level === 'EXCEPTIONAL' ? 'Exceptional Deal' : group.deal_level === 'GREAT' ? 'Great Deal' : 'Good Deal'}
                                          </span>
                                        </div>
                                      )}
                                      {group.trigger_reason && (
                                        <div className="flex items-center flex-wrap gap-2">
                                          <Check className="w-3.5 h-3.5 text-[var(--color-brand-green)]" />
                                          <span className="text-[11px] text-[var(--text-secondary)] font-medium">
                                            {group.trigger_reason}
                                          </span>
                                        </div>
                                      )}
                                    </div>
                                  )}
                                </div>
                                <div className="flex flex-col items-end shrink-0 bg-[var(--bg-page)] px-3 py-2 rounded-lg border border-[var(--border)]">
                                  <div className="text-lg font-bold text-[var(--text-primary)] leading-none mb-1.5">
                                    ₹{group.best_price}
                                  </div>
                                  <div className="flex items-center gap-2 text-xs">
                                    {group.mrp > group.best_price && (
                                      <span className="text-[var(--text-secondary)] line-through">₹{group.mrp}</span>
                                    )}
                                    {group.best_discount_percent > 0 && (
                                      <span className="text-[var(--color-brand-green)] font-bold">{Math.round(group.best_discount_percent)}% OFF</span>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                          
                          {/* Available Locations Expander */}
                          <div className="mt-3 border-t border-[var(--border)] pt-2">
                            <button 
                              onClick={() => toggleGroup(group.group_id)}
                              className="w-full flex items-center justify-center gap-2 py-2 text-[12px] font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[#f1f5f9] rounded-md transition-colors cursor-pointer border-none bg-transparent m-0"
                            >
                              Available at {group.locations_count} location{group.locations_count !== 1 ? 's' : ''} {group.platforms_count > 1 ? ` • ${group.platforms_count} platforms` : ''}
                              {expandedGroups[group.group_id] ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                            </button>
                            
                            {expandedGroups[group.group_id] && (
                              <div className="mt-2 flex flex-col gap-2 animate-in fade-in slide-in-from-top-2 duration-200">
                                {group.offers.sort((a,b) => a.price - b.price).map((offer, idx) => {
                                  const mapLink = generateMapLink(offer);
                                  return (
                                    <div key={`${offer.id}-${idx}`} className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-3 bg-[var(--bg-page)] rounded border border-[var(--border)] gap-3 hover:border-gray-300 transition-colors">
                                      <div className="flex flex-col gap-1 min-w-0">
                                        <div className="flex items-center gap-2 text-[13px]">
                                          <span className="font-bold text-[var(--text-primary)]">₹{offer.price}</span>
                                          {offer.discount_percent > 0 && (
                                            <span className="font-bold text-[var(--color-brand-green)]">{Math.round(offer.discount_percent)}% OFF</span>
                                          )}
                                        </div>
                                        <div className="flex flex-wrap items-center gap-1.5 text-[11px] text-[var(--text-secondary)] font-medium">
                                          <MapPin className="w-3 h-3 opacity-70" />
                                          {offer.store_pincode && <span className="font-bold">📍 {offer.store_pincode}</span>}
                                          {offer.store_name && <span>{offer.store_name}</span>}
                                          {offer.distance_km !== undefined && <span>· {offer.distance_km.toFixed(1)} km</span>}
                                        </div>
                                      </div>
                                      
                                      <div className="flex gap-2 self-end sm:self-auto shrink-0">
                                        {offer.product_url && (
                                          <a href={offer.product_url} target="_blank" rel="noreferrer" 
                                            className="no-underline text-[11px] font-semibold text-[var(--text-primary)] bg-white hover:bg-gray-50 border border-[var(--border)] px-2.5 py-1.5 rounded flex items-center gap-1 transition-colors shadow-sm">
                                            <ExternalLink className="w-3 h-3" />
                                            Open Product
                                          </a>
                                        )}
                                        {mapLink && (
                                          <a href={mapLink} target="_blank" rel="noreferrer"
                                            className="no-underline text-[11px] font-semibold text-[var(--text-secondary)] bg-white hover:bg-gray-50 border border-[var(--border)] px-2.5 py-1.5 rounded flex items-center gap-1 transition-colors shadow-sm">
                                            <MapPin className="w-3 h-3" />
                                            Map
                                          </a>
                                        )}
                                      </div>
                                    </div>
                                  );
                                })}
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
