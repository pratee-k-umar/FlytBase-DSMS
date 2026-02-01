export interface Waypoint {
    lat: number;
    lng: number;
    alt: number;
    action?: "fly" | "hover" | "photo" | "video";
    duration?: number;
}

export interface FlightPath {
    waypoints: Waypoint[];
    total_distance?: number;
    estimated_duration?: number;
    pattern_type: "waypoint" | "crosshatch" | "perimeter" | "spiral";
}

export interface Mission {
    id: string;
    mission_id: string;
    name: string;
    description?: string;
    site_name: string;
    survey_type: "mapping" | "inspection" | "surveillance" | "delivery";
    coverage_area?: any;
    flight_path?: FlightPath;
    altitude: number;
    speed: number;
    overlap: number;
    scheduled_start?: string;
    assigned_drone_id?: string;
    status:
        | "draft"
        | "scheduled"
        | "in_progress"
        | "paused"
        | "completed"
        | "aborted"
        | "failed";
    progress: number;
    current_waypoint_index: number;
    actual_start_time?: string;
    actual_end_time?: string;
    started_at?: string;
    completed_at?: string;
    images_captured: number;
    area_covered: number;
    priority: "low" | "medium" | "high" | "critical";
    created_at: string;
    updated_at: string;
}

export interface MissionListResponse {
    data: Mission[];
    count: number;
}

export interface CreateMissionRequest {
    name: string;
    description?: string;
    site_name: string;
    survey_type?: "mapping" | "inspection" | "surveillance" | "delivery";
    coverage_area?: any;
    altitude?: number;
    speed?: number;
    overlap?: number;
    scheduled_start?: string;
    assigned_drone_id?: string;
    waypoints?: Array<{
        order: number;
        location: {
            type: "Point";
            coordinates: [number, number];
        };
        altitude: number;
        action?: "fly_through" | "hover" | "capture" | "rotate";
        action_params?: any;
    }>;
}

export interface MissionStats {
    total: number;
    draft: number;
    scheduled: number;
    in_progress: number;
    paused: number;
    completed: number;
    aborted: number;
    failed: number;
    // Aggregate metrics
    total_area_covered?: number;
    total_images_captured?: number;
    total_flight_time?: number;
    avg_flight_time?: number;
}
