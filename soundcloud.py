"""
    @file: soundcloud.py
    @author: Nish Gowda
    @date: 07/22/20
    @about: Scrapes soundcloud to grab the links of all the songs in a given playlist
    and then autonomously visits a website that downloads soundcloud songs
"""
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import spotipy.util as util
import shutil
import os
import sys
from dotenv import load_dotenv
from os.path import join, dirname
import json
import youtube_dl


class SoundcloudPlugin():
    env_path = join(dirname(__file__), 'secrets.env')
    load_dotenv(env_path)
    def __init__(self):
        self.directory_name = ''
        self.username = ''
        self.playlist_name = ''
        self.playlist_description = ''
        self.tracks = {}
        self.playlist_url = ''
        self.chrome_driver = os.environ.get("CHROME_DRIVER")

    ''' using beautiful soup and selenium to find all the items in a playlist in soundcloud and add the song name and their links
        check if song exists in spotify and if it does then add it to the created playlist, else download it. '''
    def get_songs(self):
        token = self.authenticate_spotify()
        driver = webdriver.Chrome(self.chrome_driver)
        driver.get(self.playlist_url)
        html = driver.page_source
        spotify_uris = []
        soup = BeautifulSoup(html, 'html.parser')

        # start our beautiful soup search with the parent element
        results = soup.find_all("li", class_="trackList__item sc-border-light-bottom")

        # traverse through the all the sub elements of our search to find all the song divs in a page then retrieve their links and song data
        for x in results:
            div = x.find_all("div", class_="trackItem g-flex-row sc-type-small sc-type-light")
            for z in div:
                final_div = z.find_all("div", class_="trackItem__content sc-truncate")
                for ref in final_div:
                    href = ref.find("a", class_="trackItem__trackTitle sc-link-dark sc-font-light", href=True)
                    track_name = href.text.lower().replace(" ", "+") 
                    artist_name = ref.find("a", class_="trackItem__username sc-link-light").text.lower().replace(" ", "+") 

                    # if spotify can find a uri for this song, then we append it to our list, else we send it to our dictionary which will download the song instead
                    if self.get_spotify_uri(track_name, artist_name, token) is not None:
                        spotify_uris.append(self.get_spotify_uri(track_name, artist_name, token))
                    else:
                        link = "https://soundcloud.com" + href["href"]
                        self.tracks.update({href.text: link})
        
        driver.close()
        playlist_id = self.create_playlist(token)
        self.add_songs_to_playlist(spotify_uris, token, playlist_id)
        self.download_soundcloud(self.tracks)
        self.download_soundcloud(self.tracks)
        
    ''' authenticate users to access their spotify account. Returns a token that we can use to create playlists, search for songs and add songs to playlist '''
    def authenticate_spotify(self):
        client_id = os.environ.get("CLIENT_ID")
        client_secret = os.environ.get("CLIENT_SECRET")
        redirect_uri = os.environ.get("REDIRECT_URI")
        username = self.username
        scope = "user-library-read user-top-read playlist-modify-public user-follow-read"
        token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)
        return token

    ''' make a query for a song based on its song and artist name '''
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

    ''' create the playlist on spotify to store our songs '''
    def create_playlist(self, token):
        request_body = json.dumps({"name": self.playlist_name, "description": self.playlist_description, "public": True})
        query = "https://api.spotify.com/v1/users/{}/playlists".format(self.username)
        response = requests.post(query, data=request_body, headers={"Content-Type":"application/json", "Authorization":"Bearer {}".format(token)})
        response_json = response.json()
        return response_json["id"]

    ''' add the found soundcloud songs to created playlist on spotify '''
    def add_songs_to_playlist(self, uris, token, playlist_id):
        request_data = json.dumps(uris)
        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)
        response = requests.post(query,data=request_data, headers={"Content-Type": "application/json","Authorization": "Bearer {}".format(token)})
        response_json = response.json()

    ''' use youtube dl to download all the soundcloud songs that werent found on spotify '''
    def download_soundcloud(self, links):
        # preffered formating for audio 
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
            }]}
        ydl = youtube_dl.YoutubeDL(ydl_opts)
        for track in links.keys():
            print('-------- Downloading ' + track + ' ---------')    
            ydl.download([links[track]])   

    ''' make the directory in the same directory as the projects and move all the downloaded songs there
    Note this will work if there aren't any .mp3 files already in downloads folder '''
    def make_directory(self):
        directory_name = self.directory_name
        parent_dir = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(dirname(__file__), directory_name)
        source_files = os.listdir(parent_dir)
        os.mkdir(path)
        for file in source_files:
            if file.endswith(".mp3"):
                shutil.move(os.path.join(parent_dir, file), os.path.join(path,file))
        print("Moved files to created directory: " + str(path))

if __name__ == "__main__":
    soundcloud = SoundcloudPlugin()
    soundcloud.username = sys.argv[1]
    soundcloud.playlist_url = sys.argv[2]
    soundcloud.playlist_name = sys.argv[3]
    soundcloud.playlist_description = sys.argv[4]
    soundcloud.directory_name = sys.argv[5]
    soundcloud.get_songs()
    soundcloud.make_directory()
    
