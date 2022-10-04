$(document).ready(function() {

    $('.add_tag_button').click(function(event) {
        /*$(this).attr("disabled", true); // disable buttons*/

        var slide_id = $(this).data('slide_id');
        var tag_id = $(this).data('tag_id');

        $.ajax({
            url: "/slide/add-tag",
            type: "GET",
            data: {
                'slide_id': slide_id,
                'tag_id': tag_id,
            },
            success: function (xml) {
                location.reload();  // Using .reload() method
            },
            error: function (result) {
                alert('Error occurred when adding tag to slide. Please notify the site developers');
            }
        });
        /*event.preventDefault();*/
    })

    $('.remove_tag_button').click(function (event) {

        var slide_id = $(this).data('slide_id');
        var tag_id = $(this).data('tag_id');

        $.ajax({
            url: "/slide/remove-tag",
            type: "GET",
            data: {
                'slide_id': slide_id,
                'tag_id': tag_id,
            },
            success: function (xml) {
                location.reload();  // Using .reload() method
            },
            error: function(result) {
                alert('Error occurred when removing tag from slide. Please notify the site developers');
            }
        });
        /*event.preventDefault();*/

    })

})

