from Functions import Functions as f

folder='../node0'
# folder='../images'

img_map= f.starting_img_list(folder)

print(f.occupied_space(folder))