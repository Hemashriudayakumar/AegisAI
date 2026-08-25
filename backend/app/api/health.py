from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.config import settings
from app.policies.engine import policy_engine

router = APIRouter(tags=["health"])

@router.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if "unhealthy" not in db_status else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": db_status,
        "model": settings.OLLAMA_MODEL,
        "active_policies_count": len(policy_engine.list_policies()),
        "policies_loaded": list(policy_engine.policies.keys())
    }
