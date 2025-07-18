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

  console.log(e.target)

  // our tr will have an id attribute
  const id = e.target.dataset.id;
  const container = document.getElementById(id);

  
  const loaderSpan = document.createElement("span")
  loaderSpan.classList.add("loader")
    
  e.target.parentElement.appendChild(loaderSpan)
  e.target.remove()

  return
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
  // e.target will be the <span>
  
  const todoSpan = e.target // this will be the <span> inside the <td>
  const editTodoInput = e.target.parentElement.children[1] // this will be the input element
  const curr_text = e.target.innerText // this will be the text before editing

  // remove the current <span> html and show an input element with the todo text pre-populated
  todoSpan.classList.add("hidden")
  editTodoInput.value = curr_text
  editTodoInput.classList.remove("hidden")

  editTodoInput.focus();

  editTodoInput.addEventListener("blur", editFormHandler)
  editTodoInput.addEventListener("keypress", editFormHandler)
    
};

const editFormHandler = async (e) => {
  // e.target will be our input element

  if (e.type === "blur") {
    e.target.parentElement.children[0].classList.remove("hidden")
    e.target.classList.add("hidden")

  } else if (e.type === "keypress") {
    if (e.key === 'Enter') {
      e.target.removeEventListener("blur", editFormHandler);

      const id = e.target.getAttribute("data-id");
      const edited_todo = e.target.value

      try {
        const resp = await axios({
          method: "patch",
          headers: { "Content-Type": "application/json" },
          url: `/api/todos/${id}`,
          data: { todo: edited_todo },
        });

        if (resp.status === 200) {
          const newTodo = resp.data.todo.todo
          const complete = resp.data.todo.complete

          // remove the <input> field and replace with new text
          e.target.parentElement.children[0].innerText = newTodo

          e.target.parentElement.children[0].classList.remove("hidden")
          e.target.classList.add("hidden")

        }
      } catch (e) {
        console.log("error: ", e);
      }
    }
  }  
}

for (let todo of todos) {
  todo.addEventListener("click", handleClick )
}
