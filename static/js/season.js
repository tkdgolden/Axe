$(document).ready(function () {
    var storedPlayers = JSON.parse(sessionStorage.getItem('absentPlayers'));
    var absentPlayers = [];
    storedPlayers.forEach(function(player) {
        absentPlayers.push(Number.parseInt(player));
    })
    absentPlayers.forEach(function(player) {
        $(`.${player}`).addClass("table-active");
    })

    $(".toprow").on("dblclick", function() {
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
        sessionStorage.setItem('absentPlayers', JSON.stringify(absentPlayers));
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

    $(".view").change(function() {
        const quarter = $("#lap option:selected").data("quarter");
        const lap = $("#lap option:selected").data("lap");
        const lap_id = $("#lap option:selected").data("id");
        sessionStorage.setItem("season_lap", lap_id);        const season = new URLSearchParams(window.location.search).get('season');
        window.location = `seasonview?season=${season}&quarter=${quarter}&lap=${lap}`;
    });

    $(`#lap option[value=${sessionStorage.getItem("season_lap")}]`).attr('selected', 'true');

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
                    showing.addClass("hover");

                    const opponentElements = $("td").filter(function() {
                        if ($(this).hasClass("table-active") === false) {
                            if ($(this).hasClass(`${id}`) === true) {
                                if ($(this).hasClass("complete") === false) {
                                    return this;
                                }
                            }
                        }
                    })
                    var opponentsClasses = [];
                    $(opponentElements).each(function() {
                        const elemClasses = $(this).attr("class").split(/\s+/);
                        $(elemClasses).each(function(){
                            if (Number.parseInt(this) !== id) {
                                if (Number.parseInt(this)) {
                                    opponentsClasses.push(Number.parseInt(this));
                                } 
                            }
                        });
                    });
                    opponentsClasses.forEach(function(id) {
                    $(`th.${id}`).filter(function() {
                            $(this).toggleClass("opponent");
                        });
                    })
                });
            }
        );
        $(this).on("click",
            function() {
                playerIdClasses.forEach(function(eachId) {
                    const id = parseInt(eachId);
                    const withId = $(`.${id}`);
                    const showing = withId.filter(function() {
                        if ($(this).hasClass("table-active") === false) {
                            return this;
                        }
                    });
                    showing.toggleClass("hover");

                    const opponentElements = $("td").filter(function() {
                        if ($(this).hasClass("table-active") === false) {
                            if ($(this).hasClass(`${id}`) === true) {
                                if ($(this).hasClass("complete") === false) {
                                    return this;
                                }
                            }
                        }
                    })
                    var opponentsClasses = [];
                    $(opponentElements).each(function() {
                        const elemClasses = $(this).attr("class").split(/\s+/);
                        $(elemClasses).each(function(){
                            if (Number.parseInt(this) !== id) {
                                if (Number.parseInt(this)) {
                                    opponentsClasses.push(Number.parseInt(this));
                                } 
                            }
                        });
                    });
                    opponentsClasses.forEach(function(id) {
                    $(`th.${id}`).filter(function() {
                            $(this).toggleClass("opponent");
                        });
                    })
                });
            }
        );
        $(this).on("mouseout", function() {
            $("*").removeClass("hover");
            $("*").removeClass("opponent");
        });
    });
});