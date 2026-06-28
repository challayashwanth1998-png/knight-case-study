"use client";

interface Props {
  inputTokens: number;
  outputTokens: number;
  costUsd: number;
  callsCount: number;
  durationMs: number | null;
}

export default function AICostCard({
  inputTokens, outputTokens, costUsd, callsCount, durationMs,
}: Props) {
  if (callsCount === 0) return null;

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const formatTokens = (n: number) => {
    if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
    if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
    return String(n);
  };

  return (
    <div className="cost-card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
        <div className="cost-label">AI Processing Cost</div>
        <div className="cost-value">${costUsd.toFixed(4)}</div>
      </div>
      <div className="cost-grid">
        <div className="cost-item">
          <div className="cost-item-value">{callsCount}</div>
          <div className="cost-item-label">API Calls</div>
        </div>
        <div className="cost-item">
          <div className="cost-item-value">{formatTokens(inputTokens)}</div>
          <div className="cost-item-label">Input Tokens</div>
        </div>
        <div className="cost-item">
          <div className="cost-item-value">{formatTokens(outputTokens)}</div>
          <div className="cost-item-label">Output Tokens</div>
        </div>
        <div className="cost-item">
          <div className="cost-item-value">{durationMs ? formatDuration(durationMs) : "—"}</div>
          <div className="cost-item-label">Duration</div>
        </div>
      </div>
    </div>
  );
}
