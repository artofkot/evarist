def update(collection,doc_key,doc_value,update_key,update_value):
    if doc_key=='all':
        for doc in collection.find():
            doc['update_key']=update_value
            collection.update({'_id':doc['_id']}, {"$set": doc}, upsert=False)
    else:
        document=collection.find_one({doc_key:doc_value})
        document[update_key]=update_value
        collection.update({doc_key:doc_value}, {"$set": document}, upsert=False)