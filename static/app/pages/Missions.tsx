import { missionService } from "@/services/missionService";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

export default function Missions() {
    const queryClient = useQueryClient();
    const [selectedStatus, setSelectedStatus] = useState<string>("all");
    const [loadingMissionId, setLoadingMissionId] = useState<string | null>(
        null,
    );

    const { data: missionsData, isLoading } = useQuery({
        queryKey: ["missions", selectedStatus],
        queryFn: () => {
            if (selectedStatus === "all") {
                return missionService.getAll();
            }
            return missionService.getAll({ status: selectedStatus });
        },
        refetchInterval: 2000,
    });

    const startMissionMutation = useMutation({
        mutationFn: (missionId: string) => missionService.start(missionId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["missions"] });
            setLoadingMissionId(null);
        },
        onError: () => {
            setLoadingMissionId(null);
        },
    });

    const pauseMissionMutation = useMutation({
        mutationFn: (missionId: string) => missionService.pause(missionId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["missions"] });
            setLoadingMissionId(null);
        },
        onError: () => {
            setLoadingMissionId(null);
        },
    });

    const resumeMissionMutation = useMutation({
        mutationFn: (missionId: string) => missionService.resume(missionId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["missions"] });
            setLoadingMissionId(null);
        },
        onError: () => {
            setLoadingMissionId(null);
        },
    });

    const abortMissionMutation = useMutation({
        mutationFn: (missionId: string) => missionService.abort(missionId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["missions"] });
            setLoadingMissionId(null);
        },
        onError: () => {
            setLoadingMissionId(null);
        },
    });

    const missions = missionsData?.data || [];

    const statuses = [
        { value: "all", label: "All" },
        { value: "draft", label: "Draft" },
        { value: "scheduled", label: "Scheduled" },
        { value: "in_progress", label: "In Progress" },
        { value: "paused", label: "Paused" },
        { value: "completed", label: "Completed" },
        { value: "aborted", label: "Aborted" },
        { value: "failed", label: "Failed" },
    ];

    const getStatusDisplay = (status: string) => {
        const statusMap: Record<string, string> = {
            draft: "Draft",
            scheduled: "Scheduled",
            in_progress: "In Progress",
            paused: "Paused",
            completed: "Completed",
            aborted: "Aborted",
            failed: "Failed",
        };
        return statusMap[status] || status;
    };

    return (
        <div className="p-8">
            {/* Header */}
            <div className="mb-8 flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-foreground">Missions</h1>
                    <p className="mt-2 text-muted-foreground">
                        View and manage all missions
                    </p>
                </div>
                <button
                    onClick={() => queryClient.invalidateQueries({ queryKey: ["missions"] })}
                    className="px-4 py-2 bg-muted text-foreground rounded-md hover:bg-muted/70 transition-colors text-sm font-medium flex items-center gap-2"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                        <path d="M3 3v5h5" />
                        <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
                        <path d="M16 21h5v-5" />
                    </svg>
                    Refresh
                </button>
            </div>

            {/* Status Filter */}
            <div className="mb-6 flex gap-2 flex-wrap">
                {statuses.map((status) => (
                    <button
                        key={status.value}
                        onClick={() => setSelectedStatus(status.value)}
                        className={`px-4 py-2 rounded-md border transition-all ${
                            selectedStatus === status.value
                                ? "bg-foreground text-background border-foreground"
                                : "bg-card text-foreground border-muted hover:border-foreground"
                        }`}
                    >
                        {status.label}
                    </button>
                ))}
            </div>

            {/* Missions Table */}
            <div className="bg-card rounded-lg border shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b">
                    <h2 className="text-lg font-semibold text-card-foreground">
                        {missions.length} Mission
                        {missions.length !== 1 ? "s" : ""}
                    </h2>
                </div>

                {isLoading ? (
                    <div className="p-6 text-center text-muted-foreground">
                        Loading missions...
                    </div>
                ) : missions.length === 0 ? (
                    <div className="p-6 text-center text-muted-foreground">
                        No missions found
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="border-b bg-muted/50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-sm font-medium text-foreground">
                                        Name
                                    </th>
                                    <th className="px-6 py-3 text-left text-sm font-medium text-foreground">
                                        Site
                                    </th>
                                    <th className="px-6 py-3 text-left text-sm font-medium text-foreground">
                                        Status
                                    </th>
                                    <th className="px-6 py-3 text-left text-sm font-medium text-foreground">
                                        Progress
                                    </th>
                                    <th className="px-6 py-3 text-left text-sm font-medium text-foreground">
                                        Altitude
                                    </th>
                                    <th className="px-6 py-3 text-left text-sm font-medium text-foreground">
                                        Speed
                                    </th>
                                    <th className="px-6 py-3 text-right text-sm font-medium text-foreground">
                                        Actions
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="divide-y">
                                {missions.map((mission: any) => (
                                    <tr
                                        key={mission.mission_id}
                                        className="hover:bg-muted/50 transition-colors"
                                    >
                                        <td className="px-6 py-4 text-sm text-foreground font-medium">
                                            {mission.name}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-foreground">
                                            {mission.site_name}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-foreground">
                                            <span className="inline-block px-3 py-1 rounded-full bg-muted text-muted-foreground text-xs font-medium">
                                                {getStatusDisplay(
                                                    mission.status,
                                                )}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-foreground">
                                            <div className="w-24">
                                                <div className="h-2 bg-muted rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-foreground transition-all"
                                                        style={{
                                                            width: `${mission.progress || 0}%`,
                                                        }}
                                                    />
                                                </div>
                                                <span className="text-xs text-muted-foreground">
                                                    {Math.round(
                                                        mission.progress || 0,
                                                    )}
                                                    %
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-foreground">
                                            {mission.altitude}m
                                        </td>
                                        <td className="px-6 py-4 text-sm text-foreground">
                                            {mission.speed}m/s
                                        </td>
                                        <td className="px-6 py-4 text-right text-sm">
                                            <div className="flex gap-2 justify-end">
                                                {/* Start button for draft and scheduled missions */}
                                                {(mission.status === "draft" ||
                                                    mission.status ===
                                                        "scheduled") && (
                                                    <button
                                                        onClick={() => {
                                                            setLoadingMissionId(
                                                                mission.mission_id,
                                                            );
                                                            startMissionMutation.mutate(
                                                                mission.mission_id,
                                                            );
                                                        }}
                                                        disabled={
                                                            loadingMissionId ===
                                                            mission.mission_id
                                                        }
                                                        className="px-3 py-1 text-xs rounded bg-foreground text-background hover:opacity-90 disabled:opacity-50 font-medium"
                                                    >
                                                        {loadingMissionId ===
                                                        mission.mission_id
                                                            ? "..."
                                                            : "Start"}
                                                    </button>
                                                )}

                                                {mission.status ===
                                                    "in_progress" && (
                                                    <button
                                                        onClick={() => {
                                                            setLoadingMissionId(
                                                                mission.mission_id,
                                                            );
                                                            pauseMissionMutation.mutate(
                                                                mission.mission_id,
                                                            );
                                                        }}
                                                        disabled={
                                                            loadingMissionId ===
                                                            mission.mission_id
                                                        }
                                                        className="px-3 py-1 text-xs rounded bg-muted text-foreground hover:bg-muted/70 disabled:opacity-50 font-medium"
                                                    >
                                                        {loadingMissionId ===
                                                        mission.mission_id
                                                            ? "..."
                                                            : "Pause"}
                                                    </button>
                                                )}

                                                {mission.status ===
                                                    "paused" && (
                                                    <button
                                                        onClick={() => {
                                                            setLoadingMissionId(
                                                                mission.mission_id,
                                                            );
                                                            resumeMissionMutation.mutate(
                                                                mission.mission_id,
                                                            );
                                                        }}
                                                        disabled={
                                                            loadingMissionId ===
                                                            mission.mission_id
                                                        }
                                                        className="px-3 py-1 text-xs rounded bg-foreground text-background hover:opacity-90 disabled:opacity-50 font-medium"
                                                    >
                                                        {loadingMissionId ===
                                                        mission.mission_id
                                                            ? "..."
                                                            : "Resume"}
                                                    </button>
                                                )}

                                                {(mission.status ===
                                                    "in_progress" ||
                                                    mission.status ===
                                                        "paused") && (
                                                    <button
                                                        onClick={() => {
                                                            setLoadingMissionId(
                                                                mission.mission_id,
                                                            );
                                                            abortMissionMutation.mutate(
                                                                mission.mission_id,
                                                            );
                                                        }}
                                                        disabled={
                                                            loadingMissionId ===
                                                            mission.mission_id
                                                        }
                                                        className="px-3 py-1 text-xs rounded bg-muted text-muted-foreground hover:bg-muted/70 disabled:opacity-50 font-medium"
                                                    >
                                                        {loadingMissionId ===
                                                        mission.mission_id
                                                            ? "..."
                                                            : "Abort"}
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}
