import starpath
import timeit

### Get a value

obj = {
    'foo': {
        'bar': 123
    }
}

assert starpath.get(obj, '/foo') == {'bar': 123}

assert starpath.get(obj, '/foo/bar') == 123


### Follow references

obj = {
    'foo': {'$ref': '/bar'},
    'bar': [0,11,22,33]
}

assert starpath.get(obj, '/foo/2') == 22


### Expand references

obj = {
    'foo': [
        {'$ref': '/bar/2'},
        {'$ref': '/foo/1'},
        {'$ref': '/bar/0'}
    ],
    'bar': [
        0,
        111,
        222
    ]
}


print( starpath.get(obj, '/foo', expand=False) )
assert starpath.get(obj, '/foo', expand=False) == [{'$ref': '/bar/2'}, {'$ref': '/foo/1'}, {'$ref': '/bar/0'}]

print( starpath.get(obj, '/foo', expand=True) )
assert starpath.get(obj, '/foo', expand=True) == [222, {'$ref': '/foo/1'}, 0]

### through HTTP

obj = {
    'customers': {'$ref': 'http://www.w3schools.com/website/customers_mysql.php'}
}

assert starpath.get(obj, '/customers/0/Name') == "Alfreds Futterkiste"

### through provided data

root = {
    'foo': 123,
    'deeply': {
        'nested': {
            'child': {'$ref': '/foo'}
        }
    }
}
nested = starpath.get(root,'/deeply/nested')
assert nested == {'child': {'$ref': '/foo'}}

assert starpath.get(nested, expand=True, root=root ) == {'child': 123}

### Wildcards

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

assert starpath.find(users, '/*/name') != None #<iterator>

assert sorted(list(starpath.find(users, '/*/name'))) == ['Alice', 'Bob']

assert list(starpath.find(users, '/alice/friends/*/name')) == ['Bob']

starpath.set(users, '/bob/name', 'Bobby!')

assert list(starpath.find(users, '/alice/friends/*/name')) == ['Bobby!']

starpath.set(users, '/*/flag', True) 

#starpath.set(users, '/foo', {'bar':1}) 
print(users)

print('Done')