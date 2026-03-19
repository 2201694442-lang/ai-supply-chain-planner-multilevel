import pandas as pd


class PlanningEngine:
    def __init__(self, file_path):
        self.file_path = file_path

    @staticmethod
    def _normalize_alias_columns(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
        df = df.copy()

        # 统一去掉列名前后空格
        df.columns = [str(col).strip() for col in df.columns]

        if sheet_name == "SupplyPlan":
            # 兼容 qty -> supply
            if "supply" not in df.columns and "qty" in df.columns:
                df = df.rename(columns={"qty": "supply"})

        if sheet_name == "OpeningStock":
            # 兼容 qty -> opening_stock
            if "opening_stock" not in df.columns and "qty" in df.columns:
                df = df.rename(columns={"qty": "opening_stock"})

        return df

    def validate_input(self):
        try:
            xls = pd.ExcelFile(self.file_path)
        except Exception:
            raise ValueError("Invalid Excel file. Unable to read.")

        required_sheets = [
            "ProductionPlan",
            "BOM",
            "SupplyPlan",
            "OpeningStock",
        ]

        for sheet in required_sheets:
            if sheet not in xls.sheet_names:
                raise ValueError(f"Missing sheet: {sheet}")

        # 读取各 sheet
        df_prod = pd.read_excel(xls, "ProductionPlan")
        df_bom = pd.read_excel(xls, "BOM")
        df_supply = pd.read_excel(xls, "SupplyPlan")
        df_stock = pd.read_excel(xls, "OpeningStock")

        # 兼容别名列
        df_supply = self._normalize_alias_columns(df_supply, "SupplyPlan")
        df_stock = self._normalize_alias_columns(df_stock, "OpeningStock")

        # 检查列
        for col in ["date", "sku", "qty"]:
            if col not in df_prod.columns:
                raise ValueError(f"Missing column: {col} in ProductionPlan")

        for col in ["sku", "material", "usage"]:
            if col not in df_bom.columns:
                raise ValueError(f"Missing column: {col} in BOM")

        for col in ["date", "material", "supply"]:
            if col not in df_supply.columns:
                raise ValueError(f"Missing column: {col} in SupplyPlan")

        for col in ["material", "opening_stock"]:
            if col not in df_stock.columns:
                raise ValueError(f"Missing column: {col} in OpeningStock")

        # 检查日期格式
        prod_dates = pd.to_datetime(df_prod["date"], errors="coerce")
        if prod_dates.isna().any():
            raise ValueError("Invalid date format in ProductionPlan.date")

        supply_dates = pd.to_datetime(df_supply["date"], errors="coerce")
        if supply_dates.isna().any():
            raise ValueError("Invalid date format in SupplyPlan.date")

        # 检查数值格式
        prod_qty = pd.to_numeric(df_prod["qty"], errors="coerce")
        if prod_qty.isna().any():
            raise ValueError("Invalid numeric value in ProductionPlan.qty")

        bom_usage = pd.to_numeric(df_bom["usage"], errors="coerce")
        if bom_usage.isna().any():
            raise ValueError("Invalid numeric value in BOM.usage")

        supply_qty = pd.to_numeric(df_supply["supply"], errors="coerce")
        if supply_qty.isna().any():
            raise ValueError("Invalid numeric value in SupplyPlan.supply")

        opening_stock = pd.to_numeric(df_stock["opening_stock"], errors="coerce")
        if opening_stock.isna().any():
            raise ValueError("Invalid numeric value in OpeningStock.opening_stock")

        # 检查负数
        if (prod_qty < 0).any():
            raise ValueError("Negative quantity found in ProductionPlan.qty")

        if (bom_usage < 0).any():
            raise ValueError("Negative quantity found in BOM.usage")

        if (supply_qty < 0).any():
            raise ValueError("Negative quantity found in SupplyPlan.supply")

        if (opening_stock < 0).any():
            raise ValueError("Negative quantity found in OpeningStock.opening_stock")

        # 检查 ProductionPlan 里的 SKU 是否都能在 BOM 找到
        prod_skus = set(df_prod["sku"].astype(str))
        bom_skus = set(df_bom["sku"].astype(str))
        missing_skus = prod_skus - bom_skus
        if missing_skus:
            raise ValueError(f"SKU not found in BOM: {', '.join(sorted(missing_skus))}")

    def load_data(self):
        production = pd.read_excel(self.file_path, sheet_name="ProductionPlan")
        bom = pd.read_excel(self.file_path, sheet_name="BOM")
        supply = pd.read_excel(self.file_path, sheet_name="SupplyPlan")
        stock = pd.read_excel(self.file_path, sheet_name="OpeningStock")

        # 兼容别名列
        supply = self._normalize_alias_columns(supply, "SupplyPlan")
        stock = self._normalize_alias_columns(stock, "OpeningStock")

        # 类型清洗
        production["date"] = pd.to_datetime(production["date"])
        production["qty"] = pd.to_numeric(production["qty"])
        bom["usage"] = pd.to_numeric(bom["usage"])
        supply["date"] = pd.to_datetime(supply["date"])
        supply["supply"] = pd.to_numeric(supply["supply"])
        stock["opening_stock"] = pd.to_numeric(stock["opening_stock"])

        # 去重聚合，避免重复数据导致结果异常
        production = production.groupby(["date", "sku"], as_index=False)["qty"].sum()
        bom = bom.groupby(["sku", "material"], as_index=False)["usage"].sum()
        supply = supply.groupby(["date", "material"], as_index=False)["supply"].sum()
        stock = stock.groupby(["material"], as_index=False)["opening_stock"].sum()

        return production, bom, supply, stock

    def calculate_demand(self, production, bom):
        demand = production.merge(bom, on="sku", how="left")
        demand["demand"] = demand["qty"] * demand["usage"]
        demand = demand[["date", "material", "demand"]]
        demand = demand.groupby(["date", "material"], as_index=False)["demand"].sum()
        return demand

    def simulate_inventory(self, demand, supply, stock):
        df = demand.merge(supply, on=["date", "material"], how="outer")

        df["demand"] = df["demand"].fillna(0)
        df["supply"] = df["supply"].fillna(0)

        df = df.merge(stock, on="material", how="left")
        df["opening_stock"] = df["opening_stock"].fillna(0)

        df = df.sort_values(["material", "date"]).reset_index(drop=True)

        results = []

        for material, group in df.groupby("material"):
            inventory = group["opening_stock"].iloc[0]

            for _, row in group.iterrows():
                opening_inventory = inventory
                inventory = inventory + row["supply"] - row["demand"]
                shortage = abs(inventory) if inventory < 0 else 0

                results.append(
                    {
                        "date": row["date"],
                        "material": material,
                        "opening_inventory": opening_inventory,
                        "demand": row["demand"],
                        "supply": row["supply"],
                        "inventory": inventory,
                        "shortage": shortage,
                        "shortage_flag": shortage > 0,
                    }
                )

        return pd.DataFrame(results)

    def build_summary(self, result_df):
        shortage_df = result_df[result_df["shortage"] > 0].copy()

        total_materials = int(result_df["material"].nunique())

        shortage_materials = (
            int(shortage_df["material"].nunique()) if not shortage_df.empty else 0
        )

        total_shortage_qty = (
            float(shortage_df["shortage"].sum()) if not shortage_df.empty else 0.0
        )

        earliest_shortage_date = (
            str(shortage_df["date"].min().date()) if not shortage_df.empty else None
        )

        return {
            "total_materials": total_materials,
            "shortage_materials": shortage_materials,
            "total_shortage_qty": total_shortage_qty,
            "earliest_shortage_date": earliest_shortage_date,
        }

    def run(self):
        self.validate_input()
        production, bom, supply, stock = self.load_data()
        demand = self.calculate_demand(production, bom)
        result = self.simulate_inventory(demand, supply, stock)
        summary = self.build_summary(result)
        return result, summary