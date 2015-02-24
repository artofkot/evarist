# working with ObjectId
#
# from bson.objectid import ObjectId
# print str(  g.mongo.db.users.find_one({"username":"artofkot"})["_id"]  )
# artidhex=str(  g.mongo.db.users.find_one({"username":"artofkot"})["_id"]  )
# print g.mongo.db.users.find_one({"_id":ObjectId(artidhex)})

g.db.users
{
    "_id": {
        "$oid": "54cb533b3eab10f9c55ac824"
    },
    "username": "artofkot",
    "pw_hash": "df51e68710e7610f5908909c3e08e9fb77097aca6ed574b14f1879d82364076a:e39d0cdc8508451b9d106b28ce840bd4",
    "email": "artofkot@gmail.com",
    "date_created": "2015-02-06T02:10:32.519Z"
}


g.db.problem_sets
{
    "_id": {
        "$oid": "54d4220f5a1b06268e5b3a18"
    },
    "problems": [
        {
            "text": "{1, boy, cat, Syberia}. How many elements are in this set?",
            "posts": [
                {
                    "date": {
                        "$date": "2015-02-06T02:10:32.519Z"
                    },
                    "text": "May be 4?",
                    "type": "comment",
                    "author": "entreri"
                },
                {
                    "date": {
                        "$date": "2015-02-06T02:30:31.849Z"
                    },
                    "text": "Definitely 4.",
                    "type": "comment",
                    "author": "matilda"
                },
                {
                    "date": {
                        "$date": "2015-02-24T00:50:50.628Z"
                    },
                    "text": "gon>?",
                    "type": "comment",
                    "author": "entreri"
                }
            ],
            "title": "Problem 1."
        }
    ],
    "title": "Set Theory"
}
--------------------------------NEW:
g.db.problem_sets
{
    "_id": {
        "$oid": "54d4220f5a1b06268e5b3a18"
    },
    "title": "Set Theory",
    'slug': 'set-theory',
    "entries": [
        {
            'entry_id':ObjectId(...),
            #if "type":"problem"
            "general_discussion":[{post_id: ObjectId(...)},{post_id: ObjectId(...)},],
            "solutions":[{post_id: ObjectId(...)},{post_id: ObjectId(...)},...]  #all comments will be recursively added in backend
        }
    ]
}

g.db.entries
{           "_id": {
                "$oid": "54d4220f5a1b06268e5b3a18"
            },
            "type":"problem"
            "title": "Main theorem in something."
            "text": "{1, boy, cat, Syberia}. How many elements are in this set?"
        }

g.db.posts
{
    _id: ObjectId(...),
    'problem_id': ObjectId(...),
    'type': 'solution', #'comment'
    'parent_id': ObjectId(...), #if solution then it is the same as problem_id
    'children_ids': [ObjectID(...),ObjectID(...),ObjectID(...),...]
    'slug': '34db/8bda'
    'full_slug': '2012.02.08.12.21.08:34db/2012.02.09.22.19.16:8bda',
    'date': {
                        "$date": "2015-02-06T02:10:32.519Z"
                    },
    'author':"entreri",
    'text': 'This is so bogus ... '
}

