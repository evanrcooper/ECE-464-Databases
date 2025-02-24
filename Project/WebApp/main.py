import sqlite3 as sq3

conn = sq3.connect('/evanr/database.sqlite3')
try:
    conn.execute('CREATE TABLE if not exists test (r1 integer not null, r2 integer null);')
except Exception:
    pass
conn.execute('INSERT INTO test (r1, r2) values (1, 2), (4,5);')
conn.commit()
conn.close()

print('hi')