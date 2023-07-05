from lxml import html
from urllib.request import Request
from urllib.request import urlopen
import random
import shutil
import time
import os


# Replace and remove a list of characters
def replace_del(s, lst):
    for i in lst:
        s = s.replace(i, '')
    return s



# -- URLS --
# Urls
base_url = "https://www.myinstants.com"
home_url = "https://www.myinstants.com/index/no"
media_url = "https://www.myinstants.com/media/sounds"
page_url = "/?page="
# Header
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3"}

# -- FILES --
# Download folder
download_folder = "Assets/downloads"
if not os.path.isdir("Assets"):
    os.mkdir("Assets")
if not os.path.isdir("Assets/downloads"):
    os.mkdir("Assets/downloads")

# -- MAIN --
download_count = 0
current_page = 2
while True:
    # Generate main url
    if current_page == 0:
        current_url = home_url
    else:
        current_url = home_url + page_url + str(current_page)


    # Open url
    request = Request(url=current_url, headers=headers)

    # Read data
    tree = html.fromstring(urlopen(request).read().decode("utf-8"))

    # Get elements
    elem_container = tree.xpath("//div[@id='instants_container']")[0]
    elem_instants = elem_container.xpath(".//div[@class='instant']")


    # For buttons on page
    for elem in elem_instants:

        inst_name = None

        # Get url
        elem_inst_button = elem.xpath("div[@class='small-button']")
        if elem_inst_button is None:
            print("Could not find button url")
            continue
        try:
            js_string = elem_inst_button[0].get("onmousedown")
            js_clean = replace_del(js_string, "()'")
            inst_name = js_clean.split("/")[-1].strip()
        except Exception as e:
            print("Could not find button url\n", e)
            continue
        if not bool(inst_name):
            print("Empty string")
            continue

        # Generate download url
        download_url = "%s/%s" % (media_url, inst_name)
        #print("Url: ", download_url)
        # Generate filename
        download_filename = "%s/%s-%s" % (download_folder, str(time.time()).split('.')[0][-4:], inst_name)

        # Download file
        request = Request(url=download_url, headers=headers)
        with urlopen(request) as mp3_response, open(download_filename, "wb") as mp3_file:
            shutil.copyfileobj(mp3_response, mp3_file)

        # Debug
        download_count += 1
        print("Downloaded: %s/%s - %s - %s" % (download_count, current_page, download_filename, download_url))

        # Be nice
        time.sleep(round(random.random() + random.randint(1, 2), 2))


    # Next page
    current_page += 1
