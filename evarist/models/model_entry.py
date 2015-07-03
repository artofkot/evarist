import os, datetime
from bson.objectid import ObjectId

# How to work with ObjectId:
#
# from bson.objectid import ObjectId
# print str(  g.db.users.find_one({"username":"artofkot"})["_id"]  )
# artidhex=str(  g.db.users.find_one({"username":"artofkot"})["_id"]  )
# print g.db.users.find_one({"_id":ObjectId(artidhex)})


def add(text,db,author_id,entry_type,problem_set_id,entry_number):
    problem_set=db.problem_sets.find_one({"_id":problem_set_id})
    if entry_type=='problem': #then it will have field solutions_ids
        ob_id=db.entries.insert_one({'text':text,
                                'author_id':author_id,
                                'date':datetime.datetime.utcnow(),
                                'entry_type':entry_type, 
                                'general_discussion_ids':[], 
                                'solutions_ids':[],
                                'parents_ids':[problem_set_id],
                                'tags':[problem_set['title']]}).inserted_id
    else:
        ob_id=db.entries.insert_one({'text':text,
                                'author_id':author_id,
                                'date':datetime.datetime.utcnow(),
                                'entry_type':entry_type, 
                                'general_discussion_ids':[],
                                'parents_ids':[problem_set_id],
                                'tags':[problem_set['title']]}).inserted_id

    # add the entry to the specified problem_set 
    db.problem_sets.update_one({"_id":problem_set_id}, 
                                {"$push":   {'entries_ids':{
                                                        '$each':[ob_id],
                                                        '$position':entry_number
                                                            }   
                                            } 
                                })

    return True

def edit(ob_id, text, db, entry_type, problem_set_id, entry_number):
    db.entries.update_one({"_id":ob_id}, 
                                {"$set": {'text':text,
                                            'entry_type':entry_type}})

    db.problem_sets.update_one({"_id":problem_set_id}, 
                                    {"$pull": {'entries_ids':ob_id }})

    db.problem_sets.update_one({"_id":problem_set_id}, 
                                {"$push": {'entries_ids':{
                                                        '$each':[ob_id],
                                                        '$position':entry_number
                                                            }   
                                            } 
                                })


    return True

def delete_forever(entry_id,problem_set_id,db):
    r=db.entries.delete_one({"_id":entry_id})
    db.problem_sets.update_one({"_id":problem_set_id}, 
                                    {"$pull": {'entries_ids':entry_id }})

    if r: return True
    else: return False

    
