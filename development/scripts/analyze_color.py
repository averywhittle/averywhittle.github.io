from PIL import Image
import numpy as np
from collections import Counter

# Open the image
img = Image.open('/Users/avery/Documents/GitHub/averywhittle.github.io/images/planes_spritesheet.gif')

# Convert to RGB if needed
if img.mode != 'RGB':
    img = img.convert('RGB')

# Get image data as numpy array
img_array = np.array(img)

# Sample multiple background areas to ensure accuracy
# Top-left corner area
corner_pixels = []
for y in range(5, 15):
    for x in range(5, 15):
        corner_pixels.append(tuple(img_array[y, x]))

# Middle area between sprites
middle_pixels = []
for y in range(100, 110):
    for x in range(120, 130):
        middle_pixels.append(tuple(img_array[y, x]))

# Combine all background samples
all_background_pixels = corner_pixels + middle_pixels

# Count occurrences
color_counter = Counter(all_background_pixels)
most_common_color = color_counter.most_common(1)[0][0]

# Convert to hex
hex_color = '#{:02x}{:02x}{:02x}'.format(most_common_color[0], most_common_color[1], most_common_color[2])

print(f"Most common background color (RGB): {most_common_color}")
print(f"Hex color: {hex_color}")

# Also check a few specific pixel coordinates for verification
print("\nVerification - checking specific background pixels:")
specific_coords = [(10, 10), (50, 50), (100, 120), (200, 200)]
for coord in specific_coords:
    y, x = coord
    if y < img_array.shape[0] and x < img_array.shape[1]:
        pixel = img_array[y, x]
        hex_val = '#{:02x}{:02x}{:02x}'.format(pixel[0], pixel[1], pixel[2])
        print(f"Pixel at ({x}, {y}): RGB{tuple(pixel)} = {hex_val}")