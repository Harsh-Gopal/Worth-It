import { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from "react-leaflet";
import L from "leaflet";
import type { Store, DealResult } from "../../lib/types";
import "leaflet/dist/leaflet.css";

// Fix leaflet default icons in React
import icon from "leaflet/dist/images/marker-icon.png";
import iconShadow from "leaflet/dist/images/marker-shadow.png";

let DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});
L.Marker.prototype.options.icon = DefaultIcon;

// Custom icons based on state
const storeIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-grey.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

const dealIcon = new L.Icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-orange.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

// A component to automatically fit the map bounds to all markers
function MapBounds({ stores }: { stores: Store[] }) {
  const map = useMap();
  useEffect(() => {
    if (stores.length > 0) {
      const bounds = L.latLngBounds(stores.filter(s => s.lat && s.lng).map((s) => [s.lat!, s.lng!]));
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 14 });
    }
  }, [stores, map]);
  return null;
}

interface DealMapProps {
  stores: Record<string, Store>;
  deals: DealResult[];
  currentRadiusKm: number;
  centerLat?: number;
  centerLng?: number;
}

export default function DealMap({ stores, deals, currentRadiusKm, centerLat, centerLng }: DealMapProps) {
  const defaultLat = 12.9716; // Fallback Bangalore
  const defaultLng = 77.5946;

  const lat = centerLat || defaultLat;
  const lng = centerLng || defaultLng;

  const storeList = Object.values(stores);
  const dealStoreIds = new Set(deals.map((d) => d.store.id));

  return (
    <div className="w-full h-full min-h-[400px] relative z-0">
      <MapContainer center={[lat, lng]} zoom={12} scrollWheelZoom={false} className="h-full w-full">
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        />

        {/* User Location Center Marker */}
        <Marker position={[lat, lng]}>
          <Popup>Your Location</Popup>
        </Marker>

        {/* Radius Circle */}
        {currentRadiusKm > 0 && (
          <Circle
            center={[lat, lng]}
            radius={currentRadiusKm * 1000}
            pathOptions={{ color: "#f43f5e", fillColor: "#f43f5e", fillOpacity: 0.05, weight: 1 }}
          />
        )}

        {/* Store & Deal Markers */}
        {storeList.map((store) => {
          if (!store.lat || !store.lng) return null;
          const isDeal = dealStoreIds.has(store.id);
          const relatedDeals = deals.filter(d => d.store.id === store.id);

          return (
            <Marker 
              key={store.id} 
              position={[store.lat, store.lng]}
              icon={isDeal ? dealIcon : storeIcon}
            >
              <Popup className="rounded-xl">
                <div className="p-1">
                  <h4 className="font-bold text-slate-800">{store.name}</h4>
                  <p className="text-xs text-slate-500 mb-2">{store.distance_km?.toFixed(1)} km away</p>
                  
                  {isDeal ? (
                    <div className="flex flex-col gap-2">
                      {relatedDeals.map(d => (
                        <div key={d.deal_id} className="text-xs bg-brand-50 p-2 rounded border border-brand-100">
                          <span className="font-semibold text-brand-700">{d.discount_percent.toFixed(0)}% OFF</span>
                          <span className="ml-2 text-slate-700">{d.product.name}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <span className="text-xs text-slate-400">Scanned</span>
                  )}
                </div>
              </Popup>
            </Marker>
          );
        })}

        <MapBounds stores={storeList} />
      </MapContainer>
    </div>
  );
}
