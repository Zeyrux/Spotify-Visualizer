import { controller, user_playlists } from "./init.js";

export function create_form(form_id, action, submit_value, create_hidden, hidden_value, hidden_name) {
    // create form
    let form = document.createElement("form");
    if (form_id != undefined) {
        form.id = form_id
    }
    form.method = "get";
    form.action = action;

    // create submit
    let submit = document.createElement("input");
    submit.type = "submit";
    submit.value = submit_value;

    // create hidden input
    let hidden_input = undefined
    if (create_hidden) {
        hidden_input = document.createElement("input");
        hidden_input.type = "hidden";
        hidden_input.value = hidden_value;
        hidden_input.setAttribute("name", hidden_name);
    }

    // create controller hidden
    let controller_input = document.createElement("input");
    controller_input.type = "hidden";
    form.addEventListener("click", (e) => controller_input.value = JSON.stringify(controller));
    controller_input.setAttribute("name", "controller");
    
    form.appendChild(submit);
    form.appendChild(controller_input);
    if (create_hidden)
        form.appendChild(hidden_input);
    return form;
}


export function set_true(element) {
    element.style.background = "rgb(154, 204, 144)";
}


export function set_false(element) {
    element.style.background = "rgb(187, 104, 104)";
}


export function create_checkable_button(innerHTML, update_variable, clicked) {
    let button = document.createElement("button");
    button.innerHTML = innerHTML;
    
    if (clicked)
        set_true(button);
    else
        set_false(button);
    // click
    button.addEventListener("click", function (e) {
        if (controller[update_variable]) {
            controller[update_variable] = false;
            set_false(button);
        } else {
            controller[update_variable] = true;
            set_true(button);
        };
    });
    // hover begin
    button.addEventListener("mouseenter", function (e) {
        if (controller[update_variable])
            set_false(button);
        else
            set_true(button);
    });
    // hover leave
    button.addEventListener("mouseleave", function (e) {
        if (controller[update_variable])
            set_true(button);
        else
            set_false(button);
    });
    return button;
}


export function create_button(innerHTML, button_class, id) {
    let button = document.createElement("button");
    button.innerHTML = innerHTML;
    button.className = button_class;
    button.id = id;
    return button;
}


export function create_slider(min, step, max, value, id) {
    let slider = document.createElement("input");
    slider.type = "range";
    slider.min = min;
    slider.step = step;
    slider.max = max;
    slider.value = value;
    slider.id = id;
    return slider
}


export function seconds_to_string(seconds) {
    seconds = parseInt(seconds);
    let minutes = 0;
    while (seconds > 60) {
        minutes += 1;
        seconds -= 60
    }
    if (seconds < 9)
        seconds = "0" + seconds;
    return minutes + ":" + seconds;
}


export function create_slider_duration(duration) {
    let div = document.createElement("div");

    let slider = create_slider(0, 1, duration, 0, "duration_slider")
    slider.addEventListener("input", function (e) {
        document.getElementById("duration_label").innerHTML = seconds_to_string(e.target.value);
        document.getElementById("audio").currentTime = e.target.value;
    });

    let label = document.createElement("p");
    label.id = "duration_label";
    label.innerHTML = seconds_to_string(0);

    div.appendChild(slider);
    div.appendChild(label);
    return div
}


export function create_slider_volume(start) {
    let div = document.createElement("div");
    let div_slider = document.createElement("div");

    // create slider
    let slider_func = function (e) {
        let huge = document.getElementById("volume_slider_huge").value;
        let small = document.getElementById("volume_slider_small").value;
        let volume = parseFloat(huge) + parseFloat(small);
        controller["volume"] = volume;
        document.getElementById("audio").volume = volume;
        document.getElementById("volume_label").innerHTML = parseFloat(volume).toFixed(3) + "🔈";
    }

    let slider_huge = create_slider(0, 0.02, 0.98, start, "volume_slider_huge");
    slider_huge.addEventListener("input", slider_func);

    let slider_small = create_slider(0, 0.001, 0.02, start % 0.02, "volume_slider_small");
    slider_small.addEventListener("input", slider_func);

    div_slider.appendChild(slider_huge);
    div_slider.appendChild(slider_small);

    // create label
    let label = document.createElement("p");
    label.id = "volume_label";
    label.innerHTML = parseFloat(start).toFixed(3) + "🔈";

    div.appendChild(div_slider);
    div.appendChild(label);
    return div;
}


export function create_fps() {
    let select = document.createElement("select");
    
    // add all fps
    let all_fps = [240, 144, 60, 30, 15, 1]
    all_fps.forEach(fps => {
        let option = document.createElement("option");
        option.innerHTML = fps;
        option.value = fps;
        select.appendChild(option);
    });

    select.addEventListener("change", (e) => controller["fps"] = e.target.value);

    select.value = controller["fps"];
    return select;
}


export function create_user_playlists() {
    let div = document.createElement("div");
    div.id = "playlists"
    
    // create playlists
    user_playlists.forEach(playlist => {
        // create text
        let p = document.createElement("p");
        p.innerHTML = playlist.name;
        p.addEventListener("click", function (e) {
            document.getElementById(playlist.id).style.display = "inline";
            window.addEventListener("click", function (e) {
                if (e.target.innerHTML != playlist.name) {
                    document.getElementById(playlist.id).style.display = "none";
                }
            });
        });
        div.appendChild(p);
    });

    return div
}


export function create_user_tracks() {
    let div = document.createElement("div");
    div.id = "tracks";

    // create tracks
    user_playlists.forEach(playlist => {
        let div_track = document.createElement("div");
        div_track.id = playlist.id;
        div_track.style.display = "none";
        playlist.tracks.forEach(track => {
            let p = document.createElement("p");
            p.innerHTML = track.name;
            p.addEventListener("click", function (e) {
                let form = create_form("play_track_form", "/play_track", "Submit", true, track.id, "track");
                div_track.appendChild(form);
                //form.click();
                //form.submit();
            })
            div_track.appendChild(p);
        });
        div.appendChild(div_track);
    });

    return div;
}
