def parse_int(value, default=None, min_value=None, max_value=None):
    """安全解析整数，无效时返回default"""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return default
    try:
        result = int(value)
    except (ValueError, TypeError):
        return default
    if min_value is not None and result < min_value:
        return default
    if max_value is not None and result > max_value:
        return default
    return result


def parse_float(value, default=None, min_value=None, max_value=None):
    """安全解析浮点数，无效时返回default"""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return default
    try:
        result = float(value)
    except (ValueError, TypeError):
        return default
    if min_value is not None and result < min_value:
        return default
    if max_value is not None and result > max_value:
        return default
    return result
