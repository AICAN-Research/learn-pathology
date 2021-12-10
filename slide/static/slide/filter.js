$(document).ready(function() {
    if($('.filter').length) { // check if exists
        $('.filter').select2({});
        $('.filter').change(function (event) {
            this.form.submit();
        });
    }
});