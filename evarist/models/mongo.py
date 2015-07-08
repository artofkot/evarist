def add_key_value_where_none(collection, key, value):
    count=0
    for doc in collection.find():
        if not doc.get(key):
            doc[key]=value
            count=count+1
            collection.update({'_id':doc['_id']}, {"$set": doc}, upsert=False)
    return count

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



# def update_authors_email(collection,db):
#     for doc in collection.find():
#         user = db.users.find_one({'username':doc.get('author')})
#         if not user:
#             pass
#         else:
#             doc['authors_email']=user['email']
#             collection.update({'_id':doc['_id']}, {"$set": doc}, upsert=False)