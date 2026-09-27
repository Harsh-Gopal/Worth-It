import { useState, useEffect } from 'react';
import { API_BASE } from "../lib/api";

export interface WishlistItem {
  id: string;
  url: string;
  name: string;
  image_url: string;
  price: number;
  mrp: number;
  brand?: string;
  selected: boolean;
  added_at: string;
  min_discount_pct?: number;
}

const STORAGE_KEY = 'worth_it_wishlist';

export function useWishlist() {
  const [items, setItems] = useState<WishlistItem[]>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) return parsed;
      }
    } catch (e) {
      console.error("Failed to parse wishlist from local storage", e);
    }
    return [];
  });

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Save to local storage whenever items change
  useEffect(() => {
    if (items) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
      window.dispatchEvent(new CustomEvent('wishlist_changed'));
    }
  }, [items]);

  // Sync with backend so URLs added/removed via Telegram appear in the UI
  useEffect(() => {
    const syncBackendUrls = async () => {
      try {
        const res = await fetch(`${API_BASE}/alerts/primary`);
        if (res.ok) {
          const config = await res.json();
          const backendUrls: string[] = config.product_urls || [];
          
          setItems(prevItems => {
            const existingUrls = new Set(prevItems.map(i => i.url));
            const backendSet = new Set(backendUrls);
            
            // If the user has never submitted anything to backend, we shouldn't wipe their local list.
            // But if they have, we must sync deletions. 
            // We can assume if backend has config or we have a lot of items, we should sync.
            // A simple heuristic: remove items from frontend that are not in backend,
            // EXCEPT if backend is completely empty and frontend has items (they might just be staging them).
            // Actually, to fulfill the requirement perfectly: just sync exactly.
            
            let newItems = prevItems.filter(item => backendSet.has(item.url));
            const missingUrls = backendUrls.filter(u => !existingUrls.has(u));
            
            if (missingUrls.length > 0) {
              setTimeout(() => {
                missingUrls.forEach(async (url) => {
                  const resolved = await resolveUrl(url);
                  if (resolved) {
                    commitProduct(resolved, 15);
                  }
                });
              }, 100);
            }
            
            // If we are about to wipe staging items because backend is empty, let's keep them
            // unless we know for sure they were deleted.
            if (backendUrls.length === 0 && prevItems.length > 0) {
               // If tracking is active but backend has no URLs, it means they were removed.
               if (config.enabled || config.updated_at) {
                   return newItems;
               }
               return prevItems;
            }
            
            return newItems;
          });
        }
      } catch (err) {
        console.error("Failed to sync wishlist from backend", err);
      }
    };
    syncBackendUrls();
  }, []);

  const resolveUrl = async (url: string): Promise<WishlistItem | null> => {
    setIsLoading(true);
    setError(null);
    try {
      const parseRes = await fetch(`${API_BASE}/product/parse-url?url=${encodeURIComponent(url)}`, {
        method: 'POST'
      });
      
      if (!parseRes.ok) {
        throw new Error('Please enter a valid product link.');
      }
      
      const parsedData = await parseRes.json();
      const productId = parsedData.product_id;
      const canonicalUrl = parsedData.canonical_url;

      if (items.some(item => item.id === productId)) {
        throw new Error("Product is already in your wishlist.");
      }

      let name = `Product ${productId}`;
      let image_url = "";
      let price = 0;
      let mrp = 0;
      let brand = "";

      try {
        const storeId = localStorage.getItem('local_store_id') || '1394450';
        const lookupRes = await fetch(`${API_BASE}/product/lookup?url=${encodeURIComponent(canonicalUrl)}&store_id=${storeId}`);
        if (!lookupRes.ok) {
          let errData;
          try {
            errData = await lookupRes.json();
          } catch (e) {
            errData = {};
          }
          throw new Error(errData.detail || `Temporary platform error. Please try again.`);
        }
        
        const lookupData = await lookupRes.json();
        if (lookupData.found) {
          name = lookupData.name || name;
          image_url = lookupData.image_url || image_url;
          price = lookupData.price || price;
          mrp = lookupData.mrp || mrp;
          brand = lookupData.brand || brand;
        } else {
          throw new Error(lookupData.error || "Could not resolve this product.");
        }
      } catch (e: any) {
        console.warn("Could not fetch rich metadata for wishlist product, falling back to basic details.", e);
        throw new Error(e.message || "Could not resolve product details.");
      }

      const newItem: WishlistItem = {
        id: productId,
        url: canonicalUrl,
        name,
        image_url,
        price,
        mrp,
        brand,
        selected: true,
        added_at: new Date().toISOString(),
        min_discount_pct: 15
      };

      return newItem;
    } catch (err: any) {
      setError(err.message || 'Failed to resolve product');
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const commitProduct = (item: WishlistItem, minDiscount: number) => {
    item.min_discount_pct = minDiscount;
    setItems(prev => [item, ...prev]);
  };

  const removeUrl = (id: string) => {
    setItems(prev => prev.filter(item => item.id !== id));
  };

  const toggleSelection = (id: string) => {
    setItems(prev => prev.map(item => 
      item.id === id ? { ...item, selected: !item.selected } : item
    ));
  };

  const toggleAll = (selected: boolean) => {
    setItems(prev => prev.map(item => ({ ...item, selected })));
  };

  const reorderItems = (startIndex: number, endIndex: number) => {
    setItems(prev => {
      const result = Array.from(prev);
      const [removed] = result.splice(startIndex, 1);
      result.splice(endIndex, 0, removed);
      return result;
    });
  };

  return {
    items,
    isLoading,
    error,
    resolveUrl,
    commitProduct,
    removeUrl,
    toggleSelection,
    toggleAll,
    reorderItems
  };
}
