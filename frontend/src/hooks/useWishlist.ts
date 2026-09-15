import { useState, useEffect } from 'react';

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
}

const STORAGE_KEY = 'worth_it_wishlist';

export function useWishlist() {
  const [items, setItems] = useState<WishlistItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load from local storage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        setItems(JSON.parse(stored));
      }
    } catch (e) {
      console.error("Failed to parse wishlist from local storage", e);
    }
  }, []);

  // Save to local storage whenever items change
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  }, [items]);

  const addUrl = async (url: string) => {
    setIsLoading(true);
    setError(null);
    try {
      // First, try to fetch product metadata from the backend
      // We need a store_id for lookup. We can use a default dummy store or fetch it from context.
      // Wait, let's just parse the url to get the product ID first.
      
      const parseRes = await fetch(`/api/product-urls/parse-url?url=${encodeURIComponent(url)}`, {
        method: 'POST'
      });
      
      if (!parseRes.ok) {
        const err = await parseRes.json();
        throw new Error(err.detail || 'Invalid URL');
      }
      
      const parsedData = await parseRes.json();
      const productId = parsedData.product_id;
      const canonicalUrl = parsedData.canonical_url;

      // Check if already in wishlist
      if (items.some(item => item.id === productId)) {
        throw new Error("Product is already in your wishlist.");
      }

      // Try to get metadata (requires a store_id, if we don't have one, we can still just add it as 'Unknown')
      let name = `Product ${productId}`;
      let image_url = "";
      let price = 0;
      let mrp = 0;
      let brand = "";

      try {
        // Just try looking up at a popular default store to fetch metadata
        const storeId = localStorage.getItem('local_store_id') || '1394450';
        const lookupRes = await fetch(`/api/product-urls/lookup?url=${encodeURIComponent(canonicalUrl)}&store_id=${storeId}`);
        if (lookupRes.ok) {
          const lookupData = await lookupRes.json();
          if (lookupData.found) {
            name = lookupData.name || name;
            image_url = lookupData.image_url || image_url;
            price = lookupData.price || price;
            mrp = lookupData.mrp || mrp;
            brand = lookupData.brand || brand;
          }
        }
      } catch (e) {
        console.warn("Could not fetch rich metadata for wishlist product, falling back to basic details.");
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
        added_at: new Date().toISOString()
      };

      setItems(prev => [newItem, ...prev]);
      return true;
    } catch (err: any) {
      setError(err.message || 'Failed to add product');
      return false;
    } finally {
      setIsLoading(false);
    }
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

  return {
    items,
    isLoading,
    error,
    addUrl,
    removeUrl,
    toggleSelection,
    toggleAll
  };
}
