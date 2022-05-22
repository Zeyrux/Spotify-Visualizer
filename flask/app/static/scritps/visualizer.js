let filename = document.getElementById("script").getAttribute("filename");
let canvas = document.getElementById("canvas");
let songname = filename.replace(".aac");

let bar_width = 1;
let frame_cnt = 0;

let fps = 60
let now
let then = Date.now()
let interval = 1000 / fps
let delta


function init() {
    let audio = document.getElementById("audio");
    audio.src += filename;
    audio.volume = 0.05;
    
    window.addEventListener("click", initMp3Player);
}


function initMp3Player(){
    window.removeEventListener("click", initMp3Player);

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
	ctx.font = radius / 4+ "px serif";
	ctx.textBaseline = "middle";
	ctx.strokeText(songname, canvas.width / 2 - Math.round(ctx.measureText(songname).width) / 2, canvas.height * 0.35);
}


window.setInterval(function (e) {
    console.log(frame_cnt)
    frame_cnt = 0
}, 1000)


init();
