import os, datetime
from bson.objectid import ObjectId

# How to work with ObjectId:
#
# from bson.objectid import ObjectId
# print str(  g.db.users.find_one({"username":"artofkot"})["_id"]  )
# artidhex=str(  g.db.users.find_one({"username":"artofkot"})["_id"]  )
# print g.db.users.find_one({"_id":ObjectId(artidhex)})


def add(text,db,author,entry_type,problem_set_id,title=None,entry_number=None,authors_email=None):
    if entry_type=='problem': #then it will have field solutions
        ob_id=db.entries.insert({'text':text, 
                                "title":title,
                                'author':author,
                                'authors_email':authors_email, 
                                'entry_type':entry_type, 
                                'general_discussion_ids':[], 
                                'solutions_ids':[],
                                'general_discussion':[],
                                'solution':None,
                                'parents_ids':[problem_set_id]})
    else:
        ob_id=db.entries.insert({'text':text, 
                                "title":title,
                                'author':author, 
                                'authors_email':authors_email, 
                                'entry_type':entry_type, 
                                'general_discussion_ids':[],
                                'general_discussion':[],
                                'solution':None,
                                'parents_ids':[problem_set_id]}) 

    # add the entry to the specified problem_set 
    problem_set=db.problem_sets.find_one({"_id":problem_set_id})
    if not problem_set.get('entries_ids'):
        problem_set['entries_ids']=[]
    problem_set['entries_ids'].insert(entry_number,ob_id)
    db.problem_sets.update({"_id":problem_set_id}, {"$set": problem_set}, upsert=False)

    return True

def edit(ob_id, title, text, db, entry_type, problem_set_id, entry_number):
    entry=db.entries.find_one({"_id": ob_id})
    entry['text']=text
    entry['title']=title
    entry['entry_type']=entry_type
    db.entries.update({"_id":ob_id}, {"$set": entry}, upsert=False)

    problem_set=db.problem_sets.find_one({"_id":problem_set_id})
    if not problem_set.get('entries_ids'):
        problem_set['entries_ids']=[]
    problem_set['entries_ids'].remove(ob_id)
    problem_set['entries_ids'].insert(entry_number,ob_id)
    db.problem_sets.update({"_id":problem_set_id}, {"$set": problem_set}, upsert=False)
    return True

def delete_forever(entry_id,problem_set_id,db):
    problem_set=db.problem_sets.find_one({"_id": problem_set_id})
    
    ind=problem_set['entries_ids'].index(ObjectId(entry_id))
    problem_set['entries_ids'].pop(ind)
    db.problem_sets.update({"_id":problem_set_id}, {"$set": problem_set}, upsert=False)

    db.entries.remove({"_id":entry_id})
    return True   

def load_posts(problem,db):
    problem['general_discussion']=[]
    if not problem.get('general_discussion_ids'): return False
    for ob_id in problem['general_discussion_ids']:
        post=db.posts.find_one({'_id':ob_id})
        if post: problem['general_discussion'].append(post)


def load_solution(problem,db,username,email):
    # user=db.users.find_one({'username':username})
    solution=db.solutions.find_one({'authors_email':email,
                            'problem_id':problem['_id']})
    if solution:
        problem['solution']=solution

    
