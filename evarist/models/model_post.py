import os, datetime

def add(text,db,author_id,post_type,parent_id):
    result=db.posts.insert_one({'text':text,
                            'author_id':author_id,
                            'post_type':post_type,
                            'parent_id':parent_id,
                            'date':datetime.datetime.utcnow()})
    ob_id=result.inserted_id

    # UPDATE OTHER DATABASES
    
    if post_type=='entry->general_discussion':
        db.entries.update_one({"_id": parent_id}, 
                            {'$addToSet': {'general_discussion_ids': ob_id} })

    if post_type=='solution->comment':
        db.solutionss.update_one({"_id": parent_id}, 
                            {'$addToSet': {'solution_discussion_ids': ob_id} })

    if post_type=='feedback':
        pass

    return True