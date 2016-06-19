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


def find(obj, path='', expander=None, context=False, filt=None):
    if not expander:
        expander = DEFAULT_EXPANDER(obj)
    parts = splitPath(path)
    root = Node('', None, None, obj)
    for node in _walk(root, parts, expander=expander, strict=False):
        if filt and not filt(node):
            continue
        if context:
            yield node
        else:
            yield node.value

def get(obj, path='', expander=None):
    if not expander:
        expander = DEFAULT_EXPANDER(obj)
    parts = splitPath(path)
    if '*' in parts:
        raise Exception('No wildcards allowed in getter path!')
    
    root = Node('', None, None, obj)
    for node in _walk(root, parts, expander=expander, strict=True):
        return node.value

def splitPath(path):
    parts = path.strip('/').split('/')
    parts = [p for p in parts if p != '']
    # we don't know yet if number keys are strings for dicts or ints for lists
    return parts



def _walk(node, parts, expander, strict=False):
    """Walks down the tree according to the path.
    parts -- the path split in a list of strings
    expander -- when a reference node is encountered, the expander will be called like expander(ref) and expects the node's value in return. If None, nodes will not be expanded.
    strict -- if True, an exception will be raised if part of the path is missing/wrong. Otherwise, the entry will be skipped.
    """
    if hook_before:
        hook_before(node)
    
    if not parts:
        yield node
    else:
        part = parts[0]
        tail = parts[1:]
        current = node.value
        
        if expander and isRef(current):
            current = expander( current['$ref'] )
        
        try:
            keys = _keys(part, current)
        except Exception as e:
            if strict:
                raise Exception('Invalid path: %s/%s' % (node.path, part), e)
            else:
                #print(str(e))
                keys = []
            
        for key in keys:
            path = node.path + '/' + str(key)
            child = Node(path, current, key, current[key])
            for hit in _walk(child, tail, expander, strict):
                yield hit
        
    if hook_after:
        hook_after(node)


def _keys(part, obj):
    if isinstance(obj, list):
        if part == '*':
            return reversed(range(len(obj))) # all keys
        else:
            if not part.isdigit():
                raise Exception('Invalid key: digits expected instead of "%s"' % part)
            n = int(part)
            if n < len(obj):
                return [ n ]           # one key
            else:
                raise Exception('Out of range (list size is %d)' % len(obj))
    elif isinstance(obj, dict):
        if part == '*':
            return list(obj.keys())   # all keys
        elif part not in obj:
            raise Exception('No such key: %s' % part)
        else:
            return [ part ]          # one key
    else:
        raise Exception('Invalid object, dict or list expected instead of "%s"' % obj)


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
    strict = ('*' not in parts)
    root = Node('', None, None, obj)
    for node in _walk(root, parts, expander=None, strict=strict):
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
        key = parts[-1]
        if isinstance(node.value, list):
            key = int(key)
            if key >= len(node.value):
                raise Exception("Index out of bounds: " + node.path + '/' + str(key))
        node.value[key] = value
    return apply(_set, obj, '/'.join(parts[:-1]), root, filt)

 
def update(obj, path, value, root=None, filt=None):
    def _update(node):
        for k,v in value.items():
            set(node.value, k, v)
    return apply(_update, obj, path, root, filt)
    

def add(obj, path, value, root=None, filt=None):
    def _add(node):
        node.value.append(value)
    return apply(_add, obj, path, root, filt)


def delete(obj, path, root=None, filt=None):
    parts = splitPath(path)
    def _delete(node):
        del node.parent[node.key]
    return apply(_delete, obj, '/'.join(parts), root, filt)


# expands all references
def DEFAULT_EXPANDER(root):
    return lambda ref: _getRef(ref, root, True)

# expands only local references
def LOCAL_EXPANDER(root):
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

