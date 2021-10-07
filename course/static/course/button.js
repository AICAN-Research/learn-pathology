$(document).ready(function() {

    $('#add_button').click(function () {

        var slide_id = $(this).attr('slide_id')
        console.log("Add button for " + slide_id + " was clicked")

        $.ajax({
            url: "/course/add_slide",
            type: "GET",
            data: {
                'course_id': $(this).attr('course_id'),
                'slide_id': $(this).attr('slide_id'),
            },
            success: function (xml) {
                location.reload()  // Using .reload() method
            },
            error: function(result) {
                alert('Error occurred when adding slide to course');
            }
        });
    });

    $('#remove_button').click(function () {

        var slide_id = $(this).attr('slide_id')
        console.log("Remove button for " + slide_id + " was clicked")

        $.ajax({
            url: "/course/remove_slide",
            type: "GET",
            data: {
                'course_id': $(this).attr('course_id'),
                'slide_id': $(this).attr('slide_id'),
            },
            success: function (xml) {
                location.reload()  // Using .reload() method
            },
            error: function(result) {
                alert('Error occurred when removing slide from course');
            }
        });

    });

})

