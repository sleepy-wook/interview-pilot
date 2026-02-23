"use client";

import { useState, useEffect, useRef } from "react";
import type { StartRequest, CompanyRoleOption } from "@/lib/types";
import { uploadFile, getCompanyRoles } from "@/lib/api";

interface Props {
  onStart: (data: StartRequest) => void;
  loading: boolean;
}

export default function SetupForm({ onStart, loading }: Props) {
  const [companyRoles, setCompanyRoles] = useState<CompanyRoleOption[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [mode, setMode] = useState<"practice" | "real">("practice");
  const [model, setModel] = useState<"haiku" | "sonnet">("haiku");

  // File states
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [linkedinFile, setLinkedinFile] = useState<File | null>(null);
  const [linkedinUrl, setLinkedinUrl] = useState("");
  const [linkedinMode, setLinkedinMode] = useState<"pdf" | "url">("pdf");
  const [uploading, setUploading] = useState(false);

  const resumeInputRef = useRef<HTMLInputElement>(null);
  const linkedinInputRef = useRef<HTMLInputElement>(null);

  // Load company-role options on mount
  useEffect(() => {
    getCompanyRoles()
      .then((res) => {
        setCompanyRoles(res.company_roles);
        if (res.company_roles.length > 0) {
          setSelectedId(res.company_roles[0].id);
        }
      })
      .catch(() => setCompanyRoles([]));
  }, []);

  const selected = companyRoles.find((cr) => cr.id === selectedId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selected) return;

    setUploading(true);
    try {
      let resumePath: string | undefined;
      let linkedinPath: string | undefined;

      // Upload resume if selected
      if (resumeFile) {
        const res = await uploadFile(resumeFile);
        resumePath = res.path;
      }

      // Upload LinkedIn PDF if selected
      if (linkedinMode === "pdf" && linkedinFile) {
        const res = await uploadFile(linkedinFile);
        linkedinPath = res.path;
      }

      onStart({
        company: selected.company,
        role: selected.role,
        mode,
        model,
        resume_path: resumePath,
        linkedin_path: linkedinPath,
        linkedin_url:
          linkedinMode === "url" && linkedinUrl.trim()
            ? linkedinUrl.trim()
            : undefined,
      });
    } catch (err) {
      console.error("Upload failed:", err);
      alert("File upload failed. Please try again.");
      setUploading(false);
    }
  };

  const isLoading = loading || uploading;

  // Derive unique companies and roles for the selected company
  const companies = [...new Set(companyRoles.map((cr) => cr.company))];
  const selectedCompany = selected?.company || "";
  const rolesForCompany = companyRoles.filter(
    (cr) => cr.company === selectedCompany
  );

  const handleCompanyChange = (company: string) => {
    const first = companyRoles.find((cr) => cr.company === company);
    if (first) setSelectedId(first.id);
  };

  const handleRoleChange = (role: string) => {
    const match = companyRoles.find(
      (cr) => cr.company === selectedCompany && cr.role === role
    );
    if (match) setSelectedId(match.id);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Interview Pilot
          </h1>
          <p className="text-gray-500">
            AI-powered mock interview with multi-agent orchestration
          </p>
        </div>

        {/* Form */}
        <form
          onSubmit={handleSubmit}
          className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm space-y-5"
        >
          {/* Company */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Company
            </label>
            <select
              value={selectedCompany}
              onChange={(e) => handleCompanyChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 bg-white"
              disabled={isLoading || companies.length === 0}
            >
              {companies.length === 0 && (
                <option value="">Loading...</option>
              )}
              {companies.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* Role */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Role
            </label>
            <select
              value={selected?.role || ""}
              onChange={(e) => handleRoleChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 bg-white"
              disabled={isLoading || rolesForCompany.length === 0}
            >
              {rolesForCompany.map((cr) => (
                <option key={cr.id} value={cr.role}>
                  {cr.role}
                </option>
              ))}
            </select>
          </div>

          {/* Resume upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Resume{" "}
              <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <input
              ref={resumeInputRef}
              type="file"
              accept=".pdf"
              onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
              className="hidden"
              disabled={isLoading}
            />
            <button
              type="button"
              onClick={() => resumeInputRef.current?.click()}
              className={`w-full px-3 py-2 border rounded-lg text-sm text-left transition-colors ${
                resumeFile
                  ? "border-blue-300 bg-blue-50 text-blue-700"
                  : "border-gray-300 bg-white text-gray-500 hover:bg-gray-50"
              }`}
              disabled={isLoading}
            >
              {resumeFile ? resumeFile.name : "Upload PDF"}
            </button>
          </div>

          {/* LinkedIn */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm font-medium text-gray-700">
                LinkedIn{" "}
                <span className="text-gray-400 font-normal">(optional)</span>
              </label>
              <div className="flex bg-gray-100 rounded p-0.5 text-xs">
                <button
                  type="button"
                  onClick={() => setLinkedinMode("pdf")}
                  className={`px-2 py-0.5 rounded transition-colors ${
                    linkedinMode === "pdf"
                      ? "bg-white text-gray-900 shadow-sm"
                      : "text-gray-500"
                  }`}
                >
                  PDF
                </button>
                <button
                  type="button"
                  onClick={() => setLinkedinMode("url")}
                  className={`px-2 py-0.5 rounded transition-colors ${
                    linkedinMode === "url"
                      ? "bg-white text-gray-900 shadow-sm"
                      : "text-gray-500"
                  }`}
                >
                  URL
                </button>
              </div>
            </div>

            {linkedinMode === "pdf" ? (
              <>
                <input
                  ref={linkedinInputRef}
                  type="file"
                  accept=".pdf"
                  onChange={(e) =>
                    setLinkedinFile(e.target.files?.[0] || null)
                  }
                  className="hidden"
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => linkedinInputRef.current?.click()}
                  className={`w-full px-3 py-2 border rounded-lg text-sm text-left transition-colors ${
                    linkedinFile
                      ? "border-blue-300 bg-blue-50 text-blue-700"
                      : "border-gray-300 bg-white text-gray-500 hover:bg-gray-50"
                  }`}
                  disabled={isLoading}
                >
                  {linkedinFile ? linkedinFile.name : "Upload PDF"}
                </button>
                <p className="text-xs text-gray-400 mt-1">
                  Tip: LinkedIn &rarr; More &rarr; Save to PDF
                </p>
              </>
            ) : (
              <input
                type="url"
                value={linkedinUrl}
                onChange={(e) => setLinkedinUrl(e.target.value)}
                placeholder="https://linkedin.com/in/your-profile"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm text-gray-900"
                disabled={isLoading}
              />
            )}
          </div>

          {/* Mode toggle */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Mode
            </label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setMode("practice")}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                  mode === "practice"
                    ? "bg-blue-50 text-blue-700 border-2 border-blue-500"
                    : "bg-gray-50 text-gray-600 border-2 border-transparent hover:bg-gray-100"
                }`}
                disabled={isLoading}
              >
                Practice
                <span className="block text-xs font-normal mt-0.5">
                  Hints enabled
                </span>
              </button>
              <button
                type="button"
                onClick={() => setMode("real")}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                  mode === "real"
                    ? "bg-orange-50 text-orange-700 border-2 border-orange-500"
                    : "bg-gray-50 text-gray-600 border-2 border-transparent hover:bg-gray-100"
                }`}
                disabled={isLoading}
              >
                Real
                <span className="block text-xs font-normal mt-0.5">
                  No hints
                </span>
              </button>
            </div>
          </div>

          {/* Model toggle */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              AI Model
            </label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setModel("haiku")}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                  model === "haiku"
                    ? "bg-green-50 text-green-700 border-2 border-green-500"
                    : "bg-gray-50 text-gray-600 border-2 border-transparent hover:bg-gray-100"
                }`}
                disabled={isLoading}
              >
                Haiku
                <span className="block text-xs font-normal mt-0.5">
                  Fast &amp; lightweight
                </span>
              </button>
              <button
                type="button"
                onClick={() => setModel("sonnet")}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                  model === "sonnet"
                    ? "bg-purple-50 text-purple-700 border-2 border-purple-500"
                    : "bg-gray-50 text-gray-600 border-2 border-transparent hover:bg-gray-100"
                }`}
                disabled={isLoading}
              >
                Sonnet
                <span className="block text-xs font-normal mt-0.5">
                  Smarter &amp; deeper
                </span>
              </button>
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={isLoading || !selected}
            className="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? "Starting..." : "Start Interview"}
          </button>
        </form>

        {/* Footer info */}
        <p className="text-center text-xs text-gray-400 mt-4">
          Pre-researched competencies and interview style will be used
          automatically. No web search needed.
        </p>

      </div>
    </div>
  );
}
