import numpy as np
import pandas as pd
import requests
import os
import sqlite3 as sq3
import pathlib as pl

database_path: str = '/evanr/ece464.sqlite3'
database_init_path: str = '/app/db_init.sql'

def main() -> None:
    conn: sq3.Connection = sq3.connect(database_path)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)