import requests


def get_profile(base_url, headers):
    response = requests.get(f"{base_url}/api/auth/profile", json={}, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise response.raise_for_status()
