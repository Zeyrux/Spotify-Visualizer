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


class Memory {
	constructor(capacity) {
		this.capacity = capacity;
		this.memory = [];
		this.cur_pos = 0;
	}

	push(value) {
		if (this.cur_pos == this.capacity) {
			this.cur_pos = 0;
		}
		if (this.memory.length < this.capacity) {
			this.memory.push(value);
		} else {
			this.memory[this.cur_pos] = value;
		}
		this.cur_pos += 1;
	}

	get(index) {
		index = this.cur_pos - index - 1;
		if (index < 0) {
			index += this.capacity;
		}
		return this.memory[index];
	}
}


class ParticleSystem {
	constructor(middle_x, middle_y) {
		this.particles = [];
		this.particle_size = 3;
		this.particles_per_row = 75;
		this.velocity = 3;
		this.memory = new Memory(Math.ceil(this.particles_per_row * 2 / this.velocity));
		this.middle = {
			x: middle_x,
			y: middle_y
		}
		this.max;
		this.get_image_data()
	}

	get_image_data() {
		let image = document.createElement("img");
		image.src = track.image_url;
		image.crossOrigin = "Anonymous";
		image.addEventListener("load", function () {
			let ctx = canvas.getContext("2d");
			ctx.clearRect(0, 0, canvas.width, canvas.height);
			ctx.drawImage(image, 0, 0, this.particles_per_row, this.particles_per_row);
			let data = ctx.getImageData(0, 0, this.particles_per_row, this.particles_per_row);
			ctx.clearRect(0, 0, canvas.width, canvas.height);
			this.set_particles(data)
		}.bind(this), {once: true});
	}

	set_particles(data) {
		for (let y = 0; y < data.height; y++) {
			let row = [];
			for (let x = 0; x < data.width; x++) {
				let alpha = data.data[(x * 4 + y * 4 * data.width) + 3] - 0.5;
				if (alpha < 0) {
					alpha = 0;
				}
				row.push({
					x : x * this.particle_size,
					y : y * this.particle_size,
					color: "rgba("
						+ data.data[(x * 4 + y * 4 * data.width)] + ", "
						+ data.data[(x * 4 + y * 4 * data.width) + 1] + ", "
						+ data.data[(x * 4 + y * 4 * data.width) + 2] + ", "
						+ alpha + ")"
				});
			}
			this.particles.push(row);
		}
		this.max = {
			x: this.particles.length,
			y: this.particles[0].length
		}
	}

	draw(ctx, bass) {
		if (this.max == undefined) {
			return;
		}
		bass = bass / 300
		if (bass < 1) {
			bass = 1
		}
		this.memory.push(bass)
		for (let i = 0; i < this.particles.length; i++) {
			const row = this.particles[i];
			for (let j = 0; j < row.length; j++) {
				const particle = row[j];
				let x_distance = particle.x - (this.max.x / 2) * this.particle_size;
				let y_distance = particle.y - (this.max.y / 2) * this.particle_size;
				let bass = this.memory.get(
					Math.round((
						Math.sqrt(Math.pow(Math.abs(x_distance / this.particle_size), 2) 
						+ Math.pow(Math.abs(y_distance / this.particle_size), 2))
						) / this.velocity)
				);
				let x = this.middle.x + Math.round(x_distance * bass);
				let y = this.middle.y + Math.round(y_distance * bass);
				ctx.fillStyle = particle.color;
				ctx.beginPath();
				ctx.arc(x, y, this.particle_size, 2 * Math.PI, false);
				ctx.fill();
			}
		}
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

		this.particle_system = new ParticleSystem(canvas.width / 2, canvas.height / 2);
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
		this.particle_system.draw(this.ctx, radius_circle_bass);
	}
}


let visualizer = new Visualizer();
visualizer.start();
