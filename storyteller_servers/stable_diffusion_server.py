import toml
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Union
import torch
from diffusers import StableDiffusion3Pipeline


def create_app(image_pipe):
    app = FastAPI()

    class ImageRequest(BaseModel):
        model: str
        prompt: Union[List[str], str]
        negative_prompt: Union[List[str], str] = ""

    @app.post("/api/images")
    def generate(image_args: ImageRequest):
        with torch.autocast('cuda', dtype=torch.float16):
            image = image_pipe(
                image_args.prompt,
                negative_prompt=image_args.negative_prompt,
                num_inference_steps=28,
                guidance_scale=7.0
            ).images[0]
        image.save("data/image.png")
        return FileResponse("data/image.png")

    return app


if __name__ == "__main__":
    config = toml.load("config.toml")

    pipe = StableDiffusion3Pipeline.from_pretrained(
        "stabilityai/stable-diffusion-3-medium-diffusers",
        torch_dtype=torch.float16,
        add_prefix_space=False
    )
    pipe = pipe.to("cuda")

    app = create_app(pipe)
    print("OK")
    uvicorn.run(app, host=config['stable_diffusion']['host'], port=config['stable_diffusion']['port'])
