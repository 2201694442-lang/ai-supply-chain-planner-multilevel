import { useMemo, useRef, useState } from "react";
import axios from "axios";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
} from "recharts";
import "./index.css";
import HeatmapSection from "./components/HeatmapSection";

const API_BASE_URL = "http://127.0.0.1:8000";


function SummaryCard({ title, value, subtitle }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-medium text-slate-500">{title}</p>
      <p className="mt-3 text-3xl font-bold tracking-tight text-slate-900">
        {value ?? "-"}
      </p>
      <p className="mt-1 text-sm text-slate-400">{subtitle}</p>
    </div>
  );
}

function Panel({ title, children }) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
      <div className="mt-4">{children}</div>
    </div>
  );
}

function StatusBanner({ type, message }) {
  if (!message) return null;

  const styles = {
    success: "border-emerald-200 bg-emerald-50 text-emerald-700",
    error: "border-red-200 bg-red-50 text-red-700",
    info: "border-slate-200 bg-slate-50 text-slate-600",
  };

  return (
    <div
      className={`mt-5 rounded-2xl border px-4 py-3 text-sm ${
        styles[type] || styles.info
      }`}
    >
      {message}
    </div>
  );
}

function InventoryChart({ rows, analyzed }) {
  if (!analyzed) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-sm text-slate-500">
        No chart available before analysis.
      </div>
    );
  }

  if (!rows || rows.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-sm text-slate-500">
        No inventory trajectory available.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <ReferenceLine y={0} stroke="#ef4444" strokeDasharray="4 4" />
            <Line
              type="monotone"
              dataKey="inventory"
              strokeWidth={2}
              dot={{ r: 3 }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function DemandSupplyChart({ rows, analyzed }) {
  if (!analyzed) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-sm text-slate-500">
        No demand vs supply chart available before analysis.
      </div>
    );
  }

  if (!rows || rows.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-sm text-slate-500">
        No demand and supply data available.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-3">
        <p className="text-sm text-slate-500">
          Compare daily material demand against planned supply for the selected
          material.
        </p>
      </div>

      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="demand" name="Demand Qty" fill="#0f172a" />
            <Bar dataKey="supply" name="Supply Qty" fill="#2563eb" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function ResultTable({ rows, analyzed }) {
  if (!analyzed) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-sm text-slate-500">
        No analysis has been run yet.
      </div>
    );
  }

  if (!rows || rows.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-emerald-200 bg-emerald-50 p-6 text-sm text-emerald-700">
        No shortage detected in the uploaded planning horizon.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
      <table className="min-w-full text-sm">
        <thead className="bg-slate-50 text-left text-slate-600">
          <tr>
            <th className="px-4 py-3 font-semibold">Date</th>
            <th className="px-4 py-3 font-semibold">Material</th>
            <th className="px-4 py-3 font-semibold">Opening</th>
            <th className="px-4 py-3 font-semibold">Demand</th>
            <th className="px-4 py-3 font-semibold">Supply</th>
            <th className="px-4 py-3 font-semibold">Ending</th>
            <th className="px-4 py-3 font-semibold">Shortage</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index} className="border-t border-slate-100">
              <td className="px-4 py-3 text-slate-700">{row.date}</td>
              <td className="px-4 py-3 font-medium text-slate-900">
                {row.material}
              </td>
              <td className="px-4 py-3 text-slate-700">
                {row.opening_inventory}
              </td>
              <td className="px-4 py-3 text-slate-700">{row.demand}</td>
              <td className="px-4 py-3 text-slate-700">{row.supply}</td>
              <td className="px-4 py-3 text-slate-700">{row.inventory}</td>
              <td className="px-4 py-3">
                <span className="rounded-full bg-red-100 px-2.5 py-1 text-xs font-semibold text-red-700">
                  {row.shortage}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function App() {
  const fileInputRef = useRef(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedMaterial, setSelectedMaterial] = useState("");
  const [loading, setLoading] = useState(false);
  const [analyzed, setAnalyzed] = useState(false);
  const [selectedHeatmapCell, setSelectedHeatmapCell] = useState(null);

  const [summary, setSummary] = useState({
    total_materials: 0,
    shortage_materials: 0,
    total_shortage_qty: 0,
    earliest_shortage_date: null,
  });

  const [allRows, setAllRows] = useState([]);
  const [resultRows, setResultRows] = useState([]);
  const [heatmapData, setHeatmapData] = useState(null);

  const [status, setStatus] = useState({
    type: "info",
    message: "Analysis ready. Demo file is available for simulation.",
  });

  const handleHeatmapCellClick = (cell) => {
      setSelectedHeatmapCell((prev) => {
        const isSame =
          prev &&
          prev.material === cell.material &&
          prev.date === cell.date;

        if (isSame) {
          setSelectedMaterial("");
          return null;
        }

        setSelectedMaterial(cell.material);
        return cell;
      });
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setStatus({
        type: "success",
        message: `Selected file: ${file.name}`,
      });
    }
  };

  const applyResponseData = (responseData, successMessage) => {
    const rows = responseData.results || [];
    const shortageOnly = rows.filter((item) => Number(item.shortage) > 0);

    setSummary(responseData.summary || {});
    setAllRows(rows);
    setResultRows(shortageOnly);
    setHeatmapData(responseData.heatmap || null);
    setAnalyzed(true);
    setSelectedHeatmapCell(null);

    const defaultMaterial = shortageOnly[0]?.material || rows[0]?.material || "";
    setSelectedMaterial(defaultMaterial);

    setStatus({
      type: "success",
      message: successMessage,
    });
  };


  const resetAnalysisState = (message) => {
    setAnalyzed(false);
    setAllRows([]);
    setResultRows([]);
    setHeatmapData(null);
    setSelectedMaterial("");
    setSelectedHeatmapCell(null);
    setSummary({
      total_materials: 0,
      shortage_materials: 0,
      total_shortage_qty: 0,
      earliest_shortage_date: null,
    });
    setStatus({
      type: "error",
      message,
    });
  };

  const handleStartAnalysis = async () => {
    if (!selectedFile) {
      setStatus({
        type: "error",
        message: "Please upload an Excel file first.",
      });
      return;
    }

    try {
      setLoading(true);
      setAnalyzed(false);
      setStatus({
        type: "info",
        message: "Analyzing uploaded file...",
      });

      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await axios.post(
        `${API_BASE_URL}/analyze-upload`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      const shortageOnly = (response.data.results || []).filter(
        (item) => Number(item.shortage) > 0
      );

      applyResponseData(
        response.data,
        shortageOnly.length > 0
          ? "Analysis completed. Shortage records found."
          : "Analysis completed. No shortage detected."
      );
    } catch (error) {
      console.error("Analysis failed:", error);
      const detail =
        error?.response?.data?.detail ||
        "Analysis failed. Please check your file format.";
      resetAnalysisState(detail);
    } finally {
      setLoading(false);
    }
  };

  const handleRunDemo = async () => {
    try {
      setLoading(true);
      setAnalyzed(false);
      setStatus({
        type: "info",
        message: "Running demo analysis...",
      });

      const response = await axios.post(`${API_BASE_URL}/analyze-demo`);

      const shortageOnly = (response.data.results || []).filter(
        (item) => Number(item.shortage) > 0
      );

      applyResponseData(
        response.data,
        shortageOnly.length > 0
          ? "Demo analysis completed. Shortage records found."
          : "Demo analysis completed. No shortage detected."
      );
    } catch (error) {
      console.error("Demo analysis failed:", error);
      const detail =
        error?.response?.data?.detail || "Demo analysis failed.";
      resetAnalysisState(detail);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadTable = () => {
    window.open(`${API_BASE_URL}/download-inventory`, "_blank");
  };

  const materialList = useMemo(() => {
    if (!allRows || allRows.length === 0) return [];
    return Array.from(new Set(allRows.map((row) => row.material)));
  }, [allRows]);

  const chartRows = useMemo(() => {
    if (!allRows || allRows.length === 0) return [];
    if (!selectedMaterial) return [];

    return allRows
      .filter((row) => row.material === selectedMaterial)
      .map((row) => ({
        date: row.date,
        inventory: Number(row.inventory),
      }));
  }, [allRows, selectedMaterial]);

  const demandSupplyRows = useMemo(() => {
    if (!allRows || allRows.length === 0) return [];
    if (!selectedMaterial) return [];

    return allRows
      .filter((row) => row.material === selectedMaterial)
      .map((row) => ({
        date: row.date,
        demand: Number(row.demand),
        supply: Number(row.supply),
      }));
  }, [allRows, selectedMaterial]);

  const displayedResultRows = useMemo(() => {
      if (!selectedHeatmapCell) return resultRows;

      return resultRows.filter(
        (row) =>
          row.material === selectedHeatmapCell.material &&
          row.date === selectedHeatmapCell.date
      );
  }, [resultRows, selectedHeatmapCell]);

  return (
    <div className="min-h-screen overflow-y-auto bg-slate-50">
      <div className="mx-auto max-w-[1400px] px-6 py-14">
        <header className="mb-8">
          <h1 className="text-5xl font-bold tracking-tight text-slate-950">
            Material Shortage Analyzer
          </h1>
          <p className="mt-3 max-w-3xl text-lg text-slate-500">
            Upload planning files, simulate rolling inventory, and identify
            shortage risks.
          </p>
        </header>

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
          <div className="xl:col-span-2">
            <Panel title="File Upload">
              <div className="rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50 px-6 py-14 text-center">
                <p className="text-base font-medium text-slate-700">
                  Drag and drop your Excel planning file here
                </p>
                <p className="mt-2 text-sm text-slate-400">
                  Supported format: .xlsx
                </p>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx"
                className="hidden"
                onChange={handleFileChange}
              />

              <div className="mt-5 flex flex-col gap-3 sm:flex-row">
                <button
                  onClick={handleUploadClick}
                  className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
                >
                  Upload File
                </button>

                <button
                  onClick={handleStartAnalysis}
                  disabled={loading}
                  className="rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-60"
                >
                  {loading ? "Analyzing..." : "Start Analysis"}
                </button>

                <button
                  onClick={handleRunDemo}
                  disabled={loading}
                  className="rounded-xl border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-60"
                >
                  Run Demo
                </button>
              </div>

              <StatusBanner type={status.type} message={status.message} />
            </Panel>
          </div>

          <div className="space-y-6">
            <Panel title="Uploaded Files">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-slate-800">
                      {selectedFile ? selectedFile.name : "sample_input.xlsx"}
                    </p>
                    <p className="mt-1 text-xs text-slate-400">
                      {selectedFile
                        ? "Selected and ready for analysis"
                        : "2026-03-16 · Ready for analysis"}
                    </p>
                  </div>
                  <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-xs font-medium text-emerald-700">
                    Ready
                  </span>
                </div>
              </div>
            </Panel>

            <Panel title="Quick Guide">
              <ol className="space-y-3 text-sm text-slate-500">
                <li>1. Upload an Excel file with planning sheets.</li>
                <li>2. Start analysis to run shortage simulation.</li>
                <li>3. Or click Run Demo to test the built-in sample.</li>
              </ol>
            </Panel>
          </div>
        </div>

        <section className="mt-8">
          <h2 className="mb-4 text-xl font-semibold text-slate-900">
            Analysis Summary
          </h2>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
            <SummaryCard
              title="Total Materials"
              value={summary.total_materials}
              subtitle="materials in scope"
            />
            <SummaryCard
              title="Shortage Materials"
              value={summary.shortage_materials}
              subtitle="materials at risk"
            />
            <SummaryCard
              title="Total Shortage Qty"
              value={summary.total_shortage_qty}
              subtitle="units missing"
            />
            <SummaryCard
              title="Earliest Shortage Date"
              value={summary.earliest_shortage_date || "-"}
              subtitle="first risk date"
            />
          </div>
        </section>

      {analyzed && heatmapData && (
      <HeatmapSection
          heatmap={heatmapData}
          selectedCell={selectedHeatmapCell}
          onCellClick={handleHeatmapCellClick}
      />
    )}

        <section className="mt-8">
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="text-xl font-semibold text-slate-900">
              Inventory Trajectory
            </h2>

            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-500">Material:</span>
              <select
                value={selectedMaterial}
                onChange={(e) => setSelectedMaterial(e.target.value)}
                className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700"
              >
                {materialList.length === 0 ? (
                  <option value="">No material</option>
                ) : (
                  materialList.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))
                )}
              </select>
            </div>
          </div>

          <InventoryChart rows={chartRows} analyzed={analyzed} />
        </section>

        <section className="mt-8">
          <h2 className="mb-4 text-xl font-semibold text-slate-900">
            Demand vs Supply
          </h2>
          <DemandSupplyChart rows={demandSupplyRows} analyzed={analyzed} />
        </section>

        <section className="mt-8 pb-10">
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-xl font-semibold text-slate-900">
                Shortage Detail
              </h2>
              {selectedHeatmapCell && (
                <p className="mt-1 text-sm text-slate-500">
                  Showing records for {selectedHeatmapCell.material} on{" "}
                  {selectedHeatmapCell.date}
                </p>
              )}
            </div>

            <div className="flex items-center gap-3">
              {selectedHeatmapCell && (
                <button
                  onClick={() => {
                    setSelectedHeatmapCell(null);
                  }}
                  className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                >
                  Clear Selection
                </button>
              )}

              <button
                onClick={handleDownloadTable}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
              >
                ⬇️ Download Table
              </button>
            </div>
          </div>

          <ResultTable rows={displayedResultRows} analyzed={analyzed} />
        </section>
      </div>
    </div>
  );
}

export default App;