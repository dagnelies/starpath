try:
    import ujson as json
except:
    import json
from collections import namedtuple
import urllib.request
#from cnamedtuple import namedtuple

import urllib.request

Node = namedtuple('Node', 'path parent key value')

hook_before = None
hook_after = None


def find(obj, path="", root=None, expand=False, context=False, filt=None, strict=False):
    if not root:
        root = obj
    parts = splitPath(path)
    
    for node in _walk(Node('', None, None, obj), parts, expander=DEFAULTexpandER(root), strict=strict):
        if filt and not filt(node):
            continue
        if expand:
            value=expand(node.value, root, expand)
            node = Node(node.path, node.parent, node.key, value)
        if context:
            yield node
        else:
            yield node.value

def get(obj, path="", root=None, expand=False, context=False):
    parts = splitPath(path)
    if '*' in parts:
        raise Exception('No wildcards allowed in getter path!')
        
    return next(find(obj, path, root, expand, context, strict=True))
 
def splitPath(path):
    parts = path.strip('/').split('/')
    parts = [p for p in parts if p != '']
    # we don't know yet if number keys are strings for dicts or ints for lists
    return parts



def _walk(node, parts, expander, strict=False):
    """Walks down the tree according to the path.
    parts -- the path split in a list of strings
    expander -- when a reference node is encountered, the expander will be called like expander(ref) and expects the node's value in return. If None, nodes will not be expanded.
    """
    if hook_before:
        hook_before(node)
    
    if not parts:
        yield node
    else:
        key = parts[0]
        tail = parts[1:]
        current = node.value
        
        if expander and isRef(current):
            current = expander( current['$ref'] )
        
        if isinstance(current, list):
            if key == '*':
                keys = range(len(current)-1,-1,-1) # we need to iterate in reverse in case these get deleted on the fly
            else:
                if not key.isdigit():
                    if strict:
                        raise Exception("Digits expected in path instead of '" + key + "' at: " + node.path)
                    else:
                        return
                n = int(key)
                if n >= len(current):
                    if strict:
                        raise Exception("No such index at path: %s/%d" % (node.path, n))
                    else:
                        return
                keys = [ n ]
        elif isinstance(current, dict):
            if key == '*':
                keys = current.keys()
            elif key not in current:
                if strict:
                    raise Exception("No such path: " + node.path + "/" + key)
                else:
                    return
            else:
                keys = [ key ]
        
        for key in keys:
            path = node.path + '/' + str(key)
            child = Node(path, current, key, current[key])
            for hit in _walk(child, tail, expander, strict):
                yield hit
        
    if hook_after:
        hook_after(node)
                    
# the cache is provided to avoid endless loops because of recursive references
def expand(obj, root=None, depth=1, cache=set()):
    if not root:
        root = obj
    
    if depth == True:
        depth = 1
    elif depth <= 0:
        return obj
    
    if isRef(obj):
        ref = obj['$ref']
        if ref not in cache and depth > 0:
            trg = _getRef(ref, root, external=True)
            cache = cache.copy()
            cache.add(ref)
            return expand(trg, root, depth-1, cache)
        else:
            return obj
    
    if isinstance(obj,dict):
        trg = {}
        for (k,v) in obj.items():
            trg[k] = expand(v, root, depth, cache)
        return trg
    elif isinstance(obj,list):
        trg = []
        for val in obj:
            trg.append( expand(val, root, depth, cache) )
        return trg
    else:
        return obj


def apply(fun, obj, path, root, filt):
    if not root:
        root = obj
    parts = splitPath(path)
    modified = []
    for node in _walk(Node('', None, None, obj), parts, expander=None, strict=False):
        if filt and not filt(node):
            continue
        fun(node)
        modified.append(node.path)
    return modified

def isRef(obj):
    return (isinstance(obj, dict) and '$ref' in obj)

def set(obj, path, value, root=None, filt=None):
    parts = splitPath(path)
    def _set(node):
        if isRef(node.value):
            raise Exception('Cannot set value, object is a reference: ' + node.path)
        node.value[ parts[-1] ] = value
    return apply(_set, obj, '/'.join(parts[:-1]), root, filt)

 
def update(obj, path, value, root=None, filt=None):
    def _update(node):
        node.value.update(value)
    return apply(_update, obj, path, root, filt)
    

def add(obj, path, value, root=None, filt=None):
    def _add(node):
        node.value.append(value)
    return apply(_add, obj, path, root, filt)


def delete(obj, path, root=None, filt=None):
    parts = splitPath(path)
    def _delete(node):
        if parts[-1] in node.value:
            del node.value[ parts[-1] ]
    return apply(_delete, obj, '/'.join(parts[:-1]), root, filt)


# expands all references
def DEFAULTexpandER(root):
    return lambda ref: _getRef(ref, root, True)

# expands only local references
def LOCALexpandER(root):
    return lambda ref: _getRef(ref, root, False)


def _getRef(ref, root, external=True):
    if ref.startswith('/'):
        return get(root, ref)
    elif ref.startswith('#'):
        return get(root, ref[1:])
    elif not external:
        raise Exception('External or invalid reference: ' + ref)
    elif ref.startswith('file:///'):
        return _loadFile(ref.lstrip('file:///'))
    elif ref.startswith('file://'):
        return _loadFile(ref.lstrip('file://'))
    elif ref.startswith('http://') or ref.startswith('https://'):
        return _loadHTTP(ref.lstrip('file:///'))
    else:
        raise Exception('Invalid reference: ' + ref)


#TODO: encoding?
def _loadFile(path):
    with open(path) as f:
        raw = f.read()
        obj = json.loads(raw)
        return obj


#TODO: encoding?
def _loadHTTP(url):
    raw = urllib.request.urlopen(url).read().decode('utf-8')
    obj = json.loads(raw)
    return obj

