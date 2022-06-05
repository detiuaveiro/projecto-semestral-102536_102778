from turtle import update
from PIL import Image
import imagehash
import os
from Protocol import Protocol as p

class Functions:

    # img_map = 
    # { hashkey: (img_name, num_colors, num_pixeis, num_bytes) } 
    # local

    # my_node = (address, port)
    # local

    # all_nodes = [ (address, port), ... ]
    # SYNCRONIZED , includes my_node

    # all_socks = 
    # { (address, port) : socket }
    # local, all other nodes

    # general_map = 
    # { hashkey: [ (address1, port1), (address2, port2), num_colors, num_pixeis, num_bytes ] }
    # SYNCRONIZED

    # update_lst = 
    # { hashkey: [ (address1, port1), (address2, port2), num_colors, num_pixeis, num_bytes, img_name ] } 
    # changes to send to all nodes

    # storage = 
    # { (address, port): occupied_space } 
    # local

    # nodes_imgs = 
    # { (address, port) : [ hashkey, ... ] }
    # local

    def __init__(self):
        self.folder_path = '../node0'
        self.my_node = ("localhost", 5000)

        self.img_map= self.starting_img_list(self.folder_path)

            


    @classmethod
    def is_better(cls, num_colors1, num_colors2, num_pixeis1, num_pixeis2):
        """
        Compare two images and return True if img1 is better than img2.
        """
        n_colors=70000
        if (num_colors1 > n_colors) == (num_colors2 > n_colors):
            return num_pixeis1 > num_pixeis2
        
        if num_colors1 > n_colors:
            return num_pixeis1 > 0.7*num_pixeis2

        if num_colors2 > n_colors:
            return 0.7*num_pixeis1 > num_pixeis2


    @classmethod
    def delete_file(cls, folder_path, img_name):
        """
        Delete image from disk.
        """
        img_path = os.path.join(folder_path, img_name)
        # os.remove(img_path)
        print("Deleted:", img_path)

        
    @classmethod
    def starting_img_list(cls, folder_path):
        """
        Return map of image hashkey to image (in case there is the same hash, the best image remains).
        """
        img_map={}
        imageList= os.listdir(folder_path)

        for img_name in imageList:

            img_path= os.path.join(folder_path, img_name)

            try:
                img = Image.open(img_path)
                hash = str(imagehash.average_hash(img))
                num_colors= len(set(img.getdata()))
                size= img.size
                num_pixeis= size[0]*size[1]
            except:
                print("Error opening image: ", img_path)
                cls.delete_file(folder_path, img_name)
                continue

            if hash not in img_map.keys():
                print("New image:", img_path)
                img_map[hash]= (img_name, num_colors, num_pixeis, os.path.getsize(img_path))

            elif cls.is_better(num_colors, img_map[hash][1], num_pixeis, img_map[hash][2]):
                print("Better image found: ", img_path)
                cls.delete_file(folder_path, img_map[hash][0])
                img_map[hash] = (img_name, num_colors, num_pixeis, os.path.getsize(img_path))

            else:
                print("Worse image found: ", img_path)
                cls.delete_file(folder_path, img_name)

        return img_map


    @classmethod
    def nodes_storage(cls, general_map, all_socks):
        """
        Return occupied space in bytes.
        """
        storage={}

        for node in all_socks.keys():
            storage[node]= 0

        for val in general_map.values():
            storage[val[0]] += val[4]
            storage[val[1]] += val[4]

        return storage


    @classmethod
    def nodes_imgs(cls, general_map):
        """
        Return list of images in each node.
        """
        nodes_imgs={}

        for hash in general_map.keys():
            nodes_imgs[hash]=[]

        for key, val in general_map.items():
            nodes_imgs[val[0]].append(key)
            nodes_imgs[val[1]].append(key)

        return nodes_imgs


    @classmethod
    def get_backup_node(cls, folder_path, hashkey, img_map, general_map, all_socks, storage):
        """
        Choose the best node to backup the image.
        Send the image and update storage.
        """
        if general_map.get(hashkey) is not None:
            val = general_map[hashkey]
            storage[val[0]] -= val[4]
            storage[val[1]] -= val[4]

            #TODO send msg to old nodes to delete the file

        backup_node= min(storage, key=storage.get)

        #TODO send image to backup_node
        # use all_socks and img_map to get the name of the file
     
        storage[backup_node] += img_map[hashkey][3]

        return backup_node


    @classmethod
    def update_img(cls, folder_path, hashkey, img_map, general_map, my_node, all_socks, storage, update_lst):
        """
        Add/replace image to general_map and update_lst.
        Update storage and send image to backup node.
        """
        backup_node= cls.get_backup_node(folder_path, hashkey, img_map, general_map, all_socks, storage)
        general_map[hashkey]= (my_node, backup_node, img_map[hashkey][1], img_map[hashkey][2], img_map[hashkey][3])
        update_lst[hashkey]= (my_node, backup_node, img_map[hashkey][1], img_map[hashkey][2], img_map[hashkey][3], img_map[hashkey][0])
   

    @classmethod
    def send_update(cls, update_lst, all_socks):
        """
        Send update_lst to all nodes.
        """
        #TODO send update_lst to all nodes


    @classmethod
    def merge_my_imgs(cls, folder_path, img_map, general_map, my_node, all_socks, storage):
        """
        Update general_map with img_map.
        """
        update_lst={}

        for hashkey in img_map.keys():

            if hashkey not in general_map.keys():

                print("New image:", img_map[hashkey][0])
                cls.update_img(hashkey, folder_path, img_map, general_map, my_node, all_socks, storage, update_lst)
            
            elif cls.is_better(img_map[hashkey][1], general_map[hashkey][2], img_map[hashkey][2], general_map[hashkey][3]):

                print("Better image found: ", img_map[hashkey][0])
                cls.update_img(hashkey, folder_path, img_map, general_map, my_node, all_socks, storage, update_lst)

            else:
                print("Worse image found: ", img_map[hashkey][0])
                cls.delete_file(img_map[hashkey][0])
                img_map.pop(hashkey)

        cls.send_update(update_lst, all_socks)


    @classmethod
    def update_general_map(cls, general_map, update_lst, my_node, img_map):
        """
        Update general_map with update_lst.
        """
        for key, val in update_lst.items():
            general_map[key] = val[:-1]

            if val[1] == my_node:
                print("New image:", val[5])
                img_map[key] = (val[5], val[2], val[3], val[4])


    @classmethod
    def save_img(cls, img, folder_path, img_name):
        """
        Save image to disk.
        """
        img_path = os.path.join(folder_path, img_name)
        img.save(img_path)
        print("New image:", img_path)


    @classmethod
    def handle_disconect(cls, folder_path, node, my_node, all_socks, img_map, nodes_imgs, general_map, storage):
        """
        Re-send backup images if node dies and update general_map and storage.
        """
        update_lst={}

        for hashkey in nodes_imgs[node]:

            if hashkey in img_map.keys():
                print("Re-making backup image:", img_map[hashkey][0])
                cls.update_img(folder_path, hashkey, img_map, general_map, my_node, all_socks, storage, update_lst)

        cls.send_update(update_lst, all_socks)
