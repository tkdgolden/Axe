// dont do anything until the page is loaded
document.addEventListener('DOMContentLoaded', function() {

    // there are four targets on the target that will be "hot" on different throws of the round
    options = ["RED A (Top Left)", "GREEN B (Top Right)", "BLUE C (Bottom Left)", "ORANGE D (Bottom Right)"];

    // randomly ordering the numbers that refer to the indexes of the options array
    usedNumbers = [];
    for (let i = 0; i < 4; i++) {
        do {
            randomNumber = Math.floor(Math.random() * 4);
        } while (usedNumbers.includes(randomNumber));
        usedNumbers.push(randomNumber);
    }

    // displaying which target is "hot"
    document.getElementById("t1").innerHTML = (options[usedNumbers[0]]);
    document.getElementById("t2").innerHTML = (options[usedNumbers[1]]);
    document.getElementById("t3").innerHTML = (options[usedNumbers[2]]);
    document.getElementById("t4").innerHTML = (options[usedNumbers[3]]);

    // recording the sequence
    sequence = [options[usedNumbers[0]], (options[usedNumbers[1]]), (options[usedNumbers[2]]), (options[usedNumbers[3]])];
    
    // repeating the above for throws 5-8
    usedNumbers = [];
    for (let i = 0; i < 4; i++) {
        do {
            randomNumber = Math.floor(Math.random() * 4);
        } while (usedNumbers.includes(randomNumber));
        usedNumbers.push(randomNumber);
    }
    document.getElementById("t5").innerHTML = (options[usedNumbers[0]]);
    document.getElementById("t6").innerHTML = (options[usedNumbers[1]]);
    document.getElementById("t7").innerHTML = (options[usedNumbers[2]]);
    document.getElementById("t8").innerHTML = (options[usedNumbers[3]]);
    sequence.push([options[usedNumbers[0]], (options[usedNumbers[1]]), (options[usedNumbers[2]]), (options[usedNumbers[3]])]);
    document.getElementById("sequence").value = sequence;
    console.log(document.getElementById("sequence").value);

    // add up each players scores from the dropdowns and whether they got the quickpoint
    function calculateScores(){
        p1sum = 0;
        for (item of p1dropdowns){
            if(item.value){
                if(!isNaN(item.value)){
                    p1sum += parseInt(item.value);
                    here = item.parentNode.parentNode.getElementsByClassName('1q');
                    for (each of here){
                        each.removeAttribute('disabled');
                    }
                }
                else{
                    here = item.parentNode.parentNode.getElementsByClassName('1q');
                    for (each of here){
                        each.checked = false;
                        each.setAttribute('disabled', true);
                    }
                }
            }
        }
        for (item of p1radios){
            if(item.checked){
                p1sum += 1;
            }
        }
        document.getElementById("p1score").innerHTML = p1sum;
        p2sum = 0;
        for (item of p2dropdowns){
            if(item.value){
                if(!isNaN(item.value)){
                    p2sum += parseInt(item.value);
                    here = item.parentNode.parentNode.getElementsByClassName('2q');
                    for (each of here){
                        each.removeAttribute('disabled');
                    }
                }
                else{
                    here = item.parentNode.parentNode.getElementsByClassName('2q');
                    for (each of here){
                        each.checked = false;
                        each.setAttribute('disabled', true);
                    }
                }
            }
        }
        for (item of p2radios){
            if(item.checked){
                p2sum += 1;
            }
        }
        document.getElementById("p2score").innerHTML = p2sum;
    }

    // automatically recalculate scores when anything is changed
    p1dropdowns = document.getElementsByClassName('1');
    p2dropdowns = document.getElementsByClassName('2');
    p1radios = document.getElementsByClassName("1q");
    p2radios = document.getElementsByClassName("2q");
    radios = document.querySelectorAll('input[type=radio]');
    for (item of p1dropdowns){
        item.onchange = calculateScores;
    }
    for (item of p2dropdowns){
        item.onchange = calculateScores;
    }
    for (item of radios){
        item.onchange = calculateScores;
    }
    

}, false);

// wont show the "hot" target without a recorded score for both players 
function ShowRound(elem)
{
    if (elem != "t1") {
        if (document.getElementById(elem).parentNode.parentNode.previousElementSibling.lastElementChild.lastElementChild.value == ""){
            alert("Score previous round to move on!");
            return false;
        }
        if (document.getElementById(elem).parentNode.parentNode.previousElementSibling.firstElementChild.lastElementChild.value == ""){
            alert("Score previous round to move on!");
            return false;
        }
    }
    document.getElementById(elem).setAttribute('style', 'display:inline');
    document.getElementById(elem).previousElementSibling.setAttribute('style', 'display:none');
    document.getElementById(elem).parentNode.parentNode.firstElementChild.lastElementChild.classList.remove("wait");
    document.getElementById(elem).parentNode.parentNode.lastElementChild.lastElementChild.classList.remove("wait");
}

function CheckTie(){
    console.log("here");
    p1score = document.getElementById("p1score").innerHTML;
    p2score = document.getElementById("p2score").innerHTML;
    if (p1score == p2score){
        document.getElementById("winner").removeAttribute("hidden");
        event.preventDefault();
    }
    if (document.getElementById("winner").value){
        forms = document.getElementsByTagName('form');
        for (each of forms){
            each.submit();
        }
    }
}