import math
import time
import os
from collections import deque
from planet_intel import PlanetIntel
from rover import Rover

'''
Used gen ai to generate functions, classes, and animations

Visited set
uses a queue to store the neighboring unvisitied coordinates from the visiited set to prioritize
being visited
'''
class AnimatedMarsMapper:
    def __init__(self, animation_delay=0.3):
        self.directions = ['N', 'E', 'S', 'W']
        self.opposite_dir = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}
        self.dir_offsets = {'N': (0, -1), 'S': (0, 1), 'E': (1, 0), 'W': (-1, 0)}
        self.animation_delay = animation_delay
        self.rover_marker = 'R'
        self.max_battery = 20  # Default max battery
        self.current_battery = self.max_battery
        self.infinite_battery = False

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_battery_bar(self):
        """Displays a visual battery level indicator"""
        if self.infinite_battery:
            return "\033[94m[∞∞∞∞∞∞∞∞∞∞∞∞∞∞∞∞∞∞∞∞]\033[0m"  # Blue infinity battery bar
            
        bar_width = 20
        filled_blocks = int((self.current_battery / self.max_battery) * bar_width)
        empty_blocks = bar_width - filled_blocks
        
        # Color coding based on battery level
        if self.current_battery > 15:
            color = '\033[92m'  # Green
        elif self.current_battery > 5:
            color = '\033[93m'  # Yellow
        else:
            color = '\033[91m'  # Red
        
        reset = '\033[0m'
        battery_bar = f"{color}[{'█' * filled_blocks}{' ' * empty_blocks}]{reset}"
        return battery_bar

    def display_animated_map(self, coord_map, rover_pos):
        self.clear_screen()
        if not coord_map:
            print("No map data available")
            return

        all_x = [x for x, y in coord_map.keys()]
        all_y = [y for x, y in coord_map.keys()]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)

        # Display battery level with a visual bar
        battery_bar = self.display_battery_bar()
        if self.infinite_battery:
            print(f"Battery: INF {battery_bar}")
        else:
            print(f"Battery: {self.current_battery}/{self.max_battery} {battery_bar}")
        print(f"Position: {rover_pos}")
        
        border = '+' + '-' * (2 * (max_x - min_x + 1) - 1) + '+'
        print(border)

        for y in range(min_y, max_y + 1):
            row = []
            for x in range(min_x, max_x + 1):
                if (x, y) == rover_pos:
                    row.append(self.rover_marker)
                else:
                    row.append(coord_map.get((x, y), '?'))
            print('|' + ' '.join(row) + '|')

        print(border)
        time.sleep(self.animation_delay)

    def simulate_recharging(self):
        """Simulates the rover recharging with animation"""
        self.clear_screen()
        print("\nRecharging battery...\n")
        
        for i in range(1, 11):
            self.current_battery = i * (self.max_battery / 10)
            battery_bar = self.display_battery_bar()
            print(f"\rRecharging: {self.current_battery:.1f}/{self.max_battery} {battery_bar}", end="")
            time.sleep(0.2)
            
        print("\n\nBattery fully recharged!")
        time.sleep(1)
        self.current_battery = self.max_battery

    def map_surface(self, planet):
        rover = Rover(planet, battery_life=math.inf)
        self.current_battery = rover.get_battery_life()
        self.infinite_battery = True
       
        coord_map = {(0, 0): 'H'}
        visited = set([(0, 0)])
        frontier = deque([(0, 0)])
        current_pos = (0, 0)
       
        self.display_animated_map(coord_map, current_pos)

        while frontier:
            x, y = frontier.popleft()

            if (x, y) != current_pos:
                path = self._find_path(coord_map, current_pos, (x, y))
                if path:
                    for direction in path:
                        rover.move(direction)
                        current_pos = self._update_position(current_pos, direction)
                        self.display_animated_map(coord_map, current_pos)

            for direction in self.directions:
                dx, dy = self.dir_offsets[direction]
                new_pos = (x + dx, y + dy)

                if new_pos not in visited:
                    success, reason = rover.move(direction)
                   
                    if success:
                        terrain = rover.get_current_location()
                        coord_map[new_pos] = terrain
                        visited.add(new_pos)
                        frontier.append(new_pos)
                        current_pos = new_pos
                        self.display_animated_map(coord_map, current_pos)
                       
                        rover.move(self.opposite_dir[direction])
                        current_pos = (x, y)
                        self.display_animated_map(coord_map, current_pos)
                    elif reason == "Obstructed Space":
                        coord_map[new_pos] = 'X'
                        visited.add(new_pos)
                        self.display_animated_map(coord_map, current_pos)

        return self._convert_to_grid(coord_map)

    def map_surface_with_battery_constraint(self, planet):
        rover = Rover(planet, battery_life=20)
        self.max_battery = 20
        self.current_battery = 20
        self.infinite_battery = False
        
        coord_map = {(0, 0): 'H'}
        visited = set([(0, 0)])
        queue = deque()
        queue.append((0, 0, []))
        current_pos = (0, 0)
        
        # Display initial state
        self.display_animated_map(coord_map, current_pos)
       
        while queue:
            x, y, path = queue.popleft()
            d = len(path)
            
            # Check if we have enough battery to go and return
            if 2 * d > self.current_battery:
                continue

            # Follow path to the target position
            current_pos = (0, 0)  # Reset position for visualization
            self.display_animated_map(coord_map, current_pos)
            
            path_success = True
            for direction in path:
                success, _ = rover.move(direction)
                if not success:
                    path_success = False
                    break
                    
                # Update battery and position for visualization
                self.current_battery = rover.get_battery_life()
                current_pos = self._update_position(current_pos, direction)
                self.display_animated_map(coord_map, current_pos)
                
            if not path_success or (rover.get_current_location() != coord_map.get((x, y), '?')):
                # If path failed, go back to home
                reverse_path = [self.opposite_dir[d] for d in reversed(path)]
                for move_dir in reverse_path:
                    rover.move(move_dir)
                    self.current_battery = rover.get_battery_life()
                    current_pos = self._update_position(current_pos, move_dir)
                    self.display_animated_map(coord_map, current_pos)
                continue

            # Store current battery level
            self.current_battery = rover.get_battery_life()
            k_max = min(4, self.current_battery // 2)  # Maximum directions to explore based on battery
            directions_explored = 0

            for direction in self.directions:
                if directions_explored >= k_max:
                    break

                dx, dy = self.dir_offsets[direction]
                new_x, new_y = x + dx, y + dy
                new_pos = (new_x, new_y)
                
                if new_pos in coord_map:
                    continue

                success, reason = rover.move(direction)
                if success:
                    # Update battery and position for visualization
                    self.current_battery = rover.get_battery_life()
                    current_pos = self._update_position(current_pos, direction)
                    self.display_animated_map(coord_map, current_pos)
                    
                    terrain = rover.get_current_location()
                    coord_map[new_pos] = terrain
                    
                    rover.move(self.opposite_dir[direction])
                    self.current_battery = rover.get_battery_life()
                    current_pos = (x, y)
                    self.display_animated_map(coord_map, current_pos)
                    
                    directions_explored += 1
                    
                    if new_pos not in visited:
                        new_path = path + [direction]
                        queue.append((new_x, new_y, new_path))
                        visited.add(new_pos)
                        
                elif reason == "Obstructed Space":
                    coord_map[new_pos] = 'X'
                    self.display_animated_map(coord_map, current_pos)

            # Return to home base
            reverse_path = [self.opposite_dir[d] for d in reversed(path)]
            for move_dir in reverse_path:
                rover.move(move_dir)
                self.current_battery = rover.get_battery_life()
                current_pos = self._update_position(current_pos, move_dir)
                self.display_animated_map(coord_map, current_pos)
            
            # When back at home, recharge the battery
            if current_pos == (0, 0) and self.current_battery < self.max_battery:
                self.simulate_recharging()
                # Instead of calling rover.recharge(), we'll create a new rover instance
                # This is a workaround since the Rover class doesn't have a recharge method
                rover = Rover(planet, battery_life=20)
                self.current_battery = rover.get_battery_life()
                self.display_animated_map(coord_map, current_pos)

        return self._convert_to_grid(coord_map)

    def _update_position(self, current_pos, direction):
        x, y = current_pos
        dx, dy = self.dir_offsets[direction]
        return (x + dx, y + dy)

    def _find_path(self, coord_map, start, end):
        if start == end:
            return []

        queue = deque([(start, [])])
        visited = set([start])

        while queue:
            (x, y), path = queue.popleft()

            for direction, (dx, dy) in self.dir_offsets.items():
                new_pos = (x + dx, y + dy)

                if new_pos == end:
                    return path + [direction]

                if (new_pos in coord_map and
                    coord_map[new_pos] not in ['X'] and
                    new_pos not in visited):
                    visited.add(new_pos)
                    queue.append((new_pos, path + [direction]))

        return None

    def _convert_to_grid(self, coord_map):
        if not coord_map:
            return [['?']]

        all_x = [x for x, y in coord_map.keys()]
        all_y = [y for x, y in coord_map.keys()]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)

        grid = []
        for y in range(min_y, max_y + 1):
            row = []
            for x in range(min_x, max_x + 1):
                row.append(coord_map.get((x, y), '?'))
            grid.append(row)

        return grid

    def save_map(self, grid_map, filename):
        with open(filename, 'w') as f:
            for row in grid_map:
                f.write(''.join(row) + '\n')

def main():
    mapper = AnimatedMarsMapper(animation_delay=0.2)

    planets = {
        'planet_1': PlanetIntel.get_planet_1(),
        'planet_2': PlanetIntel.get_planet_2(),
        'planet_3': PlanetIntel.get_planet_3()
    }

    for name, planet in planets.items():
        print(f"\nMapping {name} with unlimited battery...")
        try:
            planet_map = mapper.map_surface(planet)
            mapper.save_map(planet_map, f"{name}_unlimited.txt")
            print(f"Saved to {name}_unlimited.txt")
        except KeyboardInterrupt:
            print("Skipped unlimited mapping.")

        print(f"\nMapping {name} with battery constraint...")
        try:
            constrained_map = mapper.map_surface_with_battery_constraint(planet)
            mapper.save_map(constrained_map, f"{name}_battery.txt")
            print(f"Saved to {name}_battery.txt")
        except KeyboardInterrupt:
            print("Skipped battery-constrained mapping.")

if __name__ == "__main__":
    main()
