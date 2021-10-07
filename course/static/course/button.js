$(document).ready(function() {

    $('#add_button').click(function () {

        var model_name = $(this).attr('model_name')
        var instance_id = $(this).attr('instance_id')
        console.log("Add button for " + model_name + " with id " + instance_id + " was clicked")

        $.ajax({
            url: "/course/add_item",
            type: "GET",
            data: {
                'course_id': $(this).attr('course_id'),
                'model_name': model_name,
                'instance_id': instance_id,
            },
            success: function (xml) {
                location.reload()  // Using .reload() method
            },
            error: function(result) {
                alert('Error occurred when adding item to course');
            }
        });
    });

    $('#remove_button').click(function () {

        var model_name = $(this).attr('model_name')
        var instance_id = $(this).attr('instance_id')
        console.log("Remove button for " + model_name + " with id " + instance_id + " was clicked")

        $.ajax({
            url: "/course/remove_item",
            type: "GET",
            data: {
                'course_id': $(this).attr('course_id'),
                'model_name': model_name,
                'instance_id': instance_id,
            },
            success: function (xml) {
                location.reload()  // Using .reload() method
            },
            error: function(result) {
                alert('Error occurred when removing item from course');
            }
        });

    });

})

