let popup1 = document.getElementById("popup1")
let popup2 = document.getElementById("popup2")

function openPopup1(){
    popup1.classList.add("open-popup")
}
function closePopup1(){
    popup1.classList.remove("open-popup")
}

function openPopup2(){
    popup2.classList.add("open-popup")
}
function closePopup2(){
    popup2.classList.remove("open-popup")
}


$(document).ready(function(){
    $('#formSignUp').on('submit', function(event){
        event.preventDefault();
        $.ajax({
            type: "POST",
            url: "/signUp_processing",
            data: {
                name: $('#nameUser').val(),
                email: $('#emailUser').val()
            }
        })
        
        .done(function(data){
            if (data.success){
                openPopup1()
                $('#successNofication').text(data.success).show();
            }
            else {
                openPopup2()
                $('#errorNofication').text(data.error).show();
            }
        })
    })
})

$(document).ready(function(){
    $('#formCheckIn').on('submit', function(event){
        event.preventDefault();

        $.ajax({
            type: "POST",
            url: "/checkIn_processing",
        })
        
        .done(function(data){
            if (data.welcome){
                openPopup1();
                $('#welcomeNofication').text(data.welcome + " (" + data.accuracy +  "%)").show();

            }
            else {
                openPopup2();
                $('#unknownNofication').text(data.unknown).show();
            }
        })
    })
})

$(document).ready(function(){
    $('#fingerprint_form').on('submit', function(event){
        event.preventDefault();
        var get_url = window.location.href;
        id = get_url.split("/").pop();
        $.ajax({
            type: "POST",
            url: "/fingerprint_processing",
            data:
            {
                id_from_url: id
            }
        })
        .done(function(data){
            if (data.fingerprint){
                $('#fingerprintNofication').text(data.fingerprint).show();
                // $('#unknownNofication').hide();

            }
            else {
                $('#fingerprintNofication').hide();
                // $('#unknownNofication').text(data.unknown).show();
            }
            $.ajax({
                type: "POST",
                url: "/fingerprint_processing2",
                data:
                {
                    id_from_url: id
                }
            })
            .done(function(data){
                if (data.fingerprint2success){
                    $('#fingerprintNofication').text(data.fingerprint2success).show();
                    $('#backToHome_button').show();
                } 
                else {
                    $('#fingerprintNofication').text(data.fingerprint2error).show();
                    $('#tryAgain_button').show();
                }
            })
        })
    })
})

$(document).ready(function(){
    $("#fingerprint_signUp_button").click(function(event){
        $('#fingerprintNofication').text("Please Place Your Finger On The Sensor").show();
        $("#fingerprint_signUp_button").hide();
    })
})

$(document).ready(function(){
    $("#tryAgain_button").click(function(event){
        $('#tryAgain_button').hide();
        $('#fingerprintNofication').hide();
        $("#fingerprint_signUp_button").show();
    })
})

$(document).ready(function(){
    $('#formCheckInFingerprint').on('submit', function(event){
        event.preventDefault();

        $.ajax({
            type: "POST",
            url: "/checkIn_with_fingerprint_processing",
        })
        
        .done(function(data){
            if (data.welcome){
                openPopup1();
                $('#welcomeNofication').text(data.welcome).show();
            }
            else if (data.unknown){
                openPopup2();
                $('#unknownNofication').text(data.unknown).show();
            }
        })
    })
})

$(document).ready(function(){
    $("#fingerprint_confirm").click(function(event){
        $.ajax({
            type: "POST",
            url: "/fingerprint_confirm",
        })
    })
})
$(document).ready(function(){
    $("#face_confirm").click(function(event){
        $.ajax({
            type: "POST",
            url: "/face_confirm",
        })
    })
})

$(document).ready(function(){
    $("#fingerprint_checkIn_button").click(function(event){
        $('#nofication1').text("Please Place Your Finger On The Sensor").show();
        $("#fingerprint_checkIn_button").hide();
    })
})

$(document).ready(function(){
    $("#fingerprint_tryAgain1").click(function(event){
        $('#nofication1').hide();
        $("#fingerprint_checkIn_button").show();
    })
})
$(document).ready(function(){
    $("#fingerprint_tryAgain2").click(function(event){
        $('#nofication1').hide();
        $("#fingerprint_checkIn_button").show();
    })
})

