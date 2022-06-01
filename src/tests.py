import time
from PIL import Image
import imagehash
import glob
import numpy as np

start_time = time.time()

arg='../node1'
client= 0

images ={} # {hash: [imagePath, client]}

imageList= glob.glob(arg+'/*')

for imgPath in imageList:
    img = Image.open(imgPath)
    hash = str(imagehash.average_hash(img))
    print(hash, imgPath)
    num_colors= len(set(img.getdata()))
    size= img.size
    print(num_colors> 65536, size[0]*size[1])
    


    












    # if hash in images.keys():
    #     print("Image already in list")
    #     img1 = Image.open(images[hash][0])
    #     if img.size[0]*img.size[1] > img1.size[0]*img1.size[1]:
    #         images[hash]= [imgPath, client]
    # else:
    #     images[hash]= [imgPath, client]

# for key, value in images.items():
#     print(key, value)


end_time = time.time()

time_elapsed = (end_time - start_time)
print(time_elapsed)
