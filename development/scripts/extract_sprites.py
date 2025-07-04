#!/usr/bin/env python3
"""
Extract sprites from a sprite sheet, making the background transparent.
Usage: python extract_sprites.py
"""

from PIL import Image
import os

def extract_sprite(image_path, x, y, width, height, bg_color_hex='#ABD4E6'):
    """
    Extract a sprite from the sprite sheet and make background transparent.
    
    Args:
        image_path: Path to the sprite sheet
        x, y: Top-left coordinates of the sprite
        width, height: Dimensions of the sprite
        bg_color_hex: Background color to make transparent (default: #ABD4E6)
    
    Returns:
        PIL Image with transparent background
    """
    # Open the sprite sheet
    img = Image.open(image_path)
    
    # Convert to RGBA if not already
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Crop the region
    sprite = img.crop((x, y, x + width, y + height))
    
    # Convert hex color to RGB
    bg_color = tuple(int(bg_color_hex[i:i+2], 16) for i in (1, 3, 5))
    
    # Get pixel data
    pixels = sprite.load()
    
    # Make background transparent
    for i in range(sprite.width):
        for j in range(sprite.height):
            r, g, b, a = pixels[i, j]
            # Check if pixel matches background color (with some tolerance)
            if abs(r - bg_color[0]) < 5 and abs(g - bg_color[1]) < 5 and abs(b - bg_color[2]) < 5:
                pixels[i, j] = (r, g, b, 0)  # Make transparent
    
    return sprite

def find_single_sprite_bounds(img, x_center, row_y, bg_color):
    """
    Find bounds of a single sprite centered around x_center, carefully isolating it.
    
    Returns: (x, y, width, height) of the isolated sprite
    """
    pixels = img.load()
    
    # Each sprite is roughly 64-100px wide, so search in that range
    search_width = 60
    x_start = max(0, x_center - search_width)
    x_end = min(img.width, x_center + search_width)
    
    # For Y, planes typically span 50-90px in actual height
    # Start from the expected row position and search up/down
    y_search_start = row_y - 20
    y_search_end = row_y + 90
    
    # Find the actual plane bounds within this restricted area
    # First find the main body of the plane (densest pixel area)
    top_y = y_search_end
    bottom_y = y_search_start
    left_x = x_end
    right_x = x_start
    
    # Scan for the main body
    for y in range(y_search_start, y_search_end):
        row_has_content = False
        for x in range(x_start, x_end):
            if 0 <= x < img.width and 0 <= y < img.height:
                r, g, b, a = pixels[x, y]
                if not (abs(r - bg_color[0]) < 10 and abs(g - bg_color[1]) < 10 and abs(b - bg_color[2]) < 10):
                    if y < top_y:
                        top_y = y
                    if y > bottom_y:
                        bottom_y = y
                    if x < left_x:
                        left_x = x
                    if x > right_x:
                        right_x = x
                    row_has_content = True
    
    # Add small padding but constrain to avoid neighboring sprites
    padding = 2
    left_x = max(x_start, left_x - padding)
    right_x = min(x_end, right_x + padding)
    top_y = max(y_search_start, top_y - padding)
    bottom_y = min(y_search_end, bottom_y + padding)
    
    return (left_x, top_y, right_x - left_x + 1, bottom_y - top_y + 1)

def identify_sprites_in_row(image_path, row_y, row_height, bg_color_hex='#ABD4E6'):
    """
    Identify individual sprites in a row by finding non-background regions.
    
    Args:
        image_path: Path to the sprite sheet
        row_y: Y coordinate of the row start
        row_height: Height of the row to search
        bg_color_hex: Background color to ignore
    
    Returns:
        List of sprite bounds (x, y, width, height) with actual sprite dimensions
    """
    img = Image.open(image_path)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Convert hex color to RGB
    bg_color = tuple(int(bg_color_hex[i:i+2], 16) for i in (1, 3, 5))
    
    # Search a larger area to find the actual sprites
    search_start_y = row_y - 50  # Start searching 50px above expected position
    search_end_y = row_y + row_height + 50  # End 50px below
    
    # Get the search area
    pixels = img.load()
    
    # Find columns with non-background pixels in the search area
    non_bg_columns = []
    for x in range(img.width):
        has_content = False
        for y in range(max(0, search_start_y), min(img.height, search_end_y)):
            r, g, b, a = pixels[x, y]
            # Check if pixel is NOT background (with tolerance)
            if not (abs(r - bg_color[0]) < 10 and abs(g - bg_color[1]) < 10 and abs(b - bg_color[2]) < 10):
                has_content = True
                break
        if has_content:
            non_bg_columns.append(x)
    
    # Group consecutive columns into sprites
    sprites = []
    if non_bg_columns:
        start_x = non_bg_columns[0]
        prev_x = start_x
        
        for x in non_bg_columns[1:]:
            if x - prev_x > 5:  # Gap detected, new sprite
                # Find actual bounds of this sprite
                bounds = find_sprite_bounds(img, start_x, prev_x + 1, 
                                          max(0, search_start_y), 
                                          min(img.height, search_end_y), 
                                          bg_color)
                sprites.append(bounds)
                start_x = x
            prev_x = x
        
        # Add the last sprite
        bounds = find_sprite_bounds(img, start_x, prev_x + 1, 
                                  max(0, search_start_y), 
                                  min(img.height, search_end_y), 
                                  bg_color)
        sprites.append(bounds)
    
    return sprites

def extract_isolated_planes():
    """Extract specific plane sprites with better isolation to avoid showing parts of other planes."""
    sprite_sheet = 'images/planes_spritesheet.gif'
    
    # Open the sprite sheet
    img = Image.open(sprite_sheet)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Convert hex color to RGB
    bg_color = tuple(int('#ABD4E6'[i:i+2], 16) for i in (1, 3, 5))
    
    # Define specific sprite locations (center X positions for sprites with thrust)
    # These are the approximate center positions of the thrust sprites
    planes = [
        # SU-33 (row 5) - keeping these as they are good
        {'name': 'su33_1', 'row': 5, 'row_y': 728, 'center_x': 308, 'css_class': 'plane:nth-child(2)'},
        {'name': 'su33_2', 'row': 5, 'row_y': 728, 'center_x': 424, 'css_class': 'plane:nth-child(5)'},
        {'name': 'su33_3', 'row': 5, 'row_y': 728, 'center_x': 652, 'css_class': 'plane:nth-child(6)'},
        
        # F-22 (row 3) - frame 4 with thrust
        {'name': 'f22', 'row': 3, 'row_y': 456, 'center_x': 424, 'css_class': 'plane:nth-child(3)'},
        
        # F-15 (row 4) - frame 5 with thrust  
        {'name': 'f15', 'row': 4, 'row_y': 592, 'center_x': 542, 'css_class': 'plane:nth-child(4)'},
    ]
    
    # Create output directory
    os.makedirs('isolated_sprites', exist_ok=True)
    
    # CSS output
    css_output = "/* Isolated sprite positions without neighboring planes */\n"
    
    for plane in planes:
        print(f"\nExtracting {plane['name']}...")
        
        # Find isolated bounds for this specific sprite
        bounds = find_single_sprite_bounds(img, plane['center_x'], plane['row_y'], bg_color)
        x, y, width, height = bounds
        
        print(f"{plane['name']}: x={x}, y={y}, width={width}px, height={height}px")
        
        # Extract and save the sprite
        sprite = extract_sprite(sprite_sheet, x, y, width, height)
        output_path = f"isolated_sprites/{plane['name']}.png"
        sprite.save(output_path)
        print(f"Saved: {output_path}")
        
        # Add to CSS output
        css_output += f"""
    .{plane['css_class']} {{
      width: {width}px;
      height: {height}px;
      background-position: -{x}px -{y}px;
    }}
"""
    
    # Save CSS snippet
    with open('isolated_sprite_positions.css', 'w') as f:
        f.write(css_output)
    print("\nSaved isolated CSS positions to isolated_sprite_positions.css")

def extract_all_planes():
    """Main extraction function - now extracts isolated sprites."""
    extract_isolated_planes()

def create_preview_html():
    """Create an HTML file to preview the extracted sprites."""
    import glob
    
    # Find all extracted sprites
    sprite_files = sorted(glob.glob('extracted_sprites/su33_frame_*.png'))
    
    sprite_divs = ""
    for sprite_file in sprite_files:
        filename = os.path.basename(sprite_file)
        frame_num = filename.replace('su33_frame_', '').replace('.png', '')
        sprite_divs += f"""
        <div class="sprite">
            <img src="{sprite_file}">
            <p>Frame {frame_num}</p>
        </div>"""
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Extracted Sprites Preview</title>
    <style>
        body {{ 
            background: #ABD4E6; 
            padding: 20px;
            font-family: monospace;
        }}
        .sprite-container {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}
        .sprite {{
            border: 1px solid #000;
            padding: 10px;
            background: white;
            text-align: center;
        }}
        .sprite img {{
            display: block;
            image-rendering: pixelated;
            width: 128px;
            height: 128px;
        }}
        .animation {{
            position: relative;
            width: 128px;
            height: 128px;
            margin: 20px;
        }}
        .animation img {{
            position: absolute;
            opacity: 0;
            animation: fadeSequence {len(sprite_files) * 0.2}s infinite;
        }}
        @keyframes fadeSequence {{
            0%, 100% {{ opacity: 0; }}
            10% {{ opacity: 1; }}
            20% {{ opacity: 0; }}
        }}
    </style>
</head>
<body>
    <h1>Extracted SU-33 Sprites from Row 5</h1>
    <p>Found {len(sprite_files)} sprites in row 5</p>
    
    <h2>Individual Frames</h2>
    <div class="sprite-container">
        {sprite_divs}
    </div>
    
    <h2>Animation Preview</h2>
    <div class="animation">
"""
    
    # Add animation frames with delays
    for i, sprite_file in enumerate(sprite_files):
        delay = i * 0.2
        html += f'        <img src="{sprite_file}" style="animation-delay: {delay}s;">\n'
    
    html += """    </div>
</body>
</html>"""
    
    with open('sprite_preview.html', 'w') as f:
        f.write(html)
    print("Created sprite_preview.html")

if __name__ == '__main__':
    print("Extracting plane sprites...")
    extract_all_planes()
    create_preview_html()
    print("\nDone! Check the 'extracted_sprites' folder for individual PNG files.")
    print("Open 'sprite_preview.html' to see the results.")