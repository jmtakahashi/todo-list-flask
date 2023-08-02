const BASE_URL = "http://localhost:5000";

deleteBtns = document.querySelectorAll(".todo__deleteBtn");
editBtns = document.querySelectorAll(".todo__editBtn");

const deleteHandler = async (e) => {
  e.preventDefault();
  const id = e.target.dataset.id;

  const container = document.getElementById(id);

  try {
    const resp = await axios.delete(`${BASE_URL}/api/todos/${id}`);

    console.log(resp);

    container.remove();
  } catch (e) {
    console.log("error: ", e);
  }
};

const editHandler = async (e) => {
  e.preventDefault();
  const id = e.target.dataset.id;

  const container = document.getElementById(id);

  try {
    const resp = await axios.patch(`${BASE_URL}/api/todos/${id}`);

    console.log(resp);

    e.target.parentElement.remove();
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
