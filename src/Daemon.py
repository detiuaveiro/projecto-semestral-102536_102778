import socket
import queue
import selectors
import pickle
from .Protocol import Protocol as P
from PIL import Image
import imagehash
import os
import time


class Daemon:
    """Daemon -> Node"""


    def __init__(self, folder_path):
        self.canceled = False
        self.node_type = "daemon"
        self.central_node = self.find_central_node()
        self.host, self.port = self.get_addr()  # reveiving socket (endpoint)

        self.client = None

        # self.merge_done=False
        self.can_merge = False

        self.folder_path = folder_path
        self.my_node = (self.host, self.port)
        self.general_map = {}
        self.storage = {}
        self.nodes_imgs = {}
        self.img_map = {}
        self.all_nodes = [self.my_node]
        self.all_socks = {}
        self.imgs_to_send = None 

        self.sel = selectors.DefaultSelector()

        # receiving socket
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((self.host, self.port))
        self.s.listen()

        print(f"Clients can connect via: {self.host} {self.port}")

        self.starting_img_list()

        self.imgs_to_send = queue.Queue(len(self.img_map))

        self.imgs_to_backup = []
        self.need_backup= False

        for hashkey in self.img_map.keys():
            self.imgs_to_send.put(hashkey)
        
        self.sel.register(self.s, selectors.EVENT_READ, self.verify)


        # connect to central daemon
        if self.port != self.central_node[1]:  #i'm not the central node

            self.all_socks[self.central_node] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.all_socks[self.central_node].connect(self.central_node)
            self.all_nodes.append(self.central_node)

            #connect to central node
            connect_msg = P.msg_first_connect(self.node_type, self.host, self.port)
            P.send_msg(connect_msg, self.all_socks[self.central_node])


            #register daemon socket
            self.sel.register(self.all_socks[self.central_node], selectors.EVENT_READ, self.read)


            print("-------------------")
            for n in self.all_socks.keys():
                print(n)
            print("-------------------")

    

    def verify(self, sock, mask):
        conn, addr = sock.accept()
        connect_msg = P.receive_msg(conn)

        if connect_msg:
            print("msg recv: ", connect_msg)
            host = connect_msg["recv_host"]
            port = connect_msg["recv_port"]
            node_type = connect_msg["node_type"]
            connect_type = connect_msg["type"]

            if node_type == "daemon":
                print("DEAMON WANTS TO CONNECT")

                if connect_type == "first_connect":

                    # send to my neighbour all the nodes i know
                    nodes_msg = P.msg_connect_ack(self.all_nodes[1:], self.general_map)
                    P.send_msg(nodes_msg, conn)


                #store the neighbour node
                self.add_new_node((host, port), conn)
                

                print("-------------------")
                for n in self.all_socks.keys():
                    print(n)
                print("-------------------")

                # if not self.merge_done:
                #     self.merge_my_img()
                #     self.merge_done = True
                self.can_merge = True
                

            if node_type == "client":
                print("CLIENT WANTS TO CONNECT")

                #store the node client
                self.client = conn

            
            # print(self.all_socks)
            self.sel.register(conn, selectors.EVENT_READ, self.read)



    def read(self, sock :socket, mask):
        
        msg = P.receive_msg(sock)

        #print("Msg type: ", msg["type"])

        if msg:
            msg_type = msg["type"]

            if msg_type == "connect_ack":
                nodes = msg["nodes"]  # array with neighbour nodes
                self.general_map = msg["general_map"]
                print("General map received: ", self.general_map)
                self.connect_to_nodes(nodes)
                self.all_nodes += nodes
                self.starting_updates()
                print(self.all_nodes)
                print(self.storage)
                # self.merge_my_img()
                # self.merge_done = True
                self.can_merge = True

            elif msg_type == "request_list":
                if len(self.general_map) == 0:
                    request_msg = P.msg_image_list(list(self.img_map.keys()))
                else:
                    request_msg = P.msg_image_list(list(self.general_map.keys()))

                P.send_msg(request_msg, sock)

            elif msg_type == "update":
                self.update_data(msg["update"])

            elif msg_type == "image_backup":
                self.save_img(msg["image"], msg["update"])

            elif msg_type == "debug":
                debug_request_msg = P.msg_debug_ack(self.general_map, self.all_nodes, self.storage)
                P.send_msg(debug_request_msg, self.client)
                print("debug message sent")

            elif msg_type == "request":
                self.client_request(msg["hashkey"], sock)

            elif msg_type == "request_ack":
                msg= P.msg_request_image_ack(msg["image"])
                P.send_msg(msg, self.client)

            else:
                print("ALERT: unknow message received!")


        else:
            self.sel.unregister(sock)
            sock.close()

            for node in self.all_socks.keys():
                if self.all_socks[node] == sock:
                    self.handle_disconect(node)
                    break

            
            

            #find my new central node (could be me!)
            # if sock in self.all_socks.values() and sock == self.all_socks[self.central_node]:
            #     self.central_node = self.find_central_node()
            #     print("New central node: ", self.central_node)

            # #remove socket from all_socks
            # if sock in self.all_socks.values():
            #     self.remove_node(sock)



    def run(self):
        """ Run until canceled """

        while not self.canceled:

            events = self.sel.select(0) 
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)

            if len(events) == 0:
                self.stuff_to_do()



    def stuff_to_do(self):
        """ Check if there is stuff to do """

        if self.can_merge and not self.imgs_to_send.empty():
                hashkey = self.imgs_to_send.get()
                self.merge_img(hashkey)

        if self.need_backup and len(self.imgs_to_backup) > 0 and len(self.all_nodes) > 1:
            hashkey= self.imgs_to_backup.pop()
            print("Remaking backup for: ", hashkey)
            self.backup_and_update(hashkey)
            if len(self.imgs_to_backup) == 0:
                self.need_backup = False



    def connect_to_nodes(self, nodes):
        """ connect to other nodes """

        for n in nodes:
            if n not in self.all_socks and n != self.my_node:

                self.all_socks[n] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                print("Connecting to ", n)
                self.all_socks[n].connect(n)

                #connect to node
                connect_msg = P.msg_connect(self.node_type, self.host, self.port)
                print("Connect to daemon port: ", n[1])
                P.send_msg(connect_msg, self.all_socks[n])

                #register daemon socket
                self.sel.register(self.all_socks[n], selectors.EVENT_READ, self.read)          

        
        print("-------------------")
        for n in self.all_socks.keys():
            print(n)
        print("-------------------")



    def get_addr(self):
        """ Get a valid addr to use """

        host = "localhost"
        port = 5000   #start port

        while self.is_port_in_use(port):
            port += 1

        return (host, port)

    

    def find_central_node(self):
        """ Return the addr of an existing daemon node """

        host = 'localhost'
        port = 5000
        total_ports = 100  #total ports to check 5000 -> 5100

        for _ in range(total_ports):
            if self.is_port_in_use(port):
                print("There is already a node")
                break
            else:
                port += 1
        
        if port == 5100:  #if there is no centra node
            port = 5000
        
        # print("Central node: ", (host, port))
        return (host, port)  # return ('locahost', 5000) if there are no daemon nodes



    def is_port_in_use(self, port: int) -> bool:
        """ Check if port is in use """       

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0



    def remove_node(self, s):
        node_to_delete = None
        for node, sock in self.all_socks.items():
            if s == sock:
                node_to_delete = node
        
        #remove the node
        del self.all_socks[node_to_delete]



    def is_better(self, num_colors1, num_colors2, num_pixeis1, num_pixeis2, num_bytes1, num_bytes2, port1, port2):
        """
        Compare two images and return True if img1 is better than img2.
        """
        n_colors=70000

        if num_colors1 == num_colors2 and num_pixeis1 == num_pixeis2:
            return port1 <= port2

        if (num_colors1 > n_colors) == (num_colors2 > n_colors):
            return num_pixeis1 > num_pixeis2
        
        if num_colors1 > n_colors:
            return num_pixeis1 > 0.7*num_pixeis2

        if num_colors2 > n_colors:
            return 0.7*num_pixeis1 > num_pixeis2
        


    def delete_file(self, hashkey):
        """
        Delete image from disk.
        """
        img_path = os.path.join(self.folder_path, hashkey)
        # os.remove(img_path)
        print("Deleted:", img_path)

    

    def rename_file(self, img_name, hashkey):
        """
        Rename image to hashkey.
        """
        img_path = os.path.join(self.folder_path, img_name)
        os.rename(img_path, os.path.join(self.folder_path, hashkey))
        print("Renamed to: ", hashkey)

    

    def save_file(self, img, hashkey):
        """
        Save image to disk.
        """
        # print("Saving: ", hashkey)
        # img.show()
        img_path = os.path.join(self.folder_path, hashkey)
        img.save(img_path, format="PNG")
        os.rename(img_path, os.path.join(self.folder_path, hashkey))
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

            if hash not in self.img_map:
                print("New image:", img_path)
                self.img_map[hash]= (num_colors, num_pixeis, num_bytes)
                self.rename_file(img_name, hash)

            elif self.is_better(num_colors, self.img_map[hash][0], num_pixeis, self.img_map[hash][1], num_bytes, self.img_map[hash][2], self.port, 4999):
                print("Better image found: ", img_path)
                self.delete_file(hash)
                self.img_map[hash] = (num_colors, num_pixeis, num_bytes)
                self.rename_file(img_name, hash)

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
        if node == self.my_node:
            return
        self.all_nodes.append(node)
        self.all_socks[node] = sock
        self.storage[node] = 0
        self.nodes_imgs[node] = []
        print("\nNew node joined: ", node, "\n")


    
    def update_data(self, update):
        """
        Update general_map and storage.
        """
        if update[0] != self.my_node:
            if update[0] not in self.storage:
                self.storage[update[0]] = 0
            if update[0] not in self.nodes_imgs:
                self.nodes_imgs[update[0]] = []
        if update[1] != self.my_node:
            if update[1] not in self.storage:
                self.storage[update[1]] = 0
            if update[1] not in self.nodes_imgs:
                self.nodes_imgs[update[1]] = []

        if update[5] not in self.general_map:
            print("Update recived with new image: ", update[5])
            if update[0] in self.all_nodes[1:]:
                self.storage[update[0]] += update[4]
                self.nodes_imgs[update[0]].append(update[5])
            if update[1] in self.all_nodes[1:]:
                self.storage[update[1]] += update[4]
                self.nodes_imgs[update[1]].append(update[5])
            self.general_map[update[5]] = update[0:5]

        elif self.is_better(update[2], self.general_map[update[5]][2], update[3], self.general_map[update[5]][3], update[4], self.general_map[update[5]][4], update[0], self.general_map[update[5]][0]):
            print("Update recived with better image: ", update[5])
            val = self.general_map[update[5]]
            if val[0] in self.all_nodes[1:]:
                self.storage[val[0]] -= val[4]
                self.nodes_imgs[val[0]].remove(update[5])
            if val[1] in self.all_nodes[1:]:
                self.storage[val[1]] -= val[4]
                self.nodes_imgs[val[1]].remove(update[5])
            if update[0] in self.all_nodes[1:]:
                self.storage[update[0]] += update[4]
                self.nodes_imgs[update[0]].append(update[5])
            if update[1] in self.all_nodes[1:]:
                self.storage[update[1]] += update[4]
                self.nodes_imgs[update[1]].append(update[5])

            if update[0] == self.my_node or update[1] == self.my_node:
                self.delete_file(update[5])
            self.general_map[update[5]] = update[0:5]

        else:
            print("Update recived with worse image: ", update[5])



    def backup_node(self, hashkey):
        """
        Choose the best node to backup the image.
        Send the image and update self.storage.
        """
        if hashkey in self.general_map:
            val = self.general_map[hashkey]
            if val[0] in self.all_nodes[1:]:
                self.storage[val[0]] -= val[4]
                self.nodes_imgs[val[0]].remove(hashkey)
            if val[0] in self.all_nodes[1:]:
                self.storage[val[1]] -= val[4]
                self.nodes_imgs[val[1]].remove(hashkey)

        backup_node= min(self.storage, key=self.storage.get)

        self.storage[backup_node] += self.img_map[hashkey][2]
        self.nodes_imgs[backup_node].append(hashkey)

        return backup_node



    def save_img(self, img, update):
        """
        Save image if is better
        """
        if update[5] not in self.general_map:
            print("Backup new image: ", update[5])
            self.img_map[update[5]] = update[2:5].copy()
            self.save_file(img, update[5])

        elif self.is_better(update[2], self.general_map[update[5]][2], update[3], self.general_map[update[5]][3], update[4], self.general_map[update[5]][4], update[0], self.general_map[update[5]][0]):
            print("Backup better image: ", update[5])
            if update[5] in self.img_map:
                self.delete_file(update[5])
            self.img_map[update[5]] = update[2:5].copy()
            self.save_file(img, update[5])

        else:
            print("Backup worse image: ", update[5])



    def send_update(self, hashkey):
        """
        Send update to all nodes
        """
        update= self.general_map[hashkey].copy()
        update.append(hashkey)

        for sock in self.all_socks.values():
            update_msg = P.msg_update(update)
            P.send_msg(update_msg, sock)

        print("Update sent to all nodes")

    

    def send_img(self, hashkey, node):
        """
        Send image to all nodes.
        """
        img_path = os.path.join(self.folder_path, hashkey)
        img = Image.open(img_path)
        update= self.general_map[hashkey].copy()
        update.append(hashkey)

        msg =  P.msg_image(update, img)
        P.send_msg(msg, self.all_socks[node])
    
        print("Image sent to: ", node)



    def backup_and_update(self, hashkey):
        """
        Backup image to best node and send update.
        """
        backup_node = self.backup_node(hashkey)
        self.general_map[hashkey] = [self.my_node, backup_node, self.img_map[hashkey][0], self.img_map[hashkey][1], self.img_map[hashkey][2]]
        self.send_update(hashkey)
        self.send_img(hashkey, backup_node)



    def merge_img(self, hashkey):
        """
        Merge img with genereal_map.
        """
        
        if len(self.all_nodes) == 1:
            self.can_merge = False
            return  

        if hashkey not in self.general_map:
                print("New image:", hashkey)
                self.backup_and_update(hashkey)
                      
        elif self.is_better(self.img_map[hashkey][0], self.general_map[hashkey][2], self.img_map[hashkey][1], self.general_map[hashkey][3], self.img_map[hashkey][2], self.general_map[hashkey][4], self.port, 4999):
            print("Better image found: ", hashkey)
            self.backup_and_update(hashkey)
            
        else:
            print("Worse image found: ", hashkey)
            self.delete_file(hashkey)
            self.img_map.pop(hashkey)

    
    
    def handle_disconect(self, node):
        """
        Re-send backup images if node dies, update self.general_map and self.storage.
        """
        print("\nNode disconnected: ", node, "\n")

        if node in self.all_nodes[1:]:
            self.all_nodes.remove(node)
        self.all_socks.pop(node)

        if self.central_node == node:
            
            self.central_node= self.my_node
            for node_ in self.all_nodes[1:]:
                if self.central_node[1] > node_[1]:
                    self.central_node = node_
            print("New central node: ", self.central_node)
        
        self.storage.pop(node)

        nodes_imgs_copy = self.nodes_imgs.copy()
        self.nodes_imgs.pop(node)
        

        for hashkey in nodes_imgs_copy[node]:
            if hashkey in self.img_map:
                self.imgs_to_backup.append(hashkey)
        
        if len(self.imgs_to_backup) > 0:
            self.need_backup = True

        #     # TODO UPDATE DATA EVERYTIME WE GET AN UPDATE

        #     if node in self.all_nodes:
        #         self.storage[node] = []
        #         for hash in self.nodes_imgs[node][self.nodes_imgs[node].index(hashkey):]:
        #             self.storage[node] += self.general_map[hash][2]
        #         return

            # if hashkey in self.img_map:
            #     print("Remaking backup for: ", hashkey)
            #     self.backup_and_update(hashkey)

        


    def client_request(self, hashkey, conn):
        """
        Send image to client.
        """
        print("Image requested: ", hashkey)

        if hashkey in self.img_map:
            print("Image found: ", hashkey)
            msg = P.msg_request_image_ack(Image.open(os.path.join(self.folder_path, hashkey)))
            P.send_msg(msg, conn)
            return

        if hashkey not in self.general_map:
            print("Image not found: ", hashkey)
            msg = P.msg_request_image_ack(None)
            P.send_msg(msg, conn)
            return 
            
        #TODO request image to self.all_socks[self.general_map[hashkey][0]]
        print("Requesting image: ", hashkey)
        msg = P.msg_request_image(hashkey)
        P.send_msg(msg, self.all_socks[self.general_map[hashkey][0]])
        

