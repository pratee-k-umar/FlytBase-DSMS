import { droneService } from "@/services/droneService";
import { missionService } from "@/services/missionService";
import { useQuery } from "@tanstack/react-query";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useState } from "react";
import {
    MapContainer,
    Marker,
    Polygon,
    Polyline,
    Popup,
    TileLayer,
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

export default function Analytics() {
    const [selectedMissionId, setSelectedMissionId] = useState<string | null>(
        null,
    );
    const { data: missionsData } = useQuery({
        queryKey: ["missions", "recent"],
        queryFn: () => missionService.getAll({ limit: 10 }),
    });

    const { data: missionStats } = useQuery({
        queryKey: ["missionStats"],
        queryFn: missionService.getStats,
    });

    const { data: fleetStats } = useQuery({
        queryKey: ["fleetStats"],
        queryFn: droneService.getStats,
    });

    const missions = missionsData?.data || [];
    const completedMissions = missions.filter((m) => m.status === "completed");

    // Fetch selected mission details
    const { data: selectedMissionData } = useQuery({
        queryKey: ["mission", selectedMissionId],
        queryFn: () =>
            selectedMissionId
                ? missionService.getById(selectedMissionId)
                : null,
        enabled: !!selectedMissionId,
    });

    // Fetch telemetry for selected mission
    const { data: telemetryData } = useQuery({
        queryKey: ["telemetry", selectedMissionId, "all"],
        queryFn: () =>
            selectedMissionId
                ? missionService.getAllTelemetry(selectedMissionId)
                : null,
        enabled: !!selectedMissionId,
    });

    const selectedMission = selectedMissionData;
    const telemetryPoints = telemetryData?.data || [];

    // Calculate statistics
    const totalFlightTime = completedMissions.reduce((acc: number, m) => {
        if (m.started_at && m.completed_at) {
            const start = new Date(m.started_at).getTime();
            const end = new Date(m.completed_at).getTime();
            return acc + (end - start) / (1000 * 60); // minutes
        }
        return acc;
    }, 0);

    const avgFlightTime =
        completedMissions.length > 0
            ? totalFlightTime / completedMissions.length
            : 0;

    const totalAreaCovered = completedMissions.reduce(
        (acc: number, m) => acc + (m.area_covered || 0),
        0,
    );

    const totalImages = completedMissions.reduce(
        (acc: number, m) => acc + (m.images_captured || 0),
        0,
    );

    const overviewStats = [
        { label: "Total Missions", value: missionStats?.total || 0 },
        { label: "Completed", value: missionStats?.completed || 0 },
        { label: "In Progress", value: missionStats?.in_progress || 0 },
        {
            label: "Failed/Aborted",
            value: (missionStats?.failed || 0) + (missionStats?.aborted || 0),
        },
    ];

    const fleetOverview = [
        { label: "Total Drones", value: fleetStats?.data?.total || 0 },
        { label: "Available", value: fleetStats?.data?.available || 0 },
        { label: "In Mission", value: fleetStats?.data?.in_mission || 0 },
        { label: "Maintenance", value: fleetStats?.data?.maintenance || 0 },
    ];

    const performanceStats = [
        {
            label: "Total Flight Time",
            value: `${Math.round(totalFlightTime)} min`,
            subtext: `${Math.round(totalFlightTime / 60)} hours`,
        },
        {
            label: "Avg Flight Time",
            value: `${Math.round(avgFlightTime)} min`,
            subtext: "Per mission",
        },
        {
            label: "Total Area Covered",
            value:
                totalAreaCovered > 0
                    ? `${Math.round(totalAreaCovered).toLocaleString()} m²`
                    : "0 m²",
            subtext:
                totalAreaCovered > 0
                    ? `${(totalAreaCovered / 10000).toFixed(2)} hectares`
                    : "0 hectares",
        },
        {
            label: "Images Captured",
            value: totalImages.toLocaleString(),
            subtext: "Across all missions",
        },
    ];

    return (
        <div className="p-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-foreground">
                    Analytics & Reports
                </h1>
                <p className="mt-2 text-muted-foreground">
                    Survey statistics and performance metrics
                </p>
            </div>

            <div className="space-y-6">
                {/* Mission Overview */}
                <div className="bg-card rounded-lg border shadow-sm p-6">
                    <h2 className="text-xl font-semibold text-card-foreground mb-4">
                        Mission Overview
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {overviewStats.map((stat) => (
                            <div
                                key={stat.label}
                                className="bg-background rounded-lg border p-4"
                            >
                                <p className="text-sm text-muted-foreground">
                                    {stat.label}
                                </p>
                                <p className="text-3xl font-bold mt-2 text-foreground">
                                    {stat.value}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Fleet Overview */}
                <div className="bg-card rounded-lg border shadow-sm p-6">
                    <h2 className="text-xl font-semibold text-card-foreground mb-4">
                        Fleet Status
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {fleetOverview.map((stat) => (
                            <div
                                key={stat.label}
                                className="bg-background rounded-lg border p-4"
                            >
                                <p className="text-sm text-muted-foreground">
                                    {stat.label}
                                </p>
                                <p className="text-3xl font-bold mt-2 text-foreground">
                                    {stat.value}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Performance Metrics */}
                <div className="bg-card rounded-lg border shadow-sm p-6">
                    <h2 className="text-xl font-semibold text-card-foreground mb-4">
                        Performance Metrics
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        {performanceStats.map((stat) => (
                            <div
                                key={stat.label}
                                className="bg-background rounded-lg border p-4"
                            >
                                <p className="text-sm text-muted-foreground">
                                    {stat.label}
                                </p>
                                <p className="text-2xl font-bold mt-2 text-foreground">
                                    {stat.value}
                                </p>
                                {stat.subtext && (
                                    <p className="text-xs text-muted-foreground mt-1">
                                        {stat.subtext}
                                    </p>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Recent Missions */}
                <div className="bg-card rounded-lg border shadow-sm">
                    <div className="px-6 py-4 border-b">
                        <h2 className="text-xl font-semibold text-card-foreground">
                            Recent Missions
                        </h2>
                    </div>
                    <div className="p-6">
                        {missions.length === 0 ? (
                            <p className="text-center text-muted-foreground py-8">
                                No missions yet. Create your first mission in
                                the Mission Planner.
                            </p>
                        ) : (
                            <div className="overflow-x-auto">
                                <table className="w-full">
                                    <thead>
                                        <tr className="border-b">
                                            <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                                                Mission
                                            </th>
                                            <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                                                Site
                                            </th>
                                            <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                                                Type
                                            </th>
                                            <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                                                Status
                                            </th>
                                            <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                                                Progress
                                            </th>
                                            <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                                                Created
                                            </th>
                                            <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                                                Actions
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {missions
                                            .slice(0, 10)
                                            .map((mission: any) => (
                                                <tr
                                                    key={mission.mission_id}
                                                    className="border-b"
                                                >
                                                    <td className="py-3 px-4 text-sm font-medium text-foreground">
                                                        {mission.name}
                                                    </td>
                                                    <td className="py-3 px-4 text-sm text-muted-foreground">
                                                        {mission.site_name}
                                                    </td>
                                                    <td className="py-3 px-4 text-sm text-muted-foreground">
                                                        {mission.survey_type}
                                                    </td>
                                                    <td className="py-3 px-4">
                                                        <span className="text-xs px-2 py-1 rounded bg-muted text-muted-foreground">
                                                            {mission.status}
                                                        </span>
                                                    </td>
                                                    <td className="py-3 px-4 text-sm text-muted-foreground">
                                                        {Math.round(
                                                            mission.progress,
                                                        )}
                                                        %
                                                    </td>
                                                    <td className="py-3 px-4 text-sm text-muted-foreground">
                                                        {new Date(
                                                            mission.created_at,
                                                        ).toLocaleDateString()}
                                                    </td>
                                                    <td className="py-3 px-4">
                                                        <button
                                                            onClick={() =>
                                                                setSelectedMissionId(
                                                                    mission.mission_id,
                                                                )
                                                            }
                                                            className="text-xs px-3 py-1 bg-primary text-primary-foreground rounded hover:bg-primary/90"
                                                        >
                                                            View Details
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Mission Details Modal */}
            {selectedMissionId && selectedMission && (
                <div
                    className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
                    onClick={() => setSelectedMissionId(null)}
                >
                    <div
                        className="bg-card rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="sticky top-0 bg-card border-b px-6 py-4 flex items-center justify-between">
                            <h2 className="text-2xl font-bold text-card-foreground">
                                {selectedMission.name}
                            </h2>
                            <button
                                onClick={() => setSelectedMissionId(null)}
                                className="text-muted-foreground hover:text-foreground text-2xl font-bold"
                            >
                                ×
                            </button>
                        </div>

                        <div className="p-6 space-y-6">
                            {/* Mission Details Grid */}
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                <div className="bg-background rounded-lg border p-4">
                                    <p className="text-sm text-muted-foreground">
                                        Mission ID
                                    </p>
                                    <p className="text-lg font-semibold text-foreground mt-1">
                                        {selectedMission.mission_id}
                                    </p>
                                </div>
                                <div className="bg-background rounded-lg border p-4">
                                    <p className="text-sm text-muted-foreground">
                                        Status
                                    </p>
                                    <p className="text-lg font-semibold text-foreground mt-1">
                                        <span className="text-xs px-2 py-1 rounded bg-muted text-muted-foreground">
                                            {selectedMission.status}
                                        </span>
                                    </p>
                                </div>
                                <div className="bg-background rounded-lg border p-4">
                                    <p className="text-sm text-muted-foreground">
                                        Progress
                                    </p>
                                    <p className="text-lg font-semibold text-foreground mt-1">
                                        {Math.round(selectedMission.progress)}%
                                    </p>
                                </div>
                                <div className="bg-background rounded-lg border p-4">
                                    <p className="text-sm text-muted-foreground">
                                        Site Name
                                    </p>
                                    <p className="text-lg font-semibold text-foreground mt-1">
                                        {selectedMission.site_name}
                                    </p>
                                </div>
                                <div className="bg-background rounded-lg border p-4">
                                    <p className="text-sm text-muted-foreground">
                                        Survey Type
                                    </p>
                                    <p className="text-lg font-semibold text-foreground mt-1">
                                        {selectedMission.survey_type}
                                    </p>
                                </div>
                                <div className="bg-background rounded-lg border p-4">
                                    <p className="text-sm text-muted-foreground">
                                        Altitude
                                    </p>
                                    <p className="text-lg font-semibold text-foreground mt-1">
                                        {selectedMission.altitude}m
                                    </p>
                                </div>
                                <div className="bg-background rounded-lg border p-4">
                                    <p className="text-sm text-muted-foreground">
                                        Speed
                                    </p>
                                    <p className="text-lg font-semibold text-foreground mt-1">
                                        {selectedMission.speed}m/s
                                    </p>
                                </div>
                                <div className="bg-background rounded-lg border p-4">
                                    <p className="text-sm text-muted-foreground">
                                        Area Covered
                                    </p>
                                    <p className="text-lg font-semibold text-foreground mt-1">
                                        {Math.round(
                                            selectedMission.area_covered || 0,
                                        ).toLocaleString()}{" "}
                                        m<sup>2</sup>
                                    </p>
                                    <p className="text-xs text-muted-foreground mt-1">
                                        {(
                                            (selectedMission.area_covered ||
                                                0) / 10000
                                        ).toFixed(2)}{" "}
                                        hectares
                                    </p>
                                </div>
                                <div className="bg-background rounded-lg border p-4">
                                    <p className="text-sm text-muted-foreground">
                                        Created
                                    </p>
                                    <p className="text-lg font-semibold text-foreground mt-1">
                                        {new Date(
                                            selectedMission.created_at,
                                        ).toLocaleString()}
                                    </p>
                                </div>
                                {selectedMission.started_at && (
                                    <div className="bg-background rounded-lg border p-4">
                                        <p className="text-sm text-muted-foreground">
                                            Started
                                        </p>
                                        <p className="text-lg font-semibold text-foreground mt-1">
                                            {new Date(
                                                selectedMission.started_at,
                                            ).toLocaleString()}
                                        </p>
                                    </div>
                                )}
                                {selectedMission.completed_at && (
                                    <div className="bg-background rounded-lg border p-4">
                                        <p className="text-sm text-muted-foreground">
                                            Completed
                                        </p>
                                        <p className="text-lg font-semibold text-foreground mt-1">
                                            {new Date(
                                                selectedMission.completed_at,
                                            ).toLocaleString()}
                                        </p>
                                    </div>
                                )}
                                {selectedMission.assigned_drone_id && (
                                    <div className="bg-background rounded-lg border p-4">
                                        <p className="text-sm text-muted-foreground">
                                            Drone
                                        </p>
                                        <p className="text-lg font-semibold text-foreground mt-1">
                                            {selectedMission.assigned_drone_id}
                                        </p>
                                    </div>
                                )}
                            </div>

                            {/* Flight Path Map */}
                            <div className="bg-background rounded-lg border overflow-hidden">
                                <div className="px-4 py-3 border-b">
                                    <h3 className="text-lg font-semibold text-foreground">
                                        Flight Path
                                    </h3>
                                    <p className="text-sm text-muted-foreground mt-1">
                                        {telemetryPoints.length > 0
                                            ? `Showing ${telemetryPoints.length} telemetry points`
                                            : "No telemetry data available"}
                                    </p>
                                </div>
                                <div className="h-[500px]">
                                    {(() => {
                                        // Get coverage area polygon
                                        let coveragePolygon: [
                                            number,
                                            number,
                                        ][] = [];
                                        if (
                                            selectedMission.coverage_area
                                                ?.coordinates?.[0]
                                        ) {
                                            coveragePolygon =
                                                selectedMission.coverage_area.coordinates[0].map(
                                                    (coord: number[]) =>
                                                        [
                                                            coord[1],
                                                            coord[0],
                                                        ] as [number, number],
                                                );
                                        }

                                        // Get actual flight path from telemetry
                                        const flightPath: [number, number][] =
                                            telemetryPoints.map(
                                                (point: any) =>
                                                    [
                                                        point.position.lat,
                                                        point.position.lng,
                                                    ] as [number, number],
                                            );

                                        // Get planned waypoints
                                        const plannedWaypoints: [
                                            number,
                                            number,
                                        ][] =
                                            selectedMission.flight_path?.waypoints?.map(
                                                (wp: any) =>
                                                    [wp.lat, wp.lng] as [
                                                        number,
                                                        number,
                                                    ],
                                            ) || [];

                                        const mapCenter: [number, number] =
                                            flightPath.length > 0
                                                ? flightPath[0]
                                                : coveragePolygon.length > 0
                                                  ? coveragePolygon[0]
                                                  : plannedWaypoints.length > 0
                                                    ? plannedWaypoints[0]
                                                    : [37.7749, -122.4194];

                                        return (
                                            <MapContainer
                                                center={mapCenter}
                                                zoom={15}
                                                style={{
                                                    height: "100%",
                                                    width: "100%",
                                                }}
                                            >
                                                <TileLayer
                                                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                                                    attribution="&copy; OpenStreetMap"
                                                />

                                                {/* Coverage Area Polygon */}
                                                {coveragePolygon.length > 0 && (
                                                    <Polygon
                                                        positions={
                                                            coveragePolygon
                                                        }
                                                        pathOptions={{
                                                            color: "#3b82f6",
                                                            fillColor:
                                                                "#3b82f6",
                                                            fillOpacity: 0.1,
                                                            weight: 2,
                                                            opacity: 0.6,
                                                        }}
                                                    />
                                                )}

                                                {/* Planned Flight Path */}
                                                {plannedWaypoints.length >
                                                    0 && (
                                                    <Polyline
                                                        positions={
                                                            plannedWaypoints
                                                        }
                                                        pathOptions={{
                                                            color: "#10b981",
                                                            weight: 2,
                                                            opacity: 0.4,
                                                            dashArray: "5, 10",
                                                        }}
                                                    />
                                                )}

                                                {/* Actual Flight Path (from telemetry) */}
                                                {flightPath.length > 0 && (
                                                    <Polyline
                                                        positions={flightPath}
                                                        pathOptions={{
                                                            color: "#ef4444",
                                                            weight: 3,
                                                            opacity: 0.8,
                                                        }}
                                                    />
                                                )}

                                                {/* Start/End Markers */}
                                                {flightPath.length > 0 && (
                                                    <>
                                                        <Marker
                                                            position={
                                                                flightPath[0]
                                                            }
                                                        >
                                                            <Popup>
                                                                <strong>
                                                                    Start
                                                                </strong>
                                                                <br />
                                                                {flightPath[0][0].toFixed(
                                                                    5,
                                                                )}
                                                                ,{" "}
                                                                {flightPath[0][1].toFixed(
                                                                    5,
                                                                )}
                                                            </Popup>
                                                        </Marker>
                                                        {flightPath.length >
                                                            1 && (
                                                            <Marker
                                                                position={
                                                                    flightPath[
                                                                        flightPath.length -
                                                                            1
                                                                    ]
                                                                }
                                                            >
                                                                <Popup>
                                                                    <strong>
                                                                        End
                                                                    </strong>
                                                                    <br />
                                                                    {flightPath[
                                                                        flightPath.length -
                                                                            1
                                                                    ][0].toFixed(
                                                                        5,
                                                                    )}
                                                                    ,{" "}
                                                                    {flightPath[
                                                                        flightPath.length -
                                                                            1
                                                                    ][1].toFixed(
                                                                        5,
                                                                    )}
                                                                </Popup>
                                                            </Marker>
                                                        )}
                                                    </>
                                                )}
                                            </MapContainer>
                                        );
                                    })()}
                                </div>
                            </div>

                            {/* Flight Path Legend */}
                            <div className="bg-background rounded-lg border p-4">
                                <h4 className="text-sm font-semibold text-foreground mb-3">
                                    Map Legend
                                </h4>
                                <div className="space-y-2">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-0.5 bg-blue-500 opacity-60"></div>
                                        <span className="text-sm text-muted-foreground">
                                            Coverage Area (planned)
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <div
                                            className="w-8 h-0.5 bg-green-500 opacity-40"
                                            style={{ borderTop: "2px dashed" }}
                                        ></div>
                                        <span className="text-sm text-muted-foreground">
                                            Planned Flight Path
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-1 bg-red-500"></div>
                                        <span className="text-sm text-muted-foreground">
                                            Actual Flight Path (telemetry)
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
