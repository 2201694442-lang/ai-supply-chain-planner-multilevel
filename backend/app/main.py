from datetime import datetime
from pathlib import Path
import shutil

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.services.planning_engine import PlanningEngine

app = FastAPI(title="AI-Driven Supply Shortage Planner")

# Allow frontend local dev and deployment access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_DIR = BASE_DIR / "uploaded_files"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

DEMO_FILE = BASE_DIR / "data" / "ai_infra_supply_chain_demo.xlsx"

def format_heatmap(result_df):
    df = result_df.copy()
    df["date"] = df["date"].astype(str)

    # 保证数值列可用
    for col in ["shortage", "inventory", "demand", "supply"]:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    # 统一日期顺序
    dates = sorted(df["date"].unique().tolist())

    rows = []
    for material in sorted(df["material"].unique().tolist()):
        material_df = df[df["material"] == material].copy()
        material_df = material_df.set_index("date")

        cells = []
        for date in dates:
            if date in material_df.index:
                row = material_df.loc[date]

                # 如果同一天同物料可能有多条，取第一条或聚合
                if hasattr(row, "ndim") and row.ndim > 1:
                    row = row.iloc[0]

                cells.append(
                    {
                        "date": date,
                        "shortage_qty": float(row.get("shortage", 0) or 0),
                        "inventory": float(row.get("inventory", 0) or 0),
                        "demand": float(row.get("demand", 0) or 0),
                        "supply": float(row.get("supply", 0) or 0),
                    }
                )
            else:
                cells.append(
                    {
                        "date": date,
                        "shortage_qty": 0,
                        "inventory": 0,
                        "demand": 0,
                        "supply": 0,
                    }
                )

        rows.append(
            {
                "material": material,
                "cells": cells,
            }
        )

    return {
        "dates": dates,
        "rows": rows,
    }

def format_result(result_df, summary):
    result_df = result_df.copy()
    result_df["date"] = result_df["date"].astype(str)

    return {
        "summary": summary,
        "results": result_df.to_dict(orient="records"),
        "heatmap": format_heatmap(result_df),
    }


def build_shortage_table(result_df: pd.DataFrame) -> pd.DataFrame:
    shortage_df = result_df[result_df["shortage"] > 0].copy()

    if shortage_df.empty:
        return pd.DataFrame(
            columns=[
                "material",
                "total_shortage_qty",
                "earliest_shortage_date",
                "shortage_days",
            ]
        )

    summary_df = (
        shortage_df.groupby("material")
        .agg(
            total_shortage_qty=("shortage", "sum"),
            earliest_shortage_date=("date", "min"),
            shortage_days=("date", "count"),
        )
        .reset_index()
    )

    summary_df["earliest_shortage_date"] = (
        pd.to_datetime(summary_df["earliest_shortage_date"])
        .dt.strftime("%Y-%m-%d")
    )

    return summary_df


@app.get("/")
def root():
    return {"message": "Backend is running"}


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/debug-paths")
def debug_paths():
    return {
        "base_dir": str(BASE_DIR),
        "demo_file": str(DEMO_FILE),
        "demo_exists": DEMO_FILE.exists(),
        "upload_dir": str(UPLOAD_DIR),
        "temp_dir": str(TEMP_DIR),
    }

@app.post("/analyze-demo")
def analyze_demo():
    try:
        if not DEMO_FILE.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Demo file not found: {DEMO_FILE}",
            )

        engine = PlanningEngine(file_path=str(DEMO_FILE))
        result_df, summary = engine.run()

        return format_result(result_df, summary)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Demo analysis failed: {str(e)}",
        )


@app.post("/analyze-upload")
def analyze_upload(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    if not file.filename.endswith(".xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Only .xlsx files are supported.",
        )

    save_path = UPLOAD_DIR / file.filename

    with save_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        engine = PlanningEngine(file_path=str(save_path))
        result_df, summary = engine.run()

        response = format_result(result_df, summary)
        response["filename"] = file.filename
        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}",
        )


@app.get("/download-inventory")
def download_inventory():
    try:
        if not DEMO_FILE.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Demo file not found: {DEMO_FILE}",
            )

        engine = PlanningEngine(file_path=str(DEMO_FILE))
        result_df, _ = engine.run()

        export_df = result_df.copy()
        export_df["date"] = pd.to_datetime(export_df["date"]).dt.strftime("%Y-%m-%d")

        filename = f"daily_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        temp_path = TEMP_DIR / filename

        with pd.ExcelWriter(temp_path) as writer:
            export_df.to_excel(writer, sheet_name="Daily Inventory", index=False)

        return FileResponse(
            path=temp_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Inventory download failed: {str(e)}",
        )


@app.get("/download-shortage")
def download_shortage():
    try:
        if not DEMO_FILE.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Demo file not found: {DEMO_FILE}",
            )

        engine = PlanningEngine(file_path=str(DEMO_FILE))
        result_df, _ = engine.run()

        shortage_table = build_shortage_table(result_df)

        filename = f"shortage_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        temp_path = TEMP_DIR / filename

        with pd.ExcelWriter(temp_path) as writer:
            shortage_table.to_excel(writer, sheet_name="Shortage Summary", index=False)

        return FileResponse(
            path=temp_path,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Shortage download failed: {str(e)}",
        )