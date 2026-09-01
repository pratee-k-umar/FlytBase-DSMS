import { useEffect } from "react";
import { useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "maplibre-gl/dist/maplibre-gl.css";
// import L, { maplibreGL } from "leaflet";
import "@maplibre/maplibre-gl-leaflet";
import { MaplibreGL } from "@maplibre/maplibre-gl-leaflet";

export default function MapLayer() {
    const map = useMap();

    useEffect(() => {
        if(!map) return;
        
        const gLayer = new MaplibreGL({
            style: 'https://tiles.openfreemap.org/styles/bright',
            // customAttribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        });

        gLayer.addTo(map);

        return () => {
            gLayer.remove();
        };
    }, [map]);

    return null;
}