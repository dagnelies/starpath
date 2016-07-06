import starpath

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
    },
    'charlie': {
        'name': 'Charlie',
        'friends': []
    },
    'www_users': {
        '$ref': 'http://www.w3schools.com/website/customers_mysql.php'
    },
    'my_list': [1,2,3]
}

assert starpath.get(users, 'my_list') == [1,2,3]
assert starpath.get(users, 'my_list/0') == 1
starpath.set(users, 'my_list', [4,5,6])
assert starpath.get(users, 'my_list/0') == 4
starpath.set(users, 'my_list/0', [999])
assert starpath.get(users, 'my_list') == [[999], 5, 6]


print( starpath.get(users, '/www_users/0') )
assert starpath.get(users, '/www_users/0/Name') == "Alfreds Futterkiste"


assert starpath.get(users, '/alice/name')                     == 'Alice'
assert starpath.get(users, '/alice/friends/0/name')           == 'Bob'
assert starpath.get(users, '/alice/friends/0/friends/0/name') == 'Alice'

assert sorted(starpath.find(users, '/*/name'))           == ['Alice', 'Bob', 'Charlie']
assert sorted(starpath.find(users, '/*/friends/*/name')) == ['Alice', 'Bob']

starpath.add(users, 'bob/friends', {'$ref': '/charlie'})
assert sorted(starpath.find(users, '/*/friends/*/name')) == ['Alice', 'Bob', 'Charlie']

starpath.set(users, 'charlie/status', 'New')
assert starpath.get(users, '/charlie/status') == 'New'

starpath.set(users, 'charlie/status', 'Hmm')
assert starpath.get(users, '/charlie/status') == 'Hmm'

starpath.update(users, 'charlie', {'status':'Old'})
assert starpath.get(users, '/charlie/status') == 'Old'

starpath.delete(users, '*/status')
assert starpath.get(users, '/charlie') == {'name': 'Charlie', 'friends': []}

starpath.delete(users, '*/friends/*')
assert list(starpath.find(users, '*/friends')) == [[],[],[]]

exit()
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