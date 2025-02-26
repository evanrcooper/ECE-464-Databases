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
NUM_PAGES = 4

for q in qs:
    for page in range(NUM_PAGES):
        url: str = f'https://newsapi.org/v2/everything?q={q}&apiKey={API_KEY}&page={page+1}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            with open(f'./Data/newsapi_articles_{q}_pg{page+1}.json', 'w') as f:
                json.dump(data, f, indent=4)
        else:
            print(f'Failed to fetch data, status code: {response.status_code}')
            print(url)
            exit(response.status_code)