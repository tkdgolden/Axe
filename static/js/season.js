$(document).ready(function () {
    var absentPlayers = [];

    $(".toprow").on("click", function() {
        var playerId = $(this).data("player");
        if ($(this).hasClass("table-active")) {
            absentPlayers = absentPlayers.filter(function(current) {
                return current !== playerId;
            });
            $(this).removeClass("table-active");
        }
        else {
            absentPlayers.push(playerId);
        }
        $('.squares').removeClass("table-active");
        $('.toprow').removeClass("table-active");
        absentPlayers.forEach(function(pID) {
            $(`.${pID}`).addClass("table-active");
        });
    });

    var combinations = [];
    $(".squares").each(function() {

        const arr = ($(this).prop("class")).split(" ");
        id1 = (arr[0]);
        id2 = (arr[1]);
        tuple = id1.concat(id2);
        reverse = id2.concat(id1);
        if (combinations.includes(reverse) == false) {
            combinations.push(tuple);
        }
        else {
            $(this).removeClass("squares");
            $(this).addClass("table-active");
            $(this).text("");
        }
    });

    var complete = $(".squares").filter(function() {
        return $(this).text().includes("complete");
    });

    complete.addClass("complete");
    complete.text("complete");

    var begun = $(".squares").filter(function() {
        return $(this).children().data("match");
    });
    begun.addClass("begun");
    begun.on("click", function() {
        const mId = $(this).children().data("match");
        window.location = `editmatch?match=${mId}`;
    });

    $(".squares").each(function() {

        if (($(this).hasClass("complete") === false) && ($(this).hasClass("begun") === false)) {
            var p1 = $(this).data("p1");
            var p2 = $(this).data("p2");
            $(this).on("click", function() {
                window.location = `creatematch?competitor_selection=[${p1},${p2}]`;
            });
        }
    });

    $("form").change(function() {
        const week = $(this).children("input").val();
        sessionStorage.setItem("week", week);
        const season = new URLSearchParams(window.location.search).get('season');
        window.location = `seasonview?season=${season}&week=${week}`;
    });

    $(".grid").each(function() {
        const classes = $(this).attr("class").split(/\s+/);
        const playerIdClasses = classes.filter(function(eachClass) {
            if (parseInt(eachClass)) {
                return parseInt(eachClass);
            }
        });
        $(this).on("mouseenter",
            function() {
                playerIdClasses.forEach(function(eachId) {
                    const id = parseInt(eachId);
                    const withId = $(`.${id}`);
                    const showing = withId.filter(function() {
                        if ($(this).hasClass("table-active") === false) {
                            return this;
                        }
                    });
                    console.log(showing);
                    showing.addClass("hover");
                });
            }
        );
        $(this).on("mouseout", function() {
            $("*").removeClass("hover");
        })
    });
});