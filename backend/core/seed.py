"""Seed data for company-role presets."""

from __future__ import annotations

from core.database import CompanyRole


def seed_company_roles(db) -> None:
    """Insert default company-role presets."""
    presets = [_databricks_korea_se()]
    for data in presets:
        cr = CompanyRole(**data)
        db.add(cr)
    db.commit()


def _databricks_korea_se() -> dict:
    return {
        "company": "Databricks Korea",
        "role": "Solutions Engineer",
        "role_description": (
            "Pre-sales technical role at the intersection of sales and engineering. "
            "Uses technical expertise to demonstrate how the Databricks Data Intelligence Platform "
            "solves complex data challenges. Day-to-day: leading technical demos, architecting solutions, "
            "building proof-of-concept demos, working with Account Executives on strategy, "
            "leading workshops/seminars/meetups, authoring reference architectures."
        ),
        "required_competencies": [
            "Solution architecture -- architect and implement Big Data / AI solutions end-to-end",
            "Technical discovery -- skilled at asking the right questions to uncover customer needs",
            "Technical presentation and storytelling -- deliver cohesive demos to technical and non-technical audiences",
            "Business value articulation -- identify and articulate business value of technical solutions",
            "Pre-sales methodology -- understanding of sales cycles, PoC delivery, and technical win processes",
            "Cross-functional collaboration -- work across sales, engineering, product, and customer success",
            "Self-directed learning -- enthusiasm for continuous skill development in data/AI space",
            "Proof-of-concept development -- rapidly build and present working demos",
        ],
        "technical_skills": [
            "Python (primary), Java, Scala",
            "SQL (advanced: window functions, joins, nested queries, aggregations)",
            "Apache Spark (Spark SQL, DataFrame API, distributed processing, performance tuning)",
            "Delta Lake (ACID transactions, scalable metadata, Parquet-based storage)",
            "Lakehouse architecture (unified analytics platform)",
            "Cloud platforms (AWS, Azure, or GCP -- cluster setup, resource management, auto-scaling)",
            "Big Data technologies (Hadoop ecosystem, Kafka, distributed processing)",
            "Data engineering (ETL/ELT pipeline design, data ingestion, data governance)",
            "AI/ML fundamentals (GenAI, MLOps/LLMOps, ML model lifecycle)",
            "Databricks platform (Unity Catalog, Workflows, cluster configuration, notebooks)",
            "Data structures and algorithms (medium-to-hard level for coding interviews)",
        ],
        "soft_skills": [
            "Communication excellence -- articulate technical concepts to varied audiences (Korean + English)",
            "Presentation skills -- polished demos, slides, whiteboard sessions",
            "Customer empathy -- understand pain points and translate to solutions",
            "Storytelling -- frame technical solutions in terms of business outcomes",
            "Collaboration -- work effectively with AEs, product teams, engineering",
            "Adaptability -- handle multiple customer projects in fast-paced environment",
            "Problem-solving mindset -- creative, first-principles approach",
            "Authenticity and transparency -- genuine, honest communication",
            "Bias for action -- proactive, self-starting attitude",
        ],
        "interview_rounds": [
            {
                "name": "Recruiter Screen",
                "duration": "30 min",
                "description": "Background discussion, motivation for SE role, role overview, logistics",
            },
            {
                "name": "Online Assessment / Technical Screen",
                "duration": "60-70 min",
                "description": (
                    "Live coding on CodeSignal/CoderPad. 4 questions: medium-to-hard. "
                    "Topics: data structures & algorithms, SQL (window functions, joins), Python coding."
                ),
            },
            {
                "name": "Behavioral / Hiring Manager Interview",
                "duration": "60 min",
                "description": (
                    "Deep dive into past experience, leadership, teamwork. "
                    "Cultural fit: customer obsessed, raise the bar, truth seeking, first principles, bias for action."
                ),
            },
            {
                "name": "Technical Interview",
                "duration": "60 min",
                "description": (
                    "Spark/big data architecture, system design (data pipelines, distributed storage), "
                    "domain knowledge (data engineering, lakehouse concepts), real-world problem solving."
                ),
            },
            {
                "name": "Presentation / Demo Round",
                "duration": "60 min",
                "description": (
                    "Present a recent project end-to-end. Evaluated on: clarity, technical depth, "
                    "presentation structure, handling follow-up questions. "
                    "Must define: the problem, your solution, outcome, reflections."
                ),
            },
        ],
        "question_types": [
            "Why Databricks? Why Solutions Engineer?",
            "Tell me about the accomplishment you are most proud of",
            "Describe a time when you were innovative in solving a problem",
            "Tell me about a challenging technical problem you solved",
            "SQL: window functions, complex joins, aggregations",
            "Python: data structures, algorithms, string processing",
            "Spark concepts: DataFrame vs Spark SQL, execution plans, performance tuning",
            "Data architecture: designing ETL pipelines, lakehouse architecture, Delta Lake",
            "System design: scalable data storage and processing pipelines",
            "Present a recent project (problem -> solution -> outcome -> reflections)",
            "What do you know about big data and Databricks?",
            "How many projects do you handle at the same time?",
        ],
        "interview_tips": [
            "Master the STAR method -- Databricks interviewers explicitly look for S/T/A/R structure",
            "Know Databricks platform deeply: Spark, Delta Lake, Unity Catalog, lakehouse architecture",
            "Prepare a polished project presentation for the demo round",
            "Practice SQL and Python coding under time pressure (4 questions in 60-70 min)",
            "Align with Databricks core values: customer obsessed, raise the bar, truth seeking, first principles, bias for action",
            "Demonstrate customer empathy and communication skills -- this is a pre-sales role",
            "Be authentic and transparent -- don't over-prepare scripted answers",
            "Quantify your impact with numbers: 'reduced latency by 70%', 'handled N concurrent projects'",
        ],
        "jd_structured": {
            "requirements": [
                "Strong programming skills in Python, Java, or Scala",
                "Proficiency in SQL and relational databases",
                "Experience with Apache Spark or big data technologies",
                "Cloud platform experience (AWS, Azure, or GCP)",
                "Customer-facing communication skills",
                "Korean native + business-level English",
            ],
            "responsibilities": [
                "Lead technical demos and PoC implementations for customers",
                "Work with Account Executives on account strategy",
                "Architect solutions using Databricks platform",
                "Lead workshops, seminars, and community events",
                "Author reference architectures and technical content",
                "Develop expertise across data workflows",
            ],
            "qualifications": {
                "required": [
                    "Experience in data engineering, analytics, or related field",
                    "Programming proficiency (Python, SQL)",
                    "Cloud platform experience",
                    "Native Korean speaker with business-level English",
                ],
                "preferred": [
                    "Apache Spark experience",
                    "Pre-sales or customer-facing technical experience",
                    "Delta Lake / lakehouse architecture knowledge",
                    "ML/AI experience",
                ],
            },
            "keywords": [
                "Spark", "Delta Lake", "Python", "SQL", "AWS", "Azure", "GCP",
                "ETL", "data engineering", "lakehouse", "Unity Catalog",
                "MLOps", "LLMOps", "Kafka", "Hadoop", "Databricks",
                "PoC", "pre-sales", "solutions engineering",
            ],
            "experience_level": "mid",
            "summary": "Pre-sales Solutions Engineer for Databricks Korea, combining technical expertise with customer engagement",
        },
    }
