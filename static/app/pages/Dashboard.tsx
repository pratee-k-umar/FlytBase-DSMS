import { droneService } from "@/services/droneService";
import { useQuery } from "@tanstack/react-query";

export default function Dashboard() {
    const { data: dronesData, isLoading: dronesLoading } = useQuery({
        queryKey: ["drones"],
        queryFn: droneService.getAll,
    });

    const { data: fleetStats, isLoading: statsLoading } = useQuery({
        queryKey: ["fleetStats"],
        queryFn: droneService.getStats,
    });

    const isLoading = dronesLoading || statsLoading;

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
                    <p className="mt-4 text-muted-foreground">
                        Loading dashboard...
                    </p>
                </div>
            </div>
        );
    }

    const stats = [
        { name: "Total Drones", value: dronesData?.count || 0 },
        { name: "Available", value: fleetStats?.data?.available || 0 },
        { name: "In Mission", value: fleetStats?.data?.in_mission || 0 },
        { name: "Maintenance", value: fleetStats?.data?.maintenance || 0 },
    ];

    return (
        <div className="p-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-foreground">
                    Fleet Dashboard
                </h1>
                <p className="mt-2 text-muted-foreground">
                    Monitor your drone fleet and operations
                </p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                {stats.map((stat) => (
                    <div
                        key={stat.name}
                        className="bg-card rounded-lg border shadow-sm p-6"
                    >
                        <div>
                            <p className="text-sm text-muted-foreground">
                                {stat.name}
                            </p>
                            <p className="text-3xl font-bold mt-2 text-foreground">
                                {stat.value}
                            </p>
                        </div>
                    </div>
                ))}
            </div>

            {/* Drones Grid */}
            <div className="bg-card rounded-lg border shadow-sm">
                <div className="px-6 py-4 border-b">
                    <h2 className="text-xl font-semibold text-card-foreground">
                        Drone Fleet
                    </h2>
                </div>
                <div className="p-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {dronesData?.data?.map((drone) => (
                            <div
                                key={drone.id}
                                className="border rounded-lg p-4 hover:shadow-md transition-shadow bg-card"
                            >
                                <div className="flex items-start justify-between mb-3">
                                    <div>
                                        <h3 className="font-semibold text-card-foreground">
                                            {drone.name}
                                        </h3>
                                        <p className="text-sm text-muted-foreground">
                                            {drone.model}
                                        </p>
                                    </div>
                                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-muted text-muted-foreground">
                                        {drone.status}
                                    </span>
                                </div>
                                <div className="space-y-2">
                                    <div className="flex items-center justify-between text-sm">
                                        <span className="text-muted-foreground">
                                            Battery
                                        </span>
                                        <span className="font-medium text-card-foreground">
                                            {drone.battery_level}%
                                        </span>
                                    </div>
                                    <div className="w-full bg-secondary rounded-full h-2">
                                        <div
                                            className="h-2 rounded-full bg-foreground"
                                            style={{
                                                width: `${drone.battery_level}%`,
                                            }}
                                        ></div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
