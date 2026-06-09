import subprocess
import time
import re

# 1. Read the public backend URL from the previous step
with open("backend_url.txt", "r") as f:
    backend_url = f.read().strip()

# 2. Update frontend/src/api.js with the public backend URL
api_js_path = "frontend/src/api.js"
with open(api_js_path, "r") as f:
    content = f.read()

# Replace the default local host port with the active Cloudflare gateway
updated_content = re.sub(
    r"baseURL:\s*'[^']+'",
    f"baseURL: '{backend_url}'",
    content
)

with open(api_js_path, "w") as f:
    f.write(updated_content)

print("[Link Complete] frontend/src/api.js dynamically linked to active backend gateway.\n")

# 3. Start Vite frontend as a background process
frontend_log = open("frontend_output.log", "w")
frontend_process = subprocess.Popen(
    ["npm", "run", "dev", "--prefix", "frontend", "--", "--host", "0.0.0.0", "--port", "5173"],
    stdout=frontend_log,
    stderr=frontend_log
)
time.sleep(3)

# 4. Expose Vite port 5173 via Cloudflare
frontend_tunnel_log = open("frontend_tunnel.log", "w")
frontend_tunnel_process = subprocess.Popen(
    ["cloudflared", "tunnel", "--url", "http://127.0.0.1:5173"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

# 5. Extract and print the public link
frontend_url = None
start_time = time.time()
while time.time() - start_time < 30:
    line = frontend_tunnel_process.stdout.readline()
    if not line:
        continue
    match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
    if match:
        frontend_url = match.group(0)
        break

if frontend_url:
    print(f"\n==============================================================")
    print(f"KSP-NETRA WEB PORTAL LIVE AT: {frontend_url}")
    print(f"==============================================================\n")
else:
    print("Error: Frontend tunnel could not be initialized.")
