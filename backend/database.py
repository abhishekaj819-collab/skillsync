"""
SkillSync Database Layer (SQLAlchemy)
Supports SQLite for zero-dependency local/hackathon testing,
and PostgreSQL for cloud/production deployment via DATABASE_URL.
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Generator
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ============================================================================
# Database Configuration & Session Management
# ============================================================================

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./skillsync.db")

# SQLite requires check_same_thread=False for multithreaded FastAPI requests
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding database sessions per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Database Schema Models
# ============================================================================

class JobDemand(Base):
    """Stores Labour Market Intelligence (LMI) employer demand telemetry."""
    __tablename__ = "job_demands"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    skill_id = Column(String(50), index=True, nullable=False)
    skill_name = Column(String(255), index=True, nullable=False)
    category = Column(String(100), index=True, nullable=False)
    sector = Column(String(100), index=True, nullable=False)
    demand_score = Column(Integer, nullable=False)
    growth_rate_yoy = Column(String(20), default="0%")
    ncs_code = Column(String(50), nullable=True)
    esco_code = Column(String(50), nullable=True)
    region = Column(String(100), default="National", index=True)
    district = Column(String(100), default="All Districts", index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.skill_id,
            "name": self.skill_name,
            "category": self.category,
            "sector": self.sector,
            "demand_score": self.demand_score,
            "growth_rate_yoy": self.growth_rate_yoy,
            "ncs_code": self.ncs_code,
            "esco_code": self.esco_code,
            "region": self.region,
            "district": self.district,
            "description": self.description
        }


class CandidateSupply(Base):
    """Stores workforce talent pool supply metrics across districts and regions."""
    __tablename__ = "candidate_supplies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    skill_id = Column(String(50), index=True, nullable=False)
    skill_name = Column(String(255), index=True, nullable=False)
    category = Column(String(100), index=True, nullable=False)
    sector = Column(String(100), index=True, nullable=False)
    supply_score = Column(Integer, nullable=False)
    region = Column(String(100), default="National", index=True)
    district = Column(String(100), default="All Districts", index=True)
    talent_pool_count = Column(Integer, default=1000)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "category": self.category,
            "sector": self.sector,
            "supply_score": self.supply_score,
            "region": self.region,
            "district": self.district,
            "talent_pool_count": self.talent_pool_count
        }


class CourseCatalog(Base):
    """Stores SWAYAM, NPTEL, and Mahaswayam course repository and curriculum audits."""
    __tablename__ = "course_catalogs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    course_id = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    provider = Column(String(150), nullable=False)
    platform = Column(String(100), default="SWAYAM")
    instructor = Column(String(150), nullable=True)
    duration_weeks = Column(Integer, default=8)
    credits = Column(Integer, default=3)
    level = Column(String(100), default="Undergraduate")
    status = Column(String(50), default="Active", index=True)  # "Active" or "Obsolete"
    enrolled_count = Column(Integer, default=0)
    rating = Column(Float, default=4.5)
    skills_covered = Column(JSON, default=list)
    syllabus_highlights = Column(JSON, default=list)
    alignment_status = Column(String(100), default="High Alignment")
    recommendation_reason = Column(Text, nullable=True)
    replacement_course_id = Column(String(50), nullable=True)
    replacement_title = Column(String(255), nullable=True)
    action_required = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "course_id": self.course_id,
            "title": self.title,
            "provider": self.provider,
            "platform": self.platform,
            "instructor": self.instructor,
            "duration_weeks": self.duration_weeks,
            "credits": self.credits,
            "level": self.level,
            "status": self.status,
            "enrolled_count": self.enrolled_count,
            "rating": self.rating,
            "skills_covered": self.skills_covered or [],
            "syllabus_highlights": self.syllabus_highlights or [],
            "alignment_status": self.alignment_status,
            "recommendation_reason": self.recommendation_reason,
            "replacement_course_id": self.replacement_course_id,
            "replacement_title": self.replacement_title,
            "action_required": self.action_required
        }


# ============================================================================
# Database Seeding & Migration Logic
# ============================================================================

def seed_database(db: Session) -> None:
    """Seeds static mock data from engine.py into the live database if tables are empty."""
    from engine import TAXONOMY_SKILLS, SWAYAM_COURSES

    # 1. Seed Job Demands and Candidate Supplies
    existing_demands = db.query(JobDemand).count()
    if existing_demands == 0:
        districts = ["Pune", "Mumbai", "Nagpur", "Bengaluru", "Hyderabad", "Delhi NCR"]

        for skill in TAXONOMY_SKILLS:
            # National baseline
            demand_nat = JobDemand(
                skill_id=skill["id"],
                skill_name=skill["name"],
                category=skill["category"],
                sector=skill["sector"],
                demand_score=skill["demand_score"],
                growth_rate_yoy=skill["growth_rate_yoy"],
                ncs_code=skill.get("ncs_code"),
                esco_code=skill.get("esco_code"),
                region="National",
                district="All Districts",
                description=skill.get("description", "")
            )
            supply_nat = CandidateSupply(
                skill_id=skill["id"],
                skill_name=skill["name"],
                category=skill["category"],
                sector=skill["sector"],
                supply_score=skill["supply_score"],
                region="National",
                district="All Districts",
                talent_pool_count=15000 + (skill["supply_score"] * 120)
            )
            db.add(demand_nat)
            db.add(supply_nat)

            # District variations for LMI drill-downs
            for idx, dist in enumerate(districts):
                # Deterministic variance per district
                delta_d = ((idx * 7 + len(skill["name"])) % 11) - 5
                delta_s = ((idx * 5 + len(skill["category"])) % 9) - 4
                
                d_score = max(5, min(100, skill["demand_score"] + delta_d))
                s_score = max(5, min(100, skill["supply_score"] + delta_s))

                db.add(JobDemand(
                    skill_id=skill["id"],
                    skill_name=skill["name"],
                    category=skill["category"],
                    sector=skill["sector"],
                    demand_score=d_score,
                    growth_rate_yoy=skill["growth_rate_yoy"],
                    ncs_code=skill.get("ncs_code"),
                    esco_code=skill.get("esco_code"),
                    region="Maharashtra" if dist in ["Pune", "Mumbai", "Nagpur"] else "National",
                    district=dist,
                    description=skill.get("description", "")
                ))
                db.add(CandidateSupply(
                    skill_id=skill["id"],
                    skill_name=skill["name"],
                    category=skill["category"],
                    sector=skill["sector"],
                    supply_score=s_score,
                    region="Maharashtra" if dist in ["Pune", "Mumbai", "Nagpur"] else "National",
                    district=dist,
                    talent_pool_count=max(200, int((s_score / 100) * 8500))
                ))

        db.commit()

    # 2. Seed Course Catalog
    existing_courses = db.query(CourseCatalog).count()
    if existing_courses == 0:
        replacement_map = {
            "SW-OBS-001": {
                "replacement_course_id": "SW-SYS-501",
                "replacement_title": "Systems Programming with Rust & WebAssembly",
                "action": "Immediate Decommissioning & Syllabus Modernization"
            },
            "SW-OBS-002": {
                "replacement_course_id": "SW-CS-204",
                "replacement_title": "Cloud Native DevOps & Container Orchestration",
                "action": "Complete Retirement - Replaced by Web Standards & Cloud Stacks"
            },
            "SW-OBS-003": {
                "replacement_course_id": "SW-AI-101",
                "replacement_title": "Deep Learning & Generative AI Architectures",
                "action": "Transition to Modern Automated Testing & AI-Assisted QA"
            }
        }

        for course in SWAYAM_COURSES:
            rep = replacement_map.get(course["course_id"], {})
            catalog_item = CourseCatalog(
                course_id=course["course_id"],
                title=course["title"],
                provider=course["provider"],
                platform=course["platform"],
                instructor=course.get("instructor", ""),
                duration_weeks=course.get("duration_weeks", 8),
                credits=course.get("credits", 3),
                level=course.get("level", "Undergraduate"),
                status=course.get("status", "Active"),
                enrolled_count=course.get("enrolled_count", 0),
                rating=course.get("rating", 4.5),
                skills_covered=course.get("skills_covered", []),
                syllabus_highlights=course.get("syllabus_highlights", []),
                alignment_status=course.get("alignment_status", "High Alignment"),
                recommendation_reason=course.get("recommendation_reason", ""),
                replacement_course_id=rep.get("replacement_course_id"),
                replacement_title=rep.get("replacement_title"),
                action_required=rep.get("action")
            )
            db.add(catalog_item)

        db.commit()


def init_db() -> None:
    """Creates database tables and applies seed migrations."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    db = SessionLocal()
    print("Database initialized successfully!")
    print(f"Total Job Demands: {db.query(JobDemand).count()}")
    print(f"Total Candidate Supplies: {db.query(CandidateSupply).count()}")
    print(f"Total Courses in Catalog: {db.query(CourseCatalog).count()}")
    db.close()
