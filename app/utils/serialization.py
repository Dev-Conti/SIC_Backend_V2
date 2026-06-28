from bson import ObjectId

def serialize_mongo_documents(docs):
    """Serializa uma lista de documentos do MongoDB convertendo ObjectId para string."""
    for doc in docs:
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])
    return docs
