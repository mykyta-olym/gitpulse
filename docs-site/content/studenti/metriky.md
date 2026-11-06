---
title: "Pochopenie metrík"
description: "Vysvetlenie compliance pravidiel R01-R13 pre študentov"
---
{{< details >}}
- Pre: Študent
- Vyžaduje: Školský GitLab účet
{{< /details >}}
GitPulse hodnotí váš projekt pomocou 13 pravidiel dodržiavania predpisov (compliance pravidlá R01-R13). Tieto pravidlá sú navrhnuté tak, aby overovali uplatňovanie osvedčených DevOps praktík, kvalitu workflow a spoluprácu v tíme.

## Prehľad pravidiel

| Pravidlo | Kód | Čo sleduje | Prečo je to dôležité |
|---|---|---|---|
| **Issue Assigned** | R01 | Priradenie issue študentovi | Každý člen tímu by mal vlastniť konkrétnu úlohu. |
| **Branch + MR Created** | R02 | Feature branch a otvorenie MR | Kód by sa nemal pushovať priamo do vetvy `main`. |
| **Tests Written** | R03 | Zmeny v testovacích súboroch | Kód bez testov sa nepovažuje za dokončený. |
| **MR Linked to Issue** | R04 | Prepojenie MR a prislúchajúcej issue | Traceabilita - schopnosť spätne dohľadať dôvod zmeny. |
| **MR Description** | R05 | Popis v Merge Requeste | Ostatní členovia tímu musia rozumieť, čo MR mení a ako to otestovať. |
| **Code Review Received** | R06 | Prijatie zmysluplného peer review | Zabraňuje zlúčeniu kódu bez kontroly kolegami (min. 2 recenzenti). |
| **Code Review Given** | R07 | Poskytnutie zmysluplného peer review | Vývoj softvéru je tímová práca; recenzovanie kódu kolegov je kľúčové. |
| **Review Response** | R08 | Odpovede na pripomienky v diskusii | Diskusie v MR nesmú ostať ignorované. |
| **MR Approved** | R09 | Získanie formálneho schválenia | MR musí získať schválenie pred zlúčením do `main`. |
| **Merged by Author** | R10 | Zlúčenie MR autorom | Vývojár by mal dokončiť svoj workflow a sám zlúčiť schválený kód. |
| **MR + Issue Closed** | R11 | Uzavretie MR aj prislúchajúcej issue | Udržiavanie čistého stavu úloh a tabule projektu. |
| **Pipeline Green** | R12 | Úspešný beh CI/CD pipeline | Kód musí úspešne prejsť automatickými testami v GitLab CI. |
| **Commit Quality** | R13 | Používanie lokálneho Git workflow | Minimalizuje sa priama editácia súborov cez webový editor GitLabu. |

---

## Compliance skóre

Vaše celkové compliance skóre je vážený priemer všetkých aktívnych pravidiel. Učiteľ kurzu určuje váhy jednotlivých pravidiel. Nižšie skóre indikuje procesné nedostatky alebo porušenie workflow, ktoré môžu viesť k horšiemu celkovému hodnoteniu tímu.

### Stupňovanie stavu

| Indikátor | Skóre | Význam |
|---|---|---|
| :green_heart: **Zelený (OK)** | 80 - 100 % | Tím ukážkovo dodržiava DevOps procesy a spolupracuje. |
| :yellow_heart: **Žltý (Warning)** | 50 - 79 % | Niektoré procesy alebo jednotlivci zaostávajú a vyžadujú pozornosť. |
| :heart: **Červený (Critical)** | 0 - 49 % | Vážne procesné chyby, chýbajúca spolupráca alebo nesprávne vetvenie. |

---

## Detaily pravidiel

### R01 - Issue Assigned (Priradená úloha)
{{< alert type="note" >}}
**Čo systém kontroluje.** Sleduje sa, či máte v GitLab projekte priradenú aspoň **1 issue** (predvolená konfigurácia). Každý vývojár musí niesť zodpovednosť za konkrétne úlohy.
{{< /alert >}}
**Ako splniť:**
- Pred začatím práce si v GitLabe vytvorte alebo priraďte issue.
- Nenechávajte úlohy nepriradené alebo priradené iba jednému ("hlavnému") členovi tímu.

### R02 - Branch + MR Created (Feature vetva)
{{< alert type="note" >}}
**Čo systém kontroluje.** Sleduje sa, či pracujete na vlastnej feature vetve a otvárate Merge Request. Ak učiteľ zapne prísny režim (`require_branch_convention=true`), názov vetvy musí zodpovedať maske (napr. `issue-123-popis`).
{{< /alert >}}
**Ako splniť:**
- Nikdy nepushujte kód priamo do vetvy `main` alebo `master`.
- Založte si vetvu napr. `issue-42-login` a z nej otvorte Merge Request.

### R03 - Tests Written (Napísané testy)
{{< alert type="note" >}}
**Čo systém kontroluje.** Sleduje sa, či aspoň jeden z vašich MR obsahuje zmeny v testovacích súboroch (súbory zodpovedajúce predvolenej maske, napr. `*test*`, `tests/` atď.).
{{< /alert >}}
**Ako splniť:**
- Súčasťou vašich zmien v MR musí byť aj pridanie alebo aktualizácia testov.

### R04 - MR Linked to Issue (Prepojenie MR na úlohu)
{{< alert type="note" >}}
**Čo systém kontroluje.** MR musí explicitne odkazovať na issue, ktorú rieši. Prepojenie je možné vykonať buď názvom zdrojovej vetvy (napr. `issue-42-login`), alebo textom v popise MR (napr. `Closes #42`, `Fixes #42`).
{{< /alert >}}
**Ako splniť:**
- Pri otváraní MR uveďte do popisu text typu `Closes #XYZ` (kde XYZ je číslo issue).

### R05 - MR Description (Zmysluplný popis MR)
{{< alert type="note" >}}
**Čo systém kontroluje.** Popis Merge Requestu musí mať dostatočnú kvalitu - minimálne **10 slov** po očistení od markdown syntaxe. Ak je to vyžadované, popis musí obsahovať aj predpísané sekcie (napr. `## Description` a `## Testing`).
{{< /alert >}}
**Ako splniť:**
- Napíšte jasný popis toho, čo MR mení a ako to overiť. Vyhnite sa jednoslovným popisom ako "fix" alebo "changes".

### R06 - Code Review Received (Prijaté code review)
{{< alert type="note" >}}
**Čo systém kontroluje.** Pravidlo sleduje, či vaše MR dostali zmysluplnú spätnú väzbu od aspoň **2 rôznych spolužiakov**.
{{< /alert >}}

*Poznámka: Hodnotenie podporuje **čiastočné skóre**. Ak získate review len od 1 spolužiaka, dostanete 50 % z váhy tohto pravidla. Komentáre musia byť zmysluplné (predvolene minimálne 15 slov).*
**Ako splniť:**
- Pred zlúčením MR požiadajte kolegov o kontrolu kódu. Zlúčenie bez diskusie znižuje vaše skóre.

### R07 - Code Review Given (Poskytnuté code review)
{{< alert type="note" >}}
**Čo systém kontroluje.** Sleduje sa vaša aktivita ako recenzenta. Musíte poskytnúť zmysluplné pripomienky na MR svojich kolegov (predvolene aspoň **2 rôzne MR** a každé vyjadrenie musí mať aspoň **15 slov**).
{{< /alert >}}
**Ako splniť:**
- Aktívne prezerajte kód spolužiakov. Píšte konštruktívne a detailné pripomienky, nie len jednoslovné súhlasy ("lgtm", "+1").

### R08 - Review Response (Reakcia na pripomienky)
{{< alert type="note" >}}
**Čo systém kontroluje.** Ak vám kolegovia zanechajú pripomienky na vašom MR, musíte na ne odpovedať alebo ich vyriešiť (resolve thread). Ak na MR nemáte žiadne vlákna, pravidlo automaticky prechádza ako splnené. Na komentáre bot účtov, napríklad asistenta cvičení, odpovedať nemusíte.
{{< /alert >}}
**Ako splniť:**
- Reagujte na pripomienky v diskusných vláknach, vysvetlite zmeny alebo pridajte referenciu na opravný commit.

### R09 - MR Approved (Schválenie MR)
{{< alert type="note" >}}
**Čo systém kontroluje.** Sleduje sa, či váš MR získal aspoň **1 formálne schválenie (Approve)**. Ak je zapnutá konfigurácia `count_merged_as_approval`, zlúčený MR sa považuje za schválený.
{{< /alert >}}
**Ako splniť:**
- Požiadajte kolegov, aby po úspešnom review klikli na tlačidlo **Approve** v GitLab rozhraní.

### R10 - Merged by Author (Zlúčenie autorom)
{{< alert type="note" >}}
**Čo systém kontroluje.** Vývojár, ktorý kód napísal a MR vytvoril, by ho mal po schválení aj sám zlúčiť.
{{< /alert >}}
**Ako splniť:**
- Po obdržaní schválení a úspešnom zbehnutí pipeline zlúčte (merge) svoj Merge Request sami. Nenechávajte zlúčenie na kolegov, ak ste autorom.

### R11 - MR + Issue Closed (Uzavretie úloh)
{{< alert type="note" >}}
**Čo systém kontroluje.** Po zmergovaní MR musí dôjsť aj k uzavretiu priradenej GitLab issue. Systém overuje, či je prepojená dvojica úspešne uzavretá.
{{< /alert >}}
**Ako splniť:**
- Použite kľúčové slová v popise MR (napr. `Closes #XYZ`), ktoré automaticky zatvoria issue po zlúčení, alebo issue zatvorte manuálne hneď po zmergovaní kódu.

### R12 - Pipeline Green (Funkčné CI/CD)
{{< alert type="note" >}}
**Čo systém kontroluje.** Sleduje sa, či vetva, z ktorej MR vychádza, úspešne prešla buildom a automatickými testami (CI pipeline je zelená) a či testovací job reálne bežal.
{{< /alert >}}
**Ako splniť:**
- Uistite sa, že váš projekt má nakonfigurovaný súbor `.gitlab-ci.yml`.
- Opravujte chyby kompilácie a testov okamžite, keď pipeline zlyhá.

### R13 - Commit Quality (Kvalita commitov)
{{< alert type="note" >}}
**Čo systém kontroluje.** Overuje sa, či pracujete v lokálnom prostredí cez Git CLI a pushujete zmeny. Sleduje sa pomer commitov vykonaných cez GitLab webový editor (Web IDE). Pomer nesmie prekročiť **30 %**.
{{< /alert >}}
**Ako splniť:**
- Klonujte si repozitár lokálne a pracujte vo vašom lokálnom IDE (napr. VS Code).
- Webový editor GitLabu používajte len výnimočne na drobné opravy chýb v dokumentácii.

---

## Často kladené otázky (FAQ)

{{< alert type="note" >}}
**Môžem vidieť detaily výpočtu môjho skóre?.** Áno, po kliknutí na compliance skóre vášho tímu na nástenke uvidíte zoznam pravidiel, ich stav (Splnené / Nesplnené / Čiastočne splnené), váhu a získané body.
{{< /alert >}}
{{< alert type="note" >}}
**Prečo mi systém ukazuje 0 % za pravidlo R06, keď som dostal komentár?.** Spätná väzba od spolužiakov musí byť zmysluplná. Krátke komentáre typu "+1", "LGTM" alebo prázdne pripomienky systém nepočíta. Minimálna dĺžka pre zmysluplný komentár je štandardne 15 slov.
{{< /alert >}}
{{< alert type="note" >}}
**Čo sa stane, ak sme v tíme iba dvaja alebo sám (sólo tím)?.** Compliance engine automaticky rozpozná sólo tímy. Pri pravidlách zameraných na spoluprácu (napr. Code Review Given R07, Code Review Received R06) systém automaticky udelí plný počet bodov, aby ste neboli penalizovaní za chýbajúcich spoluhráčov.
{{< /alert >}}