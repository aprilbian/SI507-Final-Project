import json
from prettytable import PrettyTable

language_table = ['Simplified Chinese', 'English', 'French', 'Russian', 'Japanese']

CACHE_FILE_NAME = 'cache.json'
num_entry = 15

def open_cache():
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

cache_dict = open_cache()
cache_list = []
for k in cache_dict.keys():
    cache_list.append(cache_dict[k])

del(cache_list[-1])


x= PrettyTable(['Simplified Chinese', 'English', 'French', 'Russian', 'Japanese'])
def construct_graph():
    cur_dicts = cache_list
    num_lang = len(language_table)
    for n in range(num_entry):
        row_info = [0 for i in range(num_lang)]
        for l in range(num_lang):
            lang_l = language_table[l]
            if (cur_dicts[n]['language_options'].find(lang_l)>=0):
                row_info[l] = 1
        x.add_row(row_info)
    print(x)

# the bipartite graph, we can print it
# using the adjacent matrix representation
construct_graph()

# The tree can be constructed via the list,
# However, as we do not perform very complex operations
# using the tree structure, there is no need to construct
# the tree to store the information, just keep the information
# as lists is enough.
item = cache_dict['https://store.steampowered.com/app/1527950']
for key,value in item.items():
    print(key,':',value)
