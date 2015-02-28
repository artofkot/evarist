# g.db.posts
# {
#     _id: ObjectId(...),
#     'problem_id': ObjectId(...),
#     'post_type': 'solution', #'comment'
#     'parent_type':'problem' or 'comment' or 'solution'
#     'parent_id': ObjectId(...), #if solution or comment in general discussion then it is the same as problem_id
#     'children_ids': [ObjectID(...),ObjectID(...),ObjectID(...),...]
#     'slug': '34db/8bda'
#     'full_slug': '2012.02.08.12.21.08:34db/2012.02.09.22.19.16:8bda',
#     "date": "2015-02-06T02:10:32.519Z"
#     'author':"entreri",
#     'text': 'This is so bogus ... '
# }