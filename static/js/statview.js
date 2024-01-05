$(document).ready(function () {
    $('#player_stats').DataTable({
        order: [[3, 'desc']]
    });

    $("#playerstats").on("click", "tr[role=\"button\"]", function () {
        window.location = $(this).data("href");
    });

    $("#seasonstats").on("click", "tr[role=\"button\"]", function () {
        window.location = $(this).data("href");
    });


    $("#matches").on("click", "tr[role=\"button\"]", function () {
        window.location = $(this).data("href");
    });

    $('.display').DataTable();

    // Hide a search bar at the top of the table I don't like.
    $('.dataTables_length').css("display", "none");
    $('.dataTables_filter').css("display", "none");

    $('#hatchet').css("display", "block");

    $('.tablinks').on("click", function(evt) {
        var discipline = evt.target.dataset.discipline;
        viewTable(evt, discipline);
    });

    function viewTable(evt, discipline) {
        $('.tabcontent').css("display", "none");
        
        $('.tablinks').removeClass("active");

        $(`#${discipline}`).css("display", "block");
        evt.target.classList.add("active");
    }
});

