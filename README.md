StarPath
========

This library implements JSON Pointers ([RFC 6901](http://tools.ietf.org/html/rfc6901)) and pimps it up with extra features.

Basics
------

### Get a value
```
obj = {
    'foo': {
        'bar': 123
    }
}

starpath.get(obj, '/foo')
=> {'bar': 123}

starpath.get(obj, '/foo/bar')
=> 123
```

...and automatically dereferences pointers:

```
users = {
    'alice': {
        'name': 'Alice',
        'friends': [
                {'$ref': '/bob'}
            ]
    },
    'bob': {
        'name': 'Bob',
        'friends': [
                {'$ref': '/alice'}
            ]
    }
}

starpath.get(users, '/alice/friends/0/friends/0/friends/0/name')
=> 'Bob'
```


### Expand an object
```
obj = {
    'foo': [
        {'$ref': '/bar/0'},
        {'$ref': '/bar/1'},
        {'$ref': '/bar/2'},
        {'$ref': '/bar/3'}
    ],
    'bar': [
        1000,
        2000,
        3000,
        4000
    ]
}

starpath.get(obj, '/foo', expand=True)
=> [1000, 2000, 3000, 4000]
```
...or just a subset of values
```
starpath.get(obj, '/foo', expand=[1,'2'])
=> [{'$ref': '/bar/0'}, 2000, 3000, {'$ref': '/bar/4'}]
```

### through HTTP
```
obj = {
    'foo': {'$ref': 'http://.../some.json'}
}

starpath.get(obj, '/foo/bar')
=> ...the content of the response will be parsed and 'bar' extracted
```
### through filesystem
```
obj = {
    'foo': {'$ref': 'file:///.../some.json'}
}

starpath.get(obj, '/foo/bar')
=> ...the content of the file will be parsed and 'bar' extracted
```

### through provided data
```
root = {
    'foo': 123,
    'deeply': {
        'nested': {
            'child': {'$ref': '/foo'}
        }
    }
}
nested = starpath.get(root,'/deeply/nested')
=> {'child': {'$ref': '/foo'}}

starpath.get(nested, expand=True, root=root )
=> {'child': 123}
```



Additional features
-------------------

### Wildcards
```
users = {
    'alice': {
        'name': 'Alice',
        'friends': [
            {'$ref': '/bob'}
        ]
    },
    'bob': {
        'name': 'Bob',
        'friends': [
                {'$ref': '/alice'}
            ]
    }
}

starpath.find(users, '/*/name')
=> <iterator>

list(starpath.find(users, '/*/name'))
=> ['Alice', 'Bob']

list(starpath.find(users, '/alice/friends/*/name'))
=> ['Bob']

list(starpath.find(users, '/alice/friends/*/name', context=True))
=> [{'value':'Bob', 'key':'name', 'path':'/alice/friends/0/name', 'parent':{'name':'Bob','friends': [{'$ref': '/alice'}]}}]
```


### Set values
```
starpath.set(users, '/charlie',  {'name': 'Charlie', 'friends': []})
```

### Update values
```
starpath.update(users, '/charlie', {'friends': [{'$ref': '/alice'}]})
```
`starpath.set` replaces the content, while `starpath.update` "merges" the new values into the old one.
It's of course a "deep" merge.

### Add values
```
starpath.add(users, '/charlie/friends', {'$ref': '/bob'})
```

### Delete values
```
starpath.delete(users, '/charlie')
```

### Combining it with wildcards
```

starpath.set(users, '/*/messages', [])
starpath.add(users, '/*/messages', {'time':now(), 'message':'Look at this brand new feature!', 'read': False})
```


Similar Libraries
-----------------

- [dpath](https://github.com/akesterson/dpath-python) - has more lookup features, but is considerably slower
- [json-pointer](https://github.com/stefankoegl/python-json-pointer) - covers only the basics of json pointers
- [json-spec](https://github.com/johnnoone/json-spec) - covers pointers, validation and editting


