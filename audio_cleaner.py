from collections import Counter
from mutagen.mp3 import MP3
from hashlib import md5
import json
import os

# --- Constants ---
ROOT = "assets"
INPUT_PATH = f'{ROOT}/downloads_raw'
OUTPUT_PATH = f'{ROOT}/sounds_lib'
FFMPEG_PATH = 'C:/Standalone/ffmpeg/ffmpeg.exe'
MP3GAIN_PATH = 'C:/Standalone/mp3gain/mp3gain.exe'
SOX_PATH = 'C:/Standalone/sox/sox.exe'
MAX_LENGTH = 15
ENCODE_SOUNDS = True
FILTER_SOUNDS = True
NORMALIZE_SOUNDS = True
TRIM_SOUNDS = False


# Create necessary directories
def create_dirs():
    if not os.path.isdir(ROOT):
        os.mkdir(ROOT)
    if not os.path.isdir(INPUT_PATH):
        os.mkdir(INPUT_PATH)
    if not os.path.isdir(OUTPUT_PATH):
        os.mkdir(OUTPUT_PATH)


def get_raw_files():
    in_files = os.listdir(INPUT_PATH)
    in_mp3s = [i for i in in_files if i.lower().endswith('.mp3')]
    in_other = Counter([i.split('.')[-1] for i in in_files if not i.lower().endswith('mp3')])
    print(f'Found {len(in_files)} files, where {len(in_mp3s)} is mp3\'s.\n{in_other}\n')
    return in_mp3s


def get_processed_files():
    in_files = os.listdir(OUTPUT_PATH)
    print(f'Found {len(in_files)} encoded files')
    return in_files


def get_source_path(file_name):
    return f'{INPUT_PATH}/{file_name}'


def get_target_path(file_name, ascii_decode=False):
    if ascii_decode:
        return f'{OUTPUT_PATH}/{file_name.encode().decode("ascii", "ignore")}'
    return f'{OUTPUT_PATH}/{file_name}'


# Uses FFMPEG to automatically fix the file length
def encode_sounds(_mp3s):
    length = len(_mp3s)
    print(f'[*] Copying {length} Mp3\'s with ffmpeg to fix missing length attributes')
    for index, mp3_file in enumerate(_mp3s):

        # Progress
        if index % 50 == 0:
            print(f' [*] Copied {index}/{length}')

        # Create paths
        mp3_in_path = get_source_path(mp3_file)
        mp3_output_path = get_target_path(mp3_file, True)

        # Run the ffmpeg command to copy this file.
        # command = f'{FFMPEG_PATH} -v quiet -i "{mp3_in_path}" -acodec copy "{mp3_output_path}"'
        # command = f'{FFMPEG_PATH} -v quiet -i "{mp3_in_path}" -c:a acc -b:a 96k "{mp3_output_path}"'
        command = f'{FFMPEG_PATH} -v quiet -i "{mp3_in_path}" -map 0:a:0 -b:a 96k "{mp3_output_path}"'
        os.system(command)


def filter_sounds(_mp3s):
    length = len(_mp3s)
    print(f'[-] Removing files with durations longer than {MAX_LENGTH}s or missing.')
    removed_error = 0
    removed_dur = 0
    for index, mp3_file in enumerate(_mp3s):

        if index % 50 == 0:
            print(f' [*] Filtered {index}/{length}.\tRemoved E:{removed_error} D:{removed_dur}')

        mp3_output_path = get_target_path(mp3_file, False)

        # Check the length
        try:
            audio = MP3(mp3_output_path)
        except Exception as e:
            os.remove(mp3_output_path)
            removed_error += 1
            continue

        if int(audio.info.length) > MAX_LENGTH:
            os.remove(mp3_output_path)
            removed_dur += 1
            continue

    print(f'Removed {removed_error + removed_dur} unwanted files. E:{removed_error} D:{removed_dur}')


def normalize_sounds(_mp3s):
    length = len(_mp3s)
    print(f'[*] Normalizing {length} sounds to a default 89.0 dB.')

    command = f'{MP3GAIN_PATH} -r -k {OUTPUT_PATH}/*.mp3'
    os.system(command)

    print(f' [*] Normalization of {length} files complete.')


def trim_sounds(_mp3s):
    length = len(_mp3s)
    print(f'[*] Trimming silence from sounds longar than 0.1s.')
    for index, mp3_file in enumerate(_mp3s):

        if index % 50 == 0:
            print(f' [*] Trimmed {index}/{length}.')

        mp3_output_path = get_target_path(mp3_file, False)
        command = f'{SOX_PATH} -t mp3 {mp3_output_path} {mp3_output_path} silence 1 0.1 0.1% reverse silence 1 0.1 0.1% reverse'
        os.system(command)

    print(f' [*] Trimming of {length} files complete.')


def hash_name(file_name):
    return md5(file_name.encode()).hexdigest()


def hash_file(file_path):
    hash_md5 = md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def generate_flatfile(_mp3s):
    length = len(_mp3s)
    js = []
    print("[+] Generating db.json.")
    for index, mp3_file in enumerate(_mp3s):

        if index % 50 == 0:
            print(f' [*] Generated {index}/{length}.')

        file_path = get_target_path(mp3_file)

        name_hash = hash_name(mp3_file)
        file_hash = hash_file(file_path)
        file_size = os.stat(file_path).st_size

        file_dur = 0
        try:
            audio = MP3(file_path)
            file_dur = int(audio.info.length)
        except Exception as e:
            pass

        entry = {
            "name": mp3_file,
            "name_hash": name_hash,
            "size": file_size,
            "file_hash": file_hash,
            "file_dur": file_dur
        }
        js.append(entry)

    with open(f'{ROOT}/db.json', 'w') as f:
        json.dump(js, f, indent=2)
    print(" [*] Generation complete.")


def main():
    #create_dirs()
    #mp3s_raw = get_raw_files()

    #if ENCODE_SOUNDS:
    #    encode_sounds(mp3s_raw)

    #if FILTER_SOUNDS:
    #    mp3s_encoded = get_raw_files()
    #    filter_sounds(mp3s_encoded)

    mp3s_filtered = get_processed_files()
    print(f'{len(mp3s_filtered)} sounds in the library.')

    #if NORMALIZE_SOUNDS:
    #    normalize_sounds(mp3s_filtered)

    #if TRIM_SOUNDS:
    #    trim_sounds(mp3s_filtered)

    generate_flatfile(mp3s_filtered)


main()
