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


