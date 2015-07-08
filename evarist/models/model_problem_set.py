import os, datetime
import model_entry

# working with ObjectId
#
# from bson.objectid import ObjectId
# print str(  g.db.users.find_one({"username":"artofkot"})["_id"]  )
# artidhex=str(  g.db.users.find_one({"username":"artofkot"})["_id"]  )
# print g.db.users.find_one({"_id":ObjectId(artidhex)})

# Creating ObjectId
#
# >>> o = ObjectId()
# >>> o == ObjectId(str(o))
# True


def add(title,slug,db,author):
    if db.problem_sets.find_one({"title": title}):
        return False
    elif db.problem_sets.find_one({"slug": slug}):
        return False
    else:
        db.problem_sets.insert({"title":title,
                                'slug':slug,
                                'author':author, 
                                'entries_ids':[],
                                'entries':[],
                                'status':'dev'})
        return True

def get_all(db):
    problem_sets=db.problem_sets.find()
    prlist=[]
    for i in problem_sets:
        prlist.append(i)
    prlist.reverse()
    return prlist

def edit(ob_id, title, slug, db, status, old_slug):
    # if db.problem_sets.find_one({"title": title}):
    #     return False
    if old_slug!=slug and db.problem_sets.find_one({"slug": slug}):
        return False
    problem_set=db.problem_sets.find_one({"_id": ob_id})
    problem_set['slug']=slug
    problem_set['title']=title
    problem_set['status']=status
    db.problem_sets.update({"_id":ob_id}, {"$set": problem_set}, upsert=False)
    return True

def delete(ob_id, db):
    problem_set=db.problem_sets.find_one({"_id":ob_id})

    # for entry_id in problem_set['entries_ids']:
    #     model_entry.delete_forever(entry_id=entry_id,problem_set_id=ob_id,db=db)

    db.problem_sets.remove({"_id":ob_id})
    return True

def load_entries(problem_set,db):
    problem_set['entries']=[]
    problem_counter=0
    definition_counter=0
    if not problem_set.get('entries_ids'): return False

    # load entries accorfing to entries_ids
    for ob_id in problem_set['entries_ids']:
        entry=db.entries.find_one({'_id':ob_id})
        if not entry: continue
        
        # get the number of problem or definition
        problem_set['entries'].append(entry)
        if entry['entry_type']=='problem': #then set the number of this problem
            problem_counter=problem_counter+1
            problem_set['entries'][-1]['problem_number']= problem_counter
        if entry['entry_type']=='definition': #then set the number of this definition
            definition_counter=definition_counter+1
            problem_set['entries'][-1]['definition_number']= definition_counter

    return True
