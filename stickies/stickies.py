#!/home/mx-linux/Desktop/projects/stickies/.stickyvenv/bin/python
import sys
from cli.cli import cli
from pathlib import Path
from models import Model
from logger import Logger
from window.window import gui
from jsonwrapper import Handler
from actions.constants import BASE_DIR


config = {'quiet': 1, 'sort_by': 'priority'}
configs = Handler(Path(f"{BASE_DIR}/.config.json"), config)
configs.init()

logger = Logger(configs.get('quiet'))

model = Model(
    'notes',
    f'{BASE_DIR}/.',
    title='TEXT type UNIQUE',
    content='TEXT',
    priority='INTEGER',
    date_created='TEXT',
    date_edited='TEXT',
    done='INTEGER'
)
model.create_table()


def main(args: list):
    if len(args) > 1:
        cli(args, model, logger, configs)
    else:
        gui(args, model, logger, configs)


if __name__ == '__main__':
    args = sys.argv
    sys.exit(main(args))
