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

  // our tr will have an id attribute
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
        container.children[1].classList.add("complete")
      } else {
        container.children[1].classList.remove("complete")
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
const editHandler = async (e) => {
  const id = e.target.dataset.id;

  const todoTextArea = e.target // this will be the <td>
  const curr_text = todoTextArea.innerText

  // hide the current html and show a form with and edit and cancel button
  const editForm = document.createElement('input')
  editForm.setAttribute("name", "editedTodo")
  editForm.setAttribute("type", "text")
  editForm.value = curr_text;
  todoTextArea.innerText = "";
  todoTextArea.append(editForm)

  todoTextArea.children[0].addEventListener("keypress", async (e) => {
    if (e.key === 'Enter') {
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
          // remove text field and replace with new text
          todoTextArea.children[0].remove()
          todoTextArea.innerText = editedTodo
         
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
