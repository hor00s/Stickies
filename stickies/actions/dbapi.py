from datetime import datetime as dt
from models import Model
from typing import (
    List,
    Tuple,
)

FIELDS = ('title', 'content', 'priority', 'date_created', 'date_edited', 'done', 'id')
DB_ROW = Tuple[str, str, int, str, str, int, int]
DB_VALUES = List[DB_ROW]


def _as_date(date: str) -> dt:
    return dt.strptime(date, '%d/%m/%Y')


def sort_by(sort_method: str, stickies: DB_VALUES, reversed: bool) -> DB_VALUES:
    sorted_stickies = stickies
    if sort_method == 'title':
        return sorted(sorted_stickies, key=lambda i: i[FIELDS.index('title')],
                      reverse=reversed)
    elif sort_method == 'content':
        return sorted(sorted_stickies, key=lambda i: i[slice(FIELDS.index('content'))],
                      reverse=reversed)
    elif sort_method == 'priority':
        return sorted(sorted_stickies, key=lambda i: i[slice(FIELDS.index('priority'))],
                      reverse=reversed)
    elif sort_method == 'date_created':
        return sorted(sorted_stickies, key=lambda i: _as_date(i[FIELDS.index('date_created')]),
                      reverse=reversed)
    elif sort_method == 'date_edited':
        return sorted(sorted_stickies, key=lambda i: _as_date(i[FIELDS.index('date_edited')]),
                      reverse=reversed)
    elif sort_method == 'done':
        return sorted(sorted_stickies, key=lambda i: i[FIELDS.index('done')],
                      reverse=not reversed)
    elif sort_method == 'id':
        return sorted(sorted_stickies, key=lambda i: i[FIELDS.index('id')],
                      reverse=reversed)
    else:  # sort method does not exist
        raise ValueError(f"Sory by `{sort_method}` does not exist")


def sanitize_entry(entry: str) -> str:
    return entry.strip().replace("'", "''")


def sanitize_command(word: str, chars: tuple[str] = ('`',)) -> str:
    fixed = []
    for i in word:
        if i in chars:
            fixed.append('\\')
        fixed.append(i)
    return ''.join(fixed)


def get_total(db_model: Model) -> int:
    return len(db_model.fetch_all())
