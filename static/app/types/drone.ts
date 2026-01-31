export interface Drone {
    id: string;
    name: string;
    model: string;
    status: "available" | "in_mission" | "maintenance" | "offline";
    battery_level: number;
    location: {
        latitude: number;
        longitude: number;
        altitude: number;
    };
    max_flight_time: number;
    max_speed: number;
    max_altitude: number;
    created_at: string;
    updated_at: string;
}

export interface DroneListResponse {
    data: Drone[];
    count: number;
}
