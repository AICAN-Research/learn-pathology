/*
* This file contains helper functions for handling annotations that are created
* using Annotorious with OpenSeadragon, annotorious-toolbar and the
* annotorious-selector-pack.
*/


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


/************************************************
Annotation interaction, clicking, highlighting
************************************************/

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

function centerAnnotation(annotation) {
    /*

    TODO
      - If you click an annotation that's much larger than the current zoom
        area, the annotation will cover all/most of the viewer. If the
        annotation is larger than the area (or at least covers all of it), we
        should change the zoom level when focusing on the annotation.
      - For teachers, the annotation also becomes active, meaning that any
        click and drag will drag the annotation, not pan and zoom.
     */
    const selectorType = annotation.target.selector.type;
    let center;

    switch (selectorType) {
        case 'FragmentSelector':
            center = getRectCenter(annotation);
            break;
        case 'SvgSelector':
            const svgValue = annotation.target.selector.value;
            if (svgValue.includes('polygon')) {
                center = getPolygonCenter(annotation);
            } else if (svgValue.includes('circle') || svgValue.includes('ellipse')) {
                center = getCircleandEllipseCenter(annotation);
            }
            break;
        default:
            console.error("Invalid selector type");
            return null;
    }

    let osdCoordinates = viewer.viewport.imageToViewportCoordinates(center.x, center.y);
    viewer.viewport.panTo(osdCoordinates, true);

}

function getRectCenter(annotation) {
    let selector = annotation.target.selector.value;
    let valuesString = selector.split('pixel:')[1];
    let xywh = valuesString.split(',').map(value => parseFloat(value));
    let center_x = xywh[0] + xywh[2] / 2;
    let center_y = xywh[1] + xywh[3] / 2;
    return {x: center_x, y: center_y};
}

function getPolygonCenter(annotation) {
    const svgSelector = annotation.target.selector.value;
    const pointsMatch = svgSelector.match(/points="([^"]+)"/);
    if (!pointsMatch || pointsMatch.length < 2) {
        console.error("Invalid SVG polygon format");
        return null;
    }

    const pointsString = pointsMatch[1];
    const points = pointsString.split(" ").map(point => {
        const [x, y] = point.split(",").map(coord => parseFloat(coord));
        return {x, y};
    });

    // Calculate centroid
    const numPoints = points.length;
    const center_x = points.reduce((sum, point) => sum + point.x, 0) / numPoints;
    const center_y = points.reduce((sum, point) => sum + point.y, 0) / numPoints;
    return {x: center_x, y: center_y};
}

function getPointCenter(annotation) {
    let selector = annotation.target.selector.value;
    let valuesString = selector.split('pixel:')[1];
    let xywh = valuesString.split(',').map(value => parseFloat(value));
    let center_x = xywh[0];
    let center_y = xywh[1];
    return {x: center_x, y: center_y};
}

function getCircleandEllipseCenter(annotation) {
    let selector = annotation.target.selector.value;
    let cx = parseFloat(selector.split('cx="')[1].split('"')[0]);
    let cy = parseFloat(selector.split('cy="')[1].split('"')[0]);
    return {x: cx, y: cy};
}