
def replace_dict(a, b):
    changed_keys = set(a.keys()) & set(b.keys())
    return {k:v if k not in changed_keys else b[k] for k,v in a.items()}