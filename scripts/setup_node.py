import os
import shutil
import urllib.request
import zipfile

NODE_URL = "https://nodejs.org/dist/v20.18.0/node-v20.18.0-win-x64.zip"
ZIP_PATH = "node.zip"
DEST_DIR = "node-bin"


def setup():
    if os.path.exists(DEST_DIR) and os.path.exists(os.path.join(DEST_DIR, "node.exe")):
        print("Node.js is already setup in", DEST_DIR)
        return

    print("Downloading portable Node.js LTS (~30MB)...")
    urllib.request.urlretrieve(NODE_URL, ZIP_PATH)

    print("Extracting...")
    with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
        zip_ref.extractall("temp_node")

    extracted_folder = os.path.join("temp_node", "node-v20.18.0-win-x64")
    if os.path.exists(DEST_DIR):
        shutil.rmtree(DEST_DIR)
    shutil.move(extracted_folder, DEST_DIR)

    # Cleanup
    if os.path.exists(ZIP_PATH):
        os.remove(ZIP_PATH)
    if os.path.exists("temp_node"):
        shutil.rmtree("temp_node")

    print("Node.js setup successful in", DEST_DIR)


if __name__ == "__main__":
    setup()
