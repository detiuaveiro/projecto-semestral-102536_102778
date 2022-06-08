from Functions2 import Functions as f

x = f()



# { hashkey: (img_name, num_colors, num_pixeis, num_bytes) } 

# x.img_map= {'hash1': ( 70001, 100000, 23000)}

# # # { hashkey: [ (address1, port1), (address2, port2), num_colors, num_pixeis, num_bytes ] }

# x.general_map= {'hash1': [('localhost', 5001), ('localhost', 5000), 70001, 100000, 23000], 'hash2': [('localhost', 5001), ('localhost', 5002), 70001, 120000, 43000]}

x.nodes_imgs= {('localhost', 5001): ['hash1', 'hash2'], ('localhost', 5002): ['hash2']}
x.storage= {('localhost', 5001): 100000, ('localhost', 5002): 120000}

# x.handle_disconect(('localhost', 5001))

# for item in x.storage.items():
#     print(item)

# x.starting_img_list()
print(x.img_map)
x.merge_my_img()

for item in x.general_map.items():
    print(item)

for item in x.storage.items():
    print(item)