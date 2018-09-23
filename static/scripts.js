// Check validity of form
function checkFormValidity() {
  'use strict';
  window.addEventListener('load', function() {
    // Fetch all forms to apply Bootstrap validation
    var forms = document.getElementsByClassName('needs-validation');
    // Loop using Array.filter() to prevent submission without validation
    var validation = Array.prototype.filter.call(forms, function(form) {
      // Add event listener for submit
      form.addEventListener('submit', function(event) {
        var loginPassword = document.getElementById("loginPassword");
        // If it's still not validated, stop default actions
        if(form.checkValidity() === false) {
          event.preventDefault();
          event.stopPropagation();
        }
        // Else, assign it was-validated class
        form.classList.add('was-validated');
      }, false);
    });
  }, false);
}

// Call checkFormValidity()
checkFormValidity();

// Set timeout for flash messages
setTimeout(function() {
  $('.alert').remove();
}, 3000);
