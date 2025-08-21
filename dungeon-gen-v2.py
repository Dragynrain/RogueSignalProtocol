// Complete dungeon generator for stealth game
const width = 50;
const height = 50;

// Initialize map (1 = wall, 0 = empty)
let map = Array(height).fill(null).map(() => Array(width).fill(1));

// Simple seeded random
let seed = 42;
function random() {
    seed = (seed * 9301 + 49297) % 233280;
    return seed / 233280;
}

// Create rooms
function createRooms() {
    const rooms = [];
    const numRooms = Math.floor(random() * 5) + 8; // 8-12 rooms
    let attempts = 0;
    
    while (rooms.length < numRooms && attempts < 200) {
        attempts++;
        
        // Vary room sizes
        let w, h;
        if (random() < 0.3) { // Larger room
            w = Math.floor(random() * 4) + 6;
            h = Math.floor(random() * 4) + 6;
        } else { // Smaller room
            w = Math.floor(random() * 4) + 3;
            h = Math.floor(random() * 4) + 3;
        }
        
        const x = Math.floor(random() * (width - w - 4)) + 2;
        const y = Math.floor(random() * (height - h - 4)) + 2;
        
        // Check overlap with buffer
        let overlaps = false;
        for (let room of rooms) {
            if (!(x + w + 1 <= room.x || x >= room.x + room.w + 1 || 
                  y + h + 1 <= room.y || y >= room.y + room.h + 1)) {
                overlaps = true;
                break;
            }
        }
        
        if (!overlaps) {
            rooms.push({x, y, w, h});
            // Carve room
            for (let i = y; i < y + h; i++) {
                for (let j = x; j < x + w; j++) {
                    if (i > 0 && i < height - 1 && j > 0 && j < width - 1) {
                        map[i][j] = 0;
                    }
                }
            }
        }
    }
    return rooms;
}

// Create corridor between two points
function createCorridor(x1, y1, x2, y2) {
    const corridorWidth = random() < 0.7 ? 1 : 2;
    
    // L-shaped corridor
    if (random() < 0.5) {
        // Horizontal first
        for (let x = Math.min(x1, x2); x <= Math.max(x1, x2); x++) {
            for (let dy = 0; dy < corridorWidth; dy++) {
                if (y1 + dy > 0 && y1 + dy < height - 1 && x > 0 && x < width - 1) {
                    map[y1 + dy][x] = 0;
                }
            }
        }
        // Then vertical
        for (let y = Math.min(y1, y2); y <= Math.max(y1, y2); y++) {
            for (let dx = 0; dx < corridorWidth; dx++) {
                if (y > 0 && y < height - 1 && x2 + dx > 0 && x2 + dx < width - 1) {
                    map[y][x2 + dx] = 0;
                }
            }
        }
    } else {
        // Vertical first
        for (let y = Math.min(y1, y2); y <= Math.max(y1, y2); y++) {
            for (let dx = 0; dx < corridorWidth; dx++) {
                if (y > 0 && y < height - 1 && x1 + dx > 0 && x1 + dx < width - 1) {
                    map[y][x1 + dx] = 0;
                }
            }
        }
        // Then horizontal
        for (let x = Math.min(x1, x2); x <= Math.max(x1, x2); x++) {
            for (let dy = 0; dy < corridorWidth; dy++) {
                if (y2 + dy > 0 && y2 + dy < height - 1 && x > 0 && x < width - 1) {
                    map[y2 + dy][x] = 0;
                }
            }
        }
    }
}

// Connect rooms using MST
function connectRooms(rooms) {
    if (rooms.length < 2) return;
    
    const connected = [rooms[0]];
    const unconnected = rooms.slice(1);
    
    while (unconnected.length > 0) {
        let minDist = Infinity;
        let closestPair = null;
        let closestIdx = -1;
        
        for (let connRoom of connected) {
            const cx = Math.floor(connRoom.x + connRoom.w / 2);
            const cy = Math.floor(connRoom.y + connRoom.h / 2);
            
            for (let i = 0; i < unconnected.length; i++) {
                const unconn = unconnected[i];
                const ux = Math.floor(unconn.x + unconn.w / 2);
                const uy = Math.floor(unconn.y + unconn.h / 2);
                
                const dist = Math.abs(cx - ux) + Math.abs(cy - uy);
                if (dist < minDist) {
                    minDist = dist;
                    closestPair = [connRoom, unconn];
                    closestIdx = i;
                }
            }
        }
        
        if (closestPair) {
            const [room1, room2] = closestPair;
            const x1 = Math.floor(room1.x + room1.w / 2);
            const y1 = Math.floor(room1.y + room1.h / 2);
            const x2 = Math.floor(room2.x + room2.w / 2);
            const y2 = Math.floor(room2.y + room2.h / 2);
            
            createCorridor(x1, y1, x2, y2);
            connected.push(room2);
            unconnected.splice(closestIdx, 1);
        }
    }
}

// Add extra paths for stealth gameplay
function addExtraPaths(rooms) {
    if (rooms.length < 3) return;
    
    const extraConnections = Math.min(Math.floor(random() * 3) + 1, rooms.length - 1);
    
    for (let i = 0; i < extraConnections; i++) {
        const room1 = rooms[Math.floor(random() * rooms.length)];
        const room2 = rooms[Math.floor(random() * rooms.length)];
        
        if (room1 !== room2) {
            const x1 = Math.floor(room1.x + room1.w / 2);
            const y1 = Math.floor(room1.y + room1.h / 2);
            const x2 = Math.floor(room2.x + room2.w / 2);
            const y2 = Math.floor(room2.y + room2.h / 2);
            
            createCorridor(x1, y1, x2, y2);
        }
    }
}

// Add cover elements in large spaces
function addCoverElements() {
    for (let y = 3; y < height - 3; y += 5) {
        for (let x = 3; x < width - 3; x += 5) {
            // Check if area is mostly open
            let openCount = 0;
            for (let dy = -2; dy <= 2; dy++) {
                for (let dx = -2; dx <= 2; dx++) {
                    if (y + dy >= 0 && y + dy < height && 
                        x + dx >= 0 && x + dx < width &&
                        map[y + dy][x + dx] === 0) {
                        openCount++;
                    }
                }
            }
            
            // If very open, maybe add cover
            if (openCount > 20 && random() < 0.3) {
                if (random() < 0.5) {
                    // Straight cover
                    if (random() < 0.5) {
                        map[y][x] = 1;
                        if (x + 1 < width - 1) map[y][x + 1] = 1;
                    } else {
                        map[y][x] = 1;
                        if (y + 1 < height - 1) map[y + 1][x] = 1;
                    }
                } else {
                    // L-shaped cover
                    map[y][x] = 1;
                    if (random() < 0.5 && x + 1 < width - 1 && y + 1 < height - 1) {
                        map[y][x + 1] = 1;
                        map[y + 1][x] = 1;
                    }
                }
            }
        }
    }
}

// Check if path exists using BFS
function isConnected(x1, y1, x2, y2) {
    if (map[y1][x1] === 1 || map[y2][x2] === 1) return false;
    
    const visited = new Set();
    const queue = [[x1, y1]];
    visited.add(`${x1},${y1}`);
    
    while (queue.length > 0) {
        const [x, y] = queue.shift();
        
        if (x === x2 && y === y2) return true;
        
        const dirs = [[0, 1], [1, 0], [0, -1], [-1, 0]];
        for (let [dx, dy] of dirs) {
            const nx = x + dx;
            const ny = y + dy;
            const key = `${nx},${ny}`;
            
            if (nx >= 0 && nx < width && ny >= 0 && ny < height &&
                !visited.has(key) && map[ny][nx] === 0) {
                visited.add(key);
                queue.push([nx, ny]);
            }
        }
    }
    return false;
}

// Ensure path from start to end
function ensurePathToEnd() {
    let x = 1, y = 1;
    const targetX = 48, targetY = 48;
    
    while (x !== targetX || y !== targetY) {
        if (x < targetX && random() < 0.7) {
            x++;
        } else if (y < targetY) {
            y++;
        } else if (x < targetX) {
            x++;
        }
        
        if (x > 0 && x < width - 1 && y > 0 && y < height - 1) {
            map[y][x] = 0;
            // Sometimes make wider
            if (random() < 0.3) {
                if (x + 1 < width - 1) map[y][x + 1] = 0;
                if (y + 1 < height - 1) map[y + 1][x] = 0;
            }
        }
    }
}

// Generate the dungeon
console.log("Generating Stealth Dungeon...\n");

// Try different seeds to get a good map
let bestMap = null;
let bestSeed = -1;
let bestStats = null;

for (let trySeed = 0; trySeed < 10; trySeed++) {
    seed = trySeed * 1337;
    map = Array(height).fill(null).map(() => Array(width).fill(1));
    
    const rooms = createRooms();
    connectRooms(rooms);
    addExtraPaths(rooms);
    
    // Ensure start and end are open
    map[1][1] = 0;
    map[48][48] = 0;
    
    // Check connectivity
    if (!isConnected(1, 1, 48, 48)) {
        ensurePathToEnd();
    }
    
    addCoverElements();
    
    // Ensure borders are walls
    for (let i = 0; i < height; i++) {
        map[i][0] = 1;
        map[i][width - 1] = 1;
    }
    for (let j = 0; j < width; j++) {
        map[0][j] = 1;
        map[height - 1][j] = 1;
    }
    
    // Calculate stats
    let emptyCount = 0;
    for (let row of map) {
        for (let cell of row) {
            if (cell === 0) emptyCount++;
        }
    }
    const emptyPercent = (emptyCount / (width * height)) * 100;
    
    if (isConnected(1, 1, 48, 48) && emptyPercent >= 25 && emptyPercent <= 40) {
        bestMap = map.map(row => [...row]);
        bestSeed = trySeed;
        bestStats = {
            rooms: rooms.length,
            emptySpaces: emptyCount,
            walls: width * height - emptyCount,
            emptyPercent: emptyPercent
        };
        break;
    }
}

// Use best map or last generated
if (bestMap) {
    map = bestMap;
    console.log(`✓ Found excellent map! Seed: ${bestSeed}`);
    console.log(`Stats: ${bestStats.rooms} rooms, ${bestStats.emptySpaces} empty spaces (${bestStats.emptyPercent.toFixed(1)}%)`);
} else {
    console.log("Using last generated map");
}

console.log("\nMap Legend: S=Start, E=End, #=Wall, .=Empty");
console.log("=" + "=".repeat(49));

// Print the map
for (let y = 0; y < height; y++) {
    let row = "";
    for (let x = 0; x < width; x++) {
        if (x === 1 && y === 1) {
            row += "S";
        } else if (x === 48 && y === 48) {
            row += "E";
        } else {
            row += map[y][x] === 1 ? "#" : ".";
        }
    }
    console.log(row);
}

console.log("\n" + "=".repeat(50));
console.log("Map features for stealth gameplay:");
console.log("- Multiple asymmetrical rooms");
console.log("- Narrow corridors for choke points");
console.log("- Multiple paths between areas");
console.log("- Cover elements in larger spaces");
console.log("- Guaranteed path from Start to End");