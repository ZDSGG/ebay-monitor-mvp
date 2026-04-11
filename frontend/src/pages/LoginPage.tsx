import { FormEvent, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { verifyAppSecret } from "../lib/api";
import { setStoredAppSecret } from "../lib/auth";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [secret, setSecret] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await verifyAppSecret(secret);
      setStoredAppSecret(secret);
      const target = typeof location.state?.from === "string" ? location.state.from : "/items";
      navigate(target, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "访问口令验证失败。");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="login-shell">
      <div className="login-card">
        <p className="eyebrow">访问保护</p>
        <h1>输入访问口令</h1>
        <p className="workspace-copy">只有持有口令的人才能进入商品监控系统。</p>
        <form className="stack-form" onSubmit={onSubmit}>
          <label>
            <span>访问口令</span>
            <input
              type="password"
              value={secret}
              onChange={(event) => setSecret(event.target.value)}
              placeholder="请输入访问口令"
              required
            />
          </label>
          <button className="primary-button" type="submit" disabled={submitting}>
            {submitting ? "验证中..." : "进入系统"}
          </button>
        </form>
        {error ? <div className="notice-banner error-panel">{error}</div> : null}
      </div>
    </section>
  );
}
