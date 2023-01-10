$(document).ready( function () {
    $('#player_stats').DataTable({
        order: [[3, 'desc']]
    });

    $(function(){
        $("#playerstats").on("click", "tr[role=\"button\"]", function () {
             window.location = $(this).data("href");
        });
   });

   $('.display').DataTable();
} );

