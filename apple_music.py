import applemusicpy
import spotipy.util as util
import requests
import json
import os
import sys
from dotenv import load_dotenv
from os.path import join, dirname
from pathlib import Path

class AppleMusicPlugin():
    env_path = join(dirname(__file__), 'secrets.env')
    load_dotenv(env_path)

    def __init__(self):
        self.secret_key = Path('secret_key.txt').read_text()
        self.key_id = os.environ.get('KEY_ID')
        self.team_id = os.environ.get('TEAM_ID')
        self.username = ''
        self.apple_playlist_url = ''
        self.playlist_name = ''
        self.playlist_description = ''
    
    ''' Given a playlist url, we parse out just the id of the string '''
    def get_apple_music_id(self):
        playlist_url =  self.apple_playlist_url.split("pl.", 1)
        playlist_id = "pl." + playlist_url[1]
        return playlist_id

    ''' Grab the song and artist name of the songs in an apple music playlist and add available songs to new spotify playlist '''
    def get_songs(self):
        am = applemusicpy.AppleMusic(self.secret_key, self.key_id, self.team_id)
        playlist_id = self.get_apple_music_id()
        playlist = am.playlist(playlist_id, storefront='us')
        token = self.authenticate_spotify()
        uris = []
        for songs in playlist['data'][0]['relationships']['tracks']['data']:
            song_name = songs['attributes']['name']
            artist_name = songs['attributes']['artistName']
            print(song_name + " by " + artist_name)
            if self.get_spotify_uri(song_name, artist_name, token) is not None:
                uris.append(self.get_spotify_uri(song_name, artist_name, token))
    
        paylist_id = self.create_playlist(token)
        self.add_songs_to_playlist(uris, token, playlist_id)
        print("Succesfully added all songs from apple music to spotify")

    ''' Using spotify authentication method to authenticate a user by their username '''
    def authenticate_spotify(self):
        client_id = os.environ.get("CLIENT_ID")
        client_secret = os.environ.get("CLIENT_SECRET")
        redirect_uri = os.environ.get("REDIRECT_URI")
        username = self.username
        scope = "user-library-read user-top-read playlist-modify-public user-follow-read"
        token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)
        return token

    ''' Given an song and artist name, we check if song exists in spotify, if it does then return it's uri'''
    def get_spotify_uri(self, track_name, artist_name, token):
        query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track".format(track_name,artist_name)
        response = requests.get(query, headers={"Content-Type":"application/json", "Authorization":"Bearer {}".format(token)})
        response_json = response.json()
        songs = response_json["tracks"]["items"]
        try:
            uri = songs[0]["uri"]
            return uri
        except:
            return None
    ''' Create a playlist to hold our songs '''
    def create_playlist(self, token):
        request_body = json.dumps({"name": self.playlist_name, "description": self.playlist_description, "public": True})
        query = "https://api.spotify.com/v1/users/{}/playlists".format(self.username)
        response = requests.post(query, data=request_body, headers={"Content-Type":"application/json", "Authorization":"Bearer {}".format(token)})
        response_json = response.json()
        return response_json["id"]

    ''' Add found songs to our newly made playlist '''
    def add_songs_to_playlist(self, uris, token, playlist_id):
        request_data = json.dumps(uris)
        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)
        response = requests.post(query,data=request_data, headers={"Content-Type": "application/json","Authorization": "Bearer {}".format(token)})
        response_json = response.json()

if __name__ == "__main__":
    apple_music = AppleMusicPlugin()
    apple_music.username = sys.argv[1]
    apple_music.apple_playlist_url = sys.argv[2]
    apple_music.playlist_name = sys.argv[3]
    apple_music.playlist_description = sys.argv[4]
    apple_music.get_songs()
