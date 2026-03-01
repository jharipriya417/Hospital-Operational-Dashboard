
const COLORS = {
  blue:   '#3b82f6',
  green:  '#10b981',
  red:    '#ef4444',
  orange: '#f97316',
  yellow: '#f59e0b',
  purple: '#8b5cf6',
  teal:   '#14b8a6',
  pink:   '#ec4899',
  text:   '#94a3b8',
  grid:   'rgba(42,51,71,0.8)',
  bg:     '#1e2535',
};

const DEPT_COLORS = {
  ICU:       COLORS.red,
  OPD:       COLORS.blue,
  Emergency: COLORS.orange,
  Radiology: COLORS.purple,
  Surgery:   COLORS.teal,
};

const CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: {
        color: COLORS.text,
        font: { family: 'Inter', size: 11 },
        boxWidth: 12,
        padding: 16,
      }
    },
    tooltip: {
      backgroundColor: '#0f1117',
      borderColor: '#2a3347',
      borderWidth: 1,
      titleColor: '#f1f5f9',
      bodyColor: '#94a3b8',
      padding: 10,
      cornerRadius: 8,
    }
  },
  scales: {
    x: {
      ticks: { color: COLORS.text, font: { family: 'Inter', size: 10 } },
      grid:  { color: COLORS.grid },
    },
    y: {
      ticks: { color: COLORS.text, font: { family: 'Inter', size: 10 } },
      grid:  { color: COLORS.grid },
    }
  }
};

function mergeDeep(target, source) {
  const result = Object.assign({}, target);
  for (const key in source) {
    if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
      result[key] = mergeDeep(target[key] || {}, source[key]);
    } else {
      result[key] = source[key];
    }
  }
  return result;
}

function chartOpts(overrides = {}) {
  return mergeDeep(CHART_DEFAULTS, overrides);
}

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}


function showSection(sectionId, navEl) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const section = document.getElementById(sectionId);
  if (section) section.classList.add('active');
  if (navEl) navEl.classList.add('active');
}


const chartInstances = {};

function destroyChart(id) {
  if (chartInstances[id]) {
    chartInstances[id].destroy();
    delete chartInstances[id];
  }
}

function createChart(id, config) {
  destroyChart(id);
  const canvas = document.getElementById(id);
  if (!canvas) return null;
  const chart = new Chart(canvas, config);
  chartInstances[id] = chart;
  return chart;
}

function renderPatientVolumeChart(deptOverview) {
  const labels = deptOverview.map(d => d.department);
  const admitted = deptOverview.map(d => d.patients_admitted);
  const emergency = deptOverview.map(d => d.emergency_cases);
  const pending = deptOverview.map(d => d.pending_cases);

  createChart('patientVolumeChart', {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Admitted',
          data: admitted,
          backgroundColor: labels.map(l => hexToRgba(DEPT_COLORS[l] || COLORS.blue, 0.75)),
          borderColor: labels.map(l => DEPT_COLORS[l] || COLORS.blue),
          borderWidth: 1,
          borderRadius: 5,
        },
        {
          label: 'Emergency',
          data: emergency,
          backgroundColor: hexToRgba(COLORS.red, 0.5),
          borderColor: COLORS.red,
          borderWidth: 1,
          borderRadius: 5,
        },
        {
          label: 'Pending',
          data: pending,
          backgroundColor: hexToRgba(COLORS.orange, 0.5),
          borderColor: COLORS.orange,
          borderWidth: 1,
          borderRadius: 5,
        }
      ]
    },
    options: chartOpts({ plugins: { legend: { position: 'top' } } })
  });
}


function renderBedUtilChart(deptOverview) {
  const labels = deptOverview.map(d => d.department);
  const bedUtils = deptOverview.map(d => d.bed_util_pct);
  const colors = labels.map(l => DEPT_COLORS[l] || COLORS.blue);

  createChart('bedUtilChart', {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: bedUtils,
        backgroundColor: colors.map(c => hexToRgba(c, 0.8)),
        borderColor: colors,
        borderWidth: 2,
        hoverOffset: 6,
      }]
    },
    options: chartOpts({
      plugins: {
        legend: { position: 'bottom' },
        tooltip: {
          callbacks: {
            label: ctx => ` ${ctx.label}: ${ctx.raw}% bed utilization`
          }
        }
      },
      scales: { x: { display: false }, y: { display: false } }
    })
  });
}

function renderResolutionChart(deptOverview) {
  const labels = deptOverview.map(d => d.department);
  const resolution = deptOverview.map(d => d.avg_resolution);
  const pending = deptOverview.map(d => d.pending_cases);

  createChart('resolutionChart', {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Avg Resolution (hrs)',
          data: resolution,
          backgroundColor: hexToRgba(COLORS.purple, 0.7),
          borderColor: COLORS.purple,
          borderWidth: 1,
          borderRadius: 5,
          yAxisID: 'y',
        },
        {
          label: 'Pending Cases',
          data: pending,
          type: 'line',
          borderColor: COLORS.orange,
          backgroundColor: hexToRgba(COLORS.orange, 0.15),
          fill: true,
          tension: 0.4,
          pointBackgroundColor: COLORS.orange,
          pointRadius: 5,
          yAxisID: 'y1',
        }
      ]
    },
    options: chartOpts({
      plugins: { legend: { position: 'top' } },
      scales: {
        y:  { position: 'left',  ticks: { color: COLORS.text }, grid: { color: COLORS.grid } },
        y1: { position: 'right', ticks: { color: COLORS.text }, grid: { drawOnChartArea: false } }
      }
    })
  });
}

function renderEmergencyRatioChart(deptOverview) {
  const labels = deptOverview.map(d => d.department);
  const ratios = deptOverview.map(d =>
    Math.round((d.emergency_cases / Math.max(d.patients_admitted, 1)) * 100)
  );

  createChart('emergencyRatioChart', {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Emergency %',
        data: ratios,
        backgroundColor: ratios.map(r =>
          r >= 80 ? hexToRgba(COLORS.red, 0.75) :
          r >= 50 ? hexToRgba(COLORS.orange, 0.75) :
                    hexToRgba(COLORS.green, 0.75)
        ),
        borderColor: ratios.map(r =>
          r >= 80 ? COLORS.red : r >= 50 ? COLORS.orange : COLORS.green
        ),
        borderWidth: 1,
        borderRadius: 5,
      }]
    },
    options: chartOpts({
      indexAxis: 'y',
      plugins: { legend: { display: false } },
      scales: {
        x: { max: 100, ticks: { callback: v => v + '%', color: COLORS.text }, grid: { color: COLORS.grid } },
        y: { ticks: { color: COLORS.text }, grid: { color: COLORS.grid } }
      }
    })
  });
}


function renderStressCompareChart(deptStress) {
  const labels = ['Patient/Staff', 'Emergency Load', 'Bed Utilization'];
  const datasets = deptStress.map(s => ({
    label: s.department,
    data: [s.ps_score, s.em_score, s.bed_score],
    borderColor: DEPT_COLORS[s.department] || COLORS.blue,
    backgroundColor: hexToRgba(DEPT_COLORS[s.department] || COLORS.blue, 0.15),
    pointBackgroundColor: DEPT_COLORS[s.department] || COLORS.blue,
    borderWidth: 2,
    pointRadius: 4,
  }));

  createChart('stressCompareChart', {
    type: 'radar',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: COLORS.text, font: { family: 'Inter', size: 11 }, boxWidth: 12, padding: 16 }
        },
        tooltip: {
          backgroundColor: '#0f1117',
          borderColor: '#2a3347',
          borderWidth: 1,
          titleColor: '#f1f5f9',
          bodyColor: '#94a3b8',
        }
      },
      scales: {
        r: {
          min: 0, max: 100,
          ticks: { color: COLORS.text, backdropColor: 'transparent', font: { size: 10 } },
          grid:  { color: COLORS.grid },
          pointLabels: { color: COLORS.text, font: { family: 'Inter', size: 11 } },
          angleLines: { color: COLORS.grid },
        }
      }
    }
  });
}

function renderAdmissionTrendChart(trendData) {
  const datasets = trendData.departments.map(dept => ({
    label: dept,
    data: trendData.patient_trends[dept],
    borderColor: DEPT_COLORS[dept] || COLORS.blue,
    backgroundColor: hexToRgba(DEPT_COLORS[dept] || COLORS.blue, 0.08),
    fill: false,
    tension: 0.4,
    pointRadius: 2,
    pointHoverRadius: 5,
    borderWidth: 2,
  }));

  createChart('admissionTrendChart', {
    type: 'line',
    data: { labels: trendData.dates.map(d => d.slice(5)), datasets },
    options: chartOpts({ plugins: { legend: { position: 'top' } } })
  });
}

function renderEmergencyTrendChart(trendData) {
  const datasets = trendData.departments.map(dept => ({
    label: dept,
    data: trendData.emergency_trends[dept],
    borderColor: DEPT_COLORS[dept] || COLORS.blue,
    backgroundColor: 'transparent',
    fill: false,
    tension: 0.4,
    pointRadius: 2,
    borderWidth: 2,
  }));

  createChart('emergencyTrendChart', {
    type: 'line',
    data: { labels: trendData.dates.map(d => d.slice(5)), datasets },
    options: chartOpts({ plugins: { legend: { position: 'top' } } })
  });
}

function renderPendingTrendChart(trendData) {
  const datasets = trendData.departments.map(dept => ({
    label: dept,
    data: trendData.pending_trends[dept],
    borderColor: DEPT_COLORS[dept] || COLORS.blue,
    backgroundColor: hexToRgba(DEPT_COLORS[dept] || COLORS.blue, 0.1),
    fill: true,
    tension: 0.4,
    pointRadius: 2,
    borderWidth: 2,
  }));

  createChart('pendingTrendChart', {
    type: 'line',
    data: { labels: trendData.dates.map(d => d.slice(5)), datasets },
    options: chartOpts({ plugins: { legend: { position: 'top' } } })
  });
}

function renderForecastChart(forecastData) {
  const departments = Object.keys(forecastData);
  if (!departments.length) return;

  const firstDept = forecastData[departments[0]];
  const histDates = firstDept.historical_dates.map(d => d.slice(5));

 
  const lastDate = new Date(firstDept.historical_dates[firstDept.historical_dates.length - 1]);
  const futureDates = [1, 2, 3].map(i => {
    const d = new Date(lastDate);
    d.setDate(d.getDate() + i);
    return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  });

  const allLabels = [...histDates, ...futureDates];

  const datasets = [];
  departments.forEach(dept => {
    const color = DEPT_COLORS[dept] || COLORS.blue;
    const hist = forecastData[dept].historical_values;
    const forecast = forecastData[dept].forecast_values;

  
    datasets.push({
      label: `${dept}`,
      data: [...hist, null, null, null],
      borderColor: color,
      backgroundColor: 'transparent',
      fill: false,
      tension: 0.4,
      pointRadius: 2,
      borderWidth: 2,
    });

    const forecastData_ = new Array(hist.length - 1).fill(null);
    forecastData_.push(hist[hist.length - 1]);
    forecastData_.push(...forecast);

    datasets.push({
      label: `${dept} (forecast)`,
      data: forecastData_,
      borderColor: color,
      backgroundColor: hexToRgba(color, 0.1),
      fill: false,
      tension: 0.4,
      pointRadius: 3,
      borderWidth: 2,
      borderDash: [6, 4],
    });
  });

  createChart('forecastChart', {
    type: 'line',
    data: { labels: allLabels, datasets },
    options: chartOpts({
      plugins: {
        legend: {
          position: 'top',
          labels: {
            filter: item => !item.text.includes('(forecast)') || true,
            color: COLORS.text,
            font: { family: 'Inter', size: 10 },
            boxWidth: 12,
            padding: 12,
          }
        }
      }
    })
  });
}


async function initDashboard(deptStress, deptOverview) {

  renderPatientVolumeChart(deptOverview);
  renderBedUtilChart(deptOverview);
  renderStressCompareChart(deptStress);
  renderResolutionChart(deptOverview);
  renderEmergencyRatioChart(deptOverview);

  try {
    const [trendResp, forecastResp] = await Promise.all([
      fetch('/api/trends'),
      fetch('/api/forecast'),
    ]);
    const trendData    = await trendResp.json();
    const forecastData = await forecastResp.json();

    renderAdmissionTrendChart(trendData);
    renderEmergencyTrendChart(trendData);
    renderPendingTrendChart(trendData);
    renderForecastChart(forecastData);
  } catch (err) {
    console.error('Failed to load chart data:', err);
  }
}
