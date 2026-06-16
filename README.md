# Orbit 🚀

> An autonomous AI growth engine that discovers trends, generates content, publishes to Threads, collects feedback, and continuously improves its strategy.

Orbit is a multi-agent content intelligence system designed to operate like a high-performing content team.

Instead of blindly generating posts, Orbit learns from audience behavior, analyzes performance data, creates strategic playbooks, and uses those insights to improve future content.

---

## ✨ Features

### 🔍 Trend Discovery

Orbit continuously scans Hacker News to identify emerging topics and opportunities.

Examples:

- AI Infrastructure
- Local LLMs
- AI Agents
- Engineering Stories
- Developer Tools
- Open Source Projects

---

### 🧠 LLM Trend Ranking

A Gemini-powered ranking engine evaluates trends based on:

- Relevance
- Technical depth
- Audience alignment
- Strategic guidance
- Growth potential

Example Output:

```json
{
  "id": 9,
  "title": "My Homelab AI Dev Platform",
  "score": 9.9,
  "reason": "Directly aligns with audience interest in local AI infrastructure."
}
```

---

### ✍️ Content Generation

Orbit generates:

- Short posts
- Medium posts
- Multi-part Threads

Every post includes:

- Hook
- Core content
- Takeaway

All outputs are validated using strict Pydantic schemas.

---

### 🧵 Threads Publishing

Supports:

- Single-post publishing
- Multi-part thread publishing
- Automatic numbering
- Thread chaining
- Length validation
- Retry handling

Example:

```text
1/6 Hook

2/6 Insight

3/6 Breakdown

4/6 Analysis

5/6 Implications

6/6 Takeaway
```

---

### 📊 Metrics Collection

Orbit continuously collects engagement metrics at:

- 2 Hours
- 24 Hours
- 72 Hours

Metrics stored:

- Likes
- Replies
- Reposts

All data is persisted in Supabase.

---

### 📈 Strategy Engine (In Progress)

Every week Orbit analyzes:

- Best performing posts
- Worst performing posts
- Market trends
- Audience behavior

And generates a strategy playbook containing:

- Winning hook structures
- Preferred tones
- Effective formats
- Topic recommendations
- Copywriting rules

This playbook directly influences future ranking and content generation.

---

## 🏗 Architecture

```text
                     ┌─────────────────┐
                     │ Hacker News API │
                     └────────┬────────┘
                              │
                              ▼
                   ┌────────────────────┐
                   │ Trend Collector    │
                   └────────┬───────────┘
                            │
                            ▼
                   ┌────────────────────┐
                   │ Trend Processor    │
                   └────────┬───────────┘
                            │
                            ▼
                   ┌────────────────────┐
                   │ LLM Ranker         │
                   └────────┬───────────┘
                            │
                            ▼
                   ┌────────────────────┐
                   │ Content Generator  │
                   └────────┬───────────┘
                            │
                            ▼
                   ┌────────────────────┐
                   │ Threads Publisher  │
                   └────────┬───────────┘
                            │
                            ▼
                   ┌────────────────────┐
                   │ Supabase Storage   │
                   └────────┬───────────┘
                            │
                            ▼
                   ┌────────────────────┐
                   │ Metrics Fetcher    │
                   └────────┬───────────┘
                            │
                            ▼
                   ┌────────────────────┐
                   │ Strategy Engine    │
                   └────────┬───────────┘
                            │
                            ▼
                   ┌────────────────────┐
                   │ Strategy Playbook  │
                   └────────┬───────────┘
                            │
                            └──────────────► Influences Future Content
```

---

## 🧠 System Philosophy

Orbit separates:

### What to talk about

Determined daily by:

- Hacker News
- Market trends
- Emerging discussions

### How to talk about it

Determined weekly by:

- Audience feedback
- Historical performance
- Strategy analysis

This separation allows Orbit to remain both:

- Responsive to trends
- Consistent in voice

---

## 📂 Project Structure

```text
orbit/
│
├── core/
│   │
│   ├── trend_engine/
│   │   ├── trend_collector.py
│   │   ├── trend_processor.py
│   │   └── llm_ranker.py
│   │
│   ├── content_engine/
│   │   ├── content_generator.py
│   │   └── prompts.py
│   │
│   ├── analytics_engine/
│   │   ├── tracker.py
│   │   ├── storage.py
│   │   └── fetch_metrics.py
│   │
│   ├── strategy_engine/
│   │   ├── calculator.py
│   │   ├── analyzer.py
│   │   ├── orchestrator.py
│   │   └── prompts.py
│   │
│   └── utils/
│       ├── logger.py
│       └── schema.py
│
├── platforms/
│   └── threads/
│       ├── client.py
│       └── publisher.py
│
├── configs/
│   └── settings.py
│
├── .github/
│   └── workflows/
│
├── main.py
├── run_strategy.py
└── requirements.txt
```

---

## 🛠 Tech Stack

### AI

- Gemini 2.5 Flash Lite
- Prompt Engineering
- Pydantic Validation

### Backend

- Python
- Supabase
- PostgreSQL

### Automation

- GitHub Actions

### Content Platform

- Threads API

### Trend Sources

- Hacker News API

### Observability

- Structured Logging
- Retry Logic
- Validation Layers
- Exponential Backoff

---

## 🗄 Database Design

### Posts Table

Stores:

- Generated content
- Topic
- Hook
- Takeaway
- Content type
- Thread IDs
- Strategy epoch

---

### Post Metrics Table

Stores:

- 2 Hour metrics
- 24 Hour metrics
- 72 Hour metrics

Metrics:

- Likes
- Replies
- Reposts
- Engagement Score

---

### Strategies Table (Planned)

Stores:

- Weekly strategy versions
- Winning patterns
- Losing patterns
- Copywriting rules
- Topic recommendations
- Hypotheses
- Rollback history

---

## ⚙️ Automation

### Content Pipeline

Runs multiple times daily:

```text
Collect Trends
→ Rank Trends
→ Generate Content
→ Publish to Threads
→ Store Metadata
```

---

### Metrics Pipeline

Runs every 2 hours:

```text
Check Eligible Posts
→ Fetch Metrics
→ Store Metrics
```

---

### Strategy Pipeline (Planned)

Runs weekly:

```text
Analyze Performance
→ Generate Strategy
→ Save Playbook
→ Influence Future Posts
```

---

## 🚦 Roadmap

### Phase 1 — Content Engine ✅

- Trend collection
- Trend ranking
- Content generation
- Threads publishing

---

### Phase 2 — Feedback Engine ✅

- Metrics collection
- Supabase integration
- Engagement tracking
- Automated metric fetching

---

### Phase 3 — Strategy Engine 🚧

- Weekly playbook generation
- Top vs Bottom post analysis
- Market trend synthesis
- Strategy epochs
- Rollback mechanism

---

### Phase 4 — Autonomous Growth

- Hypothesis testing
- Adaptive publishing schedules
- Exploration vs exploitation
- Multi-platform expansion
- Reinforcement-style learning loop

---

## 🎯 Long-Term Vision

Most AI content systems stop after generation.

Orbit closes the loop.

```text
Observe
→ Learn
→ Adapt
→ Improve
```

Every piece of content becomes training data for future decisions.

The goal is not to build an AI that posts.

The goal is to build an AI that learns.

---

## 🚀 Getting Started

### Clone Repository

```bash
git clone https://github.com/your-username/orbit.git

cd orbit
```

### Create Virtual Environment

```bash
python3 -m venv venv

source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

```bash
GEMINI_API_KEY=your_key

THREADS_ACCESS_TOKEN=your_token

SUPABASE_URL=your_url

SUPABASE_KEY=your_key
```

### Run Content Pipeline

```bash
python3 main.py
```

### Run Metrics Pipeline

```bash
python3 -m core.analytics_engine.fetch_metrics
```

### Run Strategy Pipeline

```bash
python3 run_strategy.py
```

---

## 👨‍💻 Author

**Deepansh Gupta**

Built as a hands-on exploration of:

- AI Systems Engineering
- Agentic Workflows
- Growth Engineering
- LLM Applications
- Production Infrastructure
- Autonomous Content Systems

---

## ⭐ Support

If you found Orbit interesting, consider starring the repository and following its progress.

The roadmap is only getting started.
