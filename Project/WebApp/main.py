import requests
import os
import sys
import pathlib as pl
import helper_scripts.db_utils as db
import helper_scripts.db_init as db_init

# database_path: str = '/evanr/ece464.sqlite3'
# database_init_path: str = '/app/db_init.sql'

database_directory_path: pl.Path = pl.Path('/evanr')
database_path: pl.Path = database_directory_path / 'ece464.sqlite3'
database_init_path: str = './db_init.sql'

def main() -> None:
    if not os.path.exists(database_path):
        if not db_init.db_init(database_path, database_init_path):
            raise Exception('Unable to initialize database\n')
    db_manager: db.DBManager = db.DBManager(database_path, database_directory_path)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sys.stderr.write(f'{e.__class__.__name__}: {str(e)}')
    except KeyboardInterrupt as k:
        sys.stderr.write(f'KeyboardInterrupt: {str(k)}')
        sys.stderr.write('User Interrupt\n')