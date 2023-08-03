const BASE_URL = "http://localhost:5000";

deleteBtns = document.querySelectorAll(".todo__deleteBtn");
editBtns = document.querySelectorAll(".todo__editBtn");
doneBtns = document.querySelectorAll(".todo__doneBox");

// handle the done checkbox click
const doneHandler = async (e) => {
  const id = e.target.dataset.id;

  try {
    const resp = await axios({
      method: "patch",
      headers: { "Content-Type": "application/json" },
      url: `${BASE_URL}/api/todos/${id}`,
      data: { done: e.target.checked },
    });
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
    const resp = await axios.delete(`${BASE_URL}/api/todos/${id}`);

    container.remove();
  } catch (e) {
    console.log("error: ", e);
  }
};

// handle the edit button click
const editHandler = async (e) => {
  e.preventDefault();
  const id = e.target.dataset.id;

  // our tr will have an id attribute
  const container = document.getElementById(id);

  // hide the current html and show a form with and edit and cancel button
  container.innerHTML = `<form><input type="text"/><button>Submit</button><button>Cancel</button>`;

  try {
    const resp = await axios({
      method: "patch",
      headers: { "Content-Type": "application/json" },
      url: `${BASE_URL}/api/todos/${id}`,
      data: { todo: todo.value },
    });

    // replace the current inner text with the submitted inner text
  } catch (e) {
    console.log("error: ", e);
  }
};

for (let btn of deleteBtns) {
  btn.addEventListener("click", deleteHandler);
}

for (let btn of editBtns) {
  btn.addEventListener("click", editHandler);
}

for (let btn of doneBtns) {
  btn.addEventListener("click", doneHandler);
}
