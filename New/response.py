def ok(payload=None, code=200):
    return payload or {}, code

def err(message, code=400):
    return {"error": message}, code
