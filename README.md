# 🕯️ The Last Maintainer

### When the original developers are gone, the code remembers.

**The Last Maintainer** is an open-source, local-first AI tool designed to recover forgotten knowledge from legacy and poorly documented codebases.

It investigates source code, API endpoints, dependencies, Git history, and existing documentation to help developers understand how an unfamiliar application works.

The goal is simple: **turn an undocumented codebase into an evidence-backed map of its architecture and history.**

> Built for [Hacktoberfest Open-Source AI Challenge — Week 4: Ghost in the Machine](https://dev.to/challenges/hacktoberfest-week4-2026-10-26).

---

## 👻 The Problem

Every legacy codebase has a story.

- The original developers have moved on.
- Documentation no longer reflects the implementation.
- Nobody remembers why certain APIs exist.
- Dependencies and relationships between components are difficult to trace.
- Important decisions are buried in Git history.
- Developers spend hours understanding systems before they can safely modify them.

The knowledge may be forgotten, but traces of it remain in the code.

**The Last Maintainer helps developers find those traces and reconstruct what the evidence reveals.**

## ✨ What It Aims to Do

### 🔍 1. Codebase Archaeology
Inspect a repository to discover its structure, important files, components, and relationships.

### 🔌 2. API Discovery
Extract API endpoints, HTTP methods, route mappings, and associated controllers from supported source code.

### 🗺️ 3. Architecture Reconstruction
Build a navigable representation of relationships between controllers, services, and database entities where those relationships can be established.

### 📜 4. Git History Investigation
Explore relevant commits to understand when code changed and what the available history reveals about its evolution.

### 📚 5. Documentation Gap Detection
Compare selected documentation against the actual source code to identify potentially outdated or inconsistent information.

### 🤖 6. Local AI Investigation
Use a locally running language model to explain extracted information and answer questions about the repository.

### 🧾 7. Evidence-Backed Reports
Generate findings with references to relevant source files and commits. Clearly distinguish verified facts, plausible explanations, and unanswered questions.

*These are the intended project capabilities. Features should be marked complete only after they have been implemented and tested.*

---

## 🧠 How It Works

The Last Maintainer combines deterministic code analysis with local AI.

```text
         ┌──────────────────────────┐
         │   Existing Codebase      │
         │                          │
         │  Source Code             │
         │  Git History             │
         │  Documentation           │
         │  Configuration           │
         └────────────┬─────────────┘
                      │
                      ▼
         ┌──────────────────────────┐
         │   Repository Analyzer    │
         │                          │
         │  Parse source code       │
         │  Discover API endpoints  │
         │  Extract relationships   │
         │  Inspect Git history     │
         └────────────┬─────────────┘
                      │
                      ▼
         ┌──────────────────────────┐
         │  Structured Evidence     │
         │                          │
         │  Files and symbols       │
         │  Endpoints and methods   │
         │  Component relationships│
         │  Relevant commits        │
         └────────────┬─────────────┘
                      │
                      ▼
         ┌──────────────────────────┐
         │    Local AI Analysis     │
         │                          │
         │  Explain findings        │
         │  Answer questions        │
         │  Identify uncertainties │
         └────────────┬─────────────┘
                      │
                      ▼
         ┌──────────────────────────┐
         │   Investigation Report   │
         │                          │
         │  Architecture overview   │
         │  API inventory           │
         │  Evidence references     │
         │  Documentation gaps      │
         │  Unanswered questions    │
         └──────────────────────────┘
```

The analyzer extracts facts before the language model generates explanations. This separation helps reduce unsupported claims and makes findings easier to verify.

---

## 🛠️ Technology Stack

The planned architecture uses the following technologies:

| Component | Technology | Purpose |
|---|---|---|
| Frontend | React.js + Vite | Repository exploration and investigation interface |
| Backend | Python + FastAPI | API endpoints and analysis orchestration |
| Code analysis | Tree-sitter or language-specific parsers | Extract source-code structure |
| AI inference | Ollama | Run supported open-weight models locally |
| Version history | Git | Inspect repository changes and commits |
| Output | Markdown | Export investigation findings |

The exact implementation may evolve as the project develops.

---

## 🚀 Getting Started

### Prerequisites

Install the following tools:

- [Git](https://git-scm.com/)
- [Python](https://www.python.org/)
- [Node.js](https://nodejs.org/)
- [Ollama](https://ollama.com/) for local AI inference

You will also need a locally available model supported by your Ollama installation.

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/the-last-maintainer.git
cd the-last-maintainer
```

Replace `YOUR_USERNAME` with your GitHub username.

### 2. Configure the Backend

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows:

```powershell
.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

Install the dependencies once the project's `requirements.txt` is available:

```bash
pip install -r requirements.txt   # use requirements-dev.txt to run tests (pytest)
```

Start the backend using the entry point configured in the project. For example, if the application entry point is `app.main:app`:

```bash
uvicorn app.main:app --reload   # serves http://127.0.0.1:8000
```

### 3. Configure Local AI

Install and start Ollama, then download a compatible model.

For example:

```bash
ollama pull qwen2.5:7b
```

Verify that the model is available:

```bash
ollama list
```

Configure the backend to use the selected model and local Ollama service.

The model shown above is an example; hardware requirements and model availability vary.

### 4. Configure the Frontend

If the frontend is located in a `frontend` directory:

```bash
cd frontend
npm install
npm run dev
```

Use the development URL printed by Vite to open the interface.

> **Setup status:** These commands describe the intended development workflow. Adjust directory names, application entry points, and configuration variables to match the actual repository implementation.

---

## 🔒 Privacy by Design

The project is designed around local-first analysis.

- Repository source code can be analyzed locally.
- Local AI inference avoids requiring a third-party hosted AI API.
- Findings should link back to the evidence used to produce them.
- The tool should not execute arbitrary repository code during analysis.
- Secrets and sensitive configuration should be redacted from model context and exported reports.

Local inference does not automatically guarantee complete privacy. Network access, application logging, model configuration, and data storage must also be considered.

---

## 🎯 Project Goals

The initial development priorities are:

- [x] Repository structure analysis
- [x] Java and Spring Boot source-code analysis
- [x] API endpoint discovery
- [x] Controller-to-service relationship mapping
- [x] Git history investigation
- [x] Documentation inconsistency detection
- [ ] Ollama integration
- [ ] Evidence-linked AI answers
- [x] Markdown report generation
- [x] Automated tests and example repository
- [ ] Installation and usage documentation

Update these checkboxes as the corresponding features are implemented and tested.

---

## 🧪 Example Use Case

Imagine inheriting a Spring Boot application with hundreds of classes and outdated documentation.

You want to understand the application's authentication API before modifying it.

With The Last Maintainer, the intended workflow is:

1. Select the repository for analysis.
2. Discover relevant API endpoints and controllers.
3. Trace relationships to services and database entities.
4. Inspect relevant Git history.
5. Ask a question about the authentication flow.
6. Review the answer alongside references to supporting source files.
7. Export the findings for future maintainers.

The tool should also identify when the available evidence is insufficient to answer a question reliably.

---

## 🌱 Why Open Source?

Software outlives the people who build it.

Open-source tools make it possible for developers to inspect how analysis works, contribute additional language support, improve the quality of extracted evidence, and adapt the software to their own development environments.

Open-weight models make local AI investigation possible without making a hosted AI API a mandatory dependency.

The Last Maintainer aims to make forgotten software knowledge easier to recover, verify, and share.

---

## 🤝 Contributing

Contributions are welcome!

Potential areas for contribution include:

- Additional programming-language support
- Improved source-code parsing
- Git history analysis
- Documentation comparison
- Evidence visualization
- Local model integrations
- Testing and example repositories

To contribute:

1. Fork the repository.
2. Create a feature branch.
3. Implement and test your changes.
4. Open a pull request describing the problem and solution.

Please avoid including proprietary source code, credentials, or sensitive repository data in issues and pull requests.

---

## 🗺️ Roadmap

**Phase 1 — Discover**
- Repository scanning
- Source-code structure extraction
- API inventory

**Phase 2 — Reconstruct**
- Component relationship mapping
- Git history analysis
- Documentation gap detection

**Phase 3 — Investigate**
- Local AI integration
- Evidence-grounded question answering
- Uncertainty reporting

**Phase 4 — Preserve**
- Investigation reports
- Reusable architecture documentation
- Improved support for additional languages

---

## 📜 License

This project will use an open-source license. Add the appropriate `LICENSE` file to the repository before publishing.

---

## 👨‍💻 Author

**Shivam Kumar Jha**

Built as an exploration of local AI, software archaeology, and the forgotten knowledge hidden inside legacy codebases.

**The developers may be gone. The code is still talking.** 🕯️

---

## 🧪 Try It on the Bundled Example

```bash
uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```

Open the Vite URL and analyze the absolute path of `examples/sample-spring-app`. Configure Ollama with `OLLAMA_URL` (default `http://127.0.0.1:11434`) and `OLLAMA_MODEL` (default `qwen2.5:7b`). Without Ollama the app still returns the retrieved evidence.

Run the tests with `pip install -r requirements-dev.txt && pytest`.

**Status:** the Ollama integration is covered by mocked tests only and has not been run against a live model; its checkboxes above stay unchecked until it has.
