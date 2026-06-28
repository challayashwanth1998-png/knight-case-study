"""
Knight Insurance — AI Analyzer (OPTIMIZED)
Keeps separate focused AI calls for accuracy, but runs them in PARALLEL
for speed. Summary + Conflicts + Risk run concurrently, then Recommendations.
"""
import json
import logging
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import settings
from utils.gemini import call_gemini, call_gemini_json, get_current_metrics, set_tracking

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """Cross-document AI analysis using Google Gemini — parallel execution."""

    def analyze_submission(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        results = {}

        # Pure Python — no AI needed
        results["completeness_report"] = self._check_completeness(extracted_data)

        # Propagate metrics tracker to worker threads
        parent_tracker = get_current_metrics()

        def _tracked(fn, *args):
            """Wrapper to propagate metrics tracker to worker thread."""
            if parent_tracker:
                set_tracking(parent_tracker)
            return fn(*args)

        # Run ALL 4 analysis calls IN PARALLEL
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_summary = executor.submit(_tracked, self._generate_summary, extracted_data)
            future_conflicts = executor.submit(_tracked, self._detect_conflicts, extracted_data)
            future_risk = executor.submit(_tracked, self._assess_risk, extracted_data)
            # Recommendations uses completeness (Python, already done) + raw data
            future_recs = executor.submit(
                _tracked, self._generate_recommendations, extracted_data,
                {"completeness_report": results["completeness_report"]}
            )

            results["summary"] = future_summary.result()
            results["conflicts"] = future_conflicts.result()
            results["risk_assessment"] = future_risk.result()
            results["recommendations"] = future_recs.result()

        # Pure Python confidence
        results["confidence_score"] = self._calculate_confidence(results)

        return results

    def _generate_summary(self, data: Dict[str, Any]) -> str:
        """Generate a professional underwriting summary."""
        trimmed = json.dumps({
            "application": data.get("application", {}),
            "drivers": data.get("drivers", [])[:10],
            "vehicles": data.get("vehicles", [])[:15],
            "ifta_summary": [
                {"quarter": i.get("quarter"), "total_miles": i.get("total_miles"),
                 "fleet_mpg": i.get("fleet_mpg")}
                for i in data.get("ifta_reports", [])
            ],
            "document_types": data.get("document_types", []),
        }, indent=1, default=str)[:5000]

        prompt = f"""You are an expert commercial auto insurance underwriter. Summarize this submission
in 2-3 paragraphs for a senior underwriter to quickly understand the account.

Include: Business name/type/location, fleet composition, driver demographics,
geographic scope (IFTA), and any immediate red flags.

Submission Data:
{trimmed}

Write a professional underwriting summary:"""

        try:
            return call_gemini(prompt, temperature=0.3, step_name="summary")
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return f"[Summary generation failed: {e}]"

    def _detect_conflicts(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect conflicts and inconsistencies across documents."""
        trimmed = json.dumps({
            "application": data.get("application", {}),
            "drivers": data.get("drivers", [])[:10],
            "vehicles": data.get("vehicles", [])[:15],
            "ifta_reports": [
                {"quarter": i.get("quarter"), "company_name": i.get("company_name"),
                 "total_miles": i.get("total_miles")}
                for i in data.get("ifta_reports", [])
            ],
        }, indent=1, default=str)[:6000]

        prompt = f"""You are an expert insurance underwriter. Analyze this data from MULTIPLE documents
and identify ALL conflicts, inconsistencies, and discrepancies.

For each conflict: {{"severity": "critical/high/medium/low", "type": "category", "description": "explanation", "source_documents": "which docs", "values_found": "the conflicting values"}}

Look for: company name mismatches, address mismatches, vehicle/driver count discrepancies,
VIN issues, date inconsistencies, state mismatches, financial inconsistencies.

If the data is consistent and no real conflicts exist, return an empty array [].

Submission Data:
{trimmed}

Return a JSON array of conflict objects:"""

        try:
            response = call_gemini_json(prompt, temperature=0.1, step_name="conflicts")
            conflicts = response if isinstance(response, list) else response
            if isinstance(conflicts, dict):
                conflicts = conflicts.get("conflicts", [conflicts])
            logger.info(f"Detected {len(conflicts)} conflicts")
            return conflicts
        except Exception as e:
            logger.error(f"Conflict detection failed: {e}")
            return [{"severity": "low", "type": "error",
                     "description": f"Automated conflict detection failed: {e}"}]

    def _assess_risk(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """AI-powered risk assessment."""
        trimmed = json.dumps({
            "application": data.get("application", {}),
            "drivers": data.get("drivers", [])[:10],
            "vehicles": data.get("vehicles", [])[:15],
            "ifta_summary": [
                {"quarter": i.get("quarter"), "total_miles": i.get("total_miles"),
                 "fleet_mpg": i.get("fleet_mpg"),
                 "states": [j.get("state") for j in i.get("jurisdictions", [])]}
                for i in data.get("ifta_reports", [])
            ],
            "loss_runs": data.get("loss_runs", []),
        }, indent=1, default=str)[:5000]

        prompt = f"""You are a senior commercial auto insurance underwriter. Assess the risk
of this trucking account.

Consider: fleet composition/age, driver demographics/experience, geographic spread,
business maturity, safety profile, prior insurance history.

Rate each factor 1-10 (1=lowest risk, 10=highest risk).

Submission Data:
{trimmed}

Return JSON: {{"overall_score": 1-10, "risk_tier": "Low/Medium/High/Very High", "factors": [{{"factor": "name", "score": 1-10, "reasoning": "explanation"}}], "key_concerns": ["..."], "positive_indicators": ["..."]}}

JSON response:"""

        try:
            return call_gemini_json(prompt, temperature=0.2, step_name="risk")
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            return {"error": str(e), "overall_score": None, "risk_tier": "Unknown"}

    def _generate_recommendations(self, data: Dict[str, Any],
                                   analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable underwriting recommendations."""
        context = json.dumps({
            "completeness": analysis.get("completeness_report", {}).get("completeness_percentage"),
            "missing": analysis.get("completeness_report", {}).get("missing_required", []),
            "conflict_count": len(analysis.get("conflicts", [])),
            "risk_score": analysis.get("risk_assessment", {}).get("overall_score"),
            "risk_tier": analysis.get("risk_assessment", {}).get("risk_tier"),
        }, default=str)

        app_summary = json.dumps(data.get("application", {}), indent=1, default=str)[:2000]

        prompt = f"""You are a senior underwriter. Based on the analysis results below,
provide specific actionable recommendations.

Analysis: {context}
Business: {app_summary}

For each recommendation: {{"action": "accept/decline/request_info/refer_to_underwriter/conditional_accept", "priority": "critical/high/medium/low", "title": "short title", "description": "details", "confidence": 0-100}}

Return a JSON array starting with the overall decision recommendation:"""

        try:
            recs = call_gemini_json(prompt, temperature=0.2, step_name="recommendations")
            if isinstance(recs, dict):
                recs = recs.get("recommendations", [recs])
            return recs
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return [{"action": "refer_to_underwriter", "priority": "high",
                     "title": "Manual Review Required",
                     "description": f"Automated recommendation failed: {e}",
                     "confidence": 0}]

    def _check_completeness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check what required items are present or missing — pure Python."""
        doc_types = data.get("document_types", [])
        application = data.get("application", {})
        ifta_reports = data.get("ifta_reports", [])

        checklist = {
            "application": {
                "present": "insurance_application" in doc_types,
                "label": "Insurance Application",
                "required": True
            },
            "fein_ssn": {
                "present": bool(application.get("fein_ssn")),
                "label": "FEIN / SSN",
                "required": True
            },
            "mc_dot_number": {
                "present": bool(application.get("mc_number") or application.get("dot_number")),
                "label": "MC / DOT Number",
                "required": True
            },
            "driver_list": {
                "present": "driver_list" in doc_types,
                "label": "Driver List / Roster",
                "required": True
            },
            "equipment_list": {
                "present": "equipment_list" in doc_types,
                "label": "Equipment / Vehicle Schedule",
                "required": True
            },
            "loss_runs_current": {
                "present": "loss_run" in doc_types,
                "label": "Current Loss Runs (within 60 days)",
                "required": True
            },
            "loss_runs_prior": {
                "present": "loss_run" in doc_types,
                "label": "Prior 3 Years Loss Runs",
                "required": True
            },
            "ifta_4_quarters": {
                "present": len(ifta_reports) >= 4,
                "label": f"IFTA Reports (4 quarters) — {len(ifta_reports)} provided",
                "required": True
            },
            "driver_licenses": {
                "present": "drivers_license" in doc_types,
                "label": "Driver Licenses (CDL verification)",
                "required": True,
                "note": "CDL images required for driver verification"
            },
        }

        present_count = sum(1 for v in checklist.values() if v["present"])
        required_count = sum(1 for v in checklist.values() if v["required"])
        required_present = sum(1 for v in checklist.values() if v["required"] and v["present"])
        completeness_pct = (required_present / required_count * 100) if required_count > 0 else 0

        return {
            "checklist": checklist,
            "completeness_percentage": round(completeness_pct, 1),
            "total_items": len(checklist),
            "present_count": present_count,
            "missing_required": [
                v["label"] for v in checklist.values() if v["required"] and not v["present"]
            ]
        }

    def _calculate_confidence(self, analysis: Dict[str, Any]) -> float:
        """Calculate overall analysis confidence score — pure Python."""
        scores = []

        comp = analysis.get("completeness_report", {})
        comp_pct = comp.get("completeness_percentage", 0)
        scores.append(comp_pct / 100.0)

        conflicts = analysis.get("conflicts", [])
        critical_conflicts = sum(1 for c in conflicts
                                if isinstance(c, dict) and c.get("severity") == "critical")
        scores.append(max(0, 1.0 - (critical_conflicts * 0.15)))

        risk = analysis.get("risk_assessment", {})
        scores.append(0.9 if risk.get("overall_score") is not None else 0.3)

        return round(sum(scores) / len(scores) if scores else 0.5, 2)
