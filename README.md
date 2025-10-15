# yugioh-card-finding-assistant
Yugioh Card Finding Assistant
## Use Case
Ein intelligenter Assistent zur schnellen und semantischen Suche nach Yu-Gi-Oh!-Karten anhand von natürlicher Sprache.

## Introduction

### Problem Statement
Das Sammelkartenspiel Yu-Gi-Oh! umfasst mittlerweile mehrere zehntausend Karten, die sich in Effekte, Typen, Attribute und komplexe Interaktionen unterscheiden.  
Es ist für Spieler:innen oft schwierig, in kurzer Zeit die passende Karte für eine bestimmte Spielsituation oder Strategie zu identifizieren.  
Herkömmliche Suchmethoden, wie Schlagwortsuche in Datenbanken, stoßen an ihre Grenzen, da semantische Zusammenhänge und Kontext (z. B. „Schutz vor Zerstörung“ oder „Karten, die Monster vom Friedhof zurückholen“) nicht zuverlässig erfasst werden.

### Motivation
Ein intelligentes Assistenzsystem kann Spieler:innen helfen, die Kartenauswahl zu vereinfachen, indem es natürliche Sprache versteht und passende Karten vorschlägt.  
Mit Large Language Models (LLMs) in Kombination mit Retrieval-Augmented Generation (RAG) lässt sich eine Brücke zwischen den unstrukturierten Kartenbeschreibungen und den individuellen Anfragen schlagen.  
Das Projekt bietet praktischen Nutzen für die Yu-Gi-Oh!-Community und ist technologisch relevant im Bereich NLP und semantische Suche.

### Goal
Ziel des Projekts ist die Entwicklung eines Prototyps, der:
- Eine umfangreiche Datenbasis von Yu-Gi-Oh!-Karten verarbeitet.
- Mithilfe von Embeddings und Vektorsuche relevante Karten zu einer Texteingabe findet.
- Ein LLM integriert, das die Ergebnisse aufbereitet, erklärt und priorisiert.
- Nutzer:innen eine einfache Schnittstelle bietet, um Anfragen in natürlicher Sprache zu stellen und passende Kartenempfehlungen zu erhalten.

## Methodology

### Data
**Dataset:** [Yu-Gi-Oh! TCG Complete Card Database](https://www.kaggle.com/datasets/hammadus/yugioh-full-card-database-index-august-1st-2025)  
**Anzahl der Einträge:** 13.396 Karten  

**Struktur der Karten:**
- `name`: Offizieller Name der Karte (String)  
- `description`: Beschreibung der Karte (String)  
- `set_id`: Set-ID der Karte (String)  
- `price`: Preis der Karte im offenen Markt (Float)  
- `volatility`: Preisvolatilität der Karte (String)  
- `type`: Typ der Karte (String)  
- `sub_type`: Untertyp der Karte (String)  
- `attribute`: Attribut der Karte (falls vorhanden) (String)  

### Preprocessing
- Duplikate entfernen, fehlende Werte ergänzen  
- Kategorien vereinheitlichen  
- Preise in Euro umrechnen  
- Aufteilen der Datenbank in Monster-, Zauber- und Fallenkarten  

### Experiments / Pipeline
1. **Input Guardrails:** Plausibilitätsprüfung, Entfernung von PII  
2. **Retriever:** Kombination aus Vektorsuche und Filter für relevante Karten  
3. **LLM Integration:** Formuliert verständliche Empfehlungen auf Basis der gefundenen Karten  
4. **Output Guardrails:** Empfehlungen bleiben korrekt, keine erfundenen Karten  
5. **Formatter:** Formatierung des Outputs (z. B. Pydantic-Modell oder YAML-Schema)  
6. **Frontend:** Streamlit-Web-App für direkte Eingabe von Fragen  

## Results
- Nutzer:innen erhalten klare, personalisierte Empfehlungen statt nur Tabellen  
- Kombination von Retriever und LLM sorgt für Verständlichkeit und Zuverlässigkeit  
- Der Assistent erleichtert die Suche erheblich, spart Zeit und reduziert Frust  

## References
- **Dataset:** [Kaggle – Yu-Gi-Oh! Karten](https://www.kaggle.com/datasets/hammadus/yugioh-full-card-database-index-august-1st-2025)  
- **LLMs:** [Mistral-7B](https://huggingface.co/mistralai/Mistral-7B-v0.1)  
- **Vector Search:** [Weaviate](https://weaviate.io/), [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)  
- **Database:** [PostgreSQL](https://www.postgresql.org/)  
- **Guardrails:** [Microsoft Presidio](https://github.com/microsoft/presidio), [NeMo Guardrails](https://github.com/NVIDIA-NeMo/Guardrails)  
- **Frameworks / Tools:** FastAPI, Streamlit, LangChain, Docker Compose  
- **Hosting / API:** Hugging Face Inference API oder lokal über FastAPI  

---
