document.addEventListener('DOMContentLoaded', function() {
  // Initialize charts
  initializeCharts();
  
  // Handle date range selector for blood sugar chart
  const dateRangeSelector = document.getElementById('date-range-selector');
  if (dateRangeSelector) {
    dateRangeSelector.addEventListener('change', function() {
      const days = this.value;
      updateBloodSugarChart(days);
    });
  }

  // Initialize tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
  
  // Medication reminders toggle
  const medicationToggleButtons = document.querySelectorAll('.medication-toggle');
  if (medicationToggleButtons) {
    medicationToggleButtons.forEach(button => {
      button.addEventListener('click', function() {
        const medicationId = this.getAttribute('data-medication-id');
        toggleMedication(medicationId);
      });
    });
  }

  // Handle modal form submissions
  const addBloodSugarForm = document.getElementById('add-blood-sugar-form');
  if (addBloodSugarForm) {
    addBloodSugarForm.addEventListener('submit', function(event) {
      if (!validateBloodSugarForm()) {
        event.preventDefault();
      }
    });
  }
  
  // Set current date and time for blood sugar form
  const measuredAtDateInput = document.getElementById('measured_at_date');
  const measuredAtTimeInput = document.getElementById('measured_at_time');
  
  if (measuredAtDateInput && measuredAtTimeInput) {
    const now = new Date();
    const dateString = now.toISOString().substring(0, 10); // YYYY-MM-DD
    
    // Format time as HH:MM
    let hours = now.getHours().toString().padStart(2, '0');
    let minutes = now.getMinutes().toString().padStart(2, '0');
    const timeString = `${hours}:${minutes}`;
    
    measuredAtDateInput.value = dateString;
    measuredAtTimeInput.value = timeString;
  }
});

// Initialize dashboard charts
function initializeCharts() {
  // Blood sugar chart
  initializeBloodSugarChart();
  
  // Weekly progress chart
  initializeWeeklyProgressChart();
}

// Fetch blood sugar data from the API
function updateBloodSugarChart(days = 30) {
  const bloodSugarChartContainer = document.getElementById('blood-sugar-chart');
  if (!bloodSugarChartContainer) return;
  
  // Show loading state
  bloodSugarChartContainer.classList.add('loading');
  
  // Fetch data from API
  fetch(`/api/blood-sugar-data?days=${days}`)
    .then(response => response.json())
    .then(data => {
      // Remove loading state
      bloodSugarChartContainer.classList.remove('loading');
      
      // Update chart with new data
      updateBloodSugarChartData(data.chart_data);
      
      // Update statistics
      updateStatistics(data.statistics);
    })
    .catch(error => {
      console.error('Error fetching blood sugar data:', error);
      bloodSugarChartContainer.classList.remove('loading');
      bloodSugarChartContainer.innerHTML = '<div class="alert alert-danger">Failed to load blood sugar data</div>';
    });
}

// Update statistics display
function updateStatistics(statistics) {
  // Update average blood sugar
  const avgElement = document.getElementById('avg-blood-sugar');
  if (avgElement) {
    avgElement.textContent = statistics.average;
  }
  
  // Update in-range percentage
  const inRangeElement = document.getElementById('in-range-percentage');
  if (inRangeElement) {
    inRangeElement.textContent = `${statistics.in_range_percentage}%`;
    
    // Update progress circle
    const progressCircle = document.querySelector('.progress-circle-prog');
    if (progressCircle) {
      const radius = progressCircle.r.baseVal.value;
      const circumference = radius * 2 * Math.PI;
      const offset = circumference - (statistics.in_range_percentage / 100) * circumference;
      progressCircle.style.strokeDasharray = `${circumference} ${circumference}`;
      progressCircle.style.strokeDashoffset = offset;
    }
  }
  
  // Update readings count
  const readingsElement = document.getElementById('readings-count');
  if (readingsElement) {
    readingsElement.textContent = statistics.readings_count;
  }
  
  // Update high and low counts
  const highElement = document.getElementById('high-count');
  if (highElement) {
    highElement.textContent = statistics.high_count;
  }
  
  const lowElement = document.getElementById('low-count');
  if (lowElement) {
    lowElement.textContent = statistics.low_count;
  }
}

// Validate blood sugar form
function validateBloodSugarForm() {
  const valueInput = document.getElementById('blood_sugar_value');
  const value = parseFloat(valueInput.value);
  
  if (isNaN(value) || value <= 0) {
    valueInput.classList.add('is-invalid');
    return false;
  }
  
  valueInput.classList.remove('is-invalid');
  return true;
}

// Toggle medication active status
function toggleMedication(medicationId) {
  const form = document.getElementById(`toggle-medication-form-${medicationId}`);
  if (form) {
    form.submit();
  }
}
