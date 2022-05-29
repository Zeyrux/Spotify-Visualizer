import { create_form, create_button } from "./utilities.js";

export var gradientBars;
export var gradientCircleAll;
export var gradientCircleBass;
export var bars;

let controlls = document.getElementById("controlls");
let audio = document.getElementById("audio");
let loop_active = false;

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


function init() {
	window.addEventListener("resize", resize);
	resize();

	controlls.appendChild(create_form("skip_form", "Skip", false, undefined, undefined));
	controlls.appendChild(create_form(undefined, "back", true, "back", "back"));
	controlls.appendChild(create_button("Loop", "loop"))

	window.setInterval(function (e) {
		if (audio.currentTime > audio.duration - 1) {
			if (loop_active)
				audio.currentTime = 0;
			else
				document.getElementById("skip_form").submit();
		}
	}, 500);

	let button_loop = document.getElementById("loop");
	document.getElementById("loop").addEventListener("click", function() {
		if (loop_active) {
			loop_active = false;
			button_loop.style.background = "rgb(211, 102, 102)";
		} else {;
			loop_active = true;;
			button_loop.style.background = "rgb(42, 252, 0)";
		};
	});
}


init();
