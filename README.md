# Spotify Automation Plugins
Automation "plugins" that allow you to sync your playlists from soundcloud and youtube directly to spotify

## How to install:
```
git clone https://github.com/nishgowda/Spotify-Automation-Plugins.git
```

## How to Run:
- You must create a .env file that includes your sensitive information for soundcloud and [create an app on spotify](https://developer.spotify.com/dashboard/applications)
- You must enable the [YouTube api](https://developers-dot-devsite-v2-prod.appspot.com/youtube/v3) and create an api key to store in your .env file as well as [create an app on spotify](https://developer.spotify.com/dashboard/applications)
- If you want to use Soundcloud, run: 
```
python3 soundcloud.py <spotify username> <soundcloud playlist url> <playlist name> <playlist description> <directory for songs> 
```
- If you want to use YouTube, run: 
```
python3 youtube.py <spotify username> <youtube playlist url> <spotify playlist name> <spotify playlist description>
```

## Limits:
Unfortunately Spotify's Web Api does not allow you to automate a process where you can create a playlist off of local files. So an extra step is needed where you must [select the path](https://support.spotify.com/us/using_spotify/features/listen-to-local-files/) to your created folder that holds your downloaded soundcloud playlist.

