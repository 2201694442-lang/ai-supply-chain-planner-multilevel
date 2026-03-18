from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.services.planning_engine import PlanningEngine

app = FastAPI(title="AI-Driven Supply Shortage Planner")

# 👇 允许前端访问（很关键！）
origins = [
    "http://localhost:5173",  # 本地前端
    "*"  # 先全部允许，后面再收紧
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 👇 测试接口（必须有）
@app.get("/")
def root():
    return {"message": "Backend is running"}

# 👇 健康检查（部署用）
@app.get("/health")
def health():
    return {"status": "ok"}

# 👇 你的核心接口
@app.post("/analyze-demo")
def analyze_demo():
    file_path = "data/sample_input.xlsx"

    engine = PlanningEngine(file_path=file_path)
    result_df = engine.run()

    # 转 JSON
    result_df["date"] = result_df["date"].astype(str)

    results = result_df.to_dict(orient="records")

    summary = {
        "total_rows": len(result_df),
        "shortage_rows": int((result_df["shortage"] > 0).sum()),
        "total_shortage": float(result_df["shortage"].sum())
    }

    return {
        "summary": summary,
        "results": results
    }