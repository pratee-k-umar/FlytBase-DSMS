/**
 * Geographic utilities for frontend
 */

/**
 * Normalize longitude to -180 to 180 range.
 * Fixes issues from Leaflet map wrapping where coordinates can be
 * outside the normal range (e.g., -282 instead of 77).
 */
export function normalizeLongitude(lng: number): number {
  while (lng > 180) {
    lng -= 360;
  }
  while (lng < -180) {
    lng += 360;
  }
  return lng;
}

/**
 * Normalize a [lat, lng] coordinate pair for Leaflet.
 */
export function normalizeLatLng(
  coord: [number, number],
): [number, number] {
  return [coord[0], normalizeLongitude(coord[1])];
}

/**
 * Normalize an array of [lat, lng] coordinates.
 */
export function normalizeCoordinates(
  coords: [number, number][],
): [number, number][] {
  return coords.map(normalizeLatLng);
}

/**
 * Extract survey-only waypoints from a flight path.
 * Survey waypoints are those between the travel phase and return phase.
 * Excludes: action='fly' at start (travel), action='return' or 'land' at end (RTB)
 */
export function extractSurveyWaypoints(
  waypoints: Array<{ lat: number; lng: number; action?: string }>,
): [number, number][] {
  // Find the first non-fly waypoint (start of survey)
  let surveyStartIndex = 0;
  for (let i = 0; i < waypoints.length; i++) {
    if (waypoints[i].action !== "fly") {
      surveyStartIndex = i;
      break;
    }
  }

  // Find the first return/land waypoint (end of survey)
  let surveyEndIndex = waypoints.length;
  for (let i = surveyStartIndex; i < waypoints.length; i++) {
    if (waypoints[i].action === "return" || waypoints[i].action === "land") {
      surveyEndIndex = i;
      break;
    }
  }

  // Extract survey waypoints and normalize
  return waypoints
    .slice(surveyStartIndex, surveyEndIndex)
    .map((wp) => normalizeLatLng([wp.lat, normalizeLongitude(wp.lng)]));
}
