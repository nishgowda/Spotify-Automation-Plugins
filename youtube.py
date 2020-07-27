"""
    @file:youtube.py
    @author:Nish Gowda
    @date:07/23/2020
    @about: Automate sycning songs from playlists in youtube directly to spotify
"""
import googleapiclient.discovery
import youtube_dl
import spotipy.util as util
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
        self.username = ''
        self.playlist_url = ''

    ''' Given a url, parse just the playlist id to use in your get_playlist function '''
    def search_for_playlist(self):
        playlist_id = self.playlist_url.replace("https://www.youtube.com/playlist?list=", "")
        return playlist_id
        
    ''' Grab the name and description of the youtube playlist given'''
    def get_playlist_info(self):
        # build the youtube client to find info about the playlist given
        youtube = googleapiclient.discovery.build("youtube", "v3", developerKey = os.environ.get("DEVELOPER_KEY"))
        request = youtube.playlists().list(
        part = "snippet",
        id = self.search_for_playlist(),
        maxResults = 50
        )
        response = request.execute()
        playlist_name = response["items"][0]["snippet"]["localized"]["title"]
        playlist_description = response["items"][0]["snippet"]["localized"]["description"]
        return [playlist_name, playlist_description]

    ''' Get the songs in a given youtube playlist using youtube api and use below functions to create a playlist and add each found song to it '''
    def copy_playlist(self):
        # build our youtube client to list out the content in the given playlist
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
                    # use youtube_dl to collect the song title and channel title (song name and artist)
                    video = youtube_dl.YoutubeDL({}).extract_info(
                        youtube_url, download=False)
                    song_name = video["title"]
                    artist = video["uploader"].replace(" - Topic", " ")
                    print(song_name + " by " + artist)
                    
                    # if the spotify can find the song, then we add it our list which is sent to our add_playlist function
                    if self.get_spotify_uri(song_name, artist, token) is not None:
                        uris.append(self.get_spotify_uri(song_name, artist, token))
                except:
                    print("Video is unavailable")
                # allows us to iterate through all the items in the request 
                request = youtube.playlistItems().list_next(request, response)
        playlist_name = self.get_playlist_info()[0]
        playlist_description = self.get_playlist_info()[1]
        spotify_playlist_id = self.create_playlist(token, playlist_name, playlist_description)
        self.add_songs_to_playlist(token, uris, spotify_playlist_id)
        print("Succesfully copied from yout playlist on YouTube to Spotify!")
    
    ''' Follow spotify oauth to authenticate the user. Returns a token that we can use in your create_playlist, get_spotify_uri, and add_songs_to_playlist functions '''
    def authenticate_spotify(self):
        client_id = os.environ.get("CLIENT_ID")
        client_secret = os.environ.get("CLIENT_SECRET")
        redirect_uri = os.environ.get("REDIRECT_URI")
        username = self.username
        scope = "user-library-read user-top-read playlist-modify-public user-follow-read"
        token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)
        return token

    ''' Create playlist on spotify for users '''
    def create_playlist(self, token, playlist_name, playlist_description):
        request_body = json.dumps({"name": playlist_name, "description": playlist_description, "public": True})
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
        query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20".format(track_name,artist_name)
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
    youtube.copy_playlist()
