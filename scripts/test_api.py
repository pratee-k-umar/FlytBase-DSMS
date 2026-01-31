"""
API Test Script
Automated testing of all DSMS API endpoints.
Run with: python scripts/test_api.py (with server running on localhost:8000)
"""
import requests
import json
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"


def print_header(text):
    """Print a styled header"""
    print(f"\n{Fore.CYAN}{'=' * 60}")
    print(f"{Fore.CYAN}{text}")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")


def print_success(text):
    """Print success message"""
    print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")


def print_error(text):
    """Print error message"""
    print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")


def print_info(text):
    """Print info message"""
    print(f"{Fore.YELLOW}ℹ {text}{Style.RESET_ALL}")


def test_endpoint(method, endpoint, expected_status=200, data=None, description="", use_api_base=True):
    """Test a single API endpoint"""
    base = API_BASE if use_api_base else BASE_URL
    url = f"{base}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PATCH":
            response = requests.patch(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            print_error(f"Unknown method: {method}")
            return False
        
        # Check status code
        if response.status_code == expected_status:
            print_success(f"{method} {endpoint} - {description}")
            # Some endpoints (e.g., DELETE 204) intentionally return no body.
            return response.json() if response.content else True
        else:
            print_error(f"{method} {endpoint} - Expected {expected_status}, got {response.status_code}")
            if response.content:
                print(f"  Response: {response.text[:200]}")
            return None
            
    except requests.exceptions.ConnectionError:
        print_error(f"{method} {endpoint} - Connection failed (is server running?)")
        return None
    except Exception as e:
        print_error(f"{method} {endpoint} - {str(e)}")
        return None


def main():
    print_header("DSMS API Automated Tests")
    
    # Track results
    total_tests = 0
    passed_tests = 0
    
    # Test 1: Health Check
    print_header("1. Health Check")
    total_tests += 1
    # Health is not under /api/
    result = test_endpoint("GET", "/health/", 200, description="Server health check", use_api_base=False)
    if result:
        passed_tests += 1
        print_info(f"Response: {json.dumps(result, indent=2)}")
    
    # Test 2: List Drones
    print_header("2. Fleet Endpoints")
    total_tests += 1
    drones = test_endpoint("GET", "/fleet/drones/", 200, description="List all drones")
    if drones:
        passed_tests += 1
        print_info(f"Found {len(drones.get('data', []))} drones")
        if drones.get('data'):
            first_drone = drones['data'][0]
            print_info(f"First drone: {first_drone.get('drone_id')} - {first_drone.get('name')}")
    
    # Test 3: Get Drone Details
    if drones and drones.get('data'):
        total_tests += 1
        drone_id = drones['data'][0]['drone_id']
        drone = test_endpoint("GET", f"/fleet/drones/{drone_id}/", 200, description=f"Get drone {drone_id}")
        if drone:
            passed_tests += 1
    
    # Test 4: Fleet Stats
    total_tests += 1
    stats = test_endpoint("GET", "/fleet/stats", 200, description="Get fleet statistics")
    if stats:
        passed_tests += 1
        print_info(f"Fleet stats: {json.dumps(stats.get('data', {}), indent=2)}")
    
    # Test 5: List Missions
    print_header("3. Mission Endpoints")
    total_tests += 1
    missions = test_endpoint("GET", "/missions/", 200, description="List all missions")
    if missions:
        passed_tests += 1
        print_info(f"Found {len(missions.get('data', []))} missions")
        if missions.get('data'):
            first_mission = missions['data'][0]
            print_info(f"First mission: {first_mission.get('mission_id')} - {first_mission.get('name')}")
    
    # Test 6: Get Mission Details
    if missions and missions.get('data'):
        total_tests += 1
        mission_id = missions['data'][0]['mission_id']
        mission = test_endpoint("GET", f"/missions/{mission_id}/", 200, description=f"Get mission {mission_id}")
        if mission:
            passed_tests += 1
            print_info(f"Mission has {len(mission.get('data', {}).get('flight_path', {}).get('waypoints', []))} waypoints")
    
    # Test 7: Create Mission
    total_tests += 1
    new_mission_data = {
        "name": "API Test Mission",
        "description": "Created by automated test",
        "site_name": "Test Site",
        "survey_type": "mapping",
        "coverage_area": {
            "type": "Polygon",
            "coordinates": [[
                [-122.4200, 37.7740],
                [-122.4180, 37.7740],
                [-122.4180, 37.7760],
                [-122.4200, 37.7760],
                [-122.4200, 37.7740],
            ]]
        },
        "altitude": 50.0,
        "speed": 5.0,
        "assigned_drone_id": drones['data'][0]['drone_id'] if drones and drones.get('data') else None
    }
    created_mission = test_endpoint("POST", "/missions/", 201, data=new_mission_data, description="Create new mission")
    if created_mission:
        passed_tests += 1
        created_mission_id = created_mission.get('data', {}).get('mission_id')
        print_info(f"Created mission: {created_mission_id}")
    
    # Test 8: Analytics
    print_header("4. Analytics Endpoints")
    total_tests += 1
    analytics = test_endpoint("GET", "/analytics/summary", 200, description="Get analytics summary")
    if analytics:
        passed_tests += 1
        print_info(f"Analytics: {json.dumps(analytics.get('data', {}), indent=2)}")
    
    # Test 9: Update Mission (if we created one)
    if created_mission and created_mission.get('data'):
        total_tests += 1
        mission_id = created_mission['data']['mission_id']
        update_data = {"description": "Updated by automated test"}
        updated = test_endpoint("PATCH", f"/missions/{mission_id}/", 200, data=update_data, description=f"Update mission {mission_id}")
        if updated:
            passed_tests += 1
    
    # Test 10: Delete Mission (cleanup)
    if created_mission and created_mission.get('data'):
        total_tests += 1
        mission_id = created_mission['data']['mission_id']
        deleted = test_endpoint("DELETE", f"/missions/{mission_id}/", 204, description=f"Delete mission {mission_id}")
        if deleted:
            passed_tests += 1
    
    # Print Summary
    print_header("Test Summary")
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\nTotal Tests: {total_tests}")
    print_success(f"Passed: {passed_tests}")
    print_error(f"Failed: {total_tests - passed_tests}")
    print(f"\nPass Rate: {Fore.CYAN}{pass_rate:.1f}%{Style.RESET_ALL}")
    
    if passed_tests == total_tests:
        print(f"\n{Fore.GREEN}{'=' * 60}")
        print(f"{Fore.GREEN} All tests passed! Your API is working correctly!")
        print(f"{Fore.GREEN}{'=' * 60}{Style.RESET_ALL}\n")
    else:
        print(f"\n{Fore.YELLOW}{'=' * 60}")
        print(f"{Fore.YELLOW} Some tests failed. Please check the server logs.")
        print(f"{Fore.YELLOW}{'=' * 60}{Style.RESET_ALL}\n")


if __name__ == '__main__':
    main()
