document.addEventListener('DOMContentLoaded', function() {
    options = ["Top", "Left", "Right", "Bottom"];
    usedNumbers = [];
    for (let i = 0; i < 4; i++) {
        do {
            randomNumber = Math.floor(Math.random() * 4);
        } while (usedNumbers.includes(randomNumber));
        usedNumbers.push(randomNumber);
    }
    document.getElementById("t1").innerHTML = (options[usedNumbers[0]]);
    document.getElementById("t2").innerHTML = (options[usedNumbers[1]]);
    document.getElementById("t3").innerHTML = (options[usedNumbers[2]]);
    document.getElementById("t4").innerHTML = (options[usedNumbers[3]]);
    sequence = [options[usedNumbers[0]], (options[usedNumbers[1]]), (options[usedNumbers[2]]), (options[usedNumbers[3]])];
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

function ShowRound(elem)
{
    if (elem != "t1") {
        if (document.getElementById(elem).parentNode.parentNode.previousElementSibling.lastElementChild.lastElementChild.value == "" || document.getElementById(elem).parentNode.parentNode.previousElementSibling.lastElementChild.previousElementSibling.lastElementChild.value == "")
        {
            alert("Score previous round to move on!");
            return false;
        }
    }
    document.getElementById(elem).setAttribute('style', 'display:inline');
    document.getElementById(elem).previousElementSibling.setAttribute('style', 'display:none');
    document.getElementById(elem).parentNode.nextElementSibling.firstElementChild.removeAttribute('disabled');
    document.getElementById(elem).parentNode.nextElementSibling.nextElementSibling.firstElementChild.removeAttribute('disabled');
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