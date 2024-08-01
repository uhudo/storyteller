import json
import toml
from threading import Thread
import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Union, Dict

from transformers import pipeline, AutoTokenizer, TextIteratorStreamer
import torch


def create_app(text_pipe, tokenizer):
    app = FastAPI()

    class Options(BaseModel):
        num_predict: int = 256

    class GenerateRequest(BaseModel):
        model: str
        prompt: Union[List[str], str]
        options: Options = Options()
        stream: bool = False

    class ChatRequest(BaseModel):
        model: str
        messages: List[Dict[str, str]]
        options: Options = Options()
        stream: bool = False

    @app.post("/api/generate")
    def generate(gen_args: GenerateRequest):
        if gen_args.stream:
            print("Generate stream request")
            streamer = TextIteratorStreamer(
                tokenizer=tokenizer,
                timeout=60.0,
                skip_prompt=True,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False
            )
            kwargs = dict(
                text_inputs=gen_args.prompt,
                max_new_tokens=gen_args.options.num_predict,
                eos_token_id=tokenizer.eos_token_id,
                streamer=streamer
            )
            thread = Thread(target=text_pipe, kwargs=kwargs)
            thread.start()

            def data_stream():
                for new_text in streamer:
                    yield json.dumps({"response": new_text}) + '\n'

            return StreamingResponse(data_stream(), media_type="application/x-ndjson")
        else:
            print("Generate request")
            generation = text_pipe(gen_args.prompt,
                                   max_new_tokens=gen_args.options.num_predict,
                                   eos_token_id=tokenizer.eos_token_id
                                   )
            generated_text = generation[0]['generated_text'][len(gen_args.prompt):]
            return {"response": generated_text}

    @app.post("/api/chat")
    def generate(chat_args: ChatRequest):
        if chat_args.stream:
            print("Chat stream request")
            streamer = TextIteratorStreamer(
                tokenizer=tokenizer,
                timeout=60.0,
                skip_prompt=True,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False
            )
            kwargs = dict(
                text_inputs=chat_args.messages,
                max_new_tokens=chat_args.options.num_predict,
                eos_token_id=tokenizer.eos_token_id,
                streamer=streamer
            )
            thread = Thread(target=text_pipe, kwargs=kwargs)
            thread.start()

            def data_stream():
                for new_text in streamer:
                    yield json.dumps({"message": {"role": "assistant", "content": new_text}}) + '\n'

            return StreamingResponse(data_stream(), media_type="application/x-ndjson")
        else:
            print("Chat request")
            generation = text_pipe(chat_args.messages,
                                   max_new_tokens=chat_args.options.num_predict,
                                   eos_token_id=tokenizer.eos_token_id
                                   )
            generated_text = generation[0]['generated_text'][-1]
            return {"message": generated_text}

    return app


if __name__ == "__main__":
    config = toml.load("config.toml")

    model = "meta-llama/Meta-Llama-3.1-8B-Instruct"
    tokenizer = AutoTokenizer.from_pretrained(model)
    generation_pipe = pipeline(
        "text-generation",
        model=model,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    app = create_app(generation_pipe, tokenizer)
    uvicorn.run(app, host=config['llama']['host'], port=config['llama']['port'])
