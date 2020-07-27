"""
    @file:youtube.py
    @author:Nish Gowda
    @date:07/23/2020
    @about: Automate sycning songs from playlists in youtube directly to spotify
"""
import googleapiclient.discovery
import youtube_dl
import requests
import os
import sys
from dotenv import load_dotenv
from os.path import join, dirname
import json
from spotify import Spotify

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
        spotify = Spotify(self.username)
        token = spotify.authenticate_spotify()
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
                    if spotify.get_spotify_uri(song_name, artist, token) is not None:
                        uris.append(spotify.get_spotify_uri(song_name, artist, token))
                except:
                    print("Video is unavailable")
                # allows us to iterate through all the items in the request 
                request = youtube.playlistItems().list_next(request, response)
        playlist_name = self.get_playlist_info()[0]
        playlist_description = self.get_playlist_info()[1]
        spotify_playlist_id = spotify.create_playlist(token, playlist_name, playlist_description)
        spotify.add_songs_to_playlist(token, uris, spotify_playlist_id)
        print("Succesfully copied from yout playlist on YouTube to Spotify!")


if __name__=="__main__":
    youtube = YoutubePlugin()
    youtube.username = sys.argv[1]
    youtube.playlist_url = sys.argv[2]
    youtube.copy_playlist()
