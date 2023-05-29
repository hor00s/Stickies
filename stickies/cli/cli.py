import os
import models
import logger
import sqlite3
import datetime
import jsonwrapper
from enum import Enum
from notes.note import Note
from logger import get_color
from actions.dbapi import (
    sanitize_entry,
    get_total,
    sort_by,
)


# Holds the ammount of documents printed in `help_text` to keep them always synced
len_docs = -1


class HelpTags(Enum):
    help_add = """
    Command: add
    Params:
        -t <title> -c <content> -p <priority>
    Description:
        Adds a new sticky note to your collection"""

    help_remove = """
    Command: remove
    Params:
        -t <title>
    Description:
        Deletes a sticky note from your collection"""

    purge_all_help = """
    Command: purge_all
    Params:
        None
    Description:
        Deletes all sticky notes"""

    help_edit = """
    Command: edit
    Params:
        -t <title>
    Optional:
        -sc <new-content> -sp <new-priority>
    Description:
        Edit a sticky's field"""

    peek_help = """
    Command: peek
    Params:
        -t <title>
    Description:
        See a saved sticky"""

    help_set_done = """
    Command: set_done
    Params:
        -t <title>
    Description:
        Set a sticky to `done`"""

    help_set_undone = """
    Command: set_undone
    Params:
        -t <title>
    Description:
        Set a sticky to `undone`"""

    show_all_help = """
    Command: show_all
    Params:
        -r <reverse>
    Description:
        Get a list of all your stickies"""

    clear_done_help = """
    Command: clear_done
    Params:
        None
    Description:
        Delete all the stickes that are marked as `done`
    """

    get_total_help = """
    Command: get_total
    Params:
        None
    Description:
        Get total stickies saved
    """

    config_restore_help = """
    Command: config_restore
    Params:
        None
    Description:
        Restore to the original settings
    """

    config_all_help = """
    Command: config_all
    Params:
        None
    Description:
        See all the saved configurations
    """

    config_get_help = """
    Command: config_get
    Params:
        -k <key>
    Description:
        Get the value of the selected configuration
    """

    config_edit_help = """
    Command: config_edit
    Params:
        -k <key> -v <value> -t <type>
    Description:
        Edit a configuration value
    """


def lines(count: bool = True):
    global len_docs
    if count:
        len_docs += 1
    return '-' * os.get_terminal_size().columns


help_text = f"""{get_color('yellow')}
{lines()}
{HelpTags.help_add.value}
{lines()}
{HelpTags.help_remove.value}
{lines()}
{HelpTags.purge_all_help.value}
{lines()}
{HelpTags.help_edit.value}
{lines()}
{HelpTags.peek_help.value}
{lines()}
{HelpTags.help_set_done.value}
{lines()}
{HelpTags.help_set_undone.value}
{lines()}
{HelpTags.clear_done_help.value}
{lines()}
{HelpTags.get_total_help.value}
{lines()}
{HelpTags.show_all_help.value}
{lines()}
{HelpTags.config_restore_help.value}
{lines()}
{HelpTags.config_all_help.value}
{lines()}
{HelpTags.config_get_help.value}
{lines()}
{HelpTags.config_edit_help.value}
{lines()}{get_color('reset')}"""


assert len_docs == len(HelpTags), "An assigned document is not registered in `help_text`"


def parser(args):
    command = args[1]
    args = args[2:]
    params = {args[i]: args[i + 1] for i in range(0, len(args) - 1, 2)}
    return command, params


class MetaInterface(type):
    def __new__(self, name, bases, attrs):
        # Responsible to keep the cli commands in sync with the documentation
        assert len(tuple(attr for attr in attrs if not attr.startswith('_'))) == len(HelpTags),\
            "Unhandled OR un-documented command"

        return type(name, bases, attrs)


class CliInterface(metaclass=MetaInterface):
    def __init__(self, params: dict, logger: logger.Logger,
                 model: models.Model, handler: jsonwrapper.Handler) -> None:
        self.logger = logger
        self.params = params
        self.model = model
        self.handler = handler

    def _print_sticky(self, id, title, content, priority, date_created, date_edited, done):
        attr = {
            True: ('✔', get_color('green')),
            False: ('✘', get_color('red')),
        }

        self.logger.custom(
            f"{id = }, {title = }, {content = },\
 {priority = }, {date_created = }, {date_edited = }",
            attr[done][0],
            attr[done][1],
        )

    def _print_config(self, key, value):
        self.logger.custom(f'{key} -> {value}', 'CONFIG', get_color('cyan'))

    def add(self):
        try:
            try:
                title, content, priority = (
                    self.params['-t'],
                    self.params['-c'],
                    int(self.params['-p'])
                )

                n = Note(
                    sanitize_entry(title),
                    sanitize_entry(content),
                    priority,
                )
                self.model.insert(
                    title=n.title,
                    content=n.content,
                    priority=n.priority,
                    date_created=n.date_created,
                    date_edited=n.date_created,
                    done=n.done
                )
                self.logger.success(f"Sticly `{title}` was added successfully!")
            except KeyError:
                self.logger.error(HelpTags.help_add.value)
        except sqlite3.IntegrityError:
            self.logger.warning(f"A sticky with the title `{title}` already exists.")

    def remove(self):
        try:
            title_org = self.params['-t']
            title = sanitize_entry(title_org)
            self.model.execute(f"DELETE FROM {self.model.name} WHERE title='{title}'")
            self.logger.success(f"Sticky `{title_org}` was removed successfully")
        except KeyError:
            self.logger.error(HelpTags.help_remove.value)

    def edit(self):
        date_edited = datetime.datetime.now().strftime("%d/%m/%Y")
        try:
            title = sanitize_entry(self.params['-t'])
            cols = self.params.copy()

            del cols['-t']
            if cols:
                if '-sc' in cols:
                    self.model.edit(f"content='{sanitize_entry(cols['-sc'])}'", f"title='{title}'")
                if '-sp' in cols:
                    self.model.edit(f"priority={int(cols['-sp'])}", f"title='{title}'")
                self.model.edit(f"date_edited='{date_edited}'", f"title='{title}'")
                self.logger.success(f"Sticky {title} was edited succesfuly")
            else:
                self.logger.info("Not enough arguments to edit")
        except KeyError:
            self.logger.error(HelpTags.help_edit.value)

    def peek(self):
        try:
            title = self.params['-t']
            row = self.model.select('title', f"'{title}'")
            if not row:
                self.logger.info(f"No sticky with the the `{title}` was found")
                return
            id = self.model.filter_row(row, 'id')
            title = self.model.filter_row(row, 'title')
            content = self.model.filter_row(row, 'content')
            priority = self.model.filter_row(row, 'priority')
            date_created = self.model.filter_row(row, 'date_created')
            date_edited = self.model.filter_row(row, 'date_edited')
            done = self.model.filter_row(row, 'done')

            self._print_sticky(id, title, content, priority, date_created, date_edited, done)
        except KeyError:
            self.logger.error(HelpTags.peek_help.value)

    def set_done(self):
        try:
            title_org = self.params['-t']
            title = sanitize_entry(title_org)
            if not self.model.select('title', f"'{title}'"):
                self.logger.info(f"There is no sticky with the name `{title}`")
                return
            self.model.edit('done=1', f"title='{title}'")
            self.logger.success(f"Sticky `{title_org}` is set to `done`")
        except KeyError:
            self.logger.error(HelpTags.help_set_done.value)

    def set_undone(self):
        try:
            title_org = self.params['-t']
            title = sanitize_entry(title_org)
            if not self.model.select('title', f"'{title}'"):
                self.logger.info(f"There is no sticky with the name `{title}`")
                return
            self.model.edit('done=0', f"title='{title}'")
            self.logger.success(f"Sticky `{title_org}` is set to `un-done`")
        except KeyError:
            self.logger.error(HelpTags.help_set_undone.value)

    def show_all(self):
        try:
            rows = self.model.fetch_all()
            if rows:
                reverse = self.params['-r']
                stickies = sort_by(self.handler.get('sort_by'), rows, eval(reverse.title()))
                for row in stickies:
                    id = self.model.filter_row([row], 'id')
                    title = self.model.filter_row([row], 'title')
                    content = self.model.filter_row([row], 'content')
                    priority = self.model.filter_row([row], 'priority')
                    date_created = self.model.filter_row([row], 'date_created')
                    date_edited = self.model.filter_row([row], 'date_edited')
                    done = self.model.filter_row([row], 'done')

                    self._print_sticky(id, title, content, priority,
                                       date_created, date_edited, done)
            else:
                self.logger.info("Seems like you've nothing to do!")
        except KeyError:
            self.logger.error(HelpTags.show_all_help.value)

    def clear_done(self):
        total = self.model.execute(f"SELECT * FROM {self.model.name} WHERE done=1", fetch=True)
        self.model.execute(f"DELETE FROM {self.model.name} WHERE done=1")
        self.logger.success(f"All fields set to `done` are deleted. (Total: {len(total)})")

    def purge_all(self):
        total = self.model.execute(f"SELECT * FROM {self.model.name}", fetch=True)
        self.model.execute(f"DELETE FROM {self.model.name}")
        self.logger.warning(f"All fields are purged. (Total: {len(total)})")

    def get_total(self):
        total = get_total(self.model)
        self.logger.info(f"Total stickes saved: {total}")

    def config_edit(self):
        try:
            key, value, type_ = self.params['-k'], self.params['-v'], self.params['-t']
            self.handler.edit(key, value, eval(type_))
            self.logger.success(f"`{key}` has been set to {value}")
        except KeyError:
            self.logger.error(HelpTags.config_edit_help.value)

    def config_restore(self):
        self.handler.restore_default()
        self.handler.restore_default()
        self.logger.warning("Config file is restored back to the original form")

    def config_all(self):
        data = self.handler.read()
        for key, value in data.items():
            self._print_config(key, value)

    def config_get(self):
        try:
            key = self.params['-k']
            data = self.handler.read()
            if key in data:
                value = self.handler.get(key)
                self._print_config(key, value)
            else:
                self.logger.warning(f"There is no configuration with the name `{key}`")
        except KeyError:
            self.logger.error(HelpTags.config_get_help.value)


def cli(args: list, model: models.Model, logger: logger.Logger, configs: jsonwrapper.Handler):
    command, params = parser(args)
    interface = CliInterface(params, logger, model, configs)

    commands = {
        'help': lambda: print(help_text),
        # STICKY RELATED
        'show_all': interface.show_all,
        'clear_done': interface.clear_done,
        'purge_all': interface.purge_all,
        'add': interface.add,
        'remove': interface.remove,
        'edit': interface.edit,
        'peek': interface.peek,
        'set_done': interface.set_done,
        'set_undone': interface.set_undone,
        'get_total': interface.get_total,
        # CONFIG RELATED
        'config_edit': interface.config_edit,
        'config_restore': interface.config_restore,
        'config_all': interface.config_all,
        'config_get': interface.config_get,
    }

    commands.get(command, 'help')()
