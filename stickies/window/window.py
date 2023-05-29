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
from typing import Literal
from actions.constants import LabelColor, get_icon
from PyQt5 import uic, QtGui
from PyQt5.QtGui import QFont
from actions.constants import VERSIONS
from actions.dbapi import (
    DB_ROW,
    FIELDS,
    DB_VALUES,
    sort_by,
    get_total,
    sanitize_entry,
    sanitize_command,
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


# TODO: Make search_lbl wider
class Stickies(QMainWindow):
    UIFILE = Path('window/untitled.ui')
    VIEW_SEPERATOR = '\n'
    THEME_COLOR = 'rgb(38, 147, 217)'

    def __init__(self, model: models.Model, logger: logger.Logger,
                 configs: jsonwrapper.Handler) -> None:
        super(Stickies, self).__init__()
        uic.loadUi(Stickies.UIFILE, self)
        self.app_icon = QtGui.QIcon(get_icon['Sticky'])
        self.setWindowIcon(self.app_icon)
        self.setWindowTitle(f"Stickies v{VERSIONS[-1]}")

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
        self.refresh_btn.setToolTip("Refresh")
        self.load_stickies(self.model.fetch_all())
        self.priority_ln.setReadOnly(True)
        self.priority_ln.setText('1')
        self.stickies_view.setSelectionMode(3)  # 3 -> ExtendedSelection
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
        self.total_stickies_lbl = self.findChild(QLabel, 'total_stickies_lbl')

        self.search_lbl = self.findChild(QLabel, 'search_lbl')
        self._update_search_lbl()
        self.total_stickies_lbl.setText(self.get_total_stickes())

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

    def get_total_stickes(self) -> str:
        return f"Total: {get_total(self.model)}"

    def _refresh_list(self):
        """Empties the whole list of stickies and reloads them
        """
        self.stickies_view.clear()
        self.load_stickies(self.model.fetch_all())
        self.total_stickies_lbl.setText(self.get_total_stickes())

    def _update_search_lbl(self):
        label = "Search:"
        self.search_lbl.setText(f"{label} ({self.configs.get('search_by')})")

    def _make_command(self, flags: str):
        os.system(f"./stickies.py {sanitize_command(flags)}")

    def _get_title_from_item(self, list_item) -> str:
        """By parsing the text of a sticky as it's represented in the list,
        this function extracts the title ONLY

        :param list_item: A list item
        :type list_item: QListItem
        :return: Title
        :rtype: str
        """
        exlude = len("Title: ")
        item_text = list_item.text()
        title = item_text.split(Stickies.VIEW_SEPERATOR)[0][exlude:]
        return title

    def _info_label(self, header: str, msg: str, rgb: tuple[int], label: QLabel, seconds: int = 3):
        """Interface for self.info_label. DO NOT USE DIRECTLY.
        It'll freeze the GUI
        """
        r, g, b = rgb
        label.setStyleSheet(f"color: rgb({r}, {g}, {b});")
        label.setText(f"[{header.upper()}]: {msg}")
        time.sleep(seconds)
        label.setText('')
        label.setStyleSheet("")

    def _add_stickie_fields(self, stickies: DB_VALUES)\
            -> Generator[DB_ROW, None, None]:
        """Visually add the type of each thing a sticky stores.

        :yield: A Sticky with its according labels
        :rtype: DB_ROW
        """
        other = []
        for sticky in stickies:
            temp = map(
                lambda i: f"{FIELDS[i[0]].capitalize()}: {i[1]}",
                enumerate(sticky)
            )
            other.append(list(temp))
        yield from other

    def _sort_stickies(self, stickies: DB_VALUES)\
            -> Generator[DB_ROW, None, None]:
        """This function re-orders the stickies to the way that
        is configed by the user

        :yield: The stickies row by row
        :rtype: DB_ROW
        """
        sort_method = self.configs.get('sort_by')

        sorted_stickies = stickies
        reversed = self.reverse_order_cmd.isChecked()
        yield from sort_by(sort_method, sorted_stickies, reversed)

    def _clear_selections(self):
        """Set the color of the stickies as QListItems back to the
        default (black)
        """
        self.stickies_view.selectedItems()
        for i in range(self.stickies_view.count()):
            current_item = self.stickies_view.item(i)
            current_item.setForeground(Qt.GlobalColor.black)

    def view_settings(self):
        """Create a string with the saved configurations and display them
        in a seperate MessageBox
        """
        msg = '\n'.join(
            map(lambda i: f"{i[0]}:\t{i[1]}", self.configs.read().items())
        )
        QMessageBox.information(self, 'Info', msg)

    def edit_settings(self):
        """Opens the `Edit` window and hanldles any changes
        that need to be made in the config file
        """
        def set_values(config_key, config_value):
            config_value.clear()
            key = config_key.currentText()
            for value in settings[key]:
                config_value.addItem(str(value))
            config_value.setCurrentText(str(self.configs.get(key)))

        def save_changes(config):
            key = config_key.currentText()
            value = config_value.currentText()
            config.edit(
                key,
                value,
                int if config_value.currentText().isnumeric() else str,
            )
            info_font = QFont("Times New Roman", 13)
            info_font.setBold(True)
            info_lbl.setFont(info_font)
            info_lbl.setWordWrap(True)

            self.info_label(
                'SUCCESS', f"`{key.title()}` has been set to `{value}`",
                LabelColor.SUCCESS.value,
                info_lbl,
            )

        assert len(self.configs.read()) == 3, "Unhandled setting"
        height, width = 300, 300
        layout = QVBoxLayout()
        dialog = QDialog()
        dialog.setWindowIcon(self.app_icon)
        info_lbl = QLabel(dialog)

        dialog.setWindowTitle("Edit settings")
        dialog.setLayout(layout)
        dialog.setFixedSize(QSize(height, width))

        ok_btn = QPushButton(dialog, text="Ok")

        ok_btn.clicked.connect(
            lambda: save_changes(self.configs)
        )

        config_value = QComboBox(dialog)
        config_key = QComboBox(dialog)
        layout.addWidget(config_key)
        layout.addWidget(config_value)
        config_key.activated.connect(lambda: set_values(config_key, config_value))

        settings = {
            'quiet': range(1, Note.MAX_PRIORITY + 1),
            'sort_by': FIELDS,
            'search_by': FIELDS,
        }

        for key in settings:
            config_key.addItem(key)

        set_values(config_key, config_value)
        layout.addWidget(ok_btn)
        layout.addWidget(info_lbl)

        dialog.exec_()
        self._update_search_lbl()
        self._refresh_list()

    def info_label(self, header: str, msg: str, rgb: tuple[int], label: QLabel, seconds: int = 3):
        """Shows a message at a given label for `x` ammount of seconds

        :param header: The header of the message [HEADER]: ...
        :type header: str
        :param msg: The message to be written [...]: msg
        :type msg: str
        :param rgb: The color that the msg will be displayed
        :type rgb: tuple[int]
        :param label: The label that the message will be displayed by
        :type label: QLabel
        :param seconds: The time that the msg will be shown for, defaults to 3
        :type seconds: int, optional
        """
        (
            thr.Thread(target=self._info_label, args=(header, msg, rgb, label, seconds))
            .start()
        )

    def load_stickies(self, stickies: DB_VALUES):
        """Loads all the saved stickies from the db and adds the to the GUI
        """
        stickies = self._sort_stickies(stickies)
        stickies = self._add_stickie_fields(stickies)

        for sticky in stickies:
            self.stickies_view.addItem(
                Stickies.VIEW_SEPERATOR.join(map(str, sticky))
            )

    def save(self):
        """Takes all the input fields from the user and saves them in the db
        """
        title = self.title_ln.text()
        if not title:
            msg = "Title cannon be empty"
            self.info_label("WARNING", msg, LabelColor.ERROR.value, self.info_lbl)
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
                self.info_label("edit", msg, LabelColor.SUCCESS.value, self.info_lbl)
            else:
                flags = f'add -t "{title}" -c "{content}" -p {priority}'
                self._make_command(flags)
                msg = f"Sticky `{title}` is now added"
                self.info_label('new', msg, LabelColor.SUCCESS.value, self.info_lbl)

        self._refresh_list()
        self.title_ln.setText('')

    def cancel(self):
        """Resets all the input fields
        """
        self.priority_ln.setText('1')
        inputs = (self.title_ln, self.content_ln)

        for input in inputs: input.setText('')

    def set_priority(self, direction: Literal['up', 'down']):
        """Handles the `priority` field

        :param direction: Wheather we're adding or substracting for the field
        :type direction: str
        """
        assert direction in ('up', 'down'), f"Invalid direction `{direction}`"
        line = int(self.priority_ln.text())

        if direction == 'up' and line < Note.MAX_PRIORITY:
            next_num = line + 1
            self.priority_ln.setText(str(next_num))
        elif direction == 'up' and line + 1 > Note.MAX_PRIORITY:
            self.priority_ln.setText('1')

        elif direction == 'down' and line > 1:
            prev_num = line - 1
            self.priority_ln.setText(str(prev_num))
        elif direction == 'down' and line - 1 < 1:
            self.priority_ln.setText('5')

    def delete_done(self):
        flags = 'clear_done'
        self._make_command(flags)
        self._refresh_list()
        msg = "All items marked as `done` have been removed"
        self.info_label("info", msg, LabelColor.INFO.value, self.info_lbl)

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
            msg = f"Sticky `{title}` has been removed"
            self.info_label("info", msg, LabelColor.WARNING.value, self.info_lbl)
        elif not exists:
            msg = "You have no active selection"
            self.info_label("info", msg, LabelColor.ERROR.value, self.info_lbl)
        else:
            msg = "Oops. Something went wrong"
            self.info_label("succes", msg, LabelColor.ERROR.value, self.info_lbl)

    def edit(self):
        """Fill the inputs fields with the selected sticky.
        This function will overwrite a sticky if the title is un-changed.
        Otherwise it'll just create a new one
        """
        exists = self.stickies_view.selectedItems()
        if exists:
            title = self._get_title_from_item(self.stickies_view.currentItem())
            title, content, priority, *_ = self.model.select(
                'title',
                f"'{sanitize_entry(title)}'"
            )[0]

            self.title_ln.setText(title)
            self.content_ln.setText(content)
            self.priority_ln.setText(str(priority))
            msg = f"Sticky `{title}` is being edited"
            self.info_label("info", msg, LabelColor.INFO.value, self.info_lbl)
        elif not exists:
            msg = "You have no active selection"
            self.info_label("info", msg, LabelColor.WARNING.value, self.info_lbl)
        else:
            msg = "Oops. Something went wrong"
            self.info_label("succes", msg, LabelColor.ERROR.value, self.info_lbl)

    def change_done_status(self, is_done: bool):
        if self.stickies_view.selectedItems():
            title = self._get_title_from_item(self.stickies_view.currentItem())
            if is_done:
                self._make_command(f'set_done -t "{title}"')
            elif not is_done:
                self._make_command(f'set_undone -t "{title}"')
            self._refresh_list()
            msg = f"Status of `{title}` has beed changed!"
            self.info_label("success", msg, LabelColor.SUCCESS.value, self.info_lbl)
        elif not self.stickies_view.selectedItems():
            msg = "You have no active selection"
            self.info_label("info", msg, LabelColor.WARNING.value, self.info_lbl)
        else:
            msg = "Oops. Something went wrong"
            self.info_label("info", msg, LabelColor.ERROR.value, self.info_lbl)

    def handle_search_query(self):
        """This function is bound with the `search` input field
        and on every input it'll display the stickies that match the query
        and temporarily remove the rest
        """
        matching = []
        query = self.search_ln.text()
        stickies = self.model.fetch_all()
        if query:
            self.stickies_view.clear()
            for sticky in stickies:
                if query in str(self.model.filter_row([sticky], self.configs.get('search_by'))):
                    matching.append(sticky)
            if matching:
                self.load_stickies(matching)
            elif not matching:
                self.stickies_view.addItem(f"<Nothing found matching `{query}`>")
        else:
            self._refresh_list()


def gui(args: list, logger: logger.Logger, model: models.Model,
        configs: jsonwrapper.Handler) -> int:
    app = QApplication(args)
    ui = Stickies(logger, model, configs)
    ui.show()
    app.exec_()
