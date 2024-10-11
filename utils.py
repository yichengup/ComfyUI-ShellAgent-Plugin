import hashlib
import time
from pathlib import PurePosixPath, Path

def windows_to_linux_path(windows_path):
    return str(PurePosixPath(Path(windows_path)))

def compute_sha256(file_path, chunk_size=1024 ** 2):
    # Create a new sha256 hash object
    start = time.time()
    sha256 = hashlib.sha256()
    print("start compute sha256 for", file_path)
    # Open the file in binary mode
    with open(file_path, 'rb') as file:
        # Read the file in chunks to handle large files efficiently
        while chunk := file.read(chunk_size):
            sha256.update(chunk)
    print("finish compute sha256 for", file_path, f"time: {time.time() - start}")
    # Return the hexadecimal digest of the hash
    return sha256.hexdigest()