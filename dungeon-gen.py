// Analyze what made the hand-drawn map good:
// 1. Irregular room shapes (L-shapes, alcoves, varied sizes)
// 2. No repetitive patterns or grid-like layouts
// 3. Tight corridors with tactical chokepoints
// 4. Asymmetrical placement
// 5. More complex wall patterns
// 6. Dead ends and alcoves for tactical hiding

class ImprovedDungeonGenerator {
    constructor(width = 50, height = 50) {
        this.width = width;
        this.height = height;
        this.grid = Array(height).fill().map(() => Array(width).fill(1));
    }
    
    isValid(x, y) {
        return x >= 1 && x < this.width - 1 && y >= 1 && y < this.height - 1;
    }
    
    // Carve irregular shaped rooms
    carveIrregularRoom(x, y, w, h, random) {
        const carved = [];
        
        // Base rectangle
        for (let dy = 0; dy < h; dy++) {
            for (let dx = 0; dx < w; dx++) {
                if (this.isValid(x + dx, y + dy)) {
                    this.grid[y + dy][x + dx] = 0;
                    carved.push([x + dx, y + dy]);
                }
            }
        }
        
        // Add extensions to create L-shapes or irregular forms
        if (random() < 0.6) {
            // Add horizontal extension
            const extW = Math.floor(random() * 4) + 2;
            const extH = Math.floor(random() * 3) + 2;
            const extX = random() < 0.5 ? x - extW : x + w;
            const extY = y + Math.floor(random() * (h - extH));
            
            for (let dy = 0; dy < extH; dy++) {
                for (let dx = 0; dx < extW; dx++) {
                    if (this.isValid(extX + dx, extY + dy)) {
                        this.grid[extY + dy][extX + dx] = 0;
                        carved.push([extX + dx, extY + dy]);
                    }
                }
            }
        }
        
        if (random() < 0.4) {
            // Add vertical extension
            const extW = Math.floor(random() * 3) + 2;
            const extH = Math.floor(random() * 4) + 2;
            const extX = x + Math.floor(random() * (w - extW));
            const extY = random() < 0.5 ? y - extH : y + h;
            
            for (let dy = 0; dy < extH; dy++) {
                for (let dx = 0; dx < extW; dx++) {
                    if (this.isValid(extX + dx, extY + dy)) {
                        this.grid[extY + dy][extX + dx] = 0;
                        carved.push([extX + dx, extY + dy]);
                    }
                }
            }
        }
        
        return carved;
    }
    
    // Create winding corridors instead of straight L-shapes
    carveWindingCorridor(x1, y1, x2, y2, random) {
        let currentX = x1;
        let currentY = y1;
        
        while (currentX !== x2 || currentY !== y2) {
            if (this.isValid(currentX, currentY)) {
                this.grid[currentY][currentX] = 0;
            }
            
            // Sometimes add width to corridor
            if (random() < 0.3) {
                const dirs = [[0, 1], [0, -1], [1, 0], [-1, 0]];
                for (const [dx, dy] of dirs) {
                    if (this.isValid(currentX + dx, currentY + dy)) {
                        this.grid[currentY + dy][currentX + dx] = 0;
                    }
                }
            }
            
            // Move toward target with some randomness
            const diffX = x2 - currentX;
            const diffY = y2 - currentY;
            
            if (Math.abs(diffX) > Math.abs(diffY)) {
                currentX += diffX > 0 ? 1 : -1;
                // Add some wandering
                if (random() < 0.3 && diffY !== 0) {
                    currentY += diffY > 0 ? 1 : -1;
                }
            } else {
                currentY += diffY > 0 ? 1 : -1;
                // Add some wandering
                if (random() < 0.3 && diffX !== 0) {
                    currentX += diffX > 0 ? 1 : -1;
                }
            }
        }
    }
    
    // Add small alcoves and dead ends
    addAlcoves(random, count = 15) {
        for (let i = 0; i < count; i++) {
            // Find a wall next to floor
            const candidates = [];
            
            for (let y = 2; y < this.height - 2; y++) {
                for (let x = 2; x < this.width - 2; x++) {
                    if (this.grid[y][x] === 1) {
                        // Check if adjacent to exactly one floor tile
                        const adjacent = [
                            [x-1, y], [x+1, y], [x, y-1], [x, y+1]
                        ].filter(([nx, ny]) => 
                            nx >= 0 && nx < this.width && ny >= 0 && ny < this.height &&
                            this.grid[ny][nx] === 0
                        );
                        
                        if (adjacent.length === 1) {
                            candidates.push([x, y]);
                        }
                    }
                }
            }
            
            if (candidates.length > 0) {
                const [ax, ay] = candidates[Math.floor(random() * candidates.length)];
                
                // Create small alcove
                const alcoveSize = Math.floor(random() * 3) + 1;
                const directions = [[0, 1], [0, -1], [1, 0], [-1, 0]];
                const [dx, dy] = directions[Math.floor(random() * 4)];
                
                for (let step = 0; step < alcoveSize; step++) {
                    const nx = ax + dx * step;
                    const ny = ay + dy * step;
                    if (this.isValid(nx, ny)) {
                        this.grid[ny][nx] = 0;
                    }
                }
            }
        }
    }
    
    // Add wall protrusions to break up large open areas
    addWallProtrusions(random, count = 20) {
        for (let i = 0; i < count; i++) {
            // Find floor tiles in open areas
            for (let y = 3; y < this.height - 3; y++) {
                for (let x = 3; x < this.width - 3; x++) {
                    if (this.grid[y][x] === 0 && random() < 0.01) {
                        // Check if in a large open area
                        let openCount = 0;
                        for (let dy = -2; dy <= 2; dy++) {
                            for (let dx = -2; dx <= 2; dx++) {
                                if (this.grid[y + dy][x + dx] === 0) {
                                    openCount++;
                                }
                            }
                        }
                        
                        if (openCount > 15) {
                            // Add a small wall protrusion
                            const size = Math.floor(random() * 2) + 1;
                            for (let dy = 0; dy < size; dy++) {
                                for (let dx = 0; dx < size; dx++) {
                                    if (this.isValid(x + dx, y + dy)) {
                                        this.grid[y + dy][x + dx] = 1;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    findConnectedRegions() {
        const visited = Array(this.height).fill().map(() => Array(this.width).fill(false));
        const regions = [];
        
        for (let y = 0; y < this.height; y++) {
            for (let x = 0; x < this.width; x++) {
                if (this.grid[y][x] === 0 && !visited[y][x]) {
                    const region = [];
                    const queue = [[x, y]];
                    visited[y][x] = true;
                    
                    while (queue.length > 0) {
                        const [cx, cy] = queue.shift();
                        region.push([cx, cy]);
                        
                        const directions = [[0, 1], [0, -1], [1, 0], [-1, 0]];
                        for (const [dx, dy] of directions) {
                            const nx = cx + dx;
                            const ny = cy + dy;
                            
                            if (nx >= 0 && nx < this.width && ny >= 0 && ny < this.height &&
                                this.grid[ny][nx] === 0 && !visited[ny][nx]) {
                                visited[ny][nx] = true;
                                queue.push([nx, ny]);
                            }
                        }
                    }
                    
                    regions.push(region);
                }
            }
        }
        
        return regions;
    }
    
    connectAllRegions(random) {
        let regions = this.findConnectedRegions();
        console.log(`Found ${regions.length} disconnected regions`);
        
        while (regions.length > 1) {
            const largestRegion = regions.reduce((max, region) => 
                region.length > max.length ? region : max);
            
            let minDistance = Infinity;
            let bestConnection = null;
            
            for (const region of regions) {
                if (region === largestRegion) continue;
                
                for (const [x1, y1] of largestRegion) {
                    for (const [x2, y2] of region) {
                        const distance = Math.abs(x2 - x1) + Math.abs(y2 - y1);
                        if (distance < minDistance) {
                            minDistance = distance;
                            bestConnection = [[x1, y1], [x2, y2]];
                        }
                    }
                }
            }
            
            if (bestConnection) {
                const [[x1, y1], [x2, y2]] = bestConnection;
                this.carveWindingCorridor(x1, y1, x2, y2, random);
                console.log(`Connected regions via winding corridor`);
            }
            
            regions = this.findConnectedRegions();
            console.log(`Now ${regions.length} regions after connection`);
        }
    }
    
    findPath(startX, startY, endX, endY) {
        const openSet = [[startX, startY, 0, Math.abs(endX - startX) + Math.abs(endY - startY)]];
        const closedSet = new Set();
        const gScore = new Map();
        
        gScore.set(`${startX},${startY}`, 0);
        
        while (openSet.length > 0) {
            openSet.sort((a, b) => (a[2] + a[3]) - (b[2] + b[3]));
            const [currentX, currentY, g] = openSet.shift();
            const currentKey = `${currentX},${currentY}`;
            
            if (currentX === endX && currentY === endY) {
                return true;
            }
            
            closedSet.add(currentKey);
            
            const directions = [[0, 1], [0, -1], [1, 0], [-1, 0]];
            for (const [dx, dy] of directions) {
                const neighborX = currentX + dx;
                const neighborY = currentY + dy;
                const neighborKey = `${neighborX},${neighborY}`;
                
                if (neighborX < 0 || neighborX >= this.width || 
                    neighborY < 0 || neighborY >= this.height ||
                    this.grid[neighborY][neighborX] === 1 ||
                    closedSet.has(neighborKey)) {
                    continue;
                }
                
                const tentativeG = g + 1;
                
                if (!gScore.has(neighborKey) || tentativeG < gScore.get(neighborKey)) {
                    gScore.set(neighborKey, tentativeG);
                    const neighborH = Math.abs(endX - neighborX) + Math.abs(endY - neighborY);
                    
                    const existing = openSet.findIndex(([x, y]) => x === neighborX && y === neighborY);
                    if (existing === -1) {
                        openSet.push([neighborX, neighborY, tentativeG, neighborH]);
                    }
                }
            }
        }
        
        return false;
    }
    
    verifyConnectivity() {
        let startX = null, startY = null;
        for (let y = 1; y < this.height - 1 && startX === null; y++) {
            for (let x = 1; x < this.width - 1; x++) {
                if (this.grid[y][x] === 0) {
                    startX = x;
                    startY = y;
                    break;
                }
            }
        }
        
        let endX = null, endY = null;
        for (let y = this.height - 2; y >= 1 && endX === null; y--) {
            for (let x = this.width - 2; x >= 1; x--) {
                if (this.grid[y][x] === 0) {
                    endX = x;
                    endY = y;
                    break;
                }
            }
        }
        
        if (startX === null || endX === null) {
            console.log('ERROR: No floor tiles found!');
            return false;
        }
        
        console.log(`Testing pathfinding from (${startX},${startY}) to (${endX},${endY})`);
        const pathExists = this.findPath(startX, startY, endX, endY);
        
        if (pathExists) {
            console.log(`SUCCESS: Path verified between corners`);
            return true;
        } else {
            console.log('FAILED: No path found');
            return false;
        }
    }
    
    generate(seed = 42) {
        let rng = seed;
        const random = () => {
            rng = (rng * 1664525 + 1013904223) % Math.pow(2, 32);
            return rng / Math.pow(2, 32);
        };
        
        const roomCenters = [];
        
        // Phase 1: Create irregular rooms with asymmetric placement
        const attemptedPositions = [];
        
        for (let attempts = 0; attempts < 30; attempts++) {
            const x = Math.floor(random() * (this.width - 15)) + 3;
            const y = Math.floor(random() * (this.height - 10)) + 3;
            const w = Math.floor(random() * 5) + 4;
            const h = Math.floor(random() * 4) + 3;
            
            // Check minimum distance from other rooms
            let tooClose = false;
            for (const [px, py] of attemptedPositions) {
                if (Math.abs(px - x) < 6 || Math.abs(py - y) < 5) {
                    tooClose = true;
                    break;
                }
            }
            
            if (!tooClose) {
                attemptedPositions.push([x, y]);
                this.carveIrregularRoom(x, y, w, h, random);
                roomCenters.push([x + Math.floor(w/2), y + Math.floor(h/2)]);
            }
        }
        
        console.log(`Generated ${roomCenters.length} irregular rooms`);
        
        // Phase 2: Connect rooms with winding corridors
        for (let i = 0; i < roomCenters.length - 1; i++) {
            if (random() < 0.6) {
                const [x1, y1] = roomCenters[i];
                const [x2, y2] = roomCenters[i + 1];
                this.carveWindingCorridor(x1, y1, x2, y2, random);
            }
        }
        
        // Phase 3: Add some extra connections for variety
        for (let i = 0; i < Math.min(5, roomCenters.length - 2); i++) {
            const idx1 = Math.floor(random() * roomCenters.length);
            const idx2 = Math.floor(random() * roomCenters.length);
            if (idx1 !== idx2) {
                const [x1, y1] = roomCenters[idx1];
                const [x2, y2] = roomCenters[idx2];
                this.carveWindingCorridor(x1, y1, x2, y2, random);
            }
        }
        
        // Phase 4: Ensure connectivity
        this.connectAllRegions(random);
        
        // Phase 5: Add tactical features
        this.addAlcoves(random, 12);
        this.addWallProtrusions(random, 8);
        
        // Phase 6: Verify
        console.log('Verifying connectivity...');
        return this.verifyConnectivity();
    }
    
    print() {
        const chars = {1: '▓', 0: '░'};
        for (const row of this.grid) {
            console.log(row.map(cell => chars[cell]).join(''));
        }
    }
}

// Test the improved generator
console.log('=== ITERATION 1: Improved Algorithm ===');
const dungeon1 = new ImprovedDungeonGenerator(50, 50);
const success1 = dungeon1.generate(42);
console.log(`\nGeneration ${success1 ? 'SUCCESSFUL' : 'FAILED'}\n`);
if (success1) {
    dungeon1.print();
}