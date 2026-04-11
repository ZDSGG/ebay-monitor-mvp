import { ChangeEvent, FormEvent, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { createItem, importItemsCsv } from "../lib/api";
import type { CsvImportResponse } from "../types";

type CsvPreviewRow = {
  url: string;
  note: string;
};

export function ItemCreatePage() {
  const [url, setUrl] = useState("");
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [csvRows, setCsvRows] = useState<CsvPreviewRow[]>([]);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvImportResult, setCsvImportResult] = useState<CsvImportResponse | null>(null);
  const [csvSubmitting, setCsvSubmitting] = useState(false);

  const parsedCount = useMemo(() => csvRows.length, [csvRows]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setMessage(null);

    try {
      const result = await createItem({ url, note });
      setMessage(`已创建 ${result.title ?? result.legacy_item_id}，首次抓取状态为 ${result.initial_crawl.status}。`);
      setUrl("");
      setNote("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建商品失败。");
    } finally {
      setSubmitting(false);
    }
  }

  function onCsvSelected(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setCsvFile(file);

    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result ?? "");
      const rows = text
        .split(/\r?\n/)
        .slice(1)
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => {
          const [csvUrl = "", csvNote = ""] = line.split(",");
          return { url: csvUrl, note: csvNote };
        });
      setCsvRows(rows);
    };
    reader.readAsText(file);
  }

  async function onCsvImport() {
    if (!csvFile) return;
    setCsvSubmitting(true);
    setError(null);

    try {
      const result = await importItemsCsv(csvFile);
      setCsvImportResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "CSV 导入失败。");
    } finally {
      setCsvSubmitting(false);
    }
  }

  return (
    <section className="page-grid">
      <div className="form-panel">
        <div className="section-head">
          <div>
            <p className="eyebrow">新增监控</p>
            <h3>录入新的 eBay 商品</h3>
          </div>
        </div>
        <form className="stack-form" onSubmit={onSubmit}>
          <label>
            <span>eBay 链接</span>
            <input value={url} onChange={(event) => setUrl(event.target.value)} placeholder="https://www.ebay.com/itm/..." required />
          </label>
          <label>
            <span>备注</span>
            <textarea value={note} onChange={(event) => setNote(event.target.value)} placeholder="记录监控原因或补充说明" rows={4} />
          </label>
          <button className="primary-button" type="submit" disabled={submitting}>
            {submitting ? "创建中..." : "创建商品"}
          </button>
        </form>
        {message ? <div className="empty-panel success-panel">{message}</div> : null}
        {error ? <div className="empty-panel error-panel">{error}</div> : null}
      </div>

      <div className="side-panel">
        <div className="section-head">
          <div>
            <p className="eyebrow">CSV 导入</p>
            <h3>预览待导入文件</h3>
          </div>
        </div>
        <label className="upload-panel">
          <input type="file" accept=".csv" onChange={onCsvSelected} />
          <span>选择 CSV 文件</span>
          <strong>已解析 {parsedCount} 行</strong>
        </label>
        <div className="preview-list">
          {csvRows.slice(0, 8).map((row, index) => (
            <div key={`${row.url}-${index}`} className="preview-row">
              <strong>{row.url}</strong>
              <span>{row.note || "无备注"}</span>
            </div>
          ))}
        </div>
        <button className="primary-button" type="button" disabled={!csvFile || csvSubmitting} onClick={onCsvImport}>
          {csvSubmitting ? "导入中..." : "导入 CSV"}
        </button>
        {csvImportResult ? (
          <div className="empty-panel success-panel">
            导入成功 {csvImportResult.created_count} 条，跳过 {csvImportResult.skipped_count} 条，失败 {csvImportResult.failed_count} 条。
          </div>
        ) : null}
        <Link className="action-link" to="/items">
          返回列表
        </Link>
      </div>
    </section>
  );
}
