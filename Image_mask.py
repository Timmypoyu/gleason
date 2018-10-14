import numpy, re
from PIL import Image, ImageDraw

# read image as RGB and add alpha (transparency)
im = Image.open("crop2.tiff")
tuple1 = im.tile
tuple1_len = len(tuple1)
tile_max1 = int(tuple1[tuple1_len-1][1][2])
tile_max2 = int(tuple1[tuple1_len-1][1][3])
im.size=(tile_max1, tile_max2)
im= im.convert("RGBA")

# convert to numpy (for convenience)
imArray = numpy.asarray(im)

# create mask
polygon = [(444.5736434108527, 229.45736434108517), (329.8449612403101, 231.00775193798438), (123.64341085271315, 150.38759689922477), (69.37984496124022, 285.2713178294573), (201.16279069767438, 330.23255813953483), (320.5426356589146, 375.19379844961236), (467.8294573643412, 331.78294573643404), (505.0387596899225, 311.62790697674416)]
maskIm = Image.new('L', (imArray.shape[1], imArray.shape[0]), 0)
ImageDraw.Draw(maskIm).polygon(polygon, outline=1, fill=1)
mask = numpy.array(maskIm)

# assemble new image (uint8: 0-255)
newImArray = numpy.empty(imArray.shape,dtype='uint8')

# colors (three first columns, RGB)
newImArray[:,:,:3] = imArray[:,:,:3]

# transparency (4th column)
newImArray[:,:,3] = mask*255

# back to Image from numpy
newIm = Image.fromarray(newImArray, "RGBA")
newIm.save("out2.png")