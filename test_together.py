#!/usr/bin/env python
import requests
import json

api_key = 'key_CZrXHSX6cCdyxtiz9jyPB'
url = 'https://api.together.xyz/v1/chat/completions'

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

# Simple test without image
payload = {
    'model': 'meta-llama/Llama-Vision-Free',
    'messages': [
        {
            'role': 'user',
            'content': 'Hello, can you respond with a simple test message?'
        }
    ],
    'max_tokens': 100
}

print('Testing Together.ai API endpoint...')
print(f'URL: {url}')
print(f'API Key (first 10 chars): {api_key[:10]}...')
print(f'Headers: Authorization={headers["Authorization"][:20]}..., Content-Type={headers["Content-Type"]}')

try:
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    print(f'\nStatus Code: {response.status_code}')
    print(f'Response Headers:')
    for key, value in response.headers.items():
        print(f'  {key}: {value}')
    print(f'\nResponse Body:\n{response.text}')
except Exception as e:
    print(f'Error: {str(e)}')
    import traceback
    traceback.print_exc()
