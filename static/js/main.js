document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.querySelector("#upload-form input[type='file']");
    const hint = document.getElementById("file-hint");
    if (!fileInput || !hint) {
        return;
    }

    fileInput.addEventListener("change", () => {
        const file = fileInput.files[0];
        if (!file) {
            hint.textContent = "";
            return;
        }
        const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
        const allowed = [".pdf", ".docx"];
        const name = file.name.toLowerCase();
        const okType = allowed.some((ext) => name.endsWith(ext));
        if (!okType) {
            hint.textContent = "Выбран файл недопустимого типа. На сервере будут приняты только PDF и DOCX.";
            return;
        }
        if (file.size > 10 * 1024 * 1024) {
            hint.textContent = `Файл слишком большой (${sizeMb} МБ). Максимум 10 МБ.`;
            return;
        }
        hint.textContent = `Выбран файл: ${file.name} (${sizeMb} МБ)`;
    });
});
