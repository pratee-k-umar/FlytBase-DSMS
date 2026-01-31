import type { Drone, DroneListResponse } from "@/types/drone";
import { apiClient } from "./api";

export const droneService = {
    getAll: async (): Promise<DroneListResponse> => {
        const response = await apiClient.get("/fleet/drones/");
        return response.data;
    },

    getById: async (id: string): Promise<Drone> => {
        const response = await apiClient.get(`/fleet/drones/${id}/`);
        return response.data;
    },

    getStats: async () => {
        const response = await apiClient.get("/fleet/stats/");
        return response.data;
    },
};
