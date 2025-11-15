import os
from datetime import datetime
from typing import List, Optional, Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from database import db, create_document, get_documents

# External libraries for HTTP and TTS (placeholders using built-ins/requests)
import requests

app = FastAPI(title="PakGPT News Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Schemas for API payloads --------------------
class IngestRequest(BaseModel):
    sources: List[str] = Field(default_factory=list, description="List of source identifiers to fetch from")
    language: Literal["en", "ur"] = "en"

class PersonalizeRequest(BaseModel):
    city: Optional[str] = None
    interests: List[str] = Field(default_factory=list)
    urgency: Literal["breaking", "important", "full"] = "important"
    language: Literal["en", "ur"] = "en"

class AudioRequest(BaseModel):
    text: str
    language: Literal["en", "ur"] = "en"

# -------------------- Utility AI mock functions --------------------
# Note: In this environment, we don't call external LLMs. We'll implement
# deterministic placeholder logic that structures data as required.

def ai_clean_and_summarize(article: dict, language: str = "en") -> dict:
    """Return a bias-reduced 3-bullet summary and 1-line impact.
    This is a deterministic placeholder to keep the app functional.
    """
    title = article.get("title") or "Untitled"
    content = article.get("description") or article.get("content") or ""
    bullets = [
        f"Key point: {title[:70]}",
        f"Source: {article.get('source', 'unknown')}",
        f"Time: {article.get('published_at', '')}",
    ]
    impact = "Potential impact on citizens and businesses to be monitored."

    if language == "ur":
        bullets = [
            "اہم نقطہ: " + title[:70],
            "سورس: " + (article.get('source') or "نامعلوم"),
            "وقت: " + (str(article.get('published_at')) or ""),
        ]
        impact = "شہریوں اور کاروبار پر ممکنہ اثرات کے لئے نظر رکھیں۔"

    return {
        "bullets": bullets[:3],
        "impact": impact,
    }


def ai_fact_check(article: dict) -> dict:
    """Mock fact-check classification with simple heuristics.
    In production, replace with proper pipeline and sources.
    """
    title = (article.get("title") or "").lower()
    if any(x in title for x in ["breaking", "official", "gov"]):
        return {"fact_status": "Verified", "risk_score": 5}
    if any(x in title for x in ["rumour", "leak", "unconfirmed"]):
        return {"fact_status": "Rumour", "risk_score": 65}
    return {"fact_status": "Unconfirmed", "risk_score": 30}


# -------------------- Routes --------------------
@app.get("/")
def root():
    return {"message": "PakGPT News Engine backend running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = getattr(db, 'name', '✅ Connected')
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


@app.post("/api/ingest")
def ingest_news(payload: IngestRequest):
    """Ingest news from given sources, clean, summarize, fact-check, and store.
    For demo, we simulate ingestion with a few stubbed articles.
    """
    sample_articles = [
        {
            "source": "Dawn",
            "title": "Breaking: Govt announces new economic policy",
            "url": "https://www.dawn.com/sample1",
            "published_at": datetime.utcnow().isoformat(),
            "city": "Islamabad",
            "interests": ["economy", "politics"],
        },
        {
            "source": "Geo",
            "title": "PSL updates: Lahore Qalandars clinch close match",
            "url": "https://www.geo.tv/sample2",
            "published_at": datetime.utcnow().isoformat(),
            "city": "Lahore",
            "interests": ["sports"],
        },
        {
            "source": "Express",
            "title": "Technology jobs rising in Karachi's startup ecosystem",
            "url": "https://www.express.pk/sample3",
            "published_at": datetime.utcnow().isoformat(),
            "city": "Karachi",
            "interests": ["tech", "jobs"],
        },
    ]

    created_ids = []
    for art in sample_articles:
        # AI steps
        summary = ai_clean_and_summarize(art, language=payload.language)
        check = ai_fact_check(art)
        # Compose document per language
        doc = {
            **art,
            **summary,
            **check,
            "language": payload.language,
            "urgency": "important",
        }
        try:
            _id = create_document("newsitem", doc)
            created_ids.append(_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"DB error: {str(e)}")

    return {"inserted": len(created_ids), "ids": created_ids}


@app.post("/api/feed")
def get_personalized_feed(payload: PersonalizeRequest):
    """Return personalized feed per preferences with 3 bullets, impact, and fact status."""
    query = {}
    if payload.city:
        query["city"] = payload.city
    if payload.interests:
        query["interests"] = {"$in": payload.interests}
    if payload.urgency:
        # In this demo, we simply pass urgency through
        query["urgency"] = payload.urgency
    if payload.language:
        query["language"] = payload.language

    try:
        docs = get_documents("newsitem", query, limit=50)
        # Normalize ObjectId and fields
        normalized = []
        for d in docs:
            d["id"] = str(d.get("_id"))
            d.pop("_id", None)
            # Ensure bullets exactly 3
            bullets = d.get("bullets") or []
            if len(bullets) > 3:
                bullets = bullets[:3]
            elif len(bullets) < 3:
                bullets += [""] * (3 - len(bullets))
            d["bullets"] = bullets
            normalized.append(d)
        return {"count": len(normalized), "items": normalized}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {str(e)}")


@app.post("/api/audio")
def text_to_audio(payload: AudioRequest):
    """Generate a simple audio placeholder as a URL. In production, integrate TTS.
    """
    # For demo, we return a data: URL with text content. Real app would return audio file URL.
    txt = payload.text.replace("\n", " ")
    lang = payload.language
    data_url = f"data:audio/wav;base64,{('UGFrR1BULWF1ZGlvLXBsYWNlaG9sZGVy').strip()}"
    return {"language": lang, "audio_url": data_url, "note": "Demo placeholder. Integrate a real TTS provider in production."}


@app.get("/api/digest")
def morning_digest(
    language: Literal["en", "ur"] = Query("en"),
    limit: int = Query(10, ge=1, le=20),
):
    """Return God Mode morning digest: top headlines + 60-second summary + why it matters."""
    try:
        docs = get_documents("newsitem", {"language": language}, limit=limit)
    except Exception:
        docs = []

    # Fallback simulated items if DB empty
    if not docs:
        fallback_titles = [
            "Fiscal updates and market outlook",
            "Security and regional developments",
            "PSX morning momentum",
            "Monsoon/weather advisory",
            "Tech/startup funding news",
        ]
        docs = [
            {
                "title": t,
                "source": "PakGPT",
                "published_at": datetime.utcnow().isoformat(),
                "bullets": [
                    "Key developments summarized",
                    "Numbers and context simplified",
                    "What to watch today",
                ],
                "impact": "Expect ripple effects for households and businesses.",
                "fact_status": "Unconfirmed",
                "risk_score": 20,
            }
            for t in fallback_titles
        ]

    headlines = [d.get("title") for d in docs][:10]
    sixty_sec_summary = (
        " ".join(h[:60] for h in headlines) + (
            "" if language == "en" else " آج کے اہم نکات کا خلاصہ۔"
        )
    )

    items = [
        {
            "title": d.get("title"),
            "bullets": (d.get("bullets") or [])[:3],
            "impact": d.get("impact"),
            "why_it_matters": d.get("impact"),
            "source": d.get("source"),
            "published_at": d.get("published_at"),
            "fact_status": d.get("fact_status", "Unconfirmed"),
            "risk_score": d.get("risk_score", 0),
        }
        for d in docs[:10]
    ]

    return {
        "headlines": headlines,
        "summary_60s": sixty_sec_summary,
        "items": items,
        "business_economy": {
            "snapshot": "FX, PSX, inflation, fuel updates at a glance.",
        },
        "global_affecting_pk": [
            "Oil prices and regional markets",
            "US/China moves impacting trade",
        ],
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
