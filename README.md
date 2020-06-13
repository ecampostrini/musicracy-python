# Musicracy
Musicracy is a collaborative and democratic playlist accessible via HTTP
to which anyone on the same network can connect to in order to search and
vote for the songs they want to listen to. Every time a song
playback finishes, the application backend picks the one with most votes from the playlist to be played next.

I had a couple of goals in mind with this little project:
- offer a solution to the playlist tyranny we have all been victims  (or guilty) of at home.
- have a fun playground to try and learn web technologies. At the time of
starting with it I was interested in Flask, Bootstrap, Docker and
microservices. If I had to do it now I would probably use Node on the backend.

# Setup
## Prerequisites
- Linux (didn't try it in Windows so IDK whether it works or not OOTB there)
- Python 3
- Docke and Docker Compose
- A premium Spotify account (required for the Spotify backend)

## Running the app with the Spotify backend

### Configure the backend
1. [Register](https://developer.spotify.com/documentation/general/guides/app-settings/) the application on Spotify
2. From the project root run the script called `gen_config.sh`
3. Select the Spotify backend and provide the data the script asks for


### Run the app

1. From the project root run `docker-compose up` and that should spin up all 3 containers with the different services (frontend, backend and a simple KV storage)
2. In your browser go to `http://0.0.0.0:5000` and follow the instructions
3. Now, any device connected to the same network should be able to access
   the playlist. Assuming your network IP is `192.168.178.75`
   then opening the following address from the browser should be enough:
   `http://192.168.178.75:5000`

## TODOs
- [ ] Show the playlist name  in the instructions page from the Spotify backend


## Notes
This is a little side project that I work on whenever I have some spare time (very rarely nowadays with a 👶 at 🏠). It should therefore be ran at your own risk.
