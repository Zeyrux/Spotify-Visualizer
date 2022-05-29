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


export function create_button(innerHTML, id) {
    let button = document.createElement("button");
    button.innerHTML = innerHTML;
    button.id = id;
    return button;
}
