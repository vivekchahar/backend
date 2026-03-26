"""
Main Simulation - Standalone Demo Script
Demonstrates the complete Smart Waste Collection pipeline:

    Simulated Bins -> Filter Full Bins -> Optimize Route -> Display Results

Run this file directly:
    python main_simulation.py
"""

from bin_simulator import initialize_bins, simulate_tick, get_bins_for_pickup, get_bin_stats, get_priority_emoji, DEPOT
from route_optimizer import optimize_route, distance_between


def print_header(text):
    print("\n" + "=" * 65)
    print("  " + text)
    print("=" * 65)


def print_section(text):
    print("\n  --- {} ---\n".format(text))


def main():
    # ===========================
    # STEP 1: Initialize Bins
    # ===========================
    print_header("AI-Driven Circular Waste Intelligence System")
    print("  Smart Waste Collection + Route Optimization (Delhi)")
    print("=" * 65)

    print_section("STEP 1: Initializing 20 Smart Bins across Delhi")

    bins = initialize_bins()
    stats = get_bin_stats()

    for b in bins:
        emoji = get_priority_emoji(b['priority'])
        bar_filled = b['fill_level'] // 5
        bar = '#' * bar_filled + '-' * (20 - bar_filled)
        print("  {} {}  {:25s}  [{}] {:3d}%  {}".format(
            emoji, b['bin_id'], b['area'], bar, b['fill_level'],
            b['waste_type'].replace('_', ' ')))

    print("\n  Total: {} bins  |  Avg fill: {}%".format(stats['total_bins'], stats['avg_fill_level']))
    print("  HIGH: {}  |  MEDIUM: {}  |  LOW: {}".format(
        stats['priority_counts']['HIGH'],
        stats['priority_counts']['MEDIUM'],
        stats['priority_counts']['LOW']))

    # ===========================
    # STEP 2: Simulate IoT Ticks
    # ===========================
    print_section("STEP 2: Simulating IoT Sensor Updates (3 ticks)")

    for tick in range(3):
        bins = simulate_tick()
        stats = get_bin_stats()
        print("  Tick {}: Avg fill = {:5.1f}%  |  HIGH: {:2d}  MEDIUM: {:2d}  LOW: {:2d}".format(
            tick + 1, stats['avg_fill_level'],
            stats['priority_counts']['HIGH'],
            stats['priority_counts']['MEDIUM'],
            stats['priority_counts']['LOW']))

    # ===========================
    # STEP 3: Select Bins for Pickup
    # ===========================
    print_section("STEP 3: Selecting Bins for Pickup (fill > 70%)")

    pickup_bins = get_bins_for_pickup()
    high_bins = [b for b in pickup_bins if b['priority'] == 'HIGH']
    medium_bins = [b for b in pickup_bins if b['priority'] == 'MEDIUM']

    print("  Bins needing pickup: {} / {}".format(len(pickup_bins), stats['total_bins']))
    print("    HIGH priority:   {}".format(len(high_bins)))
    print("    MEDIUM priority: {}".format(len(medium_bins)))

    if pickup_bins:
        print()
        for b in pickup_bins:
            emoji = get_priority_emoji(b['priority'])
            print("  {} {}  {:25s}  {:3d}%  {}".format(
                emoji, b['bin_id'], b['area'], b['fill_level'],
                b['waste_type'].replace('_', ' ')))

    # ===========================
    # STEP 4: Optimize Route
    # ===========================
    print_section("STEP 4: Computing Optimized Collection Route")

    result = optimize_route()

    print("  Depot: {} ({}, {})".format(
        result['depot']['area'], result['depot']['lat'], result['depot']['lng']))
    print("  Algorithm: Nearest Neighbor (Greedy TSP)")
    print("  Distance: Haversine formula")

    if result['route']:
        print("\n  {:-<60}".format(''))
        print("  {:>3}  {:8}  {:25}  {:>5}  {:>7}".format('#', 'Bin', 'Area', 'Fill', 'Dist'))
        print("  {:-<60}".format(''))

        for stop in result['route']:
            emoji = get_priority_emoji(stop['priority'])
            print("  {:3d}  {:8}  {:25}  {:3d}%  {:5.1f}km  {}".format(
                stop['stop'], stop['bin_id'], stop['area'],
                stop['fill_level'], stop['distance_from_prev_km'], emoji))

        print("  {:-<60}".format(''))

        # ===========================
        # STEP 5: Results Summary
        # ===========================
        print_section("STEP 5: Collection Summary")

        print("  Bins collected:     {}".format(result['bins_collected']))
        print("    HIGH:             {}".format(result['high_priority_count']))
        print("    MEDIUM:           {}".format(result['medium_priority_count']))
        print("  Total distance:     {} km".format(result['total_distance_km']))
        print("  Return to depot:    {} km".format(result['return_distance_km']))
        print("  Estimated time:     {} minutes".format(result['estimated_time_min']))
        print("  Fuel savings:       ~{}% vs random route".format(result['fuel_savings_pct']))

        # Route sequence
        print_section("Optimized Route Sequence")
        route_str = "  [Depot] {}".format(result['depot']['area'])
        for stop in result['route']:
            route_str += "\n    -> {}. {} ({}, {}%)".format(
                stop['stop'], stop['area'], stop['waste_type'].replace('_', ' '), stop['fill_level'])
        route_str += "\n    -> [Depot] {}".format(result['depot']['area'])
        print(route_str)

        # Fuel saving explanation
        print_section("Fuel & Cost Savings Explanation")
        print("  The Nearest Neighbor algorithm visits the closest")
        print("  unvisited bin at each step, reducing total travel")
        print("  distance compared to random or fixed routes.")
        print()
        print("  Key savings factors:")
        print("    1. Only HIGH + MEDIUM bins collected (skip LOW)")
        print("    2. Route is distance-optimized (not random)")
        print("    3. Haversine gives real-world accuracy")
        print()
        skipped = stats['total_bins'] - result['bins_collected']
        print("  Skipped {} LOW-priority bins = fewer stops".format(skipped))
        print("  Estimated ~{}% fuel savings vs unoptimized".format(result['fuel_savings_pct']))

    else:
        print("\n  All bins are under 40% fill. No pickup needed!")

    print_header("Simulation Complete!")
    print("  Run 'python app.py' for the full web interface")
    print("  Visit http://127.0.0.1:5000/bins for the Smart Bins dashboard")
    print("=" * 65 + "\n")


if __name__ == '__main__':
    main()
