from PIL import Image
import imagehash
import glob
import os
from Protocol import Protocol as p

class Functions:

    @classmethod
    def is_better(cls,is_colored1, is_colored2, num_pixeis1, num_pixeis2):
        """
        Compare two images and return True if img1 is better than img2.
        """
        if is_colored1 == is_colored2:
            return num_pixeis1 > num_pixeis2
        
        if is_colored1:
            return num_pixeis1 > 0.7*num_pixeis2

        if is_colored2:
            return 0.7*num_pixeis1 > num_pixeis2


    @classmethod
    def delete_file(cls,img_path):
        """
        Delete image from disk.
        """
        # os.remove(img_path)
        print("Deleted:", img_path)

        
    @classmethod
    def starting_img_list(cls,folder_path):
        """
        Return map of image hashkey to image (in case there is the same hash, the best image remains).
        """
        # img_map= { hashkey: (img_path, is_colored, num_pixeis, num_bytes) }

        img_map={}
        imageList= glob.glob(folder_path+'/*')

        for imgPath in imageList:
            try:
                img = Image.open(imgPath)
                hash = str(imagehash.average_hash(img))
                is_colored= len(set(img.getdata()))> 65536
                size= img.size
                num_pixeis= size[0]*size[1]
            except:
                print("Error opening image: ", imgPath)
                cls.delete_file(imgPath)
                continue

            if hash not in img_map.keys():
                print("New image:", imgPath)
                img_map[hash]= (imgPath, is_colored, num_pixeis, os.path.getsize(imgPath))

            elif cls.is_better(is_colored, img_map[hash][1], num_pixeis, img_map[hash][2]):
                print("Better image found: ", imgPath)
                cls.delete_file(img_map[hash][0])
                img_map[hash]= (imgPath, is_colored, num_pixeis, os.path.getsize(imgPath))

            else:
                print("Worse image found: ", imgPath)
                cls.delete_file(imgPath)

        return img_map

    @classmethod
    def occupied_space(cls,folder_path):
        """
        Return occupied space in bytes.
        """
        return sum([os.path.getsize(f) for f in glob.glob(folder_path+'/*')])

    @classmethod
    def choose_backup(cls, img_path, backup_list, all_tup, num_bytes):
        """
        Choose a backup node for the image and send it
        """
        # backup_list = { (addres, port): occupied_space }

        tup= min(backup_list, key=backup_list.get)
        socket_= all_tup[tup]
        # TODO send image to socket as buckup
        backup_list[tup] += num_bytes
        return tup        

    @classmethod
    def update_general_map(cls,img_map, general_map, my_tup, all_tup, backup_list):
        """
        Update general_map with img_map.
        """
        # general_map = { hashkey: [ (adress1, port1), (adress2, port2), is_colored, num_pixeis, num_bytes ] }

        for hashkey in img_map.keys():

            if hashkey not in general_map.keys():
                print("New image:", img_map[hashkey][0])
                backup_tup = cls.choose_backup(img_map[hashkey][0], backup_list, all_tup, img_map[hashkey][3])
                general_map[hashkey] = [ my_tup, backup_tup, img_map[hashkey][1], img_map[hashkey][2], img_map[hashkey][3] ]
                #TODO update other nodes general_map
                
                
    

        

