"""
SkillSync Recommendation & NLP Engine
Integrates Lightcast/ESCO taxonomy logic, semantic vector embeddings,
and cosine similarity with fallback logic for resilient hackathon execution.
"""

from typing import List, Dict, Any, Optional, Union
import math
import re

# ============================================================================
# 1. TAXONOMY & MARKET BENCHMARKS (Lightcast / ESCO Aligned)
# ============================================================================

TAXONOMY_SKILLS: List[Dict[str, Any]] = [
    # AI & Data Science
    {
        "id": "SK-001",
        "name": "Generative AI & LLM Fine-Tuning",
        "category": "Artificial Intelligence",
        "sector": "Information Technology",
        "esco_code": "2512.1.14",
        "demand_score": 96,
        "supply_score": 38,
        "growth_rate_yoy": "+142%",
        "ncs_code": "2512.0201",
        "description": "Fine-tuning foundational models, prompt engineering, RAG pipelines, and vector databases."
    },
    {
        "id": "SK-002",
        "name": "MLOps & Model Deployment",
        "category": "Artificial Intelligence",
        "sector": "Information Technology",
        "esco_code": "2512.1.18",
        "demand_score": 91,
        "supply_score": 42,
        "growth_rate_yoy": "+88%",
        "ncs_code": "2512.0204",
        "description": "Continuous delivery for ML, Kubeflow, MLflow, model monitoring, and latency optimization."
    },
    {
        "id": "SK-003",
        "name": "Distributed Data Engineering (Spark/Flink)",
        "category": "Data Engineering",
        "sector": "Information Technology",
        "esco_code": "2521.1.2",
        "demand_score": 88,
        "supply_score": 52,
        "growth_rate_yoy": "+54%",
        "ncs_code": "2521.0101",
        "description": "Petabyte-scale data pipelines, streaming architectures, Apache Spark, Kafka, and Lakehouse."
    },
    {
        "id": "SK-004",
        "name": "Classical Machine Learning (Scikit-Learn)",
        "category": "Data Science",
        "sector": "Information Technology",
        "esco_code": "2120.1.1",
        "demand_score": 75,
        "supply_score": 78,
        "growth_rate_yoy": "+12%",
        "ncs_code": "2120.0102",
        "description": "Supervised & unsupervised regression, random forests, classification, and statistical testing."
    },

    # Cloud & DevOps
    {
        "id": "SK-005",
        "name": "Kubernetes & Cloud-Native Microservices",
        "category": "Cloud & Infrastructure",
        "sector": "Information Technology",
        "esco_code": "2511.2.3",
        "demand_score": 94,
        "supply_score": 46,
        "growth_rate_yoy": "+76%",
        "ncs_code": "2511.0302",
        "description": "Container orchestration, Helm, service meshes, zero-downtime deployment, and GitOps."
    },
    {
        "id": "SK-006",
        "name": "Terraform & Multi-Cloud IaC",
        "category": "Cloud & Infrastructure",
        "sector": "Information Technology",
        "esco_code": "2511.2.8",
        "demand_score": 89,
        "supply_score": 44,
        "growth_rate_yoy": "+65%",
        "ncs_code": "2511.0305",
        "description": "Infrastructure as Code, multi-cloud provisioning, security guardrails, and state drift control."
    },

    # Cybersecurity
    {
        "id": "SK-007",
        "name": "Cloud Security Architecture & Zero Trust",
        "category": "Cybersecurity",
        "sector": "Information Technology",
        "esco_code": "2529.1.5",
        "demand_score": 95,
        "supply_score": 34,
        "growth_rate_yoy": "+95%",
        "ncs_code": "2529.0103",
        "description": "Identity federation, IAM boundaries, micro-segmentation, and cloud workload protection."
    },
    {
        "id": "SK-008",
        "name": "SOC Incident Response & Threat Hunting",
        "category": "Cybersecurity",
        "sector": "Information Technology",
        "esco_code": "2529.1.9",
        "demand_score": 87,
        "supply_score": 49,
        "growth_rate_yoy": "+48%",
        "ncs_code": "2529.0108",
        "description": "SIEM log analysis, digital forensics, threat intelligence frameworks, and incident mitigation."
    },

    # Software Engineering
    {
        "id": "SK-009",
        "name": "Rust Systems Programming & WebAssembly",
        "category": "Software Engineering",
        "sector": "Information Technology",
        "esco_code": "2512.1.22",
        "demand_score": 86,
        "supply_score": 25,
        "growth_rate_yoy": "+115%",
        "ncs_code": "2512.0105",
        "description": "Memory-safe systems programming, concurrency, high-performance microservices, and WASM runtime."
    },
    {
        "id": "SK-010",
        "name": "Modern Full-Stack React & Next.js",
        "category": "Software Engineering",
        "sector": "Information Technology",
        "esco_code": "2513.1.2",
        "demand_score": 84,
        "supply_score": 79,
        "growth_rate_yoy": "+18%",
        "ncs_code": "2513.0101",
        "description": "Server-side rendering, API routes, responsive glass UI, state management, and edge caching."
    },

    # Green Energy & Clean Tech
    {
        "id": "SK-011",
        "name": "EV Battery Management Systems (BMS)",
        "category": "Electric Mobility",
        "sector": "Automotive & Clean Energy",
        "esco_code": "2144.2.7",
        "demand_score": 92,
        "supply_score": 28,
        "growth_rate_yoy": "+130%",
        "ncs_code": "2144.0201",
        "description": "Thermal runaway prevention, state-of-charge algorithms, cell balancing, and CAN bus integration."
    },
    {
        "id": "SK-012",
        "name": "Grid-Tied Solar Inverter Design & Smart Grids",
        "category": "Renewable Energy",
        "sector": "Energy & Utilities",
        "esco_code": "2151.1.4",
        "demand_score": 83,
        "supply_score": 45,
        "growth_rate_yoy": "+52%",
        "ncs_code": "2151.0103",
        "description": "Power electronics, MPPT controllers, grid compliance, and microgrid synchronization."
    },

    # Deprecated / Declining Skills
    {
        "id": "SK-013",
        "name": "Legacy Visual Basic 6 & COM+ Architecture",
        "category": "Legacy Software",
        "sector": "Information Technology",
        "esco_code": "2512.9.1",
        "demand_score": 12,
        "supply_score": 68,
        "growth_rate_yoy": "-64%",
        "ncs_code": "2512.0901",
        "description": "Deprecated desktop client development with outdated runtime and non-existent security support."
    },
    {
        "id": "SK-014",
        "name": "ActionScript 2.0 & Adobe Flash Web Design",
        "category": "Legacy Web",
        "sector": "Information Technology",
        "esco_code": "2513.9.4",
        "demand_score": 4,
        "supply_score": 58,
        "growth_rate_yoy": "-92%",
        "ncs_code": "2513.0902",
        "description": "Obsolete browser plugin animation, replaced universally by HTML5 canvas and WebGL."
    },
    {
        "id": "SK-015",
        "name": "Manual Black-Box Testing for Win32 Apps",
        "category": "Quality Assurance",
        "sector": "Information Technology",
        "esco_code": "2519.1.1",
        "demand_score": 22,
        "supply_score": 74,
        "growth_rate_yoy": "-41%",
        "ncs_code": "2519.0102",
        "description": "Manual click-through desktop testing without automation frameworks (Cypress/Playwright/CI)."
    }
]

# ============================================================================
# 2. SWAYAM & MAHASWAYAM COURSE REPOSITORY
# ============================================================================

SWAYAM_COURSES: List[Dict[str, Any]] = [
    {
        "course_id": "SW-AI-101",
        "title": "Deep Learning & Generative AI Architectures",
        "provider": "NPTEL / IIT Madras",
        "platform": "SWAYAM",
        "instructor": "Prof. Mitesh Khapra",
        "duration_weeks": 12,
        "credits": 4,
        "level": "Postgraduate / Advanced UG",
        "status": "Active",
        "enrolled_count": 34800,
        "rating": 4.88,
        "skills_covered": [
            "Generative AI & LLM Fine-Tuning",
            "Transformer Models",
            "Prompt Engineering",
            "PyTorch",
            "Diffusion Models"
        ],
        "syllabus_highlights": [
            "Attention mechanisms and Transformer encoders/decoders",
            "Fine-tuning LLaMA, Mistral, and BERT architectures",
            "Retrieval-Augmented Generation (RAG) with ChromaDB and FAISS",
            "Reinforcement Learning with Human Feedback (RLHF)"
        ],
        "alignment_status": "High Alignment",
        "recommendation_reason": "Directly addresses India's largest tech talent deficit in LLM fine-tuning and AI engineering."
    },
    {
        "course_id": "SW-CS-204",
        "title": "Cloud Native DevOps & Container Orchestration",
        "provider": "AICTE / Mahaswayam",
        "platform": "Mahaswayam",
        "instructor": "Dr. Rajesh Kulkarni",
        "duration_weeks": 8,
        "credits": 3,
        "level": "Undergraduate",
        "status": "Active",
        "enrolled_count": 21500,
        "rating": 4.79,
        "skills_covered": [
            "Kubernetes & Cloud-Native Microservices",
            "Docker",
            "Terraform & Multi-Cloud IaC",
            "CI/CD Pipelines",
            "GitOps"
        ],
        "syllabus_highlights": [
            "Kubernetes architecture, Pods, Services, and Ingress controllers",
            "Infrastructure automation using HashiCorp Terraform",
            "ArgoCD and automated zero-downtime deployment pipelines",
            "Observability with Prometheus, Grafana, and OpenTelemetry"
        ],
        "alignment_status": "High Alignment",
        "recommendation_reason": "Closes the 48% deficit gap in enterprise Cloud Native engineering across state IT corridors."
    },
    {
        "course_id": "SW-SEC-305",
        "title": "Cloud Security, Zero Trust Architecture & Forensics",
        "provider": "NPTEL / IIT Kanpur",
        "platform": "SWAYAM",
        "instructor": "Prof. Sandeep Shukla",
        "duration_weeks": 12,
        "credits": 4,
        "level": "Postgraduate",
        "status": "Active",
        "enrolled_count": 18200,
        "rating": 4.85,
        "skills_covered": [
            "Cloud Security Architecture & Zero Trust",
            "SOC Incident Response & Threat Hunting",
            "IAM Federation",
            "Digital Forensics"
        ],
        "syllabus_highlights": [
            "Zero Trust principles, micro-segmentation, and perimeterless security",
            "Cloud security posture management (CSPM) and IAM policy validation",
            "MITRE ATT&CK framework and threat hunting automation",
            "Security incident handling and chain of custody preservation"
        ],
        "alignment_status": "Critical Alignment",
        "recommendation_reason": "High-priority national security curriculum aligned with CERT-In guidelines and NCS role standards."
    },
    {
        "course_id": "SW-EV-402",
        "title": "Electric Vehicle Powertrain & Battery Management Systems",
        "provider": "NPTEL / IIT Delhi",
        "platform": "SWAYAM",
        "instructor": "Prof. B. K. Panigrahi",
        "duration_weeks": 12,
        "credits": 4,
        "level": "Undergraduate / Professional",
        "status": "Active",
        "enrolled_count": 16400,
        "rating": 4.81,
        "skills_covered": [
            "EV Battery Management Systems (BMS)",
            "Thermal Management",
            "State of Charge (SoC) Estimation",
            "CAN Bus Communication"
        ],
        "syllabus_highlights": [
            "Lithium-ion cell electrochemistry and degradation mechanisms",
            "Kalman filtering for accurate SoC and SoH estimation",
            "Hardware-in-the-loop (HIL) BMS testing and ISO 26262 functional safety",
            "Regenerative braking integration with motor controllers"
        ],
        "alignment_status": "High Alignment",
        "recommendation_reason": "Directly supports Maharashtra EV Policy 2025 and industrial electrification initiatives."
    },
    {
        "course_id": "SW-DATA-108",
        "title": "Petabyte-Scale Distributed Data Engineering with Spark",
        "provider": "NPTEL / IISc Bangalore",
        "platform": "SWAYAM",
        "instructor": "Prof. Yogesh Simmhan",
        "duration_weeks": 8,
        "credits": 3,
        "level": "Advanced UG / PG",
        "status": "Active",
        "enrolled_count": 19300,
        "rating": 4.76,
        "skills_covered": [
            "Distributed Data Engineering (Spark/Flink)",
            "Apache Kafka",
            "Delta Lake & Iceberg",
            "PySpark"
        ],
        "syllabus_highlights": [
            "Distributed computing foundations, RDDs, DataFrames, and Catalyst Optimizer",
            "Structured Streaming with Apache Spark and Kafka event backbones",
            "ACID transactions over data lakes with Apache Iceberg",
            "Data warehouse modernization and medallion architecture"
        ],
        "alignment_status": "High Alignment",
        "recommendation_reason": "Bridges academic curricula with real-world enterprise Big Data requirements."
    },
    {
        "course_id": "SW-SYS-501",
        "title": "Systems Programming with Rust & WebAssembly",
        "provider": "AICTE / NPTEL",
        "platform": "SWAYAM",
        "instructor": "Dr. Arnab Sen",
        "duration_weeks": 8,
        "credits": 3,
        "level": "Undergraduate",
        "status": "Active",
        "enrolled_count": 12100,
        "rating": 4.90,
        "skills_covered": [
            "Rust Systems Programming & WebAssembly",
            "Memory Safety Without GC",
            "Concurrent Programming",
            "WASM Compilers"
        ],
        "syllabus_highlights": [
            "Ownership, borrowing, and lifetimes in Rust",
            "Fearless concurrency, channels, and async runtimes (Tokio)",
            "Compiling Rust to WebAssembly for near-native web execution",
            "Building high-throughput microservices and CLI tools"
        ],
        "alignment_status": "High Alignment",
        "recommendation_reason": "Addresses the 61% supply deficit for memory-safe systems engineering in modern software stacks."
    },

    # Deprecated / Obsolete Course Records in Catalog
    {
        "course_id": "SW-OBS-001",
        "title": "Desktop Application Development in Visual Basic 6.0",
        "provider": "State Technical Board / Mahaswayam",
        "platform": "Mahaswayam",
        "instructor": "Retired Faculty Panel",
        "duration_weeks": 10,
        "credits": 3,
        "level": "Diploma / Undergraduate",
        "status": "Obsolete",
        "enrolled_count": 420,
        "rating": 2.65,
        "skills_covered": [
            "Legacy Visual Basic 6 & COM+ Architecture",
            "DAO/ADO Database Access",
            "ActiveX Controls"
        ],
        "syllabus_highlights": [
            "VB6 IDE navigation and form creation",
            "Connecting to Access MDB files via DAO",
            "Compiling 32-bit standalone executables for Windows 98/XP"
        ],
        "alignment_status": "Critical Deprecation",
        "recommendation_reason": "Flagged for immediate decommissioning. Market demand has declined by 64% YoY."
    },
    {
        "course_id": "SW-OBS-002",
        "title": "Interactive Web Media with Adobe Flash & ActionScript 2",
        "provider": "Vocational Directorate / Mahaswayam",
        "platform": "Mahaswayam",
        "instructor": "Multimedia Training Board",
        "duration_weeks": 8,
        "credits": 2,
        "level": "Certificate",
        "status": "Obsolete",
        "enrolled_count": 180,
        "rating": 2.10,
        "skills_covered": [
            "ActionScript 2.0 & Adobe Flash Web Design",
            "Flash Keyframe Animation",
            "SWF File Publishing"
        ],
        "syllabus_highlights": [
            "Timeline animations and shape tweens",
            "Button scripting with on(release) in ActionScript 2.0",
            "Exporting to SWF for deprecated web browsers"
        ],
        "alignment_status": "Critical Deprecation",
        "recommendation_reason": "Flash was permanently sunsetted in 2020. Course provides zero current labor market value."
    },
    {
        "course_id": "SW-OBS-003",
        "title": "Manual Verification & QA for Win32 Standalone Applications",
        "provider": "Continuing Education Wing",
        "platform": "SWAYAM",
        "instructor": "Legacy QA Panel",
        "duration_weeks": 6,
        "credits": 2,
        "level": "Undergraduate",
        "status": "Obsolete",
        "enrolled_count": 650,
        "rating": 3.10,
        "skills_covered": [
            "Manual Black-Box Testing for Win32 Apps",
            "Static Test Plan Worksheets",
            "Bug Tracking on Paper Logs"
        ],
        "syllabus_highlights": [
            "Writing manual test scenarios in Excel",
            "Boundary value analysis for desktop input forms",
            "Manual defect reporting without CI/CD integration"
        ],
        "alignment_status": "Deprecated",
        "recommendation_reason": "Needs immediate migration to Automated E2E Testing (Playwright, Cypress, CI Pipelines)."
    }
]

# ============================================================================
# 3. NLP SIMILARITY ENGINE (Dense Embeddings + Local TF-IDF Fallback)
# ============================================================================

class NLPSimilarityEngine:
    """
    NLP Engine that provides semantic similarity search between industry
    skill requisitions and SWAYAM course curricula.
    Gracefully falls back to TF-IDF vectorization if sentence-transformers is unavailable.
    """
    def __init__(self):
        self.model_type = "TF-IDF / N-gram Cosine Engine"
        self.encoder = None
        self._initialized = False

    def _initialize_model(self):
        """Initializes SentenceTransformer lazily or falls back to TF-IDF cosine similarity."""
        if self._initialized:
            return
        self._initialized = True
        try:
            from sentence_transformers import SentenceTransformer
            self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
            self.model_type = "sentence-transformers (all-MiniLM-L6-v2)"
        except Exception:
            self.model_type = "TF-IDF / N-gram Cosine Fallback"

    def get_embeddings(self, texts: List[str]):
        """Encodes a batch of texts into PyTorch tensor embeddings in a single pass."""
        self._initialize_model()
        import torch
        if self.encoder is not None:
            return self.encoder.encode(texts, convert_to_tensor=True)
        else:
            from sklearn.feature_extraction.text import TfidfVectorizer
            vec = TfidfVectorizer().fit_transform(texts)
            return torch.tensor(vec.toarray(), dtype=torch.float32)

    def _tokenize(self, text: str) -> List[str]:
        """Simple, robust tokenization and normalization."""
        text = text.lower()
        # Keep alphanumeric words and common skill characters like C++, .NET
        tokens = re.findall(r'[a-z0-9+#.-]+', text)
        stopwords = {
            "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
            "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
            "to", "was", "were", "will", "with", "course", "curriculum", "skills"
        }
        return [t for t in tokens if t not in stopwords and len(t) > 1]

    def _compute_tfidf_vector(self, tokens: List[str], idf_dict: Dict[str, float]) -> Dict[str, float]:
        tf = {}
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
        
        vec = {}
        for token, count in tf.items():
            idf = idf_dict.get(token, 1.5)
            vec[token] = (1.0 + math.log(count)) * idf
            
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {k: v / norm for k, v in vec.items()}

    def _cosine_similarity(self, vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        dot = sum(vec_a[k] * vec_b.get(k, 0.0) for k in vec_a)
        return max(0.0, min(1.0, dot))

    def calculate_similarity(self, query: str, document: str) -> float:
        """
        Calculates a normalized similarity score between 0.0 and 1.0.
        """
        # If Dense Embeddings available
        if self.encoder:
            try:
                emb1 = self.encoder.encode(query, convert_to_tensor=False)
                emb2 = self.encoder.encode(document, convert_to_tensor=False)
                # Cosine similarity between 1D vectors
                dot = sum(a * b for a, b in zip(emb1, emb2))
                norm_a = math.sqrt(sum(a * a for a in emb1))
                norm_b = math.sqrt(sum(b * b for b in emb2))
                if norm_a > 0 and norm_b > 0:
                    sim = dot / (norm_a * norm_b)
                    return max(0.0, min(1.0, float(sim)))
            except Exception:
                pass  # Fall through to TF-IDF

        # Fast Resilient TF-IDF Fallback
        q_tokens = self._tokenize(query)
        d_tokens = self._tokenize(document)

        if not q_tokens or not d_tokens:
            return 0.0

        # Build local IDF
        corpus = [q_tokens, d_tokens]
        doc_count = len(corpus)
        vocab = set(q_tokens + d_tokens)
        idf = {}
        for word in vocab:
            df = sum(1 for doc in corpus if word in doc)
            idf[word] = math.log((1 + doc_count) / (1 + df)) + 1.0

        vec_q = self._compute_tfidf_vector(q_tokens, idf)
        vec_d = self._compute_tfidf_vector(d_tokens, idf)

        base_sim = self._cosine_similarity(vec_q, vec_d)

        # Keyword boost: If target query tokens directly appear in doc
        overlap = set(q_tokens).intersection(set(d_tokens))
        boost = min(0.35, len(overlap) * 0.12)

        return min(0.98, base_sim * 0.7 + boost)


# Singleton engine instance
nlp_engine = NLPSimilarityEngine()

# ============================================================================
# 4. BUSINESS LOGIC SERVICES
# ============================================================================

def get_gap_analysis(sector: Optional[str] = None, region: Optional[str] = None) -> Dict[str, Any]:
    """
    Computes real-time Labour Market Intelligence (LMI) Demand vs Supply gap metrics,
    identifying critical shortages, obsolete skills, and overall curriculum alignment.
    """
    skills = TAXONOMY_SKILLS
    if sector and sector.lower() != "all":
        skills = [s for s in skills if s["sector"].lower() == sector.lower()]

    enriched_skills = []
    total_demand = 0
    total_supply = 0
    critical_deficits = 0
    deprecated_count = 0

    for s in skills:
        deficit = s["demand_score"] - s["supply_score"]
        total_demand += s["demand_score"]
        total_supply += s["supply_score"]

        # Classification
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

    n = max(1, len(skills))
    avg_demand = round(total_demand / n, 1)
    avg_supply = round(total_supply / n, 1)
    alignment_score = max(0, min(100, round(100 - (abs(avg_demand - avg_supply) * 1.2), 1)))

    return {
        "metadata": {
            "sector": sector or "All Sectors",
            "region": region or "National (India - Mahaswayam & NCS Integration)",
            "total_skills_analyzed": len(skills),
            "engine_status": nlp_engine.model_type,
            "taxonomy_standard": "Lightcast / ESCO v1.1"
        },
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


def recommend_curriculum(
    query: str,
    target_role: Optional[str] = None,
    sector: Optional[str] = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Ranks SWAYAM and Mahaswayam courses against an input industry skill requirement or role description
    using NLP semantic embeddings and cosine similarity.
    """
    query_text = f"{query} {target_role or ''}".strip()
    results = []

    for course in SWAYAM_COURSES:
        # Build comprehensive document text for matching
        doc_text = (
            f"{course['title']} "
            f"{' '.join(course['skills_covered'])} "
            f"{' '.join(course['syllabus_highlights'])} "
            f"{course['provider']} {course['level']}"
        )

        sim_score = nlp_engine.calculate_similarity(query_text, doc_text)

        # Matched skills overlap
        matched_skills = [
            skill for skill in course["skills_covered"]
            if any(q.lower() in skill.lower() or skill.lower() in q.lower() for q in query.split())
        ]

        # Calculate estimated deficit closure potential
        deficit_impact = 0
        for skill_name in course["skills_covered"]:
            for tax_skill in TAXONOMY_SKILLS:
                if tax_skill["name"].lower() in skill_name.lower() or skill_name.lower() in tax_skill["name"].lower():
                    deficit_impact = max(deficit_impact, tax_skill["demand_score"] - tax_skill["supply_score"])

        results.append({
            "course_id": course["course_id"],
            "title": course["title"],
            "provider": course["provider"],
            "platform": course["platform"],
            "instructor": course["instructor"],
            "duration_weeks": course["duration_weeks"],
            "credits": course["credits"],
            "level": course["level"],
            "status": course["status"],
            "enrolled_count": course["enrolled_count"],
            "rating": course["rating"],
            "match_score": round(sim_score * 100, 1),
            "matched_skills": matched_skills or course["skills_covered"][:2],
            "syllabus_highlights": course["syllabus_highlights"],
            "alignment_status": course["alignment_status"],
            "recommendation_reason": course["recommendation_reason"],
            "gap_closure_potential": f"+{max(15, deficit_impact)}% alignment uplift"
        })

    # Sort descending by match score
    results.sort(key=lambda x: x["match_score"], reverse=True)

    return {
        "query": query,
        "target_role": target_role or "Unspecified",
        "model_used": nlp_engine.model_type,
        "total_courses_evaluated": len(SWAYAM_COURSES),
        "recommendations": results[:top_k]
    }


def get_obsolete_courses() -> Dict[str, Any]:
    """
    Returns courses and curriculum tracks flagged as obsolete or deprecated
    due to plummeting industry demand, with migration recommendations.
    """
    obsolete_items = []
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
        if course["status"] == "Obsolete":
            rep = replacement_map.get(course["course_id"], {})
            obsolete_items.append({
                "course_id": course["course_id"],
                "title": course["title"],
                "provider": course["provider"],
                "platform": course["platform"],
                "status": course["status"],
                "enrolled_count": course["enrolled_count"],
                "rating": course["rating"],
                "deprecation_reason": course["recommendation_reason"],
                "action_required": rep.get("action", "Curriculum Audit"),
                "recommended_replacement": {
                    "course_id": rep.get("replacement_course_id"),
                    "title": rep.get("replacement_title")
                }
            })

    return {
        "total_flagged_courses": len(obsolete_items),
        "audit_standard": "NCS & Mahaswayam Curricular Quality Directive 2026",
        "obsolete_courses": obsolete_items
    }


# ============================================================================
# 5. VECTORIZED SKILL GAP EVALUATOR (PyTorch Batch Tensor Operations)
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
    import torch
    import torch.nn.functional as F

    # Normalize candidate skills into a standard list of {name, proficiency}
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

