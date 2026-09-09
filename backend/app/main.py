from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import feedback, themes, query

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Customer Feedback Theme Explorer",
    description=(
        "Sistem qe zbulon automatikisht temat brenda feedback-ut te klienteve "
        "(pa liste te paracaktuar kategorish) dhe pergjigjet pyetjeve analitike "
        "te bazuara ne feedback real, me citime."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(feedback.router)
app.include_router(themes.router)
app.include_router(query.router)


@app.get("/health")
def health():
    return {"status": "ok"}