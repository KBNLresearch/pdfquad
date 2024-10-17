import pymupdf

"""
Read PDF, set PageMode value to UseThumbs, write result to new PDF 
"""

myPDF = "/home/johan/test/kort004mult/300ppi-50/kort004mult01_01_50.pdf"
doc = pymupdf.open(myPDF)
doc.set_pagemode("UseThumbs")
doc.save("pagemode-thumbs.pdf")



