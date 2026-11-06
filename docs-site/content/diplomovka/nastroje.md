---
title: "3. Existujúce nástroje"
weight: 3
description: "Posúdenie nástrojov na automatizované hodnotenie, analytiku a kontrolu zmien"
---
{{< details >}}
- Pre: Čitateľ práce
- Vyžaduje: Nič
{{< /details >}}
Pri každom nástroji práca hľadá odpoveď na tri otázky: či už úlohu nerieši celú,
čo sa z neho oplatí prevziať a či sa dá priamo zapojiť. Posudzuje sa, či pracuje
nad existujúcim GitLabom, či sleduje kroky jednotlivca, či ukazuje stav naprieč
projektmi kurzu, či sa dá nastaviť podľa pravidiel predmetu a či sa od výsledku
dá dostať k pôvodnému údaju.

| Nástroj | Nad GitLabom | Proces | Kurz | Konfig. | Detail |
|---|:---:|:---:|:---:|:---:|:---:|
| Artemis | ~ | ✓ | ✓ | ✓ | ✓ |
| GitHub Classroom | × | ~ | ✓ | ~ | ✓ |
| Analytika GitLabu | ✓ | ~ | × | × | ✓ |
| Danger | ✓ | ~ | × | ✓ | ✓ |
| SonarQube | ✓ | × | × | ✓ | ✓ |

*✓ priamo podporované, ~ čiastočne alebo po doplnení, × nie je cieľom nástroja.*

**Artemis a GitHub Classroom** si zadania a repozitáre zakladajú samy zo šablóny.
Projekty predmetov však vznikajú v GitLabe katedry mimo hodnotiaceho systému,
takže ich nasadenie by prácu presunulo mimo reálny nástroj.

**Analytika GitLabu** meria objem činnosti v jednom projekte alebo skupine.
Pojem kurzu ani pravidlá predmetu nepozná. GitPulse od nej preberá väzbu každého
výsledku na pôvodný objekt.

**Danger a SonarQube** vidia jednu zmenu alebo jeden projekt a ich nasadenie by
vyžadovalo zásah do každého študentského repozitára. Od Dangeru GitPulse preberá
zrozumiteľné zdôvodnenie výsledku, od SonarQube nastaviteľnú bránu s prahmi
určenými tým, kto nástroj nasadzuje.

Žiadny nástroj nedáva prehľad o plnení procesných požiadaviek naprieč projektmi
kurzu. Preto vznikla samostatná vrstva nad GitLabom, ktorá študentské repozitáre
iba číta.
