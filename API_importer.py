import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import base64
from config import (
    CLIENT_ID,
    CLIENT_SECRET,
    REDIRECT_URI,
    toggle_match_ratio,
    playlist_name
)

SCOPE = 'playlist-read-private playlist-modify-public playlist-modify-private'

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    open_browser=True,
    cache_path=".spotify_token"
))

def create_playlist_from_csv(csv_file, playlist_name, min_match_ratio=toggle_match_ratio):
    """Create a Spotify playlist from a CSV file containing track information."""
    desc = base64.b64decode('UGxheWxpc3QgY3JlYXRlZCB1c2luZyB0aGUgU3BvdGlmeSBwbGF5bGlzdCBpbXBvcnRlciBmb3VuZCBhdCBodHRwczovL2dpdGh1Yi5jb20vR3JpZmYtS3lhbC9TcG90aWZ5X1BsYXlsaXN0LUV4dHJhY3Rvcg==').decode('utf-8')
    user_id = sp.me()['id']
    df = pd.read_csv(csv_file)
    total_tracks = len(df)
    
    new_playlist = sp.user_playlist_create(user=user_id, name=playlist_name, description=desc)
    playlist_id = new_playlist['id']
    track_ids = []
    unmatched_tracks = []
    
    for _, row in df.iterrows():
        query = f"track:{row['Title']} artist:{row['Artist(s)']}"
        results = sp.search(q=query, type='track', limit=1)
        tracks = results['tracks']['items']
        
        if tracks:
            track_ids.append(tracks[0]['id'])
        else:
            print(f"Could not find: {row['Title']} by {row['Artist(s)']}")
            unmatched_tracks.append({
                "Title": row['Title'], 
                "Artist(s)": row['Artist(s)']
            })
    
    if unmatched_tracks:
        log_filename = f"{playlist_name.replace(' ', '_')}_unmatched.csv"
        pd.DataFrame(unmatched_tracks).to_csv(log_filename, index=False)
        print(f"Saved {len(unmatched_tracks)} unmatched tracks to {log_filename}")
    
    match_ratio = len(track_ids) / total_tracks if total_tracks > 0 else 0
    if match_ratio < min_match_ratio:
        sp.current_user_unfollow_playlist(playlist_id)
        raise Exception(
            f"Only matched {len(track_ids)}/{total_tracks} tracks "
            f"({match_ratio:.0%}), below threshold {min_match_ratio:.0%}. "
            f"Playlist has been deleted."
        )
    
    batch_size = 100
    for i in range(0, len(track_ids), batch_size):
        batch = track_ids[i:i + batch_size]
        sp.playlist_add_items(playlist_id, batch)
    
    print(f"Created playlist '{playlist_name}' with {len(track_ids)}/{total_tracks} tracks")
    return playlist_id

if __name__ == "__main__":
    create_playlist_from_csv('spotify_playlist.csv', playlist_name)