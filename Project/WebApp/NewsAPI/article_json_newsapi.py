import os
import sys
import requests
import json
import pandas
import numpy
import sqlite3

qs = {
    'software',
    'science',
    'technology',
    'politics',
    'economics',
    'sports',
    'math',
    'arts',
}

API_KEY: str = os.getenv('NewsAPI_KEY')
PAGE = 1

print(API_KEY)

for q in qs:
    url: str = f'https://newsapi.org/v2/everything?q={q}&apiKey={API_KEY}&page={PAGE}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        with open(f'./newsapi_articles_{q}.json', 'w') as f:
            json.dump(data, f, indent=4)
    else:
        print(f'Failed to fetch data, status code: {response.status_code}')
        exit(response.status_code)