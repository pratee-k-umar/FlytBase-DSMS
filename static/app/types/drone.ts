export interface Drone {
  id: string;
  drone_id: string;
  name: string;
  model: string;
  manufacturer?: string;
  image_url?: string;
  status:
    | "available"
    | "in_mission"
    | "maintenance"
    | "offline"
    | "charging"
    | "in_flight"
    | "returning";
  battery_level: number;
  location: {
    latitude: number;
    longitude: number;
    altitude: number;
  };
  base_id: string; // Associated base
  assigned_site?: string; // Base name
  sensors?: string[]; // Optional sensor list
  max_flight_time: number;
  max_speed: number;
  max_altitude: number;
  current_mission_id?: string; // Currently active mission
  payload_capacity?: number;
  total_flight_hours?: number;
  health_status?: "good" | "warning" | "critical";
  camera_specs?: {
    resolution?: string;
    sensor?: string;
    zoom?: string;
  };
  created_at: string;
  updated_at: string;
}

export interface DroneListResponse {
  data: Drone[];
  count: number;
}
