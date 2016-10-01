from PIL import Image
import sys

img = Image.open("qr.jpg")
print(img.format, img.mode, img.size)
img = img.convert("1")
img.save("qr.jpg")