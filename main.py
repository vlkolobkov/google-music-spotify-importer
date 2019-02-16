from gmusicapi import Mobileclient
import os.path
from pprint import pprint
import json
import spotipy
import spotipy.util as util
import re
import argparse
import string

spotify_username = None
spotify_client_id = None
spotify_client_secret = None
google_device_id = None
state_dir = ".state"
favorites_playlist_name = "favorites"
force_fetch = False

def create_spotify_playlists(spotify, playlists):
    for playlist in playlists:
        tracks = get_spotify_tracks(spotify, playlist['name'], playlist['tracks'])
        create_spotify_playlist(spotify, playlist['name'], tracks)

        if playlist['name'] == favorites_playlist_name:
            print("Found a favorites playlist, saving favorite tracks to Spotify library")
            spotify.current_user_saved_tracks_add(tracks=tracks)



def create_spotify_playlist(spotify, name, tracks):
    print(f"Creating {name} playlist in spotify")
    created = spotify.user_playlist_create(spotify_username, name, False)
    spotify.user_playlist_add_tracks(spotify_username, created['id'], tracks)

def get_spotify_tracks(spotify, playlist, tracks, limit=None):
    print("Matching tracks to those in spotify")
    spotify_tracks_path = f"{state_dir}/spotify_tracks.json"
    cached_tracks = {}

    if os.path.exists(spotify_tracks_path) and not force_fetch:
        with open(spotify_tracks_path, 'r') as infile:
            cached_tracks = json.load(infile)
        
        if playlist in cached_tracks and len(cached_tracks[playlist]) == len(tracks):
            print("Using cached spotify matches")
            return cached_tracks[playlist]

    sptracks = []
    misses = []
    count = 0
    for track in tracks:
        sptrack = find_spotify_track(spotify, track)
        if sptrack is None:
            misses.append(track)
        else:
            sptracks.append(sptrack['id'])

        if limit is not None and count >= limit:
            break
        count += 1
    
    cached_tracks[playlist] = sptracks
    with open(spotify_tracks_path, 'w') as outfile:
        json.dump(cached_tracks, outfile)

    misses_path = f'{state_dir}/spotify_misses.json'
    misses_cache = {}
    if os.path.exists(misses_path):
        with open(misses_path, 'r') as misses_file:
            misses_cache = json.load(misses_file)

    with open(misses_path, 'w') as outfile:
        misses_cache[playlist] = misses
        json.dump(misses_cache, outfile)

    print(f"Found {len(sptracks)} of {len(tracks)} for {playlist} in spotify")
    if len(misses) > 0:
        print(f"Check {misses_path} for tracks that could not be matched")
    return sptracks


def clean_name(name):
    # trim things like "(feat: Artist)" which are done formatted differently in spotify
    # and cause false negatives. Its better to send fewer characters because spotify fuzzy
    # completes the term, but doesn't remove characters
    m = re.match(r'(.*)\s+(\(|feat)', name)
    ret = name
    if m is not None and m.group(1) is not None:
        ret = m.group(1)

    return ret.strip()

def find_spotify_track(spotify, track):
    # because of (Deluxe Edition), etc
    track['title'] = clean_name(track['title'])
    # because of (Deluxe Edition), etc
    track['album'] = clean_name(track['album'])
    # because of (feat: Artist), etc
    track['artist'] = clean_name(track['artist'])

    full_query = 'track:{title} artist:{artist} album:{album} year:{year}'.format(**track)
    full = spotify.search(q=full_query, type='track', limit=1)
    if len(full['tracks']['items']) != 0:
        return full['tracks']['items'][0]

    # some times years are misleading because of rereleases
    no_year_query = 'track:{title} artist:{artist} album:{album}'.format(**track)
    no_year = spotify.search(q=no_year_query, type='track', limit=1)
    if len(no_year['tracks']['items']) != 0:
        return no_year['tracks']['items'][0]

    # see if its on a greatest hits album, a single or some other release
    no_album_query = 'track:{title} artist:{artist}'.format(**track)
    no_album = spotify.search(q=no_album_query, type='track', limit=1)
    if len(no_album['tracks']['items']) != 0:
        return no_album['tracks']['items'][0]

    print(f"Could not find {track} in Spotify")

def extract_google_track(track):
    if not 'track' in track:
        return

    t = track['track']
    return {
        'album': t['album'],
        'artist': t['artist'],
        'year': t['year'],
        'title': t['title'],
    }

def get_google_playlists():
    print("Retreiving playlists from Google Music.")
    playlists_path = f"{state_dir}/playlists.json"

    if os.path.exists(playlists_path) and not force_fetch:
        with open(playlists_path, 'r') as infile:
            return json.load(infile)
        
    print("Could not find saved favorites playlist, or force_fetch is True")
    credentials_path = f"{state_dir}/gmusic_credentials.json"

    mm = Mobileclient()
    if not os.path.exists(credentials_path):
        mm.perform_oauth(credentials_path, open_browser=True)

    mm.oauth_login(google_device_id, oauth_credentials=credentials_path)

    if mm.is_authenticated():
        print("Authenticated sucessfully!")
    else:
        print("Could not authenticate :(")
        raise SystemExit(1)

    playlists = mm.get_all_user_playlist_contents()
    playlist_names = [p['name'] for p in playlists]
    print(f'Found playlists: {playlist_names}')
    clean_playlists = []
    for p in playlists:
        playlist = {
            'name': p['name'],
            'tracks': [],
        }

        for track in p['tracks']:
            t = extract_google_track(track)
            if t is not None:
                playlist['tracks'].append(t)
        
        if len(playlist['tracks']) == 0:
            print(f"No tracks found in {p['name']}")
        else:
            clean_playlists.append(playlist)


    pprint(clean_playlists)
    if len(clean_playlists) == 0:
        print(f"No playlists with tracks found")
        raise SystemExit(1)

    with open(playlists_path, 'w') as outfile:
        json.dump(clean_playlists, outfile)
    
    return clean_playlists


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Import Google Music Thumbs Up into Spotify')
    parser.add_argument('--spotify-user', required=True, help='Spotify user name')
    parser.add_argument('--spotify-client-id', required=True, help='Spotify API Client ID')
    parser.add_argument('--spotify-client-secret', required=True, help='Spotify API Client Secret')
    parser.add_argument('--google-device-id', required=True, help='Google Device ID to spoof requests from')
    parser.add_argument('--state-dir', required=False, default='.state', help='Where to store cached track information, credentials, and other files generated by this program')
    parser.add_argument('--favorites-playlist', required=False,
        help="""The name of this playlist is where the user's "thumbs up"ed google music tracks are stored. These tracks will be saved to the user's spotify library.""")
    parser.add_argument('--force-fetch', required=False, default=False, help='Ignore cached track and playlist information')

    args = parser.parse_args()

    spotify_username = args.spotify_user
    spotify_client_id = args.spotify_client_id
    spotify_client_secret = args.spotify_client_secret
    google_device_id = args.google_device_id
    state_dir = args.state_dir
    favorites_playlist_name = favorites_playlist_name
    force_fetch = args.force_fetch

    playlists = get_google_playlists()

    scope = 'user-library-modify playlist-modify-private'
    token = util.prompt_for_user_token(spotify_username, scope, spotify_client_id, spotify_client_secret, 'http://localhost/')
    sp = spotipy.Spotify(auth=token)

    create_spotify_playlists(sp, playlists)