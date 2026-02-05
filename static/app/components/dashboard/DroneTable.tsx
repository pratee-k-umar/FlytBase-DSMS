import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import type { Drone } from "@/types/drone";
import { Battery, Edit, Trash2 } from "lucide-react";

interface DroneTableProps {
    drones: Drone[];
    selectedDroneId?: string;
    onSelectDrone: (drone: Drone) => void;
    onEdit: (drone: Drone) => void;
    onDelete: (droneId: string) => void;
}

export const DroneTable = ({
    drones,
    selectedDroneId,
    onSelectDrone,
    onEdit,
    onDelete,
}: DroneTableProps) => {
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

    const getBatteryColor = (level: number) => {
        if (level > 60) return "text-foreground";
        if (level > 20) return "text-muted-foreground";
        return "text-muted-foreground";
    };

    if (drones.length === 0) {
        return (
            <div className="text-center py-12 text-muted-foreground">
                <p className="text-lg">No drones at this base</p>
                <p className="text-sm mt-2">
                    Drones will appear here when assigned to this base
                </p>
            </div>
        );
    }

    return (
        <Table>
            <TableHeader>
                <TableRow>
                    <TableHead>Drone ID</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead>Battery</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {drones.map((drone) => (
                    <TableRow
                        key={drone.drone_id}
                        className={`cursor-pointer ${
                            selectedDroneId === drone.drone_id ? "bg-muted" : ""
                        }`}
                        onClick={() => onSelectDrone(drone)}
                    >
                        <TableCell className="font-medium">
                            {drone.drone_id}
                        </TableCell>
                        <TableCell>{drone.model || "N/A"}</TableCell>
                        <TableCell>
                            <div className="flex items-center gap-2">
                                <Battery
                                    className={`h-4 w-4 ${getBatteryColor(drone.battery_level)}`}
                                />
                                <span
                                    className={getBatteryColor(
                                        drone.battery_level,
                                    )}
                                >
                                    {drone.battery_level}%
                                </span>
                            </div>
                        </TableCell>
                        <TableCell>{getStatusBadge(drone.status)}</TableCell>
                        <TableCell className="text-right">
                            <div className="flex justify-end gap-2">
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onEdit(drone);
                                    }}
                                >
                                    <Edit className="h-4 w-4" />
                                </Button>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onDelete(drone.drone_id);
                                    }}
                                >
                                    <Trash2 className="h-4 w-4" />
                                </Button>
                            </div>
                        </TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
};
