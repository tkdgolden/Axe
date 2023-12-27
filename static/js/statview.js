$(document).ready(function () {
    $('#player_stats').DataTable({
        order: [[3, 'desc']]
    });

    $(function () {
        $("#playerstats").on("click", "tr[role=\"button\"]", function () {
            window.location = $(this).data("href");
        });
    });

    $(function () {
        $("#seasonstats").on("click", "tr[role=\"button\"]", function () {
            window.location = $(this).data("href");
        });
    });

    $(function () {
        $("#matches").on("click", "tr[role=\"button\"]", function () {
            window.location = $(this).data("href");
        });
    });

    $('.display').DataTable();

    $('#playerstats_length').css("visibility", "hidden");
    $('#playerstats_filter').css("visibility", "hidden");
    $('#matches_length').css("visibility", "hidden");
    $('#matches_filter').css("visibility", "hidden");
    $('#seasonstats_length').css("visibility", "hidden");
    $('#seasonstats_filter').css("visibility", "hidden");
});

