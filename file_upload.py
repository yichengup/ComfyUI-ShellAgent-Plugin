import logging
import os
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import folder_paths

from .utils import compute_sha256

ext_to_type = {
    # image
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.bmp': 'image/bmp',
    '.webp': 'image/webp',
    # video
    '.mp4': 'video/mp4',
    '.mkv': 'video/x-matroska',
    '.webm': 'video/webm',
    '.avi': 'video/x-msvideo',
    '.mov': 'video/quicktime',
    # audio
    '.mp3': 'audio/mpeg',
    '.wav': 'audio/wav',
    '.m4a': 'audio/mp4',
}

def upload_file_to_myshell(local_file: str) -> str:
    ''' Now we only support upload file one-by-one
    '''
    MYSHELL_KEY = os.environ.get('MYSHELL_KEY', "OPENSOURCE_FIXED")
    if MYSHELL_KEY is None:
        raise Exception(
            f"MYSHELL_KEY not found in ENV. Please set MYSHELL_KEY in settings for CDN uploading."
        )

    server_url = "https://openapi.myshell.ai/public/v1/store"
    headers = {
        'x-myshell-openapi-key': MYSHELL_KEY
    }

    assert os.path.isfile(local_file)
    sha256sum = compute_sha256(local_file)
    start_time = time.time()
    ext = os.path.splitext(local_file)[1]
    files = [
        ('file', (os.path.basename(local_file), open(local_file, 'rb'), ext_to_type[ext])),
    ]
    response = requests.request("POST", server_url, headers=headers, files=files)
    if response.status_code == 200:
        end_time = time.time()
        logging.info(f"{local_file} uploaded, time elapsed: {end_time - start_time}")
        return [sha256sum, response.json()['url'], local_file]
    else:
        raise Exception(
            f"[HTTP ERROR] {response.status_code} - {response.text} \n"
        )
 
 
def collect_local_file(item, mapping_dict={}):
    input_dir = folder_paths.get_input_directory()
    if not isinstance(item, str):
        return
    abspath = os.path.abspath(item)
    input_abspath = os.path.join(input_dir, item)
    # required file type
    if os.path.isfile(abspath):
        fpath = abspath
    elif os.path.isfile(input_abspath):
        fpath = input_abspath
    else:
        fpath = None
    if fpath is not None:
        ext = os.path.splitext(fpath)[1]
        if ext in ext_to_type.keys():
            mapping_dict[item] = fpath
            return
        else:
            return

def process_local_file_path_async(mapping_dict, max_workers=10):
    # Using ThreadPoolExecutor for concurrent file processing
    logging.info(f"upload start, {len(mapping_dict)} to upload")
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks to the executor
        futures = {executor.submit(upload_file_to_myshell, full_path): filename for filename, full_path in mapping_dict.items()}
        logging.info("submit done")
        # Collect the results as they complete
        for future in as_completed(futures):
            filename = futures[future]
            try:
                result = future.result()
                mapping_dict[filename] = result
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    end_time = time.time()
    logging.info(f"upload end, elapsed time: {end_time - start_time}")
    return