import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DroneBase } from "@/types/base";
import { Edit, MapPin, Trash2 } from "lucide-react";

interface BaseDetailsProps {
    base: DroneBase;
    droneCount: number;
    availableCount: number;
    onEdit: () => void;
    onDelete: () => void;
}

export const BaseDetails = ({
    base,
    droneCount,
    availableCount,
    onEdit,
    onDelete,
}: BaseDetailsProps) => {
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

    const utilization =
        base.max_drones > 0
            ? ((droneCount / base.max_drones) * 100).toFixed(0)
            : 0;

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="text-xl">{base.name}</CardTitle>
                    <div className="flex gap-2">
                        <Button variant="outline" size="sm" onClick={onEdit}>
                            <Edit className="h-4 w-4 mr-1" />
                            Edit
                        </Button>
                        <Button
                            variant="destructive"
                            size="sm"
                            onClick={onDelete}
                        >
                            <Trash2 className="h-4 w-4 mr-1" />
                            Delete
                        </Button>
                    </div>
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                        <div className="text-sm text-muted-foreground">
                            Status
                        </div>
                        <div className="mt-1">
                            {getStatusBadge(base.status)}
                        </div>
                    </div>
                    <div>
                        <div className="text-sm text-muted-foreground">
                            Total Drones
                        </div>
                        <div className="mt-1 text-lg font-semibold">
                            {droneCount} / {base.max_drones}
                        </div>
                    </div>
                    <div>
                        <div className="text-sm text-muted-foreground">
                            Available
                        </div>
                        <div className="mt-1 text-lg font-semibold text-foreground">
                            {availableCount}
                        </div>
                    </div>
                    <div>
                        <div className="text-sm text-muted-foreground">
                            Utilization
                        </div>
                        <div className="mt-1 text-lg font-semibold">
                            {utilization}%
                        </div>
                    </div>
                </div>

                <div className="pt-2 border-t">
                    <div className="flex items-center gap-2 text-sm">
                        <MapPin className="h-4 w-4 text-muted-foreground" />
                        <span className="text-muted-foreground">Location:</span>
                        <span className="font-mono">
                            {base.lat.toFixed(6)}°N, {base.lng.toFixed(6)}°E
                        </span>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};
