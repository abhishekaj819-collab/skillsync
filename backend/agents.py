"""
SkillSync Multi-Agent Architecture
Coordinates IngestionAgent, AnalyticsAgent, and CurriculumAgent
for real-time Labour Market Intelligence and SWAYAM Curriculum Matching.
"""

import math
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from database import JobDemand, CandidateSupply, CourseCatalog


# ============================================================================
# 1. IngestionAgent: District & Region Level Data Retrieval
# ============================================================================

class IngestionAgent:
    """
    IngestionAgent is responsible for querying the live database
    for the latest district-level and sector-level labour market demand
    and workforce supply metrics.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_market_telemetry(
        self,
        sector: Optional[str] = None,
        region: Optional[str] = None,
        district: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves paired job demand and workforce supply metrics
        filtered by sector, region, and district.
        """
        # Query Job Demands
        demand_query = self.db.query(JobDemand)
        supply_query = self.db.query(CandidateSupply)

        # Apply sector filter
        if sector and sector.lower() != "all":
            demand_query = demand_query.filter(func.lower(JobDemand.sector) == sector.lower())
            supply_query = supply_query.filter(func.lower(CandidateSupply.sector) == sector.lower())

        # Apply district/region filter
        if district and district.lower() != "all districts":
            demand_query = demand_query.filter(func.lower(JobDemand.district) == district.lower())
            supply_query = supply_query.filter(func.lower(CandidateSupply.district) == district.lower())
        elif region and region.lower() not in ["national", "all"]:
            demand_query = demand_query.filter(func.lower(JobDemand.region) == region.lower())
            supply_query = supply_query.filter(func.lower(CandidateSupply.region) == region.lower())
        else:
            # Default to National baseline
            demand_query = demand_query.filter(JobDemand.region == "National")
            supply_query = supply_query.filter(CandidateSupply.region == "National")

        demands = demand_query.all()
        supplies = supply_query.all()

        # Build lookup map for candidate supply by skill_id
        supply_map = {s.skill_id: s for s in supplies}

        telemetry = []
        for d in demands:
            s = supply_map.get(d.skill_id)
            supply_score = s.supply_score if s else 50
            talent_pool = s.talent_pool_count if s else 5000

            telemetry.append({
                "id": d.skill_id,
                "name": d.skill_name,
                "category": d.category,
                "sector": d.sector,
                "demand_score": d.demand_score,
                "supply_score": supply_score,
                "growth_rate_yoy": d.growth_rate_yoy,
                "ncs_code": d.ncs_code or "NCS-GEN",
                "esco_code": d.esco_code or "ESCO-GEN",
                "region": d.region,
                "district": d.district,
                "talent_pool_count": talent_pool,
                "description": d.description or ""
            })

        return telemetry

    def get_all_skills(self, sector: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns distinct skills from the taxonomy in the database."""
        query = self.db.query(JobDemand).filter(JobDemand.region == "National")
        if sector and sector.lower() != "all":
            query = query.filter(func.lower(JobDemand.sector) == sector.lower())
        
        demands = query.all()
        supplies = {s.skill_id: s.supply_score for s in self.db.query(CandidateSupply).filter(CandidateSupply.region == "National").all()}

        return [
            {
                "id": d.skill_id,
                "name": d.skill_name,
                "category": d.category,
                "sector": d.sector,
                "esco_code": d.esco_code,
                "demand_score": d.demand_score,
                "supply_score": supplies.get(d.skill_id, 50),
                "growth_rate_yoy": d.growth_rate_yoy,
                "ncs_code": d.ncs_code,
                "description": d.description
            }
            for d in demands
        ]


# ============================================================================
# 2. AnalyticsAgent: scikit-learn TF-IDF & Cosine Similarity Engine
# ============================================================================

class AnalyticsAgent:
    """
    AnalyticsAgent is responsible for mathematical and semantic computations:
    - Scikit-learn TF-IDF vectorization and cosine similarity
    - Exact skill gap deltas (demand_score - supply_score)
    - Deficit classifications and national alignment indices
    """

    def __init__(self):
        self.model_type = "scikit-learn TF-IDF & Cosine Similarity"
        self._init_vectorizer()

    def _init_vectorizer(self):
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            self.vectorizer_cls = TfidfVectorizer
            self.cosine_sim_fn = cosine_similarity
            self.has_sklearn = True
        except ImportError:
            self.has_sklearn = False
            self.model_type = "Deterministic TF-IDF Token Fallback"

    def calculate_similarity(self, query: str, document: str) -> float:
        """
        Computes semantic vector cosine similarity between search query
        and course curriculum document text.
        """
        if self.has_sklearn:
            try:
                corpus = [query, document]
                tfidf_matrix = self.vectorizer_cls(
                    stop_words='english',
                    ngram_range=(1, 2),
                    token_pattern=r'(?u)\b[a-zA-Z0-9+#.-]+\b'
                ).fit_transform(corpus)
                sim = float(self.cosine_sim_fn(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
                
                # Direct keyword boost if tokens overlap
                q_words = set(re.findall(r'[a-z0-9+#.-]+', query.lower()))
                d_words = set(re.findall(r'[a-z0-9+#.-]+', document.lower()))
                overlap = q_words.intersection(d_words)
                boost = min(0.35, len(overlap) * 0.10)
                
                return max(0.0, min(1.0, round(sim * 0.75 + boost, 4)))
            except Exception:
                pass  # Fall through to fallback token similarity

        # Robust built-in token TF-IDF fallback
        q_tokens = re.findall(r'[a-z0-9+#.-]+', query.lower())
        d_tokens = re.findall(r'[a-z0-9+#.-]+', document.lower())
        if not q_tokens or not d_tokens:
            return 0.0

        overlap = set(q_tokens).intersection(set(d_tokens))
        base_sim = len(overlap) / (math.sqrt(len(q_tokens)) * math.sqrt(len(d_tokens)) or 1.0)
        return max(0.0, min(0.98, base_sim))

    def compute_skill_gaps(self, raw_telemetry: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates exact skill gap deltas, classifies deficit status,
        and produces aggregated alignment summary indices.
        """
        enriched_skills = []
        total_demand = 0
        total_supply = 0
        critical_deficits = 0
        deprecated_count = 0

        for s in raw_telemetry:
            deficit = s["demand_score"] - s["supply_score"]
            total_demand += s["demand_score"]
            total_supply += s["supply_score"]

            # Classification logic
            if s["demand_score"] < 25 and s["supply_score"] > 50:
                status = "Obsolete / Deprecated"
                status_color = "red"
                deprecated_count += 1
            elif deficit >= 35:
                status = "Critical Deficit"
                status_color = "red"
                critical_deficits += 1
            elif deficit >= 15:
                status = "Moderate Deficit"
                status_color = "yellow"
            elif deficit <= -15:
                status = "Surplus Supply"
                status_color = "blue"
            else:
                status = "Balanced Alignment"
                status_color = "green"

            enriched_skills.append({
                **s,
                "deficit_score": deficit,
                "status": status,
                "status_color": status_color
            })

        # Sort descending by deficit (highest shortage first)
        enriched_skills.sort(key=lambda x: x["deficit_score"], reverse=True)

        n = max(1, len(raw_telemetry))
        avg_demand = round(total_demand / n, 1)
        avg_supply = round(total_supply / n, 1)
        alignment_score = max(0, min(100, round(100 - (abs(avg_demand - avg_supply) * 1.2), 1)))

        return {
            "summary": {
                "average_industry_demand": avg_demand,
                "average_workforce_supply": avg_supply,
                "net_deficit": round(avg_demand - avg_supply, 1),
                "alignment_index": f"{alignment_score}%",
                "critical_shortages_count": critical_deficits,
                "obsolete_skills_flagged": deprecated_count
            },
            "skills": enriched_skills
        }

    def evaluate_candidate_gap(
        self,
        candidate_skills: Any,
        job_requirements: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Executes vectorized PyTorch batch tensor skill gap scoring.
        """
        from engine import evaluate_skill_gap
        return evaluate_skill_gap(candidate_skills, job_requirements)


# ============================================================================
# 3. CurriculumAgent: SWAYAM Recommendations & Obsolescence Governance
# ============================================================================

class CurriculumAgent:
    """
    CurriculumAgent matches industry skill gaps against the SWAYAM/NPTEL
    CourseCatalog stored in the database, evaluating match scores,
    gap closure uplift, and course obsolescence flags.
    """

    def __init__(self, db: Session, analytics_agent: AnalyticsAgent):
        self.db = db
        self.analytics = analytics_agent

    def recommend_curriculum(
        self,
        query: str,
        target_role: Optional[str] = None,
        sector: Optional[str] = None,
        top_k: int = 5,
        known_deficits: Optional[Dict[str, int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Ranks active SWAYAM courses against an input skill query or target role.
        """
        # Fetch active courses from database
        courses = self.db.query(CourseCatalog).filter(CourseCatalog.status == "Active").all()
        query_text = f"{query} {target_role or ''}".strip()
        results = []

        for c in courses:
            skills = c.skills_covered or []
            syllabus = c.syllabus_highlights or []

            doc_text = (
                f"{c.title} "
                f"{' '.join(skills)} "
                f"{' '.join(syllabus)} "
                f"{c.provider} {c.level}"
            )

            sim_score = self.analytics.calculate_similarity(query_text, doc_text)

            # Matched skills overlap
            matched_skills = [
                skill for skill in skills
                if any(q.lower() in skill.lower() or skill.lower() in q.lower() for q in query.split())
            ]

            # Calculate estimated deficit closure potential
            deficit_impact = 15
            if known_deficits:
                for skill_name in skills:
                    for k_name, def_val in known_deficits.items():
                        if k_name.lower() in skill_name.lower() or skill_name.lower() in k_name.lower():
                            deficit_impact = max(deficit_impact, def_val)

            results.append({
                "course_id": c.course_id,
                "title": c.title,
                "provider": c.provider,
                "platform": c.platform,
                "instructor": c.instructor or "Faculty Panel",
                "duration_weeks": c.duration_weeks,
                "credits": c.credits,
                "level": c.level,
                "status": c.status,
                "enrolled_count": c.enrolled_count,
                "rating": c.rating,
                "match_score": round(sim_score * 100, 1),
                "matched_skills": matched_skills or skills[:2],
                "syllabus_highlights": syllabus,
                "alignment_status": c.alignment_status,
                "recommendation_reason": c.recommendation_reason or "Addresses identified industry deficit.",
                "gap_closure_potential": f"+{deficit_impact}% alignment uplift"
            })

        # Sort descending by match score
        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results[:top_k]

    def get_obsolete_courses(self) -> List[Dict[str, Any]]:
        """
        Retrieves obsolete courses from the CourseCatalog database
        with their designated replacement curricula.
        """
        obsolete_records = self.db.query(CourseCatalog).filter(CourseCatalog.status == "Obsolete").all()
        obsolete_items = []

        for c in obsolete_records:
            obsolete_items.append({
                "course_id": c.course_id,
                "title": c.title,
                "provider": c.provider,
                "platform": c.platform,
                "status": c.status,
                "enrolled_count": c.enrolled_count,
                "rating": c.rating,
                "deprecation_reason": c.recommendation_reason or "Market demand decline.",
                "action_required": c.action_required or "Curriculum Audit",
                "recommended_replacement": {
                    "course_id": c.replacement_course_id,
                    "title": c.replacement_title
                }
            })

        return obsolete_items

    def recommend_for_critical_gaps(
        self,
        critical_gaps: List[Dict[str, Any]],
        top_k_per_gap: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Retrieves SWAYAM and NPTEL courses from the database specifically
        targeting the highest-impact critical gaps.
        """
        targeted_courses = []
        seen_course_ids = set()

        for gap in critical_gaps:
            skill_name = gap["skill_name"]
            recs = self.recommend_curriculum(
                query=skill_name,
                top_k=top_k_per_gap,
                known_deficits={skill_name: int(gap.get("gap_impact", 1.0) * 100)}
            )
            for r in recs:
                if r["course_id"] not in seen_course_ids:
                    seen_course_ids.add(r["course_id"])
                    targeted_courses.append({
                        **r,
                        "targeted_gap_skill": skill_name,
                        "gap_impact": gap.get("gap_impact", 0.0),
                        "match_type": gap.get("match_type", "Missing")
                    })

        return targeted_courses


# ============================================================================
# 4. SkillSyncOrchestrator: Multi-Agent Coordinator
# ============================================================================

class SkillSyncOrchestrator:
    """
    Coordinates IngestionAgent, AnalyticsAgent, and CurriculumAgent to deliver
    end-to-end Labour Market Intelligence and SWAYAM recommendation workflows.
    """

    def __init__(self, db: Session):
        self.db = db
        self.ingestion = IngestionAgent(db)
        self.analytics = AnalyticsAgent()
        self.curriculum = CurriculumAgent(db, self.analytics)

    def orchestrate_gap_analysis(
        self,
        sector: Optional[str] = None,
        region: Optional[str] = None,
        district: Optional[str] = None
    ) -> Dict[str, Any]:
        """Orchestrates LMI gap analysis from DB telemetry through analytics calculations."""
        # 1. Ingestion Agent fetches raw telemetry
        raw_telemetry = self.ingestion.get_market_telemetry(sector=sector, region=region, district=district)

        # 2. Analytics Agent computes skill gap deltas
        analysis = self.analytics.compute_skill_gaps(raw_telemetry)

        region_display = district if district and district.lower() != "all districts" else (region or "National (India - Mahaswayam & NCS Integration)")

        return {
            "metadata": {
                "sector": sector or "All Sectors",
                "region": region_display,
                "total_skills_analyzed": len(analysis["skills"]),
                "engine_status": self.analytics.model_type,
                "taxonomy_standard": "Lightcast / ESCO v1.1"
            },
            "summary": analysis["summary"],
            "skills": analysis["skills"]
        }

    def orchestrate_candidate_gap_analysis(
        self,
        candidate_skills: Any,
        job_requirements: List[Dict[str, Any]],
        top_k_courses: int = 3
    ) -> Dict[str, Any]:
        """
        Orchestrates vectorized candidate skill gap evaluation and directly connects
        the top 3 highest-impact critical gaps to targeted SWAYAM/NPTEL curriculum recommendations.
        """
        # 1. AnalyticsAgent evaluates gaps via vectorized tensor operations
        gap_eval = self.analytics.evaluate_candidate_gap(candidate_skills, job_requirements)

        # 2. CurriculumAgent retrieves courses targeting top critical gaps
        critical_gaps = gap_eval.get("critical_gaps", [])
        targeted_courses = self.curriculum.recommend_for_critical_gaps(
            critical_gaps=critical_gaps,
            top_k_per_gap=1
        )

        return {
            "candidate_skills_analyzed": len(candidate_skills) if isinstance(candidate_skills, (dict, list)) else 0,
            "job_requirements_count": len(job_requirements),
            "overall_coverage": gap_eval["overall_coverage"],
            "overall_match_percentage": gap_eval["overall_match_percentage"],
            "model_used": "PyTorch Vectorized Batch Tensor Cosine Engine (SentenceTransformer all-MiniLM-L6-v2)",
            "detailed_gaps": gap_eval["detailed_gaps"],
            "critical_gaps": critical_gaps,
            "recommended_courses": targeted_courses[:top_k_courses]
        }

    def orchestrate_recommendations(
        self,
        query: str,
        target_role: Optional[str] = None,
        sector: Optional[str] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """Orchestrates SWAYAM course recommendations using NLP semantic matching."""
        # 1. Ingest known skill deficits for uplift calculation
        raw_telemetry = self.ingestion.get_market_telemetry(sector=sector)
        known_deficits = {s["name"]: s["demand_score"] - s["supply_score"] for s in raw_telemetry}

        # 2. Curriculum Agent matches and ranks courses
        recommendations = self.curriculum.recommend_curriculum(
            query=query,
            target_role=target_role,
            sector=sector,
            top_k=top_k,
            known_deficits=known_deficits
        )

        total_active_courses = self.db.query(CourseCatalog).filter(CourseCatalog.status == "Active").count()

        return {
            "query": query,
            "target_role": target_role or "Unspecified",
            "model_used": self.analytics.model_type,
            "total_courses_evaluated": total_active_courses,
            "recommendations": recommendations
        }

    def orchestrate_obsolete_courses(self) -> Dict[str, Any]:
        """Orchestrates obsolete curriculum identification and migration mapping."""
        obsolete_courses = self.curriculum.get_obsolete_courses()
        return {
            "total_flagged_courses": len(obsolete_courses),
            "audit_standard": "NCS & Mahaswayam Curricular Quality Directive 2026",
            "obsolete_courses": obsolete_courses
        }

    def orchestrate_skills(self, sector: Optional[str] = None) -> Dict[str, Any]:
        """Returns indexed taxonomy skills."""
        skills = self.ingestion.get_all_skills(sector=sector)
        return {
            "total": len(skills),
            "skills": skills
        }

