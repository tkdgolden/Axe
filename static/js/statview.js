$(document).ready(function () {
    $('#playerstats').DataTable({
        order: [[2, 'desc']]
    });

    $('.clickable-matches').DataTable({
        order: [[0, 'desc']]
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

    $("#selected_seasonstats").on("click", "tr[role=\"button\"]", function () {
        window.location = $(this).data("href");
    });

    $(".clickable-players").on("click", "tr[role=\"button\"]", function () {
        window.location = $(this).data("href");
    });

    $("#selected_matches").on("click", "tr[role=\"button\"]", function () {
        window.location = $(this).data("href");
    });

    $(".clickable-matches").on("click", "tr[role=\"button\"]", function () {
        window.location = $(this).data("href");
    });

    $('.display').DataTable();

    // Hide a search bar at the top of the table I don't like.
    $('.dataTables_length').css("display", "none");
    $('.dataTables_filter').css("display", "none");

    $('#hatchet').css("display", "block");

    $('#season_view').css("display", "block");

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

    $(".view").change(function() {
        const quarter = $("#lap option:selected").data("quarter");
        const lap = $("#lap option:selected").data("lap");
        const lap_id = $("#lap option:selected").data("id");
        sessionStorage.setItem("season_lap", lap_id);        const season = new URLSearchParams(window.location.search).get('season');
        window.location = `season_stats_view?season=${season}&quarter=${quarter}&lap=${lap}`;
    });

    $(`#lap option[value=${sessionStorage.getItem("season_lap")}]`).attr('selected', 'true');
});

