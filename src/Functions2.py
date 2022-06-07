from PIL import Image
import imagehash
import os

class Functions:
    def __init__(self):

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

    
    def rename_file(self, folder_path, img_name, hashkey):
        """
        Rename image to hashkey.
        """
        img_path = os.path.join(folder_path, img_name)
        os.rename(img_path, os.path.join(folder_path, hashkey + img_name.split('.')[-1]))
        print("Renamed to: ", hashkey + img_name.split('.')[-1])

    
    def save_file(self, img, hashkey, extension):
        """
        Save image to disk.
        """
        img_path = os.path.join(self.folder_path, hashkey + extension)
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
                self.img_map[hash]= (img_name, num_colors, num_pixeis, num_bytes)
                self.rename_file(self.folder_path, img_name, hash)

            elif self.is_better(num_colors, self.img_map[hash][1], num_pixeis, self.img_map[hash][2]):
                print("Better image found: ", img_path)
                self.delete_file(self.img_map[hash][0])
                self.img_map[hash] = (img_name, num_colors, num_pixeis, num_bytes)
                self.rename_file(self.folder_path, img_name, hash)

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

    
    def update_data(self, update):
        """
        Update general_map and storage.
        """
        if self.general_map.get(update[5]) is not None:
            val= self.general_map[update[5]]
            if val[0] != self.my_node:
                self.storage[val[0]] -= val[4]
            if val[1] != self.my_node:
                self.storage[val[1]] -= val[4]

        self.general_map[update[5]] = update[0:5]

    

        
