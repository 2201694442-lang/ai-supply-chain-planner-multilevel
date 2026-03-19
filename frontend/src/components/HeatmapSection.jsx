import { useMemo, useRef, useState } from "react";

/** 颜色映射 */
function getColor(value) {
  if (!value || value <= 0) return "#f1f5f9";
  if (value < 50) return "#fecaca";
  if (value < 150) return "#f87171";
  if (value < 300) return "#ef4444";
  return "#b91c1c";
}

export default function HeatmapSection({
  heatmap,
  selectedCell,
  onCellClick,
}) {
  const containerRef = useRef(null);

  const [tooltip, setTooltip] = useState({
    visible: false,
    x: 0,
    y: 0,
    data: null,
    placement: "top",
  });

  const rows = heatmap?.rows || [];
  const dates = heatmap?.dates || [];

  /** 动态布局参数 */
  const layout = {
    cellHeight: 56,
    labelColWidth: 140,
  };

  /** 过滤+排序 */
  const displayRows = useMemo(() => {
    return rows
      .filter((row) =>
        row.cells.some((cell) => Number(cell.shortage_qty || 0) > 0)
      )
      .sort((a, b) => {
        const aMax = Math.max(
          ...a.cells.map((c) => Number(c.shortage_qty || 0))
        );
        const bMax = Math.max(
          ...b.cells.map((c) => Number(c.shortage_qty || 0))
        );
        return bMax - aMax;
      });
  }, [rows]);

  /** tooltip */
  const showTooltip = (event, data) => {
    if (!containerRef.current) return;

    const containerRect =
      containerRef.current.getBoundingClientRect();
    const cellRect = event.currentTarget.getBoundingClientRect();

    const x = cellRect.left - containerRect.left + cellRect.width / 2;
    const y = cellRect.top - containerRect.top;

    const placement = y < 120 ? "bottom" : "top";

    setTooltip({
      visible: true,
      x,
      y,
      data,
      placement,
    });
  };

  const hideTooltip = () => {
    setTooltip((prev) => ({ ...prev, visible: false }));
  };

  if (!heatmap || rows.length === 0) return null;

  return (
    <div className="mt-12 rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
      {/* 标题 */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-slate-900">
          Heatmap Analysis
        </h2>
        <p className="text-sm text-slate-500">
          Identify shortage concentration across materials and dates
        </p>
      </div>

      {displayRows.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-6 text-sm text-slate-500">
          No shortage pattern detected.
        </div>
      ) : (
        <>
          {/* ✅ 核心结构（解决裁切问题） */}
          <div className="relative rounded-xl border border-slate-100">
            <div
              ref={containerRef}
              className="overflow-auto px-4"
              style={{ maxHeight: "560px" }}
            >
              <div
                className="grid items-center gap-y-2 text-xs w-full"
                style={{
                  gridTemplateColumns: `${layout.labelColWidth}px repeat(${dates.length}, minmax(130px, 1fr))`,
                  minWidth: `${
                    layout.labelColWidth + dates.length * 130
                  }px`,
                }}
              >
                {/* 左上角占位 */}
                <div className="sticky top-0 left-0 z-30 bg-white"></div>

                {/* 日期 */}
                {dates.map((date) => (
                  <div
                    key={date}
                    className="sticky top-0 z-20 bg-white py-3 text-center text-sm font-medium text-slate-500"
                  >
                    {date.slice(5)}
                  </div>
                ))}

                {/* 行 */}
                {displayRows.map((row) => (
                  <HeatmapRow
                    key={row.material}
                    row={row}
                    dates={dates}
                    selectedCell={selectedCell}
                    onCellClick={onCellClick}
                    onShowTooltip={showTooltip}
                    onHideTooltip={hideTooltip}
                    layout={layout}
                  />
                ))}
              </div>
            </div>

            {/* ✅ tooltip 放外层（关键修复） */}
            {tooltip.visible && tooltip.data && (
              <div
                className="pointer-events-none absolute z-40 w-64 -translate-x-1/2 rounded-2xl border border-slate-200 bg-white p-3 shadow-xl"
                style={{
                  left: tooltip.x,
                  top: tooltip.y,
                  transform:
                    tooltip.placement === "top"
                      ? "translate(-50%, -100%)"
                      : "translate(-50%, 0)",
                }}
              >
                <div className="mb-2 border-b border-slate-100 pb-2">
                  <div className="text-sm font-semibold text-slate-900">
                    {tooltip.data.material}
                  </div>
                  <div className="text-xs text-slate-500">
                    {tooltip.data.date}
                  </div>
                </div>

                <div className="space-y-1 text-sm">
                  <MetricRow
                    label="Shortage"
                    value={tooltip.data.shortage_qty}
                    valueClassName="text-red-600"
                  />
                  <MetricRow
                    label="Inventory"
                    value={tooltip.data.inventory}
                  />
                  <MetricRow
                    label="Demand"
                    value={tooltip.data.demand}
                  />
                  <MetricRow
                    label="Supply"
                    value={tooltip.data.supply}
                  />
                </div>
              </div>
            )}
          </div>

          {/* legend */}
          <div className="mt-6 flex flex-wrap items-center gap-4 text-xs text-slate-600">
            <span className="font-medium">Severity:</span>
            <LegendItem color="#f1f5f9" label="None" />
            <LegendItem color="#fecaca" label="Low" />
            <LegendItem color="#f87171" label="Medium" />
            <LegendItem color="#ef4444" label="High" />
            <LegendItem color="#b91c1c" label="Critical" />
          </div>
        </>
      )}
    </div>
  );
}

/** 行 */
function HeatmapRow({
  row,
  dates,
  selectedCell,
  onCellClick,
  onShowTooltip,
  onHideTooltip,
  layout,
}) {
  return (
    <>
      <div
        className="pr-3 text-sm font-medium text-slate-700 sticky left-0 bg-white z-10"
        style={{ height: layout.cellHeight }}
      >
        {row.material}
      </div>

      {row.cells.map((cell, index) => {
        const date = dates[index];
        const shortageQty = Number(cell.shortage_qty || 0);

        const isSelected =
          selectedCell &&
          selectedCell.material === row.material &&
          selectedCell.date === date;

        return (
          <button
            key={`${row.material}-${date}`}
            onClick={() =>
              onCellClick?.({
                material: row.material,
                date,
                shortage_qty: shortageQty,
                inventory: Number(cell.inventory || 0),
                demand: Number(cell.demand || 0),
                supply: Number(cell.supply || 0),
              })
            }
            onMouseEnter={(e) =>
              onShowTooltip(e, {
                material: row.material,
                date,
                ...cell,
              })
            }
            onMouseLeave={onHideTooltip}
            className={`border border-white transition hover:opacity-90 ${
              isSelected ? "ring-2 ring-slate-900" : ""
            }`}
            style={{
              height: layout.cellHeight,
              minWidth: 130,
              backgroundColor: getColor(shortageQty),
            }}
          />
        );
      })}
    </>
  );
}

/** tooltip row */
function MetricRow({ label, value, valueClassName = "" }) {
  return (
    <div className="flex justify-between">
      <span className="text-slate-500">{label}</span>
      <span className={`font-medium ${valueClassName}`}>
        {value}
      </span>
    </div>
  );
}

/** legend */
function LegendItem({ color, label }) {
  return (
    <div className="flex items-center gap-2">
      <div
        className="h-4 w-4 rounded-sm border border-slate-200"
        style={{ backgroundColor: color }}
      />
      <span>{label}</span>
    </div>
  );
}