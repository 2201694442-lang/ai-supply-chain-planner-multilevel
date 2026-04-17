import pandas as pd


class PlanningEngine:
    def __init__(self, file_path: str):
        self.file_path = file_path

    @staticmethod
    def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [str(col).strip() for col in df.columns]
        return df

    @staticmethod
    def _require_columns(df: pd.DataFrame, required_cols: list[str], sheet_name: str):
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing column: {col} in {sheet_name}")

    @staticmethod
    def _to_datetime(series: pd.Series, err_msg: str) -> pd.Series:
        out = pd.to_datetime(series, errors="coerce")
        if out.isna().any():
            raise ValueError(err_msg)
        return out

    @staticmethod
    def _to_numeric(series: pd.Series, err_msg: str) -> pd.Series:
        out = pd.to_numeric(series, errors="coerce")
        if out.isna().any():
            raise ValueError(err_msg)
        return out

    def validate_input(self):
        try:
            xls = pd.ExcelFile(self.file_path)
        except Exception:
            raise ValueError("Invalid Excel file. Unable to read.")

        required_sheets = [
            "ItemMaster",
            "DemandPlan",
            "BOM_MultiLevel",
            "SupplyCommit",
            "OpeningStock",
        ]

        for sheet in required_sheets:
            if sheet not in xls.sheet_names:
                raise ValueError(f"Missing sheet: {sheet}")

        item_master = self._clean_columns(pd.read_excel(xls, "ItemMaster"))
        demand_plan = self._clean_columns(pd.read_excel(xls, "DemandPlan"))
        bom = self._clean_columns(pd.read_excel(xls, "BOM_MultiLevel"))
        supply = self._clean_columns(pd.read_excel(xls, "SupplyCommit"))
        stock = self._clean_columns(pd.read_excel(xls, "OpeningStock"))

        self._require_columns(item_master, ["item_id"], "ItemMaster")

        self._require_columns(
            demand_plan,
            ["date", "deployment_batch", "program_name", "priority", "item_id", "requested_servers"],
            "DemandPlan",
        )

        self._require_columns(
            bom,
            ["parent_item", "child_item", "qty_per_parent", "lead_time_days", "level_from", "level_to"],
            "BOM_MultiLevel",
        )

        self._require_columns(
            supply,
            ["date", "item_id", "committed_qty"],
            "SupplyCommit",
        )

        self._require_columns(
            stock,
            ["item_id", "opening_qty"],
            "OpeningStock",
        )

        demand_plan["date"] = self._to_datetime(
            demand_plan["date"],
            "Invalid date format in DemandPlan.date",
        )
        supply["date"] = self._to_datetime(
            supply["date"],
            "Invalid date format in SupplyCommit.date",
        )

        if "as_of_date" in stock.columns:
            stock["as_of_date"] = self._to_datetime(
                stock["as_of_date"],
                "Invalid date format in OpeningStock.as_of_date",
            )

        demand_plan["priority"] = self._to_numeric(
            demand_plan["priority"],
            "Invalid numeric value in DemandPlan.priority",
        )
        demand_plan["requested_servers"] = self._to_numeric(
            demand_plan["requested_servers"],
            "Invalid numeric value in DemandPlan.requested_servers",
        )

        if "required_qty" in demand_plan.columns:
            demand_plan["required_qty"] = self._to_numeric(
                demand_plan["required_qty"],
                "Invalid numeric value in DemandPlan.required_qty",
            )

        bom["qty_per_parent"] = self._to_numeric(
            bom["qty_per_parent"],
            "Invalid numeric value in BOM_MultiLevel.qty_per_parent",
        )
        bom["lead_time_days"] = self._to_numeric(
            bom["lead_time_days"],
            "Invalid numeric value in BOM_MultiLevel.lead_time_days",
        )
        bom["level_from"] = self._to_numeric(
            bom["level_from"],
            "Invalid numeric value in BOM_MultiLevel.level_from",
        )
        bom["level_to"] = self._to_numeric(
            bom["level_to"],
            "Invalid numeric value in BOM_MultiLevel.level_to",
        )

        supply["committed_qty"] = self._to_numeric(
            supply["committed_qty"],
            "Invalid numeric value in SupplyCommit.committed_qty",
        )

        stock["opening_qty"] = self._to_numeric(
            stock["opening_qty"],
            "Invalid numeric value in OpeningStock.opening_qty",
        )

        if (demand_plan["requested_servers"] < 0).any():
            raise ValueError("Negative quantity found in DemandPlan.requested_servers")

        if "required_qty" in demand_plan.columns and (demand_plan["required_qty"] < 0).any():
            raise ValueError("Negative quantity found in DemandPlan.required_qty")

        if (bom["qty_per_parent"] < 0).any():
            raise ValueError("Negative quantity found in BOM_MultiLevel.qty_per_parent")

        if (bom["lead_time_days"] < 0).any():
            raise ValueError("Negative quantity found in BOM_MultiLevel.lead_time_days")

        if (supply["committed_qty"] < 0).any():
            raise ValueError("Negative quantity found in SupplyCommit.committed_qty")

        if (stock["opening_qty"] < 0).any():
            raise ValueError("Negative quantity found in OpeningStock.opening_qty")

        item_ids = set(item_master["item_id"].astype(str).str.strip())

        demand_items = set(demand_plan["item_id"].astype(str).str.strip())
        missing_demand_items = demand_items - item_ids
        if missing_demand_items:
            raise ValueError(
                f"DemandPlan item_id not found in ItemMaster: {', '.join(sorted(missing_demand_items))}"
            )

        bom_parent_items = set(bom["parent_item"].astype(str).str.strip())
        bom_child_items = set(bom["child_item"].astype(str).str.strip())
        missing_bom_items = (bom_parent_items | bom_child_items) - item_ids
        if missing_bom_items:
            raise ValueError(
                f"BOM item not found in ItemMaster: {', '.join(sorted(missing_bom_items))}"
            )

        supply_items = set(supply["item_id"].astype(str).str.strip())
        missing_supply_items = supply_items - item_ids
        if missing_supply_items:
            raise ValueError(
                f"SupplyCommit item_id not found in ItemMaster: {', '.join(sorted(missing_supply_items))}"
            )

        stock_items = set(stock["item_id"].astype(str).str.strip())
        missing_stock_items = stock_items - item_ids
        if missing_stock_items:
            raise ValueError(
                f"OpeningStock item_id not found in ItemMaster: {', '.join(sorted(missing_stock_items))}"
            )

        # DemandPlan 里的 cluster/item 必须能在 BOM 里找到下一层
        missing_parents = demand_items - bom_parent_items
        if missing_parents:
            raise ValueError(
                f"DemandPlan item_id not found as parent_item in BOM_MultiLevel: {', '.join(sorted(missing_parents))}"
            )

    def load_data(self):
        item_master = self._clean_columns(pd.read_excel(self.file_path, sheet_name="ItemMaster"))
        demand_plan = self._clean_columns(pd.read_excel(self.file_path, sheet_name="DemandPlan"))
        bom = self._clean_columns(pd.read_excel(self.file_path, sheet_name="BOM_MultiLevel"))
        supply = self._clean_columns(pd.read_excel(self.file_path, sheet_name="SupplyCommit"))
        stock = self._clean_columns(pd.read_excel(self.file_path, sheet_name="OpeningStock"))

        item_master["item_id"] = item_master["item_id"].astype(str).str.strip()

        demand_plan["date"] = pd.to_datetime(demand_plan["date"])
        demand_plan["item_id"] = demand_plan["item_id"].astype(str).str.strip()
        demand_plan["deployment_batch"] = demand_plan["deployment_batch"].astype(str).str.strip()
        demand_plan["program_name"] = demand_plan["program_name"].astype(str).str.strip()
        demand_plan["priority"] = pd.to_numeric(demand_plan["priority"])
        demand_plan["requested_servers"] = pd.to_numeric(demand_plan["requested_servers"])

        if "required_qty" in demand_plan.columns:
            demand_plan["required_qty"] = pd.to_numeric(demand_plan["required_qty"])
        else:
            demand_plan["required_qty"] = 1.0

        bom["parent_item"] = bom["parent_item"].astype(str).str.strip()
        bom["child_item"] = bom["child_item"].astype(str).str.strip()
        bom["qty_per_parent"] = pd.to_numeric(bom["qty_per_parent"])
        bom["lead_time_days"] = pd.to_numeric(bom["lead_time_days"]).astype(int)
        bom["level_from"] = pd.to_numeric(bom["level_from"]).astype(int)
        bom["level_to"] = pd.to_numeric(bom["level_to"]).astype(int)

        supply["date"] = pd.to_datetime(supply["date"])
        supply["item_id"] = supply["item_id"].astype(str).str.strip()
        supply["committed_qty"] = pd.to_numeric(supply["committed_qty"])

        stock["item_id"] = stock["item_id"].astype(str).str.strip()
        stock["opening_qty"] = pd.to_numeric(stock["opening_qty"])

        # 去重聚合
        supply = supply.groupby(["date", "item_id"], as_index=False)["committed_qty"].sum()
        stock = stock.groupby(["item_id"], as_index=False)["opening_qty"].sum()

        return item_master, demand_plan, bom, supply, stock

    def _explode_from_item(
        self,
        current_item: str,
        required_qty: float,
        required_date: pd.Timestamp,
        bom_children_map: dict,
        records: list[dict],
        deployment_batch: str,
        program_name: str,
        priority: float,
        root_cluster: str,
    ):
        children = bom_children_map.get(current_item, [])

        # 叶子节点：记为最终采购/库存需求
        if not children:
            records.append(
                {
                    "date": required_date,
                    "material": current_item,
                    "demand": float(required_qty),
                    "deployment_batch": deployment_batch,
                    "program_name": program_name,
                    "priority": priority,
                    "root_cluster": root_cluster,
                }
            )
            return

        for child in children:
            child_item = child["child_item"]
            qty_per_parent = child["qty_per_parent"]
            lead_time_days = child["lead_time_days"]

            child_qty = required_qty * qty_per_parent
            child_date = required_date - pd.Timedelta(days=lead_time_days)

            self._explode_from_item(
                current_item=child_item,
                required_qty=child_qty,
                required_date=child_date,
                bom_children_map=bom_children_map,
                records=records,
                deployment_batch=deployment_batch,
                program_name=program_name,
                priority=priority,
                root_cluster=root_cluster,
            )

    def calculate_demand(self, demand_plan: pd.DataFrame, bom: pd.DataFrame) -> pd.DataFrame:
        """
        新逻辑：
        1. DemandPlan 的 item_id 是 cluster
        2. requested_servers 是这次部署实际需要的 server 数
        3. cluster -> server 这一层用 requested_servers 驱动，而不是死用 BOM 模板数量
        4. server -> component 及更下层，按 BOM qty_per_parent 递归展开
        5. 每一层按 lead_time_days 向前推需求日期
        """
        bom_children_map: dict[str, list[dict]] = {}
        for _, row in bom.iterrows():
            parent = row["parent_item"]
            bom_children_map.setdefault(parent, []).append(
                {
                    "child_item": row["child_item"],
                    "qty_per_parent": float(row["qty_per_parent"]),
                    "lead_time_days": int(row["lead_time_days"]),
                    "level_from": int(row["level_from"]),
                    "level_to": int(row["level_to"]),
                }
            )

        demand_records: list[dict] = []

        for _, row in demand_plan.iterrows():
            deploy_date = row["date"]
            cluster_item = row["item_id"]
            requested_servers = float(row["requested_servers"])
            deployment_batch = row["deployment_batch"]
            program_name = row["program_name"]
            priority = float(row["priority"])

            level1_children = [
                child
                for child in bom_children_map.get(cluster_item, [])
                if child["level_to"] == 1
            ]

            if not level1_children:
                raise ValueError(
                    f"No level-1 server mapping found in BOM_MultiLevel for cluster: {cluster_item}"
                )

            template_total_servers = sum(child["qty_per_parent"] for child in level1_children)
            if template_total_servers <= 0:
                raise ValueError(
                    f"Invalid cluster-to-server BOM quantity for cluster: {cluster_item}"
                )

            for server_link in level1_children:
                server_item = server_link["child_item"]
                lead_time_days = server_link["lead_time_days"]

                server_qty = requested_servers * server_link["qty_per_parent"]

                server_required_date = deploy_date - pd.Timedelta(days=lead_time_days)

                self._explode_from_item(
                    current_item=server_item,
                    required_qty=server_qty,
                    required_date=server_required_date,
                    bom_children_map=bom_children_map,
                    records=demand_records,
                    deployment_batch=deployment_batch,
                    program_name=program_name,
                    priority=priority,
                    root_cluster=cluster_item,
                )

        demand_df = pd.DataFrame(demand_records)

        if demand_df.empty:
            return pd.DataFrame(
                columns=[
                    "date",
                    "material",
                    "demand",
                    "deployment_batch",
                    "program_name",
                    "priority",
                    "root_cluster",
                ]
            )

        demand_df = (
            demand_df.groupby(
                ["date", "material", "deployment_batch", "program_name", "priority", "root_cluster"],
                as_index=False,
            )["demand"]
            .sum()
        )

        return demand_df

    def simulate_inventory(
        self,
        demand: pd.DataFrame,
        supply: pd.DataFrame,
        stock: pd.DataFrame,
    ) -> pd.DataFrame:
        demand_agg = (
            demand.groupby(["date", "material"], as_index=False)["demand"].sum()
            if not demand.empty
            else pd.DataFrame(columns=["date", "material", "demand"])
        )

        supply_agg = supply.rename(columns={"item_id": "material", "committed_qty": "supply"})
        stock_agg = stock.rename(columns={"item_id": "material", "opening_qty": "opening_stock"})

        df = demand_agg.merge(supply_agg, on=["date", "material"], how="outer")

        if df.empty:
            all_materials = stock_agg["material"].dropna().unique().tolist()
            if not all_materials:
                return pd.DataFrame(
                    columns=[
                        "date",
                        "material",
                        "opening_inventory",
                        "demand",
                        "supply",
                        "inventory",
                        "shortage",
                        "shortage_flag",
                    ]
                )

        df["demand"] = df["demand"].fillna(0)
        df["supply"] = df["supply"].fillna(0)

        df = df.merge(stock_agg, on="material", how="left")
        df["opening_stock"] = df["opening_stock"].fillna(0)

        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values(["material", "date"]).reset_index(drop=True)

        results = []

        for material, group in df.groupby("material"):
            inventory = float(group["opening_stock"].iloc[0])

            for _, row in group.iterrows():
                opening_inventory = inventory
                inventory = inventory + float(row["supply"]) - float(row["demand"])
                shortage = abs(inventory) if inventory < 0 else 0.0

                results.append(
                    {
                        "date": row["date"],
                        "material": material,
                        "opening_inventory": opening_inventory,
                        "demand": float(row["demand"]),
                        "supply": float(row["supply"]),
                        "inventory": float(inventory),
                        "shortage": float(shortage),
                        "shortage_flag": shortage > 0,
                    }
                )

        return pd.DataFrame(results)

    def build_summary(self, result_df: pd.DataFrame) -> dict:
        shortage_df = result_df[result_df["shortage"] > 0].copy()

        total_materials = int(result_df["material"].nunique()) if not result_df.empty else 0
        shortage_materials = int(shortage_df["material"].nunique()) if not shortage_df.empty else 0
        total_shortage_qty = float(shortage_df["shortage"].sum()) if not shortage_df.empty else 0.0
        earliest_shortage_date = (
            str(shortage_df["date"].min().date()) if not shortage_df.empty else None
        )

        shortage_days = int(shortage_df["date"].count()) if not shortage_df.empty else 0

        worst_shortage_point = None
        if not shortage_df.empty:
            worst_row = shortage_df.sort_values(["shortage", "date"], ascending=[False, True]).iloc[0]
            worst_shortage_point = {
                "material": worst_row["material"],
                "date": str(pd.to_datetime(worst_row["date"]).date()),
                "shortage": float(worst_row["shortage"]),
            }

        return {
            "total_materials": total_materials,
            "shortage_materials": shortage_materials,
            "total_shortage_qty": total_shortage_qty,
            "earliest_shortage_date": earliest_shortage_date,
            "shortage_days": shortage_days,
            "worst_shortage_point": worst_shortage_point,
        }

    def run(self):
        self.validate_input()
        _, demand_plan, bom, supply, stock = self.load_data()
        demand = self.calculate_demand(demand_plan, bom)
        result = self.simulate_inventory(demand, supply, stock)
        summary = self.build_summary(result)
        return result, summary