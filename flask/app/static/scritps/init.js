export var controller = JSON.parse(document.getElementById("init_script").getAttribute("controller"));


function init() {
    document.getElementById("audio").volume = controller["volume"];
    document.getElementById("audio").play();
}


init();
