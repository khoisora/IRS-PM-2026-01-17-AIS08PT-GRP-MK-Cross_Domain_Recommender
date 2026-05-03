### IRS Practice Module — Group Project Submission

**[ Naming Convention ]** CourseCode-StartDate-BatchCode-TeamName-ProjectName

**[ This submission ]** `IRS-PM-2026-01-17-AIS08PT-GRP-MK-Cross_Domain_Recommender`

---

## SECTION 1 : PROJECT TITLE
## Cross-Domain Recommender System — Movies → Video Games

A research-driven recommender system that explores when and how cross-domain
signal (movie ratings) can improve recommendations in a target domain (video
games), using the Amazon Reviews 2023 dataset.

---

## SECTION 2 : EXECUTIVE SUMMARY / PAPER ABSTRACT

Most production recommenders operate within a single domain — a movie service
recommends movies, a games store recommends games — even when the same user
has rich behavioural signal sitting in another vertical. This project asks a
focused question: **when does cross-domain transfer actually help, and when
does it hurt?**

We benchmark seven recommendation models — three single-domain
(MF-BPR, NeuMF, LightGCN), three cross-domain (CMF, EMCDR, PTUPCDR), and one
content-based (SBERT-CDR) — on the Amazon Reviews 2023 movie–game pair
(75,844 users, 56,040 items, 1.7M ratings, 29.8% user overlap). We run them
through seven structured "lessons" that vary the data regime (explicit vs
implicit ranking, low vs high overlap, source-rich vs target-sparse, cold-start,
content-aware, and co-occurrence reranking) to surface the conditions under
which each model wins.

Findings drive a two-lane production design: cold-start users (zero game
ratings) are routed to CDR models that transfer their movie taste; warm users
(>=1 game rating) are routed to direct game-space models. A training-free
movie->game co-occurrence rerank delivers the biggest single lift in cold-start.
The system is delivered as a runnable FastAPI demo with a jQuery front-end,
SQLite persistence, an hourly retrain scheduler, and a packaged Docker image.

---

## SECTION 3 : CREDITS / PROJECT CONTRIBUTION

| Official Full Name | Student ID | Work Items (Who Did What) | Email |
| :--- | :---: | :--- | :--- |
| Vo Minh Khoi | A0339229W | End-to-end: data pipeline, model implementations & benchmarking, evaluation framework, co-occurrence rerank & routing, FastAPI + SQLite + jQuery demo, Docker packaging, report & videos | mr.khoivominh@gmail.com |

---

## SECTION 4 : VIDEO OF SYSTEM MODELLING & USE CASE DEMO

Two recorded videos in the `Video/` folder:

* **Promotion video** — `Video/IRS-PM-2026-01-17-AIS08PT-GRP-MK-Cross_Domain_Recommender-promotion.mp4`
  (business pain & value, use case demo)
* **Technical / system-design video** — `Video/IRS-PM-2026-01-17-AIS08PT-GRP-MK-Cross_Domain_Recommender-system.mp4`
  (architecture, recommender routing, ML pipeline)

---

## SECTION 5 : USER GUIDE

`Refer to Appendix C (Setup Guide) in the project report under ProjectReport/.`

The repository ships with a Makefile that drives both workflows.

### Option 1 — Local (non-Docker)

```bash
cd SystemCode
make all                   # = make install + make dev
# or step by step:
make install               # create .venv and install deps (Python 3.11+)
make export                # OPTIONAL: re-train and re-export artifacts/demo/
make dev                   # start FastAPI demo on http://localhost:8000
```

The demo ships with pre-built `artifacts/demo/` so `make all` works without
re-training. `make export` is only needed if you want to regenerate the
embeddings.

### Option 2 — Docker

```bash
cd SystemCode
make build                 # docker build -t crossrec .
make run                   # docker run on host port 8000
# override the port: make run PORT=8001
make logs                  # follow container logs
make stop                  # tear down
```

### Optional: full data pipeline (requires raw dataset)

```bash
cd SystemCode
make download-data         # ~3.3 GB from McAuley Lab UCSD
PYTHONPATH=. .venv/bin/python ml/data/process_data.py
make export
```

---

## SECTION 6 : PROJECT REPORT / PAPER

`Refer to project report at Github Folder: ProjectReport/`

`IRS-PM-2026-01-17-AIS08PT-GRP-MK-Cross_Domain_Recommender-Group-Report.pdf`

The report covers:
- Executive Summary
- Introduction (Background, Problem Statement, Market Research, Methodology)
- Data (sources, schema, splitting protocols)
- Methodology (single-domain, cross-domain, and content-based models)
- Experiments and Results (7 lessons)
- System Design (architecture, routing, ML pipeline, refresh)
- Conclusion and Future Work
- References
- Appendix A: Project Proposal
- Appendix B: Mapped System Functionalities against MR / RS / CGS modules
- Appendix C: Installation & User Guide
- Appendix D: Personal Contribution
- Appendix E: AI Tools Usage Declaration

---

## SECTION 7 : MISCELLANEOUS

`Refer to Github Folder: Miscellaneous/`

* `member-github.txt` — group name, member, GitHub repo URL

---

**This project is part of the Graduate Certificate in [Intelligent Reasoning
Systems (IRS)](https://www.iss.nus.edu.sg/stackable-certificate-programmes/intelligent-systems)
offered by [NUS-ISS](https://www.iss.nus.edu.sg).**
