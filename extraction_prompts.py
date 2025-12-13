"""
Exemplos de prompts customizados para extração de grafo
Use conforme o tipo de documento que está processando
"""

# Prompt genérico (padrão) - máximo de entidades e relacionamentos
GENERIC_PROMPT = """You are an expert at extracting information and building knowledge graphs.
Extract ALL entities and relationships from the text, being as comprehensive as possible.
Return a valid JSON with this exact structure:
{
  "nodes": [
    {"id": "entity_id", "type": "EntityType", "properties": {"description": "brief description"}}
  ],
  "relationships": [
    {"source": "entity_id_1", "target": "entity_id_2", "type": "RELATIONSHIP_TYPE", "properties": {"description": "brief description"}}
  ]
}

IMPORTANT:
- Extract EVERY entity mentioned, including: people, organizations, locations, concepts, products, events, dates, etc.
- Every node MUST have an "id", "type", and "properties" field
- The "type" field is REQUIRED and should be a single word (e.g., Person, Organization, Location, Concept, Product, Event, Date)
- Extract ALL relationships between entities, including implicit ones
- Every relationship MUST have "source", "target", "type", and "properties" fields
- Return ONLY valid JSON, no markdown, no extra text
- If no entities found, return {"nodes": [], "relationships": []}"""

# Prompt para documentos jurídicos
LEGAL_PROMPT = """You are an expert at extracting legal information and building knowledge graphs.
Extract entities and relationships from legal documents.
Return a valid JSON with this exact structure:
{
  "nodes": [
    {"id": "entity_id", "type": "EntityType", "properties": {"description": "brief description"}}
  ],
  "relationships": [
    {"source": "entity_id_1", "target": "entity_id_2", "type": "RELATIONSHIP_TYPE", "properties": {"description": "brief description"}}
  ]
}

Entity types to extract:
- Person: Names of individuals (plaintiffs, defendants, witnesses, judges)
- Organization: Companies, law firms, government agencies
- LegalCase: Case names and numbers
- Law: Specific laws, statutes, regulations
- Clause: Contract clauses or legal provisions
- Date: Important dates (filing, hearing, judgment dates)
- Location: Jurisdictions, courts, venues

Relationship types:
- PARTY_IN: Person/Organization is party in a case
- REPRESENTED_BY: Party represented by lawyer/firm
- CITES: References a law or case
- VIOLATES: Violates a law or clause
- FILED_IN: Case filed in a court
- DECIDED_BY: Case decided by a judge

Return ONLY valid JSON, no markdown."""

# Prompt para documentos médicos
MEDICAL_PROMPT = """You are an expert at extracting medical information and building knowledge graphs.
Extract entities and relationships from medical documents.
Return a valid JSON with this exact structure:
{
  "nodes": [
    {"id": "entity_id", "type": "EntityType", "properties": {"description": "brief description"}}
  ],
  "relationships": [
    {"source": "entity_id_1", "target": "entity_id_2", "type": "RELATIONSHIP_TYPE", "properties": {"description": "brief description"}}
  ]
}

Entity types to extract:
- Patient: Patient names/identifiers
- Doctor: Healthcare providers
- Disease: Diseases, conditions, symptoms
- Medication: Drugs, treatments
- Procedure: Medical procedures, tests
- Organization: Hospitals, clinics, labs
- Date: Dates of visits, procedures, diagnoses

Relationship types:
- HAS_SYMPTOM: Patient has symptom
- DIAGNOSED_WITH: Patient diagnosed with disease
- PRESCRIBED: Doctor prescribed medication
- TREATED_WITH: Patient treated with procedure
- WORKS_AT: Doctor works at organization
- TREATS: Doctor treats patient
- CAUSES: Disease causes symptom

Return ONLY valid JSON, no markdown."""

# Prompt para documentos técnicos
TECHNICAL_PROMPT = """You are an expert at extracting technical information and building knowledge graphs.
Extract entities and relationships from technical documents.
Return a valid JSON with this exact structure:
{
  "nodes": [
    {"id": "entity_id", "type": "EntityType", "properties": {"description": "brief description"}}
  ],
  "relationships": [
    {"source": "entity_id_1", "target": "entity_id_2", "type": "RELATIONSHIP_TYPE", "properties": {"description": "brief description"}}
  ]
}

Entity types to extract:
- Technology: Programming languages, frameworks, tools
- Component: Software/hardware components
- System: Systems, applications, services
- Person: Authors, contributors, developers
- Organization: Companies, projects
- Concept: Technical concepts, patterns
- Version: Version numbers, releases

Relationship types:
- USES: System uses technology
- IMPLEMENTS: Component implements concept
- DEPENDS_ON: Component depends on another
- CREATED_BY: Created by person/organization
- PART_OF: Component is part of system
- COMPATIBLE_WITH: Compatible with technology
- EXTENDS: Extends or inherits from

Return ONLY valid JSON, no markdown."""

# Prompt para documentos financeiros
FINANCIAL_PROMPT = """You are an expert at extracting financial information and building knowledge graphs.
Extract entities and relationships from financial documents.
Return a valid JSON with this exact structure:
{
  "nodes": [
    {"id": "entity_id", "type": "EntityType", "properties": {"description": "brief description"}}
  ],
  "relationships": [
    {"source": "entity_id_1", "target": "entity_id_2", "type": "RELATIONSHIP_TYPE", "properties": {"description": "brief description"}}
  ]
}

Entity types to extract:
- Company: Companies, corporations
- Person: Executives, investors, analysts
- Asset: Stocks, bonds, real estate
- Transaction: Mergers, acquisitions, sales
- Market: Stock markets, exchanges
- Currency: Currencies, exchange rates
- Date: Transaction dates, earnings dates

Relationship types:
- OWNS: Person/Company owns asset
- TRADES: Company trades on market
- ACQUIRES: Company acquires another
- INVESTS_IN: Person/Company invests in asset
- MANAGES: Person manages company/fund
- REPORTS_TO: Executive reports to another
- VALUED_AT: Asset valued at amount

Return ONLY valid JSON, no markdown."""

# Prompt para documentos de estética
AESTHETICS_PROMPT = """Extract entities and relationships from this aesthetic/beauty text.

Focus on: procedures, treatments, products, ingredients, body parts, conditions, professionals, clinics, results.

Return ONLY this JSON:
{
  "nodes": [
    {"id": "entity_id", "type": "EntityType", "properties": {"description": "what is this"}}
  ],
  "relationships": [
    {"source": "id1", "target": "id2", "type": "RELATIONSHIP", "properties": {"description": "how they relate"}}
  ]
}

Extract ALL entities and relationships. Return ONLY JSON."""

# Prompt para documentos de saúde geral
HEALTH_PROMPT = """Extract entities and relationships from this health/wellness text.

Focus on: conditions, diseases, symptoms, treatments, medications, professionals, facilities, lifestyle factors.

Return ONLY this JSON:
{
  "nodes": [
    {"id": "entity_id", "type": "EntityType", "properties": {"description": "what is this"}}
  ],
  "relationships": [
    {"source": "id1", "target": "id2", "type": "RELATIONSHIP", "properties": {"description": "how they relate"}}
  ]
}

Extract ALL entities and relationships. Return ONLY JSON."""

# Prompt para documentos de tecnologia da informação
IT_PROMPT = """Extract entities and relationships from this IT/technology text.

Focus on: languages, frameworks, databases, tools, architectures, services, infrastructure, security, teams, projects.

Return ONLY this JSON:
{
  "nodes": [
    {"id": "entity_id", "type": "EntityType", "properties": {"description": "what is this"}}
  ],
  "relationships": [
    {"source": "id1", "target": "id2", "type": "RELATIONSHIP", "properties": {"description": "how they relate"}}
  ]
}

Extract ALL entities and relationships. Return ONLY JSON."""

# Dicionário de prompts por tipo
PROMPTS_BY_TYPE = {
    "generic": GENERIC_PROMPT,
    "legal": LEGAL_PROMPT,
    "medical": MEDICAL_PROMPT,
    "technical": TECHNICAL_PROMPT,
    "financial": FINANCIAL_PROMPT,
    "aesthetics": AESTHETICS_PROMPT,
    "health": HEALTH_PROMPT,
    "it": IT_PROMPT,
}

def get_prompt(doc_type: str = "generic") -> str:
    """Retorna o prompt para o tipo de documento"""
    return PROMPTS_BY_TYPE.get(doc_type.lower(), GENERIC_PROMPT)
