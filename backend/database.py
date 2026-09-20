"""
SkillSync / SkillSetu Database Layer (SQLAlchemy)
Uses SQLite database (skillsync.db) with dynamic PostgreSQL support via DATABASE_URL.
Defines JobRole, JobDemand, CandidateSupply, and CourseCatalog schemas with automated seeding.
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

class JobRole(Base):
    """Stores benchmark job roles with NCS demand, Mahaswayam supply, SWAYAM courses, and action URLs."""
    __tablename__ = "job_roles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    role = Column(String(150), unique=True, index=True, nullable=False)
    sector = Column(String(100), index=True, nullable=False)
    description = Column(Text, nullable=True)
    ncs_code = Column(String(50), nullable=True)
    esco_code = Column(String(50), nullable=True)
    ncs_demand_score = Column(Integer, nullable=False)
    mahaswayam_supply_score = Column(Integer, nullable=False)
    deficit_score = Column(Integer, nullable=False)
    growth_rate_yoy = Column(String(20), default="+15%")
    gap_analysis = Column(Text, nullable=False)
    recommended_courses = Column(JSON, default=list)  # list of {"title": "...", "url": "..."}
    mahaswayam_action_url = Column(String(255), default="https://rojgar.mahaswayam.gov.in/")
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "sector": self.sector,
            "description": self.description,
            "ncs_code": self.ncs_code,
            "esco_code": self.esco_code,
            "ncs_demand_score": self.ncs_demand_score,
            "mahaswayam_supply_score": self.mahaswayam_supply_score,
            "deficit_score": self.deficit_score,
            "growth_rate_yoy": self.growth_rate_yoy,
            "gap_analysis": self.gap_analysis,
            "recommended_courses": self.recommended_courses or [],
            "mahaswayam_action_url": self.mahaswayam_action_url
        }


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
# Benchmark Realistic Job Roles Data (NCS & Mahaswayam Aligned)
# ============================================================================

SEED_JOB_ROLES: List[Dict[str, Any]] = [
    {
        "role": "Data Analyst",
        "sector": "Information Technology & Analytics",
        "description": "Analyzes complex datasets, designs automated SQL pipelines, and constructs executive dashboards for enterprise decision-making.",
        "ncs_code": "2512.0201",
        "esco_code": "2512.1.14",
        "ncs_demand_score": 92,
        "mahaswayam_supply_score": 48,
        "deficit_score": 44,
        "growth_rate_yoy": "+38%",
        "gap_analysis": "Acute shortage in advanced statistical modeling, SQL pipelining, and automated PowerBI/Tableau dashboarding across Maharashtra's IT corridors.",
        "recommended_courses": [
            {
                "title": "Data Analytics with Python - NPTEL (IIT Roorkee)",
                "url": "https://swayam.gov.in/explorer?searchText=data+analytics"
            },
            {
                "title": "Business Analytics & Data Mining - NPTEL (IIT Kharagpur)",
                "url": "https://swayam.gov.in/explorer?searchText=business+analytics"
            }
        ],
        "mahaswayam_action_url": "https://rojgar.mahaswayam.gov.in/"
    },
    {
        "role": "Solar Technician",
        "sector": "Renewable Energy & Utilities",
        "description": "Installs, operates, and maintains rooftop and utility-scale photovoltaic panels, inverters, and grid-synchronization gear.",
        "ncs_code": "2151.0103",
        "esco_code": "2151.1.4",
        "ncs_demand_score": 89,
        "mahaswayam_supply_score": 35,
        "deficit_score": 54,
        "growth_rate_yoy": "+52%",
        "gap_analysis": "High demand for certified technicians skilled in rooftop solar mounting, MPPT inverter troubleshooting, and net-metering synchronization.",
        "recommended_courses": [
            {
                "title": "Non-Conventional Energy Resources - NPTEL (IIT Madras)",
                "url": "https://swayam.gov.in/explorer?searchText=solar+energy"
            },
            {
                "title": "Solar Photovoltaics: Fundamentals, Technology & Applications",
                "url": "https://swayam.gov.in/explorer?searchText=photovoltaics"
            }
        ],
        "mahaswayam_action_url": "https://rojgar.mahaswayam.gov.in/"
    },
    {
        "role": "CNC Operator & Machining Specialist",
        "sector": "Advanced Manufacturing & Automotive",
        "description": "Sets up, programs, and operates multi-axis computer numerical control (CNC) milling and turning centers to produce precision components.",
        "ncs_code": "7223.0101",
        "esco_code": "7223.1.2",
        "ncs_demand_score": 86,
        "mahaswayam_supply_score": 52,
        "deficit_score": 34,
        "growth_rate_yoy": "+24%",
        "gap_analysis": "Industry transition to multi-axis CNC machines and G-code CAD/CAM programming leaves traditional manual lathe machinists in significant deficit.",
        "recommended_courses": [
            {
                "title": "CNC Machining & Technology - NPTEL (IIT Guwahati)",
                "url": "https://swayam.gov.in/explorer?searchText=cnc+machining"
            },
            {
                "title": "Computer Numerical Control (CNC) Programming - AICTE",
                "url": "https://swayam.gov.in/explorer?searchText=computer+numerical+control"
            }
        ],
        "mahaswayam_action_url": "https://rojgar.mahaswayam.gov.in/"
    },
    {
        "role": "Electric Vehicle (EV) Service Engineer",
        "sector": "Automotive & Clean Mobility",
        "description": "Performs diagnostics, maintenance, and repairs on electric vehicle powertrains, high-voltage battery packs, and regenerative braking systems.",
        "ncs_code": "2144.0201",
        "esco_code": "2144.2.7",
        "ncs_demand_score": 94,
        "mahaswayam_supply_score": 26,
        "deficit_score": 68,
        "growth_rate_yoy": "+130%",
        "gap_analysis": "Critical talent shortage in lithium-ion battery management systems (BMS), thermal runaway prevention, and high-voltage CAN bus telemetry.",
        "recommended_courses": [
            {
                "title": "Electric Vehicles - Part 1 - NPTEL (IIT Madras)",
                "url": "https://swayam.gov.in/explorer?searchText=electric+vehicles"
            },
            {
                "title": "Fundamentals of Electric Vehicles: Technology & Economics",
                "url": "https://swayam.gov.in/explorer?searchText=battery+management"
            }
        ],
        "mahaswayam_action_url": "https://rojgar.mahaswayam.gov.in/"
    },
    {
        "role": "Cloud & DevOps Engineer",
        "sector": "Information Technology & Infrastructure",
        "description": "Designs cloud-native microservice architectures, automates CI/CD deployment pipelines, and manages container orchestration.",
        "ncs_code": "2511.0302",
        "esco_code": "2511.2.3",
        "ncs_demand_score": 95,
        "mahaswayam_supply_score": 42,
        "deficit_score": 53,
        "growth_rate_yoy": "+76%",
        "gap_analysis": "Substantial deficit in Kubernetes container orchestration, HashiCorp Terraform Infrastructure-as-Code (IaC), and GitOps deployment automation.",
        "recommended_courses": [
            {
                "title": "Cloud Computing - NPTEL (IIT Kharagpur)",
                "url": "https://swayam.gov.in/explorer?searchText=cloud+computing"
            },
            {
                "title": "Software Engineering & DevOps - AICTE",
                "url": "https://swayam.gov.in/explorer?searchText=devops"
            }
        ],
        "mahaswayam_action_url": "https://rojgar.mahaswayam.gov.in/"
    },
    {
        "role": "Precision Agriculture Specialist",
        "sector": "Agriculture & Agritech",
        "description": "Deploys IoT soil sensors, drone multispectral imaging, and automated drip irrigation systems to optimize crop yields and water conservation.",
        "ncs_code": "2132.0104",
        "esco_code": "2132.1.3",
        "ncs_demand_score": 81,
        "mahaswayam_supply_score": 29,
        "deficit_score": 52,
        "growth_rate_yoy": "+45%",
        "gap_analysis": "Accelerated adoption of agritech drones, GIS field mapping, and variable-rate nutrient application requires specialized vocational upskilling.",
        "recommended_courses": [
            {
                "title": "Precision Agriculture - NPTEL (IIT Kharagpur)",
                "url": "https://swayam.gov.in/explorer?searchText=precision+agriculture"
            },
            {
                "title": "Drone Applications in Agriculture - NPTEL",
                "url": "https://swayam.gov.in/explorer?searchText=drone+technology"
            }
        ],
        "mahaswayam_action_url": "https://rojgar.mahaswayam.gov.in/"
    },
    {
        "role": "Cybersecurity Analyst",
        "sector": "Information Security & BFSI",
        "description": "Monitors security incident and event management (SIEM) systems, mitigates network intrusions, and validates Zero Trust architectures.",
        "ncs_code": "2529.0103",
        "esco_code": "2529.1.5",
        "ncs_demand_score": 96,
        "mahaswayam_supply_score": 31,
        "deficit_score": 65,
        "growth_rate_yoy": "+95%",
        "gap_analysis": "Rapid digitization across BFSI and state registries demands certified SOC tier-1/tier-2 analysts, threat hunters, and cloud compliance auditors.",
        "recommended_courses": [
            {
                "title": "Cyber Security and Privacy - NPTEL (IIT Madras)",
                "url": "https://swayam.gov.in/explorer?searchText=cyber+security"
            },
            {
                "title": "Information Security & Digital Forensics - NPTEL",
                "url": "https://swayam.gov.in/explorer?searchText=digital+forensics"
            }
        ],
        "mahaswayam_action_url": "https://rojgar.mahaswayam.gov.in/"
    },
    {
        "role": "Healthcare IT Technician",
        "sector": "Healthcare & MedTech",
        "description": "Maintains hospital information systems (HIS), Ayushman Bharat Digital Mission (ABDM) integration, and medical diagnostic IoT devices.",
        "ncs_code": "2131.0203",
        "esco_code": "2131.2.1",
        "ncs_demand_score": 84,
        "mahaswayam_supply_score": 40,
        "deficit_score": 44,
        "growth_rate_yoy": "+40%",
        "gap_analysis": "Deployment of electronic health records (EHR) and ABDM health repository standards requires healthcare staff trained in medical data interoperability.",
        "recommended_courses": [
            {
                "title": "Introduction to Healthcare IT & Telemedicine - NPTEL",
                "url": "https://swayam.gov.in/explorer?searchText=healthcare+technology"
            },
            {
                "title": "Biomedical Signal Processing - NPTEL",
                "url": "https://swayam.gov.in/explorer?searchText=biomedical"
            }
        ],
        "mahaswayam_action_url": "https://rojgar.mahaswayam.gov.in/"
    }
]


# ============================================================================
# Database Seeding & Migration Logic
# ============================================================================

def seed_database(db: Session) -> None:
    """Seeds benchmark job roles and telemetry into the live SQLite database."""
    # 1. Seed Job Roles
    existing_roles = db.query(JobRole).count()
    if existing_roles == 0:
        for r_data in SEED_JOB_ROLES:
            job_role = JobRole(
                role=r_data["role"],
                sector=r_data["sector"],
                description=r_data["description"],
                ncs_code=r_data.get("ncs_code"),
                esco_code=r_data.get("esco_code"),
                ncs_demand_score=r_data["ncs_demand_score"],
                mahaswayam_supply_score=r_data["mahaswayam_supply_score"],
                deficit_score=r_data["deficit_score"],
                growth_rate_yoy=r_data.get("growth_rate_yoy", "+15%"),
                gap_analysis=r_data["gap_analysis"],
                recommended_courses=r_data.get("recommended_courses", []),
                mahaswayam_action_url=r_data.get("mahaswayam_action_url", "https://rojgar.mahaswayam.gov.in/")
            )
            db.add(job_role)
        db.commit()

    # 2. Seed Job Demands and Candidate Supplies for LMI dashboard
    existing_demands = db.query(JobDemand).count()
    if existing_demands == 0:
        districts = ["Pune", "Mumbai", "Nagpur", "Nashik", "Aurangabad", "National"]

        for r_data in SEED_JOB_ROLES:
            # National baseline
            demand_nat = JobDemand(
                skill_id=f"SK-{r_data.get('ncs_code', 'GEN')}",
                skill_name=r_data["role"],
                category=r_data["sector"],
                sector=r_data["sector"],
                demand_score=r_data["ncs_demand_score"],
                growth_rate_yoy=r_data["growth_rate_yoy"],
                ncs_code=r_data.get("ncs_code"),
                esco_code=r_data.get("esco_code"),
                region="National",
                district="All Districts",
                description=r_data["description"]
            )
            supply_nat = CandidateSupply(
                skill_id=f"SK-{r_data.get('ncs_code', 'GEN')}",
                skill_name=r_data["role"],
                category=r_data["sector"],
                sector=r_data["sector"],
                supply_score=r_data["mahaswayam_supply_score"],
                region="National",
                district="All Districts",
                talent_pool_count=18000 + (r_data["mahaswayam_supply_score"] * 140)
            )
            db.add(demand_nat)
            db.add(supply_nat)

            # District variations for LMI drill-downs
            for idx, dist in enumerate(districts):
                delta_d = ((idx * 7 + len(r_data["role"])) % 11) - 5
                delta_s = ((idx * 5 + len(r_data["sector"])) % 9) - 4
                
                d_score = max(5, min(100, r_data["ncs_demand_score"] + delta_d))
                s_score = max(5, min(100, r_data["mahaswayam_supply_score"] + delta_s))

                db.add(JobDemand(
                    skill_id=f"SK-{r_data.get('ncs_code', 'GEN')}",
                    skill_name=r_data["role"],
                    category=r_data["sector"],
                    sector=r_data["sector"],
                    demand_score=d_score,
                    growth_rate_yoy=r_data["growth_rate_yoy"],
                    ncs_code=r_data.get("ncs_code"),
                    esco_code=r_data.get("esco_code"),
                    region="Maharashtra" if dist != "National" else "National",
                    district=dist,
                    description=r_data["description"]
                ))
                db.add(CandidateSupply(
                    skill_id=f"SK-{r_data.get('ncs_code', 'GEN')}",
                    skill_name=r_data["role"],
                    category=r_data["sector"],
                    sector=r_data["sector"],
                    supply_score=s_score,
                    region="Maharashtra" if dist != "National" else "National",
                    district=dist,
                    talent_pool_count=max(200, int((s_score / 100) * 8500))
                ))
        db.commit()

    # 3. Seed Course Catalog
    existing_courses = db.query(CourseCatalog).count()
    if existing_courses == 0:
        for idx, r_data in enumerate(SEED_JOB_ROLES):
            for c_idx, course in enumerate(r_data.get("recommended_courses", [])):
                catalog_item = CourseCatalog(
                    course_id=f"SW-CR-{idx+1}0{c_idx+1}",
                    title=course["title"],
                    provider="SWAYAM / NPTEL / AICTE",
                    platform="SWAYAM",
                    instructor="Faculty Panel",
                    duration_weeks=12,
                    credits=4,
                    level="Undergraduate / Postgraduate",
                    status="Active",
                    enrolled_count=15000 + (idx * 1200),
                    rating=4.82,
                    skills_covered=[r_data["role"], r_data["sector"]],
                    syllabus_highlights=[f"Core curriculum for {r_data['role']}", r_data["gap_analysis"]],
                    alignment_status="High Alignment",
                    recommendation_reason=f"Addresses key Maharashtra market deficit in {r_data['role']}."
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
    print(f"Total Job Roles: {db.query(JobRole).count()}")
    print(f"Total Job Demands: {db.query(JobDemand).count()}")
    print(f"Total Candidate Supplies: {db.query(CandidateSupply).count()}")
    print(f"Total Courses in Catalog: {db.query(CourseCatalog).count()}")
    db.close()
