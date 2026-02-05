import { BaseStats, DroneBase } from "../types/base";
import { apiClient } from "./api";

export interface CreateBaseData {
    name: string;
    location: {
        lat: number;
        lng: number;
    };
    address?: string;
    region?: string;
    max_drones?: number;
    status?: string;
}

const baseService = {
    getAll: async (filters?: {
        status?: string;
        region?: string;
    }): Promise<{ data: DroneBase[]; count: number }> => {
        const params = new URLSearchParams();
        if (filters?.status) params.append("status", filters.status);
        if (filters?.region) params.append("region", filters.region);

        const queryString = params.toString();
        const response = await apiClient.get(
            `/bases/${queryString ? `?${queryString}` : ""}`,
        );
        return response.data;
    },

    getById: async (baseId: string): Promise<DroneBase> => {
        const response = await apiClient.get(`/bases/${baseId}/`);
        return response.data;
    },

    create: async (data: CreateBaseData): Promise<DroneBase> => {
        const response = await apiClient.post("/bases/", data);
        return response.data;
    },

    update: async (
        baseId: string,
        data: Partial<CreateBaseData>,
    ): Promise<DroneBase> => {
        const response = await apiClient.put(`/bases/${baseId}/`, data);
        return response.data;
    },

    delete: async (baseId: string): Promise<void> => {
        await apiClient.delete(`/bases/${baseId}/`);
    },

    getDrones: async (baseId: string) => {
        const response = await apiClient.get(`/bases/${baseId}/drones/`);
        return response.data;
    },

    addDrone: async (baseId: string, droneId: string) => {
        const response = await apiClient.post(`/bases/${baseId}/drones/`, {
            drone_id: droneId,
        });
        return response.data;
    },

    getStats: async (): Promise<BaseStats> => {
        const response = await apiClient.get("/bases/stats/");
        return response.data;
    },

    findNearest: async (lat: number, lng: number): Promise<DroneBase> => {
        const response = await apiClient.get(
            `/bases/nearest/?lat=${lat}&lng=${lng}`,
        );
        return response.data;
    },
};

export default baseService;
