import requests

r = requests.get('http://localhost:8000/feeds/gossip?limit=5')
print('Status:', r.status_code)
if r.status_code == 200:
    data = r.json()
    print('Total:', data.get('total'))
    print('Articles:', len(data.get('articles', [])))
    for i, article in enumerate(data.get('articles', [])[:3], 1):
        print(f"{i}. {article.get('title', '')[:60]}")
else:
    print('Error:', r.text[:200])

