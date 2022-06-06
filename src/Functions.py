from PIL import Image
import imagehash
import os
from Protocol import Protocol as p

class Functions:

    # self.img_map = 
    # { hashkey: (img_name, num_colors, num_pixeis, num_bytes) } 
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

    # update_lst = 
    # { hashkey: [ (address1, port1), (address2, port2), num_colors, num_pixeis, num_bytes ] } 
    # changes to send to all nodes

    # self.storage = 
    # { (address, port): occupied_space } 
    # local

    # self.nodes_imgs = 
    # { (address, port) : [ hashkey, ... ] }
    # local

    def __init__(self):
        self.folder_path = '../node2'
        self.my_node = ("localhost", 5000)

        self.img_map= dict()
        self.starting_img_list()

        self.all_nodes= list()
        self.all_nodes= [("localhost", 5000), ("localhost", 5001), ("localhost", 5002), ("localhost", 5003)]

        self.all_socks= dict()
        self.all_socks= {("localhost", 5001): "sock1", ("localhost", 5002): "sock2", ("localhost", 5003):"sock3"}

        self.general_map= dict()

        self.storage= dict() #updated when a node dies
        self.nodes_storage()

        self.merge_my_imgs()

        self.nodes_imgs= dict() #updated when a node dies

        # quando receber um update para o general_map
        # self.update_general_map(update_lst)

        # quando receber uma imagem e a info
        # self.save_img(img, hashkey, img_name, num_colors, num_pixeis, num_bytes)

        # quando um nó morrer
        # self.handle_disconect(node) 

    
    def is_better(self, num_colors1, num_colors2, num_pixeis1, num_pixeis2):
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
                self.img_map[hash]= (img_name, num_colors, num_pixeis, num_bytes)

            elif self.is_better(num_colors, self.img_map[hash][1], num_pixeis, self.img_map[hash][2]):
                print("Better image found: ", img_path)
                self.delete_file(self.img_map[hash][0])
                self.img_map[hash] = (img_name, num_colors, num_pixeis, num_bytes)

            else:
                print("Worse image found: ", img_path)
                self.delete_file(img_name)


    def add_new_node(self, node, sock):
        """
        Add new node to all_nodes and all_socks.
        """
        self.all_nodes.append(node)
        self.all_socks[node] = sock
        print("\nNew node joined: ", node, "\n")

    
    def nodes_storage(self):
        """
        Occupied space in bytes.
        """
        self.storage={}

        for node in self.all_socks.keys():
            self.storage[node]= 0

        for val in self.general_map.values():
            if val[0] != self.my_node:
                self.storage[val[0]]+= val[4]
            if val[1] != self.my_node:
                self.storage[val[1]]+= val[4]

    
    def update_nodes_imgs(self):
        """
        Update list of images in each node.
        """
        self.nodes_imgs={}

        for node in self.all_socks.keys():
            self.nodes_imgs[node]=[]

        for key, val in self.general_map.items():
            if val[0] != self.my_node:
                self.nodes_imgs[val[0]].append(key)
            if val[1] != self.my_node:
                self.nodes_imgs[val[1]].append(key)

    
    def get_backup_node(self, hashkey):
        """
        Choose the best node to backup the image.
        Send the image and update self.storage.
        """
        if self.general_map.get(hashkey) is not None:
            val = self.general_map[hashkey]
            if val[0] != self.my_node:
                self.storage[val[0]] -= val[4]
            if val[1] != self.my_node:
                self.storage[val[1]] -= val[4]

            #TODO send msg to old nodes to delete the file

        backup_node= min(self.storage, key=self.storage.get)

        #TODO send image and its info to backup_node
        # use self.all_socks and self.img_map to get the name of the file
        # backup node updates its img_map
        print("Image sent to backup node: ", backup_node)
     
        self.storage[backup_node] += self.img_map[hashkey][3]

        return backup_node


    def update_img(self, hashkey, update_lst):
        """
        Add/replace image to self.general_map and update_lst.
        Update self.storage and send image to backup node.
        """
        backup_node= self.get_backup_node(hashkey)
        self.general_map[hashkey]= (self.my_node, backup_node, self.img_map[hashkey][1], self.img_map[hashkey][2], self.img_map[hashkey][3])
        update_lst[hashkey]= (self.my_node, backup_node, self.img_map[hashkey][1], self.img_map[hashkey][2], self.img_map[hashkey][3])
   

    def send_update(self, update_lst):
        """
        Send update_lst to all nodes.
        """
        #TODO send update_lst to all nodes
        print("\nUpdate sent to all nodes\n")


    def merge_my_imgs(self):
        """
        Update self.general_map with self.img_map.
        """
        print("\nMerging my images...\n")
        update_lst={}

        for hashkey in self.img_map.keys():

            if hashkey not in self.general_map.keys():

                print("New image:", self.img_map[hashkey][0])
                self.update_img(hashkey, update_lst)
            
            elif self.is_better(self.img_map[hashkey][1], self.general_map[hashkey][2], self.img_map[hashkey][2], self.general_map[hashkey][3]):

                print("Better image found: ", self.img_map[hashkey][0])
                self.update_img(hashkey, update_lst)

            else:
                print("Worse image found: ", self.img_map[hashkey][0])
                self.delete_file(self.img_map[hashkey][0])
                self.img_map.pop(hashkey)

        self.send_update(update_lst)

    
    def update_general_map(self, update_lst):
        """
        Update self.general_map with update_lst.
        """
        for key, val in update_lst.items():
            self.general_map[key] = val

    
    def save_img(self, img, hashkey, img_name, num_colors, num_pixeis, num_bytes):
        """
        Save image to disk.
        And update img_map.
        """
        img_path = os.path.join(self.folder_path, img_name)
        # img.save(img_path) 
        self.img_map[hashkey] = (img_name, num_colors, num_pixeis, num_bytes)
        print("New image:", img_path)


    def handle_disconect(self, node):
        """
        Re-send backup images if node dies and update self.general_map and self.storage.
        """
        print("\nNode disconnected: ", node, "\n")
        self.update_nodes_imgs()
        self.nodes_storage()

        self.storage.pop(node)
        self.all_nodes.remove(node)
        self.all_socks.pop(node)

        for hashkey in self.nodes_imgs[node]:
            self.general_map.pop(hashkey)

        update_lst={}
        
        #TODO change to update all localy and send what it needs

        for hashkey in self.nodes_imgs[node]:

            if hashkey in self.img_map.keys():
                print("Re-making backup for image:", self.img_map[hashkey][0])
                self.update_img(hashkey, update_lst)

        self.send_update(update_lst)


    def send_img(self, hashkey, sock):
        """
        Send image to node.
        """
        img_name = self.img_map[hashkey][0]
        img_path = os.path.join(self.folder_path, img_name)
        img = Image.open(img_path)
        
        #TODO send image only to node 
        