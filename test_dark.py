import base64
from PIL import Image
import io
import re

with open("frontend/public/logo-dark.svg", "r") as f:
    content = f.read()

match = re.search(r"base64,([a-zA-Z0-9+/=]+)", content)
if match:
    img_data = base64.b64decode(match.group(1))
    img = Image.open(io.BytesIO(img_data)).convert("RGBA")
    
    white_count = 0
    black_count = 0
    trans_count = 0
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = img.getpixel((x, y))
            if a == 0:
                trans_count += 1
            elif r > 200 and g > 200 and b > 200:
                white_count += 1
            elif r < 50 and g < 50 and b < 50:
                black_count += 1
                
    print(f"White pixels: {white_count}, Black pixels: {black_count}, Transparent pixels: {trans_count}")
