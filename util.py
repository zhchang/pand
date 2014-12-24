import os

def get_os_path(base,sub):
    levels = []
    if isinstance(sub,list):
        levels += sub
    else:
        levels.append(sub)
    result = base
    for level in levels:
        result = os.path.join(base,level)
        base = result
    return result

def print_help(functions):
    l = []
    l += functions
    outputs = []
    for thing in l:
        if thing.startswith('do_'):
            outputs.append(thing[3:])
    print 'avaialbe commands:'
    for output in outputs:
        print output


