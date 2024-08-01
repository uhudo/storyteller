import requests

endpoint = "http://127.0.0.1:3002/api/images"

generate_data = {
    'model': 'stabilityai/stable-diffusion-3-medium-diffusers',
    'prompt': 'Fantasy cloud world in the sky.',
    'negative_prompt': ""
}

with requests.post(endpoint, json=generate_data) as response:
    if response.status_code == 200:
        with open("data/test.png", 'wb') as f:
            f.write(response.content)
