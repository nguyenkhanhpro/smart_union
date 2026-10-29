/* Component: xác nhận trước khi gửi form có thuộc tính data-confirm (dùng cho nút Xóa). */
(function () {
  const modalEl = document.getElementById('confirmModal');
  if (!modalEl) return;
  const modal = new bootstrap.Modal(modalEl);
  const message = document.getElementById('confirmModalMessage');
  const okButton = document.getElementById('confirmModalOk');
  let pendingForm = null;

  document.addEventListener('submit', (event) => {
    const form = event.target;
    if (!form.matches('form[data-confirm]') || form.dataset.confirmed) return;
    event.preventDefault();
    pendingForm = form;
    message.textContent = form.dataset.confirm;
    modal.show();
  });

  okButton.addEventListener('click', () => {
    if (!pendingForm) return;
    pendingForm.dataset.confirmed = '1';
    pendingForm.submit();
  });
})();
