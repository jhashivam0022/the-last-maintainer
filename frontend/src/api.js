async function request(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail || detail;
    } catch {
      /* body was not JSON */
    }
    throw new Error(detail);
  }
  return res.json();
}

const post = (url, body) =>
  request(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

export const health = () => request("/api/health");
export const analyze = (path) => post("/api/analyze", { path });
export const ask = (path, question) => post("/api/ask", { path, question });
export const report = (path, qa) => post("/api/report", { path, qa });
export const source = (path, file, line) =>
  request(`/api/source?${new URLSearchParams({ path, file, line, context: 8 })}`);
