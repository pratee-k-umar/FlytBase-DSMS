"""
Base Selection Service
Handles logic for selecting the optimal base for a mission based on location.
"""

from typing import Dict, List, Optional

from dsms.models.drone import Drone
from dsms.models.drone_base import DroneBase


class BaseSelectionService:
    """Service for selecting the best base for mission assignments."""

    @staticmethod
    def find_bases_in_range(target_lat: float, target_lng: float) -> List[DroneBase]:
        """
        Find all active bases whose operational range covers the target location.

        Args:
            target_lat: Target latitude
            target_lng: Target longitude

        Returns:
            List of DroneBase objects that cover the target location
        """
        bases = DroneBase.objects(status="active")
        bases_in_range = []

        for base in bases:
            if base.is_location_in_range(target_lat, target_lng):
                bases_in_range.append(base)

        return bases_in_range

    @staticmethod
    def get_available_drone_count(base: DroneBase) -> int:
        """
        Get count of available drones at a base.

        Args:
            base: DroneBase object

        Returns:
            Number of available drones
        """
        return Drone.objects(assigned_site=base.name, status="available").count()

    @staticmethod
    def select_best_base(
        target_lat: float, target_lng: float, strategy: str = "closest"
    ) -> Optional[Dict]:
        """
        Select the best base for a mission at the target location.

        Args:
            target_lat: Mission target latitude
            target_lng: Mission target longitude
            strategy: Selection strategy - "closest", "most_drones", or "balanced"

        Returns:
            Dict with base info and metadata, or None if no base in range
        """
        bases_in_range = BaseSelectionService.find_bases_in_range(
            target_lat, target_lng
        )

        if not bases_in_range:
            return None

        if len(bases_in_range) == 1:
            base = bases_in_range[0]
            return {
                "base": base,
                "distance": base.calculate_distance(target_lat, target_lng),
                "available_drones": BaseSelectionService.get_available_drone_count(
                    base
                ),
                "reason": "Only base in range",
            }

        # Multiple bases cover the area - apply strategy
        if strategy == "closest":
            return BaseSelectionService._select_closest_base(
                bases_in_range, target_lat, target_lng
            )
        elif strategy == "most_drones":
            return BaseSelectionService._select_base_with_most_drones(
                bases_in_range, target_lat, target_lng
            )
        elif strategy == "balanced":
            return BaseSelectionService._select_balanced_base(
                bases_in_range, target_lat, target_lng
            )
        else:
            # Default to closest
            return BaseSelectionService._select_closest_base(
                bases_in_range, target_lat, target_lng
            )

    @staticmethod
    def _select_closest_base(
        bases: List[DroneBase], target_lat: float, target_lng: float
    ) -> Dict:
        """Select the base closest to the target location."""
        best_base = None
        min_distance = float("inf")

        for base in bases:
            distance = base.calculate_distance(target_lat, target_lng)
            if distance < min_distance:
                min_distance = distance
                best_base = base

        return {
            "base": best_base,
            "distance": min_distance,
            "available_drones": BaseSelectionService.get_available_drone_count(
                best_base
            ),
            "reason": f"Closest base ({min_distance:.2f} km away)",
        }

    @staticmethod
    def _select_base_with_most_drones(
        bases: List[DroneBase], target_lat: float, target_lng: float
    ) -> Dict:
        """Select the base with the most available drones."""
        best_base = None
        max_drones = -1

        for base in bases:
            available = BaseSelectionService.get_available_drone_count(base)
            if available > max_drones:
                max_drones = available
                best_base = base

        return {
            "base": best_base,
            "distance": best_base.calculate_distance(target_lat, target_lng),
            "available_drones": max_drones,
            "reason": f"Most available drones ({max_drones} drones)",
        }

    @staticmethod
    def _select_balanced_base(
        bases: List[DroneBase], target_lat: float, target_lng: float
    ) -> Dict:
        """
        Select base using a balanced score considering both distance and available drones.
        Score = (normalized_distance * 0.6) + (normalized_drone_availability * 0.4)
        Lower score is better.
        """
        base_scores = []

        # Calculate distances and drone counts
        for base in bases:
            distance = base.calculate_distance(target_lat, target_lng)
            available = BaseSelectionService.get_available_drone_count(base)
            base_scores.append(
                {"base": base, "distance": distance, "available_drones": available}
            )

        # Normalize and calculate scores
        max_distance = max(b["distance"] for b in base_scores)
        max_drones = max(b["available_drones"] for b in base_scores)

        # Avoid division by zero
        if max_distance == 0:
            max_distance = 1
        if max_drones == 0:
            max_drones = 1

        best_base_info = None
        best_score = float("inf")

        for info in base_scores:
            # Normalize distance (0-1, lower is better)
            norm_distance = info["distance"] / max_distance

            # Normalize drones (0-1, higher is better, so invert)
            norm_drones = 1 - (info["available_drones"] / max_drones)

            # Calculate weighted score (lower is better)
            score = (norm_distance * 0.6) + (norm_drones * 0.4)

            if score < best_score:
                best_score = score
                best_base_info = info

        return {
            "base": best_base_info["base"],
            "distance": best_base_info["distance"],
            "available_drones": best_base_info["available_drones"],
            "reason": f"Balanced (distance: {best_base_info['distance']:.2f}km, drones: {best_base_info['available_drones']})",
        }

    @staticmethod
    def get_base_coverage_info() -> List[Dict]:
        """
        Get coverage information for all active bases.

        Returns:
            List of dicts with base info and coverage stats
        """
        bases = DroneBase.objects(status="active")
        coverage_info = []

        for base in bases:
            coverage_info.append(
                {
                    "base_id": base.base_id,
                    "name": base.name,
                    "location": {"lat": base.lat, "lng": base.lng},
                    "operational_radius": base.operational_radius,
                    "available_drones": BaseSelectionService.get_available_drone_count(
                        base
                    ),
                    "total_drones": Drone.objects(assigned_site=base.name).count(),
                }
            )

        return coverage_info
