import React from 'react';

export default function AreaChart({ data = [], height = 120, color = '#3b82f6', label = '' }) {
  if (data.length === 0) {
    return <div className="text-gray-500 text-xs flex items-center justify-center" style={{ height }}>No data</div>;
  }

  const maxVal = Math.max(...data, 10);
  const minVal = Math.min(...data, 0);
  const range = maxVal - minVal || 1;

  const width = 500;
  const padding = 10;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  const points = data.map((val, idx) => {
    const x = padding + (idx / (data.length - 1 || 1)) * chartWidth;
    const y = padding + chartHeight - ((val - minVal) / range) * chartHeight;
    return { x, y };
  });

  // Create smooth Bezier curve line path
  let pathD = '';
  if (points.length > 0) {
    pathD = `M ${points[0].x} ${points[0].y}`;
    for (let i = 0; i < points.length - 1; i++) {
      const curr = points[i];
      const next = points[i + 1];
      const cpX1 = curr.x + (next.x - curr.x) / 3;
      const cpY1 = curr.y;
      const cpX2 = curr.x + (2 * (next.x - curr.x)) / 3;
      const cpY2 = next.y;
      pathD += ` C ${cpX1} ${cpY1}, ${cpX2} ${cpY2}, ${next.x} ${next.y}`;
    }
  }

  // Create fill path (closes the shape at the bottom)
  const fillD = points.length > 0
    ? `${pathD} L ${points[points.length - 1].x} ${height - padding} L ${points[0].x} ${height - padding} Z`
    : '';

  const gradientId = `grad-${label.replace(/\s+/g, '-')}`;

  return (
    <div className="w-full">
      <div className="flex justify-between items-center mb-2">
        <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">{label}</span>
        <span className="text-sm font-bold text-white" style={{ color }}>{data[data.length - 1]?.toFixed(1)}</span>
      </div>
      <div className="relative bg-black/40 border border-white/5 rounded-lg overflow-hidden p-2">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full overflow-visible" style={{ height }}>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.3} />
              <stop offset="100%" stopColor={color} stopOpacity={0.0} />
            </linearGradient>
          </defs>
          {/* Horizontal grid lines */}
          <line x1={padding} y1={padding} x2={width - padding} y2={padding} stroke="rgba(255,255,255,0.03)" strokeWidth={1} />
          <line x1={padding} y1={padding + chartHeight / 2} x2={width - padding} y2={padding + chartHeight / 2} stroke="rgba(255,255,255,0.03)" strokeWidth={1} />
          <line x1={padding} y1={padding + chartHeight} x2={width - padding} y2={padding + chartHeight} stroke="rgba(255,255,255,0.03)" strokeWidth={1} />

          {/* Area under the path */}
          {fillD && <path d={fillD} fill={`url(#${gradientId})`} />}

          {/* Line path */}
          {pathD && <path d={pathD} fill="none" stroke={color} strokeWidth={2} strokeLinecap="round" />}

          {/* End indicator point */}
          {points.length > 0 && (
            <circle cx={points[points.length - 1].x} cy={points[points.length - 1].y} r={4} fill={color} stroke="#0d1117" strokeWidth={1.5} />
          )}
        </svg>
      </div>
    </div>
  );
}
