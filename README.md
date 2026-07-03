# MarketNode Terminal

An institutional-grade quantitative analytical terminal for cryptographic asset due diligence, algorithmic risk modeling, and automated investment dossier compilation. Built to automate the pre-investment discovery phase for crypto venture funds and digital asset analysts.

---

## 🛠️ Production Architecture & Component Specifications

The core architecture is strictly modularized into decoupled, single-responsibility files to eliminate cross-dependency execution bottlenecks and ensure scalability.

### 1. `app.py` (The Execution Orchestrator)
* **Role:** Serves as the primary entry point and system UI execution loop state machine.
* **Core Logic:** Coordinates data flows between backend analytical modules and the frontend viewport, managing persistent session states for interactive simulations.

### 2. `ui_components.py` (The Viewport Layout Framework)
* **Role:** Manages the entire visual presentation layer.
* **Core Logic:** Implements a strict, dark-themed Bloomberg Terminal aesthetic. Configures multi-column metric layouts, data grids, stress-test input sliders, and interactive `Plotly` render frames.

### 3. `calculations.py` (The Algorithmic Math Core)
* **Role:** Handles statistical risk computation and mathematical inequality modeling.
* **Core Logic:** Houses the core **Gini Coefficient** loop and geometric array mappings for non-linear **Lorenz Curve** plotting. Tracks mathematical token trajectory decay models.

### 4. `api.py` (The Data Ingestion Layer)
* **Role:** Manages external cryptographic data pipelines and stateful endpoint resolution.
* **Core Logic:** Contains defensive ticker mapping matrices (e.g., resolving `ETH` to database slug `ethereum`) to guarantee bulletproof live market ingestion and prevent `404 Not Found` routing errors. Houses the `AssetNotIndexed` custom exception handler.

### 5. `llm_service.py` (The Intelligence Synthesis Layer)
* **Role:** Interacts with generative AI models to provide contextual qualitative risk assessments.
* **Core Logic:** Formats system-level prompts using real-time market metrics to generate structured, institutional-grade narrative briefs without pipeline lag.

### 6. `scraper.py` (The OSINT Data Harvester)
* **Role:** Automated web-ingestion tool for gathering off-chain metrics, developer velocity data, and social ecosystem sentiment.
* **Core Logic:** Parses unstructured repository metrics and cross-chain activity data to serve as an auxiliary feed for the risk scoring engine.

### 7. `report_generator.py` (The Document Compilation Engine)
* **Role:** Dedicated enterprise printing ledger powered by native `ReportLab` flowables.
* **Core Logic:** Dynamically compiles metrics, allocation weightings, and risk parameters into a sterile, data-dense 5-page PDF Institutional Dossier featuring auto-aligned citation registries on Page 5.

---

## 📊 Comprehensive Feature Suite

* **Quantitative Insider Telemetry:** Live mapping of wallet concentration indices backed by standalone statistical inequality distribution models.
* **Insider Liquidity Stress-Test Simulator:** Interactive slippage and price-impact tracking models evaluating localized AMM pool depth shifts under arbitrary whale supply dumping scenarios.
* **Ecosystem Shock Backtesting Matrix:** Algorithmic price trajectory modeling tracking historical black swan vectors alongside automated network health recovery time projections.
* **Cross-Chain Liquidity Map:** Live depth, spread, and arbitrage vector monitoring across multi-network decentralized exchange venues.
* **Syndication Pipeline:** Immediate copy-paste ready Markdown blocks structured for instant Telegram/Notion channel dissemination alongside direct AMM DEX route swap execution simulation hooks.

---

## 💻 Tech Stack & Dependencies

* **Frontend Engine:** Streamlit Framework (Dark-Mode Core)
* **Data Visualization:** Plotly Open Source (Interactive Chart Matrix)
* **Data Ingestion & Processing:** Pandas, Requests Engine
* **Document Compositor:** ReportLab Enterprise PDF Suite

---

## 📁 Project Directory Mapping

```text
├── .vscode/                # Local editor development environment profiles
├── .gitignore              # Production environment artifact exclusion protocol
├── api.py                  # Cryptographic data mapping and live ingest pipelines
├── app.py                  # Main system entry point and runtime orchestrator
├── calculations.py         # Gini algorithms, stress-test math, and trajectory models
├── llm_service.py          # AI analytical synthesis and prompt payload operations
├── prompt_rules.md         # Markdown ledger governing internal LLM behavioral criteria
├── pyrightconfig.json      # Static type-checking and code-quality profiles
├── report_generator.py     # Production-grade ReportLab PDF compilation module
├── requirements.txt        # Production server environment dependency ledger
├── scraper.py              # OSINT parser and alternative web-ingestion workflows
└── ui_components.py        # Bloomberg-themed presentation layers and widget setups
