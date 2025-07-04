#!/usr/bin/env python3
"""
Automatically detect and extract individual plane sprites without manual selection.
Uses connected component analysis to find isolated sprites.
"""

from PIL import Image
import numpy as np
from scipy import ndimage
import os

def detect_individual_sprites(image_path, bg_color_hex='#ABD4E6'):
    """
    Automatically detect individual sprites using connected component analysis.
    """
    # Open image
    img = Image.open(image_path)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Convert to numpy array
    img_array = np.array(img)
    
    # Convert bg color to RGB
    bg_color = tuple(int(bg_color_hex[i:i+2], 16) for i in (1, 3, 5))
    
    # Create binary mask (1 for sprite pixels, 0 for background)
    mask = np.zeros((img.height, img.width), dtype=bool)
    
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = img_array[y, x]
            # Check if NOT background
            if not (abs(r - bg_color[0]) < 10 and abs(g - bg_color[1]) < 10 and abs(b - bg_color[2]) < 10):
                mask[y, x] = True
    
    # Find connected components
    labeled_array, num_features = ndimage.label(mask)
    
    # Get bounding boxes for each component
    sprites = []
    for i in range(1, num_features + 1):
        # Find pixels belonging to this component
        component_mask = labeled_array == i
        
        # Get bounding box
        rows, cols = np.where(component_mask)
        if len(rows) > 0 and len(cols) > 0:
            y_min, y_max = rows.min(), rows.max()
            x_min, x_max = cols.min(), cols.max()
            
            width = x_max - x_min + 1
            height = y_max - y_min + 1
            
            # Filter out very small components (noise) and very large ones (multiple sprites)
            if 30 < width < 120 and 30 < height < 120:
                # Check if this looks like a complete plane (has enough pixels)
                pixel_count = np.sum(component_mask)
                fill_ratio = pixel_count / (width * height)
                
                if fill_ratio > 0.2:  # At least 20% filled
                    sprites.append({
                        'x': x_min,
                        'y': y_min,
                        'width': width,
                        'height': height,
                        'pixel_count': pixel_count,
                        'fill_ratio': fill_ratio
                    })
    
    return sprites, img

def find_best_plane_sprites(sprites):
    """
    From all detected sprites, find the best plane sprites for each row.
    Looking specifically for planes with thrust (usually in columns 4-7).
    """
    # Group sprites by approximate row
    rows = {}
    for sprite in sprites:
        row_y = sprite['y'] // 100 * 100  # Group by 100px rows
        if row_y not in rows:
            rows[row_y] = []
        rows[row_y].append(sprite)
    
    # For each row, find sprites that look like planes with thrust
    best_sprites = []
    
    for row_y, row_sprites in sorted(rows.items()):
        # Sort by X position
        row_sprites.sort(key=lambda s: s['x'])
        
        # Look for sprites in the thrust columns (roughly x=300-800)
        thrust_sprites = [s for s in row_sprites if 300 < s['x'] < 800]
        
        # Pick sprites with good fill ratio and reasonable size
        good_sprites = [s for s in thrust_sprites 
                       if s['width'] > 50 and s['height'] > 50 
                       and s['fill_ratio'] > 0.3]
        
        # Add the best ones from this row
        if good_sprites:
            # Take up to 3 sprites per row, preferring middle positions
            selected = sorted(good_sprites, 
                            key=lambda s: abs(s['x'] - 500))[:3]
            best_sprites.extend(selected)
    
    return best_sprites

def extract_sprite(img, x, y, width, height, bg_color_hex='#ABD4E6'):
    """Extract a sprite and make background transparent."""
    # Convert hex color to RGB
    bg_color = tuple(int(bg_color_hex[i:i+2], 16) for i in (1, 3, 5))
    
    # Crop the region
    sprite = img.crop((x, y, x + width, y + height))
    
    # Make background transparent
    sprite = sprite.convert('RGBA')
    pixels = sprite.load()
    
    for i in range(sprite.width):
        for j in range(sprite.height):
            r, g, b, a = pixels[i, j]
            if abs(r - bg_color[0]) < 10 and abs(g - bg_color[1]) < 10 and abs(b - bg_color[2]) < 10:
                pixels[i, j] = (r, g, b, 0)
    
    return sprite

def main():
    sprite_sheet = 'images/planes_spritesheet.gif'
    
    print("Automatically detecting plane sprites...")
    
    # Detect all sprites
    sprites, img = detect_individual_sprites(sprite_sheet)
    print(f"Found {len(sprites)} potential sprites")
    
    # Find the best plane sprites
    best_sprites = find_best_plane_sprites(sprites)
    print(f"Selected {len(best_sprites)} best plane sprites")
    
    # Create output directory
    os.makedirs('auto_sprites', exist_ok=True)
    
    # Generate CSS for the detected sprites
    css_output = "/* Automatically detected plane sprites */\n"
    
    # Map sprites to the 5 plane positions in index.html
    if len(best_sprites) >= 5:
        # Sort by Y then X to get consistent ordering
        best_sprites.sort(key=lambda s: (s['y'], s['x']))
        
        # Select 5 diverse sprites from different rows
        selected = []
        used_rows = set()
        
        for sprite in best_sprites:
            row = sprite['y'] // 100
            if row not in used_rows and len(selected) < 5:
                selected.append(sprite)
                used_rows.add(row)
        
        # If we need more, add from unused sprites
        if len(selected) < 5:
            for sprite in best_sprites:
                if sprite not in selected and len(selected) < 5:
                    selected.append(sprite)
        
        # Generate CSS for the 5 planes
        for i, sprite in enumerate(selected[:5]):
            plane_num = i + 2  # nth-child(2) through nth-child(6)
            
            # Extract and save the sprite
            extracted = extract_sprite(img, sprite['x'], sprite['y'], 
                                     sprite['width'], sprite['height'])
            extracted.save(f"auto_sprites/plane_{plane_num}.png")
            
            css_output += f"""
    .plane:nth-child({plane_num}) {{
      top: {50 + i * 8}%;
      width: {sprite['width']}px;
      height: {sprite['height']}px;
      animation-duration: {8 + i * 2}s;
      animation-delay: {i * 1.5}s;
      background-position: -{sprite['x']}px -{sprite['y']}px;
    }}"""
            
            print(f"Plane {plane_num}: x={sprite['x']}, y={sprite['y']}, "
                  f"size={sprite['width']}x{sprite['height']}")
    
    # Save CSS
    with open('auto_sprite_positions.css', 'w') as f:
        f.write(css_output + '\n')
    
    print("\nCSS saved to auto_sprite_positions.css")
    print("Individual sprites saved to auto_sprites/")
    
    # Also save a preview HTML
    create_preview_html(selected[:5])

def create_preview_html(sprites):
    """Create a preview of the auto-detected sprites."""
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Auto-Detected Sprites</title>
    <style>
        body { 
            background: #ABD4E6; 
            padding: 20px;
            font-family: monospace;
        }
        .preview {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }
        .sprite-box {
            background: white;
            padding: 10px;
            border: 2px solid #000;
        }
        .sprite-img {
            image-rendering: pixelated;
            display: block;
        }
    </style>
</head>
<body>
    <h1>Auto-Detected Plane Sprites</h1>
    <div class="preview">
"""
    
    for i, sprite in enumerate(sprites):
        plane_num = i + 2
        html += f"""
        <div class="sprite-box">
            <img src="auto_sprites/plane_{plane_num}.png" class="sprite-img" width="{sprite['width']*2}" height="{sprite['height']*2}">
            <p>Plane {plane_num}<br>
            {sprite['width']}x{sprite['height']}px<br>
            Pos: ({sprite['x']}, {sprite['y']})</p>
        </div>"""
    
    html += """
    </div>
    <h2>How these were detected:</h2>
    <ul>
        <li>Connected component analysis to find isolated sprites</li>
        <li>Filtered by size (30-120px) and fill ratio (>20%)</li>
        <li>Selected sprites from thrust columns (x=300-800)</li>
        <li>Chose diverse sprites from different rows</li>
    </ul>
</body>
</html>"""
    
    with open('auto_sprites_preview.html', 'w') as f:
        f.write(html)

if __name__ == '__main__':
    main()