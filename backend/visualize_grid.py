#!/usr/bin/env python3
"""
Grid Visualization for VeriGreen Demo UI

This script creates visual representations of how the satellite image
will be divided into tiles for the web interface.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from pathlib import Path

def visualize_tile_grid(image_width=10980, image_height=10980, tile_size=64, output_dir="data/processed/optimization_test"):
    """Create visual representations of the tile grid."""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Calculate grid dimensions
    tiles_x = (image_width + tile_size - 1) // tile_size
    tiles_y = (image_height + tile_size - 1) // tile_size
    total_tiles = tiles_x * tiles_y
    
    print(f"🗺️  VeriGreen Demo Grid Visualization")
    print(f"=" * 50)
    print(f"📐 Original Satellite Image: {image_width:,} x {image_height:,} pixels")
    print(f"🔲 Tile Size: {tile_size} x {tile_size} pixels")
    print(f"📏 Grid Dimensions: {tiles_x} x {tiles_y} tiles")
    print(f"🔢 Total Tiles: {total_tiles:,}")
    print(f"📦 Coverage: Each tile covers {tile_size * 10}m x {tile_size * 10}m on the ground (10m/pixel)")
    
    # Create grid visualization
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
    
    # Plot 1: Full grid overview
    ax1.set_xlim(0, tiles_x)
    ax1.set_ylim(0, tiles_y)
    ax1.set_aspect('equal')
    ax1.set_title(f'Full Grid Overview\n{tiles_x} x {tiles_y} = {total_tiles:,} tiles', fontsize=12, fontweight='bold')
    ax1.set_xlabel(f'Tiles (→ {tiles_x * tile_size * 10 / 1000:.1f} km)')
    ax1.set_ylabel(f'Tiles (↑ {tiles_y * tile_size * 10 / 1000:.1f} km)')
    
    # Draw grid lines (sample every 10th line to avoid clutter)
    for i in range(0, tiles_x + 1, max(1, tiles_x // 20)):
        ax1.axvline(i, color='gray', alpha=0.3, linewidth=0.5)
    for i in range(0, tiles_y + 1, max(1, tiles_y // 20)):
        ax1.axhline(i, color='gray', alpha=0.3, linewidth=0.5)
    
    # Add some sample tiles with different colors
    colors = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow', 'lightpink']
    sample_positions = [
        (10, 10), (50, 50), (100, 100), (150, 150), (80, 120)
    ]
    
    for i, (x, y) in enumerate(sample_positions):
        if x < tiles_x and y < tiles_y:
            rect = patches.Rectangle((x, y), 1, 1, linewidth=1, 
                                   edgecolor='black', facecolor=colors[i % len(colors)])
            ax1.add_patch(rect)
            ax1.text(x + 0.5, y + 0.5, f'{i+1}', ha='center', va='center', fontsize=8, fontweight='bold')
    
    # Plot 2: Zoomed section (showing individual tiles)
    zoom_start_x, zoom_start_y = 50, 50
    zoom_size = 20  # Show 20x20 tiles
    
    ax2.set_xlim(zoom_start_x, zoom_start_x + zoom_size)
    ax2.set_ylim(zoom_start_y, zoom_start_y + zoom_size)
    ax2.set_aspect('equal')
    ax2.set_title(f'Zoomed View: {zoom_size}x{zoom_size} tiles\n(Each square = 1 tile = {tile_size}x{tile_size} pixels)', fontsize=12, fontweight='bold')
    ax2.set_xlabel(f'Tile X (each = {tile_size * 10}m)')
    ax2.set_ylabel(f'Tile Y (each = {tile_size * 10}m)')
    
    # Draw detailed grid
    for i in range(zoom_start_x, zoom_start_x + zoom_size + 1):
        ax2.axvline(i, color='black', alpha=0.5, linewidth=0.5)
    for i in range(zoom_start_y, zoom_start_y + zoom_size + 1):
        ax2.axhline(i, color='black', alpha=0.5, linewidth=0.5)
    
    # Add tile numbers in zoomed view
    for x in range(zoom_start_x, zoom_start_x + zoom_size):
        for y in range(zoom_start_y, zoom_start_y + zoom_size):
            tile_id = y * tiles_x + x  # Simple tile ID calculation
            color = 'lightgreen' if (x + y) % 2 == 0 else 'lightblue'
            rect = patches.Rectangle((x, y), 1, 1, linewidth=0.5, 
                                   edgecolor='black', facecolor=color, alpha=0.7)
            ax2.add_patch(rect)
            if zoom_size <= 10:  # Only show numbers if not too crowded
                ax2.text(x + 0.5, y + 0.5, str(tile_id), ha='center', va='center', fontsize=6)
    
    # Plot 3: UI mockup representation
    ax3.set_xlim(0, 100)
    ax3.set_ylim(0, 100)
    ax3.set_aspect('equal')
    ax3.set_title('Web UI Representation\n(How it looks in browser)', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Browser Width %')
    ax3.set_ylabel('Browser Height %')
    
    # Mock browser window
    browser_rect = patches.Rectangle((5, 10), 90, 80, linewidth=2, 
                                   edgecolor='black', facecolor='white')
    ax3.add_patch(browser_rect)
    
    # Mock map viewport (showing a portion of tiles)
    viewport_tiles_x = min(20, tiles_x)  # Show 20x20 tiles in viewport
    viewport_tiles_y = min(20, tiles_y)
    
    map_width = 80
    map_height = 70
    
    for i in range(viewport_tiles_x):
        for j in range(viewport_tiles_y):
            x = 10 + (i / viewport_tiles_x) * map_width
            y = 15 + (j / viewport_tiles_y) * map_height
            w = map_width / viewport_tiles_x
            h = map_height / viewport_tiles_y
            
            # Color based on mock NDVI values
            mock_ndvi = 0.3 + 0.4 * np.sin(i * 0.3) * np.cos(j * 0.3)
            color = plt.cm.RdYlGn(mock_ndvi)
            
            tile_rect = patches.Rectangle((x, y), w, h, linewidth=0.1, 
                                        edgecolor='gray', facecolor=color, alpha=0.8)
            ax3.add_patch(tile_rect)
    
    # Add UI elements
    ax3.text(50, 95, 'VeriGreen - Satellite Forest Monitoring', ha='center', va='center', 
            fontsize=14, fontweight='bold')
    ax3.text(50, 5, f'Viewing {viewport_tiles_x}×{viewport_tiles_y} tiles (of {total_tiles:,} total)', 
            ha='center', va='center', fontsize=10)
    
    # Add legend
    ax3.text(85, 50, 'NDVI\nScale', ha='center', va='center', fontsize=8, rotation=90)
    
    plt.tight_layout()
    
    # Save the visualization
    output_file = output_path / f"grid_visualization_{tile_size}px.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"📊 Visualization saved to: {output_file}")
    
    plt.show()
    
    return {
        "tiles_x": tiles_x,
        "tiles_y": tiles_y,
        "total_tiles": total_tiles,
        "coverage_km": {
            "width": tiles_x * tile_size * 10 / 1000,
            "height": tiles_y * tile_size * 10 / 1000
        }
    }

def print_ui_scenarios(tile_size=64):
    """Print different UI scenarios and what they would look like."""
    
    # Calculate basic dimensions
    image_width, image_height = 10980, 10980
    tiles_x = (image_width + tile_size - 1) // tile_size
    tiles_y = (image_height + tile_size - 1) // tile_size
    total_tiles = tiles_x * tiles_y
    
    print(f"\n🖥️  UI Scenarios for {tile_size}px Tiles")
    print(f"=" * 50)
    
    # Scenario 1: Full map view
    print(f"📱 Mobile View (320px wide):")
    mobile_tiles_visible = 320 // tile_size
    print(f"   - Can see ~{mobile_tiles_visible} tiles across")
    print(f"   - Good for overview, zooming in needed for detail")
    
    print(f"\n💻 Desktop View (1920px wide):")
    desktop_tiles_visible = 1920 // tile_size
    print(f"   - Can see ~{desktop_tiles_visible} tiles across")
    print(f"   - Can see ~{min(desktop_tiles_visible, tiles_x)} x {min(desktop_tiles_visible, tiles_y)} tiles at once")
    print(f"   - Covers ~{min(desktop_tiles_visible * tile_size * 10 / 1000, tiles_x * tile_size * 10 / 1000):.1f} km x {min(desktop_tiles_visible * tile_size * 10 / 1000, tiles_y * tile_size * 10 / 1000):.1f} km")
    
    print(f"\n🗺️  Map Interaction:")
    print(f"   - Total map area: {tiles_x * tile_size * 10 / 1000:.1f} km x {tiles_y * tile_size * 10 / 1000:.1f} km")
    print(f"   - Each tile represents: {tile_size * 10}m x {tile_size * 10}m on ground")
    print(f"   - Zoom levels needed: ~{np.log2(tiles_x / 10):.0f} levels to see full detail")
    
    print(f"\n⚡ Performance Implications:")
    print(f"   - Tiles to load for full view: {total_tiles:,}")
    print(f"   - Tiles visible at desktop resolution: ~{min(30*30, total_tiles):,}")
    print(f"   - Typical viewport loads: 100-400 tiles at a time")
    print(f"   - Fast loading: Each tile is small ({tile_size}px × {tile_size}px)")
    
    print(f"\n🎯 Demo Experience:")
    print(f"   - User can zoom from country → forest → individual trees")
    print(f"   - Smooth pan/zoom with tile-based loading")
    print(f"   - NDVI colors show forest health instantly")
    print(f"   - Blockchain verification per tile area")

if __name__ == "__main__":
    # Test with recommended configuration
    print("Creating grid visualization for recommended 64px JPEG tiles...")
    result = visualize_tile_grid(tile_size=64)
    
    print_ui_scenarios(tile_size=64)
    
    print(f"\n📋 Summary for Demo Planning:")
    print(f"   🗺️  Map covers: {result['coverage_km']['width']:.1f} km × {result['coverage_km']['height']:.1f} km")
    print(f"   🔲 Grid size: {result['tiles_x']} × {result['tiles_y']} tiles") 
    print(f"   📱 Mobile friendly: Users can zoom in for detail")
    print(f"   💻 Desktop optimal: See meaningful area at once")
    print(f"   ⚡ Performance: Small tiles = fast loading")
    print(f"   🎨 Visual: Each tile can have distinct NDVI color") 