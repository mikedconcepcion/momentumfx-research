// Chart data
const periodData = [
    { period: 'COVID\n2020-2021', concentration: 2.80, zones: 88, obPct: 93.2 },
    { period: 'Post-COVID\n2022-2023', concentration: 1.90, zones: 30, obPct: 63.3 },
    { period: 'Recent\n2024-2025', concentration: 2.50, zones: 12, obPct: 83.3 },
    { period: 'FULL\n6-YEAR', concentration: 2.56, zones: 130, obPct: 85.4 }
];

const instrumentData = [
    { name: 'XAUUSD', obPct: 95.3, zones: 85, primary: true },
    { name: 'EURUSD', obPct: 80.0, zones: 10, primary: false },
    { name: 'USDJPY', obPct: 71.4, zones: 7, primary: false },
    { name: 'BTCUSD', obPct: 75.0, zones: 16, primary: false },
    { name: 'GBPUSD', obPct: 16.7, zones: 12, primary: false }
];

// Create period comparison chart
function createPeriodChart() {
    const svg = document.getElementById('periodChart');
    if (!svg) return;

    const width = 800;
    const height = 400;
    const padding = { top: 40, right: 40, bottom: 80, left: 60 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    // Clear existing content
    svg.innerHTML = '';

    // Background
    const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    bg.setAttribute('width', width);
    bg.setAttribute('height', height);
    bg.setAttribute('fill', '#f9fafb');
    svg.appendChild(bg);

    // Chart group
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.setAttribute('transform', `translate(${padding.left},${padding.top})`);
    svg.appendChild(g);

    // Scales
    const maxConcentration = 3.0;
    const barWidth = chartWidth / periodData.length / 1.5;
    const barSpacing = chartWidth / periodData.length;

    // Grid lines
    for (let i = 0; i <= 4; i++) {
        const y = chartHeight - (i / 4) * chartHeight;
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', 0);
        line.setAttribute('y1', y);
        line.setAttribute('x2', chartWidth);
        line.setAttribute('y2', y);
        line.setAttribute('stroke', '#e5e7eb');
        line.setAttribute('stroke-width', '1');
        line.setAttribute('stroke-dasharray', '4,4');
        g.appendChild(line);

        // Y-axis labels
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', -10);
        label.setAttribute('y', y + 4);
        label.setAttribute('text-anchor', 'end');
        label.setAttribute('fill', '#6b7280');
        label.setAttribute('font-size', '12');
        label.textContent = ((i / 4) * maxConcentration).toFixed(1) + 'x';
        g.appendChild(label);
    }

    // Bars
    periodData.forEach((d, i) => {
        const x = i * barSpacing + (barSpacing - barWidth) / 2;
        const barHeight = (d.concentration / maxConcentration) * chartHeight;
        const y = chartHeight - barHeight;

        // Bar
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', x);
        rect.setAttribute('y', y);
        rect.setAttribute('width', barWidth);
        rect.setAttribute('height', barHeight);
        rect.setAttribute('fill', i === 0 ? '#fbbf24' : i === 3 ? '#2563eb' : '#10b981');
        rect.setAttribute('rx', '4');
        rect.setAttribute('class', 'bar');
        g.appendChild(rect);

        // Value label
        const valueLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        valueLabel.setAttribute('x', x + barWidth / 2);
        valueLabel.setAttribute('y', y - 10);
        valueLabel.setAttribute('text-anchor', 'middle');
        valueLabel.setAttribute('fill', '#111827');
        valueLabel.setAttribute('font-weight', '600');
        valueLabel.setAttribute('font-size', '14');
        valueLabel.textContent = d.concentration.toFixed(2) + 'x';
        g.appendChild(valueLabel);

        // Period label
        const periodLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        const lines = d.period.split('\n');
        lines.forEach((line, lineIndex) => {
            const textElem = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            textElem.setAttribute('x', x + barWidth / 2);
            textElem.setAttribute('y', chartHeight + 20 + (lineIndex * 16));
            textElem.setAttribute('text-anchor', 'middle');
            textElem.setAttribute('fill', '#374151');
            textElem.setAttribute('font-size', '13');
            textElem.setAttribute('font-weight', lineIndex === 0 ? '600' : '400');
            textElem.textContent = line;
            g.appendChild(textElem);
        });
    });

    // Y-axis title
    const yTitle = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    yTitle.setAttribute('transform', `translate(${-45}, ${chartHeight / 2}) rotate(-90)`);
    yTitle.setAttribute('text-anchor', 'middle');
    yTitle.setAttribute('fill', '#374151');
    yTitle.setAttribute('font-size', '14');
    yTitle.setAttribute('font-weight', '600');
    yTitle.textContent = 'Concentration Factor';
    g.appendChild(yTitle);

    // Title
    const title = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    title.setAttribute('x', chartWidth / 2);
    title.setAttribute('y', -15);
    title.setAttribute('text-anchor', 'middle');
    title.setAttribute('fill', '#111827');
    title.setAttribute('font-size', '16');
    title.setAttribute('font-weight', '700');
    title.textContent = 'Order Block Concentration by Period';
    g.appendChild(title);
}

// Create instrument comparison chart
function createInstrumentChart() {
    const svg = document.getElementById('instrumentChart');
    if (!svg) return;

    const width = 800;
    const height = 400;
    const padding = { top: 40, right: 40, bottom: 60, left: 60 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    // Clear existing content
    svg.innerHTML = '';

    // Background
    const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    bg.setAttribute('width', width);
    bg.setAttribute('height', height);
    bg.setAttribute('fill', '#f9fafb');
    svg.appendChild(bg);

    // Chart group
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.setAttribute('transform', `translate(${padding.left},${padding.top})`);
    svg.appendChild(g);

    // Scales
    const maxPct = 100;
    const barWidth = chartWidth / instrumentData.length / 1.5;
    const barSpacing = chartWidth / instrumentData.length;

    // Grid lines
    for (let i = 0; i <= 5; i++) {
        const y = chartHeight - (i / 5) * chartHeight;
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('x1', 0);
        line.setAttribute('y1', y);
        line.setAttribute('x2', chartWidth);
        line.setAttribute('y2', y);
        line.setAttribute('stroke', '#e5e7eb');
        line.setAttribute('stroke-width', '1');
        line.setAttribute('stroke-dasharray', '4,4');
        g.appendChild(line);

        // Y-axis labels
        const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        label.setAttribute('x', -10);
        label.setAttribute('y', y + 4);
        label.setAttribute('text-anchor', 'end');
        label.setAttribute('fill', '#6b7280');
        label.setAttribute('font-size', '12');
        label.textContent = ((i / 5) * maxPct).toFixed(0) + '%';
        g.appendChild(label);
    }

    // Baseline at 33.3%
    const baselineY = chartHeight - (33.3 / maxPct) * chartHeight;
    const baseline = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    baseline.setAttribute('x1', 0);
    baseline.setAttribute('y1', baselineY);
    baseline.setAttribute('x2', chartWidth);
    baseline.setAttribute('y2', baselineY);
    baseline.setAttribute('stroke', '#ef4444');
    baseline.setAttribute('stroke-width', '2');
    baseline.setAttribute('stroke-dasharray', '8,4');
    g.appendChild(baseline);

    // Baseline label
    const baselineLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    baselineLabel.setAttribute('x', chartWidth - 5);
    baselineLabel.setAttribute('y', baselineY - 5);
    baselineLabel.setAttribute('text-anchor', 'end');
    baselineLabel.setAttribute('fill', '#ef4444');
    baselineLabel.setAttribute('font-size', '11');
    baselineLabel.setAttribute('font-weight', '600');
    baselineLabel.textContent = '33.3% Baseline';
    g.appendChild(baselineLabel);

    // Bars
    instrumentData.forEach((d, i) => {
        const x = i * barSpacing + (barSpacing - barWidth) / 2;
        const barHeight = (d.obPct / maxPct) * chartHeight;
        const y = chartHeight - barHeight;

        // Bar color
        let color;
        if (d.primary) {
            color = '#fbbf24'; // Gold
        } else if (d.obPct < 33.3) {
            color = '#ef4444'; // Red
        } else if (d.obPct > 75) {
            color = '#10b981'; // Green
        } else {
            color = '#6b7280'; // Gray
        }

        // Bar
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', x);
        rect.setAttribute('y', y);
        rect.setAttribute('width', barWidth);
        rect.setAttribute('height', barHeight);
        rect.setAttribute('fill', color);
        rect.setAttribute('rx', '4');
        g.appendChild(rect);

        // Value label
        const valueLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        valueLabel.setAttribute('x', x + barWidth / 2);
        valueLabel.setAttribute('y', y - 10);
        valueLabel.setAttribute('text-anchor', 'middle');
        valueLabel.setAttribute('fill', '#111827');
        valueLabel.setAttribute('font-weight', '600');
        valueLabel.setAttribute('font-size', '14');
        valueLabel.textContent = d.obPct.toFixed(1) + '%';
        g.appendChild(valueLabel);

        // Instrument label
        const instLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        instLabel.setAttribute('x', x + barWidth / 2);
        instLabel.setAttribute('y', chartHeight + 25);
        instLabel.setAttribute('text-anchor', 'middle');
        instLabel.setAttribute('fill', '#374151');
        instLabel.setAttribute('font-size', '13');
        instLabel.setAttribute('font-weight', '600');
        instLabel.textContent = d.name;
        g.appendChild(instLabel);
    });

    // Y-axis title
    const yTitle = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    yTitle.setAttribute('transform', `translate(${-45}, ${chartHeight / 2}) rotate(-90)`);
    yTitle.setAttribute('text-anchor', 'middle');
    yTitle.setAttribute('fill', '#374151');
    yTitle.setAttribute('font-size', '14');
    yTitle.setAttribute('font-weight', '600');
    yTitle.textContent = 'OB Concentration (%)';
    g.appendChild(yTitle);

    // Title
    const title = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    title.setAttribute('x', chartWidth / 2);
    title.setAttribute('y', -15);
    title.setAttribute('text-anchor', 'middle');
    title.setAttribute('fill', '#111827');
    title.setAttribute('font-size', '16');
    title.setAttribute('font-weight', '700');
    title.textContent = 'Order Block Concentration by Instrument';
    g.appendChild(title);
}

// Initialize charts when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        createPeriodChart();
        createInstrumentChart();
    });
} else {
    createPeriodChart();
    createInstrumentChart();
}

// Redraw charts on window resize
let resizeTimer;
window.addEventListener('resize', function() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function() {
        createPeriodChart();
        createInstrumentChart();
    }, 250);
});
