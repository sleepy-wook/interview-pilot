"""Seed data for company-role presets."""

from __future__ import annotations

from core.database import CompanyRole


def seed_company_roles(db) -> None:
    """Insert default company-role presets (skips already-existing ones)."""
    presets = [_databricks_korea_se(), _bosch_korea_erp_sm()]
    for data in presets:
        existing = (
            db.query(CompanyRole)
            .filter_by(company=data["company"], role=data["role"])
            .first()
        )
        if existing is None:
            db.add(CompanyRole(**data))
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


def _bosch_korea_erp_sm() -> dict:
    return {
        "company": "Bosch Korea",
        "role": "ERP SM (Solution Manager)",
        "role_description": (
            "ERP Solution Manager responsible for managing and optimizing SAP ERP systems "
            "across Bosch Korea's manufacturing and business operations. Leads ERP solution design, "
            "implementation, and continuous improvement. Bridges business requirements with technical "
            "solutions, coordinates with global Bosch IT teams, and ensures alignment with Bosch's "
            "digital transformation strategy."
        ),
        "required_competencies": [
            "ERP solution design -- architect end-to-end SAP solutions for manufacturing and business processes",
            "Business process analysis -- map and optimize business processes (procurement, production, sales, finance)",
            "Stakeholder management -- manage expectations of business users, IT teams, and global counterparts",
            "Project management -- lead ERP implementation and enhancement projects on time and budget",
            "Change management -- drive user adoption and organizational change for new ERP processes",
            "Cross-functional coordination -- work with manufacturing, finance, logistics, and IT departments",
            "Vendor management -- coordinate with SAP consultants and implementation partners",
            "Continuous improvement -- identify optimization opportunities in existing ERP landscape",
        ],
        "technical_skills": [
            "SAP ERP (S/4HANA, ECC) -- deep functional knowledge across core modules",
            "SAP modules: MM (Materials Management), PP (Production Planning), SD (Sales & Distribution), FI/CO (Finance & Controlling)",
            "SAP Solution Manager -- monitoring, testing, change management, ITSM",
            "SAP BTP (Business Technology Platform) -- integration and extension capabilities",
            "ABAP basics -- ability to read and understand custom developments",
            "SAP Fiori / UI5 -- modern user interface concepts",
            "Integration technologies (RFC, IDoc, BAPI, OData, PI/PO, CPI)",
            "Data migration and conversion strategies",
            "Manufacturing execution systems (MES) integration",
            "Business intelligence (SAP BW, Analytics Cloud)",
            "SQL and database concepts for troubleshooting and reporting",
        ],
        "soft_skills": [
            "Communication excellence -- explain technical solutions to non-technical business stakeholders (Korean + English)",
            "Analytical thinking -- break down complex business problems into structured solutions",
            "Leadership -- guide project teams and influence without direct authority",
            "Cultural adaptability -- work effectively with German HQ and global teams",
            "Problem-solving -- troubleshoot production issues under time pressure",
            "Documentation skills -- create clear functional specifications and process documentation",
            "Negotiation -- balance business demands with technical constraints and timelines",
            "Collaboration -- work across departments and geographies in a matrix organization",
        ],
        "interview_rounds": [
            {
                "name": "HR Screening",
                "duration": "30 min",
                "description": "Background review, motivation for Bosch, salary expectations, language proficiency check.",
            },
            {
                "name": "Hiring Manager Interview",
                "duration": "60 min",
                "description": (
                    "Deep dive into ERP project experience, leadership examples, "
                    "understanding of Bosch business and manufacturing processes. "
                    "Behavioral questions on teamwork and conflict resolution."
                ),
            },
            {
                "name": "Technical Interview",
                "duration": "60 min",
                "description": (
                    "SAP module knowledge, solution design scenarios, integration architecture, "
                    "troubleshooting cases, S/4HANA migration strategy discussion."
                ),
            },
            {
                "name": "Case Study / Presentation",
                "duration": "45-60 min",
                "description": (
                    "Present a past ERP project or solve a business case: "
                    "requirements gathering, solution design, implementation approach, risk mitigation."
                ),
            },
        ],
        "question_types": [
            "Why Bosch? Why ERP Solution Manager?",
            "Describe your experience with SAP S/4HANA implementation or migration",
            "Walk me through an ERP project you led from requirements to go-live",
            "How do you handle conflicting requirements from different business departments?",
            "Explain your approach to ERP change management and user adoption",
            "Technical: How would you design an integration between SAP and a third-party MES?",
            "Scenario: Production is down due to an SAP issue -- walk me through your troubleshooting process",
            "How do you prioritize enhancement requests in a large ERP landscape?",
            "Describe a time you had to push back on a stakeholder's requirement",
            "How do you stay current with SAP technology and Bosch digital transformation initiatives?",
        ],
        "interview_tips": [
            "Know Bosch's business: automotive (Mobility Solutions), industrial tech, consumer goods, energy",
            "Understand Bosch values: Invented for life, quality, reliability, innovation",
            "Prepare concrete examples of ERP projects with measurable outcomes (cost savings, efficiency gains)",
            "Be ready to discuss SAP S/4HANA vs ECC differences and migration strategies",
            "Show understanding of manufacturing processes (MRP, production scheduling, quality management)",
            "Demonstrate ability to work in a global matrix organization (Korean office + German HQ)",
            "Prepare a structured case study presentation with clear problem-solution-outcome flow",
            "Highlight both technical depth and business acumen -- this role bridges both worlds",
        ],
        "jd_structured": {
            "requirements": [
                "5+ years of SAP ERP experience in a manufacturing environment",
                "Deep functional knowledge in at least 2 SAP modules (MM, PP, SD, FI/CO)",
                "Project management experience for ERP implementations or enhancements",
                "Business process understanding in manufacturing, supply chain, or finance",
                "Korean native + business-level English (German is a plus)",
            ],
            "responsibilities": [
                "Manage and optimize SAP ERP solutions for Bosch Korea operations",
                "Lead requirements gathering and solution design for ERP enhancements",
                "Coordinate with global Bosch IT teams on system changes and upgrades",
                "Ensure smooth ERP operations and provide L2/L3 support",
                "Drive S/4HANA migration readiness and digital transformation initiatives",
                "Manage relationships with external SAP consultants and partners",
            ],
            "qualifications": {
                "required": [
                    "Bachelor's degree in IT, Engineering, or Business",
                    "SAP ERP experience (S/4HANA or ECC)",
                    "Manufacturing industry experience",
                    "Korean native speaker with business English proficiency",
                ],
                "preferred": [
                    "SAP certification in one or more modules",
                    "S/4HANA migration project experience",
                    "ABAP development or debugging ability",
                    "Experience in automotive or electronics manufacturing",
                    "German language skills",
                ],
            },
            "keywords": [
                "SAP", "S/4HANA", "ECC", "ERP", "ABAP", "Fiori",
                "MM", "PP", "SD", "FI/CO", "Solution Manager",
                "manufacturing", "MES", "integration", "PI/PO", "CPI",
                "BTP", "data migration", "change management",
                "Bosch", "automotive", "IoT",
            ],
            "experience_level": "mid-senior",
            "summary": "ERP Solution Manager for Bosch Korea, managing SAP systems across manufacturing and business operations",
        },
    }
