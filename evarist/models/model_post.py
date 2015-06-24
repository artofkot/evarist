import os, datetime

def add(text,db,author,post_type,parent_type,parent_id,problem_id,problem_set_id,authors_email=None):
    ob_id=db.posts.insert({'text':text,
                            'author':author,
                            'authors_email':authors_email, 
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