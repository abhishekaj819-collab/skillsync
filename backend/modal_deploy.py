"""
SkillSetu - Modal Serverless Deployment Engine (SIH PS 26134)
=============================================================
Deploys the FastAPI backend + PyTorch dense vector embeddings to Modal serverless GPUs / CPUs.

Deploy:
  python -m modal deploy backend/modal_deploy.py
"""

import os
import sys
import modal

app = modal.App("skillsync-api")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "fastapi>=0.110.0",
        "uvicorn[standard]>=0.28.0",
        "pydantic>=2.0.0",
        "scikit-learn>=1.3.0",
        "sentence-transformers>=2.2.2",
        "torch>=2.1.0",
        "numpy>=1.24.0",
        "sqlalchemy>=2.0.0",
        "requests>=2.31.0",
    )
    .add_local_dir(os.path.dirname(os.path.abspath(__file__)), remote_path="/root/backend")
)


@app.function(
    image=image,
    scaledown_window=300,
    allow_concurrent_inputs=100,
    container_idle_timeout=120,
)
@modal.asgi_app()
def serve():
    import sys
    backend_dir = "/root/backend"
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    # Seed and initialize SQLite database with 25+ Maharashtra job postings & MSSDS frameworks
    try:
        from seed_real_data import run_seed
        run_seed()
    except Exception as e:
        print(f"[WARN] Database seeding notice: {e}")

    from main import app as fastapi_app
    return fastapi_app
