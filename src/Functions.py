from PIL import Image
import imagehash
import glob

class Functions:

    @classmethod
    def put_image(cls, hashkey_dict, hash, num_pixeis, is_colored, myConnTup, OtherConnTups):

        # TODO choose a peer to send the backup image to based on the number of images they already have

        otherTup = ("adress", "port")

        hashkey_dict[hash]= [myConnTup, otherTup, num_pixeis, is_colored]


    @classmethod
    def my_images(cls, folder_path, hashkey_dict, myConnTup, OtherConnTups):

        # { hashkey: [(address, port), (address, port), num_pixeis, is_colored] }

        my_img_list={}

        imageList= glob.glob(folder_path+'/*')

        for imgPath in imageList:
            img = Image.open(imgPath)
            hash = str(imagehash.average_hash(img))

            try:
                is_colored= len(set(img.getdata()))> 65536
                size= img.size
                num_pixeis= size[0]*size[1]
            except:
                print("Error: ", imgPath)
                #TODO delete image 
                continue

            if hash not in hashkey_dict.keys():
                cls.put_image(hashkey_dict, hash, num_pixeis, is_colored, myConnTup, OtherConnTups)
                my_img_list.put(hash, imgPath)

            else:
                current_image= hashkey_dict[hash]

                if is_colored:

                    if num_pixeis > current_image[2]:

                        cls.put_image(hashkey_dict, hash, num_pixeis, is_colored, myConnTup, OtherConnTups)
                        my_img_list.put(hash, imgPath)
                        #TODO delete image from old peers

                    elif current_image[3] and num_pixeis > 0.9*current_image[2]:
                        
                        cls.put_image(hashkey_dict, hash, num_pixeis, is_colored, myConnTup, OtherConnTups)
                        my_img_list.put(hash, imgPath)
                        #TODO delete image from old peers

                    else:
                        #TODO delete image
                        continue
                else:

                    if not current_image[3] and num_pixeis > current_image[2]:

                        cls.put_image(hashkey_dict, hash, num_pixeis, is_colored, myConnTup, OtherConnTups)
                        my_img_list.put(hash, imgPath)
                        #TODO delete image from old peers
                    
                    elif current_image[3] and 0.9*num_pixeis > current_image[2]:

                        cls.put_image(hashkey_dict, hash, num_pixeis, is_colored, myConnTup, OtherConnTups)
                        my_img_list.put(hash, imgPath)
                        #TODO delete image from old peers

                    else:
                        #TODO delete image
                        continue
                    
        pass
        