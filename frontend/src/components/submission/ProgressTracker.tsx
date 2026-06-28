"use client";

import type { AuditLog } from "@/types";

const STEPS = [
  { step: 1, label: "Text Extraction", key: "step_extract_text" },
  { step: 2, label: "Classification", key: "step_classify" },
  { step: 3, label: "Data Extraction", key: "step_extract_data" },
  { step: 4, label: "AI Analysis", key: "step_ai_analysis" },
  { step: 5, label: "Rules Engine", key: "step_rules" },
  { step: 6, label: "Decision", key: "pipeline_complete" },
];

interface Props {
  auditLog: AuditLog[];
  status: string;
}

export default function ProgressTracker({ auditLog, status }: Props) {
  const completedActions = new Set(auditLog.map((l) => l.action));

  const getStepState = (stepDef: typeof STEPS[0]) => {
    const completeKey = stepDef.key + "_complete";
    if (stepDef.key === "pipeline_complete") {
      if (completedActions.has("pipeline_complete")) return "complete";
      if (status === "error") return "error";
      // Check if step 5 is complete (rules)
      if (completedActions.has("step_rules_complete")) return "active";
      return "pending";
    }
    if (completedActions.has(completeKey)) return "complete";
    if (completedActions.has(stepDef.key)) return "active";
    // Check if previous step is complete
    const idx = STEPS.indexOf(stepDef);
    if (idx > 0) {
      const prevComplete = STEPS[idx - 1].key + "_complete";
      if (STEPS[idx - 1].key === "pipeline_complete") return "pending";
      if (completedActions.has(prevComplete)) return "active";
    }
    if (idx === 0 && status === "processing") return "active";
    return "pending";
  };

  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <div style={{ fontSize: 12, fontWeight: 700, color: "var(--base-dark)", marginBottom: 14, textTransform: "uppercase", letterSpacing: "0.5px" }}>
        Pipeline Progress
      </div>
      <div className="step-indicator">
        {STEPS.map((s) => {
          const state = getStepState(s);
          return (
            <div key={s.step} className={`step-item ${state}`}>
              <div className="step-label">{s.label}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
