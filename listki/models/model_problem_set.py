import os, datetime

# working with ObjectId
#
# from bson.objectid import ObjectId
# print str(  g.mongo.db.users.find_one({"username":"artofkot"})["_id"]  )
# artidhex=str(  g.mongo.db.users.find_one({"username":"artofkot"})["_id"]  )
# print g.mongo.db.users.find_one({"_id":ObjectId(artidhex)})

# Creating ObjectId
#
# >>> o = ObjectId()
# >>> o == ObjectId(str(o))
# True

# g.db.users
# {
#     "_id": {
#         "$oid": "54cb533b3eab10f9c55ac824"
#     },
#     "username": "artofkot",
#     "pw_hash": "df51e68710e7610f5908909c3e08e9fb77097aca6ed574b14f1879d82364076a:e39d0cdc8508451b9d106b28ce840bd4",
#     "email": "artofkot@gmail.com",
#     "date": "2015-02-06T02:10:32.519Z"
# }


# g.db.problem_sets
# {
#     "_id": {
#         "$oid": "54d4220f5a1b06268e5b3a18"
#     },
#     "problems": [
#         {
#             "text": "{1, boy, cat, Syberia}. How many elements are in this set?",
#             "posts": [
#                 {
#                     "date": {
#                         "$date": "2015-02-06T02:10:32.519Z"
#                     },
#                     "text": "May be 4?",
#                     "type": "comment",
#                     "author": "entreri"
#                 },
#                 {
#                     "date": {
#                         "$date": "2015-02-06T02:30:31.849Z"
#                     },
#                     "text": "Definitely 4.",
#                     "type": "comment",
#                     "author": "matilda"
#                 },
#                 {
#                     "date": {
#                         "$date": "2015-02-24T00:50:50.628Z"
#                     },
#                     "text": "gon>?",
#                     "type": "comment",
#                     "author": "entreri"
#                 }
#             ],
#             "title": "Problem 1."
#         }
#     ],
#     "title": "Set Theory"
# }
# --------------------------------NEW:
# g.db.users
# {
#     "_id": {
#         "$oid": "54cb533b3eab10f9c55ac824"
#     },
#     "username": "artofkot",
#     "pw_hash": "df51e68710e7610f5908909c3e08e9fb77097aca6ed574b14f1879d82364076a:e39d0cdc8508451b9d106b28ce840bd4",
#     "email": "artofkot@gmail.com",
#     "date": "2015-02-06T02:10:32.519Z"
# }

# g.db.problem_sets
# {
#     "_id": {
#         "$oid": "54d4220f5a1b06268e5b3a18"
#     },
#     'aurthor':'artofkot',
#     "title": "Set Theory",
#     'slug': 'set-theory',
#     "date": "2015-02-06T02:10:32.519Z"
#     "entries": [ObjectId1,ObjectId2]
# }

# g.db.entries
#  {         "_id": {
#                 "$oid": "54d4220f5a1b06268e5b3a18"
#             },
#             "entry_type":"problem"
#             "title": "Main theorem in something."
#             "text": "{1, boy, cat, Syberia}. How many elements are in this set?"
#             "date": "2015-02-06T02:10:32.519Z"
#             'author':'dsf'
#             "general_discussion":[{post_id: ObjectId(...)},{post_id: ObjectId(...)},],
#             "solutions":[{post_id: ObjectId(...)},{post_id: ObjectId(...)},...]  #all comments will be recursively added in backend       
#  }             

# g.db.posts
# {
#     _id: ObjectId(...),
#     'problem_id': ObjectId(...),
#     'type': 'solution', #'comment'
#     'parent_type':'problem' or 'comment' or 'solution'
#     'parent_id': ObjectId(...), #if solution or comment in general discussion then it is the same as problem_id
#     'children_ids': [ObjectID(...),ObjectID(...),ObjectID(...),...]
#     'slug': '34db/8bda'
#     'full_slug': '2012.02.08.12.21.08:34db/2012.02.09.22.19.16:8bda',
#     "date": "2015-02-06T02:10:32.519Z"
#     'author':"entreri",
#     'text': 'This is so bogus ... '
# }
###################


def add(title,slug,db,author):
    if db.problem_sets.find_one({"title": title}):
        return False
    elif db.problem_sets.find_one({"slug": slug}):
        return False
    else:
        db.problem_sets.insert({"title":title,'slug':slug,'date':datetime.datetime.utcnow(),'author':author, 'entries_id':[]})
        return True

def get_all(db):
    problem_sets=db.problem_sets.find()
    prlist=[]
    for i in problem_sets:
        prlist.append(i)
    prlist.reverse()
    return prlist

def get_by_slug(problem_set_slug, db):
    a=db.problem_sets.find_one({"slug": problem_set_slug})
    if a:
        return a
    else:
        return False

def edit(ob_id, title, slug, db):
    problem_set=db.problem_sets.find_one({"_id": ob_id})
    problem_set['slug']=slug
    problem_set['title']=title
    db.problem_sets.update({"_id":ob_id}, {"$set": problem_set}, upsert=False)
    return True

def delete(ob_id, db):
    db.problem_sets.remove({"_id":ob_id})
    return True

# class ProblemSet:
#     def add(title,slug,db,author):
#         if db.problem_sets.find_one({"title": title}):
#             return False
#         elif db.problem_sets.find_one({"slug": slug}):
#             return False
#         else:
#             db.problem_sets.insert({"title":title,'slug':slug,'date':datetime.datetime.utcnow(),'author':author, 'etries':[]})
#             return True

#     def get_all(db):
#         problem_sets=db.problem_sets.find()
#         prlist=[]
#         for i in problem_sets:
#             prlist.append(i)
#         prlist.reverse()
#         return prlist


