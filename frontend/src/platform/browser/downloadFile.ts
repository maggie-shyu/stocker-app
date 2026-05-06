export function downloadFile(data: BlobPart | Blob, filename: string, mimeType?: string) {
  const blob = data instanceof Blob ? data : new Blob([data], mimeType ? { type: mimeType } : undefined);
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = filename;
  link.click();

  URL.revokeObjectURL(url);
}
