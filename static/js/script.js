document.addEventListener("DOMContentLoaded", function () {
  // Password show/hide toggle
  document.querySelectorAll("[data-toggle-pw]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var inp = document.getElementById(btn.dataset.togglePw);
      if (!inp) return;
      var icon = btn.querySelector("i");
      if (inp.type === "password") {
        inp.type = "text";
        if (icon) icon.classList.replace("bi-eye", "bi-eye-slash");
      } else {
        inp.type = "password";
        if (icon) icon.classList.replace("bi-eye-slash", "bi-eye");
      }
    });
  });

  // Delete confirmation
  document.querySelectorAll("form.confirm-delete").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!confirm("Are you sure you want to delete this student? This cannot be undone."))
        e.preventDefault();
    });
  });

  // Auto-dismiss non-danger alerts after 5s
  setTimeout(function () {
    document.querySelectorAll(".alert:not(.alert-danger)").forEach(function (el) {
      var a = bootstrap.Alert.getOrCreateInstance(el);
      if (a) a.close();
    });
  }, 5000);
});
