import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Drone } from "@/types/drone";
import { Battery, Edit, X } from "lucide-react";

const droneIcon = require("@/assets/images/drone-icon.png");

interface DroneDetailsCardProps {
    drone: Drone | null;
    onEdit: () => void;
    onClose: () => void;
}

export const DroneDetailsCard = ({
    drone,
    onEdit,
    onClose,
}: DroneDetailsCardProps) => {
    if (!drone) {
        return null;
    }

    const getBatteryColor = (level: number) => {
        if (level > 60) return "text-foreground";
        if (level > 20) return "text-muted-foreground";
        return "text-muted-foreground";
    };

    const getStatusBadge = (status: string) => {
        const statusConfig: Record<
            string,
            { label: string; variant: "default" | "secondary" | "outline" }
        > = {
            available: { label: "Available", variant: "default" },
            in_flight: { label: "In Flight", variant: "default" },
            dispatching: { label: "Dispatching", variant: "secondary" },
            returning: { label: "Returning", variant: "secondary" },
            charging: { label: "Charging", variant: "secondary" },
            maintenance: { label: "Maintenance", variant: "outline" },
            offline: { label: "Offline", variant: "outline" },
        };

        const config = statusConfig[status] || {
            label: status,
            variant: "secondary" as const,
        };
        return <Badge variant={config.variant}>{config.label}</Badge>;
    };

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <img
                            src={droneIcon}
                            alt="Drone"
                            className="h-8 w-8 object-contain"
                        />
                        <CardTitle>{drone.drone_id}</CardTitle>
                        {getStatusBadge(drone.status)}
                    </div>
                    <div className="flex gap-2">
                        <Button variant="outline" size="sm" onClick={onEdit}>
                            <Edit className="h-4 w-4 mr-1" />
                            Edit
                        </Button>
                        <Button variant="ghost" size="sm" onClick={onClose}>
                            <X className="h-4 w-4" />
                        </Button>
                    </div>
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                        <div className="text-sm text-muted-foreground">
                            Battery
                        </div>
                        <div
                            className={`mt-1 text-2xl font-bold ${getBatteryColor(drone.battery_level)}`}
                        >
                            <div className="flex items-center gap-2">
                                <Battery className="h-5 w-5" />
                                {drone.battery_level}%
                            </div>
                        </div>
                    </div>
                    <div>
                        <div className="text-sm text-muted-foreground">
                            Model
                        </div>
                        <div className="mt-1 font-medium">
                            {drone.model || "N/A"}
                        </div>
                    </div>
                    <div>
                        <div className="text-sm text-muted-foreground">
                            Base
                        </div>
                        <div className="mt-1 font-medium">
                            {drone.base_id || "Unassigned"}
                        </div>
                    </div>
                    <div>
                        <div className="text-sm text-muted-foreground">
                            Max Altitude
                        </div>
                        <div className="mt-1 font-medium">
                            {drone.max_altitude || 0}m
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4 pt-2 border-t">
                    <div>
                        <div className="text-sm text-muted-foreground">
                            Max Flight Time
                        </div>
                        <div className="mt-1">
                            {drone.max_flight_time || 0} min
                        </div>
                    </div>
                    <div>
                        <div className="text-sm text-muted-foreground">
                            Max Speed
                        </div>
                        <div className="mt-1">{drone.max_speed || 0} m/s</div>
                    </div>
                </div>

                {drone.sensors && drone.sensors.length > 0 && (
                    <div className="pt-2 border-t">
                        <div className="text-sm text-muted-foreground mb-2">
                            Sensors
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {drone.sensors.map((sensor) => (
                                <Badge key={sensor} variant="secondary">
                                    {sensor}
                                </Badge>
                            ))}
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    );
};
