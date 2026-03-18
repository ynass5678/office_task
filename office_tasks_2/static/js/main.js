// static/js/main.js

document.addEventListener("DOMContentLoaded", () => {
    // Переключение между входом и регистрацией в модальном окне авторизации
    const authForms = document.querySelector(".auth-forms");
    const showRegister = document.getElementById("showRegister");
    const showLogin = document.getElementById("showLogin");

    if (authForms) {
        if (showRegister) {
            showRegister.addEventListener("click", (e) => {
                e.preventDefault();
                authForms.dataset.mode = "register";
            });
        }

        if (showLogin) {
            showLogin.addEventListener("click", (e) => {
                e.preventDefault();
                authForms.dataset.mode = "login";
            });
        }
    }

    // Модальное окно создания задачи
    const taskModal = document.getElementById("taskModal");
    const openTaskModalBtn = document.getElementById("openTaskModal");
    const closeTaskModalBtn = document.getElementById("closeTaskModal");

    if (openTaskModalBtn && taskModal) {
        openTaskModalBtn.addEventListener("click", () => {
            taskModal.classList.remove("hidden");
        });
    }

    if (closeTaskModalBtn && taskModal) {
        closeTaskModalBtn.addEventListener("click", () => {
            taskModal.classList.add("hidden");
        });
    }

    if (taskModal) {
        taskModal.addEventListener("click", (e) => {
            if (e.target === taskModal) {
                taskModal.classList.add("hidden");
            }
        });
    }
});
