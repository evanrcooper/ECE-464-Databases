import requests
import os
import sys
import pathlib as pl
import db_utils as db
import db_init

database_path: str = '/evanr/ece464.sqlite3'
database_init_path: str = '/app/db_init.sql'

def main() -> None:
    if not db_init.db_init(database_path, database_init_path):
        raise Exception('Unable to initialize database')
    db_manager: db.DBManager = db.DBManager(database_path)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sys.stderr.write(str(e))
    except KeyboardInterrupt as k:
        sys.stderr.write(str(k))
        sys.stderr.write('User Interrupt\n')