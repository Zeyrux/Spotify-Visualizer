export var controller = JSON.parse(document.getElementById("init_script").getAttribute("controller"));
export var user_playlists = JSON.parse(document.getElementById("init_script").getAttribute("user_playlists"));
console.log(user_playlists);


function init() {
    document.getElementById("audio").volume = controller["volume"];
    document.getElementById("audio").play();
}


init();
