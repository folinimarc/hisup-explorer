'use strict';


/* ------
Leaflet
-------*/
var mapConf = {
  domElementId: 'map',
  initViewCenterlatLng: [36.1551787, -86.7967738],
  zoomLevel: 17
}
var mapWrapper = new LeafletWrapper(mapConf);

/* ------
Datatables
-------*/
var tableConf = {
  domElementId: 'table',
  tableConf: {
    scrollX: true,
    language: {
      emptyTable: "No footprint data"
    },
    ajax: {
      url: 'api/footprints/?page=0', // Get only first page
      dataSrc: 'results',
    },
    rowId: function(row) {
      return `id_${row.id}`;
    },
    order: [[ 2, "desc" ]], // sort by created date
    columns: [
      { data: 'id', title: 'id' },
      { data: 'status', title: 'status' },
      { data: 'created', title: 'timestamp', render: (d) => { return d.split('.')[0].replaceAll(':', '').replaceAll('-', '').replaceAll('T','-') }},
      { data: 'latitude', title: 'lat' , render: (d) => { return Math.round(d * 10000) / 10000 }},
      { data: 'longitude', title: 'lon' , render: (d) => { return Math.round(d * 10000) / 10000 }},
      { data: 'zoom_level', title: 'zoom' },
      { data: 'bbox_analysis_geojson', title: 'bbox_analysis_geojson', visible: false, searchable: false },
      { data: 'footprints_geojson', title: 'footprints_geojson', visible: false, searchable: false },
    ],
  }
}
var tableWrapper = new DatatablesWrapper(tableConf)


/* ------
Interactions
-------*/

// Handle table row click
tableWrapper.table.on('click', 'tr', (e) => {
  // Highlight selected row
  let rowId = e.currentTarget.id;
  // Return early if row has no id and thus is not of interest to us
  if (!rowId) { return }
  tableWrapper.setRowHighlight(rowId);
  let rowData = tableWrapper.table.row(`#${rowId}`).data();
  // Pan to center
  mapWrapper.map.setView([rowData.latitude, rowData.longitude], rowData.zoom_level);
  // Visualize footprints on map
  if (rowData && rowData.bbox_analysis_geojson) {
    mapWrapper.visualizeFootprints(rowData.bbox_analysis_geojson, rowData.footprints_geojson)
  }
});

/* ------
Trigger footprint analysis
-------*/
function scheduleFootprintExtraction(lat, lng, zoom) {
  // Deactivate button for 2 seconds and change text - then change back
  let btn = document.getElementById('btn-analyse');
  btn.disabled = true;
  btn.textContent = 'Scheduling...';
  setTimeout(() => {
    btn.disabled = false;
    btn.textContent = 'Extract footprints';
  }, 3000)

  // Post request
  $.ajax({
    method:'POST',
    url:'api/footprints/',
    data:{
      latitude: lat,
      longitude: lng,
      zoom_level: zoom,
      csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
    },
    success: function(data) {
      // Add new data temporarily to table to give visual feedback
      tableWrapper.table.row.add(data);
      tableWrapper.table.draw();
      // Highlight new row
      tableWrapper.setRowHighlight(`id_${data.id}`);
    }
  });
}

document.getElementById('btn-analyse').addEventListener('click', (e) => {
  // Get current map center and zoom level and send POST request.
  let latLngZoom = mapWrapper.getCenterlatLngZoom();
  scheduleFootprintExtraction(latLngZoom.latitude, latLngZoom.longitude, latLngZoom.zoom);
});

/* ------
Request USEPA facilities
-------*/

document.getElementById('btn-usepa').addEventListener('click', (e) => {
  let btn = e.currentTarget;
  // Deactivate button for 2 seconds and change text - then change back
  btn.disabled = true;
  btn.textContent = 'Requesting...';
  // Update button content
  setTimeout(() => {
    btn.disabled = false;
    btn.textContent = 'Nearby usepa facilities';
  }, 5000)

  // Get current map center and zoom level and send POST request.
  // On success wait another
  let latLngZoom = mapWrapper.getCenterlatLngZoom();
  let qLat = latLngZoom['latitude'];
  let qLong = latLngZoom['longitude'];
  let sRadius = 1;

  //For this REST service, it is important to specify cache: true because otherwise jQuery will append an erroneous parameter to the query.
  jQuery.ajaxSetup({
    cache: true
  });
  //specify base endpoint - note callback
  var usepaApi = "http://ofmpub.epa.gov/enviro/frs_rest_services.get_facilities?callback=?";
  //pass in parameters
  $.getJSON(usepaApi, {
      output: "jsonp",
      latitude83: qLat,
      longitude83: qLong,
      search_radius: sRadius,
  })
  .done(function (data) {
    // Visualize facitilies
    let facilities = data['Results']['FRSFacility'];
    if (facilities && facilities.length>0) {
      mapWrapper.visualizeUsepaFacilities(facilities);
    }
  });
});
