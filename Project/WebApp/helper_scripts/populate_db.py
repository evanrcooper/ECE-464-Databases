import requests
import json
import datetime
import time

API_BASE = 'http://localhost:5000/api'

USERNAME = 'PLOS'
PASSWORD = '00000000'
JSON_PATH = './WebApp/plos_articles_scraped.json'

def create_account():
    response = requests.post(f'{API_BASE}/create_user', json={
        'username': USERNAME,
        'password': PASSWORD
    })
    print('User creation:', response.status_code, response.text)

def get_token():
    response = requests.post(f'{API_BASE}/login', json={
        'username': USERNAME,
        'password': PASSWORD
    })
    if response.status_code == 200:
        return response.json().get('token')
    print('Failed to get token')
    return None

def load_articles():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_article(token, article):
    headers = {'Authorization': f'Bearer {token}'}
    payload = {
        'token': token,
        'title': article['title'],
        'authors': article['authors'],
        'content': '(' + article['url'] + ')\n\n' + article['content'],
        'publish_date': article['publish_date']
    }
    response = requests.post(f'{API_BASE}/create_article', json=payload, headers=headers)
    return response.status_code, response.text

create_account()

token = get_token()
if not token:
    exit()

articles = load_articles()
print(f'Loaded {len(articles)} articles.')

success = 0
for i, article in enumerate(articles):
    status, text = create_article(token, article)
    if status == 200:
        print(f'[{i+1}] Created: {article['title'][:60]}')
        success += 1
    else:
        print(f'[{i+1}] Failed: {status} - {text}')
    time.sleep(1)

print(f'\n🎉 {success}/{len(articles)} articles created.')
