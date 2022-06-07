from pickle import NONE
from PIL import Image
import imagehash
import os

class Functions:
    def __init__(self):

        # self.img_map = 
        # { hashkey: (num_colors, num_pixeis, num_bytes) } 
        # local

        # self.my_node = (address, port)
        # local

        # self.all_nodes = [ (address, port), ... ]
        # SYNCRONIZED , includes self.my_node

        # self.all_socks = 
        # { (address, port) : socket }
        # local, all other nodes

        # self.general_map = 
        # { hashkey: [ (address1, port1), (address2, port2), num_colors, num_pixeis, num_bytes ] }
        # SYNCRONIZED

        # update = 
        # [ (address1, port1), (address2, port2), num_colors, num_pixeis, num_bytes, hashkey ]
        # change to send to all nodes

        # self.storage = 
        # { (address, port): occupied_space } 
        # local

        # self.nodes_imgs = 
        # { (address, port) : [ hashkey, ... ] }
        # local

        self.folder_path = '../node1'
        self.my_node = ("localhost", 5000)

        self.general_map= dict()
        self.storage= dict()
        self.nodes_imgs= dict()

        self.img_map= dict()
        self.starting_img_list()

        self.all_nodes= [self.my_node]
        self.all_nodes= [("localhost", 5000), ("localhost", 5001), ("localhost", 5002), ("localhost", 5003)]

        self.all_socks= dict()
        self.all_socks= {("localhost", 5001): "sock1", ("localhost", 5002): "sock2", ("localhost", 5003):"sock3"}

        # self.merge_my_imgs()


    def is_better(self, num_colors1, num_colors2, num_pixeis1, num_pixeis2, num_bytes1, num_bytes2):
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


    def delete_file(self, img_name):
        """
        Delete image from disk.
        """
        img_path = os.path.join(self.folder_path, img_name)
        # os.remove(img_path)
        print("Deleted:", img_path)

    
    def rename_file(self, folder_path, img_name, hashkey):
        """
        Rename image to hashkey.
        """
        img_path = os.path.join(folder_path, img_name)
        os.rename(img_path, os.path.join(folder_path, hashkey))
        print("Renamed to: ", hashkey)

    
    def save_file(self, img, hashkey):
        """
        Save image to disk.
        """
        img_path = os.path.join(self.folder_path, hashkey)
        img.save(img_path)
        print("Saved: ", img_path)

    
    def starting_img_list(self):
        """
        Get map of image hashkey to image (in case there is the same hash, the best image remains).
        """
        print("\nStarting my img list\n")
        self.img_map={}
        imageList= os.listdir(self.folder_path)

        for img_name in imageList:

            img_path= os.path.join(self.folder_path, img_name)

            try:
                img = Image.open(img_path)
                hash = str(imagehash.average_hash(img))
                num_colors = len(set(img.getdata()))
                size = img.size
                num_pixeis = size[0]*size[1]
                num_bytes = os.path.getsize(img_path)
            except:
                print("Error opening image: ", img_path)
                self.delete_file(img_name)
                continue

            if hash not in self.img_map.keys():
                print("New image:", img_path)
                self.img_map[hash]= (num_colors, num_pixeis, num_bytes)
                self.rename_file(self.folder_path, img_name, hash)

            elif self.is_better(num_colors, self.img_map[hash][0], num_pixeis, self.img_map[hash][1], num_bytes, self.img_map[hash][2]):
                print("Better image found: ", img_path)
                self.delete_file(self.img_map[hash][0])
                self.img_map[hash] = (num_colors, num_pixeis, num_bytes)
                self.rename_file(self.folder_path, img_name, hash)

            else:
                print("Worse image found: ", img_path)
                self.delete_file(img_name)


    def starting_updates(self):
        """
        Update storage occupied space in bytes.
        And images per node.
        """

        for node in self.all_nodes[1:]:
            self.storage[node] = 0
            self.nodes_imgs[node] =[]

        for key, val in self.general_map.items():
            if val[0] != self.my_node:
                self.storage[val[0]] += val[4]
                self.nodes_imgs[val[0]].append(key)
            if val[1] != self.my_node:
                self.storage[val[1]] += val[4]
                self.nodes_imgs[val[1]].append(key)

        print("\nStarting updates done\n")


    def add_new_node(self, node, sock):
        """
        Add new node to all_nodes and all_socks.
        """
        self.all_nodes.append(node)
        self.all_socks[node] = sock
        self.storage[node] = 0
        self.nodes_imgs[node] = []
        print("\nNew node joined: ", node, "\n")

    
    def update_data(self, update):
        """
        Update general_map and storage.
        """
        if self.general_map.get(update[5]) is None:
            print("Update with new image: ", update[5])
            if self.all_nodes(update[0]) is not None:
                if update[0] != self.my_node:
                    self.storage[update[0]] += update[4]
                    self.nodes_imgs[update[0]].append(update[5])
            if self.all_nodes(update[1]) is not None:
                if update[1] != self.my_node:
                    self.storage[update[1]] += update[4]
                    self.nodes_imgs[update[1]].append(update[5])
            self.general_map[update[5]] = update[0:5]

        elif self.is_better(update[2], self.general_map[update[5]][2], update[3], self.general_map[update[5]][3], update[4], self.general_map[update[5]][4]):
            print("Update with better image: ", update[5])
            val= self.general_map[update[5]]
            if self.all_nodes(val[0]) is not None:
                if val[0] != self.my_node:
                    self.storage[val[0]] -= val[4]
                    self.nodes_imgs[val[0]].remove(update[5])
            if self.all_nodes(val[1]) is not None:
                if val[1] != self.my_node:
                    self.storage[val[1]] -= val[4]
                    self.nodes_imgs[val[1]].remove(update[5])
            if self.all_nodes(update[0]) is not None:
                if update[0] != self.my_node:
                    self.storage[update[0]] += update[4]
                    self.nodes_imgs[update[0]].append(update[5])
            if self.all_nodes(update[1]) is not None:
                if update[1] != self.my_node:
                    self.storage[update[1]] += update[4]
                    self.nodes_imgs[update[1]].append(update[5])
            self.general_map[update[5]] = update[0:5]

        else:
            print("Update with worse image: ", update[5])


    def backup_node(self, hashkey):
        """
        Choose the best node to backup the image.
        Send the image and update self.storage.
        """
        if self.general_map.get(hashkey) is not None:
            val = self.general_map[hashkey]
            if self.all_nodes(val[0]) is not None:
                if  val[0] != self.my_node:
                    self.storage[val[0]] -= val[4]
                    self.nodes_imgs[val[0]].remove(hashkey)
            if self.all_nodes(val[0]) is not None:
                if val[1] != self.my_node:
                    self.storage[val[1]] -= val[4]
                    self.nodes_imgs[val[1]].remove(hashkey)

        backup_node= min(self.storage, key=self.storage.get)

        self.storage[backup_node] += self.img_map[hashkey][2]
        self.nodes_imgs[backup_node].append(hashkey)

        return backup_node


    def send_update(self, hashkey):
        """
        Send update to all nodes
        """
        update= self.general_map[hashkey]
        update.append(self.my_node)
        
        #TODO send update to all nodes

    
    def send_img(self, hashkey, node):
        """
        Send image to all nodes.
        """
        img_path = os.path.join(self.folder_path, hashkey)
        # img = Image.open(img_path)
        #TODO send image to node
    
        print("Image sent to: ", node)


    def backup_and_update(self, hashkey):
        """
        Backup image to best node and send update.
        """
        backup_node = self.backup_node(hashkey)
        self.general_map[hashkey] = [self.my_node, backup_node, self.img_map[hashkey][0], self.img_map[hashkey][1], self.img_map[hashkey][2]]
        self.send_update(hashkey)
        self.send_img(hashkey, backup_node)


    def merge_my_img(self):
        """
        Update self.general_map with self.img_map.
        """
        print("\nMerging my images...\n")

        for hashkey in self.img_map.keys():

            # TODO UPDATE DATA EVERYTIME WE GET AN UPDATE

            if self.general_map.get(hashkey) is None:
                print("New image:", hashkey)
                self.backup_and_update(hashkey)
                
                
            elif self.is_better(self.img_map[hashkey][0], self.general_map[hashkey][2], self.img_map[hashkey][1], self.general_map[hashkey][3], self.img_map[hashkey][2], self.general_map[hashkey][4]):
                print("Better image found: ", hashkey)
                self.backup_and_update(hashkey)
                
            else:
                print("Worse image found: ", hashkey)
                self.delete_file(hashkey)
                self.img_map.pop(hashkey)

    
    def handle_disconect(self, node):
        """
        Re-send backup images if node dies and update self.general_map and self.storage.
        """
        print("\nNode disconnected: ", node, "\n")

        self.all_nodes.remove(node)
        self.all_socks.pop(node)
        self.storage.pop(node)     

        for hashkey in self.nodes_imgs[node]:

            # TODO UPDATE DATA EVERYTIME WE GET AN UPDATE

            if self.img_map.get(hashkey) is not None:
                print("Image: ", hashkey, " was lost")
                self.backup_and_update(hashkey)

        self.nodes_imgs.pop(node)
