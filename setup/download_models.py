# Download models lil bro

from huggingface_hub import hf_hub_download

repo_id = "Uunsloth/Qwen3.5-4B-GGUF"
model = "Qwen3.5-4B-Q4_K_S.gguf"
mmproj = "mmproj-F16.gguf"

hf_hub_download(repo_id=repo_id, filename=model, local_dir="./models")
hf_hub_download(repo_id=repo_id, filename=mmproj, local_dir="./models")

print("Models downloaded successfully!")