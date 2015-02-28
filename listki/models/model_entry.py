import os, datetime
from bson.objectid import ObjectId

# working with ObjectId
#
# from bson.objectid import ObjectId
# print str(  g.mongo.db.users.find_one({"username":"artofkot"})["_id"]  )
# artidhex=str(  g.mongo.db.users.find_one({"username":"artofkot"})["_id"]  )
# print g.mongo.db.users.find_one({"_id":ObjectId(artidhex)})


def add(text,db,author,entry_type,problem_set_id,title=None):
    if title: #then it will have field title
        if entry_type=='problem': #then it will have field solutions
            ob_id=db.entries.insert({'text':text, 
                                    "title":title,
                                    'author':author, 
                                    'entry_type':entry_type, 
                                    'general_discussion_ids':[], 
                                    'solutions_ids':[]})
        else:
            ob_id=db.entries.insert({'text':text, "title":title,'author':author, 'entry_type':entry_type, 
                                'general_discussion':[]}) 
    else:
        if entry_type=='problem':
            ob_id=db.entries.insert({'text':text,'author':author, 'entry_type':entry_type, 
                                'general_discussion':[], 'solutions':[]})
        else:
            ob_id=db.entries.insert({'text':text,'author':author, 'entry_type':entry_type, 
                                'general_discussion':[]})

    problem_set=db.problem_sets.find_one({"_id":problem_set_id})
    if not problem_set.get('entries_ids'):
        problem_set['entries_ids']=[]
    problem_set['entries_ids'].append(ob_id)
    db.problem_sets.update({"_id":problem_set_id}, {"$set": problem_set}, upsert=False)

    return True

def edit(ob_id, title, text, db):
    entry=db.entries.find_one({"_id": ob_id})
    entry['text']=text
    entry['title']=title
    db.entries.update({"_id":ob_id}, {"$set": entry}, upsert=False)
    return True

def delete_forever(entry_id,problem_set_id,db):
    problem_set=db.problem_sets.find_one({"_id": problem_set_id})
    
    ind=problem_set['entries_ids'].index(ObjectId(entry_id))
    problem_set['entries_ids'].pop(ind)
    db.problem_sets.update({"_id":problem_set_id}, {"$set": problem_set}, upsert=False)

    db.entries.remove({"_id":entry_id})
    return True   





