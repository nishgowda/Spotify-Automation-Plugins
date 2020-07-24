'''
    @file:youtube.py
    @author:Nish Gowda
    @date:07/23/2020
    @about: Automate sycning songs from playlists in youtube directly to spotify
'''
import googleapiclient.discovery
import youtube_dl
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
import requests
import os
import sys
from dotenv import load_dotenv
from os.path import join, dirname
import json

class YoutubePlugin():
    env_path = join(dirname(__file__), 'secrets.env')
    load_dotenv(env_path)
    def __init__(self):
        self.tracks = {}
        self.username = ''
        self.playlist_url = ''
        self.playlist_name = ''
        self.playlist_description = ''

   ''' Given a url, parse just the playlist id ''' 
    def search_for_playlist(self):
        playlist_id = self.playlist_url.replace("https://www.youtube.com/playlist?list=", "")
        print(playlist_id)
        return playlist_id
    
    ''' Get the songs in a given youtube playlist using youtube api and use below functions to create a playlist and add each found song to it '''
    def get_playlist(self):
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey = os.environ.get("DEVELOPER_KEY"))
        request = youtube.playlistItems().list(
        part = "snippet",
        playlistId = self.search_for_playlist(),
        maxResults = 50
        )
        response = request.execute()
        token = self.authenticate_spotify()
        uris = []
        while request is not None:
            response = request.execute()
            for item in response["items"]:
                try:
                    video_id = item["snippet"]["resourceId"]["videoId"]
                    youtube_url = "https://www.youtube.com/watch?v={}".format(
                    video_id)
                    # use youtube_dl to collect the song name & artist name
                    video = youtube_dl.YoutubeDL({}).extract_info(
                        youtube_url, download=False)
                    song_name = video["title"]
                    artist = video["uploader"].replace(" - Topic", " ")
                    self.tracks.update({song_name: artist})
                    print(song_name + " by " + artist)
                    if self.get_spotify_uri(song_name, artist, token) is not None:
                        uris.append(self.get_spotify_uri(song_name, artist, token))
                except:
                    print("Video is unavailable")
                request = youtube.playlistItems().list_next(request, response)
        spotify_playlist_id = self.create_playlist(token)
        self.add_songs_to_playlist(token, uris, spotify_playlist_id)
    
    ''' Follow spotify oauth to authenticate the user '''
    def authenticate_spotify(self):
        client_id = os.environ.get("CLIENT_ID")
        client_secret = os.environ.get("CLIENT_SECRET")
        redirect_uri = os.environ.get("REDIRECT_URI")
        username = self.username
        scope = "user-library-read user-top-read playlist-modify-public user-follow-read"
        token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)
        return token

    ''' Create playlist on spotify for users '''
    def create_playlist(self, token):
        request_body = json.dumps({"name": self.playlist_name, "description": self.playlist_description, "public": True})
        query = "https://api.spotify.com/v1/users/{}/playlists".format(self.username)
        response = requests.post(query, data=request_body, headers={"Content-Type":"application/json", "Authorization":"Bearer {}".format(token)})
        response_json = response.json()
        return response_json["id"]
    
    ''' Add found songs to previously created playlsit '''
    def add_songs_to_playlist(self, token, uris, spotify_playlist_id):
        request_data = json.dumps(uris)
        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(spotify_playlist_id)
        response = requests.post(query,data=request_data, headers={"Content-Type": "application/json","Authorization": "Bearer {}".format(token)})
        response_json = response.json()

    ''' Given a song name and artist name, use spotify web api to search for the uri of the song to later add it to the playlsit'''
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

if __name__=="__main__":
    youtube = YoutubePlugin()
    youtube.username = sys.argv[1]
    youtube.playlist_url = sys.argv[2]
    youtube.playlist_name = sys.argv[3]
    youtube.playlist_description = sys.argv[4]
    youtube.get_playlist()
