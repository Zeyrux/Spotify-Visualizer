var gradientBars;
var gradientCircleAll;
var gradientCircleBass;
var bars;


function resize() {
    canvas.width = window.innerWidth - 20;
    canvas.height = window.innerHeight - 20;
    bars = Math.ceil(canvas.width / 4) + 1;
    setGradients();
}

function setGradients() {
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


window.addEventListener("resize", resize);
resize()
