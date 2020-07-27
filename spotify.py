"""
    @file:spotify.py
    @author:Nish Gowda
    @date:07/27/2020
    @about: set of tools to add found songs from others to users spotify account
"""
import spotipy.util as util
from dotenv import load_dotenv
from os.path import join, dirname
import os
import requests
import json

class Spotify():
    env_path = join(dirname(__file__), 'secrets.env')
    load_dotenv(env_path)
    def __init__(self, username):
        self.username = username
    
    ''' Follow spotify oauth to authenticate the user. Returns a token that we can use in your create_playlist, get_spotify_uri, and add_songs_to_playlist functions '''
    def authenticate_spotify(self):
        client_id = os.environ.get("CLIENT_ID")
        client_secret = os.environ.get("CLIENT_SECRET")
        redirect_uri = os.environ.get("REDIRECT_URI")
        scope = "user-library-read user-top-read playlist-modify-public user-follow-read"
        token = util.prompt_for_user_token(self.username, scope, client_id, client_secret, redirect_uri)
        return token

    ''' Given a song name and artist name, use spotify web api to search for the uri of the song '''
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

    ''' Create playlist on spotify for users '''
    def create_playlist(self, token, playlist_name, playlist_description):
        request_body = json.dumps({"name": playlist_name, "description": playlist_description, "public": True})
        query = "https://api.spotify.com/v1/users/{}/playlists".format(self.username)
        response = requests.post(query, data=request_body, headers={"Content-Type":"application/json", "Authorization":"Bearer {}".format(token)})
        response_json = response.json()
        return response_json["id"]

    ''' Add found songs to previously created playlsit '''
    def add_songs_to_playlist(self, uris, token, playlist_id):
        request_data = json.dumps(uris)
        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)
        response = requests.post(query,data=request_data, headers={"Content-Type": "application/json","Authorization": "Bearer {}".format(token)})
        response_json = response.json()

