import datetime
import json
import os
import requests
import flask, flask.views
from flask import render_template, redirect, request
import csv
import functools
from hashlib import sha256
from app import app

app.secret_key = "lol"
users = {'user1':'password','user2':'password', 'user3':'password'}

ownership = {'betterdays.mp3':'user2', 'buddy.mp3': 'user2',\
             'tenderness.mp3':'user3','tomorrow.mp3':'user3'}

wallets = {'user1': 100, 'user2': 100, 'user3': 100}

secret_key = [1234,5432,2345,6789]

def user_hash(users):

    user = users.keys()
    password = users.values()

    user_hash = {}

    for i in range(0,len(user)):
      hash = sha256()
      string = user[i] + password[i]
      hash.update(string)
      user_hash[user[i]] = hash.hexdigest()

    return user_hash

def music_hash(ownership, secret_key):

    song_name = ownership.keys()
    owners = ownership.values()

    ownership_hash = {}

    for i in range(0,len(song_name)):
      hash = sha256()
      string = song_name[i] + owners[i] + str(secret_key[i])
      hash.update(string)
      ownership_hash[song_name[i]] = hash.hexdigest()

    return ownership_hash


class Main(flask.views.MethodView):
    def get(self):
        return flask.render_template('index.html')
    
    def post(self):
        if 'logout' in flask.request.form:
            flask.session.pop('username', None)
            return flask.redirect(flask.url_for('index'))
        required = ['username', 'passwd']

        for r in required:
            if r not in flask.request.form:
                flask.flash("Error: {0} is required.".format(r))
                return flask.redirect(flask.url_for('index'))
        username = "null"
        username = flask.request.form['username']
        passwd = flask.request.form['passwd']


        if username in users and users[username] == passwd:
            flask.session['username'] = username

        else:
            flask.flash("Username doesn't exist or incorrect password")
        return flask.redirect(flask.url_for('index'))


# The node with which our application interacts, there can be multiple
# such nodes as well.
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"

posts = []


def fetch_posts():
    """
    Function to fetch the chain from a blockchain node, parse the
    data and store it locally.
    """
    get_chain_address = "{}/chain".format(CONNECTED_NODE_ADDRESS)
    response = requests.get(get_chain_address)

    songs = os.listdir(os.path.abspath('app/static/music'))

    if response.status_code == 200:
        content = []
        chain = json.loads(response.content)
        for block in chain["chain"]:
            for tx in block["transactions"]:
                tx["index"] = block["index"]
                tx["hash"] = block["previous_hash"]
                content.append(tx)
    username_list = users.keys()

    # For Debugging
    test = chain

    global posts,test
    posts = sorted(content, key=lambda k: k['timestamp'],reverse=True)



@app.route('/base')
def base():
    return render_template('base.html')


@app.route('/wallet')
def wallet():
    flask.session['user_wallet'] = wallets.get(flask.session['username'])
    return render_template('wallet.html',
                            users = wallets.keys(),
                            wallets = wallets.values())                            

@app.route('/Logout')
def Logout():
    flask.session.pop('username', None)
    return flask.redirect('/')

@app.route('/music')
def music():
    fetch_posts()
    songs = os.listdir(os.path.abspath('app/static/music'))
    return render_template('music_player.html',
                           title='Music Player',
                           posts=posts,
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=timestamp_to_string,
                           songs=songs)

@app.route('/audioplayer')
def audio_player():
    songs = os.listdir(os.path.abspath('app/static/music'))
    song_name = "No Audio"
    return render_template('audioplayer.html',
                           songs=songs,
                           song_name = song_name
                           )


@app.route('/submit', methods=['GET','POST'])
def submit_button():

    ownership_hash = music_hash(ownership, secret_key)
    user_hash_dict = user_hash(users)
    """
    Endpoint to create a new transaction via our application.
    """
    song_name = request.form["song_name"]
    song_location = "/static/music/" + song_name 
    artist = ownership.get(song_name)
    current_user = flask.session['username']
    song_hash = ownership_hash[song_name]
    current_user_hash = user_hash_dict[current_user]
    artist_hash = user_hash_dict[artist]

    post_object = {
        'song': song_name,
        'listener': current_user_hash,
        'artist': artist_hash,
        'amount': 1,
        'song_hash': song_hash
    }

    wallets[current_user] = wallets.get(current_user) - 1
    wallets[artist] = wallets.get(artist) + 1

    # Submit a transaction
    new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)

    requests.post(new_tx_address,
                  json=post_object,
                  headers={'Content-type': 'application/json'})



    return render_template('audioplayer.html',
                    song_name = song_name,
                    listener = current_user,
                    artist = artist,
                    amount = 1,
                    song_location = song_location)



def timestamp_to_string(epoch_time):
    return datetime.datetime.fromtimestamp(epoch_time).strftime('%H:%M')


class BlockTracker(flask.views.MethodView):
  # @login_required
  def get(self):
    fetch_posts()
    return render_template('BlockTracker.html',
                         title='Block Explorer',
                         posts=posts,
                         test = test,
                         node_address=CONNECTED_NODE_ADDRESS,
                         readable_time=timestamp_to_string)

app.add_url_rule('/',
                 view_func=Main.as_view('index'),
                 methods=["GET", "POST"])

app.add_url_rule('/BlockTracker/',
                 view_func=BlockTracker.as_view('BlockTracker'),
                 methods=["GET", "POST"])










