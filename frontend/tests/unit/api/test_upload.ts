import { describe, expect, it } from "vitest";

import { getUploadStatus, uploadFile } from "@/api/endpoints";

describe("upload api client", () => {
  it("posts multipart file and parses UploadResponse", async () => {
    const file = new File(["hello world"], "note.txt", { type: "text/plain" });
    const progressEvents: number[] = [];

    const result = await uploadFile(file, {
      onProgress: (percent) => {
        progressEvents.push(percent);
      },
    });

    expect(result.kind).toBe("ok");
    if (result.kind === "ok") {
      expect(result.data.filename).toBe("note.txt");
      expect(result.data.extension).toBe("txt");
      expect(result.data.chunks_added).toBeGreaterThan(0);
      expect(result.data.total_vectors).toBeGreaterThan(0);
    }
  });

  it("returns backend_error for unsupported extensions", async () => {
    const file = new File(["ignored"], "payload.exe", { type: "application/octet-stream" });

    const result = await uploadFile(file);

    expect(result.kind).toBe("error");
    if (result.kind === "error") {
      expect(result.error.kind).toBe("backend_error");
      if (result.error.kind === "backend_error") {
        expect(result.error.status).toBe(415);
      }
    }
  });

  it("fetches upload status with allowed extensions and max size", async () => {
    const result = await getUploadStatus();

    expect(result.kind).toBe("ok");
    if (result.kind === "ok") {
      expect(result.data.allowed_extensions).toEqual(
        expect.arrayContaining(["csv", "txt", "pdf", "md", "docx"]),
      );
      expect(result.data.max_bytes).toBeGreaterThan(0);
    }
  });
});
