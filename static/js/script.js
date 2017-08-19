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

// Global Variables
var map;
var variables = [];
var labels;
var ranges = {};
var district_layer;
var geounits_layer;
var district_min = Number.MAX_VALUE; 
var district_max = -Number.MAX_VALUE;

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
	/* TODO
	 * get variable settings for a particular congressional district 
	 */
	
	var uluru = {lat: 29.8, lng: -95.6};
    map = new google.maps.Map(document.getElementById('map'), {
    	zoom: 11,
    	center: uluru,
    	fullscreenControl: true
    });

	// Create data layers for Congressional District and
	// the sub-geounits, e.g., voting precinct, tract, or block group
	district_layer = new google.maps.Data({map: map});
	geounits_layer = new google.maps.Data({map: map});
	
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

	// fill in the options for the variable selection
	$.ajax({
  		url: '/static/data/fields.json',
  		async: false,
  		dataType: 'json',
  		success: function (json) {
    		variables = json;
  		}
	});	
	$.ajax({
  		url: '/static/data/labels.json',
  		async: false,
  		dataType: 'json',
  		success: function (json) {
    		labels = json;
  		}
	});
	console.log(variables);

	var selectBox = document.getElementById('variables');
	for (var i = 0; i < variables.length; i++) {
		ranges[variables[i]] = { min: Infinity, max: -Infinity };
		// Simultaneously, build the UI for selecting different
		// ranges
			$('<option></option>')
					.text(labels[variables[i]])
			.attr('value', variables[i])
			.appendTo(selectBox);
	}

	google.maps.event.addDomListener(selectBox, 'change', function() {
          clearData();
          loadData(selectBox.options[selectBox.selectedIndex].value);
    });
}

function loadData(selected_variable) {
	data = {};
	$.ajax({
  		url: '/static/data/pid_by_age.json',
  		async: false,
  		dataType: 'json',
  		success: function (json) {
    		data = json;
  		}
	});	
	
	console.log(data);
	geounits_layer.forEach(function(feature){
		var geoid = feature.getProperty('GEOID');
		var geo_variable = parseInt(data[geoid.toString()][selected_variable]);

		console.log(geo_variable);
		console.log(typeof(geo_variable));

		// keep track of min and max values
		if (geo_variable < district_min) {
		  	district_min = geo_variable;
		}
		if (geo_variable > district_max) {
		  	district_max = geo_variable;
		}

		// update the existing row with the new data
		feature.setProperty('geo_variable', geo_variable);

	});

	// update and display the legend
	document.getElementById('variable-min').textContent =
	  district_min.toString();
	document.getElementById('variable-max').textContent =
	  district_max.toString();

}


/** Removes census data from each shape on the map and resets the UI. */
function clearData() {
	district_min = Number.MAX_VALUE;
	district_max = -Number.MAX_VALUE;
	geounits_layer.forEach(function(row) {
	  row.setProperty('geo_variable', undefined);
	});
	document.getElementById('data-box').style.display = 'none';
	document.getElementById('data-caret').style.display = 'none';
}

function styleFeature(feature) {
	var low = [5, 69, 54];  // color of smallest datum
	var high = [151, 83, 34];   // color of largest datum

	// delta represents where the value sits between the min and max
	var delta = (feature.getProperty('geo_variable') - district_min) /
		(district_max - district_min);

	var color = [];
	for (var i = 0; i < 3; i++) {
	  // calculate an integer color based on the delta
	  color[i] = (high[i] - low[i]) * delta + low[i];
	}

	// determine whether to show this shape or not
	var show_row = true;
	if (feature.getProperty('geo_variable') == null || 
			isNaN(feature.getProperty('geo_variable'))) {
		show_row = false;
	}

	var outlineWeight = 0.5, zIndex = 1;
	if (feature.getProperty('state') === 'hover') {
		outlineWeight = 3;
		zIndex = 2;
	}

	return {
	  	strokeWeight: outlineWeight,
	  	strokeColor: '#fff',
	  	zIndex: zIndex,
	  	fillColor: 'hsl(' + color[0] + ',' + color[1] + '%,' + color[2] + '%)',
	  	fillOpacity: 0.75,
		visible: show_row
	};
}

function mouseInToRegion(e) {
	// set the hover state so the setStyle function can change the border
	e.feature.setProperty('state', 'hover');
 	console.log('GEOID: ' + e.feature.getProperty('GEOID'));
 	console.log(e.feature.getProperty('geo_variable'));
}

function mouseOutOfRegion(e) {
	// reset the hover state, returning the border to normal
	e.feature.setProperty('state', 'normal');
}



