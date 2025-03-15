"""
Helper module for data cleaning functions
"""

def filter_empty(obj, preserve_tech_stack=False):
    """
    Recursively filter empty arrays, dictionaries, and None values from nested objects.
    Used to reduce size of exported graph files.
    
    Args:
        obj: The object to filter (can be dict, list or primitive value)
        preserve_tech_stack: If True, always preserve tech_stack even if empty
        
    Returns:
        Filtered object with empty values removed
    """
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            # Special case: preserve tech_stack if requested, even if empty
            if preserve_tech_stack and k == "tech_stack":
                result[k] = v
            elif v not in ([], {}, None):
                result[k] = filter_empty(v, preserve_tech_stack)
        return result
    elif isinstance(obj, list):
        return [filter_empty(v, preserve_tech_stack) for v in obj if v not in ([], {}, None)]
    return obj
