---
title: "Úvod"
nav_title: "Úvod"
description: "Úvod do GitPulse"
---
{{< details >}}
- Pre: Všetci
- Vyžaduje: Nič
{{< /details >}}
GitPulse je platforma pre transparentné a škálovateľné hodnotenie tímovej práce v GitLab projektoch.

## Hlavný cieľ

Nahradiť manuálne a subjektívne hodnotenie merateľným procesom postaveným na dátach:

- automatický zber udalostí
- konzistentné compliance pravidlá
- auditovateľné výstupy pre učiteľa

```mermaid
flowchart TB
    A["GitLab aktivita študentov"] --> B["Webhook ingestion"]
    B --> C["Spracovanie v workeroch"]
    C --> D["Compliance checks (R01-R13)"]
    D --> E["Dashboard + export dát"]
    E --> F["Objektívnejšie hodnotenie"]
```

## Pre koho je dokumentácia určená

- učitelia: interpretácia metrík a rozhodovanie
- vývojári: implementácia, testovanie, release proces
- operátori: nasadenie, monitoring, incident response

## Ďalšie kroky

- [Prehľad projektu](prehlad.md)
- [Ciele diplomovej práce](ciele.md)
- [Architektúra systému](architektura.md)
