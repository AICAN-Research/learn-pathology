/*
* This file contains helper functions for annotating and annotations that are
* created using Annotorious with OpenSeadragon, annotorious-toolbar and the
* annotorious-selector-pack.
*/


function toggleCardVisibility() {
    var x = document.getElementById("slideColumn");
    var canvas_viewer = document.getElementById('imageViewer');

    if (x.style.display === "none") {
        x.style.display = "block";
        canvas_viewer.style.width = '';
    } else {
        x.style.display = "none";
        canvas_viewer.style.width = '100%';
    }
}

/************************************************
Creating, saving, and deleting annotations
************************************************/

function createAnnotation(annotation, slide_id) {
    $.ajax({
        url: "/slide/annotation/create",
        type: "GET",
        data: {
            'slide_id': slide_id,
            'annotation': JSON.stringify(annotation),
        },
        success: function (xml) {
            // No actions required
        },
        error: function (result) {
            alert('Error occurred when attempting to store annotation.');
        }
    });
}

function updateAnnotation(annotation, previous, slide_id) {
    $.ajax({
        url: "/slide/annotation/update",
        type: "GET",
        data: {
            'slide_id': slide_id,
            'previous_annotation': JSON.stringify(previous),
            'annotation': JSON.stringify(annotation),
        },
        success: function (xml) {
            // No actions required
        },
        error: function (result) {
            alert('Error occurred when attempting to update annotation.');
        }
    });
}

function deleteAnnotation(annotation, slide_id) {
    $.ajax({
        url: "/slide/annotation/delete",
        type: "GET",
        data: {
            'slide_id': slide_id,
            'annotation': JSON.stringify(annotation),
        },
        success: function (xml) {
            // No actions required
        },
        error: function (result) {
            alert('Error occurred when attempting to delete annotation.');
        }
    });
}
