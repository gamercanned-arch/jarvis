# SETUP

---
## Step 1. setup a virtual environment
Press `ctrl + shift + P`
Select `Python: Create Environment` and choose `venv` as the environment type.
Choose your preffered python version (3.10.x).

After set up, Open terminal, or press `Ctrl + shift + ~` to open terminal.
If `.venv` is activated, send command

```Bash
pip install -r requirements.txt
```
---
## Step 2. Setup llama.cpp

Run the following commands in a separate terminal (windows)

> [!NOTE]   
> Open powershell or cmd from the start menu as admin

```Bash
winget install llama.cpp
```
---
## Step 3. Download the model
Run the file: `setup/download_models.py`
or in terminal (after activation of `.venv`)

```Bash
python setup/download_models.py
```

---
## Step 4. Install mcp-filesystem

Install the Python-based MCP filesystem server:

```Bash
pip install mcp-filesystem
```

---

## Step 5. All done, run the loop


Run the file: `main/main.py`
or in terminal (after activation of `.venv`)

```Bash
python main/main.py
```
---