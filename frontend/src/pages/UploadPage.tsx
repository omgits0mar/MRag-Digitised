import { useCallback, useEffect, useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";

import { getUploadStatus, uploadFile } from "@/api/endpoints";
import type { ApiError, UploadResponse, UploadStatusResponse } from "@/api/types";
import { cn } from "@/lib/cn";

const ACCEPTED_EXTENSIONS = ["csv", "txt", "pdf", "md", "docx"] as const;
const ACCEPT_ATTR = ACCEPTED_EXTENSIONS.map((ext) => `.${ext}`).join(",");
const DEFAULT_MAX_BYTES = 100 * 1024 * 1024;

interface RecentUpload extends UploadResponse {
  key: string;
}

function getExtension(filename: string): string {
  const idx = filename.lastIndexOf(".");
  return idx === -1 ? "" : filename.slice(idx + 1).toLowerCase();
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function apiErrorMessage(error: ApiError): string {
  if (error.kind === "backend_error") {
    return error.detail || error.message;
  }
  return error.message;
}

function UploadPage(): JSX.Element {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [recentUploads, setRecentUploads] = useState<RecentUpload[]>([]);
  const [status, setStatus] = useState<UploadStatusResponse | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const allowedExtensions = status?.allowed_extensions ?? [...ACCEPTED_EXTENSIONS];
  const maxBytes = status?.max_bytes ?? DEFAULT_MAX_BYTES;

  const refreshStatus = useCallback(async () => {
    const result = await getUploadStatus();
    if (result.kind === "ok") {
      setStatus(result.data);
    }
  }, []);

  useEffect(() => {
    void refreshStatus();
  }, [refreshStatus]);

  const handleFiles = useCallback(
    async (files: FileList | null) => {
      if (files === null || files.length === 0) {
        return;
      }
      const file = files[0];
      if (file === undefined) {
        return;
      }

      const ext = getExtension(file.name);
      if (!allowedExtensions.includes(ext)) {
        setErrorMessage(
          `Unsupported file type ".${ext}". Allowed: ${allowedExtensions.join(", ")}.`,
        );
        return;
      }
      if (file.size > maxBytes) {
        setErrorMessage(
          `File is ${formatBytes(file.size)}. Maximum allowed is ${formatBytes(maxBytes)}.`,
        );
        return;
      }

      setErrorMessage(null);
      setProgress(0);
      setIsUploading(true);

      const result = await uploadFile(file, {
        onProgress: (percent) => {
          setProgress(percent);
        },
      });

      setIsUploading(false);

      if (result.kind === "error") {
        setErrorMessage(apiErrorMessage(result.error));
        return;
      }

      setRecentUploads((previous) => [
        { ...result.data, key: `${Date.now()}-${result.data.filename}` },
        ...previous,
      ]);
      void refreshStatus();
    },
    [allowedExtensions, maxBytes, refreshStatus],
  );

  const handleDrop = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      setIsDragging(false);
      void handleFiles(event.dataTransfer.files);
    },
    [handleFiles],
  );

  const handleInputChange = useCallback(
    (event: ChangeEvent<HTMLInputElement>) => {
      void handleFiles(event.currentTarget.files);
      event.currentTarget.value = "";
    },
    [handleFiles],
  );

  return (
    <section className="bg-card text-card-foreground rounded-[2rem] border p-8 shadow-shell">
      <p className="text-sm uppercase tracking-[0.3em] text-slate-500">Upload</p>
      <h2 className="mt-3 text-3xl font-semibold">Expand the knowledge base</h2>
      <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600 dark:text-slate-300">
        Drop a document below to chunk it, embed it, and append it to the live FAISS index.
        Accepted formats: {allowedExtensions.map((ext) => `.${ext}`).join(", ")}. Maximum size{" "}
        {formatBytes(maxBytes)}.
      </p>

      <div
        role="button"
        tabIndex={0}
        aria-label="Upload a document"
        onClick={() => fileInputRef.current?.click()}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            fileInputRef.current?.click();
          }
        }}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => {
          setIsDragging(false);
        }}
        onDrop={handleDrop}
        className={cn(
          "mt-8 flex cursor-pointer flex-col items-center justify-center gap-3 rounded-[1.75rem] border-2 border-dashed px-6 py-12 text-center transition-colors",
          isDragging
            ? "border-primary bg-primary/10"
            : "border-slate-300 bg-background/60 hover:bg-background",
          isUploading ? "pointer-events-none opacity-70" : "",
        )}
      >
        <p className="text-base font-semibold">
          {isUploading ? "Uploading..." : "Drop a file here or click to browse"}
        </p>
        <p className="text-xs text-slate-500">
          {allowedExtensions.map((ext) => `.${ext}`).join(" · ")}
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPT_ATTR}
          aria-label="Select file to upload"
          className="sr-only"
          onChange={handleInputChange}
        />
      </div>

      {isUploading ? (
        <div className="mt-6" role="status" aria-live="polite">
          <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
            <span>Uploading</span>
            <span>{progress}%</span>
          </div>
          <div className="bg-muted mt-2 h-2 overflow-hidden rounded-full">
            <div
              className="bg-primary h-full rounded-full transition-[width]"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      ) : null}

      {errorMessage !== null ? (
        <p
          role="alert"
          className="mt-6 rounded-[1.2rem] border border-red-300 bg-red-100/70 px-4 py-3 text-sm text-red-900 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-200"
        >
          {errorMessage}
        </p>
      ) : null}

      <div className="mt-10 grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <div className="bg-background/70 rounded-[1.75rem] border p-5">
          <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Index status</p>
          <dl className="mt-4 grid gap-3 text-sm">
            <div className="flex items-center justify-between gap-3">
              <dt className="text-slate-500 dark:text-slate-300">Total vectors</dt>
              <dd className="font-semibold">{status?.total_vectors ?? "—"}</dd>
            </div>
            <div className="flex items-center justify-between gap-3">
              <dt className="text-slate-500 dark:text-slate-300">Max file size</dt>
              <dd className="font-semibold">{formatBytes(maxBytes)}</dd>
            </div>
            <div className="flex items-center justify-between gap-3">
              <dt className="text-slate-500 dark:text-slate-300">Last upload</dt>
              <dd className="font-semibold">
                {status?.last_upload === null || status?.last_upload === undefined
                  ? "—"
                  : status.last_upload.filename}
              </dd>
            </div>
          </dl>
        </div>

        <div className="bg-background/70 rounded-[1.75rem] border p-5">
          <p className="text-xs uppercase tracking-[0.24em] text-slate-500">This session</p>
          {recentUploads.length === 0 ? (
            <p className="mt-4 text-sm text-slate-500 dark:text-slate-300">
              Uploaded files will appear here.
            </p>
          ) : (
            <ul className="mt-4 grid gap-3 text-sm">
              {recentUploads.map((upload) => (
                <li
                  key={upload.key}
                  className="border-border flex items-center justify-between gap-3 rounded-2xl border px-4 py-3"
                >
                  <div className="min-w-0">
                    <p className="truncate font-semibold">{upload.filename}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-300">
                      {upload.chunks_added} chunks · index now {upload.total_vectors} vectors
                    </p>
                  </div>
                  <span className="bg-primary/10 text-primary shrink-0 rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide">
                    .{upload.extension}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}

export default UploadPage;
