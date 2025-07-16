#!/usr/bin/env python3
"""
Sprite Extractor - Extracts individual sprites from a sprite sheet
Detects sprites by finding connected regions of non-background pixels
"""

from PIL import Image
import os
from collections import Counter
import numpy as np

def get_background_color(image):
    """
    Detect the background color (most common color in the image)
    """
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Get all pixels
    pixels = list(image.getdata())
    
    # Count occurrences of each color
    color_counts = Counter(pixels)
    
    # Return the most common color
    background_color = color_counts.most_common(1)[0][0]
    print(f"Detected background color: RGB{background_color}")
    return background_color

def find_sprite_bounds(image, background_color, tolerance=10):
    """
    Find bounding boxes of all sprites in the image
    """
    # Ensure image is in RGB mode
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    width, height = image.size
    pixels = image.load()
    visited = [[False for _ in range(width)] for _ in range(height)]
    sprites = []
    
    def is_background(color):
        """Check if a color is close to the background color"""
        if len(color) == 4:  # RGBA
            color = color[:3]  # Use only RGB
        return all(abs(c1 - c2) <= tolerance for c1, c2 in zip(color, background_color))
    
    def flood_fill(x, y):
        """Find connected region starting from (x, y)"""
        min_x, min_y = x, y
        max_x, max_y = x, y
        stack = [(x, y)]
        
        while stack:
            cx, cy = stack.pop()
            
            if cx < 0 or cx >= width or cy < 0 or cy >= height:
                continue
            if visited[cy][cx]:
                continue
            
            pixel = pixels[cx, cy]
            if is_background(pixel):
                continue
            
            visited[cy][cx] = True
            min_x = min(min_x, cx)
            max_x = max(max_x, cx)
            min_y = min(min_y, cy)
            max_y = max(max_y, cy)
            
            # Check 8 neighbors
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    stack.append((cx + dx, cy + dy))
        
        return min_x, min_y, max_x, max_y
    
    # Scan the image for sprites
    for y in range(height):
        for x in range(width):
            if not visited[y][x] and not is_background(pixels[x, y]):
                bounds = flood_fill(x, y)
                # Only include if the sprite is reasonably sized
                sprite_width = bounds[2] - bounds[0] + 1
                sprite_height = bounds[3] - bounds[1] + 1
                if sprite_width > 10 and sprite_height > 10:
                    sprites.append(bounds)
    
    return sprites

def extract_sprites(image_path, output_dir="sprites"):
    """
    Extract all sprites from the sprite sheet
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the image
    print(f"Loading sprite sheet: {image_path}")
    image = Image.open(image_path)
    
    # Convert to RGB for consistent processing
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Detect background color
    background_color = get_background_color(image)
    
    # Find all sprites
    print("Detecting sprites...")
    sprite_bounds = find_sprite_bounds(image, background_color)
    print(f"Found {len(sprite_bounds)} sprites")
    
    # Sort sprites by position (top to bottom, left to right)
    sprite_bounds.sort(key=lambda b: (b[1], b[0]))
    
    # Extract and save each sprite
    sprite_info = []
    for i, (min_x, min_y, max_x, max_y) in enumerate(sprite_bounds):
        # Crop the sprite
        sprite = image.crop((min_x, min_y, max_x + 1, max_y + 1))
        
        # Convert to RGBA for transparency
        sprite_rgba = Image.new('RGBA', sprite.size, (0, 0, 0, 0))
        sprite_rgba.paste(sprite)
        
        # Make background transparent
        pixels = sprite_rgba.load()
        for y in range(sprite_rgba.height):
            for x in range(sprite_rgba.width):
                if is_background_similar(pixels[x, y][:3], background_color, tolerance=10):
                    pixels[x, y] = (0, 0, 0, 0)
        
        # Save the sprite
        filename = f"plane_{i+1}.png"
        filepath = os.path.join(output_dir, filename)
        sprite_rgba.save(filepath)
        
        sprite_info.append({
            'filename': filename,
            'width': sprite_rgba.width,
            'height': sprite_rgba.height,
            'original_x': min_x,
            'original_y': min_y
        })
        
        print(f"Saved {filename} ({sprite_rgba.width}x{sprite_rgba.height})")
    
    # Generate CSS file
    generate_css(sprite_info, output_dir)
    
    return sprite_info

def is_background_similar(color1, color2, tolerance=10):
    """Check if two colors are similar within tolerance"""
    return all(abs(c1 - c2) <= tolerance for c1, c2 in zip(color1, color2))

def generate_css(sprite_info, output_dir):
    """Generate CSS for using individual sprites"""
    css_content = """/* Individual sprite styles */
.plane {
  position: absolute;
  image-rendering: pixelated;
  transform: rotate(180deg); /* Point downwards */
}

"""
    
    for i, info in enumerate(sprite_info):
        css_content += f""".plane:nth-child({i+1}) {{
  width: {info['width']}px;
  height: {info['height']}px;
  background: url('sprites/{info['filename']}') no-repeat center;
  background-size: contain;
}}

"""
    
    css_path = os.path.join(output_dir, "sprites.css")
    with open(css_path, 'w') as f:
        f.write(css_content)
    
    print(f"\nGenerated CSS file: {css_path}")

if __name__ == "__main__":
    # Extract sprites from the sprite sheet
    sprite_info = extract_sprites("images/planes_spritesheet.gif")
    
    print("\nExtraction complete!")
    print("\nTo use individual sprites, update your HTML to include:")
    print('  <link rel="stylesheet" href="sprites/sprites.css">')
    print("\nAnd remove the sprite sheet background-position styles.")