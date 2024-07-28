import requests
import urllib.parse

from datetime import datetime, timedelta
from flask import Flask, redirect, request, jsonify, session, render_template



app = Flask(__name__)
app.secret_key = '53d355f8-571a-4590-a310-1f9579440851'

CLIENT_ID = '0cda9fe12c6d425494a15bf39ae055ba'
CLIENT_SECRET = 'ca411aa4f3a94888bcfc161c781109ed'
REDIRECT_URI = 'http://localhost:5000/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

# global variables to store data
global_playlists_data = []
global_songs = []
global_gifs = []

# home page route
@app.route('/')
def index():
    return "Welcome to my Spotify App <a href='/login'>Login with Spotify</a>"

# login route
@app.route('/login')
def login():
    scope = 'user-read-private user-read-email user-modify-playback-state playlist-read-private playlist-read-collaborative'

    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)

# redirect from login to get tokens
@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({'error': request.args['error']})
    
    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp()  + token_info['expires_in']

        return redirect('/playlists')




# route to get playlists
@app.route('/playlists')
def get_playlists():
    print("here")
    global global_playlists_data

    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh_token')
    
    headers = {
        'Authorization': f'Bearer {session["access_token"]}'
    }

    response = requests.get(API_BASE_URL + 'me/playlists', headers=headers)

    playlists_data = response.json()['items']

    global_playlists_data = playlists_data


    return render_template('layout.html', playlists=global_playlists_data)

# route to get tracks in a playlist
@app.route('/playlists/<playlist_id>/tracks')
def get_tracks(playlist_id):
    global global_playlists_data

    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh_token')
    
    headers = {
        'Authorization': f'Bearer {session["access_token"]}'
    }

    response = requests.get(API_BASE_URL + f'playlists/{playlist_id}/tracks', headers=headers)
    tracks_data = response.json()['items']

                
    return render_template('tracks.html', tracks=tracks_data, playlists=global_playlists_data)



# route to display a song
@app.route('/tracks/<songs_id>')
def get_songs(songs_id):
    global global_playlists_data
    global global_songs

    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh_token')
    
    headers = {
        'Authorization': f'Bearer {session["access_token"]}'
    }

    response = requests.get(API_BASE_URL + f'tracks/{songs_id}', headers=headers)
    songs_data = response.json()

    


    if songs_data not in global_songs:
        global_songs.append(songs_data)

    return render_template('songs.html', songs=global_songs, playlists=global_playlists_data)

@app.route('/songs')
def goto_songs():
    global global_playlists_data
    global global_songs

    return render_template('songs.html', songs=global_songs, playlists=global_playlists_data)


    

# route to refresh expired token
@app.route('/refresh_token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant_type':'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }
    
        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']
        
        return redirect('/playlists')
    

@app.route('/delete-song/<songs_id>', methods=['DELETE'])
def delete_song(songs_id):
    global global_playlists_data
    global global_songs

    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh_token')
    
    headers = {
        'Authorization': f'Bearer {session["access_token"]}'
    }

    response = requests.get(API_BASE_URL + f'tracks/{songs_id}', headers=headers)
    songs_data = response.json()

    if songs_data in global_songs:
        global_songs.remove(songs_data)
        return jsonify({'message': 'Song deleted successfully'}), 200

    
    return jsonify({'error': 'Song not found'}), 404

@app.route('/play-song/<songs_id>/<track_id>', methods=['PUT'])
def play_song(songs_id, track_id):
    global global_playlists_data
    global global_songs

    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh_token')
    
    headers = {
        'Authorization': f'Bearer {session["access_token"]}'
    }

    payload = {
        'context_uri': f'{songs_id}',
        'offset': {
            'uri': f'{track_id}'  # Specify the track URI
        }
    }

    
    response = requests.put(API_BASE_URL + f'me/player/play', json=payload, headers=headers)


    return jsonify({'error': 'Song not found'}), 404

    
@app.route('/giphy')
def giphy():
    global global_playlists_data
    return render_template('giphy.html',  playlists=global_playlists_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)