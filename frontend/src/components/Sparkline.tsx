type Props = {
  values: string[];
  tone?: "neutral" | "drop" | "rise";
};

export function Sparkline({ values, tone = "neutral" }: Props) {
  const numbers = values.map((value) => Number(value)).filter((value) => Number.isFinite(value));
  if (numbers.length === 0) {
    return <div className="sparkline-empty">暂无趋势</div>;
  }

  const width = 120;
  const height = 40;
  const min = Math.min(...numbers);
  const max = Math.max(...numbers);
  const range = max - min || 1;
  const points = numbers
    .map((value, index) => {
      const x = numbers.length === 1 ? width / 2 : (index / (numbers.length - 1)) * width;
      const y = height - ((value - min) / range) * (height - 6) - 3;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <div className={`sparkline sparkline-${tone}`}>
      <svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" aria-hidden="true">
        <polyline fill="none" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" points={points} />
      </svg>
      <span>{numbers.length} 个采样点</span>
    </div>
  );
}
