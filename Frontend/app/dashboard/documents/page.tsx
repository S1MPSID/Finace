"use client";

import { useRef, useState } from "react";
import { FileText, Download, Edit3, Loader2, Upload, CheckCircle2, AlertTriangle } from "lucide-react";
import { docsApi, uploadApi, PdfUploadResponse } from "@/services/api";

export default function DocumentsPage() {
  const [activeTab, setActiveTab] = useState("Privacy Policy");
  const [productDetails, setProductDetails] = useState("");
  const [generating, setGenerating] = useState(false);
  
  // Cleaned: No mock data here. Empty object initially.
  const [docs, setDocs] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);

  // OCR upload state
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [ingestEnabled, setIngestEnabled] = useState(false);
  const [uploadResult, setUploadResult] = useState<PdfUploadResponse | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const documentTypes = ["Privacy Policy", "Terms of Service", "AML Addendum"];

  const handleFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadError(null);
    setUploadResult(null);

    try {
      const result = await uploadApi.uploadPdf(file, ingestEnabled);
      setUploadResult(result);
    } catch (err: any) {
      console.error(err);
      setUploadError(err?.message || "PDF upload failed. Is the RAG service running?");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setGenerating(true);
    setError(null);
    
    try {
      // Calls the centralized API layer
      const response: any = await docsApi.generate({
        type: activeTab,
        details: productDetails
      });
      
      if (response && response.content) {
        setDocs(prev => ({
          ...prev,
          [activeTab]: response.content
        }));
        setProductDetails("");
      } else {
        throw new Error("No content received from server.");
      }
    } catch (err: any) {
      console.error(err);
      setError("Document Generation API is not available yet. Please connect the backend module.");
    } finally {
      setGenerating(false);
    }
  };

  const exportPDF = () => {
    if (!docs[activeTab]) return;
    alert(`Exporting ${activeTab} as PDF...`);
  };

  return (
    <div className="space-y-6">
      <div className="glass rounded-[1.8rem] p-6">
        <p className="text-sm text-accent flex items-center gap-2"><Upload className="w-4 h-4"/> Document OCR</p>
        <h2 className="mt-3 text-3xl font-semibold text-white">Upload a PDF & Extract its Content</h2>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-white/65">
          Drop in a scanned or digital PDF. Finace parses it (with OCR fallback for scanned documents)
          and recognises the text so you can review it or search it via the RAG engine.
        </p>
      </div>

      <div className="glass rounded-[1.8rem] p-6">
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf,.pdf"
          className="hidden"
          onChange={handleFileSelected}
        />
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="rounded-xl bg-accent px-5 py-2.5 text-sm font-semibold text-ink hover:bg-accent/90 transition flex items-center gap-2 disabled:opacity-50"
          >
            {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
            {uploading ? "Processing PDF…" : "Choose PDF to upload"}
          </button>

          <label className="flex items-center gap-2 text-sm text-white/70 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={ingestEnabled}
              onChange={(e) => setIngestEnabled(e.target.checked)}
              className="accent-[#4ade80] w-4 h-4"
            />
            Add to RAG search index (embeds & chunks the text)
          </label>
        </div>

        {uploadError && (
          <div className="mt-4 flex items-start gap-2 text-sm text-rose-400 rounded-xl border border-rose-400/30 bg-rose-950/30 px-4 py-3">
            <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
            <span>{uploadError}</span>
          </div>
        )}

        {uploadResult && (
          <div className="mt-5 rounded-[1.4rem] border border-white/10 bg-black/20 p-5 space-y-4">
            <div className="flex items-center gap-3">
              <CheckCircle2 className={`w-6 h-6 ${uploadResult.extraction_status === "success" ? "text-emerald-400" : "text-amber-400"}`} />
              <div>
                <p className="text-sm font-semibold text-white">{uploadResult.filename}</p>
                <p className="text-xs text-white/50">
                  Extraction: <span className="uppercase text-white/70">{uploadResult.method}</span>
                  {" · "}{uploadResult.page_count} pages · {uploadResult.char_count.toLocaleString()} characters
                </p>
              </div>
            </div>

            {uploadResult.warnings && uploadResult.warnings.length > 0 && (
              <div className="text-xs text-amber-400/90 space-y-1">
                {uploadResult.warnings.map((w, i) => (
                  <p key={i}>• {w}</p>
                ))}
              </div>
            )}

            {uploadResult.ingest && (
              <div className="text-xs text-emerald-400/90">
                Indexed — {uploadResult.ingest.chunks_created} chunks created, {uploadResult.ingest.embedded} embedded
                (<span className="font-mono">{uploadResult.ingest.regulation_id}</span>). You can now ask about it via Workflow / RAG chat.
              </div>
            )}

            {uploadResult.text ? (
              <div>
                <p className="mb-2 text-xs uppercase tracking-[0.18em] text-white/45">Recognised text preview</p>
                <pre className="max-h-64 overflow-y-auto whitespace-pre-wrap rounded-[1rem] border border-white/8 bg-black/20 p-4 text-xs leading-6 text-white/75 font-mono">
                  {uploadResult.text.length > 4000 ? `${uploadResult.text.slice(0, 4000)}…` : uploadResult.text}
                </pre>
              </div>
            ) : (
              <p className="text-xs text-rose-400/90">
                No text could be recognised. If this is a scanned PDF, make sure Tesseract OCR is installed and on PATH.
              </p>
            )}
          </div>
        )}
      </div>

      <div className="glass rounded-[1.8rem] p-6">
        <p className="text-sm text-accent flex items-center gap-2"><FileText className="w-4 h-4"/> Legal Document Generator</p>
        <h2 className="mt-3 text-3xl font-semibold text-white">Draft & Export Compliance Policies</h2>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-white/65">
          Input your product specifics to dynamically generate tailored legal documents from the API.
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
        <div className="space-y-6">
          <div className="glass rounded-[1.8rem] p-6">
            <p className="text-xs uppercase tracking-[0.18em] text-white/45 mb-4">Document Type</p>
            <div className="flex flex-col gap-2">
              {documentTypes.map((item) => (
                <button 
                  key={item} 
                  onClick={() => setActiveTab(item)}
                  className={`text-left rounded-[1.3rem] border p-4 transition-all ${
                    activeTab === item 
                      ? "border-accent/40 bg-accent/10" 
                      : "border-white/8 bg-white/[0.03] hover:border-white/20"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <h3 className={`text-sm font-semibold ${activeTab === item ? "text-accent" : "text-white"}`}>{item}</h3>
                    {docs[item] && <span className="w-2 h-2 rounded-full bg-emerald-400"></span>}
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="glass rounded-[1.8rem] p-6">
            <p className="text-xs uppercase tracking-[0.18em] text-white/45 mb-4">Generate Context</p>
            <form onSubmit={handleGenerate} className="space-y-4">
              <textarea
                value={productDetails}
                onChange={(e) => setProductDetails(e.target.value)}
                required
                className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-accent/50 transition min-h-[120px]"
                placeholder="Enter specific product features to include in the policy..."
              />
              {error && <p className="text-xs text-rose-400">{error}</p>}
              <button 
                type="submit" 
                disabled={generating || !productDetails}
                className="w-full rounded-xl bg-white/10 px-4 py-2 text-sm font-semibold text-white hover:bg-white/20 transition disabled:opacity-50 flex justify-center items-center gap-2"
              >
                {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Generate via API"}
              </button>
            </form>
          </div>
        </div>

        <div className="rounded-[1.8rem] border border-white/10 bg-gradient-to-br from-[#0f1917] to-[#0a0f10] p-6 flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-white/45">Editor</p>
              <h3 className="mt-2 text-2xl font-semibold text-white">{activeTab}</h3>
            </div>
            <div className="flex gap-2">
              <button 
                onClick={() => setEditing(!editing)}
                disabled={!docs[activeTab]}
                className="rounded-full bg-white/10 px-4 py-2 text-sm font-semibold text-white hover:bg-white/20 transition flex items-center gap-2 disabled:opacity-30"
              >
                <Edit3 className="w-4 h-4"/> {editing ? "Save" : "Edit"}
              </button>
              <button 
                onClick={exportPDF}
                disabled={!docs[activeTab]}
                className="rounded-full bg-accent px-4 py-2 text-sm font-semibold text-ink hover:bg-accent/90 transition flex items-center gap-2 disabled:opacity-30"
              >
                <Download className="w-4 h-4"/> Export PDF
              </button>
            </div>
          </div>

          <div className="flex-1 rounded-[1.5rem] border border-white/8 bg-black/20 p-5 overflow-hidden flex flex-col min-h-[400px]">
            {!docs[activeTab] ? (
              <div className="w-full h-full flex flex-col items-center justify-center text-center opacity-50">
                <FileText className="w-12 h-12 mb-4 text-white/20" />
                <p>No document generated yet.</p>
                <p className="text-sm mt-2 max-w-xs">Enter product context and click generate to invoke the backend API.</p>
              </div>
            ) : editing ? (
              <textarea 
                className="w-full h-full bg-transparent text-sm leading-8 text-white/80 focus:outline-none resize-none"
                value={docs[activeTab]}
                onChange={(e) => setDocs({...docs, [activeTab]: e.target.value})}
              />
            ) : (
              <div className="w-full h-full text-sm leading-8 text-white/80 whitespace-pre-wrap overflow-y-auto">
                {docs[activeTab]}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
