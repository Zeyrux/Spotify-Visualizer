import { Playlist, Track } from "./tracks.js";

export var controller = JSON.parse(document.getElementById("init_script").getAttribute("controller"));
export var user_playlists = JSON.parse(document.getElementById("init_script").getAttribute("user_playlists"));
export var track = new Track(JSON.parse(document.getElementById("init_script").getAttribute("track")));

for (let i = 0; i < user_playlists.length; i++) {
    user_playlists[i] = new Playlist(user_playlists[i]);
}


function init() {
    document.getElementById("audio").volume = controller["volume"];
    document.getElementById("audio").play();
}


init();
