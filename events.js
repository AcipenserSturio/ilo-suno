const TIMETRAVEL = 44792 * 1000;

function set_overlay() {
	var now = new Date();
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
	var currentAuthor = "";
	if(currentEvent['authors']) {
		currentAuthor = ` by ${currentEvent['authors']}`;
	}
	currentText.innerHTML = `<b>${currentEvent['title']}</b>${currentAuthor}`;
	current.appendChild(currentText);
	var nextTime = times[times.indexOf(time) + 2];
	var nextMinutes = Math.ceil((nextTime - now.getTime()) / 60000);
	var nextEvent = timings[nextTime];
	var next = document.getElementById("next");
	next.innerHTML = "";
	if (nextMinutes == 5 || nextMinutes == 10) {
		var nextText = document.createElement("span");
		var nextAuthor = "";
		if(nextEvent['authors']) {
			nextAuthor = ` by ${nextEvent['authors']}`;
		}
		nextText.innerHTML = `<h1>in ${nextMinutes} minutes</h1><b>${nextEvent['title']}</b>${nextAuthor}`;
		next.appendChild(nextText);
	}
}

var timings = {};

Promise.all([
	fetch('events.json')
	.then(res => res.json())
])
.then(([events]) => {
	Array.from(events).forEach(function(element) {
		var start = new Date(Date.parse(element['start'] + '+00:00') - TIMETRAVEL);
		timings[start.getTime()] = element;
	});
	set_overlay;
}).catch(err => {
	console.log(err)
});

setInterval(set_overlay, 1000);
