import random
from collections import deque
from typing import List, Tuple, Set

class StealthDungeonGenerator:
    def __init__(self, width=50, height=50, seed=None):
        self.width = width
        self.height = height
        self.map = [[1 for _ in range(width)] for _ in range(height)]  # 1 = wall, 0 = empty
        if seed is not None:
            random.seed(seed)
    
    def generate(self):
        """Generate a stealth-focused dungeon with rooms and corridors"""
        # Create rooms
        rooms = self._create_rooms()
        
        # Connect rooms with corridors
        self._connect_rooms(rooms)
        
        # Add some additional corridors for multiple paths (good for stealth)
        self._add_extra_paths(rooms)
        
        # Ensure start and end are accessible
        self.map[1][1] = 0  # Start position
        self.map[48][48] = 0  # End position
        
        # Verify and fix connectivity
        if not self._is_connected(1, 1, 48, 48):
            self._ensure_path_to_end()
        
        # Add some strategic cover (small wall segments in larger spaces)
        self._add_cover_elements()
        
        # Ensure edges are walls
        self._ensure_border_walls()
        
        return self.map
    
    def _create_rooms(self) -> List[Tuple[int, int, int, int]]:
        """Create multiple rooms of varying sizes"""
        rooms = []
        num_rooms = random.randint(12, 18)  # More rooms
        attempts = 0
        max_attempts = 300  # More attempts to place rooms
        
        while len(rooms) < num_rooms and attempts < max_attempts:
            attempts += 1
            
            # Increased room sizes and variety
            room_type = random.random()
            if room_type < 0.15:  # 15% chance of extra large room
                w = random.randint(10, 14)
                h = random.randint(10, 14)
            elif room_type < 0.40:  # 25% chance of large room
                w = random.randint(7, 10)
                h = random.randint(7, 10)
            elif room_type < 0.70:  # 30% chance of medium room
                w = random.randint(5, 7)
                h = random.randint(5, 7)
            else:  # 30% chance of small room (good for stealth)
                w = random.randint(3, 5)
                h = random.randint(3, 5)
            
            x = random.randint(1, self.width - w - 1)
            y = random.randint(1, self.height - h - 1)
            
            # Reduced buffer for tighter packing (was x-1, y-1, w+2, h+2)
            if not self._room_overlaps(rooms, x-1, y-1, w+1, h+1):
                rooms.append((x, y, w, h))
                self._carve_room(x, y, w, h)
        
        # Try to fill gaps with smaller rooms
        for _ in range(50):  # Extra attempts to fill space
            w = random.randint(2, 4)
            h = random.randint(2, 4)
            x = random.randint(1, self.width - w - 1)
            y = random.randint(1, self.height - h - 1)
            
            if not self._room_overlaps(rooms, x, y, w, h):
                rooms.append((x, y, w, h))
                self._carve_room(x, y, w, h)
        
        return rooms
    
    def _room_overlaps(self, rooms: List[Tuple[int, int, int, int]], 
                       x: int, y: int, w: int, h: int) -> bool:
        """Check if a room overlaps with existing rooms"""
        for rx, ry, rw, rh in rooms:
            if not (x + w <= rx or x >= rx + rw or y + h <= ry or y >= ry + rh):
                return True
        return False
    
    def _carve_room(self, x: int, y: int, w: int, h: int):
        """Carve out a room in the map"""
        for i in range(y, y + h):
            for j in range(x, x + w):
                if 1 <= i < self.height - 1 and 1 <= j < self.width - 1:
                    self.map[i][j] = 0
    
    def _connect_rooms(self, rooms: List[Tuple[int, int, int, int]]):
        """Connect rooms with corridors using MST approach"""
        if len(rooms) < 2:
            return
        
        connected = [rooms[0]]
        unconnected = rooms[1:]
        
        while unconnected:
            # Find closest pair between connected and unconnected
            min_dist = float('inf')
            closest_pair = None
            
            for conn_room in connected:
                cx = conn_room[0] + conn_room[2] // 2
                cy = conn_room[1] + conn_room[3] // 2
                
                for i, unconn_room in enumerate(unconnected):
                    ux = unconn_room[0] + unconn_room[2] // 2
                    uy = unconn_room[1] + unconn_room[3] // 2
                    
                    dist = abs(cx - ux) + abs(cy - uy)
                    if dist < min_dist:
                        min_dist = dist
                        closest_pair = (conn_room, unconn_room, i)
            
            if closest_pair:
                room1, room2, idx = closest_pair
                self._create_corridor(room1, room2)
                connected.append(room2)
                unconnected.pop(idx)
    
    def _create_corridor(self, room1: Tuple[int, int, int, int], 
                        room2: Tuple[int, int, int, int]):
        """Create an L-shaped corridor between two rooms"""
        # Get center points of rooms
        x1 = room1[0] + room1[2] // 2
        y1 = room1[1] + room1[3] // 2
        x2 = room2[0] + room2[2] // 2
        y2 = room2[1] + room2[3] // 2
        
        # Randomly choose corridor width (1-2 for stealth gameplay)
        corridor_width = 1 if random.random() < 0.7 else 2
        
        # Randomly choose to go horizontal first or vertical first
        if random.random() < 0.5:
            self._carve_h_corridor(x1, x2, y1, corridor_width)
            self._carve_v_corridor(y1, y2, x2, corridor_width)
        else:
            self._carve_v_corridor(y1, y2, x1, corridor_width)
            self._carve_h_corridor(x1, x2, y2, corridor_width)
    
    def _carve_h_corridor(self, x1: int, x2: int, y: int, width: int):
        """Carve a horizontal corridor"""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for dy in range(width):
                if 1 <= y + dy < self.height - 1 and 1 <= x < self.width - 1:
                    self.map[y + dy][x] = 0
    
    def _carve_v_corridor(self, y1: int, y2: int, x: int, width: int):
        """Carve a vertical corridor"""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for dx in range(width):
                if 1 <= y < self.height - 1 and 1 <= x + dx < self.width - 1:
                    self.map[y][x + dx] = 0
    
    def _add_extra_paths(self, rooms: List[Tuple[int, int, int, int]]):
        """Add extra corridors for multiple paths (good for stealth)"""
        if len(rooms) < 3:
            return
        
        # Add more extra connections for better connectivity
        extra_connections = min(random.randint(3, 6), len(rooms) // 2)
        
        for _ in range(extra_connections):
            room1 = random.choice(rooms)
            room2 = random.choice(rooms)
            if room1 != room2:
                self._create_corridor(room1, room2)
    
    def _add_cover_elements(self):
        """Add small wall segments in larger open areas for cover"""
        for y in range(3, self.height - 3, 5):
            for x in range(3, self.width - 3, 5):
                # Check if area is mostly open
                open_count = sum(1 for dy in range(-2, 3) for dx in range(-2, 3)
                               if 0 <= y+dy < self.height and 0 <= x+dx < self.width
                               and self.map[y+dy][x+dx] == 0)
                
                # If area is very open, maybe add a small cover element
                if open_count > 20 and random.random() < 0.3:
                    # Add small L-shaped or straight cover
                    if random.random() < 0.5:
                        # Straight cover
                        if random.random() < 0.5:
                            for dx in range(2):
                                self.map[y][x + dx] = 1
                        else:
                            for dy in range(2):
                                self.map[y + dy][x] = 1
                    else:
                        # L-shaped cover
                        self.map[y][x] = 1
                        if random.random() < 0.5:
                            self.map[y][x + 1] = 1
                            self.map[y + 1][x] = 1
    
    def _is_connected(self, x1: int, y1: int, x2: int, y2: int) -> bool:
        """Check if two points are connected using BFS"""
        if self.map[y1][x1] == 1 or self.map[y2][x2] == 1:
            return False
        
        visited = set()
        queue = deque([(x1, y1)])
        visited.add((x1, y1))
        
        while queue:
            x, y = queue.popleft()
            
            if x == x2 and y == y2:
                return True
            
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if (0 <= nx < self.width and 0 <= ny < self.height and
                    (nx, ny) not in visited and self.map[ny][nx] == 0):
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        
        return False
    
    def _ensure_path_to_end(self):
        """Carve a direct path from start to end if not connected"""
        # Simple pathfinding from start to end
        x, y = 1, 1
        target_x, target_y = 48, 48
        
        while x != target_x or y != target_y:
            # Move towards target
            if x < target_x and random.random() < 0.7:
                x += 1
            elif y < target_y:
                y += 1
            elif x < target_x:
                x += 1
            
            # Carve path
            if 1 <= x < self.width - 1 and 1 <= y < self.height - 1:
                self.map[y][x] = 0
                # Make path slightly wider sometimes
                if random.random() < 0.3:
                    if x + 1 < self.width - 1:
                        self.map[y][x + 1] = 0
                    if y + 1 < self.height - 1:
                        self.map[y + 1][x] = 0
    
    def _ensure_border_walls(self):
        """Ensure all edges are walls"""
        for i in range(self.height):
            self.map[i][0] = 1
            self.map[i][self.width - 1] = 1
        for j in range(self.width):
            self.map[0][j] = 1
            self.map[self.height - 1][j] = 1
    
    def print_map(self):
        """Print the map with ASCII characters"""
        symbols = {0: ' ', 1: '█'}
        
        # Mark start and end
        temp_start = self.map[1][1]
        temp_end = self.map[48][48]
        
        for y in range(self.height):
            row = ''
            for x in range(self.width):
                if x == 1 and y == 1:
                    row += 'S'
                elif x == 48 and y == 48:
                    row += 'E'
                else:
                    row += symbols[self.map[y][x]]
            print(row)
    
    def get_stats(self):
        """Get statistics about the generated map"""
        empty_count = sum(row.count(0) for row in self.map)
        total = self.width * self.height
        
        return {
            'empty_spaces': empty_count,
            'walls': total - empty_count,
            'empty_percentage': (empty_count / total) * 100,
            'connected': self._is_connected(1, 1, 48, 48)
        }


# Generate and display a sample map
if __name__ == "__main__":
    print("Generating Stealth Dungeon Map...")
    print("=" * 50)
    
    # Try a few seeds to get a good map
    best_map = None
    best_stats = None
    
    for seed in range(10):  # Try 10 different seeds
        generator = StealthDungeonGenerator(seed=seed)
        dungeon_map = generator.generate()
        stats = generator.get_stats()
        
        # Look for a map with better space utilization
        if (stats['connected'] and 
            35 <= stats['empty_percentage'] <= 55):  # Increased empty space target
            best_map = generator
            best_stats = stats
            break
    
    if best_map:
        print(f"Map generated successfully!")
        print(f"Seed used: {seed}")
        print(f"Stats: {best_stats}")
        print("\nMap Legend: S=Start, E=End, █=Wall, Space=Empty")
        print("=" * 50)
        best_map.print_map()
    else:
        # Fallback to last generated map
        print("Using last generated map:")
        print(f"Stats: {stats}")
        print("\nMap Legend: S=Start, E=End, █=Wall, Space=Empty")
        print("=" * 50)
        generator.print_map()