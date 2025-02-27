import aiohttp
import json


async def llama_generate_query(endpoint, payload, num_predict, index, count):
    data = {
        "model": "llama3.1",
        "stream": False,
        "prompt": payload,
        "options": {
            "num_predict": num_predict
        }
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, json=data) as response:
            res = await response.json()
            return {"index": index, "data": res["response"], "count": count}


async def llama_generate_stream(endpoint, payload, num_predict, index, count, queue):
    data = {
        "model": "llama3.1",
        "stream": True,
        "prompt": payload,
        "options": {
            "num_predict": num_predict
        }
    }
    i = 0
    async with aiohttp.ClientSession(raise_for_status=True) as session:
        async with session.post(endpoint, json=data) as response:
            async for line in response.content:
                if line:
                    body = json.loads(line)
                    await queue.put({"index": index,
                                     "data": body["response"],
                                     "count": [count, i],
                                     "final": False})
                    i += 1
            await queue.put({"index": index,
                             "data": "",
                             "count": [count, i],
                             "final": True})


async def llama_chat_query(endpoint, payload, num_predict, index, count):
    data = {
        "model": "llama3.1",
        "stream": False,
        "messages": payload,
        "options": {
            "num_predict": num_predict
        }
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, json=data) as response:
            res = await response.json()
            return {"index": index, "data": res["message"]["content"], "count": count, "final": True}


async def llama_chat_stream(endpoint, payload, num_predict, index, count, queue):
    data = {
        "model": "llama3.1",
        "stream": True,
        "messages": payload,
        "options": {
            "num_predict": num_predict
        }
    }
    i = 0
    async with aiohttp.ClientSession(raise_for_status=True) as session:
        async with session.post(endpoint, json=data) as response:
            async for line in response.content:
                if line:
                    body = json.loads(line)
                    await queue.put({"index": index,
                                     "data": body["message"]["content"],
                                     "count": [count, i],
                                     "final": False})
                    i += 1
            await queue.put({"index": index,
                             "data": "",
                             "count": [count, i],
                             "final": True})


async def stable_diffusion_query(endpoint, prompt, negative_prompt, index, count):
    data = {
        "model": "stabilityai/stable-diffusion-3-medium-diffusers",
        "prompt": prompt,
        "negative_prompt": negative_prompt
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, json=data) as response:
            res = await response.content.read()
            return {"index": index, "data": res, "count": count}
