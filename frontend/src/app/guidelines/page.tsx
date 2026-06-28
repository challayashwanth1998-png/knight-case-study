"use client";

const STATES = [
  "AL", "AZ", "AR", "CA", "SC", "SD", "TN", "TX*", "UT", "VA", "WV", "WI", "WY"
];

export default function GuidelinesPage() {
  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      <div className="page-header">
        <h1 className="page-title">Knight Specialty Insurance Guidelines</h1>
        <p className="page-description">
          Excess &amp; Surplus Lines Carrier — Trucking Program
        </p>
      </div>

      <div className="usa-alert usa-alert-info" style={{ marginBottom: 24 }}>
        This is the reference guide for Knight Specialty Insurance underwriting rules.
        All rules are programmatically enforced by the Rules Engine.
      </div>

      <div className="grid-2" style={{ gap: 20 }}>
        {/* Program Appetite */}
        <div className="card">
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12, color: "var(--primary-dark)" }}>
            🎯 Program Appetite
          </h3>
          <div style={{ fontSize: 13, lineHeight: 1.7 }}>
            <p style={{ marginBottom: 10 }}>
              <strong>Target Risk:</strong> Semi-trucks hauling general freight across state lines.
            </p>
            <p style={{ marginBottom: 10 }}>
              <strong>Not Eligible:</strong> Straight trucks, tow trucks, dump trucks,
              concrete mixers/pumpers, cranes, or mobile equipment regardless of GVW.
            </p>
            <p style={{ marginBottom: 10 }}>
              <strong>Auto Liability Deductibles:</strong> Not allowed.
            </p>
            <p>
              <strong>Auto Physical Damage:</strong> Not available.
            </p>
          </div>
        </div>

        {/* Available States */}
        <div className="card">
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12, color: "var(--primary-dark)" }}>
            🗺️ Available States
          </h3>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 12 }}>
            {STATES.map((s) => (
              <span
                key={s}
                className="usa-tag usa-tag-primary"
                style={{ fontSize: 12, padding: "3px 8px" }}
              >
                {s}
              </span>
            ))}
          </div>
          <div style={{ fontSize: 12, color: "var(--base-dark)", lineHeight: 1.6 }}>
            <p><strong>*TX:</strong> Accounts must operate north of Interstate 10 (I-10).</p>
            <p><strong>IL:</strong> Illinois-based accounts accepted on selective basis.</p>
          </div>
        </div>

        {/* New Ventures */}
        <div className="card">
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12, color: "var(--primary-dark)" }}>
            🆕 New Ventures
          </h3>
          <div style={{ fontSize: 13, lineHeight: 1.7 }}>
            <p style={{ marginBottom: 8 }}>
              <strong>Sole Proprietors, Partnerships, LLCs:</strong> Acceptable with
              2 years documented CDL experience and resume/letter of experience.
            </p>
            <p>
              <strong>Corporations:</strong> Subject to underwriter review.
            </p>
          </div>
        </div>

        {/* Submission Requirements */}
        <div className="card">
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12, color: "var(--primary-dark)" }}>
            📋 Submission Requirements
          </h3>
          <ul style={{ paddingLeft: 18, fontSize: 13, lineHeight: 1.8 }}>
            <li>Application with <strong>FEIN/SSN</strong> and <strong>MC/Docket number</strong></li>
            <li>Current loss runs valued within <strong>60 days</strong></li>
            <li>At least <strong>3 prior years</strong> of loss history</li>
            <li>Most recent <strong>4 quarters of IFTA</strong> reports</li>
          </ul>
        </div>

        {/* Driver Criteria */}
        <div className="card">
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12, color: "var(--primary-dark)" }}>
            🚛 Safe Driver Criteria
          </h3>
          <ul style={{ paddingLeft: 18, fontSize: 13, lineHeight: 1.8 }}>
            <li>Valid U.S. driver license with <strong>CDL</strong></li>
            <li>Minimum <strong>2 years CDL</strong> experience (U.S. or Canada)</li>
            <li>Minimum age <strong>23</strong></li>
            <li>Drivers age <strong>65+</strong>: DOT medical examination required</li>
            <li>No more than <strong>6 points in 3 years</strong></li>
            <li>No more than <strong>4 points in 12 months</strong></li>
          </ul>
        </div>

        {/* Quick Decline */}
        <div className="card" style={{ borderColor: "rgba(213,67,9,0.3)" }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12, color: "var(--error)" }}>
            🚫 Quick Decline / Escalation
          </h3>
          <div style={{ fontSize: 13, lineHeight: 1.7 }}>
            <p style={{ fontWeight: 600, marginBottom: 6 }}>Unacceptable Driver History:</p>
            <ul style={{ paddingLeft: 18, marginBottom: 12, lineHeight: 1.8 }}>
              <li>DUI/DWI in past 5 years</li>
              <li>Vehicular homicide/assault</li>
              <li>Negligent or reckless driving</li>
              <li>Speeding 30+ mph above limit</li>
              <li>Hit-and-run · Fleeing/eluding</li>
              <li>Felony involving a motor vehicle</li>
              <li>Passing a stopped school bus</li>
            </ul>
            <p style={{ fontWeight: 600, marginBottom: 6 }}>Prohibited Exposures:</p>
            <ul style={{ paddingLeft: 18, lineHeight: 1.8 }}>
              <li>Hazardous materials</li>
              <li>Lithium battery cargo</li>
              <li>Operations within 50mi of USA/Mexico border</li>
              <li>Serious SAFER violations</li>
              <li>Towing/recovery · Intermodal/container</li>
              <li>Waste disposal</li>
            </ul>
          </div>
        </div>

        {/* Selective */}
        <div className="card" style={{ gridColumn: "span 2" }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 12, color: "var(--primary-dark)" }}>
            🔍 Selective Exposures
          </h3>
          <div className="grid-3" style={{ gap: 16 }}>
            <div style={{ padding: 12, background: "var(--surface-alt)", borderRadius: 6 }}>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>Automobile Haulers</div>
              <div style={{ fontSize: 12, color: "var(--base-dark)" }}>Accepted on selective basis</div>
            </div>
            <div style={{ padding: 12, background: "var(--surface-alt)", borderRadius: 6 }}>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>Box Trucks / Transit Vans</div>
              <div style={{ fontSize: 12, color: "var(--base-dark)" }}>Minimum premium $250,000</div>
            </div>
            <div style={{ padding: 12, background: "var(--surface-alt)", borderRadius: 6 }}>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>Per Power Unit Pricing</div>
              <div style={{ fontSize: 12, color: "var(--base-dark)" }}>
                &lt;$13,000/unit requires ≥20 power units
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
