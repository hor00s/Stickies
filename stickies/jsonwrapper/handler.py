import os
import json
from typing import Any


class Handler:
    def __init__(self, file: str, config: Any) -> None:
        self._file = file
        self.config = config

    def __str__(self) -> str:
        return self._read()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.read()})>"

    @property
    def file(self):
        return self._file

    def _write(self, data: Any):
        with open(self.file, mode='w') as f:
            json.dump(data, f, indent=4)

    def _read(self):
        with open(self.file, mode='r') as f:
            return json.load(f)

    def init(self):
        if not os.path.exists(self.file):
            self._write(self.config)

    def write(self, data: Any):
        self._write(data)

    def read(self) -> Any:
        return self._read()

    def get(self, key: Any):
        data = self._read()
        return data[key]

    def remove_key(self, key: Any):
        data = self._read()
        del data[key]
        self._write(data)

    def edit(self, key: Any, value: Any, value_type: type):
        data = self._read()
        if key not in data:
            msg = f"Key `{key}` does not exist. If you want to add a key use `Handler.add`"
            raise ValueError(msg)
        data[key] = value_type(value)
        self._write(data)

    def add(self, key: Any, value: Any, value_type: type):
        data = self.read()
        data[key] = value_type(value)
        self._write(data)

    def restore_default(self):
        self.delete_all()
        self.init()

    def delete_all(self):
        os.remove(self.file)
