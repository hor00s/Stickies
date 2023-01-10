from datetime import datetime as dt
from typing import (
    Union,
    List,
    Tuple,
)

FIELDS = ('title', 'content', 'priority', 'date_created', 'date_edited', 'done', 'id')
DB_ROW = Tuple[Union[str, str, int, str, str, int, int]]
DB_VALUES = List[Tuple[Union[str, str, int, str, str, int, int]]]


def _as_date(date: str):
    return dt.strptime(date, '%d/%m/%Y')


def sort_by(sort_method: str, stickies: DB_VALUES, reversed: bool) -> DB_VALUES:
    assert sort_method in FIELDS, f"Sort by `{sort_method}` is invalid"

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
                      reverse=reversed)
    elif sort_method == 'id':
        return sorted(sorted_stickies, key=lambda i: i[FIELDS.index('id')],
                      reverse=reversed)


def sanitize_entry(entry: str) -> str:
    return entry.strip().replace("'", "''")


def sanitize_command(word: str, chars: tuple = ('`',)):
    fixed = []
    for i in word:
        if i in chars:
            fixed.append('\\')
        fixed.append(i)
    return ''.join(fixed)
