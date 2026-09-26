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

  const addUrl = async (url: string) => {
    setIsLoading(true);
    setError(null);
    try {
      // First, try to fetch product metadata from the backend
      // We need a store_id for lookup. We can use a default dummy store or fetch it from context.
      // Wait, let's just parse the url to get the product ID first.
      
      const parseRes = await fetch(`/api/product/parse-url?url=${encodeURIComponent(url)}`, {
        method: 'POST'
      });
      
      if (!parseRes.ok) {
        throw new Error('Please enter a valid Instamart product link.');
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
        const lookupRes = await fetch(`/api/product/lookup?url=${encodeURIComponent(canonicalUrl)}&store_id=${storeId}`);
        if (!lookupRes.ok) {
          throw new Error("Temporary platform error. Please try again.");
        }
        const lookupData = await lookupRes.json();
        if (lookupData.found) {
          name = lookupData.name || name;
          image_url = lookupData.image_url || image_url;
          price = lookupData.price || price;
          mrp = lookupData.mrp || mrp;
          brand = lookupData.brand || brand;
        } else {
          throw new Error("Couldn't find this product. Check that this is a valid Instamart product link.");
        }
      } catch (e: any) {
        if (e.message && e.message.includes("Couldn't find")) {
          throw e; // Re-throw product not found error
        }
        console.warn("Could not fetch rich metadata for wishlist product, falling back to basic details.", e);
        // We still allow adding if it's just a temporary network error, but the user requested explicit errors.
        // If we strictly want to prevent adding unknown products:
        throw new Error(e.message || "Could not resolve product details from Instamart.");
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
