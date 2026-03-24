import subprocess
import os
import datetime
from pathlib import Path

def serve():
    model_path = "./models/Qwen3.5-4B-Q4_K_S.gguf"
    mmproj_path = "./models/mmproj-F16.gguf"
    subprocess.Popen([
        "llama-server",
        "-m", model_path,
        "--mmproj", mmproj_path,
        "--n-gpu-layers", "35",
        "--temp", "0.7",
        "--top-k", "20",
        "--top-p", "0.95",
        "--repeat-penalty", "1",
        "--repeat-last-n", "64",
        "--ctx-size", "65536",
        "--batch-size", "512",
        "--host", "127.0.0.1",
        "--port", "8080",
        "--threads", "8"
    ])

def sys_prompt():
    path = "main/system_prompt.txt"
    with open(path, "r") as file:
        i = file.read()
    date = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    prompt = i + "\n\nDate and Time: " + date
    return prompt