import { controller, user_playlists } from "./init.js";


export function create_controller(form) {
    let controller_input = document.createElement("input");
    controller_input.type = "hidden";
    form.addEventListener("click", (e) => controller_input.value = JSON.stringify(controller));
    controller_input.setAttribute("name", "controller");
    return controller_input;
}

export function create_form(form_id, action, submit_value, class_name, create_hidden, hidden_value, hidden_name) {
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
    if (class_name != undefined) {
        submit.className = class_name;
    }
    submit.value = submit_value;

    // create hidden input
    let hidden_input = undefined
    if (create_hidden) {
        hidden_input = document.createElement("input");
        hidden_input.type = "hidden";
        hidden_input.value = hidden_value;
        hidden_input.setAttribute("name", hidden_name);
    }

    form.appendChild(submit);
    form.appendChild(create_controller(form));
    if (create_hidden)
        form.appendChild(hidden_input);
    return form;
}


export function create_form_two_hidden(action, submit_value, class_name, hidden_value_one, hidden_name_one, hidden_value_two, hidden_name_two) {
    // create form
    let form = document.createElement("form");
    form.method = "get";
    form.action = action;

    // create submit
    let submit = document.createElement("input");
    submit.type = "submit";
    submit.value = submit_value;
    if (class_name != undefined) {
        submit.className = class_name;
    }

    // create hidden input
    let hidden_input_one = document.createElement("input");
    hidden_input_one.type = "hidden";
    hidden_input_one.value = hidden_value_one;
    hidden_input_one.setAttribute("name", hidden_name_one);

    let hidden_input_two = document.createElement("input");
    hidden_input_two.type = "hidden";
    hidden_input_two.value = hidden_value_two;
    hidden_input_two.setAttribute("name", hidden_name_two);

    // add to form
    form.appendChild(submit);
    form.appendChild(hidden_input_one);
    form.appendChild(hidden_input_two);
    form.appendChild(create_controller(form));
    return form;
}


export function create_form_without_hidden(action, _blank, submit_value) {
    // create form
    let form = document.createElement("form");
    form.action = action;
    if (_blank)
        form.target = "_blank";
    form.method = "get";
    // create submit
    let submit = document.createElement("input");
    submit.type = "submit";
    submit.value = submit_value;
    form.appendChild(submit);
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
    return slider;
}


export function seconds_to_string(seconds) {
    seconds = parseInt(seconds);
    let minutes = 0;
    while (seconds > 60) {
        minutes += 1;
        seconds -= 60
    }
    if (seconds <= 9)
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
    div.id = "playlists";

    // create playlists
    user_playlists.forEach(playlist => {
        // create playlist div
        let playlist_div = document.createElement("div");
        playlist_div.className = "playlist";
        // add image
        let playlist_image = document.createElement("img");
        playlist_image.src = playlist.image_url;
        playlist_image.className = "playlist_image";
        // add text
        let p = document.createElement("p");
        p.innerHTML = playlist.name;

        // add event show tracks
        playlist_div.addEventListener("click", function (e) {
            // display playlist
            document.getElementById(playlist.id).style.display = "inline";
            window.addEventListener("click", function undisplay_playlist(e) {
                if (e.target.innerHTML != playlist.name && !e.target.classList.contains("track_part")) {
                    // undisplay playlist
                    document.getElementById(playlist.id).style.display = "none";
                    window.removeEventListener("click", undisplay_playlist);
                };
            });
        });

        // play playlist
        playlist_div.addEventListener("dblclick", function (e) {
            let form = create_form(undefined, "play_track", undefined, undefined, true, playlist.id, "playlist_id");
            form.click();
            form.submit();
        }, { once: true });

        playlist_div.appendChild(playlist_image);
        playlist_div.appendChild(p);
        div.appendChild(playlist_div);
    });
    return div;
}


export function create_user_tracks() {
    let div = document.createElement("div");
    div.id = "tracks";

    // create tracks
    user_playlists.forEach(playlist => {
        // create track div
        let div_tracks = document.createElement("div");
        div_tracks.id = playlist.id;
        div_tracks.style.display = "none";

        // create playlist details
        let div_playlist_details = document.createElement("div");
        div_playlist_details.className = "playlist_details";
        // image
        let image = document.createElement("img");
        image.src = playlist.image_url;
        image.className = "playlist_details_image";
        // buttons
        let div_buttons = document.createElement("div");
        div_buttons.className = "playlist_details_buttons";
        // play button
        let button_play = create_form(undefined, "/play_track", "▶", "button_details", true, playlist.id, "playlist_id");
        // download button
        let button_download = create_form(undefined, "/download_playlist", "⭳", "button_details", true, playlist.id, "playlist_id");
        // add to div
        div_buttons.appendChild(button_play);
        div_buttons.appendChild(button_download);
        div_playlist_details.appendChild(image);
        div_playlist_details.appendChild(div_buttons);
        // p
        let p = document.createElement("p");
        p.innerHTML = playlist.name;
        p.className = "playlist_details_p";
        // add to div
        div_tracks.appendChild(div_playlist_details);
        div_tracks.appendChild(p);

        // add tracks
        playlist.tracks.forEach(track => {
            // create div track
            let div_track = document.createElement("div");
            div_track.className = "track";
            // create image
            let image = document.createElement("img");
            image.src = track.image_url;
            image.classList.add("track_image", "track_part");
            // create p
            let p = document.createElement("p");
            p.innerHTML = track.name;
            p.classList.add("track_p", "track_part");

            // add show track event
            div_track.addEventListener("click", function (e) {
                // display track
                document.getElementById(track.id).style.display = "inline";
                window.addEventListener("click", function undisplay_track(e) {
                    if (!(e.target.classList.contains("track_part") && e.target.innerHTML == track.name)) {
                        // undisplay track
                        document.getElementById(track.id).style.display = "none";
                        window.removeEventListener("click", undisplay_track);
                    }
                });
            });

            // add submit event
            div_track.addEventListener("dblclick", function (e) {
                // create form and add second hidden input
                let form = create_form_two_hidden("/play_track", "Submit", undefined, track.id, "track_id", playlist.id, "playlist_id");
                form.style.visibility = "hidden";
                div_tracks.appendChild(form);
                form.click();
                form.submit();
            })

            div_track.appendChild(image);
            div_track.appendChild(p);
            div_tracks.appendChild(div_track);
        });
        div.appendChild(div_tracks);
    });
    return div;
}


export function create_user_track_details() {
    let div = document.createElement("div");
    div.id = "tracks_details";

    // create track details
    user_playlists.forEach(playlist => {
        playlist.tracks.forEach(track => {
            // create track div
            let div_track = document.createElement("div");
            div_track.id = track.id;
            div_track.style.display = "none";
            div_track.className = "track_details";
            // create image
            let image = document.createElement("img");
            image.src = track.image_url;
            image.classList.add("track_details_image", "track_part_details");
            // create p
            let p = document.createElement("p");
            p.innerHTML = track.name;
            p.classList.add("track_part_details");

            // div buttons
            let div_buttons = document.createElement("div");
            div_buttons.className = "track_details_buttons";
            // create play button
            let button_play = create_form_two_hidden("/play_track", "▶", "button_details", track.id, "track_id", playlist.id, "playlist_id");
            // create download button
            let button_download = create_form(undefined, "/download_track", "⭳", "button_details", true, track.id, "track_id");
            // add everything to div
            div_buttons.appendChild(button_play);
            div_buttons.appendChild(button_download);
            div_track.appendChild(image);
            div_track.appendChild(div_buttons);
            div_track.appendChild(p);
            div.appendChild(div_track);
        });
    });
    return div
}

export function create_reload() {
    return create_form_without_hidden("/refresh", true, "🗘");
}