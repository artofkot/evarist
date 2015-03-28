import os, datetime

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

def add(text,db,author,post_type,parent_type,parent_id,problem_id,problem_set_id):
    ob_id=db.posts.insert({'text':text,
                            'author':author, 
                            'post_type':post_type,
                            'parent_type':parent_type,
                            'parent_id':parent_id,
                            'problem_id':problem_id,
                            'problem_set_id':problem_set_id,
                            'children_ids':[],
                            'date':datetime.datetime.utcnow()})

    # UPDATE OTHER DATABASES
    
    
    if parent_type=='problem':
        problem=db.entries.find_one({"_id":problem_id})
        problem['general_discussion_ids'].append(ob_id)
        db.entries.update({"_id":problem_id}, {"$set": problem}, upsert=False)

    if parent_type=='solution':
        solution=db.solutions.find_one({"_id":parent_id})
        solution['solution_discussion_ids'].append(ob_id)
        db.solutions.update({"_id":solution['_id']}, {"$set": solution}, upsert=False)

    if parent_type=='comment':
        pass
    
    

    return True