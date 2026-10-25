"""Serve an open model on Modal behind an OpenAI-compatible endpoint (vLLM).

One deploy per model, so the capability ladder is two apps side by side:

    bash scripts/setup_machine.sh     # login, API key secret and both deploys

or by hand:

    pip install modal && modal setup                      # once
    modal secret create vllm-api-key VLLM_API_KEY=<any random string>
    MODEL=Qwen/Qwen3-8B      GPU=L40S modal deploy infra/modal_vllm.py
    MODEL=Qwen/Qwen3-32B-FP8 GPU=H100 modal deploy infra/modal_vllm.py

Each deploy prints a URL like https://<workspace>--collusion-qwen3-8b-serve.modal.run.
Point the harness at it:

    export LLM_BASE_URL="https://<...>.modal.run/v1"
    export LLM_API_KEY="<the same random string>"

Containers scale to zero after SCALEDOWN seconds idle, so credits are only
spent while sessions run. Weights are cached in a Modal Volume, so only the
first cold start downloads them.
(On PowerShell: $env:MODEL="Qwen/Qwen3-8B"; $env:GPU="L40S"; modal deploy ...)
"""

import os
import subprocess

import modal

MODEL = os.environ.get("MODEL", "Qwen/Qwen3-8B")
GPU = os.environ.get("GPU", "L40S")
MAX_MODEL_LEN = int(os.environ.get("MAX_MODEL_LEN", "32768"))  # Qwen3 native context
SCALEDOWN = 300
PORT = 8000

slug = MODEL.split("/")[-1].lower().replace(".", "-").replace("_", "-")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("vllm==0.9.1", "huggingface_hub[hf_transfer]==0.32.0")
    # Baked into the image so the remote container sees the same MODEL/GPU.
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1", "MODEL": MODEL, "GPU": GPU,
          "MAX_MODEL_LEN": str(MAX_MODEL_LEN)})
)
hf_cache = modal.Volume.from_name("hf-cache", create_if_missing=True)
vllm_cache = modal.Volume.from_name("vllm-cache", create_if_missing=True)

app = modal.App(f"collusion-{slug}")


@app.function(
    image=image,
    gpu=GPU,
    scaledown_window=SCALEDOWN,
    timeout=60 * 60,
    secrets=[modal.Secret.from_name("vllm-api-key")],
    volumes={"/root/.cache/huggingface": hf_cache, "/root/.cache/vllm": vllm_cache},
)
@modal.concurrent(max_inputs=64)  # many parallel sessions share one GPU
@modal.web_server(port=PORT, startup_timeout=20 * 60)
def serve():
    subprocess.Popen([
        "vllm", "serve", MODEL,
        "--served-model-name", MODEL,
        "--host", "0.0.0.0",
        "--port", str(PORT),
        "--api-key", os.environ["VLLM_API_KEY"],
        "--max-model-len", str(MAX_MODEL_LEN),
    ])
