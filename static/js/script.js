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

// TODO: move the variables into a separate js file, e.g., util.js
// maybe even have separate files for the charts and the maps
var categories;
var category;
var category_type;
var census_year = '2015';
var chartColors = {
	red: 'rgb(255, 99, 132)',
	green: 'rgb(75, 192, 192)',
	blue: 'rgb(54, 162, 235)',
	orange: 'rgb(255, 159, 64)',
	purple: 'rgb(153, 102, 255)',
	yellow: 'rgb(255, 205, 86)',
	grey: 'rgb(201, 203, 207)'
};
var chart_intervals = 100;
var color = Chart.helpers.color;
var colorNames = Object.keys(chartColors);
var data = {};
var distribution_chart_data;
var distribution_geounits;
var district_chart_data;
var district_layer;
var district_min = Number.MAX_VALUE; 
var district_max = -Number.MAX_VALUE;
var debug_is_on = false;
var fields;
var field_graph_data;
var geounit_type;
var geounit_chart_data;
var geounit_files = {
	//TODO read these from a settings file
	'tract': '/static/geojson/TX07-tracts.geojson',
	'bg': '/static/geojson/TX07-blockgroups.geojson',
	'precinct': '/static/geojson/tx7-precincts.geojson'
};
var geounit_labels = {
	'tract': 'Tract',
	'bg': 'Block Group',
	'precinct': 'Precinct'
};
var geounits_layer;
var hover_geounits = [];
var labels;
var map;
var property_name = 'GEOID';
var slideout;
var years;

/* loadGoogleMapsAPI() enables Goolge Maps API using Google API Key
 * returns nothing
 */ 
function loadGoogleMapsAPI() {
    var script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = 'https://maps.googleapis.com/maps/api/js?v=3' +
        '&key=' + GOOGLE_API_KEY + 
		'&callback=init';
	script.setAttribute('defer','');
	script.setAttribute('async','');
    document.body.appendChild(script);
}


// on load enable Google Maps API and kick off init()
window.onload = loadGoogleMapsAPI;


/**
 * init() initializes elements in index.html
 * e.g., map, charts, slideout menu, etc.
 * returns nothing
 **/
function init() {
	// TODO: get settings from JSON file
	
	// enable slideout functionality	
	slideout = new Slideout({
		'panel': document.getElementById('panel'),
		'menu': document.getElementById('menu'),
		'padding': 256,
		'tolerance': 70
	});
	
	var fixed = document.querySelector('.fixed-header');

	slideout.on('translate', function(translated) {
	  fixed.style.transform = 'translateX(' + translated + 'px)';
	});

	slideout.on('beforeopen', function () {
	  fixed.style.transition = 'transform 300ms ease';
	  fixed.style.transform = 'translateX(256px)';
	});

	slideout.on('beforeclose', function () {
	  fixed.style.transition = 'transform 300ms ease';
	  fixed.style.transform = 'translateX(0px)';
	});

	slideout.on('open', function () {
	  fixed.style.transition = '';
	});

	slideout.on('close', function () {
	  fixed.style.transition = '';
	});

	// enable hamburger
	var hamburger = document.querySelector(".hamburger");
   	hamburger.addEventListener('click', function() {
		slideout.toggle();
		hamburger.classList.toggle("is-active");
   	});
	
	// set default settings for window.onLoad
	category = 'Age';
	category_type = 'Census';
	geounit_type = 'bg';
	
	$.ajax({
  		url: '/static/data/district.json',
  		async: false,
  		dataType: 'json',
  		success: function (json) {
    		years = json['years'].sort();
  		}
	});
	
	$.ajax({
  		url: '/static/data/district-data.json',
  		async: false,
  		dataType: 'json',
  		success: function (json) {
    		data = json;
  		}
	});	
	
	// TODO read this from the centroid of the district identified in statbuilder.py
	var uluru = {lat: 29.8, lng: -95.6};
    map = new google.maps.Map(document.getElementById('map'), {
    	zoom: 11,
    	center: uluru,
    	fullscreenControl: true
    });

	// Create data layers for the Congressional District and
	// the geounits, e.g., voting precinct, tract, or block group
	district_layer = new google.maps.Data({map: map});
	district_layer.setStyle({
		clickable: false,
		zIndex: 3,
		fillOpacity: 0.0,
		strokeColor: '#43a2ca',
		strokeWeight: 3
	});

	geounits_layer = new google.maps.Data({map: map});
	geounits_layer.setStyle(style_feature);
	geounits_layer.addListener('mouseover', mouse_in_to_region);
    geounits_layer.addListener('mouseout', mouse_out_of_region);
	geounits_layer.addListener('click', click_region);

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
	
	fields = categories[category][category_type]['fields'];
	labels = categories[category][category_type]['labels'];

	set_select_box();
	var select_box = document.getElementById('fields');
	var selected_variable = select_box.options[select_box.selectedIndex].value
	google.maps.event.addDomListener(select_box, 'change', function() {
		clear_map_data();
        load_map_data(select_box.options[select_box.selectedIndex].value);
        load_distribution_chart(select_box.options[select_box.selectedIndex].value);
		load_district_chart();
		load_top_geounits(select_box.options[select_box.selectedIndex].value);
		document.getElementById('geounit_chart').style.display = 'none';
    });

	load_maps();
	init_distribution_chart(selected_variable);
	init_district_chart();
	init_geounit_chart();
}


/**
 * load_maps() waits for Google Maps API to finish loading
 * then it sets the position of the map controls
 * loads the geounits map layer and the district boundary map layer
 * returns nothing
 * 
 * TODO: maybe rename this to be more descriptive of its functionality
 *
 **/
function load_maps() {
	google.maps.event.addListenerOnce(map, 'idle', function() {
		var controls = document.getElementById('controls');
    	map.controls[google.maps.ControlPosition.TOP_CENTER].push(controls);
		controls.style.opacity = 1;
	});

	// TODO: read this from a variable
	district_layer.loadGeoJson("/static/geojson/district-TX07.geojson");
	
	geounits_layer.loadGeoJson(
		geounit_files[geounit_type],
		{ idPropertyName: property_name },
		function (features) {
			google.maps.event.trigger(document.getElementById('fields'), 'change');
		}
	);
}


/**
 * load_category() 
 *
 * returns false
 *
 * TODO change from static embedded onclicks to DOM populated onclicks
 *
 **/
function set_nav_behavior(){
	var age_census = document.getElementById("age-census");
	age_census.onclick = load_category('Age', 'Census');
}


/**
 * set_select_box() clears the drop down menu in the map and
 * sets it according to the labels and fields
 * returns nothing
 *
 **/
function set_select_box() {
	var select_box = document.getElementById('fields');
	
	// clear any old options
	while (select_box.firstChild) {
    	select_box.removeChild(select_box.firstChild);
	}
	// set the drop down menu 
	for (var i = 0; i < fields.length; i++) {
		$('<option></option>')
			.text(labels[fields[i]])
			.attr('value', fields[i])
			.appendTo(select_box);
	}
}

/**
 * load_category() loads the map and charts for a given category, c
 * e.g., Age:Census
 * 
 * TODO elimate category type or only show Census data by default a
 * 
 * returns false
 *
 **/
function load_category(c, c_type) {
	category = c;
	category_type = c_type;
	fields = categories[category][category_type]['fields'];
	labels = categories[category][category_type]['labels'];
	
	if( property_name === 'PRECINCT' ) {
		// remove the median income field if it's precinct
		if( category === 'Income' && category_type === 'Census' ){
			var index = fields.indexOf('median_income');
			if (index > -1) {
    			fields.splice(index, 1);
			}
		}
	}

	set_select_box();
	google.maps.event.trigger(document.getElementById('fields'), 'change');

	return false;
}

/**
 * load_geounits() loads the map and charts for a given, geounit
 * e.g., tract, block group, or precinct
 *
 * returns false
 **/
function load_geounit(geounit) {
	fields = categories[category][category_type]['fields'];
	labels = categories[category][category_type]['labels'];

	geounit_type = geounit;
	property_name = 'GEOID';
	if( geounit === 'precinct' ) {
		property_name = 'PRECINCT';
		
		// remove the median income field if it's precinct
		if( category === 'Income' && category_type === 'Census' ){
			var index = fields.indexOf('median_income');
			if (index > -1) {
    			fields.splice(index, 1);
			}
		}
	}

	// clear geounits_layer
	geounits_layer.forEach(function(feature){
		geounits_layer.remove(feature);
	});
	
	// clear the geounits which are highlighted from the previous distribution chart
	hover_geounits = [];
	
	set_select_box();
	
	geounits_layer.loadGeoJson(
		geounit_files[geounit_type],
		{ idPropertyName: property_name },
		function (features) {
			google.maps.event.trigger(document.getElementById('fields'), 'change');
		}
	);

	return false;
}


/**
 * load_map_data(selected_variable) combines the census data (TODO or election results)
 *
 * returns nothing
 *
 **/
function load_map_data(selected_variable) {
	if(debug_is_on){	
		console.log('Loading map data');
	}
	
	geounits_layer.forEach(function(feature){
		var geoid = feature.getProperty(property_name);
		if(debug_is_on){	
			console.log('GEOID:  ' + geoid);
			console.log('Geounit Type:  ' + geounit_type);
			console.log(data[census_year][geounit_type.toString()]);
		}
		var data_value = parseInt(data[census_year][geounit_type.toString()][geoid.toString()][selected_variable]);
		
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


/**
 * clear_map_data() removes census data from each shape on the map and resets the UI. 
 * 
 * returns nothing
 *
 **/
function clear_map_data() {
	district_min = Number.MAX_VALUE;
	district_max = -Number.MAX_VALUE;
	geounits_layer.forEach(function(row) {
	  row.setProperty('data_value', undefined);
	});
	document.getElementById('data-box').style.display = 'none';
	document.getElementById('data-caret').style.display = 'none';
}


/**
 * style_feature(feature) set the style of each geounit
 *
 * returns nothing
 * 
 **/
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
	// default values
	var outlineWeight = 0.5, 
		zIndex = 1,
		stroke_color = '#fff';
	if (feature.getProperty('map_state') === 'hover') {
		outlineWeight = 3;
		zIndex = 2;
	}
	if (feature.getProperty('chart_state') === 'hover') {
		outlineWeight = 3;
		zIndex = 2;
		stroke_color = '#000';
	}
	
	return {
	  	strokeWeight: outlineWeight,
	  	strokeColor: stroke_color,
	  	zIndex: zIndex,
	  	fillColor: 'hsl(' + color[0] + ',' + color[1] + '%,' + color[2] + '%)',
	  	fillOpacity: 0.75,
		visible: show_row
	};
}


/**
 * mouse_in_to_region(e) update the data box with info about the geounit
 * when the mouse hovers in the region
 * 
 * returns nothing
 * 
 **/
function mouse_in_to_region(e) {
	// set the hover state so the setStyle function can change the border
	e.feature.setProperty('map_state', 'hover');
	var geoid = e.feature.getProperty(property_name);
	var data_value = e.feature.getProperty('data_value');
	var data_label = e.feature.getProperty('label');
	var percent = (data_value - district_min) / (district_max - district_min) * 100;
	if(debug_is_on) {
 		console.log('GEOID: ' + geoid );
 		console.log(data_label + ': ' + data_value);
	}
	document.getElementById('data-label').textContent = data_label;
    document.getElementById('data-value').textContent = number_with_commas(data_value.toString());
    document.getElementById('data-box').style.display = 'block';
    document.getElementById('data-caret').style.display = 'block';
    document.getElementById('data-caret').style.paddingLeft = percent + '%';
}


/**
 * mouse_out_of_region(e) resets the hover state for a geounit
 *
 * returns nothing
 * 
 **/
function mouse_out_of_region(e) {
	// reset the hover state, returning the border to normal
	e.feature.setProperty('map_state', 'normal');
}


/**
 * click_region(e) loads the chart for a region when it is clicked
 * 
 * returns nothing
 * 
 **/
function click_region(e) {
	var geoid = e.feature.getProperty(property_name);

	load_geounit_chart(geoid);
}


/**
 * init_distribution_chart(selected_variable) 
 *
 * returns nothing
 * 
 **/
function init_distribution_chart(selected_variable) {
	var barchart_values = new Array(chart_intervals).fill(0)
	var barchart_labels = [];

	distribution_chart_data = {
			labels: barchart_labels,
			datasets: [{
				label: labels[selected_variable],
				backgroundColor: 'rgb(255, 99, 132)',
				borderColor: 'rgb(255, 99, 132)',
				data: barchart_values,
			}]
		};

	var title = "Districtwide Distribution for " + labels[selected_variable];
	
	var ctx = document.getElementById('distribution_chart').getContext('2d');
	window.bar_chart = new Chart(ctx, {
		// The type of chart we want to create
		type: 'bar',

		// The data for our dataset
		data: distribution_chart_data,

		// Configuration options go here
		options: {
			maintainAspectRatio: false,
			onHover: mouse_on_distrib_chart,
			title: {
				display: true,
				text: title,
				fontsize: 18
			}
		}
	});
}


/**
 * load_distribution_chart(selected_variable) 
 * 
 * returns
 * 
 **/
function load_distribution_chart(selected_variable) {
	if(debug_is_on){ 
		console.log('Loading distribution chart'); 
	}
	
	var barchart_values = new Array(chart_intervals).fill(0)
	var barchart_labels = [];
	var title = "Districtwide Distribution for " + labels[selected_variable];
	
	for (var i = 0; i < barchart_values.length; i++) {
		var interval = Math.floor(
			((i + 1) * ((district_max - district_min) / chart_intervals)) + district_min
		);
		barchart_labels[i] = interval.toString();
	}
	distribution_geounits = new Array(chart_intervals).fill([])
	geounits_layer.forEach(function(feature){
		var geoid = feature.getProperty(property_name);
		var data_value = parseInt(data[census_year][geounit_type][geoid.toString()][selected_variable]);
		var interval = Math.floor(
			(chart_intervals - 1) *
			((data_value - district_min) /
			(district_max - district_min))
		);
		barchart_values[interval] = barchart_values[interval] + 1;
		var t = distribution_geounits[interval].concat();
		t.push(geoid);
		distribution_geounits[interval] = t.concat();
		
	});
	distribution_chart_data.labels = barchart_labels;
	distribution_chart_data.datasets = [{
				label: labels[selected_variable],
				backgroundColor: 'rgb(255, 99, 132)',
				borderColor: 'rgb(255, 99, 132)',
				data: barchart_values,
			}];

	// clear any highlighting
	for(i=0; i < hover_geounits.length; i++) {
		geounits_layer.getFeatureById(hover_geounits[i]).setProperty('chart_state', 'normal');
	}

	window.bar_chart.options.title.text = title;
	window.bar_chart.update();
}


/**
 * mouse_on_distrib_chart(e, a) 
 * returns
 * 
 **/
function mouse_on_distrib_chart(e, a) {
	if(a.length > 0){
		// clear old data
		for(i=0; i < hover_geounits.length; i++) {
			geounits_layer.getFeatureById(hover_geounits[i]).setProperty('chart_state', 'normal');
		}

		var index = a[0]._index;
		hover_geounits = distribution_geounits[index].concat();
		for(i=0; i < hover_geounits.length; i++) {
			geounits_layer.getFeatureById(hover_geounits[i]).setProperty('chart_state', 'hover');
		}
	}
}


/**
 * init_district_chart() 
 * returns
 * 
 **/
function init_district_chart() {
	var barchart_values = [];
	var barchart_labels = [];

	for(var i = 0; i < fields.length; i++) {
		barchart_labels[i] = labels[fields[i]];
	}
	var index = barchart_labels.indexOf(labels['median_income']);
	if (index > -1) {
    	barchart_labels.splice(index, 1);
	}

	district_chart_data = {
			labels: barchart_labels,
			datasets: []
		};
	
	for(var j = 0; j < years.length; j++) {
		barchart_values = [];
		for(var i = 0; i < fields.length; i++) {
			barchart_values[i] = data[years[j]]['district'][fields[i]];
		}
		var colorName = colorNames[district_chart_data.datasets.length % colorNames.length];
		var dsColor = chartColors[colorName];
		district_chart_data.datasets.push({
				label: years[j],
				backgroundColor: color(dsColor).alpha(0.5).rgbString(),
				borderColor: dsColor,
				borderWidth: 1,
				data: barchart_values,
			});
	}
	
	var ctx = document.getElementById('district_chart').getContext('2d');
	
	var title = category + " for District";
	window.district_chart = new Chart(ctx, {
		// The type of chart we want to create
		type: 'bar',

		// The data for our dataset
		data: district_chart_data,

		// Configuration options go here
		options: {
			title: {
				display: true,
				text: title,
				fontsize: 18
			}
		}
	});
}


/**
 * load_district_chart() 
 * returns
 * 
 **/
function load_district_chart() {
	if(debug_is_on) {	
		console.log('Loading district chart');
	}

	var barchart_values = [];
	var barchart_labels = [];
	
	district_chart_data.datasets.splice(0, district_chart_data.datasets.length);

	for(var j = 0; j < years.length; j++) {
		barchart_values = [];
		for(var i = 0; i < fields.length; i++) {
			barchart_values[i] = data[years[j]]['district'][fields[i]];
		}
		var colorName = colorNames[district_chart_data.datasets.length % colorNames.length];
		var dsColor = chartColors[colorName];
		district_chart_data.datasets.push({
				label: years[j],
				backgroundColor: color(dsColor).alpha(0.5).rgbString(),
				borderColor: dsColor,
				borderWidth: 1,
				data: barchart_values,
			});
	}
	for(var i = 0; i < fields.length; i++) {
		barchart_labels[i] = labels[fields[i]];
	}
	var index = barchart_labels.indexOf(labels['median_income']);
	if (index > -1) {
    	barchart_labels.splice(index, 1);
	}

	district_chart_data.labels = barchart_labels;
	
	var title = category + " for District";
	window.district_chart.options.title.text = title;
	
	window.district_chart.update();
}


/**
 * init_geounit_chart() 
 * 
 * returns
 * 
 **/
function init_geounit_chart() {
	var barchart_values = [];
	var barchart_labels = [];
	
	for(var i = 0; i < fields.length; i++) {
		barchart_labels[i] = labels[fields[i]];
	}
	geounit_chart_data = {
			labels: barchart_labels,
			datasets: [{
				label: '',
				backgroundColor: 'rgb(255, 99, 132)',
				borderColor: 'rgb(255, 99, 132)',
				data: barchart_values,
			}]
		};

	var title = '';
	var ctx = document.getElementById('geounit_chart').getContext('2d');
	
	window.geounit_chart = new Chart(ctx, {
		// The type of chart we want to create
		type: 'bar',

		// The data for our dataset
		data: geounit_chart_data,

		// Configuration options go here
		options: {
			title: {
				display: true,
				text: title,
				fontsize: 18
			}
		}
	});
	document.getElementById('geounit_chart').style.display = 'none';
}


/**
 * load_geounit_chart(geoid)
 * 
 * returns
 * 
 **/
function load_geounit_chart(geoid) {
	if(debug_is_on) {	
		console.log('Loading geounit chart');
	}

	var barchart_values = [];
	var barchart_labels = [];
	var title = category + " for " + geounit_labels[geounit_type] + " " + geoid.toString();

	geounit_chart_data.datasets.splice(0, geounit_chart_data.datasets.length);

	for(var j = 0; j < years.length; j++) {
		barchart_values = [];
		for(var i = 0; i < fields.length; i++) {
			barchart_values[i] = data[years[j]][geounit_type.toString()][geoid.toString()][fields[i]];
		}
		var colorName = colorNames[geounit_chart_data.datasets.length % colorNames.length];
		var dsColor = chartColors[colorName];
		geounit_chart_data.datasets.push({
				label: years[j],
				backgroundColor: color(dsColor).alpha(0.5).rgbString(),
				borderColor: dsColor,
				borderWidth: 1,
				data: barchart_values,
			});
	}
	for(var i = 0; i < fields.length; i++) {
		barchart_labels[i] = labels[fields[i]];
	}

	geounit_chart_data.labels = barchart_labels;
	
	window.geounit_chart.options.title.text = title;

	window.geounit_chart.update();
	document.getElementById('geounit_chart').style.display = 'block';
}


/**
 * load_top_geounits(selected_variable) 
 * 
 * returns nothing
 * 
 **/
function load_top_geounits(selected_variable) {
	if(debug_is_on){ 
		console.log('Loading top precincts table'); 
	}
	
	var geounits = [];
	var total = 0;
	geounits_layer.forEach(function(feature){
		var geoid = feature.getProperty(property_name);
		var data_value = parseInt(data[census_year][geounit_type][geoid.toString()][selected_variable]);
		
		total = parseInt(data_value) + total;
		geounits.push([geoid, data_value]);
	});
	geounits.sort(function(a, b) {
		return b[1] - a[1];
	});

	var top_third = parseInt(total / 3);
	total = 0;
	for( var i = 0; total < top_third; i++) {
		var geoid = geounits[i][0];
		var data_value = geounits[i][1];

		total = data_value + total;
		
		console.log(geoid.toString() + ": " + data_value.toString());
	}
}


/**
 * number_with_commas(x) inserts commas in a number
 * 
 * returns a string with commas
 * 
 **/
function number_with_commas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}
