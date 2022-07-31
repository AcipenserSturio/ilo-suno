var now = new Date(1654162200000);

function set_overlay() {
	var times = Object.keys(timings);
	var time = 0;
	Array.from(times).forEach(function(element) {
	var eventTime = new Date(Number(element));
	if (now >= eventTime)
		time = eventTime.getTime();
	});
	var currentEvent = timings[time];
	var current = document.getElementById("current");
	current.innerHTML = "";
	var currentText = document.createElement("span");
	currentText.innerHTML = `<b>${currentEvent['title']}</b> by ${currentEvent['authors']}`;
	current.appendChild(currentText);
	var nextTime = times[times.indexOf(time) + 2];
	var nextMinutes = Math.ceil((nextTime - now.getTime()) / 60000);
	var nextEvent = timings[nextTime];
	var next = document.getElementById("next");
	next.innerHTML = "";
	var nextText = document.createElement("span");
	nextText.innerHTML = `<h1>in ${nextMinutes} minutes</h1><b>${nextEvent['title']}</b> by ${nextEvent['authors']}`;
	next.appendChild(nextText);
}

var timings = {};

Promise.all([
	fetch('events.json')
	.then(res => res.json())
])
.then(([events]) => {
	Array.from(events).forEach(function(element) {
		var start = new Date(Date.parse(element['start'] + '+00:00'));
		timings[start.getTime()] = element;
	});
	set_overlay;
}).catch(err => {
	console.log(err)
});

setInterval(set_overlay, 1000);
