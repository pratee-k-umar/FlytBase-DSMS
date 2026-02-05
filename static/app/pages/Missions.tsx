import { missionService } from "@/services/missionService";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

export default function Missions() {
    const queryClient = useQueryClient();
    const [selectedStatus, setSelectedStatus] = useState<string>("all");
    const [loadingMissionId, setLoadingMissionId] = useState<string | null>(
        null,
    );
    const [currentPage, setCurrentPage] = useState<number>(1);
    const itemsPerPage = 10;

    const { data: missionsData, isLoading, refetch } = useQuery({
        queryKey: ["missions", selectedStatus],
        queryFn: () => {
            if (selectedStatus === "all") {
                return missionService.getAll({ limit: 50 });
            }
            return missionService.getAll({ status: selectedStatus, limit: 50 });
        },
        refetchInterval: 5000, // Slower refresh to reduce load
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

    // Pagination logic
    const totalPages = Math.ceil(missions.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedMissions = missions.slice(startIndex, endIndex);

    // Reset to page 1 when status filter changes
    const handleStatusChange = (status: string) => {
        setSelectedStatus(status);
        setCurrentPage(1);
    };

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
                    onClick={() => refetch()}
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
                        onClick={() => handleStatusChange(status.value)}
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
                <div className="px-6 py-4 border-b flex items-center justify-between">
                    <h2 className="text-lg font-semibold text-card-foreground">
                        {missions.length} Mission
                        {missions.length !== 1 ? "s" : ""}
                    </h2>
                    {missions.length > 0 && (
                        <p className="text-sm text-muted-foreground">
                            Showing {startIndex + 1}-{Math.min(endIndex, missions.length)} of {missions.length}
                        </p>
                    )}
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
                                {paginatedMissions.map((mission: any) => (
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

                {/* Pagination */}
                {missions.length > itemsPerPage && (
                    <div className="px-6 py-4 border-t flex items-center justify-between">
                        <button
                            onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                            disabled={currentPage === 1}
                            className="px-4 py-2 text-sm font-medium rounded-md bg-muted text-foreground hover:bg-muted/70 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            Previous
                        </button>

                        <div className="flex items-center gap-2">
                            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                                <button
                                    key={page}
                                    onClick={() => setCurrentPage(page)}
                                    className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                                        currentPage === page
                                            ? "bg-foreground text-background"
                                            : "bg-muted text-foreground hover:bg-muted/70"
                                    }`}
                                >
                                    {page}
                                </button>
                            ))}
                        </div>

                        <button
                            onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
                            disabled={currentPage === totalPages}
                            className="px-4 py-2 text-sm font-medium rounded-md bg-muted text-foreground hover:bg-muted/70 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            Next
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
