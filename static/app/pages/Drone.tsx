import { Badge } from "@/components/ui/badge";
import baseService from "@/services/baseService";
import { droneService } from "@/services/droneService";
import type { Drone } from "@/types/drone";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
    Battery,
    Building2,
    Clock,
    Edit,
    Filter,
    Gauge,
    Mountain,
    Plus,
    Radio,
    Trash2,
    X,
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

const droneIcon = require("@/assets/images/drone-icon.png");

export default function Drone() {
    const queryClient = useQueryClient();
    const [selectedDrone, setSelectedDrone] = useState<Drone | null>(null);
    const [selectedBaseId, setSelectedBaseId] = useState<string>("all");
    const [selectedStatus, setSelectedStatus] = useState<string>("all");
    const [showAddModal, setShowAddModal] = useState(false);
    const [formData, setFormData] = useState({
        name: "",
        model: "",
        manufacturer: "DJI",
        base_id: "",
        max_flight_time: 30,
        max_speed: 15,
        max_altitude: 120,
        payload_capacity: 0.5,
    });

    // Fetch all bases
    const { data: basesData } = useQuery({
        queryKey: ["bases"],
        queryFn: async () => {
            const result = await baseService.getAll();
            return result;
        },
    });

    // Fetch all drones
    const { data: dronesData, isLoading: dronesLoading } = useQuery({
        queryKey: ["drones"],
        queryFn: async () => {
            const result = await droneService.getAll();
            return result;
        },
    });

    // Delete drone mutation
    const deleteDroneMutation = useMutation({
        mutationFn: droneService.delete,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["drones"] });
            setSelectedDrone(null);
            toast.success("Drone deleted successfully");
        },
        onError: (error: any) => {
            toast.error(error.message || "Failed to delete drone");
        },
    });

    // Create drone mutation
    const createDroneMutation = useMutation({
        mutationFn: droneService.create,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["drones"] });
            setShowAddModal(false);
            setFormData({
                name: "",
                model: "",
                manufacturer: "DJI",
                base_id: "",
                max_flight_time: 30,
                max_speed: 15,
                max_altitude: 120,
                payload_capacity: 0.5,
            });
            toast.success("Drone added successfully");
        },
        onError: (error: any) => {
            toast.error(error.message || "Failed to add drone");
        },
    });

    if (dronesLoading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
                    <p className="mt-4 text-muted-foreground">
                        Loading drones...
                    </p>
                </div>
            </div>
        );
    }

    const bases = basesData?.data || [];
    const drones = dronesData?.data || [];

    // Filter drones based on selected base and status
    const filteredDrones = drones.filter((drone: Drone) => {
        const baseMatch =
            selectedBaseId === "all" || drone.base_id === selectedBaseId;
        const statusMatch =
            selectedStatus === "all" || drone.status === selectedStatus;
        return baseMatch && statusMatch;
    });

    // All possible drone statuses
    const allStatuses = [
        { value: "all", label: "All Status" },
        { value: "available", label: "Available" },
        { value: "in_flight", label: "In Flight" },
        { value: "dispatching", label: "Dispatching" },
        { value: "returning", label: "Returning" },
        { value: "charging", label: "Charging" },
        { value: "maintenance", label: "Maintenance" },
        { value: "offline", label: "Offline" },
    ];

    const handleDroneDelete = (droneId: string) => {
        if (
            confirm(
                "Are you sure you want to delete this drone? This action cannot be undone.",
            )
        ) {
            deleteDroneMutation.mutate(droneId);
        }
    };

    const getStatusConfig = (status: string) => {
        const configs: Record<
            string,
            {
                label: string;
                variant: "default" | "secondary" | "outline";
                color: string;
            }
        > = {
            available: {
                label: "Available",
                variant: "default",
                color: "bg-green-500",
            },
            in_flight: {
                label: "In Flight",
                variant: "default",
                color: "bg-blue-500",
            },
            dispatching: {
                label: "Dispatching",
                variant: "secondary",
                color: "bg-yellow-500",
            },
            returning: {
                label: "Returning",
                variant: "secondary",
                color: "bg-purple-500",
            },
            charging: {
                label: "Charging",
                variant: "secondary",
                color: "bg-orange-500",
            },
            maintenance: {
                label: "Maintenance",
                variant: "outline",
                color: "bg-gray-500",
            },
            offline: {
                label: "Offline",
                variant: "outline",
                color: "bg-red-500",
            },
        };
        return (
            configs[status] || {
                label: status,
                variant: "secondary" as const,
                color: "bg-gray-400",
            }
        );
    };

    const getBatteryColor = (level: number) => {
        if (level > 60) return "text-green-600";
        if (level > 30) return "text-yellow-600";
        return "text-red-600";
    };

    return (
        <div className="p-8 h-[calc(100vh-64px)] flex flex-col overflow-hidden">
            {/* Header */}
            <div className="flex-shrink-0 mb-6 flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-foreground">
                        Drones
                    </h1>
                    <p className="mt-1 text-muted-foreground">
                        Monitor and manage your drone fleet
                    </p>
                </div>
                <button
                    onClick={() => setShowAddModal(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                >
                    <Plus className="h-5 w-5" />
                    Add Drone
                </button>
            </div>

            {/* Main Content - Two Column Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
                {/* Left Column - Drone List */}
                <div className="lg:col-span-1 flex flex-col min-h-0">
                    {/* Fleet Header */}
                    <div className="flex-shrink-0 mb-4">
                        <div className="flex items-center justify-between mb-3">
                            <h2 className="text-xl font-semibold">
                                Fleet ({filteredDrones.length})
                            </h2>
                            <div className="flex gap-2 text-xs text-muted-foreground">
                                <span className="flex items-center gap-1">
                                    <span className="w-2 h-2 rounded-full bg-green-500"></span>
                                    {
                                        drones.filter(
                                            (d: Drone) =>
                                                d.status === "available",
                                        ).length
                                    }{" "}
                                    Available
                                </span>
                            </div>
                        </div>

                        {/* Filters */}
                        <div className="flex gap-2">
                            {/* Base Filter */}
                            <div className="flex-1 relative">
                                <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                                    <Building2 className="h-4 w-4" />
                                </div>
                                <select
                                    value={selectedBaseId}
                                    onChange={(e) =>
                                        setSelectedBaseId(e.target.value)
                                    }
                                    className="w-full pl-9 pr-3 py-2 text-sm bg-card border rounded-lg appearance-none cursor-pointer hover:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20"
                                >
                                    <option value="all">All Bases</option>
                                    {bases.map((base: any) => (
                                        <option
                                            key={base.base_id}
                                            value={base.base_id}
                                        >
                                            {base.name}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {/* Status Filter */}
                            <div className="flex-1 relative">
                                <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                                    <Filter className="h-4 w-4" />
                                </div>
                                <select
                                    value={selectedStatus}
                                    onChange={(e) =>
                                        setSelectedStatus(e.target.value)
                                    }
                                    className="w-full pl-9 pr-3 py-2 text-sm bg-card border rounded-lg appearance-none cursor-pointer hover:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20 capitalize"
                                >
                                    {allStatuses.map((status) => (
                                        <option
                                            key={status.value}
                                            value={status.value}
                                        >
                                            {status.label}
                                        </option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </div>

                    {/* Scrollable Drone List */}
                    <div className="flex-1 overflow-y-auto space-y-2 pr-2 min-h-0">
                        {filteredDrones.length === 0 ? (
                            <div className="text-center py-12 text-muted-foreground bg-card rounded-lg border">
                                {drones.length === 0
                                    ? "No drones found. Add one to get started."
                                    : "No drones match the selected filters."}
                            </div>
                        ) : (
                            filteredDrones.map((drone: Drone) => {
                                const statusConfig = getStatusConfig(
                                    drone.status,
                                );
                                const isSelected =
                                    selectedDrone?.drone_id === drone.drone_id;

                                return (
                                    <button
                                        key={drone.drone_id}
                                        onClick={() => setSelectedDrone(drone)}
                                        className={`w-full p-4 rounded-lg border text-left transition-all duration-200 ${
                                            isSelected
                                                ? "bg-foreground text-background border-foreground shadow-lg"
                                                : "bg-card hover:bg-muted/50 hover:border-primary/50"
                                        }`}
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-3">
                                                <img
                                                    src={droneIcon}
                                                    alt="Drone"
                                                    className={`h-10 w-10 object-contain ${isSelected ? "invert" : ""}`}
                                                />
                                                <div>
                                                    <div className="font-semibold">
                                                        {drone.drone_id}
                                                    </div>
                                                    <div
                                                        className={`text-xs ${isSelected ? "text-background/70" : "text-muted-foreground"}`}
                                                    >
                                                        {drone.model ||
                                                            "Unknown Model"}
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="flex flex-col items-end gap-1">
                                                <Badge
                                                    variant={
                                                        isSelected
                                                            ? "secondary"
                                                            : statusConfig.variant
                                                    }
                                                >
                                                    {statusConfig.label}
                                                </Badge>
                                                <div
                                                    className={`text-xs font-medium flex items-center gap-1 ${isSelected ? "text-background/80" : getBatteryColor(drone.battery_level)}`}
                                                >
                                                    <Battery className="h-3 w-3" />
                                                    {drone.battery_level}%
                                                </div>
                                            </div>
                                        </div>
                                    </button>
                                );
                            })
                        )}
                    </div>
                </div>

                {/* Right Column - Drone Details */}
                <div className="lg:col-span-2 min-h-0">
                    {selectedDrone ? (
                        <div className="h-full bg-card rounded-xl border shadow-sm overflow-hidden flex flex-col">
                            {/* Header with drone ID and actions */}
                            <div className="flex-shrink-0 px-6 py-4 border-b flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div>
                                        <h2 className="text-2xl font-bold text-foreground tracking-wide">
                                            {selectedDrone.name ||
                                                selectedDrone.drone_id}
                                        </h2>
                                        <div className="flex items-center gap-3 mt-1">
                                            <Badge
                                                variant={
                                                    getStatusConfig(
                                                        selectedDrone.status,
                                                    ).variant
                                                }
                                            >
                                                {
                                                    getStatusConfig(
                                                        selectedDrone.status,
                                                    ).label
                                                }
                                            </Badge>
                                            <span className="text-sm text-muted-foreground">
                                                {selectedDrone.model ||
                                                    "Unknown Model"}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={() =>
                                            toast.info("Edit coming soon")
                                        }
                                        className="p-2 rounded-lg border hover:bg-muted transition-colors"
                                    >
                                        <Edit className="h-5 w-5" />
                                    </button>
                                    <button
                                        onClick={() =>
                                            handleDroneDelete(
                                                selectedDrone.drone_id,
                                            )
                                        }
                                        className="p-2 rounded-lg border hover:bg-destructive/10 hover:text-destructive transition-colors"
                                    >
                                        <Trash2 className="h-5 w-5" />
                                    </button>
                                </div>
                            </div>

                            {/* Main Content - Hero Layout */}
                            <div className="flex-1 p-6 overflow-y-auto relative">
                                {/* Central Drone Display */}
                                <div className="flex flex-col lg:flex-row items-center justify-center gap-8 min-h-[280px]">
                                    {/* Left Stats Column */}
                                    <div className="flex flex-col gap-6 lg:w-40">
                                        {/* Speed */}
                                        <div className="flex items-center gap-4">
                                            <Gauge className="h-8 w-8 text-foreground" />
                                            <div>
                                                <div className="text-2xl font-bold text-foreground">
                                                    {Math.round(
                                                        selectedDrone.max_speed ||
                                                            0,
                                                    )}
                                                    <span className="text-sm font-normal text-muted-foreground ml-1">
                                                        m/s
                                                    </span>
                                                </div>
                                                <div className="text-xs text-muted-foreground uppercase tracking-wider">
                                                    Speed
                                                </div>
                                                <div className="w-16 h-0.5 bg-border mt-1"></div>
                                            </div>
                                        </div>

                                        {/* Altitude */}
                                        <div className="flex items-center gap-4">
                                            <Mountain className="h-8 w-8 text-foreground" />
                                            <div>
                                                <div className="text-2xl font-bold text-foreground">
                                                    {Math.round(
                                                        selectedDrone.max_altitude ||
                                                            0,
                                                    )}
                                                </div>
                                                <div className="text-xs text-muted-foreground uppercase tracking-wider">
                                                    Altitude
                                                </div>
                                                <div className="w-16 h-0.5 bg-border mt-1"></div>
                                            </div>
                                        </div>

                                        {/* Flight Time */}
                                        <div className="flex items-center gap-4">
                                            <Clock className="h-8 w-8 text-foreground" />
                                            <div>
                                                <div className="text-2xl font-bold text-foreground">
                                                    {selectedDrone.max_flight_time ||
                                                        0}
                                                    <span className="text-sm font-normal text-muted-foreground ml-1">
                                                        min
                                                    </span>
                                                </div>
                                                <div className="text-xs text-muted-foreground uppercase tracking-wider">
                                                    Flight Time
                                                </div>
                                                <div className="w-16 h-0.5 bg-border mt-1"></div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Center - Drone Image */}
                                    <div className="relative flex-shrink-0">
                                        {/* Drone Image */}
                                        <div className="relative">
                                            {selectedDrone.image_url ? (
                                                <img
                                                    src={
                                                        selectedDrone.image_url
                                                    }
                                                    alt={selectedDrone.model}
                                                    className="h-48 w-auto object-contain drop-shadow-xl"
                                                    onError={(e) => {
                                                        (
                                                            e.target as HTMLImageElement
                                                        ).src = droneIcon;
                                                    }}
                                                />
                                            ) : (
                                                <img
                                                    src={droneIcon}
                                                    alt="Drone"
                                                    className="h-48 w-48 object-contain drop-shadow-xl opacity-50"
                                                />
                                            )}
                                        </div>

                                        {/* Shadow beneath drone */}
                                        <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 w-32 h-4 bg-foreground/10 rounded-full blur-md"></div>
                                    </div>

                                    {/* Right Stats Column */}
                                    <div className="flex flex-col gap-6 lg:w-40">
                                        {/* Battery */}
                                        <div className="flex items-center gap-4">
                                            <Battery
                                                className={`h-8 w-8 ${
                                                    selectedDrone.battery_level >
                                                    60
                                                        ? "text-green-600"
                                                        : selectedDrone.battery_level >
                                                            30
                                                          ? "text-yellow-600"
                                                          : "text-red-600"
                                                }`}
                                            />
                                            <div>
                                                <div
                                                    className={`text-2xl font-bold ${
                                                        selectedDrone.battery_level >
                                                        60
                                                            ? "text-green-600"
                                                            : selectedDrone.battery_level >
                                                                30
                                                              ? "text-yellow-600"
                                                              : "text-red-600"
                                                    }`}
                                                >
                                                    {
                                                        selectedDrone.battery_level
                                                    }
                                                    %
                                                </div>
                                                <div className="text-xs text-muted-foreground uppercase tracking-wider">
                                                    Battery
                                                </div>
                                                <div className="w-16 h-1 bg-muted mt-1 rounded-full overflow-hidden">
                                                    <div
                                                        className={`h-full ${
                                                            selectedDrone.battery_level >
                                                            60
                                                                ? "bg-green-500"
                                                                : selectedDrone.battery_level >
                                                                    30
                                                                  ? "bg-yellow-500"
                                                                  : "bg-red-500"
                                                        }`}
                                                        style={{
                                                            width: `${selectedDrone.battery_level}%`,
                                                        }}
                                                    />
                                                </div>
                                            </div>
                                        </div>

                                        {/* Base */}
                                        <div className="flex items-center gap-4">
                                            <Building2 className="h-8 w-8 text-foreground" />
                                            <div>
                                                <div className="text-sm font-bold text-foreground truncate max-w-24">
                                                    {selectedDrone.base_id ||
                                                        "Unassigned"}
                                                </div>
                                                <div className="text-xs text-muted-foreground uppercase tracking-wider">
                                                    Base
                                                </div>
                                                <div className="w-16 h-0.5 bg-border mt-1"></div>
                                            </div>
                                        </div>

                                        {/* Mission */}
                                        <div className="flex items-center gap-4">
                                            <Radio className="h-8 w-8 text-foreground" />
                                            <div>
                                                <div className="text-sm font-bold text-foreground truncate max-w-24">
                                                    {selectedDrone.current_mission_id ||
                                                        "None"}
                                                </div>
                                                <div className="text-xs text-muted-foreground uppercase tracking-wider">
                                                    Mission
                                                </div>
                                                <div className="w-16 h-0.5 bg-border mt-1"></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Bottom Info Cards */}
                                <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <div className="bg-muted/50 rounded-xl p-4 border text-center">
                                        <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
                                            Manufacturer
                                        </div>
                                        <div className="text-foreground font-semibold">
                                            {selectedDrone.manufacturer ||
                                                "DJI"}
                                        </div>
                                    </div>
                                    <div className="bg-muted/50 rounded-xl p-4 border text-center">
                                        <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
                                            Payload
                                        </div>
                                        <div className="text-foreground font-semibold">
                                            {selectedDrone.payload_capacity?.toFixed(
                                                1,
                                            ) || 0}{" "}
                                            kg
                                        </div>
                                    </div>
                                    <div className="bg-muted/50 rounded-xl p-4 border text-center">
                                        <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
                                            Flight Hours
                                        </div>
                                        <div className="text-foreground font-semibold">
                                            {Math.round(
                                                selectedDrone.total_flight_hours ||
                                                    0,
                                            )}{" "}
                                            hrs
                                        </div>
                                    </div>
                                    <div className="bg-muted/50 rounded-xl p-4 border text-center">
                                        <div className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
                                            Health
                                        </div>
                                        <div
                                            className={`font-semibold capitalize ${
                                                selectedDrone.health_status ===
                                                "good"
                                                    ? "text-green-600"
                                                    : selectedDrone.health_status ===
                                                        "warning"
                                                      ? "text-yellow-600"
                                                      : "text-red-600"
                                            }`}
                                        >
                                            {selectedDrone.health_status ||
                                                "Good"}
                                        </div>
                                    </div>
                                </div>

                                {/* Sensors */}
                                {selectedDrone.sensors &&
                                    selectedDrone.sensors.length > 0 && (
                                        <div className="mt-6 bg-muted/50 rounded-xl p-4 border">
                                            <div className="text-xs text-muted-foreground uppercase tracking-wider mb-3">
                                                Sensors & Equipment
                                            </div>
                                            <div className="flex flex-wrap gap-2">
                                                {selectedDrone.sensors.map(
                                                    (sensor) => (
                                                        <Badge
                                                            key={sensor}
                                                            variant="secondary"
                                                            className="px-3 py-1"
                                                        >
                                                            {sensor}
                                                        </Badge>
                                                    ),
                                                )}
                                            </div>
                                        </div>
                                    )}
                            </div>
                        </div>
                    ) : (
                        <div className="h-full bg-card rounded-xl border flex flex-col items-center justify-center">
                            <img
                                src={droneIcon}
                                alt="Drone"
                                className="h-32 w-32 object-contain opacity-20 mb-6"
                            />
                            <p className="text-lg text-muted-foreground">
                                Select a drone to view details
                            </p>
                            <p className="text-sm mt-2 text-muted-foreground/70">
                                Choose from the fleet list on the left
                            </p>
                        </div>
                    )}
                </div>
            </div>

            {/* Add Drone Modal */}
            {showAddModal && (
                <div className="fixed inset-0 bg-foreground/20 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-card rounded-xl border shadow-lg max-w-2xl w-full max-h-[90vh] overflow-hidden">
                        {/* Modal Header */}
                        <div className="p-6 border-b flex items-center justify-between">
                            <h2 className="text-2xl font-bold text-foreground">
                                Add New Drone
                            </h2>
                            <button
                                onClick={() => setShowAddModal(false)}
                                className="p-2 hover:bg-muted rounded-lg transition-colors"
                            >
                                <X className="h-5 w-5" />
                            </button>
                        </div>

                        {/* Modal Form */}
                        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
                            <form
                                onSubmit={(e) => {
                                    e.preventDefault();
                                    if (
                                        !formData.name ||
                                        !formData.model ||
                                        !formData.base_id
                                    ) {
                                        toast.error(
                                            "Please fill in all required fields",
                                        );
                                        return;
                                    }
                                    createDroneMutation.mutate(formData);
                                }}
                                className="space-y-4"
                            >
                                {/* Drone Name */}
                                <div>
                                    <label className="block text-sm font-medium mb-2 text-foreground">
                                        Drone Name *
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.name}
                                        onChange={(e) =>
                                            setFormData({
                                                ...formData,
                                                name: e.target.value,
                                            })
                                        }
                                        className="w-full px-3 py-2 border rounded-lg bg-background focus:ring-2 focus:ring-primary focus:outline-none"
                                        placeholder="e.g., Alpha-001"
                                        required
                                    />
                                </div>

                                {/* Model */}
                                <div>
                                    <label className="block text-sm font-medium mb-2 text-foreground">
                                        Model *
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.model}
                                        onChange={(e) =>
                                            setFormData({
                                                ...formData,
                                                model: e.target.value,
                                            })
                                        }
                                        className="w-full px-3 py-2 border rounded-lg bg-background focus:ring-2 focus:ring-primary focus:outline-none"
                                        placeholder="e.g., DJI Mavic 4 Pro"
                                        required
                                    />
                                </div>

                                {/* Manufacturer */}
                                <div>
                                    <label className="block text-sm font-medium mb-2 text-foreground">
                                        Manufacturer
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.manufacturer}
                                        onChange={(e) =>
                                            setFormData({
                                                ...formData,
                                                manufacturer: e.target.value,
                                            })
                                        }
                                        className="w-full px-3 py-2 border rounded-lg bg-background focus:ring-2 focus:ring-primary focus:outline-none"
                                        placeholder="e.g., DJI"
                                    />
                                </div>

                                {/* Base Assignment */}
                                <div>
                                    <label className="block text-sm font-medium mb-2 text-foreground">
                                        Assign to Base *
                                    </label>
                                    <select
                                        value={formData.base_id}
                                        onChange={(e) =>
                                            setFormData({
                                                ...formData,
                                                base_id: e.target.value,
                                            })
                                        }
                                        className="w-full px-3 py-2 border rounded-lg bg-background focus:ring-2 focus:ring-primary focus:outline-none"
                                        required
                                    >
                                        <option value="">Select a base</option>
                                        {bases.map((base: any) => (
                                            <option
                                                key={base.base_id}
                                                value={base.base_id}
                                            >
                                                {base.name}
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                {/* Technical Specifications */}
                                <div className="pt-4 border-t">
                                    <h3 className="text-lg font-semibold mb-4 text-foreground">
                                        Technical Specifications
                                    </h3>
                                    <div className="grid grid-cols-2 gap-4">
                                        {/* Max Flight Time */}
                                        <div>
                                            <label className="block text-sm font-medium mb-2 text-foreground">
                                                Max Flight Time (min)
                                            </label>
                                            <input
                                                type="number"
                                                value={formData.max_flight_time}
                                                onChange={(e) =>
                                                    setFormData({
                                                        ...formData,
                                                        max_flight_time: Number(
                                                            e.target.value,
                                                        ),
                                                    })
                                                }
                                                className="w-full px-3 py-2 border rounded-lg bg-background focus:ring-2 focus:ring-primary focus:outline-none"
                                                min="1"
                                            />
                                        </div>

                                        {/* Max Speed */}
                                        <div>
                                            <label className="block text-sm font-medium mb-2 text-foreground">
                                                Max Speed (m/s)
                                            </label>
                                            <input
                                                type="number"
                                                value={formData.max_speed}
                                                onChange={(e) =>
                                                    setFormData({
                                                        ...formData,
                                                        max_speed: Number(
                                                            e.target.value,
                                                        ),
                                                    })
                                                }
                                                className="w-full px-3 py-2 border rounded-lg bg-background focus:ring-2 focus:ring-primary focus:outline-none"
                                                min="1"
                                            />
                                        </div>

                                        {/* Max Altitude */}
                                        <div>
                                            <label className="block text-sm font-medium mb-2 text-foreground">
                                                Max Altitude (m)
                                            </label>
                                            <input
                                                type="number"
                                                value={formData.max_altitude}
                                                onChange={(e) =>
                                                    setFormData({
                                                        ...formData,
                                                        max_altitude: Number(
                                                            e.target.value,
                                                        ),
                                                    })
                                                }
                                                className="w-full px-3 py-2 border rounded-lg bg-background focus:ring-2 focus:ring-primary focus:outline-none"
                                                min="1"
                                            />
                                        </div>

                                        {/* Payload Capacity */}
                                        <div>
                                            <label className="block text-sm font-medium mb-2 text-foreground">
                                                Payload Capacity (kg)
                                            </label>
                                            <input
                                                type="number"
                                                step="0.1"
                                                value={
                                                    formData.payload_capacity
                                                }
                                                onChange={(e) =>
                                                    setFormData({
                                                        ...formData,
                                                        payload_capacity:
                                                            Number(
                                                                e.target.value,
                                                            ),
                                                    })
                                                }
                                                className="w-full px-3 py-2 border rounded-lg bg-background focus:ring-2 focus:ring-primary focus:outline-none"
                                                min="0"
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* Action Buttons */}
                                <div className="flex gap-3 pt-4">
                                    <button
                                        type="submit"
                                        disabled={createDroneMutation.isPending}
                                        className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        {createDroneMutation.isPending
                                            ? "Adding..."
                                            : "Add Drone"}
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setShowAddModal(false)}
                                        className="px-4 py-2 border rounded-lg hover:bg-muted transition-colors"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
