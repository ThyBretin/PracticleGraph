"""
Helper module for data cleaning functions
"""

def filter_empty(obj):
    """
    Recursively filter empty arrays, dictionaries, and None values from nested objects.
    Used to reduce size of exported graph files.
    
    Args:
        obj: The object to filter (can be dict, list or primitive value)
        
    Returns:
        Filtered object with empty values removed
    """
    if isinstance(obj, dict):
        return {k: filter_empty(v) for k, v in obj.items() if v not in ([], {}, None)}
    elif isinstance(obj, list):
        return [filter_empty(v) for v in obj if v not in ([], {}, None)]
    return obj
