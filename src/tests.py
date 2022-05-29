from PIL import Image
import imagehash
hash = imagehash.average_hash(Image.open('../images/_019_Aveiro.png'))

print(hash)