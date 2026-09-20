"""
SkillSync / SkillSetu PyTorch Vector Search Engine
Eliminates static dummy data by executing real semantic vector search against
the SQLite database using SentenceTransformers and PyTorch tensor operations.
"""

from typing import List, Dict, Any, Optional, Union
import math
import re
import torch
import torch.nn.functional as F
from sqlalchemy.orm import Session

from database import JobRole


# ============================================================================
# 1. NLP SIMILARITY ENGINE (PyTorch Dense Embeddings + Resilient Fallback)
# ============================================================================

class NLPSimilarityEngine:
    """
    NLP Engine providing semantic vector embeddings and cosine similarity search
    using SentenceTransformers ('all-MiniLM-L6-v2') and PyTorch tensors.
    """
    def __init__(self):
        self.model_type = "sentence-transformers (all-MiniLM-L6-v2)"
        self.encoder = None
        self._initialized = False

    def _initialize_model(self):
        """Initializes SentenceTransformer lazily."""
        if self._initialized:
            return
        self._initialized = True
        try:
            from sentence_transformers import SentenceTransformer
            self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
            self.model_type = "sentence-transformers (all-MiniLM-L6-v2)"
        except Exception:
            self.encoder = None
            self.model_type = "TF-IDF / N-gram Cosine Fallback"

    def get_embeddings(self, texts: List[str]) -> torch.Tensor:
        """
        Encodes a batch of texts into PyTorch tensor embeddings in a single forward pass.
        Returns a 2D torch.FloatTensor of shape (len(texts), embedding_dim).
        """
        self._initialize_model()
        if self.encoder is not None:
            return self.encoder.encode(texts, convert_to_tensor=True)
        else:
            from sklearn.feature_extraction.text import TfidfVectorizer
            vec = TfidfVectorizer().fit_transform(texts)
            return torch.tensor(vec.toarray(), dtype=torch.float32)

    def calculate_similarity(self, query: str, document: str) -> float:
        """Calculates normalized cosine similarity between query and document."""
        embs = self.get_embeddings([query, document])
        norm_embs = F.normalize(embs, p=2, dim=1)
        sim = float(torch.mm(norm_embs[0:1], norm_embs[1:2].T).item())
        return max(0.0, min(1.0, sim))


# Singleton instance
nlp_engine = NLPSimilarityEngine()


# ============================================================================
# 2. LIVE SQLITE VECTOR SEARCH (Job Roles & Curriculum Alignment)
# ============================================================================

def search_job_roles(db: Session, query: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Performs real vector similarity search against the seeded SQLite database
    using PyTorch tensor cosine similarity.

    Returns strict JSON response:
    {
        "status": "success",
        "query": query,
        "results": [
            {
                "role": role.role,
                "match_score": 0.95,
                "gap_analysis": role.gap_analysis,
                "recommended_courses": [ {"title": "...", "url": "..."} ],
                "mahaswayam_action_url": role.mahaswayam_action_url
            }
        ]
    }
    """
    clean_query = query.strip() if query else ""
    if not clean_query:
        return {
            "status": "success",
            "query": clean_query,
            "results": []
        }

    # Retrieve all benchmark job roles from the live SQLite database
    roles = db.query(JobRole).all()
    if not roles:
        from database import init_db
        init_db()
        roles = db.query(JobRole).all()

    if not roles:
        return {
            "status": "success",
            "query": clean_query,
            "results": []
        }

    # Construct rich semantic representations for each role from database columns
    role_texts = [
        f"{r.role}. Sector: {r.sector}. {r.description or ''} {r.gap_analysis or ''}"
        for r in roles
    ]

    # Batch encode query and role texts in single PyTorch forward passes
    query_emb = nlp_engine.get_embeddings([clean_query])  # Shape: (1, D)
    role_embs = nlp_engine.get_embeddings(role_texts)     # Shape: (N, D)

    # Normalize vectors for cosine similarity
    query_norm = F.normalize(query_emb, p=2, dim=1)
    role_norms = F.normalize(role_embs, p=2, dim=1)

    # Compute cosine similarities via matrix multiplication: (1, D) x (D, N) -> (1, N)
    sim_scores = torch.mm(query_norm, role_norms.T).squeeze(0)  # Shape: (N,)

    # Pair each role with its computed similarity score
    scored_roles = []
    for idx, r in enumerate(roles):
        score = float(sim_scores[idx].item())
        # Apply slight keyword bonus if query terms appear directly in the role title or sector
        q_tokens = set(re.findall(r'[a-z0-9]+', clean_query.lower()))
        role_tokens = set(re.findall(r'[a-z0-9]+', f"{r.role} {r.sector}".lower()))
        if q_tokens.intersection(role_tokens):
            score = min(1.0, score + 0.10)

        scored_roles.append((r, score))

    # Sort descending by match score
    scored_roles.sort(key=lambda x: x[1], reverse=True)

    results = []
    for r, score in scored_roles[:top_k]:
        courses = r.recommended_courses if isinstance(r.recommended_courses, list) else []
        results.append({
            "role": r.role,
            "match_score": round(max(0.0, min(1.0, score)), 2),
            "gap_analysis": r.gap_analysis or "No critical gaps identified.",
            "recommended_courses": courses,
            "mahaswayam_action_url": r.mahaswayam_action_url or "https://rojgar.mahaswayam.gov.in/"
        })

    return {
        "status": "success",
        "query": clean_query,
        "results": results
    }


# ============================================================================
# 3. VECTORIZED SKILL GAP EVALUATOR (PyTorch Batch Tensor Operations)
# ============================================================================

def evaluate_skill_gap(
    candidate_skills: Union[Dict[str, float], List[Dict[str, Any]]],
    job_requirements: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Vectorized candidate-to-job skill gap scoring engine using single-pass
    SentenceTransformer batch encoding and PyTorch tensor matrix multiplication.

    Thresholds:
      - Exact match (>= 0.85): coverage = min(1.0, cand_prof / req_prof)
      - Partial match (0.60 <= sim < 0.849): coverage = min(1.0, (cand_prof / req_prof) * sim)
      - Missing (< 0.60): coverage = 0.0

    Gap Ranking:
      - gap_impact = weight * (1.0 - coverage)
    """
    # Normalize candidate skills into standard list of {name, proficiency}
    cand_list = []
    if isinstance(candidate_skills, dict):
        for k, v in candidate_skills.items():
            cand_list.append({"name": str(k).strip(), "proficiency": float(v)})
    elif isinstance(candidate_skills, list):
        for c in candidate_skills:
            name = c.get("name") or c.get("skill")
            if name:
                cand_list.append({"name": str(name).strip(), "proficiency": float(c.get("proficiency", 3))})

    # Normalize job requirements into standard list of {name, required_proficiency, weight}
    req_list = []
    for r in job_requirements:
        name = r.get("name") or r.get("skill")
        if name:
            req_list.append({
                "name": str(name).strip(),
                "required_proficiency": float(r.get("required_proficiency", 4)),
                "weight": float(r.get("weight", 1.0))
            })

    if not req_list:
        return {
            "overall_coverage": 0.0,
            "overall_match_percentage": "0.0%",
            "detailed_gaps": [],
            "critical_gaps": []
        }

    # If candidate has no skills listed
    if not cand_list:
        detailed_gaps = []
        for r in req_list:
            detailed_gaps.append({
                "skill_name": r["name"],
                "required_proficiency": r["required_proficiency"],
                "candidate_proficiency": 0.0,
                "matched_candidate_skill": None,
                "similarity": 0.0,
                "match_type": "Missing",
                "coverage": 0.0,
                "coverage_percentage": "0.0%",
                "weight": r["weight"],
                "gap_impact": round(r["weight"] * 1.0, 4)
            })
        detailed_gaps.sort(key=lambda x: x["gap_impact"], reverse=True)
        return {
            "overall_coverage": 0.0,
            "overall_match_percentage": "0.0%",
            "detailed_gaps": detailed_gaps,
            "critical_gaps": detailed_gaps[:3]
        }

    cand_names = [c["name"] for c in cand_list]
    req_names = [r["name"] for r in req_list]

    # Batch encode in 1 forward pass each without redundant per-item passes
    cand_embs = nlp_engine.get_embeddings(cand_names)
    req_embs = nlp_engine.get_embeddings(req_names)

    # Normalize vectors
    cand_norm = F.normalize(cand_embs, p=2, dim=1)
    req_norm = F.normalize(req_embs, p=2, dim=1)

    # Compute full cosine similarity matrix in single tensor multiplication (N x M)
    sim_matrix = torch.mm(req_norm, cand_norm.T)

    # For each requirement, find the top matching candidate skill
    max_sims, best_indices = torch.max(sim_matrix, dim=1)

    detailed_gaps = []
    total_weighted_coverage = 0.0
    total_weight = 0.0

    for i, r in enumerate(req_list):
        best_sim = float(max_sims[i].item())
        best_cand_idx = int(best_indices[i].item())
        matched_cand = cand_list[best_cand_idx]
        cand_prof = matched_cand["proficiency"]
        req_prof = max(0.1, r["required_proficiency"])
        weight = r["weight"]
        total_weight += weight

        # Strict Thresholds:
        # Exact: >= 0.85
        # Partial: 0.60 to 0.849
        # Missing: < 0.60
        if best_sim >= 0.85:
            match_type = "Exact"
            coverage = min(1.0, cand_prof / req_prof)
        elif best_sim >= 0.60:
            match_type = "Partial"
            coverage = min(1.0, (cand_prof / req_prof) * best_sim)
        else:
            match_type = "Missing"
            coverage = 0.0

        gap_impact = weight * (1.0 - coverage)
        total_weighted_coverage += weight * coverage

        detailed_gaps.append({
            "skill_name": r["name"],
            "required_proficiency": r["required_proficiency"],
            "candidate_proficiency": cand_prof if match_type != "Missing" else 0.0,
            "matched_candidate_skill": matched_cand["name"] if match_type != "Missing" else None,
            "similarity": round(best_sim, 4),
            "match_type": match_type,
            "coverage": round(coverage, 4),
            "coverage_percentage": f"{round(coverage * 100, 1)}%",
            "weight": weight,
            "gap_impact": round(gap_impact, 4)
        })

    # Sort descending by gap_impact
    detailed_gaps.sort(key=lambda x: x["gap_impact"], reverse=True)
    overall_cov = round(total_weighted_coverage / (total_weight or 1.0), 4)

    return {
        "overall_coverage": overall_cov,
        "overall_match_percentage": f"{round(overall_cov * 100, 1)}%",
        "detailed_gaps": detailed_gaps,
        "critical_gaps": detailed_gaps[:3]
    }
