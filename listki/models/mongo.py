def update(collection,doc_key,doc_value,update_key,update_value):
    document=collection.find_one({doc_key:doc_value})
    document[update_key]=update_value
    collection.update({doc_key:doc_value}, {"$set": document}, upsert=False)