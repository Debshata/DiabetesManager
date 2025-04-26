document.addEventListener('DOMContentLoaded', function() {
  // Handle form validation
  const profileForm = document.getElementById('profile-form');
  if (profileForm) {
    profileForm.addEventListener('submit', validateProfileForm);
  }

  const passwordForm = document.getElementById('password-form');
  if (passwordForm) {
    passwordForm.addEventListener('submit', validatePasswordForm);
  }

  // Initialize date picker for diagnosed date
  const diagnosedDateInput = document.getElementById('diagnosed_date');
  if (diagnosedDateInput) {
    // You could initialize a date picker here if needed
    // For now we'll use the browser's native date input
  }

  // Auto-calculate BMI when height or weight changes
  const heightInput = document.getElementById('height');
  const weightInput = document.getElementById('weight');
  const bmiOutput = document.getElementById('bmi-value');

  if (heightInput && weightInput && bmiOutput) {
    heightInput.addEventListener('input', updateBMI);
    weightInput.addEventListener('input', updateBMI);
    
    // Calculate initial BMI if values exist
    updateBMI();
  }
});

// Validate profile form
function validateProfileForm(event) {
  let isValid = true;
  
  // Get form fields
  const heightInput = document.getElementById('height');
  const weightInput = document.getElementById('weight');
  const ageInput = document.getElementById('age');
  
  // Validate height (must be a positive number)
  if (heightInput && heightInput.value) {
    const height = parseFloat(heightInput.value);
    if (isNaN(height) || height <= 0 || height > 300) {
      showError(heightInput, 'Please enter a valid height (1-300 cm)');
      isValid = false;
    } else {
      clearError(heightInput);
    }
  }
  
  // Validate weight (must be a positive number)
  if (weightInput && weightInput.value) {
    const weight = parseFloat(weightInput.value);
    if (isNaN(weight) || weight <= 0 || weight > 500) {
      showError(weightInput, 'Please enter a valid weight (1-500 kg)');
      isValid = false;
    } else {
      clearError(weightInput);
    }
  }
  
  // Validate age (must be a positive integer)
  if (ageInput && ageInput.value) {
    const age = parseInt(ageInput.value);
    if (isNaN(age) || age <= 0 || age > 120) {
      showError(ageInput, 'Please enter a valid age (1-120 years)');
      isValid = false;
    } else {
      clearError(ageInput);
    }
  }
  
  if (!isValid) {
    event.preventDefault();
  }
}

// Validate password form
function validatePasswordForm(event) {
  let isValid = true;
  
  // Get form fields
  const currentPasswordInput = document.getElementById('current_password');
  const newPasswordInput = document.getElementById('new_password');
  const confirmPasswordInput = document.getElementById('confirm_password');
  
  // Validate current password (must not be empty)
  if (!currentPasswordInput.value.trim()) {
    showError(currentPasswordInput, 'Please enter your current password');
    isValid = false;
  } else {
    clearError(currentPasswordInput);
  }
  
  // Validate new password (must be at least 8 characters)
  if (newPasswordInput.value.length < 8) {
    showError(newPasswordInput, 'Password must be at least 8 characters');
    isValid = false;
  } else {
    clearError(newPasswordInput);
  }
  
  // Validate password confirmation (must match new password)
  if (newPasswordInput.value !== confirmPasswordInput.value) {
    showError(confirmPasswordInput, 'Passwords do not match');
    isValid = false;
  } else {
    clearError(confirmPasswordInput);
  }
  
  if (!isValid) {
    event.preventDefault();
  }
}

// Calculate and update BMI
function updateBMI() {
  const heightInput = document.getElementById('height');
  const weightInput = document.getElementById('weight');
  const bmiOutput = document.getElementById('bmi-value');
  const bmiCategory = document.getElementById('bmi-category');
  
  if (!heightInput || !weightInput || !bmiOutput) return;
  
  const height = parseFloat(heightInput.value);
  const weight = parseFloat(weightInput.value);
  
  if (isNaN(height) || isNaN(weight) || height <= 0 || weight <= 0) {
    bmiOutput.textContent = '--';
    if (bmiCategory) {
      bmiCategory.textContent = '';
      bmiCategory.className = '';
    }
    return;
  }
  
  // Calculate BMI: weight(kg) / height²(m)
  const heightInMeters = height / 100;
  const bmi = weight / (heightInMeters * heightInMeters);
  const roundedBmi = Math.round(bmi * 10) / 10;
  
  bmiOutput.textContent = roundedBmi;
  
  // Set BMI category and color
  if (bmiCategory) {
    let category = '';
    let className = '';
    
    if (bmi < 18.5) {
      category = 'Underweight';
      className = 'text-warning';
    } else if (bmi < 25) {
      category = 'Normal';
      className = 'text-success';
    } else if (bmi < 30) {
      category = 'Overweight';
      className = 'text-warning';
    } else {
      category = 'Obese';
      className = 'text-danger';
    }
    
    bmiCategory.textContent = category;
    bmiCategory.className = className;
  }
}

// Show error message for an input
function showError(input, message) {
  const formGroup = input.closest('.mb-3');
  const errorElement = formGroup.querySelector('.invalid-feedback') || document.createElement('div');
  
  errorElement.className = 'invalid-feedback';
  errorElement.textContent = message;
  
  if (!formGroup.querySelector('.invalid-feedback')) {
    input.parentNode.appendChild(errorElement);
  }
  
  input.classList.add('is-invalid');
}

// Clear error message for an input
function clearError(input) {
  input.classList.remove('is-invalid');
}
