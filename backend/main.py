"""
SkillSync / SkillSetu FastAPI Backend Service
Production-Grade Multi-Agent Architecture with SQLAlchemy Database Integration.
Orchestrates IngestionAgent, AnalyticsAgent, and CurriculumAgent.
Provides PyTorch vector search against live SQLite database for job roles and SWAYAM courses.
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

from database import init_db, get_db
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
