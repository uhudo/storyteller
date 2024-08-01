import requests

generate_endpoint = 'http://127.0.0.1:3001/api/generate'
chat_endpoint = 'http://127.0.0.1:3001/api/chat'

generate_data = {
	'model': 'llama3.1',
	'stream': False,
	'prompt': 'Tell me about London.',
	'options': {
		'num_predict': 50
	}
}

stream_data = {
	'model': 'llama3.1',
	'stream': True,
	'prompt': 'Tell me about London.',
	'options': {
		'num_predict': 50
	}
}


with requests.post(generate_endpoint, json=generate_data) as response:
	response_data = response.json()
	print(response_data)


s = requests.Session()
with s.post(generate_endpoint, json=stream_data, stream=True) as response:
	for line in response.iter_lines():
		if line:
			print(line)

chat_data = {
	'model': 'llama3.1',
	'stream': False,
	'messages': [
		{"role": "system", "content": "You are a helpful assistant."},
		{"role": "user", "content": "Why is the sky blue?"}
	],
	'options': {
		'num_predict': 50
	}
}

chat_stream_data = {
	'model': 'llama3.1',
	'stream': True,
	'messages': [
		{"role": "system", "content": "You are a helpful assistant."},
		{"role": "user", "content": "Why is the sky blue?"}
	],
	'options': {
		'num_predict': 50
	}
}

with requests.post(chat_endpoint, json=chat_data) as response:
	response_data = response.json()
	print(response_data['message']['content'])


s = requests.Session()
with s.post(chat_endpoint, json=chat_stream_data, stream=True) as response:
	for line in response.iter_lines():
		if line:
			print(line)
