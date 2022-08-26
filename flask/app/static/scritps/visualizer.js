import { setGradients, bars, gradientBars, gradientCircleAll, gradientCircleBass } from "./controller.js";
import { controller, track } from "./init.js";


let canvas = document.getElementById("canvas");
let audio = document.getElementById("audio");


function average(array) {
	let sum = 0;
	array.forEach(number => {
		sum += number;
	});
	return sum / array.length
}


class ParticleSystem {


	set_image_data() {
		let image = document.createElement("img");
		image.src = track.image_url;
		image.crossOrigin = "Anonymous";
		image.addEventListener("load", function () {
			let ctx = canvas.getContext("2d");
			ctx.drawImage(image, 0, 0);
			console.log(ctx.getImageData(0, 0, image.width, image.height));
			ctx.clearRect(0, 0, canvas.width, canvas.height);
		}, {once: true})
	}
}


class Visualizer {
	constructor () {
		this.bar_width = 1;
		this.frame_cnt = 0;
		this.analyser;
		this.ctx;
		
		this.now;
		this.then = Date.now();
		this.interval = 1000 / controller["fps"];
		this.delta;

		this.particle_system = new ParticleSystem();
	}

	start () {
		let context = new AudioContext();
		if (context.state == "suspended") {
			// audio context can not start
			window.addEventListener("click", this.enable_anaylser, { once: true });
		} else {
			// audio context started
			this.enable_anaylser();
		}
	}

	enable_anaylser() {
		audio.play();
		let context = new AudioContext();
		let source = context.createMediaElementSource(audio);
		this.analyser = context.createAnalyser();
		source.connect(this.analyser);
		this.analyser.connect(context.destination);
		this.ctx = canvas.getContext("2d");
		setGradients();
		this.set_image_data();
		this.lopper();
	}

	lopper() {
		function frame_lopper() {
			this.now = Date.now();
			this.delta = this.now - this.then;
			this.interval = 1000 / controller["fps"]
		
			if (this.delta > this.interval) {
				this.animate()
				this.then = this.now - (this.delta % this.interval)
			}
			this.lopper()
		}
		requestAnimationFrame(frame_lopper.bind(this));
	}

	animate_bars(fbc_array) {
		this.ctx.fillStyle = gradientBars;
		for (let i = 0; i < bars; i += 1) {
			let bar_x = i * 2;
			let bar_height = -(fbc_array[i] * canvas.height / 275);
			this.ctx.fillRect(canvas.width / 2 + bar_x, canvas.height, this.bar_width, bar_height);
			this.ctx.fillRect(canvas.width / 2 + bar_x * -1, canvas.height, this.bar_width, bar_height);
		}
	}

	animate_circle_all(radius) {
		this.ctx.fillStyle = gradientCircleAll;
		this.ctx.beginPath();
		this.ctx.arc(canvas.width / 2, 0, radius, 2 * Math.PI, false);
		this.ctx.fill();
	}

	animate_circle_bass(radius) {
		this.ctx.fillStyle = gradientCircleBass;
		this.ctx.beginPath();
		this.ctx.arc(canvas.width / 2, 0, radius, 2 * Math.PI, false);
		this.ctx.fill();
	}

	animate_text(font_size) {
		if (font_size < 25)
			font_size = 25;
		this.ctx.font = font_size + "px serif";
		this.ctx.textBaseline = "middle";
		this.ctx.strokeText(track.name, canvas.width / 2 - Math.round(this.ctx.measureText(track.name).width) / 2, canvas.height * 0.35);
	}

	animate_image() {

	}

	animate() {
		// fbc_array max: 255
		// calculate everything
		let fbc_array = new Uint8Array(this.analyser.frequencyBinCount);
		this.analyser.getByteFrequencyData(fbc_array);
		this.ctx.clearRect(0, 0, canvas.width, canvas.height);
		let radius_circle_all = Math.round(average(fbc_array.slice(0, bars)) * canvas.height / 275);
		let radius_circle_bass = Math.round(average(fbc_array.slice(0, 5)) * canvas.height / 275);
		
		// animate
		this.animate_bars(fbc_array);
		this.animate_circle_all(radius_circle_all);
		this.animate_circle_bass(radius_circle_bass);
		this.animate_text(radius_circle_bass / 4);
	}
}


let visualizer = new Visualizer()
visualizer.start()
