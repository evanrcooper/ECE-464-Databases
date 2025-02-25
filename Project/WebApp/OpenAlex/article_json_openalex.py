import json
import requests
import os
import datetime

N_ARTICLES: int = 100
SEED: int = 101 ^ 1010101

if not os.path.exists(f'./openalex_articles_{N_ARTICLES}.json'):
    url = f'https://api.openalex.org/works?filter=open_access.is_oa:true&sample={N_ARTICLES}&per-page={N_ARTICLES}&mailto=evan.rosenfeld@cooper.edu&seed={SEED}'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        with open(f'./openalex_articles_{N_ARTICLES}.json', 'w') as f:
            json.dump(data, f, indent=4)
    else:
        print(f'Failed to fetch data, status code: {response.status_code}')
        exit(response.status_code)

with open(f'./openalex_articles_{N_ARTICLES}.json', 'r') as json_file:
    article_request: json.JSONDecoder = json.load(json_file)

meta: json.JSONDecoder = article_request['meta']
results: list = article_request['results']

for result in results:
    try:
        id: str = result['id']
        if result['language'] != 'en' or not result['has_fulltext']: # skip non-ideal entries
            continue
        title: str = result['display_name'] # or result['title']
        published_date: datetime.date = datetime.date(*[int(n) for n in result['publication_date'].split('-')])
        kws: list[str] = []
        for kw in result['keywords']:
            kws.append(kw['id'].split('/')[-1])
        for authorship in result['authorships']:
            if authorship['author_position'] == 'first':
                author_name: str = authorship['author']['display_name']
                break
        else:
            continue
        if author_name is None or author_name == '' or title is None or title == '':
            continue
    except Exception as e:
        continue
    except KeyboardInterrupt as k:
        break
    
    print(id)
    print(title)
    print(author_name)
    print(published_date)
    print(kws)
    print()
    # insert_article()