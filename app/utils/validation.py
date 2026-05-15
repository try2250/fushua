def parse_int(value, default=None, min_value=None, max_value=None):
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


def paginate(query, page, per_page=20):
    total = query.count()
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()
    return {
        "items": items,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
    }
