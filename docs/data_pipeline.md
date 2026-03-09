# Orbit Data Pipeline

The data pipeline collects signals from multiple sources to detect emerging trends.

---

# Data Sources

Orbit collects data from several external platforms:

Google Trends
Reddit discussions
Technology news feeds

These signals help the system understand what topics are gaining attention.

---

# Data Processing Steps

The pipeline processes data in several stages.

Data Collection
Fetch trending keywords and discussions from external sources.

Topic Extraction
Identify key topics and keywords from collected data.

Topic Clustering
Group related topics together to form narrative clusters.

Momentum Scoring
Calculate how quickly a topic is gaining attention.

---

# Pipeline Output

The output of the pipeline is a list of trending topics.

Example output:

Topic: AI agents
Momentum Score: High
Source Signals: Google Trends + Reddit

This information is passed to the Strategy Engine.
