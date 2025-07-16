const todos = document.getElementsByClassName("todo")

const handleClick = (e) => {
  if (e.target.classList.contains("todo__doneBtn")) {
    doneHandler(e)
  }
  if (e.target.classList.contains("todo__text")) {
    editHandler(e)
  }
  if (e.target.classList.contains("todo__deleteBtn")) {
    deleteHandler(e)
  }
}

// handle the done checkbox click
const doneHandler = async (e) => {
  const id = e.target.dataset.id;

  // will be the <tr> and <tr> will have an id attribute
  const container = document.getElementById(id);

  try {
    const resp = await axios({
      method: "patch",
      headers: { "Content-Type": "application/json" },
      url: `/api/todos/${id}`,
      data: { complete: e.target.checked },
    });

    if (resp.status == 200) {
      if (resp.data.todo.complete) {
        container.children[1].children[0].classList.add("complete")
      } else {
        container.children[1].children[0].classList.remove("complete")
      }
    }
    
  } catch (e) {
    console.log("error: ", e);
  }
};

// handle the delete button click
const deleteHandler = async (e) => {
  e.preventDefault();

  const id = e.target.dataset.id;

  // our tr will have an id attribute
  const container = document.getElementById(id);

  try {
    const resp = await axios.delete(`/api/todos/${id}`);

    if (resp.status === 200) {
      container.remove();
    }
    
  } catch (e) {
    console.log("error: ", e);
  }
  
};

// handle editing the todo
const editHandler = (e) => {
  const id = e.target.dataset.id;

  const todoTextArea = e.target // this will be the <span> inside the <td>
  const todoTD = e.target.parentElement // this will be the <td>
  const curr_text = todoTextArea.innerText

  // hide the current <span> html and show an input element with the todo text pre-populated
  const editForm = document.createElement('input')
  editForm.setAttribute("name", "editedTodo")
  editForm.setAttribute("type", "text")
  editForm.classList.add("todo__editTodoInput")
  editForm.setAttribute("data-id", id)
  editForm.value = curr_text;
  todoTextArea.remove()
  todoTD.append(editForm)
  editForm.focus();

  // if input is unfocused with hitting enter, reset the <td> to original state
  editForm.addEventListener("blur", (e) => {
    e.target.remove()
    todoTD.append(todoTextArea)
  })

  
  editForm.addEventListener("keypress", async (e) => {
    if (e.key === 'Enter') {

      const id = editForm.getAttribute("data-id");
      const todo = e.target.value

      try {
        const resp = await axios({
          method: "patch",
          headers: { "Content-Type": "application/json" },
          url: `/api/todos/${id}`,
          data: { todo },
        });

        if (resp.status === 200) {
          const editedTodo = resp.data.todo.todo
          const complete = resp.data.todo.complete
          // remove the editTodo <input> field and replace with new text
          const span = document.createElement('span')
          span.setAttribute('data-id', id)
          span.classList.add('todo__text')
          if (complete) span.classList.add('complete')
          span.innerText = editedTodo
          // editForm.remove()
          // form is already removed from our blur event
          todoTD.append(span)
        }
      } catch (e) {
        console.log("error: ", e);
      }
    }
  })
};

for (let todo of todos) {
  todo.addEventListener("click", handleClick )
}
