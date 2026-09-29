"""
Vector Gap-Analysis Agent (SkillSetu Gov-Tech Platform)
SIH Problem Statement 26134 — Directorate of Vocational Education & Training (DVET), Govt of Maharashtra.

Core Responsibilities:
1. PyTorch Semantic Inference Engine: Loaded on Modal GPU instance (with resilient CPU/GPU fallback).
2. Dense Embedding Generation: Converts live scraped industry skills and static ITI trade curricula into 384-dimensional dense vectors using sentence-transformers/all-MiniLM-L6-v2.
3. Cosine Similarity Matrix: Computes exact mathematical alignment between real-time industry demand and state vocational course modules.
4. Strict 75% Deficit Thresholding: Automatically flags any curriculum module dropping below 0.75 cosine similarity as "Obsolete" or "Critical Deficit", triggering automated policy intervention.
"""

import os
import math
import logging
from typing import List, Dict, Any, Optional, Tuple
import torch
import torch.nn.functional as F

logger = logging.getLogger("SkillSetu.VectorGapAnalysisAgent")
logging.basicConfig(level=logging.INFO)

# ============================================================================
# 1. STATIC ITI / MSSDS VOCATIONAL CURRICULUM BASELINE
# ============================================================================
STATIC_ITI_CURRICULUM = [
    {
        "trade_code": "TRADE-MECH-AUTO",
        "trade_name": "Mechanic Auto / Motor Vehicle (NSQF Level 4)",
        "module_id": "MOD-AUTO-004",
        "module_title": "Legacy Carburetor Tuning & 2-Stroke ICE Maintenance",
        "syllabus_text": "Manual carburetor jet cleaning, distributor points adjustment, 2-stroke single cylinder overhaul, lead-acid battery top-up, mechanical brake drum skimming.",
        "district": "Pune"
    },
    {
        "trade_code": "TRADE-MECH-AUTO",
        "trade_name": "Mechanic Auto / Motor Vehicle (NSQF Level 4)",
        "module_id": "MOD-AUTO-005",
        "module_title": "Conventional Gearbox & Manual Clutch Assemblies",
        "syllabus_text": "Disassembly of 4-speed synchromesh manual transmissions, dry single plate friction clutch replacement, mechanical throttle cable linkages.",
        "district": "Pune"
    },
    {
        "trade_code": "TRADE-DRAUGHTSMAN-MECH",
        "trade_name": "Draughtsman Mechanical (NSQF Level 5)",
        "module_id": "MOD-DRAFT-002",
        "module_title": "Manual 2D Drawing Board Drafting & Isometric Projections",
        "syllabus_text": "Pencil drafting on paper sheet, manual T-square drawing, orthographic projections of machine bolts and nuts, 2D ink line tracing.",
        "district": "Chhatrapati Sambhajinagar"
    },
    {
        "trade_code": "TRADE-COPA-IT",
        "trade_name": "Computer Operator & Programming Assistant (NSQF Level 4)",
        "module_id": "MOD-COPA-003",
        "module_title": "Legacy Desktop Publishing, DTP & Office 2007 Macros",
        "syllabus_text": "PageMaker 7.0 layout design, CorelDraw 12 basic vector logos, Microsoft Office 2007 Word mail merge and Excel VBA simple macros, manual registry cleaning.",
        "district": "Mumbai MMR"
    },
    {
        "trade_code": "TRADE-WELDER-FAB",
        "trade_name": "Welder Structural & Pipe (NSQF Level 3)",
        "module_id": "MOD-WELD-001",
        "module_title": "Manual SMAW Shielded Arc Welding & Basic Gas Torch Cutting",
        "syllabus_text": "Shielded metal arc welding using basic coated electrodes, oxy-acetylene torch flame cutting on mild steel plates, visual inspection of surface weld beads.",
        "district": "Nashik"
    },
    {
        "trade_code": "TRADE-CHEM-PLANT",
        "trade_name": "Attendant Operator Chemical Plant (NSQF Level 5)",
        "module_id": "MOD-CHEM-002",
        "module_title": "Manual Distillation Column & Wet Chemistry Titration",
        "syllabus_text": "Glassware batch distillation, manual burette acid-base titration, paper filtration, qualitative salt analysis, mercury thermometer temperature monitoring.",
        "district": "Thane"
    },
    {
        "trade_code": "TRADE-ELECTRICIAN",
        "trade_name": "Electrician Power Systems (NSQF Level 4)",
        "module_id": "MOD-ELEC-003",
        "module_title": "Legacy DC Shunt Motor Armature Rewinding",
        "syllabus_text": "Manual copper wire rewinding of DC commutator armatures, knife-edge switch wiring, electromechanical relay maintenance, basic conduit pipe bending.",
        "district": "Nagpur"
    }
]


# ============================================================================
# 2. VECTOR GAP-ANALYSIS AGENT CLASS
# ============================================================================
class VectorGapAnalysisAgent:
    """
    Autonomous Vector Gap-Analysis Agent.
    Executes dense PyTorch semantic embeddings, cosine similarity matrix computation,
    and flags vocational curriculum deficits below the 75% threshold.
    """

    DEFICIT_THRESHOLD = 0.75  # 75% similarity threshold

    def __init__(self, device: Optional[str] = None):
        self.agent_name = "SkillSetu-VectorGapAnalysisAgent-v2.0"
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.embedding_dim = 384
        self.encoder = None
        self._load_model()

    def _load_model(self):
        """Initializes the SentenceTransformer PyTorch encoder onto GPU/CPU."""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"[{self.agent_name}] Loading PyTorch model '{self.model_name}' on device: {self.device}...")
            self.encoder = SentenceTransformer("all-MiniLM-L6-v2", device=self.device)
            logger.info(f"[{self.agent_name}] SentenceTransformer loaded successfully (384-dim dense vectors).")
        except Exception as e:
            logger.warning(f"[{self.agent_name}] Falling back to resilient dense vectorizer ({e}).")
            self.encoder = None

    def generate_embeddings(self, text_list: List[str]) -> torch.Tensor:
        """
        Converts a list of text strings into a 2D PyTorch FloatTensor of shape (N, 384).
        """
        if not text_list:
            return torch.empty((0, self.embedding_dim), device=self.device)

        if self.encoder is not None:
            embeddings = self.encoder.encode(
                text_list,
                convert_to_tensor=True,
                device=self.device,
                show_progress_bar=False
            )
            if not isinstance(embeddings, torch.Tensor):
                embeddings = torch.tensor(embeddings, dtype=torch.float32, device=self.device)
            return embeddings
        else:
            # Resilient fallback: 384-dimensional dense hashed vectors normalized in PyTorch
            from sklearn.feature_extraction.text import HashingVectorizer
            vectorizer = HashingVectorizer(n_features=self.embedding_dim, alternate_sign=False)
            sparse_mat = vectorizer.fit_transform(text_list).toarray()
            t = torch.tensor(sparse_mat, dtype=torch.float32, device=self.device)
            return F.normalize(t, p=2, dim=1)

    def calculate_cosine_similarity_matrix(
        self,
        demand_embeddings: torch.Tensor,
        curriculum_embeddings: torch.Tensor
    ) -> torch.Tensor:
        """
        Computes the pairwise cosine similarity matrix between industry demand embeddings
        and ITI curriculum embeddings using PyTorch matrix multiplication:
        Sim(A, B) = (A / ||A||) * (B / ||B||)^T
        """
        norm_demands = F.normalize(demand_embeddings, p=2, dim=1)
        norm_curricula = F.normalize(curriculum_embeddings, p=2, dim=1)
        # Result shape: (num_demands, num_curricula)
        sim_matrix = torch.mm(norm_demands, norm_curricula.transpose(0, 1))
        return sim_matrix

    def analyze_curriculum_gaps(
        self,
        live_industry_records: List[Dict[str, Any]],
        curriculum_catalog: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Compares live industry demand signals against the static curriculum catalog.
        Flags any curriculum module whose maximum cosine similarity with live industry demand
        falls below the strict 75% threshold (0.75).
        """
        curricula = curriculum_catalog or STATIC_ITI_CURRICULUM
        logger.info(f"[{self.agent_name}] Running PyTorch gap analysis: {len(live_industry_records)} live industry feeds vs {len(curricula)} curriculum modules...")

        # Flatten all live industry skill strings
        demand_items = []
        for feed in live_industry_records:
            district = feed.get("district", "Maharashtra")
            sector = feed.get("sector", "General Industry")
            for skill in feed.get("extracted_skills", []):
                demand_items.append({
                    "skill_string": skill,
                    "district": district,
                    "sector": sector,
                    "company": feed.get("company", "Industry Requisition"),
                    "vacancies": feed.get("vacancies", 100)
                })

        if not demand_items:
            logger.warning(f"[{self.agent_name}] No live industry demand items available for vectorization.")
            return []

        demand_texts = [d["skill_string"] for d in demand_items]
        curriculum_texts = [f"{c['module_title']}. {c['syllabus_text']}" for c in curricula]

        # Generate PyTorch 384-dim tensor embeddings
        demand_tensor = self.generate_embeddings(demand_texts)
        curriculum_tensor = self.generate_embeddings(curriculum_texts)

        # Compute Cosine Similarity Matrix (num_demands x num_curricula)
        sim_matrix = self.calculate_cosine_similarity_matrix(demand_tensor, curriculum_tensor)

        gap_dossiers = []

        for c_idx, curr in enumerate(curricula):
            # Extract column for this curriculum module across all live demand items
            curr_sims = sim_matrix[:, c_idx]
            max_sim_val, best_match_idx = torch.max(curr_sims, dim=0)
            score = float(max_sim_val.item())
            best_industry_match = demand_items[best_match_idx.item()]

            # Determine deficit classification based on 75% threshold
            if score < self.DEFICIT_THRESHOLD:
                severity = "Critical Deficit"
                status = "Obsolete"
                action_required = "Immediate Syllabus Overhaul & Lab Hardware Modernization"
                is_deficit = True
            elif score < 0.85:
                severity = "Moderate Deficit"
                status = "Needs Modernization"
                action_required = "Elective Module Addition"
                is_deficit = False
            else:
                severity = "Aligned"
                status = "Compliant"
                action_required = "Maintain Current Standard"
                is_deficit = False

            gap_score_pct = round((1.0 - score) * 100, 1)

            dossier = {
                "trade_code": curr["trade_code"],
                "trade_name": curr["trade_name"],
                "module_id": curr["module_id"],
                "module_title": curr["module_title"],
                "district": curr["district"],
                "cosine_similarity": round(score, 4),
                "similarity_percentage": f"{round(score * 100, 1)}%",
                "gap_distance_pct": f"{gap_score_pct}%",
                "threshold_applied": "75.0%",
                "status": status,
                "severity": severity,
                "is_deficit": is_deficit,
                "closest_live_industry_demand": best_industry_match["skill_string"],
                "industry_employer": best_industry_match["company"],
                "regional_vacancies": best_industry_match["vacancies"],
                "action_directive": action_required,
                "vector_dimension": self.embedding_dim,
                "compute_device": str(self.device)
            }
            gap_dossiers.append(dossier)

        deficit_count = sum(1 for d in gap_dossiers if d["is_deficit"])
        logger.info(f"[{self.agent_name}] Analysis Complete: {deficit_count} / {len(gap_dossiers)} modules flagged as Obsolete / Critical Deficit (<75%).")
        return gap_dossiers


if __name__ == "__main__":
    from scraper_agent import LMIScraperAgent
    scraper = LMIScraperAgent()
    feeds = scraper.scrape_and_process_feeds()

    vector_agent = VectorGapAnalysisAgent()
    dossiers = vector_agent.analyze_curriculum_gaps(feeds)
    import json
    print(json.dumps(dossiers, indent=2))
