import unittest
from models import Model
from .note import (
    Note,
    NoteCreationError,
)


class TestNote(unittest.TestCase):
    def setUp(self) -> None:
        self.model = Model(
            'test_notes',
            'notes/',
            title='TEXT type UNIQUE',
            content='TEXT',
            priority='INTEGER',
            date_created='TEXT',
            date_edited='TEXT',
            done='INTEGER'
        )

        self.note = Note('title', 'test content', 3)
        self.model.create_table()

    def test_content_len_setter(self):
        content = 'a' * Note.MAX_CONTENT_LEN + 'a'
        with self.assertRaises(NoteCreationError):
            _ = Note('title', content, 3)
        content = content[:-1]
        _ = Note('title', content, 3)

    def test_title_setter(self):
        title = 'a' * Note.MAX_TITLE_LEN + 'a'
        with self.assertRaises(NoteCreationError):
            _ = Note(title, 'content', 3)

        title = title[:-1]
        _ = Note('content', title, 3)

    def test_priority_setter(self):
        priority = Note.MAX_PRIORITY + 1
        with self.assertRaises(NoteCreationError):
            _ = Note('content', 'title', priority)
        priority = Note.MAX_PRIORITY
        _ = Note('content', 'title', priority)

    def test_set_date(self):
        self.assertEqual(self.note.date_created, self.note.date_edited)

    def test_insert(self):
        self.model.insert(
            title=self.note.title,
            content=self.note.content,
            priority=self.note.priority,
            date_edited=self.note.date_edited,
            date_created=self.note.date_created,
            done=self.note.done,
        )
        row = self.model.fetch_last()
        row_id = self.model.filter_row(row, 'id')
        expected = [(self.note.title, self.note.content, self.note.priority,
                    self.note.date_created, self.note.date_edited, self.note.done, row_id)]
        self.assertEqual(row, expected)

        self.model.delete('title', self.note.title)
        self.assertEqual(len(self.model.fetch_all()), 0)

    def test_edit(self):
        self.model.insert(
            title=self.note.title,
            content=self.note.content,
            priority=self.note.priority,
            date_edited=self.note.date_edited,
            date_created=self.note.date_created,
            done=self.note.done
        )
        self.model.edit("priority=5", f"title='{self.note.title}'")
        priority = self.model.fetch_last('priority')
        self.assertEqual(priority, 5)
        self.model.delete('title', self.note.title)
