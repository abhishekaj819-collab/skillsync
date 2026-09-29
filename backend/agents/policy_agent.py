"""
Policy Routing & Notification Agent (SkillSetu Gov-Tech Platform)
SIH Problem Statement 26134 — Directorate of Vocational Education & Training (DVET), Govt of Maharashtra.

Core Responsibilities:
1. Translates Mathematical Vector Deficits into Human-Actionable Gov-Tech Directives.
2. Localized ITI Directive Generation: Generates syllabus replacement diffs, faculty development quotas, and GeM lab procurement specifications.
3. Multi-Stakeholder Policy Routing:
   - Routes granular operational directives strictly to the affected ITI Principal's dashboard.
   - Routes consolidated macro capital expenditure requests to the State Govt Admin dashboard.
4. Asynchronous Background Worker: Tied into FastAPI lifecycle to continuously monitor vector outputs and dispatch notifications.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger("SkillSetu.PolicyRoutingAgent")
logging.basicConfig(level=logging.INFO)

# ============================================================================
# 1. SPECIFIC EQUIPMENT & BUDGET MATRIX (GOV-TECH STANDARDS)
# ============================================================================
DISTRICT_MODERNIZATION_BLUEPRINTS = {
    "Pune": {
        "lab_hardware": "48V Modular EV Battery Test Bench & CAN-Bus Diagnostic Simulators",
        "lab_est_cost_lakhs": 45.0,
        "trainer_delta": "+2 EV Master Trainers",
        "capital_allocation_cr": 4.80,
        "iti_target": "Government ITI Aundh (Pune)",
        "gem_category": "Automotive Testing & Diagnostic Benches (GeM/2026/AUTO/48V)"
    },
    "Chhatrapati Sambhajinagar": {
        "lab_hardware": "5-Axis Siemens NX CNC Machining & Live Tooling Center",
        "lab_est_cost_lakhs": 85.0,
        "trainer_delta": "+2 CAD/CAM Specialists",
        "capital_allocation_cr": 3.20,
        "iti_target": "Government ITI Waluj (Chh. Sambhajinagar)",
        "gem_category": "Industrial Machining & CNC Equipment (GeM/2026/IND/5AXIS)"
    },
    "Mumbai MMR": {
        "lab_hardware": "Cloud DevOps Development Workstations & Microservices Sandbox",
        "lab_est_cost_lakhs": 38.0,
        "trainer_delta": "+3 Certified Cloud Instructors",
        "capital_allocation_cr": 2.40,
        "iti_target": "Government ITI Dadar (Mumbai)",
        "gem_category": "Cloud Computing Workstations & Server Rigs (GeM/2026/IT/CLOUD)"
    },
    "Thane": {
        "lab_hardware": "Shimadzu HPLC Chromatography Testing Skid (UV-Vis PDA Detector)",
        "lab_est_cost_lakhs": 32.0,
        "trainer_delta": "+2 Analytical Chemists",
        "capital_allocation_cr": 1.90,
        "iti_target": "Government ITI Thane (Wagle Estate)",
        "gem_category": "Pharma & Biotech Analytical Instruments (GeM/2026/PHA/HPLC)"
    },
    "Nagpur": {
        "lab_hardware": "Miniature Autonomous Guided Vehicle (AGV) Sorting Track & PLC Rig",
        "lab_est_cost_lakhs": 28.0,
        "trainer_delta": "+2 Mechatronics Instructors",
        "capital_allocation_cr": 2.75,
        "iti_target": "Government ITI MIHAN (Nagpur)",
        "gem_category": "Warehouse Automation & AGV Trainers (GeM/2026/LOG/AGV)"
    },
    "Nashik": {
        "lab_hardware": "6-Axis FANUC Robotic Welding Cell & Ultrasonic NDT Inspection Station",
        "lab_est_cost_lakhs": 52.0,
        "trainer_delta": "+2 Certified Welding Inspectors (AWS CWI)",
        "capital_allocation_cr": 2.10,
        "iti_target": "Government ITI Satpur (Nashik)",
        "gem_category": "Robotics & Industrial Fabrication Cells (GeM/2026/ROB/WELD)"
    }
}


# ============================================================================
# 2. POLICY ROUTING & NOTIFICATION AGENT CLASS
# ============================================================================
class PolicyRoutingAgent:
    """
    Autonomous Policy Routing & Notification Agent.
    Monitors the outputs of the Vector Gap-Analysis Agent, generates administrative directives,
    and isolates delivery between ITI Principals and State Government Admins.
    """

    def __init__(self):
        self.agent_name = "SkillSetu-PolicyRoutingAgent-v2.0"
        self.iti_directives_store: List[Dict[str, Any]] = []
        self.govt_budget_requests_store: List[Dict[str, Any]] = []
        self.notifications_queue: List[Dict[str, Any]] = []
        self.is_running = False

    def generate_directives_from_gaps(
        self,
        gap_dossiers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Processes vector gap dossiers and generates:
        1. Localized ITI Directives (Actionable syllabus replacements & GeM lab requisitions).
        2. Govt Budget Allocation Requests (Consolidated capital reallocations per district).
        """
        logger.info(f"[{self.agent_name}] Translating {len(gap_dossiers)} vector gap dossiers into administrative directives...")

        new_iti_directives = []
        district_budget_map: Dict[str, Dict[str, Any]] = {}

        for gap in gap_dossiers:
            district = gap.get("district", "Pune")
            is_critical = gap.get("is_deficit", False)
            cos_sim = gap.get("cosine_similarity", 0.6)
            trade_name = gap.get("trade_name", "Vocational Trade")
            curr_module = gap.get("module_title", "Legacy Module")
            industry_skill = gap.get("closest_live_industry_demand", "Modern Industrial Skill")
            company = gap.get("industry_employer", "Regional Industrial Sector")
            vacancies = gap.get("regional_vacancies", 250)

            # Look up standard blueprint
            blueprint = DISTRICT_MODERNIZATION_BLUEPRINTS.get(district, DISTRICT_MODERNIZATION_BLUEPRINTS["Pune"])

            # 1. Generate Localized ITI Principal Directive
            directive_id = f"DIR-{district[:3].upper()}-{len(new_iti_directives) + 101}"
            iti_directive = {
                "directive_id": directive_id,
                "target_stakeholder": "iti",
                "target_district": district,
                "target_institute": blueprint["iti_target"],
                "trade_name": trade_name,
                "urgency": "Critical Surge" if is_critical else "Standard Review",
                "similarity_score": f"{round(cos_sim * 100, 1)}%",
                "title": f"{district} ITI: Modernize {trade_name}",
                "summary": f"Deficit detected in {district} ({round((1 - cos_sim)*100, 1)}% gap distance). Replace '{curr_module}' with '{industry_skill}'.",
                "diff": {
                    "replace_module": curr_module,
                    "new_module": f"{industry_skill} (NSQF-Aligned)",
                    "syllabus_hours": 120,
                    "trainer_requirement": blueprint["trainer_delta"]
                },
                "lab_procurement": {
                    "equipment": blueprint["lab_hardware"],
                    "estimated_cost": f"₹{blueprint['lab_est_cost_lakhs']} Lakhs",
                    "gem_tender_category": blueprint["gem_category"],
                    "procurement_status": "Ready for GeM Dispatch"
                },
                "industry_pipeline": {
                    "lead_employer": company,
                    "verified_openings": vacancies
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "AWAITING_PRINCIPAL_APPROVAL"
            }
            new_iti_directives.append(iti_directive)

            # 2. Accumulate Govt Capital Budget Request
            if district not in district_budget_map:
                district_budget_map[district] = {
                    "district": district,
                    "capital_cr": blueprint["capital_allocation_cr"],
                    "priority": "High" if is_critical else "Medium",
                    "initiatives": [],
                    "critical_gaps_count": 0,
                    "target_itis": blueprint["iti_target"]
                }
            
            district_budget_map[district]["initiatives"].append(f"{trade_name}: {industry_skill}")
            if is_critical:
                district_budget_map[district]["critical_gaps_count"] += 1

        # Format Govt Budget Directives
        govt_budget_requests = []
        for dist_name, data in district_budget_map.items():
            req_id = f"BUDGET-MAH-{dist_name[:3].upper()}-2026"
            govt_req = {
                "request_id": req_id,
                "target_stakeholder": "gov",
                "target_district": dist_name,
                "capital_routed_cr": f"₹{data['capital_cr']:.2f} Cr",
                "critical_gaps": f"{data['critical_gaps_count']} Gaps",
                "priority_status": "Authorized" if data["critical_gaps_count"] > 0 else "In Review",
                "authorized_initiative": f"{dist_name} Advanced Modernization Rigs",
                "description": f"Reallocating ₹{data['capital_cr']:.2f} Cr from legacy non-performing trades to modern lab hardware at {data['target_itis']}.",
                "disbursement_progress_pct": 85 if dist_name == "Pune" else 60,
                "initiatives_covered": data["initiatives"][:3],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            govt_budget_requests.append(govt_req)

        self.iti_directives_store = new_iti_directives
        self.govt_budget_requests_store = govt_budget_requests

        logger.info(f"[{self.agent_name}] Generated {len(new_iti_directives)} ITI directives and {len(govt_budget_requests)} Govt capital requests.")
        return {
            "iti_directives": self.iti_directives_store,
            "govt_budget_requests": self.govt_budget_requests_store,
            "total_directives": len(new_iti_directives) + len(govt_budget_requests)
        }

    def get_directives_for_role(
        self,
        role: str,
        district_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Enforces strict stakeholder isolation:
        - Role 'iti': Returns ONLY granular curriculum & lab directives for the ITI Principal.
        - Role 'gov': Returns ONLY macro fiscal budget requests & statewide compliance audits.
        - Role 'emp': Returns empty list (Employers do not have clearance for internal directives).
        """
        if role == "iti":
            if district_filter and district_filter.lower() != "all":
                return [d for d in self.iti_directives_store if d["target_district"].lower() == district_filter.lower()]
            return self.iti_directives_store
        elif role in ["gov", "govt"]:
            return self.govt_budget_requests_store
        else:
            return []

    async def run_policy_worker_loop(self, interval_seconds: int = 3600):
        """
        Asynchronous background worker task that periodically runs policy generation.
        """
        self.is_running = True
        logger.info(f"[{self.agent_name}] Asynchronous policy worker started (polling every {interval_seconds}s)...")
        while self.is_running:
            try:
                # Trigger pipeline orchestration
                from scraper_agent import LMIScraperAgent
                from vector_agent import VectorGapAnalysisAgent

                scraper = LMIScraperAgent()
                feeds = scraper.scrape_and_process_feeds()

                vector_agent = VectorGapAnalysisAgent()
                gaps = vector_agent.analyze_curriculum_gaps(feeds)

                self.generate_directives_from_gaps(gaps)
            except Exception as e:
                logger.error(f"[{self.agent_name}] Error in policy background cycle: {e}")

            await asyncio.sleep(interval_seconds)

    def stop_worker(self):
        self.is_running = False


# Singleton Policy Agent Instance
_policy_agent_instance = PolicyRoutingAgent()

def get_policy_agent() -> PolicyRoutingAgent:
    return _policy_agent_instance


if __name__ == "__main__":
    from scraper_agent import LMIScraperAgent
    from vector_agent import VectorGapAnalysisAgent

    scraper = LMIScraperAgent()
    feeds = scraper.scrape_and_process_feeds()

    vector_agent = VectorGapAnalysisAgent()
    gaps = vector_agent.analyze_curriculum_gaps(feeds)

    policy_agent = PolicyRoutingAgent()
    result = policy_agent.generate_directives_from_gaps(gaps)
    import json
    print("=== ITI DIRECTIVES ===")
    print(json.dumps(result["iti_directives"][:2], indent=2))
    print("=== GOVT BUDGET REQUESTS ===")
    print(json.dumps(result["govt_budget_requests"][:2], indent=2))
