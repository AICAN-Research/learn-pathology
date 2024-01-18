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

function focusAnnotation(annotation) {
    /*
    TODO
      - If you click an annotation that's much larger than the current zoom
        area, the annotation will cover all/most of the viewer. If the
        annotation is larger than the area (or at least covers all of it), we
        should change the zoom level when focusing on the annotation.
      - For teachers, the annotation also becomes active, meaning that any
        click and drag will drag the annotation, not pan and zoom.
     */

    // Pan to put annotation in center of viewer
    centerAnnotation(annotation);

    // Ensure full extent of annotation is within the viewer area
    zoomToShowFullAnnotation(annotation);
}

function centerAnnotation(annotation) {
    /*
    Centers the (centre of the) annotation in the centre of the OSD viewer
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
                center = getCircleAndEllipseCenter(annotation);
            }
            break;
        default:
            console.error("Invalid selector type");
            return null;
    }

    let osdCoordinates = viewer.viewport.imageToViewportCoordinates(center.x, center.y);
    viewer.viewport.panTo(osdCoordinates, true);

}

function zoomToShowFullAnnotation(annotation) {
    /*
    Zoom to zoom level that displays the whole annotation extent (with some
    space on the sides)
     */

    let [extentX, extentY] = getAnnotationExtent(annotation);
    let width = extentX[1] - extentX[0];
    let height = extentY[1] - extentY[0];
    let x = viewer.viewport.imageToViewportCoordinates(width);
    let y = viewer.viewport.imageToViewportCoordinates(height);
    console.log(x, y);

    let maxZoomLevelX = 10.;
    let maxZoomLevelY = 10.;
    let zoomTo = Math.min(maxZoomLevelX, maxZoomLevelY);
    console.log('Zooming to', zoomTo);
    viewer.viewport.zoomTo(zoomTo);
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

function getCircleAndEllipseCenter(annotation) {
    let selector = annotation.target.selector.value;
    let cx = parseFloat(selector.split('cx="')[1].split('"')[0]);
    let cy = parseFloat(selector.split('cy="')[1].split('"')[0]);
    return {x: cx, y: cy};
}

function getAnnotationExtent(annotation) {
    /* Find extent in x and y directions */

    const selectorType = annotation.target.selector.type;
    let extentX, extentY;

    switch (selectorType) {
        case 'FragmentSelector':
            let valueString = annotation.target.selector.value;
            valueString = valueString.replace('xywh=pixel:', '');
            let [x, y, w, h] = valueString.split(',').map(value => parseFloat(value));

            if ((w === 0) && (h === 0)) {
                // Point
                // TODO: Special case for point
                extentX = [0, 0]    // extent X
                extentY = [0, 0]    // extent Y
            } else {
                // Rectangle/box
                extentX = [x, x + w];
                extentY = [y, y + h];
            }
            break;
        case 'SvgSelector':
            const svgValue = annotation.target.selector.value;
            if (svgValue.includes('polygon')) {
                [extentX, extentY] = getPolygonExtent(annotation);
            } else if (svgValue.includes('circle') || svgValue.includes('ellipse')) {
                [extentX, extentY] = getCircleAndEllipseExtent(annotation);
            }
            break;
        default:
            console.error("Invalid selector type");
            return null;
    }

    // console.log(extentX, extentY);
    return [extentX, extentY];

}

function getCircleAndEllipseExtent(annotation) {
    let valueStr = annotation.target.selector.value;
    let cx = parseFloat(valueStr.split('cx="')[1].split('"')[0]);
    let cy = parseFloat(valueStr.split('cy="')[1].split('"')[0]);
    let rx = parseFloat(valueStr.split('rx="')[1].split('"')[0]);
    let ry = parseFloat(valueStr.split('ry="')[1].split('"')[0]);
    return [[cx - rx/2, cx + rx/2],
            [cy - ry/2, cy + ry/2],
            ];
}

function getPolygonExtent(annotation) {
    let valueStr = annotation.target.selector.value;
    let polygonPts = valueStr.split('"')[1] // remove <svg> and <polygon...> designators
        .split(' ')                         // split string into points
        .map(pointStr => {                  // convert point strings 'x.xx,y.yy' to [x.xx, y.yy]
            return pointStr.split(",").map(coord => parseFloat(coord));
        });

    // Polygon must have at least one point
    if (polygonPts.length <= 0) {
        alert('Error in polygon, the shape has no points');
    }

    // Find smallest and largest X and Y coordinates
    let minX = polygonPts[0][0], maxX = polygonPts[0][0],
        minY = polygonPts[0][0], maxY = polygonPts[0][0];
    for (let i = 0; i < polygonPts.length; i++) {
        let [x, y] = polygonPts[i]
        if (x <= minX) minX = x;
        if (x >= maxX) maxX = x;
        if (y <= minY) minY = y;
        if (y >= maxY) maxY = y;
    }
    return [[minX, maxX],
            [minY, maxY]];
}
