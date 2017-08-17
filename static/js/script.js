/*
 * This file is part of Statistical Districts.
 * 
 * Copyright (c) 2017, James Sinton
 * All rights reserved.
 * 
 * Released under the BSD 3-Clause License
 * https://github.com/jksinton/Statistical-Districts/blob/master/LICENSE
 *
 */


function loadGoogleMapsAPI() {
    var script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = 'https://maps.googleapis.com/maps/api/js?v=3' +
        '&key=' + GOOGLE_API_KEY + 
		'&libraries=places&callback=initMap';
    document.body.appendChild(script);
}

window.onload = loadGoogleMapsAPI;

function initMap() {
	var uluru = {lat: 29.8, lng: -95.6};
    var map = new google.maps.Map(document.getElementById('map'), {
    	zoom: 11,
    	center: uluru,
    	fullscreenControl: true
    });

	var district_layer = new google.maps.Data({map: map});
	var geounits_layer = new google.maps.Data({map: map});
	
	district_layer.loadGeoJson("/static/geojson/tx7.geojson");
	geounits_layer.loadGeoJson("/static/geojson/tx7-blockgroups.geojson");
	
	district_layer.setStyle({
		clickable: false,
		zIndex: 3,
		fillOpacity: 0.0,
		strokeColor: '#fff',
		strokeWeight: 3
	});
	geounits_layer.setStyle(styleFeature);
	
	geounits_layer.addListener('mouseover', mouseInToRegion);
    geounits_layer.addListener('mouseout', mouseOutOfRegion);
}

function styleFeature(feature) {
	var outlineWeight = 0.5, zIndex = 1;
	if (feature.getProperty('state') === 'hover') {
		outlineWeight = 3;
		zIndex = 2;
	}

	return {
	  strokeWeight: outlineWeight,
	  strokeColor: '#fff',
	  zIndex: zIndex,
	  fillColor: '#2171b5',
	  fillOpacity: 0.75
	};
}

function mouseInToRegion(e) {
	// set the hover state so the setStyle function can change the border
	e.feature.setProperty('state', 'hover');
}

function mouseOutOfRegion(e) {
	// reset the hover state, returning the border to normal
	e.feature.setProperty('state', 'normal');
}



