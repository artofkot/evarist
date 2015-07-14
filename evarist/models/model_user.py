# -*- coding: utf-8 -*-
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

def add(username, password, email,db, secret_key):
    if db.users.find_one({"email": email,
                        "provider":'email'}):
        return False
    else:
        pw_hash = hash_str(password,secret_key)
        db.users.insert_one({"username":username, 
                            "pw_hash":pw_hash, 
                            "email":email,
                            "confirmed":False,
                            'provider':'email',
                            "date":datetime.datetime.utcnow(),
                            'rights':{'is_checker':False, #checkers can see and vote any solutions
                                      'is_moderator':False #moderators are checkers who also 
                                                            #can create content
                                     },
                            "problems_ids": { #множества идут в порядке убывания тут
                                       "solution_written": [],
                                       "solved": [],
                                       "can_see_other_solutions":[], 
                                       "can_vote": []
                                   }
                        })
        return True

def add_gplus(gplus_id, gplus_picture,db, gplus_name, gplus_email):
    if db.users.find_one({"gplus_email": gplus_email,
                            "provider":'gplus'}):
        return False
    else:
        result=db.users.insert_one({"provider":'gplus',
                        "date":datetime.datetime.utcnow(),
                        "gplus_id":gplus_id,
                        "gplus_picture":gplus_picture,
                        "gplus_email":gplus_email,
                        "gplus_name":gplus_name,

                        # след два поля для того, чтобы все время не разбирать случаи provider:'email' or provider:'gplus'
                        "email":gplus_email, 
                        "username":gplus_name,
                        # их можно потом поменять/удалить

                        'rights':{'is_checker':False, #checkers can see and vote any solutions
                                  'is_moderator':False #moderators are checkers who also 
                                                #can create content
                                 },

                        "problems_ids": {
                                   "solution_written": [],
                                   "solved": [],
                                   "can_see_other_solutions":[], 
                                   "can_vote": []
                                   }
                        })
        return result.inserted_id