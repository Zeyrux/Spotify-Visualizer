import { setGradients, bars, gradientBars, gradientCircleAll, gradientCircleBass } from "./controller.js";
import { controller } from "./init.js";

let songname = document.getElementById("script").getAttribute("song_name");
let canvas = document.getElementById("canvas");
let audio = document.getElementById("audio");

let bar_width = 1;
let frame_cnt = 0;
let analyser;
let ctx;

let now;
let then = Date.now();
let interval = 1000 / controller["fps"];
let delta;


function init() {
    let context = new AudioContext();

	if (context.state == "suspended") {
		// audio context can not start
		window.addEventListener("click", enable_anaylser);
	} else {
		// audio context started
		enable_anaylser();
	}
}


function enable_anaylser() {
    window.removeEventListener("click", enable_anaylser);

	audio.play();
	let context = new AudioContext();
	analyser = context.createAnalyser();
	let source = context.createMediaElementSource(audio);
	source.connect(analyser);
	analyser.connect(context.destination);
	ctx = canvas.getContext('2d');

    setGradients();
    frameLopper();
}


function average(ar) {
	let sum = 0;
	for (let i = 0; i < ar.length; i++) {
		sum += ar[i];
	}
	return sum / ar.length;
}


function frameLopper() {
    requestAnimationFrame(frameLopper);

    now = Date.now();
    delta = now - then;
	interval = 1000 / controller["fps"]

    if (delta > interval) {
        animate()
        then = now - (delta % interval)
    }
}


function animate(){
	// skip every second frame
    frame_cnt += 1;
	//fbc_array max: 255
	let fbc_array = new Uint8Array(analyser.frequencyBinCount);
	analyser.getByteFrequencyData(fbc_array);
	ctx.clearRect(0, 0, canvas.width, canvas.height);
	ctx.fillStyle = gradientBars;
    
    // draw bars
    for (let i = 0; i < bars; i+=1) {
		let bar_x = i * 2;
		let bar_height = -(fbc_array[i] * canvas.height / 275);
        ctx.fillRect(canvas.width / 2 + bar_x, canvas.height, bar_width, bar_height);
        ctx.fillRect(canvas.width / 2 + bar_x * -1, canvas.height, bar_width, bar_height);
	}

    // circle all
	ctx.fillStyle = gradientCircleAll;
	ctx.beginPath();
	let radius = Math.round(average(fbc_array.slice(0, bars)) * canvas.height / 275);
	ctx.arc(canvas.width / 2, 0, radius, 2 * Math.PI, false);
	ctx.fill();

    // circle bass
	ctx.fillStyle = gradientCircleBass;
	ctx.beginPath();
	radius = Math.round(average(fbc_array.slice(0, 5)) * canvas.height / 275);
	ctx.arc(canvas.width / 2, 0, radius, 2 * Math.PI, false);
	ctx.fill();

    // text
	let font_size = radius / 4;
	if (font_size < 20)
		font_size = 20;
	ctx.font = font_size + "px serif";
	ctx.textBaseline = "middle";
	ctx.strokeText(songname, canvas.width / 2 - Math.round(ctx.measureText(songname).width) / 2, canvas.height * 0.35);
}


window.setInterval(function (e) {
    console.log(frame_cnt)
    frame_cnt = 0
}, 1000)


init();
