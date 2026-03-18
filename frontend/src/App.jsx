import { useRef, useState } from "react";
import "./index.css";

function SummaryCard({ title, value, subtitle }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-sm font-medium text-slate-500">{title}</p>
      <p className="mt-3 text-3xl font-bold tracking-tight text-slate-900">{value}</p>
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

function App() {
  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-7xl px-6 py-10">
        <header className="mb-8">
          <h1 className="text-5xl font-bold tracking-tight text-slate-950">
            Material Shortage Analyzer
          </h1>
          <p className="mt-3 max-w-3xl text-lg text-slate-500">
            Upload planning files, simulate rolling inventory, and identify shortage risks.
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

                <button className="rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800">
                  Start Analysis
                </button>
              </div>

              <div className="mt-5 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                {selectedFile
                  ? `Selected file: ${selectedFile.name}`
                  : "Analysis ready. Demo file is available for simulation."}
              </div>
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
                <li>3. Review summary metrics and shortage details.</li>
              </ol>
            </Panel>
          </div>
        </div>

        <section className="mt-8">
          <h2 className="mb-4 text-xl font-semibold text-slate-900">
            Analysis Summary
          </h2>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            <SummaryCard
              title="Total Materials"
              value="120"
              subtitle="materials in scope"
            />
            <SummaryCard
              title="Shortage Materials"
              value="18"
              subtitle="at risk"
            />
            <SummaryCard
              title="Total Shortage Qty"
              value="3200"
              subtitle="units missing"
            />
          </div>
        </section>
      </div>
    </div>
  );
}

export default App;