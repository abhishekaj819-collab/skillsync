"""
SkillSync / SkillSetu FastAPI Backend Service
Production-Grade Multi-Agent Architecture with SQLAlchemy Database Integration.
Orchestrates IngestionAgent, AnalyticsAgent, and CurriculumAgent.
Provides PyTorch vector search against live SQLite database for job roles and SWAYAM courses.

SIH PS 26134 — Bridging Skills to Industry | Govt. of Maharashtra
"""

import sys
import re
import traceback
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any, Tuple
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import init_db, get_db, JobDemand, CandidateSupply
from agents import SkillSyncOrchestrator
from engine import search_job_roles


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes the database schema and seeds initial records on startup."""
    init_db()
    yield


app = FastAPI(
    title="SkillSetu Multi-Agent LMI & Curriculum Alignment API",
    description="Production Multi-Agent Labour-Market Intelligence & SWAYAM Curriculum Matching Engine",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS for buildless frontend and cross-origin hackathon consumption
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Maharashtra Districts Taxonomy & Query Parser
# ============================================================================

MAHARASHTRA_DISTRICTS = {
    "pune", "mumbai", "nagpur", "nashik", "aurangabad", "chhatrapati sambhajinagar",
    "sambhajinagar", "thane", "kolhapur", "solapur", "amravati", "nanded", "jalgaon",
    "akola", "latur", "dhule", "ahmednagar", "ahilyanagar", "chandrapur", "parbhani",
    "jalna", "satara", "beed", "yavatmal", "gondia", "wardha", "bhandara",
    "gadchiroli", "washim", "hingoli", "ratnagiri", "sindhudurg", "raigad",
    "palghar", "nandurbar", "osmanabad", "dharashiv"
}


def parse_location_query(raw_query: str) -> tuple[Optional[str], str]:
    """
    When a query contains a hyphen (e.g., 'Pune - Software Engineer'),
    splits the string, extracts the geographic district to filter district-level
    metrics, and returns ONLY the occupation string for the PyTorch embedding model
    so semantic similarity math is not distorted by the city name.
    """
    if not raw_query:
        return None, ""

    clean_str = raw_query.strip()
    # Check for hyphens, en-dashes, or em-dashes
    if any(h in clean_str for h in ["-", "—", "–"]):
        parts = [p.strip() for p in re.split(r'[-—–]', clean_str) if p.strip()]
        if len(parts) >= 2:
            first_lower = parts[0].lower()
            last_lower = parts[-1].lower()

            if first_lower in MAHARASHTRA_DISTRICTS:
                district = parts[0]
                occupation = " - ".join(parts[1:]).strip()
                return district, occupation
            elif last_lower in MAHARASHTRA_DISTRICTS:
                district = parts[-1]
                occupation = " - ".join(parts[:-1]).strip()
                return district, occupation
            else:
                # Default: first part is district, remainder is occupation
                district = parts[0]
                occupation = " - ".join(parts[1:]).strip()
                return district, occupation

    return None, clean_str


# ============================================================================
# Request Models
# ============================================================================

class SearchRequest(BaseModel):
    query: str = Field(..., example="Pune - Software Engineer", description="Target job title or location - role query")
    district: Optional[str] = Field(None, example="Pune", description="Optional explicit geographic district filter")
    top_k: Optional[int] = Field(5, ge=1, le=20, description="Maximum number of matched roles to return")


class CurriculumRecommendationRequest(BaseModel):
    query: str = Field(..., example="Generative AI LLM RAG pipelines", description="Target skills or job description keywords")
    target_role: Optional[str] = Field(None, example="Lead AI Engineer", description="Target job title or NCS role")
    sector: Optional[str] = Field(None, example="Information Technology", description="Industry sector filter")
    top_k: Optional[int] = Field(5, ge=1, le=20, description="Maximum number of recommendations to return")


class JobRequirement(BaseModel):
    name: str = Field(..., example="ReactJS", description="Required skill name")
    required_proficiency: int = Field(4, ge=1, le=5, description="Required proficiency level (1-5)")
    weight: float = Field(1.0, ge=0.0, le=1.0, description="Importance weight (0.0 to 1.0)")


class CandidateGapAnalysisRequest(BaseModel):
    candidate_skills: Dict[str, int] = Field(
        ...,
        example={"React": 3, "JavaScript": 4, "Docker": 2},
        description="Candidate skill proficiency sliders (1-5)"
    )
    job_requirements: List[JobRequirement] = Field(
        ...,
        example=[
            {"name": "ReactJS", "required_proficiency": 4, "weight": 0.8},
            {"name": "Kubernetes & Cloud-Native Microservices", "required_proficiency": 4, "weight": 1.0}
        ],
        description="Target job vacancy skill profile"
    )
    top_k_courses: Optional[int] = Field(3, ge=1, le=10, description="Number of targeted course recommendations")


# ============================================================================
# API Routes
# ============================================================================

@app.get("/", tags=["Health"])
def root_status(db: Session = Depends(get_db)):
    orchestrator = SkillSyncOrchestrator(db)
    return {
        "service": "SkillSetu Multi-Agent LMI & Curriculum Engine",
        "status": "online",
        "version": "2.0.0",
        "architecture": "Multi-Agent System (IngestionAgent, AnalyticsAgent, CurriculumAgent)",
        "model_backend": orchestrator.analytics.model_type,
        "docs_url": "/docs"
    }


@app.get("/api/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    orchestrator = SkillSyncOrchestrator(db)
    skills_data = orchestrator.orchestrate_skills()
    return {
        "status": "healthy",
        "engine": orchestrator.analytics.model_type,
        "taxonomy_skills_count": skills_data["total"],
        "agents": ["IngestionAgent", "AnalyticsAgent", "CurriculumAgent"],
        "database": "SQLAlchemy (Live SQLite/Postgres)",
        "standards": ["Lightcast", "ESCO v1.1", "NCS India", "SWAYAM", "Mahaswayam"]
    }


# ============================================================================
# Vector Search Endpoint (PyTorch Tensor Cosine Similarity against SQLite)
# ============================================================================

@app.post("/api/search", tags=["Semantic Search & Alignment"])
def search_job_roles_endpoint(
    payload: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    Performs real vector similarity search against the seeded SQLite database
    using PyTorch sentence-transformer cosine similarity.
    Parses hyphenated location queries (e.g., 'Pune - Software Engineer')
    to filter district metrics and vectorizes only the occupation.
    """
    try:
        district_parsed, occupation = parse_location_query(payload.query)
        effective_district = payload.district or district_parsed
        search_term = occupation if occupation else payload.query
        return search_job_roles(
            db=db,
            query=search_term,
            top_k=payload.top_k or 5,
            district=effective_district
        )
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"Vector search failed: {str(e)}")


@app.get("/api/search", tags=["Semantic Search & Alignment"])
def search_job_roles_get_endpoint(
    query: str = Query(..., description="Target job title or location - role query"),
    district: Optional[str] = Query(None, description="Optional geographic district filter"),
    top_k: Optional[int] = Query(5, ge=1, le=20, description="Max results"),
    db: Session = Depends(get_db)
):
    """
    GET variant of vector similarity search against the seeded SQLite database.
    Parses hyphenated location queries (e.g., 'Pune - Software Engineer')
    to filter district metrics and vectorizes only the occupation.
    """
    try:
        district_parsed, occupation = parse_location_query(query)
        effective_district = district or district_parsed
        search_term = occupation if occupation else query
        return search_job_roles(
            db=db,
            query=search_term,
            top_k=top_k or 5,
            district=effective_district
        )
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"Vector search failed: {str(e)}")


# ============================================================================
# Multi-Agent LMI & Candidate Gap Analysis Endpoints
# ============================================================================

@app.get("/api/gap-analysis", tags=["Labour Market Intelligence"])
def gap_analysis_endpoint(
    sector: Optional[str] = Query(None, description="Filter by sector e.g. 'Information Technology'"),
    region: Optional[str] = Query(None, description="Filter by region e.g. 'Maharashtra' or 'National'"),
    district: Optional[str] = Query(None, description="Filter by district e.g. 'Pune', 'Mumbai', 'Bengaluru'"),
    db: Session = Depends(get_db)
):
    """
    Orchestrates IngestionAgent and AnalyticsAgent to return demand vs supply metrics,
    exact deficit scores, and skill classifications derived from database telemetry.
    """
    try:
        orchestrator = SkillSyncOrchestrator(db)
        return orchestrator.orchestrate_gap_analysis(
            sector=sector,
            region=region,
            district=district
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gap analysis calculation failed: {str(e)}")


@app.post("/api/gap-analysis", tags=["Labour Market Intelligence & Candidate Evaluation"])
def candidate_gap_analysis_endpoint(
    payload: CandidateGapAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Vectorized candidate-to-job skill gap scoring engine using single-pass
    SentenceTransformer batch encoding and PyTorch tensor matrix multiplication.
    Retrieves SWAYAM and NPTEL courses targeting exclusively the top 3 highest-impact gaps.
    """
    try:
        orchestrator = SkillSyncOrchestrator(db)
        job_reqs = [r.model_dump() for r in payload.job_requirements]
        return orchestrator.orchestrate_candidate_gap_analysis(
            candidate_skills=payload.candidate_skills,
            job_requirements=job_reqs,
            top_k_courses=payload.top_k_courses or 3
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Candidate gap analysis failed: {str(e)}")


@app.post("/api/recommend-curriculum", tags=["Curriculum Recommendations"])
def recommend_curriculum_endpoint(
    payload: CurriculumRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Orchestrates AnalyticsAgent (TF-IDF semantic cosine similarity) and CurriculumAgent
    to match industry requirements to SWAYAM/Mahaswayam courses.
    """
    try:
        orchestrator = SkillSyncOrchestrator(db)
        return orchestrator.orchestrate_recommendations(
            query=payload.query,
            target_role=payload.target_role,
            sector=payload.sector,
            top_k=payload.top_k or 5
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation engine error: {str(e)}")


@app.get("/api/obsolete-courses", tags=["Curriculum Governance"])
def obsolete_courses_endpoint(db: Session = Depends(get_db)):
    """
    Orchestrates CurriculumAgent to list courses with severe market demand obsolescence
    and map them to modern curriculum replacements.
    """
    try:
        orchestrator = SkillSyncOrchestrator(db)
        return orchestrator.orchestrate_obsolete_courses()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch obsolete courses: {str(e)}")


@app.get("/api/skills", tags=["Taxonomy"])
def list_skills_endpoint(
    sector: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns all indexed taxonomy skills with current demand and supply scores
    via IngestionAgent.
    """
    try:
        orchestrator = SkillSyncOrchestrator(db)
        return orchestrator.orchestrate_skills(sector=sector)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list skills: {str(e)}")


# ============================================================================
# /api/v1/ VERSIONED ENDPOINTS (SIH 26134 SkillSetu Deck-Aligned)
# ============================================================================

# Static district profiles aligned with deck KPIs
_DISTRICT_PROFILES: Dict[str, Any] = {
    "pune": {
        "district": "Pune",
        "zone": "Western Maharashtra Tech & Auto Hub",
        "total_demand": 174600,
        "total_supply": 102300,
        "placement_rate": 84.2,
        "active_openings": 4820,
        "key_sectors": ["AI & Machine Learning", "EV Powertrain", "Industrial IoT", "Cloud DevOps"],
        "top_skills_demanded": ["PyTorch", "CAN-bus", "PLC Programming", "AWS", "React"],
        "demand_signals": "Automotive CNC & EV Battery Tech demand up 42% in Pune MIDC",
        "alignment_score": 58.6,
        "deficit_rate": -41.4,
    },
    "mumbai": {
        "district": "Mumbai MMR",
        "zone": "Konkan Metro - FinTech & Cloud Enterprise",
        "total_demand": 149400,
        "total_supply": 88200,
        "placement_rate": 88.7,
        "active_openings": 7150,
        "key_sectors": ["BFSI & FinTech", "Cloud Infrastructure", "Cyber Security", "GenAI"],
        "top_skills_demanded": ["Python", "Kafka", "SIEM", "LangChain", "Kubernetes"],
        "demand_signals": "Cloud Infrastructure and GenAI hiring up 28% in Navi Mumbai",
        "alignment_score": 59.0,
        "deficit_rate": -41.0,
    },
    "nagpur": {
        "district": "Nagpur",
        "zone": "Vidarbha Industrial & Logistics MIHAN",
        "total_demand": 72900,
        "total_supply": 36300,
        "placement_rate": 58.4,
        "active_openings": 2340,
        "key_sectors": ["Aviation MRO", "Logistics Automation", "Renewable Energy", "Embedded Systems"],
        "top_skills_demanded": ["Avionics Maintenance", "AGV Systems", "Solar PV", "AUTOSAR", "PLC"],
        "demand_signals": "Solar Technician & PLC vacancies surging in Nagpur ITI zone",
        "alignment_score": 49.8,
        "deficit_rate": -50.2,
    },
    "thane": {
        "district": "Thane",
        "zone": "MMR Industrial Corridor - Pharma & IT",
        "total_demand": 57600,
        "total_supply": 32400,
        "placement_rate": 72.5,
        "active_openings": 1950,
        "key_sectors": ["Pharmaceuticals", "Full-Stack IT", "Logistics SCM", "Life Sciences"],
        "top_skills_demanded": ["HPLC", "React", "SAP SCM", "Python", "Power BI"],
        "demand_signals": "Pharma QC and Full-Stack roles growing 30% in Thane industrial belt",
        "alignment_score": 56.2,
        "deficit_rate": -43.8,
    },
    "nashik": {
        "district": "Nashik",
        "zone": "Northern Maharashtra - Agri-Tech & Auto Components",
        "total_demand": 55800,
        "total_supply": 29400,
        "placement_rate": 64.3,
        "active_openings": 1680,
        "key_sectors": ["Automotive Manufacturing", "Food Processing", "Precision Agri-Tech", "Healthcare"],
        "top_skills_demanded": ["Welding CWI", "HACCP", "Drone NDVI", "ABDM FHIR", "CAD/CAM"],
        "demand_signals": "Agri-Tech and Food Processing hiring rising 25% in Nashik district",
        "alignment_score": 52.7,
        "deficit_rate": -47.3,
    },
    "chhatrapati_sambhajinagar": {
        "district": "Chhatrapati Sambhajinagar",
        "zone": "Marathwada Industrial Region - Precision Engineering",
        "total_demand": 52500,
        "total_supply": 26100,
        "placement_rate": 61.8,
        "active_openings": 1420,
        "key_sectors": ["Die Casting & Engineering", "HVAC & Refrigeration", "Digital Commerce", "EV Components"],
        "top_skills_demanded": ["CAD/CAM", "CNC Machining", "Refrigeration Systems", "Digital Marketing", "SEO"],
        "demand_signals": "CNC & CAD/CAM precision engineering vacancies up 32% in Marathwada",
        "alignment_score": 49.7,
        "deficit_rate": -50.3,
    },
}


@app.get("/api/v1/districts", tags=["SkillSetu v1 - Districts LMI"])
def districts_alignment_endpoint(
    district: Optional[str] = Query(None, description="Filter by district slug (pune, mumbai, nagpur, thane, nashik, chhatrapati_sambhajinagar)"),
    db: Session = Depends(get_db)
):
    """
    Returns aggregated alignment data and demand signals for key Maharashtra districts.
    Dynamically overrides static profiles with live DB telemetry when available.
    SIH PS 26134 - SkillSetu deck-aligned district intelligence endpoint.
    """
    import torch
    import torch.nn.functional as F

    result = []
    profiles = _DISTRICT_PROFILES
    target_keys = [district.lower().replace(" ", "_")] if district else list(profiles.keys())

    for key in target_keys:
        profile = profiles.get(key)
        if not profile:
            continue

        profile_out = dict(profile)
        dist_name = profile["district"]

        # Attempt live DB override
        try:
            d_recs = db.query(JobDemand).filter(JobDemand.district.ilike(f"%{dist_name.split()[0]}%")).all()
            s_recs = db.query(CandidateSupply).filter(CandidateSupply.district.ilike(f"%{dist_name.split()[0]}%")).all()
            if d_recs and s_recs:
                db_demand = int(sum(r.demand_score * 1800 for r in d_recs))
                db_supply = int(sum(r.talent_pool_count for r in s_recs))
                if db_demand > 0:
                    profile_out["total_demand"] = db_demand
                    profile_out["total_supply"] = db_supply
                    profile_out["alignment_score"] = round(db_supply / db_demand * 100, 1)
                    profile_out["deficit_rate"] = round((db_supply - db_demand) / db_demand * 100, 1)
                    profile_out["data_source"] = "live_db"
        except Exception:
            profile_out["data_source"] = "static_deck"

        if "data_source" not in profile_out:
            profile_out["data_source"] = "static_deck"

        result.append(profile_out)

    return {
        "status": "success",
        "tagline": "Bridging Skills to Industry | Govt. of Maharashtra (PS 26134)",
        "deck_kpis": {
            "curriculum_agility": "80%+ revision latency cut from years to days",
            "placement_acceleration": "35%+ projected lift across pilot ITIs",
            "districts_covered": "36 Districts statewide labour-market intelligence",
            "tco_per_citizen": "< INR 2 projected TCO per citizen/year on serverless Modal compute",
        },
        "total_districts": len(result),
        "districts": result,
    }


@app.post("/api/v1/search", tags=["SkillSetu v1 - Semantic Search"])
def v1_search_endpoint(
    payload: SearchRequest,
    db: Session = Depends(get_db)
):
    """Versioned search alias — identical to /api/search but under /api/v1/ namespace."""
    try:
        district_parsed, occupation = parse_location_query(payload.query)
        effective_district = payload.district or district_parsed
        search_term = occupation if occupation else payload.query
        return search_job_roles(
            db=db, query=search_term, top_k=payload.top_k or 5,
            district=effective_district
        )
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Vector search failed: {str(e)}")


@app.get("/api/v1/gap-analysis", tags=["SkillSetu v1 - Labour Market Intelligence"])
def v1_gap_analysis_endpoint(
    sector: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Versioned gap-analysis alias — queries live SQLite DB via SkillSyncOrchestrator."""
    try:
        orchestrator = SkillSyncOrchestrator(db)
        return orchestrator.orchestrate_gap_analysis(
            sector=sector, region=region, district=district
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gap analysis failed: {str(e)}")


# ============================================================================
# Autonomous Multi-Agent System Endpoints (Auth, Scraper, Vector, Policy)
# ============================================================================

class LoginRequest(BaseModel):
    identifier: str = Field(..., example="director@mah.gov.in", description="Gov-Tech credential (email or ITI code)")
    password: Optional[str] = Field(None, example="GovTech@2026", description="Optional secure password string")


@app.post("/api/v1/auth/login", tags=["Agent 1: Auth & Security Supervisor"])
def auth_login_endpoint(payload: LoginRequest):
    """
    Validates Gov-Tech credentials via regex rules and issues a cryptographic JWT token:
    - Govt: director@mah.gov.in (Role: 'gov', Clearance: 3)
    - ITI: ITI-PUN-2045 (Role: 'iti', Clearance: 2)
    - Employer: hr@industry.com (Role: 'emp', Clearance: 1)
    """
    try:
        from agents.auth_agent import get_auth_agent
        agent = get_auth_agent()
        return agent.validate_and_authenticate(identifier=payload.identifier, password=payload.password)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auth Supervisor failed: {str(e)}")


@app.get("/api/v1/auth/audit-logs", tags=["Agent 1: Auth & Security Supervisor"])
def get_audit_logs_endpoint(
    limit: int = Query(50, ge=1, le=200),
    role: Optional[str] = Query(None)
):
    """Retrieves SQLite audit trail of all logins and district data access."""
    try:
        from agents.auth_agent import get_auth_agent
        agent = get_auth_agent()
        return agent.get_audit_trail(limit=limit, role_filter=role)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit retrieval failed: {str(e)}")


@app.post("/api/v1/agents/scraper/run", tags=["Agent 2: LMI Scraper Agent"])
def run_lmi_scraper_endpoint(db: Session = Depends(get_db)):
    """Runs the 12-hour LMI Scraper pipeline, stripping PII and normalizing live feeds."""
    try:
        from agents.scraper_agent import LMIScraperAgent
        agent = LMIScraperAgent()
        records = agent.scrape_and_process_feeds()
        updated_count = agent.sync_to_database(db)
        return {
            "status": "SUCCESS",
            "agent": agent.agent_name,
            "feeds_processed": len(records),
            "skills_extracted_count": agent.total_signals_ingested,
            "db_records_synced": updated_count,
            "sample_dossiers": records[:2]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraper Agent failed: {str(e)}")


@app.post("/api/v1/agents/vector/analyze", tags=["Agent 3: Vector Gap-Analysis Agent"])
def run_vector_gap_analysis_endpoint():
    """
    Computes PyTorch 384-dimensional cosine similarity mismatch between live industry demand
    and static ITI trade curricula. Flags all modules below 75% similarity.
    """
    try:
        from agents.scraper_agent import LMIScraperAgent
        from agents.vector_agent import VectorGapAnalysisAgent

        scraper = LMIScraperAgent()
        feeds = scraper.scrape_and_process_feeds()

        vector_agent = VectorGapAnalysisAgent()
        dossiers = vector_agent.analyze_curriculum_gaps(feeds)

        return {
            "status": "SUCCESS",
            "agent": vector_agent.agent_name,
            "threshold_applied": "75.0%",
            "total_modules_evaluated": len(dossiers),
            "critical_deficits_count": sum(1 for d in dossiers if d["is_deficit"]),
            "gap_dossiers": dossiers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector Gap Analysis failed: {str(e)}")


@app.get("/api/v1/agents/policy/directives", tags=["Agent 4: Policy Routing & Notification Agent"])
def get_policy_directives_endpoint(
    role: str = Query("gov", description="Role: 'gov' (capital budget) or 'iti' (syllabus diffs)"),
    district: Optional[str] = Query(None, description="Optional district filter for ITI Principal")
):
    """
    Translates vector deficits into human-actionable Gov-Tech directives
    and routes them strictly to the designated stakeholder dashboard.
    """
    try:
        from agents.scraper_agent import LMIScraperAgent
        from agents.vector_agent import VectorGapAnalysisAgent
        from agents.policy_agent import get_policy_agent

        scraper = LMIScraperAgent()
        feeds = scraper.scrape_and_process_feeds()

        vector_agent = VectorGapAnalysisAgent()
        dossiers = vector_agent.analyze_curriculum_gaps(feeds)

        policy_agent = get_policy_agent()
        policy_agent.generate_directives_from_gaps(dossiers)

        directives = policy_agent.get_directives_for_role(role=role, district_filter=district)
        return {
            "status": "SUCCESS",
            "stakeholder_role": role,
            "district_scope": district or "All Designated",
            "total_directives": len(directives),
            "directives": directives
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy Agent failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

