"""
SkillSync / SkillSetu Database Layer (SQLAlchemy)
Uses SQLite database (skillsync.db) with dynamic PostgreSQL support via DATABASE_URL.
Defines JobRole, JobDemand, CandidateSupply, and CourseCatalog schemas with automated seeding.
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Generator
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, JSON, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# ============================================================================
# Database Configuration & Session Management (Cloud SQL & SQLite)
# ============================================================================

def create_database_engine():
    """
    Initializes a resilient SQLAlchemy connection pool for Google Cloud SQL
    using the Cloud SQL Python Connector with IAM authentication, or falls
    back to standard DATABASE_URL / SQLite for local development.
    """
    instance_connection_name = os.getenv("INSTANCE_CONNECTION_NAME")
    db_user = os.getenv("DB_USER", "skillsetu-backend-sa")
    db_pass = os.getenv("DB_PASS", "")
    db_name = os.getenv("DB_NAME", "skillsetu_db")
    db_type = os.getenv("DB_TYPE", "postgres").lower()

    if instance_connection_name:
        try:
            from google.cloud.sql.connector import Connector, IPTypes
            connector = Connector()

            def getconn():
                conn = connector.connect(
                    instance_connection_name,
                    "pg8000" if "postgres" in db_type else "pymysql",
                    user=db_user,
                    password=db_pass if db_pass else None,
                    db=db_name,
                    ip_type=IPTypes.PUBLIC,
                    enable_iam_auth=True if not db_pass else False
                )
                return conn

            return create_engine(
                "postgresql+pg8000://" if "postgres" in db_type else "mysql+pymysql://",
                creator=getconn,
                pool_size=5,
                max_overflow=2,
                pool_timeout=30,
                pool_recycle=1800,
                echo=False
            )
        except Exception as e:
            print(f"[WARN] Cloud SQL Connector initialization failed ({e}). Falling back to DATABASE_URL.")

    # Fallback to standard connection string (Postgres/MySQL or local SQLite)
    database_url = os.getenv("DATABASE_URL", "sqlite:///./skillsync.db")
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            echo=False
        )
    else:
        return create_engine(
            database_url,
            pool_size=5,
            max_overflow=2,
            pool_timeout=30,
            pool_recycle=1800,
            echo=False
        )


engine = create_database_engine()
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
    skills = Column(JSON, default=list)  # list of {"name": "...", "demand": int, "supply": int}
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
            "skills": self.skills or [],
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
        "role": "Software Engineer / IT Analyst",
        "sector": "Information Technology & Software Services",
        "description": "Develops, tests, and maintains enterprise software applications, cloud services, and RESTful APIs using modern programming languages and frameworks.",
        "ncs_code": "2512.0101",
        "esco_code": "2512.1.1",
        "ncs_demand_score": 95,
        "mahaswayam_supply_score": 52,
        "deficit_score": 43,
        "growth_rate_yoy": "+42%",
        "gap_analysis": "High industry demand for full-stack engineering, microservices architecture, and cloud deployment pipelines across Pune and Mumbai IT hubs.",
        "skills": [
            {"name": "Full-Stack Web & RESTful APIs", "demand": 94, "supply": 48},
            {"name": "Cloud Microservices & Docker", "demand": 92, "supply": 42},
            {"name": "Python & Data Structures", "demand": 96, "supply": 55},
            {"name": "CI/CD & DevOps Automation", "demand": 88, "supply": 38}
        ],
        "recommended_courses": [
            {
                "title": "Programming, Data Structures And Algorithms Using Python - NPTEL (IIT Madras)",
                "url": "https://swayam.gov.in/explorer?searchText=python+programming"
            },
            {
                "title": "Cloud Computing - NPTEL (IIT Kharagpur)",
                "url": "https://swayam.gov.in/explorer?searchText=cloud+computing"
            }
        ],
        "mahaswayam_action_url": "https://rojgar.mahaswayam.gov.in/"
    },
    {
        "role": "Government School Teacher / Educator",
        "sector": "Education & Public Instruction",
        "description": "Delivers curriculum-aligned foundational literacy, numeracy, and STEM education in government and aided schools following NEP 2020 standards.",
        "ncs_code": "2341.0101",
        "esco_code": "2341.1.2",
        "ncs_demand_score": 88,
        "mahaswayam_supply_score": 64,
        "deficit_score": 24,
        "growth_rate_yoy": "+18%",
        "gap_analysis": "Need for teachers proficient in digital pedagogy, ICT-enabled smart classrooms, inclusive teaching methods, and foundational numeracy.",
        "skills": [
            {"name": "Digital Pedagogy & ICT Classrooms", "demand": 89, "supply": 58},
            {"name": "Foundational Literacy & Numeracy (FLN)", "demand": 92, "supply": 64},
            {"name": "NEP 2020 Curriculum Standards", "demand": 86, "supply": 50},
            {"name": "Inclusive Classroom Instruction", "demand": 84, "supply": 60}
        ],
        "recommended_courses": [
            {
                "title": "Pedagogy of Teaching - SWAYAM (IGNOU)",
                "url": "https://swayam.gov.in/explorer?searchText=pedagogy"
            },
            {
                "title": "ICT in Teaching and Learning - SWAYAM (NCERT)",
                "url": "https://swayam.gov.in/explorer?searchText=ict+teaching"
            }
        ],
        "mahaswayam_action_url": "https://rojgar.mahaswayam.gov.in/"
    },
    {
        "role": "Data Analyst",
        "sector": "Information Technology & Analytics",
        "description": "Analyzes complex datasets, designs automated SQL pipelines, and constructs executive dashboards for enterprise decision-making.",
        "ncs_code": "2512.0201",
        "esco_code": "2512.1.14",
        "ncs_demand_score": 92,
        "mahaswayam_supply_score": 46,
        "deficit_score": 46,
        "growth_rate_yoy": "+38%",
        "gap_analysis": "Acute shortage in advanced statistical modeling, SQL pipelining, and automated PowerBI/Tableau dashboarding across Maharashtra's IT corridors.",
        "skills": [
            {"name": "Advanced SQL Pipelining", "demand": 95, "supply": 40},
            {"name": "PowerBI / Tableau", "demand": 88, "supply": 45},
            {"name": "Python Data Ecosystem (Pandas)", "demand": 92, "supply": 38}
        ],
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
        "role": "Administrative Clerk / Data Entry Operator",
        "sector": "Public Administration & Office Support",
        "description": "Manages digital document processing, record maintenance, data entry operations, and office automation across public and private sector offices.",
        "ncs_code": "4112.0101",
        "esco_code": "4112.1.3",
        "ncs_demand_score": 84,
        "mahaswayam_supply_score": 70,
        "deficit_score": 14,
        "growth_rate_yoy": "+12%",
        "gap_analysis": "Demand has shifted from basic typing to digital records management, ERP database entry, advanced spreadsheet automation, and e-governance portal handling.",
        "skills": [
            {"name": "Advanced Spreadsheet & Excel Modeling", "demand": 86, "supply": 68},
            {"name": "Digital Records & ERP Data Entry", "demand": 84, "supply": 72},
            {"name": "e-Governance Portals & Document Handling", "demand": 82, "supply": 65},
            {"name": "Office Automation & Typing Accuracy", "demand": 78, "supply": 80}
        ],
        "recommended_courses": [
            {
                "title": "Office Automation & Digital Skills - SWAYAM (AICTE)",
                "url": "https://swayam.gov.in/explorer?searchText=office+automation"
            },
            {
                "title": "Computer Concepts and Applications - SWAYAM (NITTTR)",
                "url": "https://swayam.gov.in/explorer?searchText=computer+applications"
            }
        ],
        "mahaswayam_action_url": "https://rojgar.mahaswayam.gov.in/"
    },
    {
        "role": "Healthcare Nurse / Ward Attendant",
        "sector": "Healthcare & Allied Medical Services",
        "description": "Provides bedside patient care, monitors vital signs, assists physicians in clinical procedures, and manages healthcare hygiene standards.",
        "ncs_code": "3221.0101",
        "esco_code": "3221.1.1",
        "ncs_demand_score": 94,
        "mahaswayam_supply_score": 42,
        "deficit_score": 52,
        "growth_rate_yoy": "+48%",
        "gap_analysis": "Severe deficit in emergency triage care, ICU monitoring, infection control protocols, and digital health records handling across district hospitals.",
        "skills": [
            {"name": "Emergency Triage & Vital Signs Monitoring", "demand": 95, "supply": 38},
            {"name": "Infection Control & Clinical Protocols", "demand": 92, "supply": 44},
            {"name": "ICU & Patient Bedside Nursing", "demand": 94, "supply": 36},
            {"name": "Digital Health Records (ABDM / EHR)", "demand": 85, "supply": 40}
        ],
        "recommended_courses": [
            {
                "title": "Nursing Care & Clinical Practices - SWAYAM (AIIMS)",
                "url": "https://swayam.gov.in/explorer?searchText=nursing"
            },
            {
                "title": "Infection Prevention & Hospital Safety - SWAYAM (NPTEL)",
                "url": "https://swayam.gov.in/explorer?searchText=healthcare"
            }
        ],
        "mahaswayam_action_url": "https://rojgar.mahaswayam.gov.in/"
    },
    {
        "role": "Vocational Electrician / Solar Technician",
        "sector": "Renewable Energy & Electrical Engineering",
        "description": "Installs, tests, and repairs residential and commercial electrical wiring, rooftop solar PV systems, inverters, and switchgear.",
        "ncs_code": "7411.0101",
        "esco_code": "7411.1.2",
        "ncs_demand_score": 90,
        "mahaswayam_supply_score": 44,
        "deficit_score": 46,
        "growth_rate_yoy": "+55%",
        "gap_analysis": "Rapid expansion of rooftop solar installations and EV charging infrastructure requires certified electricians skilled in DC wiring, MPPT inverters, and net-metering.",
        "skills": [
            {"name": "Rooftop Solar PV Installation", "demand": 92, "supply": 42},
            {"name": "MPPT Inverters & Net-Metering Setup", "demand": 88, "supply": 38},
            {"name": "Industrial & Domestic Wiring (AC/DC)", "demand": 90, "supply": 52},
            {"name": "EV Charging Station Maintenance", "demand": 86, "supply": 34}
        ],
        "recommended_courses": [
            {
                "title": "Non-Conventional Energy Resources - NPTEL (IIT Madras)",
                "url": "https://swayam.gov.in/explorer?searchText=solar+energy"
            },
            {
                "title": "Basic Electrical Circuits - NPTEL (IIT Madras)",
                "url": "https://swayam.gov.in/explorer?searchText=electrical+circuits"
            }
        ],
        "mahaswayam_action_url": "https://rojgar.mahaswayam.gov.in/"
    }
]


# ============================================================================
# Database Seeding & Migration Logic
# ============================================================================

def seed_database(db: Session) -> None:
    """Seeds and updates benchmark job roles and telemetry into the live SQLite database."""
    # 0. Migrate SQLite schema if skills column is missing
    try:
        db.execute(text("ALTER TABLE job_roles ADD COLUMN skills JSON DEFAULT '[]'"))
        db.commit()
    except Exception:
        db.rollback()

    # 1. Clear generic seed data and replace with high-volume benchmark roles
    valid_roles = [r["role"] for r in SEED_JOB_ROLES]
    db.query(JobRole).filter(~JobRole.role.in_(valid_roles)).delete(synchronize_session=False)
    db.query(JobDemand).filter(~JobDemand.skill_name.in_(valid_roles)).delete(synchronize_session=False)
    db.query(CandidateSupply).filter(~CandidateSupply.skill_name.in_(valid_roles)).delete(synchronize_session=False)
    db.commit()

    # Upsert Job Roles
    for r_data in SEED_JOB_ROLES:
        existing = db.query(JobRole).filter(JobRole.role == r_data["role"]).first()
        if existing:
            existing.sector = r_data["sector"]
            existing.description = r_data["description"]
            existing.ncs_code = r_data.get("ncs_code")
            existing.esco_code = r_data.get("esco_code")
            existing.ncs_demand_score = r_data["ncs_demand_score"]
            existing.mahaswayam_supply_score = r_data["mahaswayam_supply_score"]
            existing.deficit_score = r_data["deficit_score"]
            existing.growth_rate_yoy = r_data.get("growth_rate_yoy", "+15%")
            existing.gap_analysis = r_data["gap_analysis"]
            existing.skills = r_data.get("skills", [])
            existing.recommended_courses = r_data.get("recommended_courses", [])
            existing.mahaswayam_action_url = r_data.get("mahaswayam_action_url", "https://rojgar.mahaswayam.gov.in/")
        else:
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
                skills=r_data.get("skills", []),
                recommended_courses=r_data.get("recommended_courses", []),
                mahaswayam_action_url=r_data.get("mahaswayam_action_url", "https://rojgar.mahaswayam.gov.in/")
            )
            db.add(job_role)
    db.commit()

    # 2. Seed Job Demands and Candidate Supplies for LMI dashboard
    districts = ["Pune", "Mumbai", "Nagpur", "Nashik", "Aurangabad", "Thane", "National"]

    for r_data in SEED_JOB_ROLES:
        # Check if National baseline exists
        existing_nat = db.query(JobDemand).filter(
            JobDemand.skill_name == r_data["role"],
            JobDemand.region == "National"
        ).first()

        if not existing_nat:
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
            if dist == "National":
                continue
            existing_dist = db.query(JobDemand).filter(
                JobDemand.skill_name == r_data["role"],
                JobDemand.district == dist
            ).first()

            if not existing_dist:
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
                    region="Maharashtra",
                    district=dist,
                    description=r_data["description"]
                ))
                db.add(CandidateSupply(
                    skill_id=f"SK-{r_data.get('ncs_code', 'GEN')}",
                    skill_name=r_data["role"],
                    category=r_data["sector"],
                    sector=r_data["sector"],
                    supply_score=s_score,
                    region="Maharashtra",
                    district=dist,
                    talent_pool_count=max(200, int((s_score / 100) * 8500))
                ))
    db.commit()

    # 3. Seed Course Catalog
    for idx, r_data in enumerate(SEED_JOB_ROLES):
        for c_idx, course in enumerate(r_data.get("recommended_courses", [])):
            course_id = f"SW-CR-{idx+1}0{c_idx+1}"
            existing_c = db.query(CourseCatalog).filter(CourseCatalog.course_id == course_id).first()
            if not existing_c:
                catalog_item = CourseCatalog(
                    course_id=course_id,
                    title=course["title"],
                    provider="SWAYAM / NPTEL / AICTE",
                    platform="SWAYAM",
                    instructor="Faculty Panel",
                    duration_weeks=12,
                    credits=4,
                    level="Undergraduate / Vocational",
                    status="Active",
                    enrolled_count=15000 + (idx * 1200),
                    rating=4.85,
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
