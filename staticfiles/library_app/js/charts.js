/* LibraryGIS — charts.js  |  Blue theme */
const C = {
  primary: '#1e6fbf', sky: '#0284c7', teal: '#0891b2',
  green: '#16a34a', red: '#dc2626', orange: '#d97706', purple: '#7c3aed',
  text2: '#64748b', text3: '#94a3b8', grid: 'rgba(226,232,240,.8)',
  primaryBg: 'rgba(30,111,191,.08)', tealBg: 'rgba(8,145,178,.07)',
};

const BASE = {
  responsive: true,
  plugins: { legend: { labels: { color: C.text2, font: { family: 'Inter', size: 11 } } } },
  scales: {
    y: { ticks: { color: C.text3 }, grid: { color: C.grid }, beginAtZero: true },
    x: { ticks: { color: C.text3 }, grid: { display: false } },
  },
};
const PIE = {
  responsive: true,
  plugins: { legend: { position: 'bottom', labels: { color: C.text2, font: { size: 11 }, padding: 10 } } },
};

function makeTrendChart(id, data) {
  return new Chart(id, { type: 'line', data: {
    labels: data.map(d => d.month),
    datasets: [
      { label: 'Mượn', data: data.map(d => d.borrowed), borderColor: C.primary, backgroundColor: C.primaryBg, tension: .4, fill: true, pointRadius: 3 },
      { label: 'Trả',  data: data.map(d => d.returned), borderColor: C.teal,    backgroundColor: C.tealBg,    tension: .4, fill: true, pointRadius: 3 },
    ]
  }, options: BASE });
}

function makeBranchChart(id, data) {
  return new Chart(id, { type: 'bar', data: {
    labels: data.map(b => b.name),
    datasets: [
      { label: 'Sách',       data: data.map(b => b.books),   backgroundColor: 'rgba(30,111,191,.35)',  borderColor: C.primary, borderWidth: 1, borderRadius: 4 },
      { label: 'Lượt mượn', data: data.map(b => b.borrows), backgroundColor: 'rgba(8,145,178,.35)',   borderColor: C.teal,    borderWidth: 1, borderRadius: 4 },
    ]
  }, options: BASE });
}

function makeCategoryChart(id, data) {
  const colors = [C.primary, C.teal, C.sky, C.green, C.orange, C.purple, C.red, '#8b5cf6'];
  return new Chart(id, { type: 'doughnut', data: {
    labels: data.map(c => c.name),
    datasets: [{ data: data.map(c => c.cnt), backgroundColor: colors.map(c => c + 'cc'), borderColor: colors, borderWidth: 2 }]
  }, options: PIE });
}

function makeFineChart(id, data) {
  return new Chart(id, { type: 'bar', data: {
    labels: data.map(d => d.month),
    datasets: [{ label: 'Phí phạt (đ)', data: data.map(d => d.total), backgroundColor: 'rgba(220,38,38,.25)', borderColor: C.red, borderWidth: 2, borderRadius: 5 }]
  }, options: BASE });
}

function makeDailyChart(id, data) {
  return new Chart(id, { type: 'line', data: {
    labels: data.map(d => d.date),
    datasets: [
      { label: 'Mượn', data: data.map(d => d.borrowed), borderColor: C.primary, backgroundColor: C.primaryBg, tension: .4, fill: true, pointRadius: 2 },
      { label: 'Trả',  data: data.map(d => d.returned), borderColor: C.teal,    backgroundColor: C.tealBg,    tension: .4, fill: true, pointRadius: 2 },
    ]
  }, options: BASE });
}

function makeAgingChart(id, labels, values) {
  return new Chart(id, { type: 'doughnut', data: {
    labels,
    datasets: [{ data: values, backgroundColor: ['rgba(22,163,74,.75)','rgba(217,119,6,.75)','rgba(220,38,38,.55)','rgba(220,38,38,.9)'], borderWidth: 0 }]
  }, options: PIE });
}

