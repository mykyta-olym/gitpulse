---
title: "Testovanie"
description: "Sprievodca testovaním projektu GitPulse"
---
{{< details >}}
- Pre: Vývojár
- Vyžaduje: Lokálne prostredie podľa príručky pre vývojárov
{{< /details >}}
Táto stránka popisuje aktuálny lokálny testovací workflow pre GitPulse.

## Základná sada

```bash
python scripts/build_bundle.py --check
python scripts/check_static_artifacts.py
ruff check src tests scripts
ruff format --check src tests scripts
mypy src/app
pytest -q
```

## Cielené spustenia

```bash
pytest tests/unit/
pytest tests/unit/test_compliance_engine.py
pytest tests/unit/test_sweep_automation.py -q
pytest tests/unit/test_compliance_history_and_support_feedback.py -q
pytest -m "not performance"
```

## Štruktúra testov

```text
tests/
+-- unit/
|   +-- test_compliance_engine.py
|   +-- test_dynamic_checks.py
|   +-- test_sweep_automation.py
|   +-- test_compliance_history_and_support_feedback.py
|   +-- test_security.py
|   +-- test_frontend_resilience.py
+-- integration/
+-- load/
```

## Frontend assety

Generované bundle súbory neupravujte ručne. Zdrojové zmeny patria do:

- `src/app/templates/static/js/_parts/`
- `src/app/templates/static/js/*.js`
- `src/app/templates/static/css/_parts/`
- `src/app/templates/static/css/pages/`

Potom rebuild do `dist/` (súbory s hashom v mene + `dist/manifest.json`; necommituje sa, Docker image a CI si ho postavia sami):

```bash
python scripts/build_bundle.py          # alebo --watch počas vývoja
python scripts/check_static_artifacts.py
```

## Regresné priority

- sync/job stavy naprieč navigáciou
- invalidácia cache po sync/import/webhook update
- server-rendered stránky bez zastaraných client-only placeholderov
- support formuláre a compliance a support schémy
- voliteľné LLM flow
