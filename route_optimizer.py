"""
Route Optimizer - Smart Waste Collection Route Planning
Uses Haversine distance + Nearest Neighbor algorithm to find optimal pickup routes.

Can be run standalone for testing:
    python route_optimizer.py
"""

import math
import random as rnd
from bin_simulator import load_bins, get_bins_for_pickup, get_priority_emoji, DEPOT


# --- Distance Calculation ---
def haversine(lat1, lng1, lat2, lng2):
    """
    Calculate distance (km) between two lat/lng points using Haversine formula.
    """
    R = 6371  # Earth radius in km

    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)

    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lng / 2) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def distance_between(point_a, point_b):
    """Distance in km between two location dicts with 'lat' and 'lng' keys."""
    return haversine(point_a['lat'], point_a['lng'], point_b['lat'], point_b['lng'])


# --- Nearest Neighbor Algorithm ---
def nearest_neighbor_route(bins, depot):
    """
    Compute an optimized route using the Nearest Neighbor heuristic:
    1. Start at depot
    2. Visit the closest unvisited bin
    3. Repeat until all bins visited
    4. Return to depot
    """
    if not bins:
        return {
            'route': [],
            'total_distance_km': 0,
            'bins_collected': 0,
            'estimated_time_min': 0,
            'depot': depot,
            'route_coordinates': [],
        }

    unvisited = list(bins)
    route = []
    total_distance = 0
    current = depot

    while unvisited:
        # Find nearest unvisited bin
        nearest = min(unvisited, key=lambda b: distance_between(current, b))
        dist = distance_between(current, nearest)

        route.append({
            'stop': len(route) + 1,
            'bin_id': nearest['bin_id'],
            'area': nearest['area'],
            'lat': nearest['lat'],
            'lng': nearest['lng'],
            'fill_level': nearest['fill_level'],
            'priority': nearest['priority'],
            'waste_type': nearest['waste_type'],
            'distance_from_prev_km': round(dist, 2),
        })

        total_distance += dist
        current = nearest
        unvisited.remove(nearest)

    # Return to depot
    return_dist = distance_between(current, depot)
    total_distance += return_dist

    # Estimated time: avg 20 km/h in city + 3 min per bin for collection
    travel_time = (total_distance / 20) * 60  # minutes
    collection_time = len(route) * 3  # 3 min per bin
    total_time = travel_time + collection_time

    # Build coordinate list for map polyline
    coords = [[depot['lat'], depot['lng']]]
    for stop in route:
        coords.append([stop['lat'], stop['lng']])
    coords.append([depot['lat'], depot['lng']])  # return to depot

    return {
        'route': route,
        'total_distance_km': round(total_distance, 2),
        'return_distance_km': round(return_dist, 2),
        'bins_collected': len(route),
        'estimated_time_min': round(total_time),
        'depot': depot,
        'route_coordinates': coords,
    }


# --- Main Optimization Function ---
def optimize_route(depot=None):
    """
    Full optimization pipeline:
    1. Load bins needing pickup (HIGH + MEDIUM priority)
    2. Run Nearest Neighbor algorithm
    3. Return optimized route
    """
    if depot is None:
        depot = DEPOT

    pickup_bins = get_bins_for_pickup()

    # Sort HIGH priority first for display
    pickup_bins.sort(key=lambda b: 0 if b['priority'] == 'HIGH' else 1)

    result = nearest_neighbor_route(pickup_bins, depot)
    result['high_priority_count'] = sum(1 for b in pickup_bins if b['priority'] == 'HIGH')
    result['medium_priority_count'] = sum(1 for b in pickup_bins if b['priority'] == 'MEDIUM')

    # Fuel savings estimate (vs random route)
    if result['bins_collected'] > 1:
        random_distances = []
        for _ in range(100):
            shuffled = list(pickup_bins)
            rnd.shuffle(shuffled)
            total = 0
            curr = depot
            for b in shuffled:
                total += distance_between(curr, b)
                curr = b
            total += distance_between(curr, depot)
            random_distances.append(total)

        avg_random = sum(random_distances) / len(random_distances)
        savings = max(0, round((1 - result['total_distance_km'] / avg_random) * 100, 1))
        result['fuel_savings_pct'] = savings
    else:
        result['fuel_savings_pct'] = 0

    return result


# --- Standalone CLI ---
if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  Route Optimizer - Smart Waste Collection")
    print("=" * 60)

    result = optimize_route()

    print("\n  Depot: {}".format(result['depot']['area']))
    print("  Bins to collect: {}".format(result['bins_collected']))
    print("     HIGH: {}".format(result['high_priority_count']))
    print("     MEDIUM: {}".format(result['medium_priority_count']))

    if result['route']:
        print("\n  " + "-" * 55)
        print("  {:>3}  {:8}  {:25}  {:>5}  {:>6}".format('#', 'Bin', 'Area', 'Fill', 'Dist'))
        print("  " + "-" * 55)

        for stop in result['route']:
            emoji = get_priority_emoji(stop['priority'])
            print("  {:3d}  {:8}  {:25}  {:4d}%  {:5.1f}km  {}".format(
                stop['stop'], stop['bin_id'], stop['area'],
                stop['fill_level'], stop['distance_from_prev_km'], emoji))

        print("  " + "-" * 55)
        print("\n  Total Distance:    {} km".format(result['total_distance_km']))
        print("  Estimated Time:    {} min".format(result['estimated_time_min']))
        print("  Fuel Savings:      ~{}% vs random".format(result['fuel_savings_pct']))

        route_str = "  {} {}".format("Depot:", result['depot']['area'])
        for stop in result['route']:
            route_str += " -> {}".format(stop['area'])
        route_str += " -> Depot"
        print("\n  Route: " + route_str)
    else:
        print("\n  No bins need pickup right now!")

    print("\n  Done!\n")
