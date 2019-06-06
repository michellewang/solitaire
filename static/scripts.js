var clicked = false;

var move = {
    initial_cardgroup_id: "",
    initial_position: "",
    initial_row: "",
    
    final_cardgroup_id: "",
    final_position: "",
    final_row: "",
};

// get links from meta data
var draw_link = $("#links").data("draw_link");
var play_link = $("#links").data("play_link");

var acepiles_id = ["acepile0", "acepile1", "acepile2", "acepile3"];

$(function () {
    
    // when image is clicked
    $("img").click(function() {
        
        // get image's id
        var img_id = this.id;
        
        // if user wants to draw cards
        if (img_id == "draw") {
            
            // draw 3 cards
            window.location.replace(draw_link);
        
        // if no image was clicked before
        } else if (!clicked) {
            
            // if image is in column and visible
            if (!isNaN(Number(img_id))) {
                
                // select clicked image and all images below
                $(this).addClass("selected");
                $(this).nextAll().addClass("selected");
                clicked = true;

                // remember image location (column)
                move.initial_cardgroup_id = 2;
                move.initial_position = Number(img_id.slice(0, 1));
                move.initial_row = Number(img_id.slice(1));
                
            // else if image is from stack
            } else if (img_id == "stack") {
                
                // select image
                $(this).addClass("selected");
                clicked = true;
                
                // remember image location (stack)
                move.initial_cardgroup_id = 0;
            }
            
            // make acepiles clickable
            for (var i = 0; i < 4; i++) {
                $("#" + acepiles_id[i]).addClass("clickable");
            }
        
        // if this image was clicked previously
        } else if ($(this).hasClass("selected")) {
            
            // unselect image
            $(this).removeClass("selected");
            clicked = false;
            
            // forget image was selected
            move.initial_cardgroup_id = "";
            move.initial_position = "";
            move.initial_row = "";
            
            // make acepiles not clickable anymore
            for (var i = 0; i < 4; i++) {
                $("#" + acepiles_id[i]).removeClass("clickable");
            }
            
            // also unselect all images from column
            $(this).siblings().removeClass("selected");
        
        // if user is trying to move a card to a column
        } else if (!isNaN(Number(img_id))) {
            
            // remember image destination (column)
            move.final_cardgroup_id = 2;
            move.final_position = Number(img_id.slice(0, 1));
            move.final_row = Number(img_id.slice(1));
            
            // move card
            $.post(play_link,
                move,
                function() {
                window.location.replace(play_link);
            });
            
        // if user is trying to move a card to an acepile
        } else if (acepiles_id.includes(img_id)) {
            
            // remember image location (acepile)
            move.final_cardgroup_id = 1;
            move.final_position = Number(img_id.slice(-1));
            
            // move card
            $.post(play_link,
                move,
                function() {
                window.location.replace(play_link + "?");
            });
        }
    });
});

$(function () {
    
    // when user clicks on "New Game" button in play page
    $("#new_game").click( function() {
        
        // make sure that user wants to start a new game
        if (confirm("Are you sure you want to start a new game?")) {
            return true;
        } else {
            return false;
        }
    });
});
