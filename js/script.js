/*
 * This file is part of Statistical Districts.
 * Copyright (c) 2017, James Sinton
 * All rights reserved.
 * Released under the BSD 3-Clause License
 * https://github.com/jksinton/Statistical-Districts/blob/master/LICENSE
 *
 */


function loadGoogleMapsAPI() {
    var script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = 'https://maps.googleapis.com/maps/api/js?v=3' +
        '&key=' + GOOGLE_API_KEY + 
		'&libraries=places&callback=initAutocomplete';
    document.body.appendChild(script);
}

window.onload = loadGoogleMapsAPI;

function initAutocomplete() {
	var uluru = {lat: 29.8, lng: -95.6};
    var map = new google.maps.Map(document.getElementById('map'), {
    	zoom: 11,
    	center: uluru,
    	fullscreenControl: true
    });
	// TODO 
	// Host index.html via python-based webserver Tornado
	//
	// Error encountered when geojson is access on a different server, e.g., jksinton.com
	// No 'Access-Control-Allow-Origin' header is present on the requested resource.
	// 
	// Error produced when geojson is accessed locally:
	// Cross origin requests are only supported for protocol schemes: http, data, chrome, chrome-extension, https.
	//map.data.loadGeoJson("/geojson/tx7.geojson");
	//map.data.setStyle({ fillColor: '#2171b5'});
}
