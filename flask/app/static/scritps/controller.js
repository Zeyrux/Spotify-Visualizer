import { create_form, create_button, create_checkable_button, create_slider_volume, create_slider_duration, seconds_to_string, create_fps } from "./utilities.js";
import { controller } from "./init.js";

export var gradientBars;
export var gradientCircleAll;
export var gradientCircleBass;
export var bars;

let controlls = document.getElementById("controlls");
let audio = document.getElementById("audio");
let post_init_id

function resize() {
    canvas.width = window.innerWidth - 20;
    canvas.height = window.innerHeight - 20;
    bars = Math.ceil(canvas.width / 4) + 1;
    setGradients();
}


export function setGradients() {
	let ctx = canvas.getContext('2d')
    gradientBars = ctx.createLinearGradient(canvas.width, canvas.height, canvas.width, -canvas.height);
	gradientBars.addColorStop(0.0, "blue");
	gradientBars.addColorStop(0.4, "red");
	gradientCircleAll = ctx.createLinearGradient(canvas.width, 0, canvas.width, canvas.height);
	gradientCircleAll.addColorStop(0, "rgba(0, 0, 0, 0.2)");
	gradientCircleAll.addColorStop(0.5, "rgba(255, 255, 255, 0.2)");
	gradientCircleBass = ctx.createLinearGradient(canvas.width, 0, canvas.width, canvas.height);
	gradientCircleBass.addColorStop(0, "rgba(0, 0, 255, 0.2)");
	gradientCircleBass.addColorStop(0.5, "rgba(0, 255, 0, 0.2");
}


function post_init() {
	if (! isNaN(audio.duration)) {
		clearInterval(post_init_id);
		document.getElementById("duration_slider").max = audio.duration;
	}
}


function init() {
	window.addEventListener("resize", resize);
	resize();

	// add buttons
	controlls.appendChild(create_slider_duration(audio.duration))
	controlls.appendChild(create_form("skip_form", "Skip", false, undefined, undefined));
	controlls.appendChild(create_form("back_form", "Back", true, "back", "back"));
	controlls.appendChild(create_button("Pause", "hover_button", "play_pause"));
	controlls.appendChild(create_checkable_button("Loop", "loop_active", false));
	controlls.appendChild(create_fps());
	controlls.appendChild(create_slider_volume(audio.volume));

	// add play and pause
	let button_play_pause = document.getElementById("play_pause");
	button_play_pause.addEventListener("click", function (e) {
		if (button_play_pause.innerHTML == "Pause")
			audio.pause();
		else
			audio.play();
	});

	audio.onplay = (e) => document.getElementById("play_pause").innerHTML = "Pause";
	audio.onpause = (e) => document.getElementById("play_pause").innerHTML = "Play";
	navigator.mediaSession.setActionHandler("nexttrack", () => document.getElementById("skip_form").submit());
	navigator.mediaSession.setActionHandler("previoustrack", () => document.getElementById("back_form").submit());

	// skip song if song ends
	window.setInterval(function (e) {
        document.getElementById("duration_label").innerHTML = seconds_to_string(audio.currentTime);
		document.getElementById("duration_slider").value = audio.currentTime;
		if (audio.currentTime > audio.duration - 1) {
			if (controller["loop_active"])
				audio.currentTime = 0;
			else
				document.getElementById("skip_form").submit();
		}
	}, 250);

	post_init_id = window.setInterval(post_init, 100);
}


init();
