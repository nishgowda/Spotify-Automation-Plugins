"""
    @file:apple_music.py
    @author:Nish Gowda
    @date:07/26/2020
    @about: Automate sycning songs from playlists in apple music directly to spotify
"""
import requests
import json
import os
import sys
from dotenv import load_dotenv
from os.path import join, dirname
from pathlib import Path
import jwt
import datetime
from spotify import Spotify
class AppleMusicPlugin():
    env_path = join(dirname(__file__), 'secrets.env')
    load_dotenv(env_path)

    def __init__(self):
        self.secret_key = Path('secret_key.p8').read_text()
        self.key_id = os.environ.get('KEY_ID')
        self.team_id = os.environ.get('TEAM_ID')
        self.username = ''
        self.apple_playlist_url = ''

    ''' Given a playlist url, we parse out just the id of the string '''
    def get_apple_music_id(self):
        playlist_url =  self.apple_playlist_url.split("pl.", 1)
        playlist_id = "pl." + playlist_url[1]
        return playlist_id

    ''' Return a jwt token that will be passed in via a header to our query, allowing us to access the apple music api'''
    def get_apple_key(self):
        time_now = datetime.datetime.now()
        time_expired = datetime.datetime.now() + datetime.timedelta(hours=12)
        headers = {
            "alg": "ES256",
            "kid": self.key_id
        }

        payload = {
            "iss": self.team_id,
            "iat": int(time_now.strftime("%s")),
            "exp": int(time_expired.strftime("%s"))
        }
        token = jwt.encode(payload, self.secret_key, algorithm='ES256', headers=headers)
        return token.decode()

    ''' Grab the song and artist name of the songs in an apple music playlist and add available songs to new spotify playlist '''
    def copy_playlist(self):
        apple_token = self.get_apple_key()
        apple_playlist_id = self.get_apple_music_id()
        query = 'https://api.music.apple.com/v1/catalog/{}/playlists/{}'.format('us', apple_playlist_id)
        response = requests.get(query, headers={"Content-Type":"application/json", "Authorization":"Bearer {}".format(apple_token)})
        playlist = response.json()
        spotify = Spotify(self.username)
        spotify_token = spotify.authenticate_spotify()
        uris = []
        playlist_description = playlist['data'][0]['attributes']['description']['short']
        playlist_name = playlist['data'][0]['attributes']['name']
        for i, songs in enumerate(playlist['data'][0]['relationships']['tracks']['data']):
            song_name = songs['attributes']['name']
            artist_name = songs['attributes']['artistName']
            if spotify.get_spotify_uri(song_name, artist_name, spotify_token) is not None:
                uris.append(spotify.get_spotify_uri(song_name, artist_name, spotify_token))
                print(str(i) + ".) " + song_name + " by " + artist_name)
        spotify_paylist_id = spotify.create_playlist(spotify_token, playlist_name, playlist_description)
        spotify.add_songs_to_playlist(uris, spotify_token, spotify_paylist_id)
        print("-------- Succesfully copied your playlist on Apple Music to Spotify! --------")

   


if __name__ == "__main__":
    apple_music = AppleMusicPlugin()
    apple_music.username = sys.argv[1]
    apple_music.apple_playlist_url = sys.argv[2]
    apple_music.copy_playlist()
