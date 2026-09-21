"""
SkillSetu Asynchronous ETL Ingestion Agent (Layer 2 & Layer 3)
Scrapes or fetches real-time/simulated job postings from the National Career Service (NCS)
and state portals, performs Layer 2 skill extraction, maps to standard NCO and NSQF taxonomies,
and upserts records into the SQLite database (skillsync.db).

Cron-ready standalone execution:
  python backend/ingestion_agent.py [--dry-run] [--limit N] [--verbose]
"""

import sys
import os
import re
import json
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

# Ensure backend directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from database import init_db, SessionLocal, JobRole, JobDemand, CandidateSupply

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [ETL IngestionAgent] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("IngestionAgent")


# ============================================================================
# 1. TAXONOMY DICTIONARY (NCO Codes & NSQF Levels 1 to 8)
# ============================================================================

TAXONOMY_MAP: Dict[str, Dict[str, Any]] = {
    "data analyst": {
        "nco_code": "2512.0201",
        "esco_code": "2512.1.14",
        "nsqf_level": "Level 6 (Bachelor / Professional)",
        "sector": "Information Technology & Analytics",
        "skills": ["SQL", "Python", "Tableau", "PowerBI", "Statistical Modeling", "ETL"],
        "default_demand": 92,
        "default_supply": 48,
        "growth": "+38%",
        "search_query": "data analytics"
    },
    "solar technician": {
        "nco_code": "2151.0103",
        "esco_code": "2151.1.4",
        "nsqf_level": "Level 4 (Vocational / Technician)",
        "sector": "Renewable Energy & Utilities",
        "skills": ["Photovoltaic Installation", "Inverter Wiring", "Grid Synchronization", "MPPT", "Preventive Maintenance"],
        "default_demand": 89,
        "default_supply": 35,
        "growth": "+52%",
        "search_query": "solar energy"
    },
    "cnc operator": {
        "nco_code": "7223.0101",
        "esco_code": "7223.1.2",
        "nsqf_level": "Level 4.5 (Technician / Operator)",
        "sector": "Advanced Manufacturing & Automotive",
        "skills": ["G-Code", "M-Code", "CNC Milling", "CAD/CAM", "Precision Metrology", "Tool Offsets"],
        "default_demand": 86,
        "default_supply": 52,
        "growth": "+24%",
        "search_query": "cnc machining"
    },
    "electric vehicle": {
        "nco_code": "2144.0201",
        "esco_code": "2144.2.7",
        "nsqf_level": "Level 5.5 (Diploma / Advanced Technician)",
        "sector": "Automotive & Clean Energy",
        "skills": ["Battery Management Systems (BMS)", "Thermal Runaway Prevention", "CAN Bus", "High-Voltage Safety"],
        "default_demand": 94,
        "default_supply": 28,
        "growth": "+68%",
        "search_query": "electric vehicles"
    },
    "cloud devops": {
        "nco_code": "2511.0302",
        "esco_code": "2511.2.3",
        "nsqf_level": "Level 6 (Graduate / Engineering)",
        "sector": "Information Technology & Cloud",
        "skills": ["Kubernetes", "Docker", "Terraform", "CI/CD Pipelines", "AWS", "GitOps"],
        "default_demand": 95,
        "default_supply": 44,
        "growth": "+45%",
        "search_query": "cloud computing"
    },
    "cybersecurity": {
        "nco_code": "2529.0103",
        "esco_code": "2529.1.5",
        "nsqf_level": "Level 7 (Postgraduate / Specialist)",
        "sector": "Information Security & Defense",
        "skills": ["Zero Trust Architecture", "SOC Analysis", "Threat Hunting", "IAM Federation", "SIEM", "Incident Response"],
        "default_demand": 96,
        "default_supply": 32,
        "growth": "+58%",
        "search_query": "cyber security"
    },
    "precision agriculture": {
        "nco_code": "2132.0101",
        "esco_code": "2132.1.3",
        "nsqf_level": "Level 5 (Applied AgriTech / Diploma)",
        "sector": "Agriculture & AgriTech",
        "skills": ["IoT Soil Sensors", "Drone Crop Spraying", "Drip Automation", "Satellite Telemetry", "Yield Analytics"],
        "default_demand": 84,
        "default_supply": 38,
        "growth": "+42%",
        "search_query": "precision agriculture"
    },
    "healthcare it": {
        "nco_code": "2269.0102",
        "esco_code": "2269.1.5",
        "nsqf_level": "Level 5 (Healthcare Informatics)",
        "sector": "Healthcare & Life Sciences",
        "skills": ["ABDM Health Standards", "FHIR / HL7 Protocols", "Electronic Health Records (EHR)", "PACS Telemedicine"],
        "default_demand": 82,
        "default_supply": 41,
        "growth": "+36%",
        "search_query": "healthcare technology"
    },
    "industrial automation": {
        "nco_code": "2152.0104",
        "esco_code": "2152.1.2",
        "nsqf_level": "Level 6 (Industrial Robotics / SCADA)",
        "sector": "Advanced Manufacturing & Robotics",
        "skills": ["PLC Programming", "SCADA Architecture", "Industrial Robotics", "Modbus", "Sensor Interfacing"],
        "default_demand": 90,
        "default_supply": 36,
        "growth": "+48%",
        "search_query": "industrial automation"
    },
    "drone technician": {
        "nco_code": "3119.0101",
        "esco_code": "3119.2.1",
        "nsqf_level": "Level 4 (DGCA Certified Remote Pilot)",
        "sector": "Aerospace & Geospatial",
        "skills": ["DGCA Flight Regulations", "LiDAR Surveying", "Battery Maintenance", "Gimbal Calibration", "GIS Mapping"],
        "default_demand": 88,
        "default_supply": 29,
        "growth": "+74%",
        "search_query": "drone technology"
    }
}


# ============================================================================
# 2. SIMULATED NCS & PUBLIC DATASET SCRAPER (Layer 1 Ingestion)
# ============================================================================

SAMPLE_PUBLIC_JOB_POSTINGS: List[Dict[str, Any]] = [
    {
        "title": "Senior Data Analyst - Business Intelligence & SQL Pipelining",
        "employer": "Maharashtra State Innovation Society / Tech Partner",
        "district": "Pune District",
        "sector": "Information Technology & Analytics",
        "raw_html": """
        <div class="job-card">
            <h3 class="title">Senior Data Analyst - Business Intelligence & SQL Pipelining</h3>
            <p class="desc">
                Seeking a certified Data Analyst to design automated SQL pipelines, build executive
                PowerBI dashboards, and execute statistical forecasting across state registries.
                Requires expertise in Python, SQL, statistical modeling, and ETL data warehouse design.
            </p>
            <div class="meta">Location: Pune (Hinjawadi IT Corridor) | Vacancies: 85</div>
        </div>
        """
    },
    {
        "title": "Rooftop Solar Installation & Inverter Maintenance Technician",
        "employer": "Mahavitaran Solar Infrastructure Development",
        "district": "Nagpur Industrial",
        "sector": "Renewable Energy & Utilities",
        "raw_html": """
        <div class="job-card">
            <h3 class="title">Rooftop Solar Installation & Inverter Maintenance Technician</h3>
            <p class="desc">
                Urgent requirement for Solar Technicians to mount photovoltaic modules, configure
                MPPT string inverters, and perform net-metering grid synchronization.
                Must be skilled in solar array installation, DC wiring, and preventive maintenance.
            </p>
            <div class="meta">Location: Nagpur / Vidarbha | Vacancies: 140</div>
        </div>
        """
    },
    {
        "title": "Precision CNC Milling & Turning Operator",
        "employer": "Chakan Automotive Engineering Consortium",
        "district": "Pune District",
        "sector": "Advanced Manufacturing & Automotive",
        "raw_html": """
        <div class="job-card">
            <h3 class="title">Precision CNC Milling & Turning Operator</h3>
            <p class="desc">
                Operate multi-axis CNC milling centers producing precision transmission components.
                Candidate must know G-code, M-code editing, tool offsets, and micrometric metrology.
            </p>
            <div class="meta">Location: Chakan / Bhosari MIDC | Vacancies: 210</div>
        </div>
        """
    },
    {
        "title": "EV Service Specialist - Battery Management Systems & Diagnostics",
        "employer": "Maharashtra Clean Mobility Fleet Solutions",
        "district": "Mumbai Metro",
        "sector": "Automotive & Clean Energy",
        "raw_html": """
        <div class="job-card">
            <h3 class="title">EV Service Specialist - Battery Management Systems & Diagnostics</h3>
            <p class="desc">
                Diagnose high-voltage lithium-ion battery packs, calibrate BMS telemetry,
                and resolve CAN bus communication errors for electric bus and commercial fleets.
            </p>
            <div class="meta">Location: Mumbai Suburban & Navi Mumbai | Vacancies: 95</div>
        </div>
        """
    },
    {
        "title": "Cloud Infrastructure & Kubernetes DevOps Engineer",
        "employer": "Enterprise Cloud Services Ltd",
        "district": "Pune District",
        "sector": "Information Technology & Cloud",
        "raw_html": """
        <div class="job-card">
            <h3 class="title">Cloud Infrastructure & Kubernetes DevOps Engineer</h3>
            <p class="desc">
                Deploy and maintain microservices on Kubernetes clusters. Automate multi-cloud infrastructure
                using Terraform and configure zero-downtime CI/CD pipelines with GitOps.
            </p>
            <div class="meta">Location: Magarpatta City, Pune | Vacancies: 120</div>
        </div>
        """
    },
    {
        "title": "Cybersecurity SOC Tier-2 Threat Hunter",
        "employer": "State Financial Data Security Center",
        "district": "Mumbai Metro",
        "sector": "Information Security & Defense",
        "raw_html": """
        <div class="job-card">
            <h3 class="title">Cybersecurity SOC Tier-2 Threat Hunter</h3>
            <p class="desc">
                Monitor security logs, execute MITRE ATT&CK threat hunting, implement Zero Trust access
                controls, and investigate digital forensics incidents across banking cloud endpoints.
            </p>
            <div class="meta">Location: BKC, Mumbai | Vacancies: 60</div>
        </div>
        """
    },
    {
        "title": "Precision Agriculture & Smart Irrigation Specialist",
        "employer": "Nashik Agro-Tech Cooperative Federation",
        "district": "Nashik District",
        "sector": "Agriculture & AgriTech",
        "raw_html": """
        <div class="job-card">
            <h3 class="title">Precision Agriculture & Smart Irrigation Specialist</h3>
            <p class="desc">
                Install IoT soil moisture sensors, automate drip fertigation systems, and interpret
                satellite crop health imagery for high-yield grape and horticulture farming.
            </p>
            <div class="meta">Location: Nashik / Dindori | Vacancies: 75</div>
        </div>
        """
    },
    {
        "title": "Hospital EHR & ABDM Informatics Technician",
        "employer": "Maharashtra District Health Mission",
        "district": "Chhatrapati Sambhajinagar",
        "sector": "Healthcare & Life Sciences",
        "raw_html": """
        <div class="job-card">
            <h3 class="title">Hospital EHR & ABDM Informatics Technician</h3>
            <p class="desc">
                Implement electronic health records (EHR), link patient health IDs to Ayushman Bharat
                Digital Mission (ABDM), and maintain hospital telemedicine telemetry systems.
            </p>
            <div class="meta">Location: Sambhajinagar District | Vacancies: 90</div>
        </div>
        """
    },
    {
        "title": "Industrial Robotics & PLC Automation Engineer",
        "employer": "Waluj Industrial Automation Cluster",
        "district": "Chhatrapati Sambhajinagar",
        "sector": "Advanced Manufacturing & Robotics",
        "raw_html": """
        <div class="job-card">
            <h3 class="title">Industrial Robotics & PLC Automation Engineer</h3>
            <p class="desc">
                Program Siemens and Allen-Bradley PLCs, configure SCADA monitoring stations, and integrate
                6-axis articulated robotic arms for automated assembly lines.
            </p>
            <div class="meta">Location: Waluj MIDC | Vacancies: 65</div>
        </div>
        """
    },
    {
        "title": "DGCA Certified Drone Pilot & LiDAR Maintenance Technician",
        "employer": "State Land Records & Geospatial Mapping Agency",
        "district": "Thane District",
        "sector": "Aerospace & Geospatial",
        "raw_html": """
        <div class="job-card">
            <h3 class="title">DGCA Certified Drone Pilot & LiDAR Maintenance Technician</h3>
            <p class="desc">
                Conduct aerial topography surveys using multirotor drones equipped with LiDAR and multispectral
                cameras. Perform propeller, motor, and avionics field maintenance.
            </p>
            <div class="meta">Location: Thane / Navi Mumbai | Vacancies: 50</div>
        </div>
        """
    }
]


# ============================================================================
# 3. LAYER 2 SKILL EXTRACTION & TAXONOMY MAPPING
# ============================================================================

class SkillExtractionEngine:
    """
    Parses raw job descriptions, extracts competencies, and maps them
    to standard National Classification of Occupations (NCO) and
    National Skills Qualification Framework (NSQF) taxonomies.
    """

    @staticmethod
    def extract_skills_and_taxonomy(title: str, description: str) -> Dict[str, Any]:
        combined_text = f"{title} {description}".lower()

        matched_key = None
        for key in TAXONOMY_MAP:
            if key in combined_text:
                matched_key = key
                break

        if not matched_key:
            # Fallback matching based on tokens
            for key, meta in TAXONOMY_MAP.items():
                if any(k in combined_text for k in key.split()):
                    matched_key = key
                    break

        if not matched_key:
            matched_key = "data analyst"  # Default baseline

        meta = TAXONOMY_MAP[matched_key]

        # Extract specific skills mentioned
        detected_skills = []
        for s in meta["skills"]:
            if s.lower() in combined_text:
                detected_skills.append(s)
        if not detected_skills:
            detected_skills = meta["skills"][:3]

        # Standardized SWAYAM URLs
        search_q = meta["search_query"]
        recommended_courses = [
            {
                "title": f"{matched_key.title()} Masterclass - NPTEL (IIT)",
                "url": f"https://swayam.gov.in/explorer?searchText={quote_plus(search_q)}"
            },
            {
                "title": f"Applied {meta['sector']} - AICTE / SWAYAM",
                "url": f"https://swayam.gov.in/explorer?searchText={quote_plus(matched_key)}"
            }
        ]

        demand_score = meta["default_demand"]
        supply_score = meta["default_supply"]
        deficit = demand_score - supply_score

        gap_analysis = (
            f"NSQF {meta['nsqf_level']}: Market demand is surging ({meta['growth']} YoY) "
            f"while candidate supply in Mahaswayam registers an acute {deficit}% deficit. "
            f"Key competency gaps identified in {', '.join(detected_skills)}."
        )

        return {
            "canonical_role": matched_key.title(),
            "sector": meta["sector"],
            "nco_code": meta["nco_code"],
            "esco_code": meta["esco_code"],
            "nsqf_level": meta["nsqf_level"],
            "extracted_skills": detected_skills,
            "demand_score": demand_score,
            "supply_score": supply_score,
            "deficit_score": deficit,
            "growth_rate_yoy": meta["growth"],
            "gap_analysis": gap_analysis,
            "recommended_courses": recommended_courses,
            "mahaswayam_action_url": "https://rojgar.mahaswayam.gov.in/"
        }


# ============================================================================
# 4. ETL INGESTION AGENT CLASS
# ============================================================================

class IngestionETLAgent:
    """
    Asynchronous ETL Ingestion Pipeline:
    - Fetches/scrapes job postings
    - Parses HTML via BeautifulSoup
    - Extracts skills and maps to NCO / NSQF taxonomies
    - Upserts records into SQLite (skillsync.db)
    """

    def __init__(self, db_session=None):
        self.db = db_session or SessionLocal()
        self.extractor = SkillExtractionEngine()

    def scrape_simulated_postings(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Parses raw job posting HTML records using BeautifulSoup.
        """
        parsed_postings = []
        for raw in SAMPLE_PUBLIC_JOB_POSTINGS[:limit]:
            soup = BeautifulSoup(raw["raw_html"], "html.parser")
            title = soup.find("h3", class_="title")
            desc = soup.find("p", class_="desc")
            meta = soup.find("div", class_="meta")

            title_text = title.get_text(strip=True) if title else raw["title"]
            desc_text = desc.get_text(strip=True) if desc else ""
            meta_text = meta.get_text(strip=True) if meta else ""

            parsed_postings.append({
                "title": title_text,
                "description": desc_text,
                "meta": meta_text,
                "district": raw["district"],
                "sector": raw["sector"]
            })

        return parsed_postings

    def ingest_and_sync(self, limit: int = 10, dry_run: bool = False) -> Dict[str, Any]:
        """
        Runs the full ETL pipeline: Scrape -> Parse -> Map Taxonomies -> Upsert to SQLite.
        """
        logger.info(f"Starting ETL Ingestion pipeline (limit={limit}, dry_run={dry_run})...")
        postings = self.scrape_simulated_postings(limit=limit)
        logger.info(f"Scraped and parsed {len(postings)} job posting documents via BeautifulSoup.")

        inserted_count = 0
        updated_count = 0
        processed_roles = []

        for p in postings:
            extracted = self.extractor.extract_skills_and_taxonomy(p["title"], p["description"])
            canonical_role = extracted["canonical_role"]
            processed_roles.append(canonical_role)

            if dry_run:
                logger.info(f"[DRY-RUN] Extracted Role: {canonical_role} | NCO: {extracted['nco_code']} | NSQF: {extracted['nsqf_level']}")
                continue

            # Upsert into JobRole table
            existing_role = self.db.query(JobRole).filter(JobRole.role == canonical_role).first()
            if existing_role:
                # Update existing record
                existing_role.sector = extracted["sector"]
                existing_role.description = p["description"]
                existing_role.ncs_code = extracted["nco_code"]
                existing_role.esco_code = extracted["esco_code"]
                existing_role.ncs_demand_score = extracted["demand_score"]
                existing_role.mahaswayam_supply_score = extracted["supply_supply"] if "supply_supply" in extracted else extracted["supply_score"]
                existing_role.deficit_score = extracted["deficit_score"]
                existing_role.growth_rate_yoy = extracted["growth_rate_yoy"]
                existing_role.gap_analysis = extracted["gap_analysis"]
                existing_role.recommended_courses = extracted["recommended_courses"]
                existing_role.mahaswayam_action_url = extracted["mahaswayam_action_url"]
                updated_count += 1
            else:
                # Insert new record
                new_role = JobRole(
                    role=canonical_role,
                    sector=extracted["sector"],
                    description=p["description"],
                    ncs_code=extracted["nco_code"],
                    esco_code=extracted["esco_code"],
                    ncs_demand_score=extracted["demand_score"],
                    mahaswayam_supply_score=extracted["supply_score"],
                    deficit_score=extracted["deficit_score"],
                    growth_rate_yoy=extracted["growth_rate_yoy"],
                    gap_analysis=extracted["gap_analysis"],
                    recommended_courses=extracted["recommended_courses"],
                    mahaswayam_action_url=extracted["mahaswayam_action_url"]
                )
                self.db.add(new_role)
                inserted_count += 1

            # Also ensure JobDemand and CandidateSupply tables receive district-level telemetry
            dist = p["district"]
            existing_demand = self.db.query(JobDemand).filter(
                JobDemand.skill_name == canonical_role,
                JobDemand.district == dist
            ).first()

            if not existing_demand:
                self.db.add(JobDemand(
                    skill_id=f"SK-{extracted['nco_code']}",
                    skill_name=canonical_role,
                    category=extracted["sector"],
                    sector=extracted["sector"],
                    demand_score=extracted["demand_score"],
                    growth_rate_yoy=extracted["growth_rate_yoy"],
                    ncs_code=extracted["nco_code"],
                    esco_code=extracted["esco_code"],
                    region="Maharashtra",
                    district=dist,
                    description=p["description"]
                ))

            existing_supply = self.db.query(CandidateSupply).filter(
                CandidateSupply.skill_name == canonical_role,
                CandidateSupply.district == dist
            ).first()

            if not existing_supply:
                self.db.add(CandidateSupply(
                    skill_id=f"SK-{extracted['nco_code']}",
                    skill_name=canonical_role,
                    category=extracted["sector"],
                    sector=extracted["sector"],
                    supply_score=extracted["supply_score"],
                    region="Maharashtra",
                    district=dist,
                    talent_pool_count=int(extracted["supply_score"] * 75)
                ))

        if not dry_run:
            self.db.commit()
            logger.info(f"Database commit successful: {inserted_count} new roles inserted, {updated_count} roles updated.")

        return {
            "status": "success",
            "dry_run": dry_run,
            "postings_scraped": len(postings),
            "roles_inserted": inserted_count,
            "roles_updated": updated_count,
            "processed_roles": list(set(processed_roles))
        }

    def close(self):
        if self.db:
            self.db.close()


# ============================================================================
# 5. STANDALONE CRON EXECUTION BLOCK
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="SkillSetu Asynchronous ETL Ingestion Pipeline (Cron Job)")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of job postings to scrape and process")
    parser.add_argument("--dry-run", action="store_true", help="Parse and extract skills without writing to SQLite")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose debug logging")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    logger.info("Initializing database schema...")
    init_db()

    agent = IngestionETLAgent()
    try:
        results = agent.ingest_and_sync(limit=args.limit, dry_run=args.dry_run)
        print("\n" + "=" * 60)
        print("ETL INGESTION AGENT RUN COMPLETE")
        print("=" * 60)
        print(json.dumps(results, indent=2))
        print("=" * 60 + "\n")
    except Exception as e:
        logger.error(f"ETL Ingestion Agent failed with error: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        agent.close()


if __name__ == "__main__":
    main()
