/* ============================================
   Field Validation Helpers
   ============================================ */
function showFieldError(input, message) {
  if (!input) {
    return;
  }
  input.classList.add('input-error');
  input.classList.remove('input-success');
  input.setAttribute('aria-invalid', 'true');

  let errorNode = input.parentElement?.querySelector('.error-text');
  if (!errorNode) {
    errorNode = document.createElement('span');
    errorNode.className = 'error-text';
    if (input.parentElement) {
      input.parentElement.appendChild(errorNode);
    }
  }
  if (errorNode) {
    errorNode.textContent = _translateUiText(String(message || 'Invalid value'));
  }
}

function clearFieldError(input) {
  if (!input) {
    return;
  }
  input.classList.remove('input-error');
  input.removeAttribute('aria-invalid');
  const errorNode = input.parentElement?.querySelector('.error-text');
  if (errorNode) {
    errorNode.remove();
  }
}
