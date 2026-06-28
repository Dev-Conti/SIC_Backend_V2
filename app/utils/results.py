from bson import ObjectId
from bson.objectid import ObjectId


def serialize_results(results):
    """
    Serializa listas ou dicionários retornados do MongoDB,
    convertendo ObjectId para string e mantendo a estrutura original.
    """
    if isinstance(results, list):
        return [serialize_results(item) for item in results]
    elif isinstance(results, dict):
        return {
            key: str(value) if isinstance(value, ObjectId) else value
            for key, value in results.items()
        }
    return results