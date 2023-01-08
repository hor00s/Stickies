import os
import time
import models
import logger
import jsonwrapper
import webbrowser as web
import threading as thr
from typing import Generator
from pathlib import Path
from notes.note import Note
from datetime import datetime as dt
from actions.constants import LabelColor, get_icon
from PyQt5 import uic, QtGui
from actions.dbapi import (
    DB_ROW,
    FIELDS,
    DB_VALUES,
    sort_by,
    sanitize_entry,
)
from PyQt5.QtCore import (
    Qt,
    QSize,
)
from PyQt5.QtWidgets import (
    QApplication,
    QRadioButton,
    QMessageBox,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QListWidget,
    QComboBox,
    QLineEdit,
    QDialog,
    QLabel,
)


class Stickies(QMainWindow):
    UIFILE = Path('window/untitled.ui')
    VIEW_SEPERATOR = '\n'
    THEME_COLOR = 'rgb(38, 147, 217)'

    def __init__(self, model: models.Model, logger: logger.Logger,
                 configs: jsonwrapper.Handler) -> None:
        super(Stickies, self).__init__()
        uic.loadUi(Stickies.UIFILE, self)

        # Utils
        self.logger = logger
        self.model = model
        self.configs = configs

        # Load widgets
        self._load_line_edits()
        self._load_buttons()
        self._load_labels()
        self._load_lists()

        # Set up
        self.load_stickies()
        self.priority_ln.setReadOnly(True)
        self.priority_ln.setText('1')
        self.stickies_view.setSelectionMode(3)  # 3 -> ExtendedSelection
        self._disable_priority_direction_btn(
            int(self.priority_ln.text()),
            self.priority_up_btn,
            self.priority_down_btn
        )
        self.search_ln.textChanged.connect(self.handle_search_query)

        self.title_ln.setMaxLength(Note.MAX_TITLE_LEN)
        self.search_ln.setMaxLength(Note.MAX_TITLE_LEN)
        self.content_ln.setMaxLength(Note.MAX_CONTENT_LEN)
        self.stickies_view.setStyleSheet(
            "QListWidget::item {margin-bottom: 10px;}"
        )

        # MENU
        # Triggers
        self.actionView.triggered.connect(self.view_settings)
        self.actionEdit.triggered.connect(self.edit_settings)
        self.actionSource_code.triggered.connect(lambda: web.open('github.com/hor00s/Stickies'))
        # Icons
        self.actionView.setIcon(QtGui.QIcon(get_icon['view']))
        self.actionEdit.setIcon(QtGui.QIcon(get_icon['edit']))
        self.actionShortcuts.setIcon(QtGui.QIcon(get_icon['shortcuts']))
        self.actionSource_code.setIcon(QtGui.QIcon(get_icon['source']))

        # Button commands
        self.save_btn.clicked.connect(self.save)
        self.cancel_btn.clicked.connect(self.cancel)
        self.refresh_btn.clicked.connect(lambda: self._refresh_list())
        self.priority_up_btn.clicked.connect(
            lambda: self.set_priority('up')
        )
        self.priority_down_btn.clicked.connect(
            lambda: self.set_priority('down')
        )
        self.delete_done_btn.clicked.connect(self.delete_done)
        self.delete_all_btn.clicked.connect(self.delete_all)
        self.delete_btn.clicked.connect(self.delete_one)
        self.edit_btn.clicked.connect(self.edit)
        self.reverse_order_cmd.clicked.connect(self._refresh_list)

        self.mark_done_btn.clicked.connect(
            lambda: self.change_done_status(True)
        )
        self.mark_undone_btn.clicked.connect(
            lambda: self.change_done_status(False)
        )

    def _load_labels(self):
        label_style = 'color: rgb(38, 147, 217);'
        self.title_lbl = self.findChild(QLabel, 'title_lbl')
        self.content_lbl = self.findChild(QLabel, 'content_lbl')
        self.priority_lbl = self.findChild(QLabel, 'priority_lbl')
        self.info_lbl = self.findChild(QLabel, 'info_lbl')
        self.search_lbl = self.findChild(QLabel, 'search_lbl')

        self.title_lbl.setStyleSheet(label_style)
        self.content_lbl.setStyleSheet(label_style)
        self.priority_lbl.setStyleSheet(label_style)
        self.search_lbl.setStyleSheet(label_style)

    def _load_line_edits(self):
        self.title_ln = self.findChild(QLineEdit, 'title_ln')
        self.content_ln = self.findChild(QLineEdit, 'content_ln')
        self.priority_ln = self.findChild(QLineEdit, 'priority_ln')
        self.search_ln = self.findChild(QLineEdit, 'search_ln')

    def _load_lists(self):
        self.stickies_view = self.findChild(QListWidget, 'sticky_view')

    def _load_buttons(self):
        self.save_btn = self.findChild(QPushButton, 'save_btn')
        self.cancel_btn = self.findChild(QPushButton, 'cancel_btn')
        self.priority_up_btn = self.findChild(QPushButton, 'priority_up_btn')
        self.priority_down_btn = self.findChild(QPushButton, 'priority_down_btn')
        self.edit_btn = self.findChild(QPushButton, 'edit_btn')
        self.delete_btn = self.findChild(QPushButton, 'delete_btn')
        self.delete_all_btn = self.findChild(QPushButton, 'delete_all_btn')
        self.delete_done_btn = self.findChild(QPushButton, 'delete_done_btn')
        self.mark_done_btn = self.findChild(QPushButton, 'mark_done_btn')
        self.mark_undone_btn = self.findChild(QPushButton, 'mark_undone_btn')
        self.refresh_btn = self.findChild(QPushButton, 'refresh_btn')
        self.reverse_order_cmd = self.findChild(QRadioButton, 'reverse_order_cmd')

        self.save_btn.setIcon(QtGui.QIcon(get_icon['save']))
        self.cancel_btn.setIcon(QtGui.QIcon(get_icon['cancel']))
        self.priority_up_btn.setIcon(QtGui.QIcon(get_icon['plus']))
        self.priority_down_btn.setIcon(QtGui.QIcon(get_icon['minus']))
        self.edit_btn.setIcon(QtGui.QIcon(get_icon['edit']))
        self.delete_btn.setIcon(QtGui.QIcon(get_icon['delete']))
        self.delete_all_btn.setIcon(QtGui.QIcon(get_icon['deleteall']))
        self.delete_done_btn.setIcon(QtGui.QIcon(get_icon['deletedone']))
        self.mark_done_btn.setIcon(QtGui.QIcon(get_icon['markdone']))
        self.mark_undone_btn.setIcon(QtGui.QIcon(get_icon['markundone']))
        self.refresh_btn.setIcon(QtGui.QIcon(get_icon['refresh']))

    def _refresh_list(self):
        self.stickies_view.clear()
        self.load_stickies()

    def _disable_priority_direction_btn(self, current_priority: int,
                                        up_btn: QPushButton,
                                        down_btn: QPushButton):
        if current_priority == 1:
            down_btn.setEnabled(False)
        else:
            down_btn.setEnabled(True)

        if current_priority == 5:
            up_btn.setEnabled(False)
        else:
            up_btn.setEnabled(True)

    def _make_command(self, flags: str):
        os.system(f"./stickies.py {flags}")

    def _get_title_from_item(self, list_item) -> str:
        exlude = len("Title: ")
        item_text = list_item.text()
        title = item_text.split(Stickies.VIEW_SEPERATOR)[0][exlude:]
        return title

    def _info_label(self, header: str, msg: str, rgb: tuple[int], seconds: int = 3):
        r, g, b = rgb
        self.info_lbl.setStyleSheet(f"color: rgb({r}, {g}, {b});")
        self.info_lbl.setText(f"[{header.upper()}]: {msg}")
        time.sleep(seconds)
        self.info_lbl.setText('')
        self.info_lbl.setStyleSheet("")

    def _add_stickie_fields(self, stickies: DB_VALUES)\
            -> Generator[DB_ROW, None, None]:
        other = []
        for sticky in stickies:
            temp = map(
                lambda i: f"{FIELDS[i[0]].capitalize()}: {i[1]}",
                enumerate(sticky)
            )
            other.append(list(temp))
        yield from other

    def _get_date(self, date: str):
        return dt.strptime(date, '%d/%m/%Y')

    def _sort_stickies(self, stickies: DB_VALUES)\
            -> Generator[DB_ROW, None, None]:
        sort_method = self.configs.get('sort_by')

        sorted_stickies = stickies
        reversed = self.reverse_order_cmd.isChecked()
        yield from sort_by(sort_method, sorted_stickies, reversed)

    def _clear_selections(self):
        self.stickies_view.selectedItems()
        for i in range(self.stickies_view.count()):
            current_item = self.stickies_view.item(i)
            current_item.setForeground(Qt.GlobalColor.black)

    def view_settings(self):
        msg = '\n'.join(
            map(lambda i: f"{i[0]}:\t{i[1]}", self.configs.read().items())
        )
        QMessageBox.information(self, 'Info', msg)

    def edit_settings(self):
        def set_values(config_key, config_value):
            config_value.clear()
            key = config_key.currentText()
            for value in settings[key]:
                config_value.addItem(str(value))
            config_value.setCurrentText(str(self.configs.get(key)))

        assert len(self.configs.read()) == 2, "Unhandled setting"
        height, width = 300, 300
        layout = QVBoxLayout()
        dialog = QDialog()
        dialog.setWindowTitle("Edit settings")
        dialog.setLayout(layout)
        dialog.setFixedSize(QSize(height, width))

        ok_btn = QPushButton(dialog, text="Ok")

        ok_btn.clicked.connect(
            lambda: self.configs.edit(
                config_key.currentText(),
                config_value.currentText(),
                int if config_value.currentText().isnumeric() else str,
            )
        )

        config_value = QComboBox(dialog)
        config_key = QComboBox(dialog)
        layout.addWidget(config_key)
        layout.addWidget(config_value)
        config_key.activated.connect(lambda: set_values(config_key, config_value))

        settings = {
            'quiet': range(1, Note.MAX_PRIORITY + 1),
            'sort_by': FIELDS,
        }

        for key in settings:
            config_key.addItem(key)
        set_values(config_key, config_value)
        layout.addWidget(ok_btn)

        dialog.exec_()
        self._refresh_list()

    def info_label(self, header: str, msg: str, rgb: tuple[int], seconds: int = 3):
        (
            thr.Thread(target=self._info_label, args=(header, msg, rgb, seconds))
            .start()
        )

    def load_stickies(self):
        stickies: DB_VALUES = self.model.fetch_all()
        stickies = self._sort_stickies(stickies)
        stickies = self._add_stickie_fields(stickies)

        for sticky in stickies:
            self.stickies_view.addItem(
                Stickies.VIEW_SEPERATOR.join(map(str, sticky))
            )

    def save(self):
        title = self.title_ln.text()
        if not title:
            self.info_label("WARNING", "Title cannon be empty", LabelColor.ERROR.value)
        else:
            exists = self.model.execute(
                f"SELECT * FROM {self.model.name} WHERE\
                     title='{sanitize_entry(title)}'", True
            )
            content = self.content_ln.text()
            priority = self .priority_ln.text()

            if exists:
                self._make_command(
                    f'edit -t "{title}" -sc "{self.content_ln.text()}" -sp\
                         {int(self.priority_ln.text())}'
                )
                msg = f"Sticky `{title}` has been edited"
                self.info_label("edit", msg, LabelColor.SUCCESS.value)
            else:
                flags = f'add -t "{title}" -c "{content}" -p {priority}'
                self._make_command(flags)
                self.info_label('new', f"Sticky `{title}` is now added", LabelColor.SUCCESS.value)

        self._refresh_list()
        self.title_ln.setText('')

    def cancel(self):
        self.priority_ln.setText('1')
        self._disable_priority_direction_btn(
            int(self.priority_ln.text()),
            self.priority_up_btn,
            self.priority_down_btn
        )

        inputs = (self.title_ln, self.content_ln)
        for input in inputs: input.setText('')

    def set_priority(self, direction: str):
        line = self.priority_ln.text()
        if direction == 'up' and int(line) < Note.MAX_PRIORITY:
            next_num = int(line) + 1
            self.priority_ln.setText(str(next_num))
        elif direction == 'down' and int(line) > 1:
            prev_num = int(line) - 1
            self.priority_ln.setText(str(prev_num))

        self._disable_priority_direction_btn(
            int(self.priority_ln.text()),
            self.priority_up_btn,
            self.priority_down_btn
        )

    def delete_done(self):
        flags = 'clear_done'
        self._make_command(flags)
        self._refresh_list()
        msg = "All items marked as `done` have been removed"
        self.info_label("info", msg, LabelColor.INFO.value)

    def delete_all(self):
        flags = 'purge_all'
        self._make_command(flags)
        self._refresh_list()

    def delete_one(self):
        exists = self.stickies_view.selectedItems()
        if exists:
            title = self._get_title_from_item(self.stickies_view.currentItem())
            self._make_command(f'remove -t "{title}"')
            self._refresh_list()
            self.info_label("delete", f"Sticky `{title}` has been removed", LabelColor.INFO.value)
        elif not exists:
            self.info_label("info", "You have no active selection", LabelColor.WARNING.value)
        else:
            self.info_label("succes", "Oops. Something went wrong", LabelColor.ERROR.value)

    def edit(self):
        exists = self.stickies_view.selectedItems()
        if exists:
            title = self._get_title_from_item(self.stickies_view.currentItem())
            title, content, priority, *_ = self.model.select('title',
                                                             f"'{title}'")[0]
            self.title_ln.setText(title)
            self.content_ln.setText(content)
            self.priority_ln.setText(str(priority))

            self._disable_priority_direction_btn(
                int(self.priority_ln.text()),
                self.priority_up_btn,
                self.priority_down_btn
            )

            self.info_label("info", f"Sticky `{title}` is being edited", LabelColor.INFO.value)
        elif not exists:
            self.info_label("info", "You have no active selection", LabelColor.WARNING.value)
        else:
            self.info_label("succes", "Oops. Something went wrong", LabelColor.ERROR.value)

    def change_done_status(self, is_done: bool):
        if self.stickies_view.selectedItems():
            title = self._get_title_from_item(self.stickies_view.currentItem())
            if is_done:
                self._make_command(f'set_done -t "{title}"')
            elif not is_done:
                self._make_command(f'set_undone -t {title}')
            self._refresh_list()
            msg = f"Status of `{title}` has beed changed!"
            self.info_label("success", msg, LabelColor.SUCCESS.value)
        elif not is_done:
            self.info_label("info", "You have no active selection", LabelColor.WARNING.value)
        else:
            self.info_label("info", "Oops. Something went wrong", LabelColor.ERROR.value)

    def handle_search_query(self):
        self._clear_selections()
        query = self.search_ln.text().strip()
        if query:
            self.stickies_view.selectedItems()
            for i in range(self.stickies_view.count()):
                current_item = self.stickies_view.item(i)
                title = self._get_title_from_item(current_item)
                if self.search_ln.text() in title:
                    current_item.setForeground(Qt.GlobalColor.green)
        else:
            self._clear_selections()


def gui(args: list, logger: logger.Logger, model: models.Model,
        configs: jsonwrapper.Handler) -> int:
    app = QApplication(args)
    ui = Stickies(logger, model, configs)
    ui.show()
    app.exec_()
