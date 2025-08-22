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