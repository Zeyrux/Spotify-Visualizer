import { Playlist } from "./tracks.js";

export var controller = JSON.parse(document.getElementById("init_script").getAttribute("controller"));
export var user_playlists = JSON.parse(document.getElementById("init_script").getAttribute("user_playlists"));
for (let i = 0; i < user_playlists.length; i++) {
    user_playlists[i] = new Playlist(user_playlists[i]);
    
}
console.log(user_playlists);


function init() {
    document.getElementById("audio").volume = controller["volume"];
    document.getElementById("audio").play();
}


init();
