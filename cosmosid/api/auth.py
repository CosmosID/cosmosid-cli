import requests


def get_profile(base_url, api_key):
    response = requests.get(base_url + '/api/auth/profile', json={}, headers={'X-Api-Key': api_key})
    if response.status_code == 200:
        return response.json()
    else:
        raise response.raise_for_status()
