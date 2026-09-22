export interface DealSearchConfig {
  categories: string[];
  keywords: string[];
  exclude_keywords: string[];
  
  location: {
    lat?: number;
    lng?: number;
    pincode?: string;
    local_store_id?: string;
  };

  radius_km: number;
  expansion_strategy: "NEARBY_FIRST" | "FULL_RADIUS";

  deal: {
    max_price?: number;
    min_price_drop_pct?: number;
    require_historical_low: boolean;
    condition_operator: "AND" | "OR";
    require_in_stock: boolean;
  };
}

export interface TelegramRecipient {
  id: string;
  name: string;
  type: string;
}

export interface SearchRequest {
  categories: string[];
  keywords: string[];
  exclude_keywords: string[];
  product_urls?: string[]; // Wishlist mode
  max_price?: number;
  min_price_drop_pct?: number;
  require_historical_low?: boolean;
  condition_operator?: "AND" | "OR";
  require_in_stock?: boolean;
  radius_km?: number;
  expansion_strategy?: "NEARBY_FIRST" | "FULL_RADIUS";
  lat?: number;
  lng?: number;
  pincode?: string;
  local_store_id?: string;
  platforms?: string[];
}

export interface Product {
  canonical_product_id?: string;
  external_product_id: string;
  name: string;
  brand?: string;
  size?: string;
  price: number;
  mrp: number;
  stock: boolean;
  image_url?: string;
  product_url?: string;
}

export interface Store {
  id: string;
  name?: string;
  platform?: string;
  address?: string;
  lat?: number;
  lng?: number;
  distance_km?: number;
}

export interface DealResult {
  deal_id?: string;
  product: Product;
  store: Store;
  discount_percent: number;
  price_drop_percent?: number;
  historical_low_before_now?: number;
  is_historical_low: boolean;
  trigger_reasons: string[];
  deal_level?: "EXCEPTIONAL" | "GREAT" | "GOOD" | "NORMAL";
  deal_score?: number;
  savings_amount?: number;
  applicable_rule?: string;
}

// SSE Events
export type SearchEventType = 
  | 'search_started'
  | 'location_resolved'
  | 'local_search_started'
  | 'product_discovered'
  | 'local_search_completed'
  | 'radius_expansion_started'
  | 'store_discovered'
  | 'store_scan_started'
  | 'store_scan_completed'
  | 'deal_found'
  | 'radius_completed'
  | 'search_completed'
  | 'search_cancelled'
  | 'search_error';

export interface SearchEvent {
  event: SearchEventType;
  data: any; // payload varies heavily based on event
}

export interface AlertRule {
  id?: string;
  categories: string[];
  keywords: string[];
  exclude_keywords: string[];
  min_discount_pct?: number;
  max_price?: number;
  min_price_drop_pct?: number;
  require_historical_low: boolean;
  condition_operator: string;
  require_in_stock: boolean;
  radius_km: number;
  expansion_strategy: string;
  ranking_strategy: string;
  platforms: string[];
  enabled: boolean;
  cooldown_hours: number;
}

export interface AlertEvent {
  id: string;
  alert_rule_id: string;
  instamart_product_id: string;
  store_id: string;
  price: number;
  mrp: number;
  discount_percent: number;
  previous_price?: number;
  price_drop_percent?: number;
  trigger_reason: string;
  triggered_at: string;
  notification_status: string;
  deal_level?: "EXCEPTIONAL" | "GREAT" | "GOOD" | "NORMAL";
  deal_score?: number;
  savings_amount?: number;
  applicable_rule?: string;
}

export interface PriceObservation {
  id?: string;
  instamart_product_id: string;
  store_id: string;
  observed_price: number;
  mrp: number;
  discount_percent: number;
  in_stock: boolean;
  timestamp: string;
}

export interface TargetRule {
  name: string;
  minDiscount: number | null;
}
