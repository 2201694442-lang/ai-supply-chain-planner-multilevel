import pandas as pd


class PlanningEngine:

    def __init__(self, file_path):
        self.file_path = file_path

    def load_data(self):

        production = pd.read_excel(self.file_path, sheet_name="ProductionPlan")
        bom = pd.read_excel(self.file_path, sheet_name="BOM")
        supply = pd.read_excel(self.file_path, sheet_name="SupplyPlan")
        stock = pd.read_excel(self.file_path, sheet_name="OpeningStock")

        print("Loaded sheets successfully")

        return production, bom, supply, stock

    def calculate_demand(self, production, bom):

        demand = production.merge(bom, on="sku")

        demand["demand"] = demand["qty"] * demand["usage"]

        demand = demand[["date", "material", "demand"]]

        demand = demand.groupby(["date", "material"]).sum().reset_index()

        print("Material demand calculated")

        return demand

    def simulate_inventory(self, demand, supply, stock):

        df = demand.merge(supply, on=["date", "material"], how="outer")

        df["demand"] = df["demand"].fillna(0)
        df["supply"] = df["supply"].fillna(0)

        df = df.merge(stock, on="material", how="left")

        df = df.sort_values(["material", "date"])

        results = []

        for material, group in df.groupby("material"):

            inventory = group["opening_stock"].iloc[0]

            for _, row in group.iterrows():

                inventory = inventory + row["supply"] - row["demand"]

                shortage = abs(inventory) if inventory < 0 else 0

                results.append({
                    "date": row["date"],
                    "material": material,
                    "demand": row["demand"],
                    "supply": row["supply"],
                    "inventory": inventory,
                    "shortage": shortage
                })

        result_df = pd.DataFrame(results)

        print("Inventory simulation completed")

        return result_df

    def run(self):

        production, bom, supply, stock = self.load_data()

        demand = self.calculate_demand(production, bom)

        result = self.simulate_inventory(demand, supply, stock)

        print("Shortage analysis completed")

        return result