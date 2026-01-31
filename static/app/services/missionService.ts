import type {
    CreateMissionRequest,
    Mission,
    MissionListResponse,
    MissionStats,
} from "@/types/mission";
import { apiClient } from "./api";

export const missionService = {
    getAll: async (filters?: {
        status?: string;
        drone_id?: string;
        site?: string;
    }): Promise<MissionListResponse> => {
        const params = new URLSearchParams();
        if (filters?.status) params.append("status", filters.status);
        if (filters?.drone_id) params.append("drone_id", filters.drone_id);
        if (filters?.site) params.append("site", filters.site);

        const queryString = params.toString();
        const response = await apiClient.get(
            `/missions/${queryString ? `?${queryString}` : ""}`,
        );
        return response.data;
    },

    getById: async (id: string): Promise<Mission> => {
        const response = await apiClient.get(`/missions/${id}/`);
        return response.data.data;
    },

    create: async (data: CreateMissionRequest): Promise<Mission> => {
        const response = await apiClient.post("/missions/", data);
        return response.data.data;
    },

    update: async (
        id: string,
        data: Partial<CreateMissionRequest>,
    ): Promise<Mission> => {
        const response = await apiClient.patch(`/missions/${id}/`, data);
        return response.data.data;
    },

    delete: async (id: string): Promise<void> => {
        await apiClient.delete(`/missions/${id}/`);
    },

    start: async (id: string): Promise<Mission> => {
        const response = await apiClient.post(`/missions/${id}/start/`);
        return response.data.mission;
    },

    pause: async (id: string): Promise<Mission> => {
        const response = await apiClient.post(`/missions/${id}/pause/`);
        return response.data.mission;
    },

    resume: async (id: string): Promise<Mission> => {
        const response = await apiClient.post(`/missions/${id}/resume/`);
        return response.data.mission;
    },

    abort: async (id: string): Promise<Mission> => {
        const response = await apiClient.post(`/missions/${id}/abort/`);
        return response.data.mission;
    },

    getStats: async (): Promise<MissionStats> => {
        const response = await apiClient.get("/missions/stats/");
        return response.data;
    },

    getTelemetry: async (missionId: string, limit: number = 1) => {
        const response = await apiClient.get(
            `/missions/${missionId}/telemetry/?limit=${limit}`,
        );
        return response.data;
    },

    getAllTelemetry: async (missionId: string) => {
        const response = await apiClient.get(
            `/missions/${missionId}/telemetry/?limit=10000`,
        );
        return response.data;
    },
};
