from PIL import Image, ImageEnhance, ImageOps

#imageIn = "/home/johan/kb/digitalisering/dbnl/pdfs-2023/PDFs-scans/images-BKT/ecur-000.jpg"
imageIn = "/home/johan/kb/digitalisering/dbnl/pdfs-2023/PDFs-scans/images-scanproject/klo-001.jp2"

with Image.open(imageIn) as im:
    im.load()
    print(im.format)
