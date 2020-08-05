# Google Music To Spotify

This tool exports the user's Google Music playlists and albums to spotify.

## Usage

1. `pipenv install`
2. `pipenv shell`
3. `python3 main`

See `--help` for detailed flag usage.

### Obtaining your Google device ID

Google does not have a public api for Google Music.
As a consquence using this script violates the Google's terms of use.
You have been warned.
In order to make requests we must spoof a device that is already connected to your Google Music account.
Fortuantely our Google Music library, [simon-weber/gmusicapi](https://github.com/simon-weber/gmusic-api), does most of the work.
The easiest way to get a device id is for you to supply a dummy one on the command line, this will crash the app, but Google returns your device IDs in the error message (nice).


### Obtaining your Spotify Client ID and Secret

1. Visit your [spotify developer dashboard](https://developer.spotify.com/dashboard/login)
2. Create an app, the Client ID and Secret Should be immediately visible
3. Click "Edit Settings"
4. Add "http://localhost/" to "Redirect URIs".
During the first execution of the script this will open your browser, authenticate you with Spotify then redirect you to "http://localhost/?code=...".
Copy this URL (yes the entire thing) into your terminal when prompted.

### Favorites Playlist

Spotify and Google Music don't exactly see eye-to-eye on what they consider ways to favorite a track.
Google allows you to "thumbs up" tracks that you like.
Spotify allows you to save tracks you like and add them to playlists.
When you save a track or add it to a playlist Spotify infers that you like the song.
To import your Google "thumbs up" I recommend creating a new playlist from your "thumbs up"ed tracks.
Unfortunately the pre-created auto playlist is not accessible from outside of an official client so you will need to export these to a new playlist.
To do so, go to your "playlists" page in Google music find "Thumbs up" in the "Auto-playlists" section.
Mouse over it, and click the three-dots menu, select "Add playlist to playlist" > "New Playlist".
When you specify `--favorites-playlist` make sure to supply the same name (capitilization matters!).

### Albums

All Google music favorite tracks transfer to Spotify liked albums.

P.S. In this fork transfer albums added.