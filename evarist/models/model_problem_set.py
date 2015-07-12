import mongo

def add(title,slug,db):
    if db.problem_sets.find_one({"title": title}):
        return False
    elif db.problem_sets.find_one({"slug": slug}):
        return False
    else:
        db.problem_sets.insert_one({"title":title,
                                'slug':slug,
                                'entries_ids':[],
                                'status':'dev',
                                'tags':[]})
        return True

def edit(ob_id, title, slug, db, status, old_slug, old_title):
    if old_title!=title and db.problem_sets.find_one({"title": title}):
        return False
    elif old_slug!=slug and db.problem_sets.find_one({"slug": slug}):
        return False
    else:
        db.problem_sets.update_one({"_id": ob_id}, {'$set': {'slug': slug,
                                                      'title':title,  
                                                      'status':status}
                                            })
        
        # update tags of entries
        problem_set=db.problem_sets.find_one({"_id": ob_id})
        for entry_id in problem_set['entries_ids']:
            db.entries.update_one({"_id": entry_id}, {
                                                            '$pull': {'tags': old_title} 
                                                        })
            db.entries.update_one({"_id": entry_id}, {
                                                            '$addToSet': {'tags': title} 
                                                        })

        return True

def delete(ob_id, db):
    if db.problem_sets.delete_one({"_id":ob_id}):return True
    else: return False

def get_numbers(problem_set):
    definition_counter=0
    problem_counter=0
    for entry in problem_set['entries']:
        if entry['entry_type']=='problem': #then set the number of this problem
            problem_counter=problem_counter+1
            entry['problem_number']= problem_counter
        if entry['entry_type']=='definition': #then set the number of this definition
            definition_counter=definition_counter+1
            entry ['definition_number']= definition_counter
