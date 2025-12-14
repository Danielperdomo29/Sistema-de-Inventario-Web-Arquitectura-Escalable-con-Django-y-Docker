import os

file_path = r'.docker/server/scripts/entrypoint.sh'

if os.path.exists(file_path):
    with open(file_path, 'rb') as f:
        content = f.read()
    content = content.replace(b'\r\n', b'\n')
    with open(file_path, 'wb') as f:
        f.write(content)
    print(f"Fixed {file_path}")
