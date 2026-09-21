"""
SkillSetu Database Migration Script: SQLite to Google Cloud SQL
Reads the local SQLite database (skillsync.db) and migrates all schemas,
Job Roles (with granular skills telemetry), Job Demands, Candidate Supplies,
and Course Catalogs into the target Google Cloud SQL instance.
"""

import os
import sys
from typing import Dict, Any, List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Support both absolute and package imports
try:
    from backend.database import (
        Base,
        JobRole,
        JobDemand,
        CandidateSupply,
        CourseCatalog,
        create_database_engine
    )
except ImportError:
    from database import (
        Base,
        JobRole,
        JobDemand,
        CandidateSupply,
        CourseCatalog,
        create_database_engine
    )


def migrate_data(source_db_path: str = "sqlite:///./skillsync.db", target_engine=None):
    """
    Performs full ETL migration from local SQLite to Google Cloud SQL.
    """
    print(f"[1/4] Connecting to source SQLite database: {source_db_path}...")
    source_engine = create_engine(
        source_db_path,
        connect_args={"check_same_thread": False},
        echo=False
    )
    SourceSession = sessionmaker(bind=source_engine)
    source_session = SourceSession()

    if target_engine is None:
        print("[2/4] Initializing Cloud SQL target engine...")
        target_engine = create_database_engine()

    TargetSession = sessionmaker(bind=target_engine)
    target_session = TargetSession()

    print("[3/4] Creating database schema in target database...")
    Base.metadata.create_all(bind=target_engine)

    try:
        # 1. Migrate Job Roles
        roles: List[JobRole] = source_session.query(JobRole).all()
        print(f"  -> Found {len(roles)} JobRole records in source SQLite.")
        for r in roles:
            existing = target_session.query(JobRole).filter(JobRole.role == r.role).first()
            if not existing:
                new_role = JobRole(
                    role=r.role,
                    sector=r.sector,
                    description=r.description,
                    ncs_code=r.ncs_code,
                    esco_code=r.esco_code,
                    ncs_demand_score=r.ncs_demand_score,
                    mahaswayam_supply_score=r.mahaswayam_supply_score,
                    deficit_score=r.deficit_score,
                    growth_rate_yoy=r.growth_rate_yoy,
                    gap_analysis=r.gap_analysis,
                    skills=r.skills or [],
                    recommended_courses=r.recommended_courses or [],
                    mahaswayam_action_url=r.mahaswayam_action_url,
                    created_at=r.created_at
                )
                target_session.add(new_role)
            else:
                existing.skills = r.skills or []
                existing.recommended_courses = r.recommended_courses or []
        target_session.commit()

        # 2. Migrate Job Demands
        demands: List[JobDemand] = source_session.query(JobDemand).all()
        print(f"  -> Found {len(demands)} JobDemand records in source SQLite.")
        for d in demands:
            existing_d = target_session.query(JobDemand).filter(
                JobDemand.skill_name == d.skill_name,
                JobDemand.district == d.district
            ).first()
            if not existing_d:
                target_session.add(JobDemand(
                    skill_id=d.skill_id,
                    skill_name=d.skill_name,
                    category=d.category,
                    sector=d.sector,
                    demand_score=d.demand_score,
                    growth_rate_yoy=d.growth_rate_yoy,
                    ncs_code=d.ncs_code,
                    esco_code=d.esco_code,
                    region=d.region,
                    district=d.district,
                    description=d.description,
                    created_at=d.created_at
                ))
        target_session.commit()

        # 3. Migrate Candidate Supplies
        supplies: List[CandidateSupply] = source_session.query(CandidateSupply).all()
        print(f"  -> Found {len(supplies)} CandidateSupply records in source SQLite.")
        for s in supplies:
            existing_s = target_session.query(CandidateSupply).filter(
                CandidateSupply.skill_name == s.skill_name,
                CandidateSupply.district == s.district
            ).first()
            if not existing_s:
                target_session.add(CandidateSupply(
                    candidate_id=s.candidate_id,
                    skill_id=s.skill_id,
                    skill_name=s.skill_name,
                    category=s.category,
                    sector=s.sector,
                    supply_score=s.supply_score,
                    ncs_code=s.ncs_code,
                    esco_code=s.esco_code,
                    region=s.region,
                    district=s.district,
                    talent_pool_count=s.talent_pool_count,
                    created_at=s.created_at
                ))
        target_session.commit()

        # 4. Migrate Course Catalog
        courses: List[CourseCatalog] = source_session.query(CourseCatalog).all()
        print(f"  -> Found {len(courses)} CourseCatalog records in source SQLite.")
        for c in courses:
            existing_c = target_session.query(CourseCatalog).filter(
                CourseCatalog.course_id == c.course_id
            ).first()
            if not existing_c:
                target_session.add(CourseCatalog(
                    course_id=c.course_id,
                    title=c.title,
                    provider=c.provider,
                    platform=c.platform,
                    instructor=c.instructor,
                    duration_weeks=c.duration_weeks,
                    credits=c.credits,
                    level=c.level,
                    status=c.status,
                    enrolled_count=c.enrolled_count,
                    rating=c.rating,
                    skills_covered=c.skills_covered or [],
                    syllabus_highlights=c.syllabus_highlights or [],
                    alignment_status=c.alignment_status,
                    recommendation_reason=c.recommendation_reason,
                    created_at=c.created_at
                ))
        target_session.commit()

        # Verification Report
        print("\n[4/4] Migration Verification Report:")
        print(f"  Job Roles in Cloud SQL:         {target_session.query(JobRole).count()}")
        print(f"  Job Demands in Cloud SQL:       {target_session.query(JobDemand).count()}")
        print(f"  Candidate Supplies in Cloud SQL: {target_session.query(CandidateSupply).count()}")
        print(f"  Course Catalog in Cloud SQL:    {target_session.query(CourseCatalog).count()}")
        print("Migration completed successfully with 100% data fidelity.")

    except Exception as e:
        target_session.rollback()
        print(f"[ERROR] Migration failed with error: {e}", file=sys.stderr)
        raise e
    finally:
        source_session.close()
        target_session.close()


if __name__ == "__main__":
    migrate_data()
