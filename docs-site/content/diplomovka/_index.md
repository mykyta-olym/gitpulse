---
title: "Diplomová práca"
nav_title: "Diplomovka"
description: "Prehľad diplomovej práce podľa aktuálneho textu v thesis repozitári"
---
{{< details >}}
- Pre: Čitateľ práce
- Vyžaduje: Nič
{{< /details >}}
**Téma:** Nástroje pre podporu výučby základov DevOps<br />
**Autor:** Bc.&nbsp;Mykyta Olym<br />
**Vedúci práce:** Ing.&nbsp;Sergej Chodarev,&nbsp;PhD.<br />
**Študijný program:** Informatika<br />
**Aktuálna etapa:** 4. priebežné odovzdanie, 1. 11. 2026 (realizácia riešenia a metódy vyhodnotenia)

---

## Abstrakt

V tímových zadaniach predmetov Základy softvérového inžinierstva a Základy DevOps
sa hodnotí aj pracovný postup študenta, no dôkaz o ňom je v systéme GitLab
rozptýlený medzi tikety, vetvy, žiadosti o zlúčenie, diskusie, commity a procesy
CI/CD. Práca rozkladá požiadavky obidvoch zadaní na trinásť strojovo overiteľných
otázok, pri každej pomenúva hranicu interpretácie a porovnáva existujúce nástroje.
Overenie rozhraní GitLabu určilo, ktoré údaje prináša webhook, ktoré treba
doplniť cez REST a ktoré nie sú dostupné vôbec. Na tomto základe vznikla platforma
GitPulse riadená udalosťami z GitLabu, ku ktorej patrí voliteľný asistent cvičení.
Posledná časť práce opisuje, ako sa riešenie vyhodnotí s cvičiacimi a študentmi.

**Kľúčové slová:** DevOps, GitPulse, GitLab, webhooky, hodnotenie pracovného postupu, recenzia kódu, vzdelávanie v softvérovom inžinierstve

---

## Obsah práce

  - [1. Úvod](./uvod/) - problém, motivácia a formulácia úlohy.
  - [2. Analýza tímových zadaní](./analyza/) - požiadavky predmetov a kontroly R01 až R13.
  - [3. Existujúce nástroje](./nastroje/) - Artemis, GitHub Classroom, analytika GitLabu, Danger a SonarQube.
  - [4. Získavanie údajov z GitLabu](./preskumanie/) - webhooky, REST API a hranice interpretácie.
  - [5. Návrh platformy GitPulse](./navrh/) - scenáre, architektúra, výpočet kontrol a asistent.
  - [6. Realizácia riešenia](./realizacia/) - technológie, hlavné časti, priebeh kontroly a kvalita.
  - [7. Metódy vyhodnotenia](./vyhodnotenie/) - čo, ako a s kým sa bude merať.
  - [8. Záver](./zaver/) - prínosy, splnenie cieľov a ďalší postup.

---

{{< alert type="note" >}}
**Zdroj pravdy.** Táto sekcia stručne sprevádza aktuálnym textom práce. Úplný text je v LaTeX zdroji v repozitári [`dp.mykyta.olym/thesis`](https://gitlab.example.com/kpi-zp/2027/dp.mykyta.olym/thesis). Pri rozdiele má prednosť LaTeX zdroj.
{{< /alert >}}
