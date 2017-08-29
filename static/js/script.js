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
var categories;
var labels;
var ranges = {};
var district_layer;
var geounits_layer;
var district_min = Number.MAX_VALUE; 
var district_max = -Number.MAX_VALUE;
var chart_intervals = 100;
var barchart_data;

function loadGoogleMapsAPI() {
    var script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = 'https://maps.googleapis.com/maps/api/js?v=3' +
        '&key=' + GOOGLE_API_KEY + 
		'&callback=initMap';
    document.body.appendChild(script);
}

window.onload = loadGoogleMapsAPI;
 
function initMap() {
	/* TODO
	 * get variable settings for a particular congressional district 
	 */
	var category = 'Age';
	var category_type = 'Census';

	var uluru = {lat: 29.8, lng: -95.6};
    map = new google.maps.Map(document.getElementById('map'), {
    	zoom: 11,
    	center: uluru,
    	fullscreenControl: true
    });

	// Create data layers for the Congressional District and
	// the sub-geounits, e.g., voting precinct, tract, or block group
	district_layer = new google.maps.Data({map: map});
	geounits_layer = new google.maps.Data({map: map});
	
	geounits_layer.loadGeoJson("/static/geojson/tx7-blockgroups.geojson");
	district_layer.loadGeoJson("/static/geojson/tx7.geojson");
	
	district_layer.setStyle({
		clickable: false,
		zIndex: 3,
		fillOpacity: 0.0,
		strokeColor: '#43a2ca',
		strokeWeight: 3
	});

	geounits_layer.setStyle(style_feature);
	geounits_layer.addListener('mouseover', mouse_in_to_region);
    geounits_layer.addListener('mouseout', mouse_out_of_region);

	// fill in the options for the variable selection
	// get category fields
	$.ajax({
  		url: '/static/data/categories.json',
  		async: false,
  		dataType: 'json',
  		success: function (json) {
    		categories = json;
  		}
	});	
	
	var databox = document.getElementById('data-box');
    map.controls[google.maps.ControlPosition.RIGHT_TOP].push(databox);
	
	var fields = categories[category][category_type]['fields'];
	labels = categories[category][category_type]['labels'];

	set_select_box(fields, labels);
	var select_box = document.getElementById('fields');
	google.maps.event.addDomListener(select_box, 'change', function() {
		clear_data();
        load_data(select_box.options[select_box.selectedIndex].value);
        load_chart(select_box.options[select_box.selectedIndex].value);

    });
	init_chart(select_box.options[select_box.selectedIndex].value);
	load_maps();
}

function load_maps() {
	// wait for Google maps to finish loading and then do stuff
	google.maps.event.addListenerOnce(map, 'idle', function() {
		google.maps.event.trigger(document.getElementById('fields'), 'change');
		
		var controls = document.getElementById('controls');
    	map.controls[google.maps.ControlPosition.TOP_CENTER].push(controls);
		controls.style.opacity = 1;
	});
}

// TODO change from embedded onclick to DOM populated onclicks
function set_nav_behavior(){
	var age_census = document.getElementById("age-census");
	age_census.onclick = load_category('Age', 'Census');
}

function set_select_box(fields, my_labels) {
	var select_box = document.getElementById('fields');
	// clear any options
	while (select_box.firstChild) {
    	select_box.removeChild(select_box.firstChild);
	}
	for (var i = 0; i < fields.length; i++) {
	ranges[fields[i]] = { min: Infinity, max: -Infinity };
		// Simultaneously, build the UI for selecting different
		// ranges
		$('<option></option>')
			.text(my_labels[fields[i]])
			.attr('value', fields[i])
			.appendTo(select_box);
	}
}

function load_category(category, category_type) {
	var fields = categories[category][category_type]['fields'];
	labels = categories[category][category_type]['labels'];
	
	console.log(labels);

	set_select_box(fields, labels);
	clear_data();
	google.maps.event.trigger(document.getElementById('fields'), 'change');

	return false;
}

function load_data(selected_variable) {
	var data = {};
	$.ajax({
  		url: '/static/data/district-data.json',
  		async: false,
  		dataType: 'json',
  		success: function (json) {
    		data = json;
  		}
	});	
	
	geounits_layer.forEach(function(feature){
		var geoid = feature.getProperty('GEOID');
		var data_value = parseInt(data[geoid.toString()][selected_variable]);
		
		// keep track of min and max values
		if (data_value < district_min) {
		  	district_min = data_value;
		}
		if (data_value > district_max) {
		  	district_max = data_value;
		}

		// update the existing row with the new data
		feature.setProperty('data_value', data_value);
		feature.setProperty('label', labels[selected_variable]);

	});

	// update and display the legend
	document.getElementById('variable-min').textContent =
	  district_min.toString();
	document.getElementById('variable-max').textContent =
	  district_max.toString();
}

/** Removes census data from each shape on the map and resets the UI. */
function clear_data() {
	district_min = Number.MAX_VALUE;
	district_max = -Number.MAX_VALUE;
	geounits_layer.forEach(function(row) {
	  row.setProperty('data_value', undefined);
	});
	document.getElementById('data-box').style.display = 'none';
	document.getElementById('data-caret').style.display = 'none';
}

function style_feature(feature) {
	var low = [5, 69, 54];  // color of smallest datum
	var high = [151, 83, 34];   // color of largest datum

	// delta represents where the value sits between the min and max
	var delta = (feature.getProperty('data_value') - district_min) /
		(district_max - district_min);

	var color = [];
	for (var i = 0; i < 3; i++) {
	  // calculate an integer color based on the delta
	  color[i] = (high[i] - low[i]) * delta + low[i];
	}

	// determine whether to show this shape or not
	var show_row = true;
	if (feature.getProperty('data_value') == null || 
			isNaN(feature.getProperty('data_value'))) {
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

function mouse_in_to_region(e) {
	// set the hover state so the setStyle function can change the border
	e.feature.setProperty('state', 'hover');
	var geoid = e.feature.getProperty('GEOID');
	var data_value = e.feature.getProperty('data_value');
	var data_label = e.feature.getProperty('label');
	var percent = (data_value - district_min) / (district_max - district_min) * 100;

 	console.log('GEOID: ' + geoid );
 	console.log(data_label + ': ' + data_value);
	document.getElementById('data-label').textContent = data_label
    document.getElementById('data-value').textContent = data_value
    document.getElementById('data-box').style.display = 'block';
    document.getElementById('data-caret').style.display = 'block';
    document.getElementById('data-caret').style.paddingLeft = percent + '%';
}

function mouse_out_of_region(e) {
	// reset the hover state, returning the border to normal
	e.feature.setProperty('state', 'normal');
}

function init_chart(selected_variable) {
	var data = {};
	$.ajax({
  		url: '/static/data/district-data.json',
  		async: false,
  		dataType: 'json',
  		success: function (json) {
    		data = json;
  		}
	});
	var barchart_values = new Array(chart_intervals).fill(0)
	var barchart_labels = [];

	barchart_data = {
			labels: barchart_labels,
			datasets: [{
				label: labels[selected_variable],
				backgroundColor: 'rgb(255, 99, 132)',
				borderColor: 'rgb(255, 99, 132)',
				data: barchart_values,
			}]
		};

	var ctx = document.getElementById('bar_chart').getContext('2d');
	
	window.bar_chart = new Chart(ctx, {
		// The type of chart we want to create
		type: 'bar',

		// The data for our dataset
		data: barchart_data,

		// Configuration options go here
		options: {}
	});
}

function load_chart(selected_variable) {
	var data = {};
	$.ajax({
  		url: '/static/data/district-data.json',
  		async: false,
  		dataType: 'json',
  		success: function (json) {
    		data = json;
  		}
	});
	var barchart_values = new Array(chart_intervals).fill(0)
	var barchart_labels = [];
	for (var i = 0; i < barchart_values.length; i++) {
		var interval = Math.floor(
			((i + 1) * ((district_max - district_min) / chart_intervals)) + district_min
		);
		barchart_labels[i] = interval.toString();
	}
	geounits_layer.forEach(function(feature){
		var geoid = feature.getProperty('GEOID');
		var data_value = parseInt(data[geoid.toString()][selected_variable]);
		var interval = Math.floor(
			(chart_intervals - 1) *
			((data_value - district_min) /
			(district_max - district_min))
		);
		barchart_values[interval] = barchart_values[interval] + 1;
	});
	console.log(barchart_values);
	console.log(barchart_labels);
	barchart_data.labels = barchart_labels;
	barchart_data.datasets = [{
				label: labels[selected_variable],
				backgroundColor: 'rgb(255, 99, 132)',
				borderColor: 'rgb(255, 99, 132)',
				data: barchart_values,
			}];
	window.bar_chart.update();
}
