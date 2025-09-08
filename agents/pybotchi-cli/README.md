# PyBotchi Files

Dedicated agents for cli commands execution.

## Feel free to override/extend it's functionality to cater your requirements.

# Example Usage

- [Execute Bash](https://github.com/amadolid/pybotchi/blob/master/agents/pybotchi-cli/example_usage.py)

## `python3 example_usage.py "list files"`

```
Logging: Listing files in the current directory
total 248
drwxr-xr-x 4 root root   4096 Sep  8 14:06 .
drwxr-xr-x 4 root root   4096 Sep  8 12:40 ..
-rw-r--r-- 1 root root    202 Sep  8 13:41 .flake8
drwxr-xr-x 3 root root   4096 Sep  8 13:56 .mypy_cache
-rw-r--r-- 1 root root    297 Sep  8 14:07 README.md
-rw-r--r-- 1 root root   2243 Sep  8 14:06 example_usage.py
-rw-r--r-- 1 root root     28 Sep  8 14:06 mypy.ini
-rw-r--r-- 1 root root 211899 Sep  8 12:43 poetry.lock
drwxr-xr-x 3 root root   4096 Sep  8 13:51 pybotchi_cli
-rw-r--r-- 1 root root    811 Sep  8 12:42 pyproject.toml
Logging: Listing complete
```

## `python3 example_usage.py "remove README.md"`

```
Here's the script I will run:
---
echo "[INFO] Attempting to remove README.md file..."
if [ -f "README.md" ]; then
  rm README.md
  echo "[SUCCESS] README.md has been deleted."
else
  echo "[ERROR] README.md file does not exist."
fi
---

If you want to proceed, please reply with "I know what I am doing" exactly:
```

- > I know what I am doing

```
[INFO] Attempting to remove README.md file...
[SUCCESS] README.md has been deleted.
```

- > anything else

```
Cancelled!
```
