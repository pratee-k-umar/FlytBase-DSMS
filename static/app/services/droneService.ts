import type { Drone, DroneListResponse } from "@/types/drone";
import { apiClient } from "./api";

export interface CreateDroneData {
    name: string;
    model?: string;
    base_id?: string;
    max_flight_time?: number;
    max_speed?: number;
    max_altitude?: number;
    sensors?: string[];
}

export interface UpdateDroneData {
    name?: string;
    model?: string;
    base_id?: string;
    status?: string;
    battery_level?: number;
    max_flight_time?: number;
    max_speed?: number;
    max_altitude?: number;
    sensors?: string[];
}

export const droneService = {
    getAll: async (): Promise<DroneListResponse> => {
        const response = await apiClient.get("/fleet/drones/");
        return response.data;
    },

    getById: async (id: string): Promise<Drone> => {
        const response = await apiClient.get(`/fleet/drones/${id}/`);
        return response.data.data;
    },

    create: async (data: CreateDroneData): Promise<Drone> => {
        const response = await apiClient.post("/fleet/drones/", data);
        return response.data.data;
    },

    update: async (id: string, data: UpdateDroneData): Promise<Drone> => {
        const response = await apiClient.patch(`/fleet/drones/${id}/`, data);
        return response.data.data;
    },

    delete: async (id: string): Promise<void> => {
        await apiClient.delete(`/fleet/drones/${id}/`);
    },

    getStats: async () => {
        const response = await apiClient.get("/fleet/stats/");
        return response.data;
    },
};
