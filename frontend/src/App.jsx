import { Fragment, useEffect, useState } from "react";
import * as api from "./api.js";

const TABS = ["Overview", "API", "Architecture", "History", "Doc gaps", "Ask", "Report"];
const LAYERS = ["controller", "service", "repository", "entity"];

function CodeViewer({ repoPath, file, line }) {
  const [state, setState] = useState({ loading: true });
  useEffect(() => {
    setState({ loading: true });
    api
      .source(repoPath, file, line)
      .then((d) => setState({ snippet: d.snippet }))
      .catch((e) => setState({ error: e.message }));
  }, [repoPath, file, line]);
  if (state.loading) return <pre className="code">Loading…</pre>;
  return <pre className="code">{state.error ? `Error: ${state.error}` : state.snippet}</pre>;
}

function Overview({ data }) {
  const { repo } = data;
  return (
    <div className="stack">
      <div className="stats">
        {[
          ["Files", repo.file_count],
          ["Java files", repo.java_files],
          ["Components", data.components.length],
          ["Endpoints", data.endpoints.length],
          ["Relationships", data.relationships.length],
        ].map(([label, value]) => (
          <div className="stat" key={label}>
            <b>{value}</b>
            <span>{label}</span>
          </div>
        ))}
      </div>
      <h3>Unanswered questions</h3>
      {data.open_questions.length ? (
        <ul>{data.open_questions.map((q) => <li key={q}>{q}</li>)}</ul>
      ) : (
        <p className="muted">None identified automatically.</p>
      )}
      <h3>Dependencies</h3>
      {repo.dependencies.length ? (
        <ul className="cols">
          {repo.dependencies.map((d) => (
            <li key={d.source + d.name}><code>{d.name}</code> {d.version}</li>
          ))}
        </ul>
      ) : (
        <p className="muted">No dependencies detected.</p>
      )}
    </div>
  );
}

function Endpoints({ data, repoPath }) {
  const [open, setOpen] = useState(null);
  if (!data.endpoints.length) return <p className="muted">No endpoints detected.</p>;
  return (
    <table>
      <thead>
        <tr><th>Method</th><th>Path</th><th>Handler</th><th>Source</th><th>Last commit</th></tr>
      </thead>
      <tbody>
        {data.endpoints.map((e, i) => {
          const last = e.history[0];
          return (
            <Fragment key={i}>
              <tr className="click" onClick={() => setOpen(open === i ? null : i)}>
                <td><span className={`verb ${e.method}`}>{e.method}</span></td>
                <td><code>{e.path}</code></td>
                <td>{e.controller}.{e.handler}</td>
                <td><code>{e.file}:{e.line}</code></td>
                <td>{last ? `${last.short} ${last.subject}` : "n/a"}</td>
              </tr>
              {open === i && (
                <tr>
                  <td colSpan={5}><CodeViewer repoPath={repoPath} file={e.file} line={e.line} /></td>
                </tr>
              )}
            </Fragment>
          );
        })}
      </tbody>
    </table>
  );
}

function Architecture({ data }) {
  const byLayer = Object.fromEntries(LAYERS.map((l) => [l, data.components.filter((c) => c.kind === l)]));
  const edges = (name) => data.relationships.filter((r) => r.source === name);
  return (
    <div className="stack">
      <div className="layers">
        {LAYERS.map((layer) => (
          <div className="layer" key={layer}>
            <h4>{layer}s</h4>
            {byLayer[layer].length === 0 && <p className="muted">none</p>}
            {byLayer[layer].map((c) => (
              <div className="card" key={c.name}>
                <b>{c.name}</b>
                {c.table && <span className="muted"> table {c.table}</span>}
                <div className="muted small">{c.file}:{c.line}</div>
                {edges(c.name).map((r) => (
                  <div className="edge" key={r.target + r.kind}>
                    → {r.kind} <b>{r.target}</b>
                  </div>
                ))}
              </div>
            ))}
          </div>
        ))}
      </div>
      <p className="muted small">Relationships come from type usage in declarations; each is backed by a file and line in the report.</p>
    </div>
  );
}

function History({ data }) {
  if (!data.repo.is_git) return <p className="muted">Not a Git repository.</p>;
  return (
    <ul className="commits">
      {data.commits.map((c) => (
        <li key={c.hash}>
          <code>{c.short}</code> <span className="muted">{c.date.slice(0, 10)} {c.author}</span>
          <div>{c.subject}</div>
        </li>
      ))}
    </ul>
  );
}

function DocGaps({ data }) {
  const g = data.doc_gaps;
  return (
    <div className="stack">
      <p className="muted">Heuristic matches. Verify each before acting. Docs scanned: {g.docs_scanned.length}.</p>
      <h3>Documented but not found in source</h3>
      {g.documented_not_found.length ? (
        <ul>
          {g.documented_not_found.map((x, i) => (
            <li key={i}><code>{x.method || "ANY"} {x.path}</code> in <code>{x.file}:{x.line}</code> — {x.problem}</li>
          ))}
        </ul>
      ) : <p className="muted">None.</p>}
      <h3>In source but not documented</h3>
      {g.undocumented.length ? (
        <ul>
          {g.undocumented.map((e, i) => (
            <li key={i}><code>{e.method} {e.path}</code> (<code>{e.file}:{e.line}</code>)</li>
          ))}
        </ul>
      ) : <p className="muted">None.</p>}
    </div>
  );
}

function Ask({ repoPath, qa, setQa }) {
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(e) {
    e.preventDefault();
    if (!question.trim()) return;
    setBusy(true);
    setError("");
    try {
      const res = await api.ask(repoPath, question);
      setQa([{ question, ...res }, ...qa]);
      setQuestion("");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="stack">
      <form onSubmit={submit} className="row">
        <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="e.g. How does login work?" />
        <button disabled={busy}>{busy ? "Thinking…" : "Ask"}</button>
      </form>
      {error && <p className="error">{error}</p>}
      {qa.map((item, i) => (
        <div className="card" key={i}>
          <b>{item.question}</b>
          {item.answer ? <pre className="answer">{item.answer}</pre> : <p className="muted">{item.note}</p>}
          {item.answer && <p className="muted small">{item.note}</p>}
          {item.evidence.map((ev) => (
            <details key={ev.id}>
              <summary><code>[{ev.id}]</code> {ev.title}</summary>
              {ev.snippet && <pre className="code">{ev.snippet}</pre>}
            </details>
          ))}
        </div>
      ))}
    </div>
  );
}

function Report({ repoPath, qa }) {
  const [markdown, setMarkdown] = useState("");
  const [error, setError] = useState("");

  async function generate() {
    setError("");
    try {
      const withAnswers = qa.filter((q) => q.answer).reverse();
      setMarkdown((await api.report(repoPath, withAnswers)).markdown);
    } catch (e) {
      setError(e.message);
    }
  }

  function download() {
    const url = URL.createObjectURL(new Blob([markdown], { type: "text/markdown" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = "investigation-report.md";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="stack">
      <div className="row">
        <button onClick={generate}>Generate report</button>
        {markdown && <button className="ghost" onClick={download}>Download .md</button>}
      </div>
      {error && <p className="error">{error}</p>}
      {markdown && <pre className="code report">{markdown}</pre>}
    </div>
  );
}

export default function App() {
  const [path, setPath] = useState("");
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [tab, setTab] = useState(TABS[0]);
  const [qa, setQa] = useState([]);
  const [ollama, setOllama] = useState(null);

  useEffect(() => {
    api.health().then((h) => setOllama(h.ollama)).catch(() => setOllama({ available: false }));
  }, []);

  async function run(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      setData(await api.analyze(path));
      setQa([]);
      setTab(TABS[0]);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app">
      <header>
        <h1>🕯️ The Last Maintainer</h1>
        <span className={`pill ${ollama?.available ? "ok" : "off"}`}>
          {ollama == null ? "checking AI…" : ollama.available
            ? `Ollama · ${ollama.model}${ollama.model_installed === false ? " (not pulled)" : ""}`
            : "Ollama offline · evidence only"}
        </span>
      </header>

      <form onSubmit={run} className="row">
        <input value={path} onChange={(e) => setPath(e.target.value)} placeholder="Absolute path to a local repository" />
        <button disabled={busy || !path.trim()}>{busy ? "Analyzing…" : "Analyze"}</button>
      </form>
      {error && <p className="error">{error}</p>}

      {data && (
        <>
          <nav>
            {TABS.map((t) => (
              <button key={t} className={t === tab ? "tab active" : "tab"} onClick={() => setTab(t)}>{t}</button>
            ))}
          </nav>
          <main>
            {tab === "Overview" && <Overview data={data} />}
            {tab === "API" && <Endpoints data={data} repoPath={data.repo.path} />}
            {tab === "Architecture" && <Architecture data={data} />}
            {tab === "History" && <History data={data} />}
            {tab === "Doc gaps" && <DocGaps data={data} />}
            {tab === "Ask" && <Ask repoPath={data.repo.path} qa={qa} setQa={setQa} />}
            {tab === "Report" && <Report repoPath={data.repo.path} qa={qa} />}
          </main>
        </>
      )}
    </div>
  );
}
