"""Rebuild the LumaTint PNG and ICO assets with Pillow."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

path = Path(__file__).parent
size = 512
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
for i in range(445, 0, -1):
    ratio = i / 445
    col = (int(116 + 28 * (1-ratio)), int(92 + 70 * (1-ratio)), 244, 255)
    inset = int((445 - i)/2)
    draw.rounded_rectangle((34+inset, 34+inset, 478-inset, 478-inset), radius=max(8, int(117*ratio)), fill=col)
# soft circle glow
glow = Image.new("RGBA", (size, size), (0,0,0,0))
g = ImageDraw.Draw(glow)
g.ellipse((145, 145, 367, 367), fill=(254, 214, 255, 155))
glow = glow.filter(ImageFilter.GaussianBlur(43))
img.alpha_composite(glow)
draw = ImageDraw.Draw(img)
# white sparkle / optical hue symbol
path1=[(256, 115), (291, 217), (397, 256), (291, 291), (256, 397), (220, 291), (115, 256), (220, 217)]
draw.polygon(path1, fill=(255,255,255,255))
draw.ellipse((230, 230, 281, 281),fill=(129,111,249,255))
img.save(path / "lumatint.png")
img.save(path / "lumatint.ico", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
print("Created icon assets")
