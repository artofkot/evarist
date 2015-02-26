import os, datetime
from bson.objectid import ObjectId

# working with ObjectId
#
# from bson.objectid import ObjectId
# print str(  g.mongo.db.users.find_one({"username":"artofkot"})["_id"]  )
# artidhex=str(  g.mongo.db.users.find_one({"username":"artofkot"})["_id"]  )
# print g.mongo.db.users.find_one({"_id":ObjectId(artidhex)})

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

def add(text,db,author,entry_type,problem_set_id,title=None):
    if db.entries.find_one({"text": text}):
        return False

    if title:
        if entry_type=='problem':
            ob_id=db.entries.insert({'text':text, "title":title,'date':datetime.datetime.utcnow(),'author':author, 'entry_type':entry_type, 
                                'general_discussion':[], 'solutions':[]})
        else:
            ob_id=db.entries.insert({'text':text, "title":title,'date':datetime.datetime.utcnow(),'author':author, 'entry_type':entry_type, 
                                'general_discussion':[]}) 
    else:
        if entry_type=='problem':
            ob_id=db.entries.insert({'text':text,'date':datetime.datetime.utcnow(),'author':author, 'entry_type':entry_type, 
                                'general_discussion':[], 'solutions':[]})
        else:
            ob_id=db.entries.insert({'text':text,'date':datetime.datetime.utcnow(),'author':author, 'entry_type':entry_type, 
                                'general_discussion':[]})

    problem_set=db.problem_sets.find_one({"_id":problem_set_id})
    if not problem_set.get('entries_id'):
        problem_set['entries_id']=[]
    problem_set['entries_id'].append(ob_id)
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
    
    ind=problem_set['entries_id'].index(ObjectId(entry_id))
    problem_set['entries_id'].pop(ind)
    db.problem_sets.update({"_id":problem_set_id}, {"$set": problem_set}, upsert=False)

    db.entries.remove({"_id":entry_id})
    return True   





