from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import projects, sessions, content, agent

app = FastAPI(
    title="灵枢桌面版 API",
    description="AI 辅助创作平台后端",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(sessions.router)
app.include_router(content.router)
app.include_router(agent.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
