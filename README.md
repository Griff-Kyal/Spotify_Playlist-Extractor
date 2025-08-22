# Spotify Playlist Extractor :musical_note:

Spotify Playlist Extractor is a tool which can be used to scrape the data of a playlist link and export the songs to a CSV file. 

The main purpose of this script being created is due to the limited functionality of when sharing a **Made For You** playlist. Opening that link on a Spotify account that is logged in changes the original song list to be tailored to your recommended songs, rather than the original song list. This mitigates that by scraping the songs from the original link, exporting them to a CSV file and then using a Spotify API key, importing that playlist into your spotify as intended. 

## Pre-Requisites :clipboard:

The script is written in [Python](https://www.python.org/downloads/) which is required to run the script. it can be downloaded by following the hyperlink.

You will need to create an app on the [Spotify Dashboard](https://developer.spotify.com/dashboard) for the API to be able to make a playlist on your Spotify account. When configuring, you will need to add the following settings:

- **Redirect URIs:** http://127.0.0.1:8888/callback
- **APIs used:** Web API

> [!NOTE]
> There is no requisite for the App name and App description. These can be as desired.

Once these steps have been completed, simply copy your Client ID and Client secret and paste them into the *config.py* file under the CLIENT_ID and CLIENT_SECRET parameters.

## Installation :desktop_computer:

The following python scripts will need downloading and placing in the same directory:

> main.py  
> config.py  
> spotify_scraper.py  
> API_importer.py  

If you have python already configured or an environment set up, use the package manager [pip](https://pip.pypa.io/en/stable/) to install the required packages to your python environment.

```bash
pip install playwright pandas spotipy
```

If you downloaded Python from the link for the purpose of this script, run the following in cmd.

```bash
python -m pip install playwright pandas spotipy
```

This will globally install the required packages.

## Configuration :gear:

Before the first-time run, open the *config.py* file and configure the file as required:

```python
# Paste the required playlist URL you want to scrape the songs to here
playlist_url = ""

# Number of attempts to scrape the songs after the page scrolls down and finds no new values (default to 3)
max_attempts = 3

# Setting this to True will run the web browser in silent mode. Set this to False to see the browser for debugging
run_headless = True

# API client details for playlist import
CLIENT_ID = ''
CLIENT_SECRET = ''
REDIRECT_URI = 'http://127.0.0.1:8888/callback' #Don't change unless Spotify make changes their end

# The ratio for songs to be imported from csv to be considered successful. Range from 0.0 to 1.0 (default is 80%) 
toggle_match_ratio = 0.8

# Enter the name you want for the new playlist here
playlist_name = ""

# You can toggle which functionality you want to enable. Toggle with True/False
playlist_extract = True #Scrapes the shared playlist URL into the CSV
playlist_import = True #Create a new playlist using the data from the CSV
```

## Usage :heavy_check_mark:

If you use a Source Code Editor, such as Visual Studio Code, Then the code can be ran from the main.py file, which will run all the necessary functions within the other files. Otherwise, you can run the following in cmd:

```bash
cd /d <c:/directory/of/PythonFiles> && python main.py
```

> [!IMPORTANT]
> For the first time run for the API playlist import, you will need to log into Spotify to allow the token access, which will create a .spotify_token file which will be referenced for reoccurring runs.

## Troubleshooting :spiral_notepad:

If you encounter any issues, the main.py outputs a log file when ran, which writes to the log folder and labelled by date and time

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.
