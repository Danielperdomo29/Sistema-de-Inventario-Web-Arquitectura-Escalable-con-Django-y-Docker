import os

files = [
    r'.docker/server/scripts/entrypoint.sh'
]

for file_path in files:
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            content = f.read()
            # Replace CRLF with LF
            content = content.replace(b'\r\n', b'\n')
        with open(file_path, 'wb') as f:
            f.write(content)
        print(f"Fixed {file_path}")
