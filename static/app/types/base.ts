export interface DroneBase {
    id: string;
    base_id: string;
    name: string;
    location: {
        type: "Point";
        coordinates: [number, number]; // [lng, lat]
    };
    lat: number; // Helper property from backend
    lng: number; // Helper property from backend
    address?: string;
    region?: string;
    status: "active" | "maintenance" | "offline";
    max_drones: number;
    drone_count: number; // Current number of drones at this base
    created_at: string;
    updated_at: string;
}

export interface BaseStats {
    total_drones: number;
    available_drones: number;
    in_flight_drones: number;
    charging_drones: number;
    dispatching_drones: number;
    returning_drones: number;
    // Also used by baseService
    total_bases?: number;
    active_bases?: number;
    total_capacity?: number;
    total_drones_assigned?: number;
    utilization?: number;
}

export interface BaseCreateData {
    name: string;
    location: {
        type: "Point";
        coordinates: [number, number];
    };
    max_drones?: number;
    status?: "active" | "maintenance" | "offline";
}

export interface BaseUpdateData {
    name?: string;
    location?: {
        type: "Point";
        coordinates: [number, number];
    };
    max_drones?: number;
    status?: "active" | "maintenance" | "offline";
}
