from app.services.planning_engine import PlanningEngine

if __name__ == "__main__":
    file_path = "data/sample_input.xlsx"

    engine = PlanningEngine(file_path=file_path)
    result = engine.run()

    print("\nFinal result:")
    print(result)