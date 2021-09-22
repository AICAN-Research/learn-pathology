$(document).ready(function() {
    $('.filter').select2({});
    $('.filter').change(function(event) {
        this.form.submit();
    });
});