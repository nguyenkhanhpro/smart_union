/* Component: <canvas data-chart="trend|criteria" data-src="/api/..."> tự tải JSON và vẽ biểu đồ. */
(function () {
  if (typeof Chart === 'undefined') return;
  const PALETTE = ['#16213e', '#c8102e', '#1f7a52', '#f5b700', '#6c7a96'];
  Chart.defaults.font.family = '"Be Vietnam Pro", system-ui, sans-serif';
  Chart.defaults.color = '#5b6784';

  const builders = {
    trend: (data) => ({
      type: 'line',
      data: {
        labels: data.labels,
        datasets: data.datasets.map((d, i) => ({
          label: d.label, data: d.data, borderColor: PALETTE[i % PALETTE.length],
          backgroundColor: PALETTE[i % PALETTE.length], borderWidth: 2, tension: 0.3, pointRadius: 3,
        })),
      },
      options: baseOptions({ legend: true }),
      isEmpty: !data.datasets.some((d) => d.data.some((v) => v !== 0)),
    }),
    criteria: (data) => ({
      type: 'bar',
      data: {
        labels: data.labels,
        datasets: [
          { label: 'Điểm cộng', data: data.positive, backgroundColor: '#1f7a52', borderRadius: 4 },
          { label: 'Điểm trừ', data: data.negative, backgroundColor: '#c8102e', borderRadius: 4 },
        ],
      },
      options: baseOptions({ legend: true }),
      isEmpty: ![...data.positive, ...data.negative].some((v) => v !== 0),
    }),
  };

  function baseOptions({ legend }) {
    return {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: { legend: { display: legend, position: 'bottom', labels: { usePointStyle: true, boxWidth: 8 } } },
      scales: { y: { grid: { color: '#eef1f6' } }, x: { grid: { display: false } } },
    };
  }

  function showMessage(canvas, text) {
    const box = document.createElement('div');
    box.className = 'chart-empty';
    box.textContent = text;
    canvas.replaceWith(box);
  }

  document.querySelectorAll('canvas[data-chart]').forEach(async (canvas) => {
    const build = builders[canvas.dataset.chart];
    if (!build) return;
    try {
      const response = await fetch(canvas.dataset.src, { headers: { Accept: 'application/json' } });
      if (!response.ok) throw new Error(response.status);
      const config = build(await response.json());
      if (config.isEmpty) return showMessage(canvas, 'Chưa có dữ liệu trong kỳ này.');
      new Chart(canvas, config);
    } catch (err) {
      showMessage(canvas, 'Không tải được biểu đồ. Tải lại trang để thử lại.');
    }
  });
})();
