import os
from PIL import Image, ImageDraw, ImageFont

def create_placeholder_logo(text, filename, color, size=(200, 200)):
    # Create a new image with a white background
    img = Image.new('RGB', size, color=color)
    d = ImageDraw.Draw(img)

    # Load a font (try default, else fallback)
    try:
        # Try to load a generic font
        font = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font = ImageFont.load_default()

    # Draw text in the center
    # Note: simplistic centering
    d.text((10, size[1]//2), text, fill=(255, 255, 255), font=font)

    # Save
    path = os.path.join('statics/img', filename)
    img.save(path)
    print(f"Generated {path}")

def main():
    os.makedirs('statics/img', exist_ok=True)
    create_placeholder_logo("RVA", "logo_rva.png", (0, 0, 128)) # Navy Blue
    create_placeholder_logo("GoPass", "logo_gopass.png", (0, 128, 0)) # Green

if __name__ == "__main__":
    main()
