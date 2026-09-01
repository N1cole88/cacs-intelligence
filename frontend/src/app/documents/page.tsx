"use client";
import { useState, useRef } from "react";
import { Upload, FileText, CheckCircle, XCircle, Loader2 } from "lucide-react";
import { uploadDocument } from "@/lib/api";
import type { Document } from "@/types";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const doc = await uploadDocument(file);
      setDocuments((prev) => [{ id: doc.id, title: doc.title, file_path: "", file_size: file.size, status: "pending", error_message: null, uploaded_at: new Date().toISOString(), processed_at: null }, ...prev]);
    } catch { alert("Failed to upload document"); }
    finally { setUploading(false); if (fileInputRef.current) fileInputRef.current.value = ""; }
  };

  const getStatusIcon = (status: string) => {
    switch (status) { case "completed": return <CheckCircle className="w-5 h-5 text-green-600" />; case "failed": return <XCircle className="w-5 h-5 text-red-600" />; default: return <Loader2 className="w-5 h-5 text-yellow-600 animate-spin" />; }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-4 py-4">
        <div className="max-w-4xl mx-auto"><h1 className="text-xl font-bold">Documents</h1><p className="text-sm text-gray-600">Upload your CACS study materials</p></div>
      </header>
      <main className="max-w-4xl mx-auto p-4">
        <div className="bg-white rounded-lg border p-6 mb-6">
          <label className="flex flex-col items-center justify-center cursor-pointer">
            <Upload className="w-10 h-10 text-gray-400 mb-2" />
            <span className="text-gray-600">{uploading ? "Uploading..." : "Click to upload PDF"}</span>
            <span className="text-sm text-gray-400">PDF files only</span>
            <input ref={fileInputRef} type="file" accept=".pdf" onChange={handleUpload} disabled={uploading} className="hidden" />
          </label>
        </div>
        <div className="bg-white rounded-lg border">
          <div className="px-6 py-4 border-b"><h2 className="font-semibold">Your Documents</h2></div>
          {documents.length === 0 ? <div className="p-6 text-center text-gray-500">No documents uploaded yet</div> : (
            <div className="divide-y">
              {documents.map((doc) => (
                <div key={doc.id} className="px-6 py-4 flex items-center gap-4">
                  <FileText className="w-8 h-8 text-gray-400" />
                  <div className="flex-1"><p className="font-medium">{doc.title}</p><p className="text-sm text-gray-500">{new Date(doc.uploaded_at).toLocaleDateString()}</p></div>
                  {getStatusIcon(doc.status)}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
