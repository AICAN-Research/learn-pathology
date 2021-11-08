$(document).ready(function() {

    $('.add_button').click(function(event) {

        $(this).attr("disabled", true); // disable buttons

        var course_id = $(this).data('course_id');
        var model_name = $(this).data('model_name');
        var instance_id = $(this).data('instance_id');
        console.log("Add button for " + model_name + " with id " + instance_id + " clicked");

        $.ajax({
            url: "/course/add_item",
            type: "GET",
            data: {
                'course_id': course_id,
                'model_name': model_name,
                'instance_id': instance_id,
            },
            success: function (xml) {
                location.reload();  // Using .reload() method
            },
            error: function (result) {
                alert('Error occurred when adding item to course');
            }
        });
        event.preventDefault();
    });

    $('.remove_button').click(function (event) {
        var course_id = $(this).data('course_id');
        var model_name = $(this).data('model_name');
        var instance_id = $(this).data('instance_id');
        console.log("Remove button for " + model_name + " with id " + instance_id + " was clicked");

        $.ajax({
            url: "/course/remove_item",
            type: "GET",
            data: {
                'course_id': course_id,
                'model_name': model_name,
                'instance_id': instance_id,
            },
            success: function (xml) {
                location.reload();  // Using .reload() method
            },
            error: function(result) {
                alert('Error occurred when removing item from course');
            }
        });
        event.preventDefault();

    });

})

