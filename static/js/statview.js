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

    $('.dataTables_length').css("display", "none");
    $('.dataTables_filter').css("display", "none");

    $('.tablinks').on("click", function(evt) {
        discipline = evt.target.dataset.discipline;
        viewTable(evt, discipline);
    });

    function viewTable(evt, discipline) {
        console.log(discipline);
        var tabcontent, tablinks;

        tabcontent = $('.tabcontent').css("display", "none");
        
        tablinks = $('.tablinks').removeClass("active");

        $(`#${discipline}`).css("display", "block");
        evt.target.classList.add("active");
    }
});

