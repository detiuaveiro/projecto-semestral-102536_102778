import socket
import selectors
from .Protocol import Protocol as P
from PIL import Image
import imagehash
import os


class Daemon:
    """Daemon -> Node"""
    def __init__(self, folder_path):
        """ Init """

        self.folder_path = folder_path
        self.can_merge = False
        self.canceled = False
        self.node_type = "daemon"
        self.client = None

        self.general_map = {}
        self.storage = {}
        self.nodes_imgs = {}
        self.my_imgs = {}
        self.all_nodes = []
        self.all_socks = {}

        self.host, self.port = self.get_addr()
        self.my_node = (self.host, self.port)

        self.sel = selectors.DefaultSelector()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((self.host, self.port))
        self.s.listen()
        print(f"Clients can connect via: {self.host} {self.port}")


        self.starting_img_list()
        self.imgs_to_send = list(self.my_imgs.keys())


        self.sel.register(self.s, selectors.EVENT_READ, self.verify)

        self.central_node = self.find_central_node()

        if self.port != self.central_node[1]:  #i'm not the central node
            self.join_mesh()



    def run(self):
        """ Run until canceled """

        while not self.canceled:

            events = self.sel.select(0) 
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)

            if len(self.all_nodes) == 0:
                self.can_merge = False

            if len(events) == 0:
                self.stuff_to_do()



    def stuff_to_do(self):
        """ Check if there is stuff to do """

        if self.can_merge and len(self.imgs_to_send) > 0:
            self.merge_img(self.imgs_to_send.pop(0))
        



    def join_mesh(self):
        """
        Join the mesh.
        """
        self.all_socks[self.central_node] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.all_socks[self.central_node].connect(self.central_node)
        self.all_nodes.append(self.central_node)

        #connect to central node
        connect_msg = P.msg_first_connect(self.node_type, self.host, self.port)
        P.send_msg(connect_msg, self.all_socks[self.central_node])

        #register daemon socket
        self.sel.register(self.all_socks[self.central_node], selectors.EVENT_READ, self.read)

        print("Connected to central node")



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



    def get_addr(self):
        """ Get a valid addr to use """

        host = "localhost"
        port = 5000   #start port

        while self.is_port_in_use(port):
            port += 1

        return (host, port)



    def is_port_in_use(self, port: int) -> bool:
        """ Check if port is in use """       

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0



    def is_better(self, num_colors1, num_colors2, num_pixeis1, num_pixeis2, num_bytes1, num_bytes2, port1, port2):
        """
        Compare two images and return True if img1 is better than img2.
        """
        n_colors=70000

        # if num_colors1 == num_colors2 and num_pixeis1 == num_pixeis2 and num_bytes1 == num_bytes2:
        #     return port1 < port2

        # if  num_colors1 == num_colors2 and num_pixeis1 == num_pixeis2:
        #     return num_bytes1 < num_bytes2

        if num_colors1 == num_colors2 and num_pixeis1 == num_pixeis2:
            return port1 < port2

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
        if "node" in img_path:
            os.remove(img_path)
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

            if hash not in self.my_imgs:
                print("[local] New image:", img_path)
                self.my_imgs[hash]= (num_colors, num_pixeis, num_bytes)
                self.rename_file(img_name, hash)

            elif self.is_better(num_colors, self.my_imgs[hash][0], num_pixeis, self.my_imgs[hash][1], num_bytes, self.my_imgs[hash][2], self.port, 4999):
                print("[local] Better image found: ", img_path)
                self.delete_file(hash)
                self.my_imgs[hash] = (num_colors, num_pixeis, num_bytes)
                self.rename_file(img_name, hash)

            else:
                print("[local] Worse image found: ", img_path)
                self.delete_file(img_name)

    

    def starting_updates(self):
        """
        Update storage occupied space in bytes.
        And images per node.
        """

        for node in self.all_nodes:
            self.storage[node] = 0
            self.nodes_imgs[node] = []

        for key, val in self.general_map.items():
            if val[0] != self.my_node:
                self.storage[val[0]] += val[4]
                self.nodes_imgs[val[0]].append(key)
            if val[1] != self.my_node:
                self.storage[val[1]] += val[4]
                self.nodes_imgs[val[1]].append(key)

        print("\nStarting updates done\n")

    

    def get_storage(self):
        """
        Storage values for all nodes including this one
        """

        new_storage = {}
        for val in self.general_map.values():
            if val[0] not in new_storage:
                new_storage[val[0]] = 0
            new_storage[val[0]] += val[4]
            if val[1] not in new_storage:
                new_storage[val[1]] = 0
            new_storage[val[1]] += val[4]

        return new_storage


    
    def add_new_node(self, node, sock):
        """
        Add new node.
        """
        # if node == self.my_node:
        #     return
        self.all_nodes.append(node)
        self.all_socks[node] = sock
        self.storage[node] = 0
        self.nodes_imgs[node] = []
        print("\nNew node joined: ", node, "\n")


    
    def connect_to_nodes(self, nodes):
        """ 
        connect to other nodes 
        """
        for node in nodes:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("Connecting to ", node)
            sock.connect(node)
            self.add_new_node(node, sock)
            #connect to node
            connect_msg = P.msg_connect(self.node_type, self.host, self.port)
            print("Connect to daemon port: ", node[1])
            P.send_msg(connect_msg, self.all_socks[node])
            #register daemon socket
            self.sel.register(self.all_socks[node], selectors.EVENT_READ, self.read)



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
            print("Update received with new image: ", update[5])
            if update[0] != self.my_node:
                self.storage[update[0]] += update[4]
                self.nodes_imgs[update[0]].append(update[5])
            if update[1] != self.my_node:
                self.storage[update[1]] += update[4]
                self.nodes_imgs[update[1]].append(update[5])
                
            self.general_map[update[5]] = update[0:5]

        elif self.is_better(update[2], self.general_map[update[5]][2], update[3], self.general_map[update[5]][3], update[4], self.general_map[update[5]][4], update[0], self.general_map[update[5]][0]):
            print("Update received with better image: ", update[5])
            val = self.general_map[update[5]]
            if val[0] != self.my_node:
                self.storage[val[0]] -= val[4]
                self.nodes_imgs[val[0]].remove(update[5])
            if val[1] != self.my_node:
                self.storage[val[1]] -= val[4]
                self.nodes_imgs[val[1]].remove(update[5])
            if update[0] != self.my_node:
                self.storage[update[0]] += update[4]
                self.nodes_imgs[update[0]].append(update[5])
            if update[1] != self.my_node:
                self.storage[update[1]] += update[4]
                self.nodes_imgs[update[1]].append(update[5])

            if update[0] == self.my_node or update[1] == self.my_node:
                self.delete_file(update[5])
                self.my_imgs.pop(update[5])

            self.general_map[update[5]] = update[0:5]

        else:
            print("Update received with worse image: ", update[5])



    def backup_node(self, hashkey):
        """
        Choose the best node to backup the image.
        Send the image and update self.storage.
        """
        if hashkey in self.general_map:
            val = self.general_map[hashkey]
            if val[0] != self.my_node:
                self.storage[val[0]] -= val[4]
                self.nodes_imgs[val[0]].remove(hashkey)
            if val[1] != self.my_node:
                self.storage[val[1]] -= val[4]
                self.nodes_imgs[val[1]].remove(hashkey)

        backup_node= min(self.storage, key=self.storage.get)

        self.storage[backup_node] += self.my_imgs[hashkey][2]
        self.nodes_imgs[backup_node].append(hashkey)

        return backup_node
        

    
    def save_img(self, img, update):
        """
        Save image if is better
        """
        if update[5] not in self.general_map:
            print("Backup received new image: ", update[5])
            self.my_imgs[update[5]] = update[2:5]
            self.save_file(img, update[5])

        elif self.is_better(update[2], self.general_map[update[5]][2], update[3], self.general_map[update[5]][3], update[4], self.general_map[update[5]][4], update[0], self.general_map[update[5]][0]):
            print("Backup received better image: ", update[5])
            if update[5] in self.my_imgs:
                self.delete_file(update[5])
            self.my_imgs[update[5]] = update[2:5]
            self.save_file(img, update[5])

        else:
            print("Backup received worse image: ", update[5])



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



    def backup_and_update(self, hashkey):
        """
        Backup image to best node and send update.
        """
        backup_node = self.backup_node(hashkey)
        self.general_map[hashkey] = [self.my_node, backup_node, self.my_imgs[hashkey][0], self.my_imgs[hashkey][1], self.my_imgs[hashkey][2]]
        self.send_img(hashkey, backup_node)
        self.send_update(hashkey)



    def merge_img(self, hashkey):
        """
        Merge img with genereal_map.
        """
        if hashkey not in self.my_imgs:
            return

        if hashkey not in self.general_map:
            print("New image to send:", hashkey)
            self.backup_and_update(hashkey)
                      
        elif self.is_better(self.my_imgs[hashkey][0], self.general_map[hashkey][2], self.my_imgs[hashkey][1], self.general_map[hashkey][3], self.my_imgs[hashkey][2], self.general_map[hashkey][4], self.port, 4999):
            print("Better image to send: ", hashkey)
            self.backup_and_update(hashkey)
            
        else:
            print("Worse image to send: ", hashkey)
            if self.general_map[hashkey][0] != self.my_node and self.general_map[hashkey][1] != self.my_node: 
                self.delete_file(hashkey)
                self.my_imgs.pop(hashkey)



    def handle_disconnect(self, node):
        """
        Re-send backup images if node dies, update self.general_map and self.storage.
        """
        print("\nNode disconnected: ", node, "\n")

        self.all_nodes.remove(node)
        self.all_socks.pop(node)
        
        if self.central_node == node:
            self.central_node= self.my_node
            for node_ in self.all_nodes:
                if self.central_node[1] > node_[1]:
                    self.central_node = node_
            print("New central node: ", self.central_node)
        

        for hashkey in self.nodes_imgs[node].copy():

            val = self.general_map[hashkey]
            if val[0] != self.my_node:
                self.storage[val[0]] -= val[4]
                self.nodes_imgs[val[0]].remove(hashkey)
            if val[1] != self.my_node:
                self.storage[val[1]] -= val[4]
                self.nodes_imgs[val[1]].remove(hashkey)
                
            self.general_map.pop(hashkey)

            if hashkey in self.my_imgs:
                self.imgs_to_send.append(hashkey)


        self.storage.pop(node)
        self.nodes_imgs.pop(node)



    def client_request(self, hashkey, conn):
        """
        Send image to client.
        """
        print("Image requested: ", hashkey)

        if hashkey in self.my_imgs:
            print("Image found: ", hashkey)
            msg = P.msg_request_image_ack(Image.open(os.path.join(self.folder_path, hashkey)))
            P.send_msg(msg, conn)
            return

        if hashkey not in self.general_map:
            print("Image not found: ", hashkey)
            msg = P.msg_request_image_ack(None)
            P.send_msg(msg, conn)
            return 
            
        print("Requesting image: ", hashkey)
        msg = P.msg_request_image(hashkey)
        P.send_msg(msg, self.all_socks[self.general_map[hashkey][0]])


    
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
                    nodes_msg = P.msg_connect_ack(self.all_nodes)
                    P.send_msg(nodes_msg, conn)

                #store the neighbour node
                self.add_new_node((host, port), conn)           

            if node_type == "client":
                print("CLIENT WANTS TO CONNECT")
                #store the node client
                self.client = conn

            self.sel.register(conn, selectors.EVENT_READ, self.read)



    def read(self, sock :socket, mask):
        
        msg = P.receive_msg(sock)

        #print("Msg type: ", msg["type"])

        if msg:
            msg_type = msg["type"]

            if msg_type == "connect_ack":
                nodes = msg["nodes"]  # array with neighbour nodes
                self.connect_to_nodes(nodes)

                msg = P.req_general_map()
                P.send_msg(msg, self.all_socks[self.central_node])


                print("-------------------------------")
                for n in self.all_nodes:
                    print(n)
                print("-------------------------------")

            elif msg_type == "general_map":
                # general_map_received = msg["general_map"]
                # general_map_received.update(self.general_map)
                # self.general_map = general_map_received.copy()
                self.general_map.update(msg["general_map"])
                self.starting_updates()
                self.can_merge = True

            elif msg_type == "req_general_map":
                msg= P.msg_general_map(self.general_map)
                P.send_msg(msg, sock)
                self.can_merge = True
                

            elif msg_type == "request_list":
                if len(self.general_map) == 0:
                    request_msg = P.msg_image_list(list(self.my_imgs.keys()))
                else:
                    request_msg = P.msg_image_list(list(self.general_map.keys()))

                P.send_msg(request_msg, sock)

            elif msg_type == "update":
                self.update_data(msg["update"])

            elif msg_type == "image_backup":
                self.save_img(msg["image"], msg["update"])

            elif msg_type == "debug":
                debug_request_msg = P.msg_debug_ack(self.general_map, self.all_nodes, self.storage, self.get_storage())
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

            for node in self.all_nodes:
                if self.all_socks[node] == sock:
                    self.handle_disconnect(node)
                    break

