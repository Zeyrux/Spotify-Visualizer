import { controller } from "./init.js";

export function create_form(form_id, submit_value, create_hidden, hidden_value, hidden_name) {
    // create form
    let form = document.createElement("form");
    if (form_id != undefined) {
        form.id = form_id
    }
    form.method = "get";
    form.action = "/visualizer";

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
    
    form.appendChild(submit);
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


export function create_slider_volume(start) {
    let div = document.createElement("div");
    let div_slider = document.createElement("div");

    // create slider
    let slider_func = function (e) {
        let huge = document.getElementById("volume_huge").value;
        let small = document.getElementById("volume_small").value;
        let volume = parseFloat(huge) + parseFloat(small);
        document.getElementById("audio").volume = volume;
        document.getElementById("volume_label").innerHTML = parseFloat(volume).toFixed(3) + "🔈";
    }

    let slider_huge = create_slider(0, 0.02, 1, start, "volume_huge");
    slider_huge.addEventListener("input", slider_func);

    let slider_small = create_slider(0, 0.001, 0.02, 0, "volume_small");
    slider_small.addEventListener("input", slider_func);

    div_slider.appendChild(slider_huge);
    div_slider.appendChild(slider_small);

    // create label
    let label = document.createElement("label");
    label.id = "volume_label";
    label.innerHTML = parseFloat(start).toFixed(3) + "🔈";

    div.appendChild(div_slider);
    div.appendChild(label);
    return div;
}
