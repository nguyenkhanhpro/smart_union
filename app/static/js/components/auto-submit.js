/* Component: form có data-auto-submit tự gửi khi người dùng đổi lựa chọn. */
document.querySelectorAll('form[data-auto-submit]').forEach((form) => {
  form.addEventListener('change', () => form.requestSubmit());
});
