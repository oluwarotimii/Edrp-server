import math
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class Coordinate:
    """Represents a geographic coordinate"""
    latitude: float
    longitude: float
    
    def __post_init__(self):
        """Validate coordinate values"""
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"Invalid latitude: {self.latitude}. Must be between -90 and 90")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"Invalid longitude: {self.longitude}. Must be between -180 and 180")

def calculate_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    unit: str = "meters"
) -> float:
    """
    Calculate the distance between two geographic coordinates using the Haversine formula.
    
    Args:
        lat1: Latitude of first point in decimal degrees
        lon1: Longitude of first point in decimal degrees
        lat2: Latitude of second point in decimal degrees
        lon2: Longitude of second point in decimal degrees
        unit: Unit of measurement ("meters", "kilometers", "miles", "feet")
    
    Returns:
        Distance between the two points in the specified unit
    """
    
    # Validate coordinates
    Coordinate(lat1, lon1)
    Coordinate(lat2, lon2)
    
    # Convert decimal degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
    
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth's radius in different units
    earth_radius = {
        "meters": 6371000,
        "kilometers": 6371,
        "miles": 3959,
        "feet": 20902231
    }
    
    if unit not in earth_radius:
        raise ValueError(f"Invalid unit: {unit}. Must be one of {list(earth_radius.keys())}")
    
    # Calculate distance
    distance = earth_radius[unit] * c
    
    return distance

def verify_location(
    current_lat: float,
    current_lon: float,
    target_lat: float,
    target_lon: float,
    tolerance_meters: float = 100.0
) -> bool:
    """
    Verify if current location is within tolerance of target location.
    
    Args:
        current_lat: Current latitude
        current_lon: Current longitude
        target_lat: Target latitude
        target_lon: Target longitude
        tolerance_meters: Acceptable distance in meters
    
    Returns:
        True if current location is within tolerance, False otherwise
    """
    
    try:
        distance = calculate_distance(
            current_lat, current_lon,
            target_lat, target_lon,
            unit="meters"
        )
        
        return distance <= tolerance_meters
        
    except ValueError:
        # Invalid coordinates
        return False

def get_location_verification_result(
    current_lat: float,
    current_lon: float,
    target_lat: float,
    target_lon: float,
    tolerance_meters: float = 100.0
) -> Dict[str, Any]:
    """
    Get detailed location verification result.
    
    Args:
        current_lat: Current latitude
        current_lon: Current longitude
        target_lat: Target latitude
        target_lon: Target longitude
        tolerance_meters: Acceptable distance in meters
    
    Returns:
        Dictionary with verification details
    """
    
    try:
        distance = calculate_distance(
            current_lat, current_lon,
            target_lat, target_lon,
            unit="meters"
        )
        
        is_valid = distance <= tolerance_meters
        
        return {
            "is_valid": is_valid,
            "distance_meters": round(distance, 2),
            "tolerance_meters": tolerance_meters,
            "accuracy": "high" if distance <= tolerance_meters / 2 else "medium" if is_valid else "low",
            "message": (
                "Location verified successfully" if is_valid 
                else f"Location is {round(distance - tolerance_meters, 2)}m outside allowed area"
            )
        }
        
    except ValueError as e:
        return {
            "is_valid": False,
            "distance_meters": None,
            "tolerance_meters": tolerance_meters,
            "accuracy": "invalid",
            "message": f"Invalid coordinates: {str(e)}"
        }

def calculate_bearing(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calculate the initial bearing from point 1 to point 2.
    
    Args:
        lat1: Latitude of first point in decimal degrees
        lon1: Longitude of first point in decimal degrees
        lat2: Latitude of second point in decimal degrees
        lon2: Longitude of second point in decimal degrees
    
    Returns:
        Bearing in degrees (0-360)
    """
    
    # Validate coordinates
    Coordinate(lat1, lon1)
    Coordinate(lat2, lon2)
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlon_rad = math.radians(lon2 - lon1)
    
    # Calculate bearing
    y = math.sin(dlon_rad) * math.cos(lat2_rad)
    x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
         math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad))
    
    bearing_rad = math.atan2(y, x)
    bearing_deg = math.degrees(bearing_rad)
    
    # Normalize to 0-360 degrees
    bearing_deg = (bearing_deg + 360) % 360
    
    return bearing_deg

def get_cardinal_direction(bearing: float) -> str:
    """
    Convert bearing to cardinal direction.
    
    Args:
        bearing: Bearing in degrees (0-360)
    
    Returns:
        Cardinal direction string
    """
    
    directions = [
        "N", "NNE", "NE", "ENE",
        "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW",
        "W", "WNW", "NW", "NNW"
    ]
    
    # Each direction covers 22.5 degrees
    index = int((bearing + 11.25) / 22.5) % 16
    
    return directions[index]

def calculate_midpoint(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> Tuple[float, float]:
    """
    Calculate the midpoint between two geographic coordinates.
    
    Args:
        lat1: Latitude of first point in decimal degrees
        lon1: Longitude of first point in decimal degrees
        lat2: Latitude of second point in decimal degrees
        lon2: Longitude of second point in decimal degrees
    
    Returns:
        Tuple of (latitude, longitude) for the midpoint
    """
    
    # Validate coordinates
    Coordinate(lat1, lon1)
    Coordinate(lat2, lon2)
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlon = lon2_rad - lon1_rad
    
    # Calculate midpoint
    bx = math.cos(lat2_rad) * math.cos(dlon)
    by = math.cos(lat2_rad) * math.sin(dlon)
    
    lat_mid = math.atan2(
        math.sin(lat1_rad) + math.sin(lat2_rad),
        math.sqrt((math.cos(lat1_rad) + bx) ** 2 + by ** 2)
    )
    
    lon_mid = lon1_rad + math.atan2(by, math.cos(lat1_rad) + bx)
    
    # Convert back to degrees
    lat_mid_deg = math.degrees(lat_mid)
    lon_mid_deg = math.degrees(lon_mid)
    
    return lat_mid_deg, lon_mid_deg

def is_point_in_circle(
    point_lat: float,
    point_lon: float,
    center_lat: float,
    center_lon: float,
    radius_meters: float
) -> bool:
    """
    Check if a point is within a circular area.
    
    Args:
        point_lat: Latitude of the point to check
        point_lon: Longitude of the point to check
        center_lat: Latitude of the circle center
        center_lon: Longitude of the circle center
        radius_meters: Radius of the circle in meters
    
    Returns:
        True if point is within the circle, False otherwise
    """
    
    return verify_location(
        point_lat, point_lon,
        center_lat, center_lon,
        radius_meters
    )

def is_point_in_polygon(
    point_lat: float,
    point_lon: float,
    polygon_coords: list
) -> bool:
    """
    Check if a point is within a polygon using the ray casting algorithm.
    
    Args:
        point_lat: Latitude of the point to check
        point_lon: Longitude of the point to check
        polygon_coords: List of (lat, lon) tuples defining the polygon vertices
    
    Returns:
        True if point is within the polygon, False otherwise
    """
    
    # Validate point coordinates
    Coordinate(point_lat, point_lon)
    
    # Validate polygon coordinates
    if len(polygon_coords) < 3:
        raise ValueError("Polygon must have at least 3 vertices")
    
    for lat, lon in polygon_coords:
        Coordinate(lat, lon)
    
    # Ray casting algorithm
    x, y = point_lon, point_lat
    n = len(polygon_coords)
    inside = False
    
    p1x, p1y = polygon_coords[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon_coords[i % n]
        
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        
        p1x, p1y = p2x, p2y
    
    return inside

def calculate_polygon_area(polygon_coords: list, unit: str = "square_meters") -> float:
    """
    Calculate the area of a polygon using the shoelace formula.
    
    Args:
        polygon_coords: List of (lat, lon) tuples defining the polygon vertices
        unit: Unit of measurement ("square_meters", "square_kilometers", "hectares", "acres")
    
    Returns:
        Area of the polygon in the specified unit
    """
    
    if len(polygon_coords) < 3:
        raise ValueError("Polygon must have at least 3 vertices")
    
    # Validate coordinates
    for lat, lon in polygon_coords:
        Coordinate(lat, lon)
    
    # Convert to approximate meters (this is simplified and may not be accurate for large areas)
    # For precise calculations, consider using a proper geographic projection
    
    # Earth's circumference at equator in meters
    earth_circumference = 40075017
    
    # Convert coordinates to approximate meters
    coords_m = []
    for lat, lon in polygon_coords:
        x = lon * earth_circumference / 360
        y = lat * earth_circumference / 360
        coords_m.append((x, y))
    
    # Shoelace formula
    n = len(coords_m)
    area = 0
    for i in range(n):
        j = (i + 1) % n
        area += coords_m[i][0] * coords_m[j][1]
        area -= coords_m[j][0] * coords_m[i][1]
    
    area = abs(area) / 2
    
    # Convert to requested unit
    conversions = {
        "square_meters": 1,
        "square_kilometers": 1e-6,
        "hectares": 1e-4,
        "acres": 2.47105e-4
    }
    
    if unit not in conversions:
        raise ValueError(f"Invalid unit: {unit}. Must be one of {list(conversions.keys())}")
    
    return area * conversions[unit]

def get_location_accuracy_description(accuracy_meters: float) -> Dict[str, str]:
    """
    Get a description of location accuracy.
    
    Args:
        accuracy_meters: GPS accuracy in meters
    
    Returns:
        Dictionary with accuracy level and description
    """
    
    if accuracy_meters <= 5:
        return {
            "level": "excellent",
            "description": "Very precise location (within 5 meters)",
            "color": "green"
        }
    elif accuracy_meters <= 10:
        return {
            "level": "good",
            "description": "Good location accuracy (within 10 meters)",
            "color": "light_green"
        }
    elif accuracy_meters <= 20:
        return {
            "level": "fair",
            "description": "Fair location accuracy (within 20 meters)",
            "color": "yellow"
        }
    elif accuracy_meters <= 50:
        return {
            "level": "poor",
            "description": "Poor location accuracy (within 50 meters)",
            "color": "orange"
        }
    else:
        return {
            "level": "very_poor",
            "description": f"Very poor location accuracy (within {accuracy_meters} meters)",
            "color": "red"
        }

class LocationService:
    """Service class for location-related operations"""
    
    @staticmethod
    def validate_attendance_location(
        user_lat: float,
        user_lon: float,
        school_locations: list,
        tolerance_meters: float = 100
    ) -> Dict[str, Any]:
        """
        Validate if user location is within any of the school's approved locations.
        
        Args:
            user_lat: User's current latitude
            user_lon: User's current longitude
            school_locations: List of approved school locations
            tolerance_meters: Tolerance in meters
        
        Returns:
            Validation result with details
        """
        
        results = []
        
        for location in school_locations:
            result = get_location_verification_result(
                user_lat, user_lon,
                location['latitude'], location['longitude'],
                location.get('radius_meters', tolerance_meters)
            )
            
            result['location_name'] = location.get('name', 'Unnamed Location')
            result['location_id'] = location.get('id')
            results.append(result)
        
        # Check if any location is valid
        valid_location = next((r for r in results if r['is_valid']), None)
        
        return {
            "is_valid": valid_location is not None,
            "matched_location": valid_location,
            "all_results": results,
            "closest_location": min(results, key=lambda x: x['distance_meters'] or float('inf'))
        }
    
    @staticmethod
    def get_movement_analysis(
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float
    ) -> Dict[str, Any]:
        """
        Analyze movement between two locations.
        
        Args:
            start_lat: Starting latitude
            start_lon: Starting longitude
            end_lat: Ending latitude
            end_lon: Ending longitude
        
        Returns:
            Movement analysis details
        """
        
        distance = calculate_distance(start_lat, start_lon, end_lat, end_lon)
        bearing = calculate_bearing(start_lat, start_lon, end_lat, end_lon)
        direction = get_cardinal_direction(bearing)
        
        return {
            "distance_meters": round(distance, 2),
            "distance_kilometers": round(distance / 1000, 3),
            "bearing_degrees": round(bearing, 1),
            "cardinal_direction": direction,
            "movement_type": (
                "no_movement" if distance < 5 else
                "minimal_movement" if distance < 50 else
                "local_movement" if distance < 500 else
                "significant_movement"
            )
        }
