import os
from PIL import Image
from PIL import ImageEnhance

for wine_level in range(0, 11):
    for f in os.listdir("base_sprites"):
        pil_image = Image.open("base_sprites/" + f)
        converter = ImageEnhance.Color(pil_image)
        img2 = converter.enhance(wine_level / 5)
        img2.save("sprites/" + f.replace(".png", ".{}.png".format(wine_level)))
