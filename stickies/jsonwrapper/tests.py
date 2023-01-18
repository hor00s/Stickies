import unittest
from . import Handler
from pathlib import Path
from actions.constants import BASE_DIR


class TestHandler(unittest.TestCase):
    def setUp(self) -> None:
        path = str(Path(f"{BASE_DIR}/testconfig.json"))
        self.data = {'c0': 'v0', 'c1': 'v1'}
        self.file = Handler(path, self.data)
        self.file.init()

    def tearDown(self) -> None:
        self.file.restore_default()

    def test_read(self):
        data = self.file.read()
        self.assertEqual(self.data, data)

    def test_get(self):
        c0 = self.file.get('c0')
        v0 = self.data['c0']
        self.assertEqual(c0, v0)

    def test_edit(self):
        self.file.edit('c0', 'o0', str)
        o0 = self.file.get('c0')
        self.assertEqual(o0, 'o0')

    def test_delete(self):
        delete = 'c0'
        self.file.remove_key(delete)
        with self.assertRaises(KeyError):
            self.file.get(delete)

    def test_restore_default(self):
        data = self.file.read()
        for i in data:
            data[i] = 'other'
        self.file.write(data)
        self.file.restore_default()
        default = self.file.read()
        self.assertEqual(self.data, default)
