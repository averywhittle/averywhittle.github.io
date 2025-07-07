#!/usr/bin/env python3
"""
Generate cloud sprites for the game.
"""

from PIL import Image, ImageDraw
import os

def create_cloud_sprite(width, height, filename):
    """Create a simple cloud sprite with transparency."""
    # Create image with transparent background
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Cloud color (white with some transparency)
    cloud_color = (255, 255, 255, 200)
    
    # Draw overlapping ellipses to create cloud shape
    # Main body
    draw.ellipse([width*0.2, height*0.3, width*0.8, height*0.7], fill=cloud_color)
    
    # Left puff
    draw.ellipse([width*0.1, height*0.35, width*0.4, height*0.65], fill=cloud_color)
    
    # Right puff
    draw.ellipse([width*0.6, height*0.35, width*0.9, height*0.65], fill=cloud_color)
    
    # Top puff
    draw.ellipse([width*0.35, height*0.2, width*0.65, height*0.5], fill=cloud_color)
    
    # Bottom puffs
    draw.ellipse([width*0.25, height*0.5, width*0.5, height*0.8], fill=cloud_color)
    draw.ellipse([width*0.5, height*0.5, width*0.75, height*0.8], fill=cloud_color)
    
    # Save the cloud sprite
    img.save(filename)

# Create cloud sprites directory
os.makedirs('images/clouds', exist_ok=True)

# Generate different sized cloud sprites
clouds = [
    (120, 60, 'images/clouds/cloud1.png'),
    (150, 70, 'images/clouds/cloud2.png'),
    (100, 50, 'images/clouds/cloud3.png'),
    (130, 65, 'images/clouds/cloud4.png'),
    (110, 55, 'images/clouds/cloud5.png'),
]

for width, height, filename in clouds:
    create_cloud_sprite(width, height, filename)
    print(f"Created {filename}")

print("Cloud sprites generated!")