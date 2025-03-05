import sys
import sqlite3 as sq3

def db_init(database_path: str, database_init_path: str) -> bool:
    try:
        conn: sq3.Connection = sq3.connect(database_path)
        with open(database_init_path, 'r') as init_query:
            query: str = init_query.read()
        conn.executescript(query)
        conn.commit()
        conn.close()
    except Exception as e:
        sys.stderr.write(f'{e.__class__.__name__}: {str(e)}')
        sys.stderr.write('Unable to initialize database.\n')
        return False
    return True