import pickle

class Protocol:

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
