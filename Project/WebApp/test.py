import requests
import os
import sys
import pathlib as pl
import helper_scripts.db_utils as db
import helper_scripts.db_init as db_init

database_directory_path: pl.Path = pl.Path('/evanr')
database_path: pl.Path = database_directory_path / 'ece464.sqlite3'
database_init_path: str = './db_init.sql'


if not os.path.exists(database_path):
    if not db_init.db_init(database_path, database_init_path):
        raise Exception('Unable to initialize database\n')
db_manager: db.DBManager = db.DBManager(database_path, database_directory_path)
print(db_manager.create_user('admin', 'ffffffff'))
x = db_manager.log_in('admin', 'ffffffff')
print(x)
token = x[1]
