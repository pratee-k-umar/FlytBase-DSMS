import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DroneBase } from "@/types/base";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Map as MapIcon } from "lucide-react";
import { useEffect, useRef } from "react";

// Fix Leaflet default icon issue with webpack
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl:
        "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
    iconUrl:
        "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
    shadowUrl:
        "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

interface BaseMapProps {
    bases: DroneBase[];
    selectedBaseId?: string;
    onBaseSelect: (baseId: string) => void;
}

export const BaseMap = ({
    bases,
    selectedBaseId,
    onBaseSelect,
}: BaseMapProps) => {
    const mapRef = useRef<L.Map | null>(null);
    const markersRef = useRef<Map<string, L.Marker>>(new Map());

    useEffect(() => {
        if (!mapRef.current) {
            // Initialize map with options to handle world wrap better
            const map = L.map("base-map", {
                worldCopyJump: true, // Jump to the main world copy when panning
            }).setView([12.9716, 77.5946], 6); // Default to India

            L.tileLayer(
                "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
                {
                    attribution: "© OpenStreetMap contributors",
                    maxZoom: 19,
                },
            ).addTo(map);

            mapRef.current = map;
        }

        return () => {
            if (mapRef.current) {
                mapRef.current.remove();
                mapRef.current = null;
            }
        };
    }, []);

    useEffect(() => {
        if (!mapRef.current || !bases.length) return;

        // Clear existing markers
        markersRef.current.forEach((marker) => marker.remove());
        markersRef.current.clear();

        // Add markers for each base
        bases.forEach((base) => {
            const isSelected = base.base_id === selectedBaseId;

            // Custom icon based on selection
            const iconHtml = `
                <div style="
                    background-color: ${isSelected ? "#3b82f6" : "#10b981"};
                    color: white;
                    border-radius: 50%;
                    width: 32px;
                    height: 32px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    font-size: 12px;
                    border: 3px solid white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                    ${isSelected ? "transform: scale(1.2);" : ""}
                ">
                    ${base.drone_count || 0}
                </div>
            `;

            const customIcon = L.divIcon({
                html: iconHtml,
                className: "",
                iconSize: [32, 32],
                iconAnchor: [16, 16],
            });

            const marker = L.marker([base.lat, base.lng], { icon: customIcon })
                .addTo(mapRef.current!)
                .bindPopup(
                    `
                    <div style="text-align: center;">
                        <strong>${base.name}</strong><br/>
                        <span style="color: #666;">Drones: ${base.drone_count || 0}</span><br/>
                        <span style="color: #666; font-size: 12px;">
                            ${base.lat.toFixed(4)}°N, ${base.lng.toFixed(4)}°E
                        </span>
                    </div>
                `,
                )
                .on("click", () => onBaseSelect(base.base_id));

            markersRef.current.set(base.base_id, marker);
        });

        // Fit map to show all bases
        if (bases.length > 0) {
            const bounds = L.latLngBounds(bases.map((b) => [b.lat, b.lng]));
            mapRef.current.fitBounds(bounds, { padding: [50, 50] });
        }
    }, [bases, selectedBaseId, onBaseSelect]);

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center gap-2">
                    <MapIcon className="h-5 w-5" />
                    <CardTitle>Base Locations</CardTitle>
                </div>
            </CardHeader>
            <CardContent>
                <div
                    id="base-map"
                    style={{
                        height: "400px",
                        width: "100%",
                        borderRadius: "8px",
                    }}
                ></div>
                <div className="text-sm text-muted-foreground mt-2">
                    Click a base marker to view its drones
                </div>
            </CardContent>
        </Card>
    );
};
