import { missionService } from "@/services/missionService";
import { normalizeLongitude } from "@/utils/geo";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useEffect, useState } from "react";
import {
    MapContainer,
    Marker,
    Polygon,
    Polyline,
    Popup,
    TileLayer,
    useMap,
} from "react-leaflet";

// Fix Leaflet icons
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl:
        "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
    iconUrl:
        "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
    shadowUrl:
        "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

// Custom drone icon using uploaded image
const droneIcon = L.icon({
    iconUrl: require("../assets/images/drone-icon.png"),
    iconSize: [40, 40],
    iconAnchor: [20, 20],
    popupAnchor: [0, -20],
});

// Component to update map view to follow drone position
function MapViewController({
    center,
    zoom,
    dronePosition,
    shouldRecenter,
    onRecenterComplete,
}: {
    center: [number, number];
    zoom: number;
    dronePosition: [number, number] | null;
    shouldRecenter: boolean;
    onRecenterComplete: () => void;
}) {
    const map = useMap();
    const [hasInitialized, setHasInitialized] = useState(false);

    useEffect(() => {
        // Initial view setup
        if (!hasInitialized) {
            map.setView(center, zoom);
            setHasInitialized(true);
        }
    }, [center, zoom, hasInitialized, map]);

    useEffect(() => {
        // Only recenter when button is clicked
        if (shouldRecenter && dronePosition && hasInitialized) {
            map.setView(dronePosition, map.getZoom(), {
                animate: true,
                duration: 0.5,
            });
            onRecenterComplete();
        }
    }, [
        shouldRecenter,
        dronePosition,
        hasInitialized,
        map,
        onRecenterComplete,
    ]);

    return null;
}

export default function LiveMonitor() {
    const queryClient = useQueryClient();
    const [selectedMission, setSelectedMission] = useState<string | null>(null);
    const [autoRefresh, setAutoRefresh] = useState(true);
    const [shouldRecenter, setShouldRecenter] = useState(false);
    const [lastSelectedMission, setLastSelectedMission] = useState<
        string | null
    >(null);

    // Fetch active missions
    const { data: missionsData } = useQuery({
        queryKey: ["missions", "active"],
        queryFn: () => missionService.getAll({ status: "in_progress" }),
        refetchInterval: autoRefresh ? 5000 : false,
    });

    // Fetch selected mission details (for future WebSocket integration)
    useQuery({
        queryKey: ["mission", selectedMission],
        queryFn: () =>
            selectedMission ? missionService.getById(selectedMission) : null,
        enabled: !!selectedMission,
        refetchInterval: autoRefresh ? 3000 : false,
    });

    // Fetch latest telemetry for selected mission
    const { data: telemetryData } = useQuery({
        queryKey: ["telemetry", selectedMission],
        queryFn: () =>
            selectedMission
                ? missionService.getTelemetry(selectedMission, 1)
                : null,
        enabled: !!selectedMission,
        refetchInterval: autoRefresh ? 1000 : false, // Update every second for smooth movement
    });

    const pauseMutation = useMutation({
        mutationFn: (missionId: string) => missionService.pause(missionId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["missions"] });
            queryClient.invalidateQueries({
                queryKey: ["mission", selectedMission],
            });
        },
    });

    const resumeMutation = useMutation({
        mutationFn: (missionId: string) => missionService.resume(missionId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["missions"] });
            queryClient.invalidateQueries({
                queryKey: ["mission", selectedMission],
            });
        },
    });

    const abortMutation = useMutation({
        mutationFn: (missionId: string) => missionService.abort(missionId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["missions"] });
            setSelectedMission(null);
        },
    });

    const activeMissions = missionsData?.data || [];

    // Fetch full mission details for selected mission (includes coverage_area and flight_path)
    const { data: currentMission } = useQuery({
        queryKey: ["mission", selectedMission],
        queryFn: () =>
            selectedMission ? missionService.getById(selectedMission) : null,
        enabled: !!selectedMission,
        refetchInterval: autoRefresh ? 3000 : false,
    });

    // Auto-select first mission if none selected
    useEffect(() => {
        if (!selectedMission && activeMissions.length > 0) {
            setSelectedMission(activeMissions[0].mission_id);
        }
    }, [activeMissions, selectedMission]);

    // Auto-center map when a different mission is selected
    useEffect(() => {
        if (selectedMission && selectedMission !== lastSelectedMission) {
            // Trigger recenter when mission changes
            setShouldRecenter(true);
            setLastSelectedMission(selectedMission);
        }
    }, [selectedMission, lastSelectedMission]);

    // Get waypoint positions for map - normalize and extract survey-only waypoints
    const waypointPositions =
        currentMission?.flight_path?.waypoints?.map(
            (wp: any) =>
                [wp.lat, normalizeLongitude(wp.lng)] as [number, number],
        ) || [];

    // Extract coverage area polygon - handle GeoJSON format and normalize coordinates
    let coveragePolygon: [number, number][] = [];
    if (currentMission?.coverage_area) {
        const coords = currentMission.coverage_area.coordinates?.[0];
        if (coords && Array.isArray(coords)) {
            // GeoJSON format: [lng, lat] -> Leaflet format: [lat, lng]
            // Also normalize longitude to fix values like -282 -> 77
            coveragePolygon = coords.map(
                (coord: number[]) =>
                    [coord[1], normalizeLongitude(coord[0])] as [
                        number,
                        number,
                    ],
            );
        }
        console.log("Coverage polygon points:", coveragePolygon);
    }

    // Calculate map center - prioritize coverage polygon, then waypoints
    const mapCenter: [number, number] =
        coveragePolygon.length > 0
            ? coveragePolygon[0]
            : waypointPositions.length > 0
              ? waypointPositions[0]
              : [37.7749, -122.4194];

    const mapZoom =
        coveragePolygon.length > 0 || waypointPositions.length > 0 ? 15 : 13;

    // Get current drone position from latest telemetry
    let dronePosition: [number, number] | null = null;
    if (telemetryData?.data && telemetryData.data.length > 0) {
        const latestTelemetry = telemetryData.data[0];
        if (latestTelemetry.position) {
            dronePosition = [
                latestTelemetry.position.lat,
                latestTelemetry.position.lng,
            ];
            console.log("Drone position updated:", dronePosition);
        }
    }

    return (
        <div className="p-8">
            <div className="mb-8 flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-foreground">
                        Live Mission Monitor
                    </h1>
                    <p className="mt-2 text-muted-foreground">
                        Real-time drone tracking and telemetry
                    </p>
                </div>
                <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2 text-sm text-foreground">
                        <input
                            type="checkbox"
                            checked={autoRefresh}
                            onChange={(e) => setAutoRefresh(e.target.checked)}
                            className="rounded"
                        />
                        Auto-refresh
                    </label>
                    {dronePosition && (
                        <button
                            onClick={() => setShouldRecenter(true)}
                            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors text-sm font-medium"
                        >
                            Center on Drone
                        </button>
                    )}
                </div>
            </div>

            {activeMissions.length === 0 ? (
                <div className="bg-card rounded-lg border shadow-sm p-12 text-center">
                    <p className="text-muted-foreground">
                        No active missions. Start a mission from the Mission
                        Planner.
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                    {/* Mission List Sidebar */}
                    <div className="lg:col-span-1">
                        <div className="bg-card rounded-lg border shadow-sm p-4">
                            <h2 className="text-lg font-semibold text-card-foreground mb-4">
                                Active Missions ({activeMissions.length})
                            </h2>
                            <div className="space-y-2">
                                {activeMissions.map((mission) => (
                                    <div
                                        key={mission.mission_id}
                                        className={`w-full text-left p-3 rounded border transition-colors ${
                                            selectedMission ===
                                            mission.mission_id
                                                ? "bg-accent border-foreground"
                                                : "bg-background border-border hover:border-foreground"
                                        }`}
                                    >
                                        <button
                                            onClick={() =>
                                                setSelectedMission(
                                                    mission.mission_id,
                                                )
                                            }
                                            className="w-full text-left"
                                        >
                                            <div className="font-medium text-foreground text-sm">
                                                {mission.name}
                                            </div>
                                            <div className="text-xs text-muted-foreground mt-1">
                                                {mission.site_name}
                                            </div>
                                            <div className="mt-2 flex items-center justify-between">
                                                <span className="text-xs px-2 py-1 rounded bg-muted text-muted-foreground">
                                                    {mission.status}
                                                </span>
                                                <span className="text-xs text-muted-foreground">
                                                    {Math.round(
                                                        mission.progress,
                                                    )}
                                                    %
                                                </span>
                                            </div>
                                        </button>
                                        {/* Quick action buttons */}
                                        <div className="mt-2 flex gap-2">
                                            {mission.status ===
                                                "in_progress" && (
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        pauseMutation.mutate(
                                                            mission.mission_id,
                                                        );
                                                    }}
                                                    disabled={
                                                        pauseMutation.isPending
                                                    }
                                                    className="flex-1 px-2 py-1 text-xs rounded bg-muted text-foreground hover:bg-foreground hover:text-background transition-colors duration-150 disabled:opacity-50"
                                                >
                                                    Pause
                                                </button>
                                            )}
                                            {mission.status === "paused" && (
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        resumeMutation.mutate(
                                                            mission.mission_id,
                                                        );
                                                    }}
                                                    disabled={
                                                        resumeMutation.isPending
                                                    }
                                                    className="flex-1 px-2 py-1 text-xs rounded bg-foreground text-background hover:bg-primary hover:scale-105 transition-all duration-150 disabled:opacity-50"
                                                >
                                                    Resume
                                                </button>
                                            )}
                                            {(mission.status ===
                                                "in_progress" ||
                                                mission.status ===
                                                    "paused") && (
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        if (
                                                            confirm(
                                                                "Abort this mission?",
                                                            )
                                                        ) {
                                                            abortMutation.mutate(
                                                                mission.mission_id,
                                                            );
                                                        }
                                                    }}
                                                    disabled={
                                                        abortMutation.isPending
                                                    }
                                                    className="flex-1 px-2 py-1 text-xs rounded bg-red-100 text-red-600 hover:bg-red-500 hover:text-white transition-colors duration-150 disabled:opacity-50"
                                                >
                                                    Abort
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Map and Details */}
                    <div className="lg:col-span-3 space-y-6">
                        {/* Map */}
                        <div className="bg-card rounded-lg border shadow-sm overflow-hidden">
                            <div className="px-6 py-4 border-b">
                                <h2 className="text-lg font-semibold text-card-foreground">
                                    Live Map -{" "}
                                    {currentMission?.name || "Select a mission"}
                                </h2>
                            </div>
                            <div className="h-[500px]">
                                <MapContainer
                                    center={mapCenter}
                                    zoom={mapZoom}
                                    style={{ height: "100%", width: "100%" }}
                                >
                                    <MapViewController
                                        center={mapCenter}
                                        zoom={mapZoom}
                                        dronePosition={dronePosition}
                                        shouldRecenter={shouldRecenter}
                                        onRecenterComplete={() =>
                                            setShouldRecenter(false)
                                        }
                                    />
                                    <TileLayer
                                        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                                        attribution="&copy; OpenStreetMap"
                                    />

                                    {/* Coverage Area - Survey polygon */}
                                    {coveragePolygon.length > 0 && (
                                        <Polygon
                                            positions={coveragePolygon}
                                            pathOptions={{
                                                color: "#3b82f6",
                                                fillColor: "#3b82f6",
                                                fillOpacity: 0.05,
                                                weight: 3,
                                                opacity: 0.8,
                                            }}
                                        />
                                    )}

                                    {/* Flight path polyline */}
                                    {waypointPositions.length > 0 && (
                                        <Polyline
                                            positions={waypointPositions}
                                            color="#10b981"
                                            weight={2}
                                            opacity={0.6}
                                            dashArray="5, 10"
                                        />
                                    )}

                                    {/* Current drone position from telemetry */}
                                    {dronePosition && (
                                        <Marker
                                            key={`${dronePosition[0]}-${dronePosition[1]}`}
                                            position={dronePosition}
                                            icon={droneIcon}
                                        >
                                            <Popup>
                                                <div>
                                                    <strong>
                                                        Drone Position
                                                    </strong>
                                                    <br />
                                                    Lat:{" "}
                                                    {dronePosition[0].toFixed(
                                                        5,
                                                    )}
                                                    <br />
                                                    Lng:{" "}
                                                    {dronePosition[1].toFixed(
                                                        5,
                                                    )}
                                                    <br />
                                                    {telemetryData?.data?.[0]
                                                        ?.battery &&
                                                        `Battery: ${telemetryData.data[0].battery}%`}
                                                </div>
                                            </Popup>
                                        </Marker>
                                    )}
                                </MapContainer>
                            </div>
                        </div>

                        {/* Mission Details & Controls */}
                        {currentMission && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {/* Telemetry */}
                                <div className="bg-card rounded-lg border shadow-sm p-6">
                                    <h3 className="text-lg font-semibold text-card-foreground mb-4">
                                        Telemetry
                                    </h3>
                                    <div className="space-y-3">
                                        <div className="flex justify-between">
                                            <span className="text-sm text-muted-foreground">
                                                Progress
                                            </span>
                                            <span className="text-sm font-medium text-foreground">
                                                {Math.round(
                                                    currentMission.progress,
                                                )}
                                                %
                                            </span>
                                        </div>
                                        <div className="w-full bg-secondary rounded-full h-2">
                                            <div
                                                className="h-2 rounded-full bg-foreground"
                                                style={{
                                                    width: `${currentMission.progress}%`,
                                                }}
                                            />
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-sm text-muted-foreground">
                                                Waypoint
                                            </span>
                                            <span className="text-sm font-medium text-foreground">
                                                {currentMission.current_waypoint_index +
                                                    1}{" "}
                                                / {waypointPositions.length}
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-sm text-muted-foreground">
                                                Altitude
                                            </span>
                                            <span className="text-sm font-medium text-foreground">
                                                {currentMission.altitude}m
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-sm text-muted-foreground">
                                                Speed
                                            </span>
                                            <span className="text-sm font-medium text-foreground">
                                                {currentMission.speed} m/s
                                            </span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-sm text-muted-foreground">
                                                Status
                                            </span>
                                            <span className="text-sm font-medium px-2 py-1 rounded bg-muted text-muted-foreground">
                                                {currentMission.status}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                {/* Mission Controls */}
                                <div className="bg-card rounded-lg border shadow-sm p-6">
                                    <h3 className="text-lg font-semibold text-card-foreground mb-4">
                                        Mission Controls
                                    </h3>
                                    <div className="space-y-3">
                                        {currentMission.status ===
                                            "in_progress" && (
                                            <button
                                                onClick={() =>
                                                    pauseMutation.mutate(
                                                        currentMission.mission_id,
                                                    )
                                                }
                                                disabled={
                                                    pauseMutation.isPending
                                                }
                                                className="w-full py-2 px-4 bg-muted text-foreground rounded-md hover:opacity-90 disabled:opacity-50"
                                            >
                                                {pauseMutation.isPending
                                                    ? "Pausing..."
                                                    : "Pause Mission"}
                                            </button>
                                        )}

                                        {currentMission.status === "paused" && (
                                            <button
                                                onClick={() =>
                                                    resumeMutation.mutate(
                                                        currentMission.mission_id,
                                                    )
                                                }
                                                disabled={
                                                    resumeMutation.isPending
                                                }
                                                className="w-full py-2 px-4 bg-foreground text-background rounded-md hover:opacity-90 disabled:opacity-50"
                                            >
                                                {resumeMutation.isPending
                                                    ? "Resuming..."
                                                    : "Resume Mission"}
                                            </button>
                                        )}

                                        <button
                                            onClick={() => {
                                                if (
                                                    confirm(
                                                        "Are you sure you want to abort this mission?",
                                                    )
                                                ) {
                                                    abortMutation.mutate(
                                                        currentMission.mission_id,
                                                    );
                                                }
                                            }}
                                            disabled={abortMutation.isPending}
                                            className="w-full py-2 px-4 bg-muted text-foreground rounded-md hover:opacity-90 disabled:opacity-50 border"
                                        >
                                            {abortMutation.isPending
                                                ? "Aborting..."
                                                : "Abort Mission"}
                                        </button>

                                        <div className="mt-6 p-4 bg-muted rounded border">
                                            <h4 className="text-sm font-medium text-foreground mb-2">
                                                Mission Info
                                            </h4>
                                            <div className="space-y-1 text-xs text-muted-foreground">
                                                <div>
                                                    ID:{" "}
                                                    {currentMission.mission_id}
                                                </div>
                                                <div>
                                                    Site:{" "}
                                                    {currentMission.site_name}
                                                </div>
                                                <div>
                                                    Type:{" "}
                                                    {currentMission.survey_type}
                                                </div>
                                                <div>
                                                    Drone:{" "}
                                                    {currentMission.assigned_drone_id ||
                                                        "None"}
                                                </div>
                                                {currentMission.mission_phase && (
                                                    <div className="mt-2 pt-2 border-t">
                                                        <span
                                                            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                                                                currentMission.mission_phase ===
                                                                "traveling"
                                                                    ? "bg-blue-100 text-blue-800"
                                                                    : currentMission.mission_phase ===
                                                                        "surveying"
                                                                      ? "bg-green-100 text-green-800"
                                                                      : "bg-yellow-100 text-yellow-800"
                                                            }`}
                                                        >
                                                            Phase:{" "}
                                                            {currentMission.mission_phase
                                                                .charAt(0)
                                                                .toUpperCase() +
                                                                currentMission.mission_phase.slice(
                                                                    1,
                                                                )}
                                                        </span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
