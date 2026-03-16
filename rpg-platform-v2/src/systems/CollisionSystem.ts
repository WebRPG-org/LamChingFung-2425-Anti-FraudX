/**
 * CollisionSystem - RPG Maker MV Compatible Collision Detection
 * 
 * This system implements RPG Maker MV's tile-based collision rules:
 * - Uses tileset flags to determine passability
 * - Supports 4-directional collision checking
 * - Implements invisible walls (air walls)
 * 
 * Flag bits (from RPG Maker MV):
 * - 0x0010 (16): Impassable (空氣牆 - Air Wall)
 * - 0x0020 (32): Down blocked
 * - 0x0040 (64): Left blocked  
 * - 0x0080 (128): Right blocked
 * - 0x0100 (256): Up blocked
 * - 0x0800 (2048): Star passable (☆ - can pass from below)
 */

export class CollisionSystem {
  private tilemap: Phaser.Tilemaps.Tilemap;
  private tilesetFlags: number[] = [];
  private tileSize: number = 48;

  // Collision flag constants (RPG Maker MV standard)
  private readonly FLAG_IMPASSABLE = 0x0010;  // 16 - 完全不可通行
  private readonly FLAG_DOWN = 0x0020;        // 32 - 下方被阻擋
  private readonly FLAG_LEFT = 0x0040;        // 64 - 左方被阻擋
  private readonly FLAG_RIGHT = 0x0080;       // 128 - 右方被阻擋
  private readonly FLAG_UP = 0x0100;          // 256 - 上方被阻擋
  private readonly FLAG_STAR = 0x0800;        // 2048 - 星標可通行（從下方可通過）

  constructor(_scene: Phaser.Scene, tilemap: Phaser.Tilemaps.Tilemap) {
    this.tilemap = tilemap;
    this.loadTilesetFlags();
  }

  /**
   * Load tileset flags from map data
   * In RPG Maker, each tileset has a flags array that defines collision for each tile
   */
  private loadTilesetFlags(): void {
    // Try to load flags from map data
    const firstTileset = this.tilemap.getTileset('Tileset');
    
    if (firstTileset && (firstTileset as any).tileData) {
      const tileData = (firstTileset as any).tileData;
      if (tileData.flags) {
        this.tilesetFlags = tileData.flags;
        console.log(`[CollisionSystem] Loaded ${this.tilesetFlags.length} tileset flags`);
        return;
      }
    }

    // Fallback: Create default flags based on tile properties
    console.log('[CollisionSystem] Using default collision flags');
    this.createDefaultFlags();
  }

  /**
   * Create default collision flags for common tile patterns
   */
  private createDefaultFlags(): void {
    // Initialize with 8192 tiles (RPG Maker MV standard)
    this.tilesetFlags = new Array(8192).fill(0);

    // Set impassable flags for common obstacle tiles
    // These are typical RPG Maker tile IDs that should block movement
    
    // Water tiles (2816-2900) - impassable
    for (let i = 2816; i <= 2900; i++) {
      this.tilesetFlags[i] = this.FLAG_IMPASSABLE;
    }

    // Building/wall tiles (typically higher IDs)
    // Trees, rocks, buildings should be impassable
    const impassableRanges = [
      [2048, 2100],  // Walls
      [2226, 2232],  // Special objects
      [7760, 7800],  // Buildings
      [8154, 8158],  // More buildings
    ];

    impassableRanges.forEach(([start, end]) => {
      for (let i = start; i <= end; i++) {
        this.tilesetFlags[i] = this.FLAG_IMPASSABLE;
      }
    });

    console.log('[CollisionSystem] Created default collision flags');
  }

  /**
   * Check if a character can pass through a tile in a specific direction
   * This is the core collision detection method from RPG Maker MV
   */
  public canPass(x: number, y: number, direction: number): boolean {
    // Convert pixel coordinates to tile coordinates
    const tileX = Math.floor(x / this.tileSize);
    const tileY = Math.floor(y / this.tileSize);

    // Check if position is within map bounds
    if (!this.isValid(tileX, tileY)) {
      return false;
    }

    // Check all layers for collision
    const layers = this.tilemap.layers;
    for (let i = 0; i < layers.length; i++) {
      const tile = this.tilemap.getTileAt(tileX, tileY, false, i);
      if (tile && !this.checkPassage(tile.index, direction)) {
        return false;
      }
    }

    // Check destination tile
    const dx = this.getDirectionX(direction);
    const dy = this.getDirectionY(direction);
    const destX = tileX + dx;
    const destY = tileY + dy;

    if (!this.isValid(destX, destY)) {
      return false;
    }

    // Check if destination tile blocks entry from our direction
    for (let i = 0; i < layers.length; i++) {
      const tile = this.tilemap.getTileAt(destX, destY, false, i);
      if (tile && !this.checkPassage(tile.index, this.reverseDirection(direction))) {
        return false;
      }
    }

    return true;
  }

  /**
   * Check if a tile allows passage in a specific direction
   * @param tileId - The tile ID to check
   * @param direction - Direction: 2=down, 4=left, 6=right, 8=up
   */
  private checkPassage(tileId: number, direction: number): boolean {
    const flags = this.tilesetFlags[tileId] || 0;

    // If tile is completely impassable
    if ((flags & this.FLAG_IMPASSABLE) !== 0) {
      return false;
    }

    // Check directional flags
    switch (direction) {
      case 2: // Down
        return (flags & this.FLAG_DOWN) === 0;
      case 4: // Left
        return (flags & this.FLAG_LEFT) === 0;
      case 6: // Right
        return (flags & this.FLAG_RIGHT) === 0;
      case 8: // Up
        // Star tiles can be passed from below
        if ((flags & this.FLAG_STAR) !== 0) {
          return true;
        }
        return (flags & this.FLAG_UP) === 0;
      default:
        return true;
    }
  }

  /**
   * Check if tile coordinates are within map bounds
   */
  private isValid(x: number, y: number): boolean {
    return x >= 0 && x < this.tilemap.width && y >= 0 && y < this.tilemap.height;
  }

  /**
   * Get X offset for direction
   */
  private getDirectionX(direction: number): number {
    switch (direction) {
      case 4: return -1; // Left
      case 6: return 1;  // Right
      default: return 0;
    }
  }

  /**
   * Get Y offset for direction
   */
  private getDirectionY(direction: number): number {
    switch (direction) {
      case 2: return 1;  // Down
      case 8: return -1; // Up
      default: return 0;
    }
  }

  /**
   * Reverse direction (for checking entry from opposite side)
   */
  private reverseDirection(direction: number): number {
    switch (direction) {
      case 2: return 8; // Down -> Up
      case 4: return 6; // Left -> Right
      case 6: return 4; // Right -> Left
      case 8: return 2; // Up -> Down
      default: return direction;
    }
  }

  /**
   * Convert Phaser direction string to RPG Maker direction number
   */
  public directionToNumber(direction: 'down' | 'left' | 'right' | 'up'): number {
    switch (direction) {
      case 'down': return 2;
      case 'left': return 4;
      case 'right': return 6;
      case 'up': return 8;
      default: return 2;
    }
  }

  /**
   * Check if player can move to a specific position
   * This is a convenience method for Phaser integration
   */
  public canMoveTo(fromX: number, fromY: number, toX: number, toY: number): boolean {
    // Determine direction of movement
    const dx = toX - fromX;
    const dy = toY - fromY;

    let direction: number;
    if (Math.abs(dx) > Math.abs(dy)) {
      direction = dx > 0 ? 6 : 4; // Right or Left
    } else {
      direction = dy > 0 ? 2 : 8; // Down or Up
    }

    return this.canPass(fromX, fromY, direction);
  }

  /**
   * Get collision bounds for a tile
   * Returns null if tile is passable, or a rectangle if impassable
   */
  public getTileCollisionBounds(tileX: number, tileY: number): Phaser.Geom.Rectangle | null {
    if (!this.isValid(tileX, tileY)) {
      return null;
    }

    // Check all layers
    const layers = this.tilemap.layers;
    for (let i = 0; i < layers.length; i++) {
      const tile = this.tilemap.getTileAt(tileX, tileY, false, layers[i].name);
      if (tile) {
        const flags = this.tilesetFlags[tile.index] || 0;
        if ((flags & this.FLAG_IMPASSABLE) !== 0) {
          return new Phaser.Geom.Rectangle(
            tileX * this.tileSize,
            tileY * this.tileSize,
            this.tileSize,
            this.tileSize
          );
        }
      }
    }

    return null;
  }

  /**
   * Set custom flags for a specific tile ID
   * Useful for dynamic collision changes
   */
  public setTileFlags(tileId: number, flags: number): void {
    this.tilesetFlags[tileId] = flags;
  }

  /**
   * Get flags for a specific tile ID
   */
  public getTileFlags(tileId: number): number {
    return this.tilesetFlags[tileId] || 0;
  }

  /**
   * Load flags from RPG Maker tileset data
   */
  public loadFlagsFromData(flags: number[]): void {
    this.tilesetFlags = flags;
    console.log(`[CollisionSystem] Loaded ${flags.length} flags from tileset data`);
  }
}
