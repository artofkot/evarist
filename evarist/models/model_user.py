import uuid
import hashlib
import os, datetime
from bson.objectid import ObjectId

def hash_str(password,secret_key):
    # uuid is used to generate a random number
    salt = uuid.uuid4().hex
    return hashlib.sha256(secret_key +salt.encode() + password.encode()).hexdigest() + ':' + salt
    
def check_pwd(user_password, hashed_password, secret_key):
    password, salt = hashed_password.split(':')
    return password == hashlib.sha256(secret_key+ salt.encode() + user_password.encode()).hexdigest()

# def hash_str(s):
#     return bcrypt.hashpw(current_app.config["SECRET_KEY"]+s, bcrypt.gensalt(10))

# def check_pwd(password,hashed):
#     return bcrypt.hashpw(current_app.config["SECRET_KEY"]+password,hashed) == hashed

def add(username, password, email,db, secret_key, picture):
    if db.users.find_one({"email": email}):
        return False
    else:
        pw_hash = hash_str(password,secret_key)
        db.users.insert({"username":username, 
                        "pw_hash":pw_hash, 
                        "email":email,
                        'picture':picture,
                        "date":datetime.datetime.utcnow(),
                        'rights':{'is_checker':False, #checkers can see and vote any solutions
                                  'is_moderator':False #moderators are checkers who also 
                                                #can create content
                                 },

                        'problems_ids':{
                            "solution_written":[], #either unchecked ot not correct
                            'can_see_other_solutions':[], #all true if checker or moderator
                            "solved":[],
                            'can_vote':[] #all true if checker or moderator
                            } 
                        })
        return True