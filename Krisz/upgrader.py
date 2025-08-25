import json
import os
import urllib.request
from urllib.parse import urljoin

# --- Konfiguráció ---
GITHUB_BASE = "https://raw.githubusercontent.com/PetiRu/piac_figyelo/main/Krisz"
VERSION_FILE = "version.json"

# --- Segédfüggvények ---
def log(msg):
    print(f"[CHECK PANEL] {msg}")

def get_local_version():
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, "r") as f:
                data = json.load(f)
                return data.get("version", "0.0.0")
        except Exception as e:
            log(f"Hiba a helyi verzió olvasásánál: {e}")
            return "0.0.0"
    log("Helyi verziófájl nem található, kezdés 0.0.0-ról")
    return "0.0.0"

def get_github_version_info():
    url = urljoin(GITHUB_BASE, "version.json")
    try:
        with urllib.request.urlopen(url) as response:
            data = json.load(response)
            version = data.get("version", "0.0.0")
            files = data.get("files", [])
            log(f"GitHub verzió lekérve: {version}, {len(files)} fájl")
            return version, files
    except Exception as e:
        log(f"Hiba a GitHub verzió lekérésénél: {e}")
        return "0.0.0", []

def version_greater(v1, v2):
    def parse(v):
        return [int(x) for x in v.split(".")]
    return parse(v1) > parse(v2)

def download_file(file_name):
    url = urljoin(GITHUB_BASE, file_name)
    local_path = os.path.join(".", file_name)
    os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
    try:
        with urllib.request.urlopen(url) as response:
            content = response.read()
            with open(local_path, "wb") as f:
                f.write(content)
        log(f"Letöltve: {file_name}")
    except Exception as e:
        log(f"Hiba a letöltés során: {file_name}, {e}")

def update_all(files):
    for i, file in enumerate(files, start=1):
        download_file(file)
        log(f"Frissítés: {i}/{len(files)} fájl kész")

def run_updater():
    log("Updater elindult...")
    github_version, files = get_github_version_info()
    local_version = get_local_version()

    if version_greater(github_version, local_version):
        log(f"Új verzió elérhető: {github_version} (helyi: {local_version})")
        if files:
            update_all(files)
        try:
            with open(VERSION_FILE, "w") as f:
                json.dump({"version": github_version, "files": files}, f, indent=4)
            log("Helyi verzió frissítve")
        except Exception as e:
            log(f"Hiba a helyi verzió mentésénél: {e}")
        log("Frissítés kész")
    else:
        log("Már a legfrissebb verzió van telepítve")
