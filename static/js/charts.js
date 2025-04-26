// Initialize Blood Sugar Chart
function initializeBloodSugarChart() {
  const ctx = document.getElementById('blood-sugar-chart');
  if (!ctx) return;

  // Default chart data
  const labels = [];
  const values = [];
  
  // Configure the chart
  window.bloodSugarChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Blood Sugar (mg/dL)',
        data: values,
        borderColor: '#4062bb',
        backgroundColor: 'rgba(64, 98, 187, 0.1)',
        tension: 0.4,
        fill: true,
        pointBackgroundColor: '#4062bb',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          position: 'top',
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          callbacks: {
            label: function(context) {
              const value = context.parsed.y;
              return `Blood Sugar: ${value} mg/dL`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          },
          ticks: {
            maxRotation: 45,
            minRotation: 45
          }
        },
        y: {
          beginAtZero: false,
          min: 40,
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          },
          ticks: {
            callback: function(value) {
              return value + ' mg/dL';
            }
          }
        }
      },
      interaction: {
        intersect: false,
        mode: 'index',
      },
      elements: {
        line: {
          borderWidth: 2
        }
      }
    }
  });
  
  // Fetch initial data
  updateBloodSugarChart();
}

// Update Blood Sugar Chart with new data
function updateBloodSugarChartData(chartData) {
  if (!window.bloodSugarChart || !chartData) return;
  
  // Process chart data
  const labels = [];
  const values = [];
  const dataByMealStatus = {
    'before_meal': [],
    'after_meal': [],
    'fasting': [],
    'unknown': []
  };
  
  // Group data by date for better display
  const groupedData = {};
  chartData.forEach(entry => {
    if (!groupedData[entry.date]) {
      groupedData[entry.date] = [];
    }
    groupedData[entry.date].push(entry);
  });
  
  // Create datasets based on meal status
  Object.keys(groupedData).forEach(date => {
    groupedData[date].forEach(entry => {
      labels.push(`${date} ${entry.time}`);
      values.push(entry.value);
      
      // Add to appropriate meal status dataset
      const status = entry.meal_status || 'unknown';
      if (dataByMealStatus[status]) {
        dataByMealStatus[status].push({
          x: `${date} ${entry.time}`,
          y: entry.value
        });
      } else {
        dataByMealStatus.unknown.push({
          x: `${date} ${entry.time}`,
          y: entry.value
        });
      }
    });
  });
  
  // Update the chart data
  window.bloodSugarChart.data.labels = labels;
  window.bloodSugarChart.data.datasets = [
    {
      label: 'Fasting',
      data: dataByMealStatus.fasting,
      borderColor: '#4062bb',
      backgroundColor: 'rgba(64, 98, 187, 0.1)',
      tension: 0.4,
      fill: false,
      pointBackgroundColor: '#4062bb',
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      pointRadius: 4,
      pointHoverRadius: 6
    },
    {
      label: 'Before Meal',
      data: dataByMealStatus.before_meal,
      borderColor: '#5a9367',
      backgroundColor: 'rgba(90, 147, 103, 0.1)',
      tension: 0.4,
      fill: false,
      pointBackgroundColor: '#5a9367',
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      pointRadius: 4,
      pointHoverRadius: 6
    },
    {
      label: 'After Meal',
      data: dataByMealStatus.after_meal,
      borderColor: '#f9c74f',
      backgroundColor: 'rgba(249, 199, 79, 0.1)',
      tension: 0.4,
      fill: false,
      pointBackgroundColor: '#f9c74f',
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      pointRadius: 4,
      pointHoverRadius: 6
    },
    {
      label: 'Other',
      data: dataByMealStatus.unknown,
      borderColor: '#6b7280',
      backgroundColor: 'rgba(107, 114, 128, 0.1)',
      tension: 0.4,
      fill: false,
      pointBackgroundColor: '#6b7280',
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      pointRadius: 4,
      pointHoverRadius: 6
    }
  ];
  
  // Add threshold lines
  window.bloodSugarChart.options.plugins.annotation = {
    annotations: {
      lowThresholdLine: {
        type: 'line',
        yMin: 70,
        yMax: 70,
        borderColor: '#dc2626',
        borderWidth: 2,
        borderDash: [6, 6],
        label: {
          content: 'Low',
          position: 'start',
          backgroundColor: 'rgba(220, 38, 38, 0.8)'
        }
      },
      highThresholdLine: {
        type: 'line',
        yMin: 180,
        yMax: 180,
        borderColor: '#dc2626',
        borderWidth: 2,
        borderDash: [6, 6],
        label: {
          content: 'High',
          position: 'start',
          backgroundColor: 'rgba(220, 38, 38, 0.8)'
        }
      },
      targetRangeArea: {
        type: 'box',
        yMin: 70,
        yMax: 180,
        backgroundColor: 'rgba(47, 173, 102, 0.1)',
        borderWidth: 0
      }
    }
  };
  
  // Update the chart
  window.bloodSugarChart.update();
}

// Initialize Weekly Progress Chart
function initializeWeeklyProgressChart() {
  const ctx = document.getElementById('weekly-progress-chart');
  if (!ctx) return;
  
  // Weekly data (to be replaced with real data)
  const data = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        label: 'In Range %',
        data: [65, 72, 68, 80, 74, 85, 78],
        backgroundColor: '#2fad66',
        borderRadius: 4,
      }
    ]
  };
  
  // Configure the chart
  const weeklyProgressChart = new Chart(ctx, {
    type: 'bar',
    data: data,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `In Range: ${context.parsed.y}%`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          }
        },
        y: {
          beginAtZero: true,
          max: 100,
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          },
          ticks: {
            callback: function(value) {
              return value + '%';
            }
          }
        }
      }
    }
  });
}

// Initialize Carbohydrates and Insulin Chart
function initializeCarbohydratesInsulinChart() {
  const ctx = document.getElementById('carbs-insulin-chart');
  if (!ctx) return;
  
  // Sample data (to be replaced with real data)
  const data = {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      {
        label: 'Carbohydrates (g)',
        data: [120, 150, 135, 110, 145, 160, 130],
        backgroundColor: '#f9c74f',
        borderRadius: 4,
        order: 2
      },
      {
        label: 'Insulin (units)',
        data: [20, 24, 22, 18, 25, 26, 21],
        borderColor: '#4062bb',
        backgroundColor: 'transparent',
        type: 'line',
        tension: 0.4,
        order: 1
      }
    ]
  };
  
  // Configure the chart
  const carbsInsulinChart = new Chart(ctx, {
    type: 'bar',
    data: data,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top'
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          }
        },
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          }
        }
      }
    }
  });
}

// Initialize A1C History Chart
function initializeA1CHistoryChart() {
  const ctx = document.getElementById('a1c-history-chart');
  if (!ctx) return;
  
  // Sample data (to be replaced with real data)
  const data = {
    labels: ['Jan', 'Mar', 'Jun', 'Sep', 'Dec'],
    datasets: [
      {
        label: 'A1C %',
        data: [7.8, 7.5, 7.3, 7.0, 6.8],
        borderColor: '#5a9367',
        backgroundColor: 'rgba(90, 147, 103, 0.1)',
        tension: 0.4,
        fill: true
      }
    ]
  };
  
  // Configure the chart
  const a1cHistoryChart = new Chart(ctx, {
    type: 'line',
    data: data,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          }
        },
        y: {
          beginAtZero: false,
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          },
          ticks: {
            callback: function(value) {
              return value + '%';
            }
          }
        }
      }
    }
  });
}
