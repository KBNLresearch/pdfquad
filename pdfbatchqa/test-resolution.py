import io
from PIL import Image

myJPEG = "/home/johan/test/BKT-ecur/images/-000.jpg"

with open(myJPEG, 'rb') as fIn:
        im = Image.open(fIn)
        im.load()

        for key, value in im.info.items():
            print(key, value)

