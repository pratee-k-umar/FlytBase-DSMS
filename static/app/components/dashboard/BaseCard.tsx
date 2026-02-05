import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DroneBase } from "@/types/base";
import { Home } from "lucide-react";
const droneIcon = require("@/assets/images/drone-icon.png");

interface BaseCardProps {
    base: DroneBase;
    droneCount: number;
    availableCount: number;
    isSelected: boolean;
    onClick: () => void;
}

export const BaseCard = ({
    base,
    droneCount,
    availableCount,
    isSelected,
    onClick,
}: BaseCardProps) => {
    const getStatusColor = (status: string) => {
        switch (status) {
            case "active":
                return "bg-primary";
            case "maintenance":
                return "bg-muted";
            case "offline":
                return "bg-muted-foreground";
            default:
                return "bg-muted";
        }
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case "active":
                return <Badge variant="default">Active</Badge>;
            case "maintenance":
                return <Badge variant="secondary">Maintenance</Badge>;
            case "offline":
                return <Badge variant="outline">Offline</Badge>;
            default:
                return <Badge variant="secondary">Unknown</Badge>;
        }
    };

    return (
        <Card
            className={`cursor-pointer transition-all hover:shadow-md ${
                isSelected ? "ring-primary shadow-lg" : ""
            }`}
            onClick={onClick}
        >
            <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                        <Home className="h-4 w-4 text-muted-foreground" />
                        <CardTitle className="text-base">{base.name}</CardTitle>
                    </div>
                    {getStatusBadge(base.status)}
                </div>
            </CardHeader>
            <CardContent className="space-y-2">
                <div className="flex items-center gap-2 text-sm">
                    <img
                        src={droneIcon}
                        alt="Drone"
                        className="h-4 w-4 object-contain"
                    />
                    <span className="text-muted-foreground">Drones:</span>
                    <span className="font-medium">
                        {droneCount} / {base.max_drones}
                    </span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                    <div
                        className={`h-2 w-2 rounded-full ${getStatusColor("active")}`}
                    />
                    <span className="text-muted-foreground">Available:</span>
                    <span className="font-medium">{availableCount}</span>
                </div>
                <div className="text-xs text-muted-foreground mt-2">
                    {base.lat.toFixed(4)}°N, {base.lng.toFixed(4)}°E
                </div>
            </CardContent>
        </Card>
    );
};
