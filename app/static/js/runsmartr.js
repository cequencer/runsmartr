$(document).ready(function(){
    sizeMap();
    $(window).resize(sizeMap);
    addMap();
    $("#address").geocomplete();
});

function sizeMap(){
    $("#map").height($("body").height());
}

function addMap(){		// Mapbox.js map
    L.mapbox.accessToken = 'pk.eyJ1IjoiYW5keWFsbWFuZGh1bnRlciIsImEiOiJLOUh5aS1vIn0.zFS519161_PwwjqlyMWezA';
    var map = L.mapbox.map('map', 'andyalmandhunter.l52ai08p', {
	zoomControl: false
    }).setView([37.771, -122.409], 15);
    map.addControl(
	L.control.zoom().setPosition('bottomleft')
    );
}
