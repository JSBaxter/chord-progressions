import requests, bs4, re, json, time


def get_song_urls(page_number):
    rsp = requests.get(
        f"https://www.ultimate-guitar.com/explore?page={page_number}&type[]=Chords"
    )
    bs4.BeautifulSoup(rsp.text)

    pattern = r"https://tabs\.ultimate-guitar\.com/tab/([^/]+)/([^/]+?)(?=&quot;)"
    matches = re.findall(pattern, rsp.text)

    urls = []

    for match in matches:
        artist, song = match
        full_url = f"https://tabs.ultimate-guitar.com/tab/{artist}/{song}"
        urls.append({"artist": artist, "song": song, "full_url": full_url})
    return urls


def extract_data_content(chords_url: str) -> str:
    """
    Extract the value of the 'data-content' attribute from an element with class 'js-store'.

    :param html_content: The HTML content as a string.
    :return: Value of the 'data-content' attribute. Returns None if not found.
    """
    rsp = requests.get(chords_url)
    if rsp.status_code == 404:
        return None
    if rsp.status_code != 200:
        time.sleep(60)
        if rsp.status_code != 200:
            raise Exception(f"Status code {rsp.status_code} not OK")
    soup = bs4.BeautifulSoup(rsp.text, "html.parser")
    element = soup.find(class_="js-store")

    if element:
        return json.loads(element.get("data-content"))
    else:
        return None


def get_chords_tab(content_dict):
    chords_tab = content_dict["store"]["page"]["data"]["tab_view"]["wiki_tab"][
        "content"
    ]
    chords_tab = chords_tab.replace(" - ", ", ")
    return chords_tab


def parse_tabline(tabline):
    chords, lyrics = tabline.split("\r\n")
    chords_spaces = [j for i in chords.split("[ch]") for j in i.split("[/ch]") if j]
    return chords_spaces, lyrics


def chords_tab_generator(chords_tab):
    pattern = r"\[tab\](.*?)\[/tab\]"
    for tabline in re.findall(pattern, chords_tab, re.DOTALL):
        if "[ch]" not in tabline:
            continue
        chords, lyrics = parse_tabline(tabline)
        yield chords, lyrics


def parse_chords_tab(chords_tab):
    chord_lyr = [{"chord": "", "lyrics": ""}]
    for chd_line, lyr in chords_tab_generator(chords_tab):
        for value in chd_line:
            if " " in value:
                ind = len(value)
                space_ind = -lyr[::-1].find(" ", -ind)
                chord_lyr[-1]["lyrics"] += lyr[:space_ind]
                lyr = lyr[space_ind:]
                chd_line = chd_line[1:]
            else:
                chord_lyr.append({"chord": value, "lyrics": lyr[0]})
                lyr = lyr[1:]
        if " " not in chd_line[-1]:
            chord_lyr[-1]["lyrics"] += lyr + "; "
    return chord_lyr


def get_metadata(content_dict):
    return {
        "versions": content_dict["store"]["page"]["data"]["tab_view"]["versions"],
        "meta": content_dict["store"]["page"]["data"]["tab_view"]["meta"],
        "tab": content_dict["store"]["page"]["data"]["tab"],
        "content": content_dict["store"]["page"]["data"]["tab_view"]["wiki_tab"][
            "content"
        ],
    }


def get_url_tab_data(song):
    content_dict = extract_data_content(song["full_url"])
    fields = {
        "id",
        "song_id",
        "song_name",
        "artist_id",
        "artist_name",
        "votes",
        "rating",
        "tonality_name",
        "tab_url",
        "type",
    }
    tab_meta = content_dict["store"]["page"]["data"]["tab"]
    song_data = {key: value for key, value in tab_meta.items() if key in fields}

    fields = {"votes", "rating", "tab_url"}
    vsns = content_dict["store"]["page"]["data"]["tab_view"]["versions"]
    song_data["versions"] = [
        {key: value for key, value in ver.items() if key in fields} for ver in vsns
    ]
    song_data["view_meta"] = content_dict["store"]["page"]["data"]["tab_view"]["meta"]

    song_data["content"] = content_dict["store"]["page"]["data"]["tab_view"][
        "wiki_tab"
    ]["content"]
    return song_data


def get_page_tabs(song_list):
    """
    Write dictionaries from a generator to a file as a JSON array.

    :param generator: The generator yielding dictionaries.
    :param filename: The file name to write to.
    """
    songdata = []
    for song in song_list:
        try:
            data = get_url_tab_data(song)
            songdata.append(data)
        except:
            continue
    return songdata


def scrape_page(pg_num):
    song_list = get_song_urls(pg_num)
    data = {
        "data": get_page_tabs(song_list),
        "page_url": f"https://www.ultimate-guitar.com/explore?page={pg_num:05}&type[]=Chords",
        "song_list": song_list,
        "pg_num": pg_num,
    }
    with open(f"data/pg_{pg_num}.json", "w") as f:
        json.dump(data, f)
