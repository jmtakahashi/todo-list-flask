(function () {
  const todoListTitle = document.getElementById('todo-list-title');
  const todoListEN = document.getElementById('todo-list-en');
  const todoListJP = document.getElementById('todo-list-jp');
  const newTodoInput = document.getElementById('todo');
  const addTodoButton = document.getElementById('add-todo-button');
  const todos = document.getElementsByClassName('todo');

  // function to toggle between english and japanese todo list titles
  todoListTitle &&
    todoListTitle.addEventListener('click', (e) => {
      todoListEN.toggleAttribute('hidden');
      todoListJP.toggleAttribute('hidden');
    });

  // handle the click event for the add todo button (this is not an ajax request)
  const handleAddTodo = async (e) => {
    if (newTodoInput.value !== '') {
      const loaderSpan = document.createElement('span');
      loaderSpan.classList.add('loader');

      e.target.innerText = '';
      e.target.appendChild(loaderSpan);
    }
  };

  // handle the click event for the done checkbox, edit and delete buttons
  const handleClick = (e) => {
    /* ------------------------ handler defs ------------------------ */

    // handle setting completed status of the todo
    const doneHandler = async (e) => {
      const id = e.target.dataset.id;

      try {
        const res = await axios({
          method: 'patch',
          headers: { 'Content-Type': 'application/json' },
          url: `/api/todos/${id}`,
          data: { complete: e.target.checked },
        });

        /**
         * if the request was not successful or
         * the completed status of the returned todo is not what we set it to in the ui,
         * toggle the checkbox back to its original state
         */
        if (res.status !== 200 || res.data.todo.complete !== e.target.checked) {
          e.target.checked = !e.target.checked;
        }
      } catch (e) {
        console.error('error: ', e);
      }
    };

    // handle entering editing mode for the todo
    const editHandler = (e) => {
      const id = e.target.dataset.id;
      const container = document.getElementById(id);

      const todoSpan = container.querySelector('.todo__text');
      const todo = todoSpan.innerText; // this is the text before editing
      const editTodoInput = container.querySelector('.todo__editTodoInput');

      const todoFunctionsContainer = container.querySelector(
        '.todo__functionsContainer',
      );
      const editBtn = todoFunctionsContainer.querySelector('.todo__editBtn');
      const deleteBtn = todoFunctionsContainer.querySelector('.todo__deleteBtn');
      const saveBtn = todoFunctionsContainer.querySelector('.todo__saveBtn');
      const cancelBtn = todoFunctionsContainer.querySelector('.todo__cancelBtn');

      // hide the todo__text <span> and show an <input> with the todo text pre-populated
      todoSpan.toggleAttribute('hidden');
      editTodoInput.toggleAttribute('hidden');
      editTodoInput.value = todo;
      editTodoInput.focus();

      // hide the edit and delete buttons and show the save and cancel buttons
      editBtn.toggleAttribute('hidden');
      deleteBtn.toggleAttribute('hidden');
      saveBtn.toggleAttribute('hidden');
      cancelBtn.toggleAttribute('hidden');

      // handle any changes to the edit todo <input> field and save the changes
      // when the user clicks out of the input box or presses the enter key
      // this function is only used for the blur and keypress event listeners
      // on the <input> field when editing a todo.
      // the event listeners are removed in the editFormHandler function after
      // the user clicks out of the input box or presses the enter key to save the changes
      const editFormHandler = async (e) => {
        // if (e.type === 'blur') {
        //   todoSpan.toggleAttribute('hidden');
        //   editTodoInput.toggleAttribute('hidden');
        // }

        if (e.type === 'keypress') {
          if (e.key === 'Enter') {
            // e.target.removeEventListener('blur', editFormHandler);
            e.target.removeEventListener('keypress', editFormHandler);

            const todoSpan = e.target
              .closest('.completedInputContainer')
              .querySelector('.todo__text'); // the <span> element that contains the todo text
            const editedTodo = e.target.value;

            try {
              const res = await axios({
                method: 'patch',
                headers: { 'Content-Type': 'application/json' },
                url: `/api/todos/${id}`,
                data: { todo: editedTodo },
              });

              if (res.status === 200) {
                const newTodo = res.data.todo.todo;

                // replace todo__text <span> text with updated todo
                todoSpan.innerText = newTodo;
                todoSpan.toggleAttribute('hidden');

                // hide the input box
                e.target.toggleAttribute('hidden', true);

                // hide the save and cancel buttons and show the edit and delete buttons again
                editBtn.toggleAttribute('hidden');
                deleteBtn.toggleAttribute('hidden');
                saveBtn.toggleAttribute('hidden');
                cancelBtn.toggleAttribute('hidden');
              }
            } catch (e) {
              console.error('error: ', e);
            }
          }
        }
      };

      // add event listeners to the edit todo <input> field for when
      // the user clicks out of the input box or presses the enter key
      // editTodoInput.addEventListener('blur', editFormHandler);
      editTodoInput.addEventListener('keypress', editFormHandler);
    };

    // handle saving the todo after editing
    const saveEditedTodoHandler = async (e) => {
      const id = e.target.dataset.id;
      const container = document.getElementById(id);

      const todoSpan = container.querySelector('.todo__text');
      const todo = todoSpan.innerText;
      const editTodoInput = container.querySelector('.todo__editTodoInput');
      const editedTodo = editTodoInput.value;

      const todoFunctionsContainer = container.querySelector(
        '.todo__functionsContainer',
      );
      const editBtn = todoFunctionsContainer.querySelector('.todo__editBtn');
      const deleteBtn = todoFunctionsContainer.querySelector('.todo__deleteBtn');
      const cancelBtn = todoFunctionsContainer.querySelector('.todo__cancelBtn');
      const saveBtn = todoFunctionsContainer.querySelector('.todo__saveBtn');

      // if the edited todo is the same as the original todo
      // just toggle the visibility of the elements and return
      if (editedTodo.trim() === todo) {
        todoSpan.innerText = todo; // in case there are extra spaces, reset the text to the original todo
        editTodoInput.toggleAttribute('hidden');
        todoSpan.toggleAttribute('hidden');
        editBtn.toggleAttribute('hidden');
        deleteBtn.toggleAttribute('hidden');
        saveBtn.toggleAttribute('hidden');
        cancelBtn.toggleAttribute('hidden');
        return;
      }

      const loaderSpan = document.createElement('span');
      loaderSpan.classList.add('loader');

      // hide the save and cancel buttons and show the loader
      // edit and delete buttons are already hidden from when the user clicked the edit button
      saveBtn.toggleAttribute('hidden');
      cancelBtn.toggleAttribute('hidden');
      todoFunctionsContainer.appendChild(loaderSpan);

      try {
        const res = await axios({
          method: 'patch',
          headers: { 'Content-Type': 'application/json' },
          url: `/api/todos/${id}`,
          data: { todo: editedTodo },
        });

        if (res.status === 200) {
          const newTodo = res.data.todo.todo;

          // remove the <input> field and replace with new text
          todoSpan.innerText = newTodo;
          todoSpan.toggleAttribute('hidden');
          editTodoInput.toggleAttribute('hidden', true);

          // hide the loader and show the edit and delete buttons again
          todoFunctionsContainer.querySelector('.loader').remove();
          editBtn.toggleAttribute('hidden');
          deleteBtn.toggleAttribute('hidden');
        }
      } catch (e) {
        console.error('error: ', e);
      }
    };

    // handle canceling editing the todo
    const cancelEditHandler = (e) => {
      const id = e.target.dataset.id;
      const container = document.getElementById(id);
      const todoSpan = container.querySelector('.todo__text');
      const editTodoInput = container.querySelector('.todo__editTodoInput');

      // hide the input box and show the todo text again
      editTodoInput.toggleAttribute('hidden');
      todoSpan.toggleAttribute('hidden');

      // remove the save and cancel buttons and show the edit and delete buttons again
      const editBtn = container.querySelector('.todo__editBtn');
      const deleteBtn = container.querySelector('.todo__deleteBtn');
      const saveBtn = container.querySelector('.todo__saveBtn');
      const cancelBtn = container.querySelector('.todo__cancelBtn');

      editBtn.toggleAttribute('hidden');
      deleteBtn.toggleAttribute('hidden');
      saveBtn.toggleAttribute('hidden');
      cancelBtn.toggleAttribute('hidden');
    };

    // handle the deleting of the todo
    const deleteHandler = async (e) => {
      const id = e.target.dataset.id;
      const container = document.getElementById(id);

      const todoFunctionsContainer = container.querySelector(
        '.todo__functionsContainer',
      );
      const editBtn = todoFunctionsContainer.querySelector('.todo__editBtn');
      const deleteBtn = todoFunctionsContainer.querySelector('.todo__deleteBtn');

      const loaderSpan = document.createElement('span');
      loaderSpan.classList.add('loader');

      // hide the edit and delete buttons and show the loader
      editBtn.toggleAttribute('hidden');
      deleteBtn.toggleAttribute('hidden');
      todoFunctionsContainer.appendChild(loaderSpan);

      try {
        const res = await axios.delete(`/api/todos/${id}`);

        if (res.status === 200) {
          container.remove();
        }
      } catch (e) {
        console.error('error: ', e);
      }
    };

    /* ------------------------ event delegation ------------------------ */
    if (
      e.target.classList.contains('todo__doneBtn') ||
      e.target.classList.contains('todo__text')
    ) {
      doneHandler(e);
    }
    if (e.target.classList.contains('todo__editBtn')) {
      editHandler(e);
    }
    if (e.target.classList.contains('todo__saveBtn')) {
      saveEditedTodoHandler(e);
    }
    if (e.target.classList.contains('todo__cancelBtn')) {
      cancelEditHandler(e);
    }
    if (e.target.classList.contains('todo__deleteBtn')) {
      deleteHandler(e);
    }
  };

  // add click listener to add todo button
  addTodoButton && addTodoButton.addEventListener('click', handleAddTodo);

  // add click event listener to each todo item
  for (let todo of todos) {
    todo.addEventListener('click', handleClick);
  }

})();