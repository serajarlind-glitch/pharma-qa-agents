"""
Regulatory standards reference database.

Embedded citation index so agents can reference precise, verifiable regulatory
sections. This is NOT a substitute for reading the actual regulations — it's a
structured lookup to enforce citation accuracy.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Regulation:
    code: str
    title: str
    authority: str
    scope: str
    key_sections: dict[str, str]


# ---------------------------------------------------------------------------
# FDA CFR — Code of Federal Regulations
# ---------------------------------------------------------------------------

FDA_21CFR_210 = Regulation(
    code="21 CFR Part 210",
    title="Current Good Manufacturing Practice in Manufacturing, Processing, Packing, or Holding of Drugs; General",
    authority="FDA",
    scope="General cGMP requirements for all drug products",
    key_sections={
        "210.1": "Status of current good manufacturing practice regulations",
        "210.2": "Applicability of current good manufacturing practice regulations",
        "210.3": "Definitions",
    },
)

FDA_21CFR_211 = Regulation(
    code="21 CFR Part 211",
    title="Current Good Manufacturing Practice for Finished Pharmaceuticals",
    authority="FDA",
    scope="Specific cGMP requirements for finished pharmaceutical products",
    key_sections={
        "211.22": "Responsibilities of quality control unit",
        "211.25": "Personnel qualifications",
        "211.42": "Design and construction features (facilities)",
        "211.46": "Ventilation, air filtration, air heating and cooling",
        "211.56": "Sanitation (facilities maintenance)",
        "211.63": "Equipment design, size, and location",
        "211.67": "Equipment cleaning and maintenance",
        "211.68": "Automatic, mechanical, and electronic equipment (computerized systems)",
        "211.80": "General requirements for components, containers, and closures",
        "211.84": "Testing and approval or rejection of components, containers, and closures",
        "211.100": "Written procedures; deviations",
        "211.101": "Charge-in of components",
        "211.103": "Calculation of yield",
        "211.105": "Equipment identification",
        "211.110": "Sampling and testing of in-process materials and drug products",
        "211.111": "Time limitations on production",
        "211.113": "Control of microbiological contamination",
        "211.115": "Reprocessing",
        "211.130": "Packaging and labeling operations",
        "211.132": "Tamper-evident packaging for OTC drugs",
        "211.134": "Drug product inspection",
        "211.137": "Expiration dating",
        "211.142": "Warehousing procedures",
        "211.150": "Distribution procedures",
        "211.160": "General requirements for laboratory controls",
        "211.165": "Testing and release for distribution",
        "211.166": "Stability testing",
        "211.167": "Special testing requirements",
        "211.170": "Reserve samples",
        "211.176": "Penicillin contamination",
        "211.180": "General requirements for records and reports",
        "211.182": "Equipment cleaning and use log",
        "211.184": "Component, drug product container, closure, and labeling records",
        "211.186": "Master production and control records",
        "211.188": "Batch production and control records",
        "211.192": "Production record review (QA review of batch records)",
        "211.194": "Laboratory records",
        "211.196": "Distribution records",
        "211.198": "Complaint files",
    },
)

FDA_21CFR_11 = Regulation(
    code="21 CFR Part 11",
    title="Electronic Records; Electronic Signatures",
    authority="FDA",
    scope="Requirements for electronic records and signatures to be trustworthy, reliable, and equivalent to paper records",
    key_sections={
        "11.10": "Controls for closed systems",
        "11.30": "Controls for open systems",
        "11.50": "Signature manifestations",
        "11.70": "Signature/record linking",
        "11.100": "General requirements for electronic signatures",
        "11.200": "Electronic signature components and controls",
        "11.300": "Controls for identification codes/passwords",
    },
)

# ---------------------------------------------------------------------------
# EU GMP — EudraLex Volume 4
# ---------------------------------------------------------------------------

EU_GMP_PART1 = Regulation(
    code="EudraLex Volume 4 Part I",
    title="EU Guidelines for Good Manufacturing Practice for Medicinal Products for Human and Veterinary Use",
    authority="EMA",
    scope="Basic requirements for GMP in EU pharmaceutical manufacturing",
    key_sections={
        "Chapter 1": "Pharmaceutical Quality System",
        "Chapter 2": "Personnel",
        "Chapter 3": "Premises and Equipment",
        "Chapter 4": "Documentation",
        "Chapter 5": "Production",
        "Chapter 6": "Quality Control",
        "Chapter 7": "Outsourced Activities",
        "Chapter 8": "Complaints, Quality Defects and Product Recalls",
        "Chapter 9": "Self Inspection",
    },
)

EU_GMP_ANNEX1 = Regulation(
    code="EU GMP Annex 1",
    title="Manufacture of Sterile Medicinal Products (2022 revision)",
    authority="EMA",
    scope="Contamination control strategy, cleanroom design, sterile manufacturing",
    key_sections={
        "§3-4": "Principle and scope",
        "§5-§16": "Contamination Control Strategy (CCS)",
        "§17-§41": "Premises (cleanroom classification, Grade A/B/C/D)",
        "§42-§56": "Equipment",
        "§57-§70": "Utilities (water, gases, HVAC)",
        "§71-§97": "Personnel",
        "§98-§114": "Production and specific technologies",
        "§115-§131": "Environmental and process monitoring",
        "§132-§143": "Quality Control",
    },
)

EU_GMP_ANNEX11 = Regulation(
    code="EU GMP Annex 11",
    title="Computerised Systems",
    authority="EMA",
    scope="Requirements for GMP-regulated computerised systems",
    key_sections={
        "§1": "Risk Management",
        "§2": "Personnel",
        "§3": "Suppliers and Service Providers",
        "§4": "Validation",
        "§5": "Data (accuracy, completeness, legibility)",
        "§6": "Accuracy Checks",
        "§7": "Data Storage",
        "§8": "Printouts",
        "§9": "Audit Trails",
        "§10": "Change and Configuration Management",
        "§11": "Periodic Evaluation",
        "§12": "Security",
        "§13": "Incident Management",
        "§14": "Electronic Signature",
        "§15": "Batch Release",
        "§16": "Business Continuity",
        "§17": "Archiving",
    },
)

EU_GMP_ANNEX15 = Regulation(
    code="EU GMP Annex 15",
    title="Qualification and Validation",
    authority="EMA",
    scope="Requirements for qualification of equipment/facilities and validation of processes",
    key_sections={
        "§1-§3": "Principle, scope, and organizing validation",
        "§4-§8": "Documentation (VMP, protocols, reports)",
        "§9-§13": "Qualification stages (DQ, IQ, OQ, PQ)",
        "§14-§19": "Process Validation (traditional, continuous, hybrid)",
        "§20-§23": "Verification of transportation",
        "§24-§29": "Cleaning validation (MACO, PDE, visual limits)",
        "§30-§35": "Change control and revalidation",
    },
)

# ---------------------------------------------------------------------------
# ICH Guidelines
# ---------------------------------------------------------------------------

ICH_Q1A = Regulation(
    code="ICH Q1A(R2)",
    title="Stability Testing of New Drug Substances and Products",
    authority="ICH",
    scope="Stability study design, conditions, and testing frequency",
    key_sections={
        "2.1": "Stress testing (forced degradation)",
        "2.2": "Selection of batches",
        "2.3": "Container closure system",
        "2.4": "Specification",
        "2.5": "Testing frequency",
        "2.6": "Storage conditions (25°C/60%RH, 30°C/65%RH, 40°C/75%RH)",
        "2.7": "Stability commitment",
        "2.8": "Evaluation (statistical analysis, shelf life determination)",
    },
)

ICH_Q2 = Regulation(
    code="ICH Q2(R2)",
    title="Validation of Analytical Procedures",
    authority="ICH",
    scope="Validation parameters for analytical methods",
    key_sections={
        "Specificity": "Ability to assess analyte in presence of other components",
        "Linearity": "Proportional response within a given range",
        "Range": "Interval between upper and lower concentration levels",
        "Accuracy": "Closeness of test results to true value",
        "Precision": "Repeatability, intermediate precision, reproducibility",
        "Detection Limit": "Lowest amount that can be detected (LOD)",
        "Quantitation Limit": "Lowest amount that can be quantitated (LOQ)",
        "Robustness": "Capacity to remain unaffected by small deliberate variations",
    },
)

ICH_Q3C = Regulation(
    code="ICH Q3C(R8)",
    title="Impurities: Guideline for Residual Solvents",
    authority="ICH",
    scope="Classification and limits for residual solvents in pharmaceuticals",
    key_sections={
        "Class 1": "Solvents to be avoided (benzene, carbon tetrachloride, etc.)",
        "Class 2": "Solvents to be limited (acetonitrile, methanol, DCM, etc.)",
        "Class 3": "Solvents with low toxic potential (acetone, ethanol, etc.)",
    },
)

ICH_Q7 = Regulation(
    code="ICH Q7",
    title="Good Manufacturing Practice Guide for Active Pharmaceutical Ingredients",
    authority="ICH",
    scope="GMP for API manufacturing",
    key_sections={
        "Section 2": "Quality Management",
        "Section 3": "Personnel",
        "Section 4": "Buildings and Facilities",
        "Section 5": "Process Equipment",
        "Section 6": "Documentation and Records",
        "Section 7": "Materials Management",
        "Section 8": "Production and In-Process Controls",
        "Section 9": "Packaging and Identification Labeling",
        "Section 10": "Storage and Distribution",
        "Section 11": "Laboratory Controls",
        "Section 12": "Validation",
        "Section 13": "Change Control",
        "Section 14": "Rejection and Re-Use of Materials",
        "Section 15": "Complaints and Recalls",
        "Section 16": "Contract Manufacturers",
        "Section 17": "Agents, Brokers, Traders, Distributors, Repackers, Relabelers",
        "Section 18": "Specific Guidance for APIs by Cell Culture/Fermentation",
        "Section 19": "APIs for Use in Clinical Trials",
    },
)

ICH_Q8 = Regulation(
    code="ICH Q8(R2)",
    title="Pharmaceutical Development",
    authority="ICH",
    scope="Quality by Design (QbD), design space, critical quality attributes",
    key_sections={
        "2.1": "Components of the Drug Substance",
        "2.2": "Drug Product — formulation development",
        "2.3": "Manufacturing Process Development",
        "2.4": "Container Closure System",
        "2.5": "Microbiological Attributes",
        "2.6": "Compatibility",
        "P.2": "Pharmaceutical Development (CTD section)",
    },
)

ICH_Q9 = Regulation(
    code="ICH Q9(R1)",
    title="Quality Risk Management",
    authority="ICH",
    scope="Principles and tools for quality risk management in pharma",
    key_sections={
        "Section 4": "QRM process (initiate, assess, control, communicate, review)",
        "Section 5": "Risk Management Methodology",
        "Annex I.1": "FMEA / FMECA",
        "Annex I.2": "HACCP",
        "Annex I.3": "PHA (Preliminary Hazard Analysis)",
        "Annex I.4": "Risk Ranking and Filtering",
        "Annex I.5": "FTA (Fault Tree Analysis)",
        "Annex I.6": "HAZOP",
        "Annex I.7": "Supporting Statistical Tools",
    },
)

ICH_Q10 = Regulation(
    code="ICH Q10",
    title="Pharmaceutical Quality System",
    authority="ICH",
    scope="Lifecycle quality system model for pharmaceutical industry",
    key_sections={
        "Section 1": "Pharmaceutical Quality System (PQS)",
        "Section 2": "Management Responsibility",
        "Section 3": "Continual Improvement of Process Performance and Product Quality",
        "Section 4": "Continual Improvement of the PQS",
        "1.5": "Knowledge Management",
        "3.2.1": "CAPA System",
        "3.2.2": "Change Management System",
        "3.2.3": "Management Review",
    },
)

ICH_Q12 = Regulation(
    code="ICH Q12",
    title="Technical and Regulatory Considerations for Pharmaceutical Product Lifecycle Management",
    authority="ICH",
    scope="Post-approval change management, established conditions",
    key_sections={
        "Section 3": "Established Conditions (ECs)",
        "Section 4": "Post-Approval CMC Change Management Tools",
        "Section 5": "PACMP (Post-Approval Change Management Protocol)",
        "Section 6": "Product Lifecycle Management (PLCM) document",
    },
)

# ---------------------------------------------------------------------------
# GAMP & Data Integrity
# ---------------------------------------------------------------------------

GAMP5 = Regulation(
    code="GAMP 5 (2nd Edition, 2022)",
    title="A Risk-Based Approach to Compliant GxP Computerized Systems",
    authority="ISPE",
    scope="Computer system validation / assurance methodology",
    key_sections={
        "Category 1": "Infrastructure Software (OS, database engines)",
        "Category 3": "Non-configured Products (COTS, firmware)",
        "Category 4": "Configured Products (ERP, LIMS, MES configured)",
        "Category 5": "Custom Applications (bespoke software)",
        "Critical Thinking": "Risk-based approach to validation effort",
        "CSA": "Computer Software Assurance (FDA draft guidance alignment)",
    },
)

DATA_INTEGRITY_ALCOA = Regulation(
    code="ALCOA+ Principles",
    title="Data Integrity Framework",
    authority="FDA/WHO/PIC/S",
    scope="Fundamental data integrity requirements for GxP data",
    key_sections={
        "Attributable": "Who performed the action and when",
        "Legible": "Data can be read and understood",
        "Contemporaneous": "Recorded at the time of the activity",
        "Original": "First capture of the data (or certified true copy)",
        "Accurate": "No errors or editing without documented amendment",
        "+Complete": "All data including repeat/reanalysis data retained",
        "+Consistent": "Applied in a predictable manner (date formats, sequences)",
        "+Enduring": "Recorded on approved/controlled media, durable",
        "+Available": "Accessible for review throughout the retention period",
    },
)

# ---------------------------------------------------------------------------
# Pharmacopeial references
# ---------------------------------------------------------------------------

USP_GENERAL_CHAPTERS = Regulation(
    code="USP General Chapters",
    title="United States Pharmacopeia — Key General Chapters",
    authority="USP",
    scope="Compendial test methods and requirements",
    key_sections={
        "<1>": "Injections and Implanted Drug Products",
        "<11>": "USP Reference Standards",
        "<61>": "Microbiological Examination of Nonsterile Products: Microbial Enumeration Tests",
        "<62>": "Microbiological Examination of Nonsterile Products: Tests for Specified Microorganisms",
        "<71>": "Sterility Tests",
        "<85>": "Bacterial Endotoxins Test",
        "<197>": "Spectrophotometric Identification Tests",
        "<231>": "Heavy Metals (being replaced by <232>/<233>)",
        "<232>": "Elemental Impurities — Limits",
        "<233>": "Elemental Impurities — Procedures",
        "<467>": "Residual Solvents",
        "<621>": "Chromatography (system suitability requirements)",
        "<711>": "Dissolution",
        "<724>": "Drug Release (extended-release dosage forms)",
        "<731>": "Loss on Drying",
        "<785>": "Osmolality and Osmolarity",
        "<788>": "Particulate Matter in Injections",
        "<795>": "Pharmaceutical Compounding — Nonsterile",
        "<797>": "Pharmaceutical Compounding — Sterile",
        "<905>": "Uniformity of Dosage Units",
        "<921>": "Water Determination (Karl Fischer)",
        "<1058>": "Analytical Instrument Qualification",
        "<1225>": "Validation of Compendial Procedures",
        "<1226>": "Verification of Compendial Procedures",
    },
)


# ---------------------------------------------------------------------------
# Registry — quick lookup by topic
# ---------------------------------------------------------------------------

ALL_REGULATIONS = [
    FDA_21CFR_210, FDA_21CFR_211, FDA_21CFR_11,
    EU_GMP_PART1, EU_GMP_ANNEX1, EU_GMP_ANNEX11, EU_GMP_ANNEX15,
    ICH_Q1A, ICH_Q2, ICH_Q3C, ICH_Q7, ICH_Q8, ICH_Q9, ICH_Q10, ICH_Q12,
    GAMP5, DATA_INTEGRITY_ALCOA,
    USP_GENERAL_CHAPTERS,
]

# Topic → regulation mapping for agents to cross-reference
TOPIC_INDEX: dict[str, list[Regulation]] = {
    "deviation": [FDA_21CFR_211, EU_GMP_PART1, ICH_Q10],
    "oos": [FDA_21CFR_211, ICH_Q2, USP_GENERAL_CHAPTERS],
    "capa": [FDA_21CFR_211, ICH_Q10, EU_GMP_PART1],
    "change_control": [ICH_Q10, ICH_Q12, EU_GMP_PART1],
    "validation": [EU_GMP_ANNEX15, FDA_21CFR_211, ICH_Q2],
    "process_validation": [EU_GMP_ANNEX15, FDA_21CFR_211, ICH_Q8],
    "cleaning_validation": [EU_GMP_ANNEX15, FDA_21CFR_211],
    "csv": [EU_GMP_ANNEX11, FDA_21CFR_11, GAMP5],
    "data_integrity": [DATA_INTEGRITY_ALCOA, EU_GMP_ANNEX11, FDA_21CFR_11],
    "risk": [ICH_Q9, ICH_Q10],
    "stability": [ICH_Q1A, FDA_21CFR_211],
    "analytical": [ICH_Q2, USP_GENERAL_CHAPTERS, FDA_21CFR_211],
    "sterile": [EU_GMP_ANNEX1, USP_GENERAL_CHAPTERS],
    "api": [ICH_Q7],
    "quality_system": [ICH_Q10, EU_GMP_PART1, FDA_21CFR_211],
    "audit": [FDA_21CFR_211, EU_GMP_PART1, ICH_Q10],
    "documentation": [EU_GMP_PART1, FDA_21CFR_211, DATA_INTEGRITY_ALCOA],
    "dissolution": [USP_GENERAL_CHAPTERS, ICH_Q2],
    "residual_solvents": [ICH_Q3C, USP_GENERAL_CHAPTERS],
    "equipment_qualification": [EU_GMP_ANNEX15, FDA_21CFR_211],
    "training": [FDA_21CFR_211, EU_GMP_PART1, ICH_Q10],
    "supplier": [FDA_21CFR_211, ICH_Q7, EU_GMP_PART1],
    "regulatory_submission": [ICH_Q12, ICH_Q10],
    "recall": [FDA_21CFR_211, EU_GMP_PART1],
}


def get_regulations_for_topic(topic: str) -> list[Regulation]:
    """Look up applicable regulations for a topic keyword."""
    topic_lower = topic.lower().replace(" ", "_")
    if topic_lower in TOPIC_INDEX:
        return TOPIC_INDEX[topic_lower]
    # Fuzzy fallback: match any topic containing the keyword
    matches = []
    for key, regs in TOPIC_INDEX.items():
        if topic_lower in key or key in topic_lower:
            matches.extend(regs)
    # Deduplicate preserving order
    seen = set()
    result = []
    for r in matches:
        if r.code not in seen:
            seen.add(r.code)
            result.append(r)
    return result


def format_regulation_context(regs: list[Regulation]) -> str:
    """Format regulations as structured context for injection into agent prompts."""
    if not regs:
        return ""
    lines = ["APPLICABLE REGULATORY REFERENCES:"]
    for reg in regs:
        lines.append(f"\n## {reg.code} — {reg.title}")
        lines.append(f"Authority: {reg.authority} | Scope: {reg.scope}")
        lines.append("Key sections:")
        for sec, desc in reg.key_sections.items():
            lines.append(f"  - {sec}: {desc}")
    return "\n".join(lines)
