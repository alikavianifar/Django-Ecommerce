document.addEventListener("DOMContentLoaded", function () {
    const inputElems = document.querySelectorAll('input[type="file"][name$="file"]');

    inputElems.forEach(function (input) {
        input.setAttribute('multiple', 'multiple');
    });

    inputElems.forEach(function (input) {
        input.addEventListener("change", function (event) {
            const files = event.target.files;
            if (files.length > 1) {
                const container = input.closest('.inline-related');
                for (let i = 1; i < files.length; i++) {
                    const addBtn = document.querySelector('.add-row a');
                    if (addBtn) addBtn.click();

                    const newInput = document.querySelectorAll('input[type="file"][name$="file"]')[i];
                    newInput.files = (function () {
                        const dt = new DataTransfer();
                        dt.items.add(files[i]);
                        return dt.files;
                    })();
                }
            }
        });
    });

    const setupDeleteButtons = () => {
        document.querySelectorAll('.inline-related').forEach(function (formset) {
            const deleteCheckbox = formset.querySelector('input[type="checkbox"][name$="DELETE"]');

            if (deleteCheckbox && !formset.querySelector('.custom-delete-btn')) {
                deleteCheckbox.style.display = 'none';

                const deleteLabel = deleteCheckbox.parentNode.querySelector('label');
                if (deleteLabel) deleteLabel.remove();

                const deleteBtn = document.createElement('button');
                deleteBtn.type = 'button';
                deleteBtn.innerText = '🗑️ Delete';
                deleteBtn.className = 'custom-delete-btn';
                deleteCheckbox.parentNode.appendChild(deleteBtn);

                deleteBtn.addEventListener('click', function () {
                    if (deleteCheckbox.checked) {
                        deleteCheckbox.checked = false;
                        formset.style.opacity = '1';
                        deleteBtn.innerText = '🗑️ Delete';
                        deleteBtn.style.backgroundColor = '#dc3545';
                    } else {
                        deleteCheckbox.checked = true;
                        formset.style.opacity = '0.5';
                        deleteBtn.innerText = '🔄 Undo';
                        deleteBtn.style.backgroundColor = '#6c757d';
                    }
                });
            }
        });
    };

    setupDeleteButtons();

    const observer = new MutationObserver(setupDeleteButtons);
    observer.observe(document.body, { childList: true, subtree: true });
});
