try:
    import ujson as json
except:
    import json
from collections import namedtuple
#from cnamedtuple import namedtuple

import urllib.request

Node = namedtuple('Node', 'path parent key value')


#all:
#    root=None

#get/find:
#    expand=False
#    context=False

    
#######################################################################################
#   GET
#######################################################################################

def find(obj, path="", root=None, expand=False, context=False):
    if not root:
        root = obj
    parts = splitPath(path)
    for node in _walk2(Node('', None, None, obj), parts, root=root):
        if expand:
            node = Node(node.path, node.parent, node.key, _expand(node.value, root))
        if context:
            yield node
        else:
            yield node.value
        

def get(obj, path="", root=None, expand=False, context=False):
    parts = splitPath(path)
    if '*' in parts:
        raise Exception('No wildcards allowed in getter path!')
        
    return next(find(obj, path, root, expand, context))
 
def splitPath(path):
    parts = path.strip('/').split('/')
    parts = [p for p in parts if p != '']
    # we don't know yet if number keys are strings for dicts or ints for lists
    return parts



def _walk2(node, parts :list, root):
    if not parts:
        yield node
        return
    
    key = parts[0]
    tail = parts[1:]
    current = node.value
    
    if isinstance(current, dict) and '$ref' in current:
        current = _getRef( current, root )
    
    if key != '*':
        path = node.path + '/' + key
        if isinstance(current, list):
            if not key.isdigit():
                return
                #raise Exception("Digits expected in path instead of " + key + " at: " + path)
            key = int(key)
            if key < len(current):
                child = Node(path, current, key, current[key])
                for hit in _walk2(child, tail, root):
                    yield hit
            else:
                return
                #raise Exception("No such path: " + path)
        elif isinstance(current, dict):
            if key in current:
                child = Node(path, current, key, current[key])
                for hit in _walk2(child, tail, root):
                    yield hit
            else:
                return
                #raise Exception("No such path: " + path)
        else:
            raise Exception("Unexpected primitive value at " + node.path)
    
    else: # wildcard
        
        if isinstance(current, list):
            # we need to iterate in reverse in case these get deleted on the fly
            for key in range(len(current)-1,-1,-1):
                path = node.path + '/' + str(key)
                child = Node(path, current, key, current[key])
                for hit in _walk2(child, tail, root):
                    yield hit
        elif isinstance(current, dict):
            for (key, value) in current.items():
                path = node.path + '/' + key
                child = Node(path, current, key, value)
                for hit in _walk2(child, tail, root):
                    yield hit
        else:
            raise Exception("Unexpected primitive value at " + node.path)

# this is a walk without context (parent/key)
# it was used before the need to edit arose
def _walk(parts, obj, pi=0, path=""):
    if pi == len(parts):
        yield (path, obj)
        return
    
    p = parts[pi]
    if p != '*':
        if isinstance(obj,list):
            if not p.isdigit():
                raise "Digits expected in path instead of " + p + " (" + path + ")"
            p = int(p)
            if p < len(obj):
                for item in _walk(parts, obj[p], pi+1, path + '/' + str(p)):
                    yield item
        elif p in obj:
            for item in _walk(parts, obj[p], pi+1, path + '/' + str(p)):
                yield item
    else:
        if isinstance(obj,list):
            for i in range(len(obj)):
                for item in _walk(parts, obj[i], pi+1, path + '/' + str(i)):
                    yield item
        elif isinstance(obj,dict):
            for (key,val) in obj.items():
                for item in _walk(parts, val, pi+1, path + '/' + key):
                    yield item

def _getRef(obj, root):
    assert isinstance(obj, dict) and '$ref' in obj
    if len(obj) != 1:
        raise Exception('Reference object cannot have other attributes: ' + str(obj))
    ref = obj['$ref']
    if ref.startswith('http://') or ref.startswith('https://'):
        # web
        res = urllib.request.urlopen(ref).read()
        return json.loads(res.decode('utf-8'))
    else:
        # local
        return get(root, ref)

def _expand(obj, root, attr=[]):
    if attr:
        pass
    else:
        if isinstance(obj,dict):
            if '$ref' in obj:
                trg = _getRef(obj, root)
                return _expand(trg, root)
            else:
                trg = {}
                for (k,v) in obj.items():
                    trg[k] = _expand(v, root)
                return trg
        elif isinstance(obj,list):
            trg = []
            for val in obj:
                trg.append( _expand(val, root) )
            return trg
        else:
            return obj
    