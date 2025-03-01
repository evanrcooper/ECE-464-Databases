import sqlite3 as sq3
import pickle
import numpy as np
import pandas as pd


def serialize_vector(vector: np.ndarray) -> bytes:
    return pickle.dumps(vector)

def deserialize_vector(data: bytes) -> np.ndarray:
    return pickle.loads(data)

conn = sq3.connect('/evanr/database.sqlite3')

cursor = conn.cursor()

# Create table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS vectors (
        id INTEGER PRIMARY KEY,
        vector BLOB
    )
''')

# Serialize and insert vector
vector = np.array([5.5, 6.6, 7.7], dtype=np.float32)
blob = serialize_vector(vector)

cursor.execute('INSERT INTO vectors (vector) VALUES (?)', (blob,))
conn.commit()

# Read and deserialize vector
cursor.execute('SELECT vector FROM vectors WHERE id = 1')
data = cursor.fetchone()[0]
retrieved_vector = deserialize_vector(data)

print("Retrieved Vector:", retrieved_vector)
cursor.close()
conn.close()
