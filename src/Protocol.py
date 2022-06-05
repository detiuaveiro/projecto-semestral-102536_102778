import pickle

class Protocol:

    @classmethod
    def msg_connect(cls, node_type):
        msg = pickle.dumps({"type": "connect", "node_type": node_type})
        return msg    

    @classmethod
    def msg_request_image(cls, hashkey):
        msg = pickle.dumps({"type": "request", "hashkey": hashkey})
        return msg

    @classmethod
    def msg_image(cls, hashkey, image):
        msg = pickle.dumps({"type": "image", "hashkey": hashkey, "image": image})
        return msg

    @classmethod
    def msg_request_image_list(cls):
        msg = pickle.dumps({"type": "request_list"})
        return msg

    @classmethod
    def msg_image_list(cls, image_list):
        msg = pickle.dumps({"type": "image_list", "image_list": image_list})
        return msg







    @classmethod
    def send_msg(cls, msg, sock):
        msg_size = len(msg).to_bytes(2, "big")
        msg_to_send = msg_size + msg

        print("msg: ", msg_to_send)

        sock.send(msg_to_send)

    @classmethod
    def receive_msg(cls, sock ):
        msg_size= int.from_bytes(sock.recv(2), "big")
        msg = sock.recv(msg_size)
        
        #decode msg and return
        return pickle.loads(msg)



