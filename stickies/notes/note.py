from copy import copy
import datetime


class NoteCreationError(Exception): ...


class Note:
    MAX_CONTENT_LEN = 50
    MAX_TITLE_LEN = 20
    MAX_PRIORITY = 5

    def __init__(self, title: str, content: str, priority: int) -> None:
        self.content = content
        self.title = title
        self.priority = priority
        self.done = 0
        self._date_created = str(datetime.datetime.now().strftime("%d/%m/%Y"))
        self._date_editited = copy(self._date_created)

    def __str__(self) -> str:
        return f"<Note {self.content}>"

    def __repr__(self) -> str:
        return f"<Note({self.title}, {self.content}, {self.priority})>"

    def __int__(self) -> int:
        return self.priority

    def __bool__(self):
        return self.content or self.title

    @property
    def done(self):
        return self._done

    @property
    def date_created(self):
        return self._date_created

    @property
    def date_edited(self):
        return self._date_editited

    @property
    def content(self) -> str:
        return self._content

    @property
    def title(self) -> str:
        return self._title

    @property
    def priority(self) -> int:
        return self._priority

    @done.setter
    def done(self, v: int):
        if v not in (0, 1):
            raise NoteCreationError("`Done` value can only be set to 0 or 1")
        self._done = v

    @content.setter
    def content(self, content: str):
        if len(content) > Note.MAX_CONTENT_LEN:
            raise NoteCreationError("Content of note is too long")
        self._content = content

    @title.setter
    def title(self, title: str):
        if not len(title) or len(title) > Note.MAX_TITLE_LEN:
            raise NoteCreationError("Title is either too long (>50) or invalid")
        self._title = title

    @priority.setter
    def priority(self, priority: int):
        if not 0 < priority <= Note.MAX_PRIORITY:
            raise NoteCreationError(f"`Priority` can be set between 0 - {Note.MAX_PRIORITY}")
        self._priority = priority
