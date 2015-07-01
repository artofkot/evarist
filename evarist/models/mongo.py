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

def add_key_value_where_none(collection, key, value):
    count=0
    for doc in collection.find():
        if not doc.get(key):
            count=count+1
            collection.update_one({'_id':doc['_id']}, {"$set": { key:value } }, upsert=False)
    return count

def load(obj,key_id,key,collection):
    if key_id.endswith('_ids'):
        obj[key]=[]
        for _id in obj[key_id]:
            doc=collection.find_one({'_id':_id})
            obj[key].append(doc)
        return True

    elif key_id.endswith('_id'):
        _id=obj[key_id]
        obj[key]=collection.find_one({'_id':_id})
        return True
    
    else: return False

def get_all(collection):
    docs=[]
    for i in collection.find():
        docs.append(i)
    return docs

def update(collection,doc_key,doc_value,update_key,update_value):
    count=0
    if doc_key=='all':
        for doc in collection.find():
            if not doc.get(update_key):
                doc[update_key]=update_value
                count=count+1
                collection.update({'_id':doc['_id']}, {"$set": doc}, upsert=False)
        return count
    else:
        document=collection.find_one({doc_key:doc_value})
        document[update_key]=update_value
        collection.update({doc_key:doc_value}, {"$set": document}, upsert=False)
