$(document).ready(function () {
    var teamsArray = $('.tourney').data('teams-array');
    var resultsArray = $('.tourney').data('results');

    console.log(resultsArray);
    var bigData = {
        teams : teamsArray,
        results : resultsArray,
    };
    
    $(function() {
        $('.tourney').bracket({skipConsolationRound: true, init: bigData})
    });

    var resizeParameters = {
        skipConsolationRound: true, 
        scoreWidth: 20,
        init: bigData
    };

    function resize(input, propName) {
        resizeParameters[propName] = parseInt(input);
        $('.tourney').bracket(resizeParameters);        
    }
    
    $('input').on('input', function(evt) {
        resize(evt.target.value, evt.target.dataset.propname);
        console.log(evt.target.value, evt.target.dataset.propname);
    });
})