import os, datetime
import mongo

def add(text,db,author,problem_id,problem_set_id):
    ob_id=db.solutions.insert({'text':text,
                               'author':author,
                               'problem_id':problem_id,
                               'problem_set_id':problem_set_id,
                               'date':datetime.datetime.utcnow(),
                               'solution_discussion_ids':[],
                               'discussion':[],
                               'upvotes':0,
                               'downvotes':0,
                               'usernames_voted':[],
                               'is_right': False})

    # UPDATE OTHER DATABASES
    
    problem=db.entries.find_one({"_id":problem_id})
    problem['solutions_ids'].append(ob_id)
    db.entries.update({"_id":problem_id}, {"$set": problem}, upsert=False)

    user=db.users.find_one({'username':author})
    if not user.get('problems_ids'):
        user['problems_ids']={
                            "solution_written":[], #either unchecked ot not correct
                            'can_see_other_solutions':[], #all true if checker or moderator
                            "solved":[],
                            'can_vote':[] #all true if checker or moderator
                            } 

    user['problems_ids']['solution_written'].append(problem['_id'])
    db.users.update({"_id":user['_id']}, {"$set": user}, upsert=False)

    return True

def delete(db,solution):
    db.solutions.remove({'_id':solution['_id']})
    problem=db.entries.find_one({'_id':solution['problem_id']})
    problem['solutions_ids'].remove(solution['_id'])

    mongo.update(collection=db.entries,
                doc_key='_id',doc_value=solution["problem_id"],
                update_key='solutions_ids',
                update_value=problem['solutions_ids'])




def load_discussion(db,solution):
    if solution.get('discussion'):
        solution['discussion']=[]
    if solution['solution_discussion_ids']:
        for ob_id in solution['solution_discussion_ids']:
            post=db.posts.find_one({'_id':ob_id})
            if post:
                solution['discussion'].append(post)