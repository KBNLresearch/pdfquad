import io
from PIL import Image
from PIL import ImageCms
import pymupdf

#myPDF = "/home/johan/test/kort004mult/300ppi-50/kort004mult01_01_50.pdf"
myPDF = "/home/johan/test/BKT-ecur/BKT-ecur002glas01_01.pdf"

doc = pymupdf.open(myPDF)

encrypted = doc.is_encrypted

meta = doc.metadata

version = doc.page_count
versionCount = doc.version_count

print(meta)

catXref = doc.pdf_catalog()  # get xref of the /Catalog

catDict = doc.xref_get_keys(catXref)

typeValue = doc.xref_get_key(catXref, 'Type')
pageMode = doc.xref_get_key(catXref, 'PageMode')

print(typeValue)
print(pageMode)

pages = 0

for page in doc:
    pages +=1
    images = page.get_images(full=False)
    for image in images:
        # Store PDF object level properties to dictionary
        propsPDF = {}
        propsPDF['xref'] = image[0]
        #propsPDF['smask'] = image[1]
        propsPDF['width'] = image[2]
        propsPDF['height'] = image[3]
        propsPDF['bpc'] = image[4]
        propsPDF['colorspace'] = image[5]
        propsPDF['altcolorspace'] = image[6]
        #propsPDF['name'] = image[7]
        propsPDF['filter'] = image[8]

        # Read raw image stream data from xref id
        xref = propsPDF['xref']
        stream = doc.xref_stream_raw(xref)

        with open('test.dat', 'wb') as fOut:
            fOut.write(stream)

        im = Image.open(io.BytesIO(stream))
        im.load()
        propsStream = {}
        propsStream['format'] = im.format
        propsStream['width'] = im.size[0]
        propsStream['height'] = im.size[1]
        propsStream['mode'] = im.mode
        for key, value in im.info.items():
            if isinstance(value, bytes):
                propsStream[key] = 'bytes'
            elif key == 'dpi' and isinstance(value, tuple):
                propsStream['ppi_x'] = value[0]
                propsStream['ppi_y'] = value[1]
            elif key == 'jfif_density' and isinstance(value, tuple):
                propsStream['jfif_density_x'] = value[0]
                propsStream['jfif_density_y'] = value[1]
            elif isinstance(value, tuple):
                # Skip any other properties that return tuples
                pass
            else:
                propsStream[key] = value
  
        try:
            # ICC profile name and description
            icc = im.info['icc_profile']
            iccProfile = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            propsStream['icc_profile_name'] = ImageCms.getProfileName(iccProfile).strip()
            propsStream['icc_profile_description'] = ImageCms.getProfileDescription(iccProfile).strip()
        except KeyError:
            pass

        #print(propsPDF)
        #print(propsStream)
        #print(str(pages))

