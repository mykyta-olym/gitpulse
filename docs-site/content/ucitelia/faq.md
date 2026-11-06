---
title: "Často kladené otázky"
description: "FAQ pre učiteľov používajúcich GitPulse"
---
{{< details >}}
- Pre: Učiteľ
- Vyžaduje: Účet v GitPulse s rolou inštruktora
{{< /details >}}
## Všeobecné otázky

### Čo je GitPulse?

GitPulse je nástroj na automatickú analýzu aktivity študentov na GitLab projektoch. Poskytuje objektívne metriky pre hodnotenie tímovej práce a DevOps praktík.

### Kto môže GitPulse používať?

GitPulse je určený primárne pre učiteľov a cvičiacich. Prihlásenie prebieha cez školský GitLab (OAuth) - účet sa vytvorí automaticky pri prvom prihlásení. Rolu (napr. inštruktor) môže zmeniť administrátor.

### Aké dáta GitPulse zbiera?

GitPulse zbiera verejne dostupné dáta z GitLab projektov:

- Commit históriu
- Merge requesty a code review komentáre
- Pipeline výsledky a test coverage
- Issues
- Členov projektu/skupiny

{{< alert type="note" >}}
**Čo nezbierame.** GitPulse nezbiera obsah súkromných správ, lokálne dáta študentov, ani nemonitoruje ich aktivitu mimo GitLab. AI obohatenie spracováva len agregované metriky - osobné údaje sú automaticky redakované.
{{< /alert >}}
---

## Import a synchronizácia

### Ako importovať kurz z GitLabu?

1. Na dashboarde kliknite **"Import z GitLabu"**
2. Vložte URL:
      - **URL skupiny** - importuje všetky podskupiny (tímy) a projekty
      - **URL projektu** - importuje iba jeden projekt
3. Vyplňte názov kurzu a semester
4. Kliknite **"Importovať"**

### Prečo sa importoval celý rodičovský group?

Ak vložíte URL skupiny, GitPulse importuje všetky podskupiny ako tímy. Ak chcete importovať iba jeden projekt, uistite sa, že vkladáte URL konkrétneho **projektu**, nie skupiny.

### Prečo nevidím aktivitu tímu?

**Možné príčiny:**

1. **Synchronizácia ešte neprebehla**
   - Skontrolujte globálny status bar - synchronizácia môže ešte prebiehať
   - Kliknite **"Synchronizovať"** na stránke kurzu

2. **Projekt nie je v kurze**
   - Skontrolujte, či je projekt pridaný v GitPulse

3. **Oneskorenie spracovania**
   - Pri vysokej záťaži môže byť oneskorenie do niekoľkých minút

### Čo synchronizácia sťahuje?

- Commity, Merge Requests, Issues, Pipeline výsledky
- Členov projektu (automatická detekcia študentov)
- Code review komentáre
- Test coverage dáta

### Prečo status bar ukazuje zlé čísla?

Status bar sa aktualizuje každé 2 sekundy. Staré úlohy (staršie ako 3 minúty) sú automaticky vyčistené. Ak vidíte nesprávne počty, obnovte stránku.

---

## Metriky a hodnotenie

### Čo znamená compliance skóre?

Compliance skóre (0-100 %) vyjadruje, nakoľko tím dodržiava definované DevOps praktiky. Skladá sa z 13 vstavaných kontrol (R01-R13) plus voliteľných vlastných kontrol. Počítajú sa len zapnuté kontroly a súčet ich čiastkových skóre sa delí súčtom ich váh.

### Sú prahy konfigurovateľné?

Áno. V nastaveniach kurzu môžete zmeniť:

- **Zelený prah** (predvolene 80 %) - tím spĺňa požiadavky
- **Žltý prah** (predvolene 50 %) - vyžaduje pozornosť
- Zmeny sa okamžite prejavia na dashboarde

### Je compliance skóre absolútna známka?

**Nie.** Compliance skóre je len jeden z indikátorov. Mali by ste ho kombinovať s:

- Kvalitou výstupov (demo, kód)
- Prezentáciou projektu
- Individuálnym rozhovorom
- Peer evaluation

### Ako interpretovať nízke skóre v jednej kategórii?

Nízke skóre v kategórii môže znamenať:

1. **Skutočný problém** - tím ignoruje danú praktiku
2. **Odlišný workflow** - legitímny dôvod (napr. pair programming)
3. **Technický problém** - dáta nie sú správne zbierané
4. **Chýbajúca konfigurácia** - napr. chýba CI/CD v projekte

{{< alert type="note" >}}
**Best Practice.** Vždy overte nízke skóre rozhovorom s tímom.
{{< /alert >}}
---

## Roly a scoring

### Čo znamenajú farebné odznaky pri menách členov?

Odznaky zobrazujú GitLab rolu člena tímu. Farby zodpovedajú úrovni prístupu:

- **Owner** (žltá) - najvyššia úroveň (50)
- **Maintainer** (modrá) - úroveň 40
- **Developer** (šedá) - úroveň 30
- **Reporter/Guest** (svetlošedá) - úroveň 20/10

### Čo znamená "(not in team score)"?

Tento štítok znamená, že člen nie je zahrnutý do tímového compliance skóre. Dôvody:

1. **Nízka rola bez aktivity** - Guest alebo Reporter, ktorý nevytvoril žiadny commit, MR, issue ani review
2. **Dedený prístup bez aktivity** - člen zdedil prístup cez nadskupinu, ale nemá žiadnu aktivitu v projekte
3. **Inštruktor** - učiteľ/cvičiaci pridaný ako `is_teacher`

### Čo je "inherited" členstvo?

Člen s odznakom "inherited" získal prístup k projektu/skupine nie priamo, ale zdedením z nadradskupiny GitLab. Ak nemá žiadnu aktivitu, je automaticky vylúčený z tímového skóre.

### Prečo má môj tím nižšie skóre ako som čakal?

Skontrolujte, či nemáte neaktívnych členov, ktorí znižujú priemer. GitPulse teraz automaticky vylučuje Guest/Reporter bez aktivity a inherited členov bez aktivity, ale Developer+ s nulovou aktivitou sa stále počíta do skóre.

### Čo robí tlačidlo "Re-check"?

Tlačidlo spustí okamžité prepočítanie compliance metrik tímu. Na rozdiel od bežného prepočtu spúšťa **všetky** kontroly (R01-R13 + vlastné), aj keď sú niektoré filtované v aktuálnom týždni kurzu.

---

## Akademická integrita

### Ako riešiť podozrivú aktivitu?

GitPulse zobrazuje dáta potrebné na manuálnu kontrolu: časovú os commitov, issues, MR, review a CI. Ak vidíte veľa generických commitov, formálne review bez obsahu alebo nezvyčajné rozdelenie práce, overte detail v GitLabe a až potom robte záver.

### Čo dokumentovať?

1. **Konkrétne odkazy** - issue, MR, commit alebo pipeline
2. **Kontext** - deadline, typ úlohy, dohodnutý workflow
3. **Vysvetlenie študenta** - ak bolo poskytnuté
4. **Rozhodnutie učiteľa** - podľa pravidiel kurzu

---

## Konfigurácia a export

### Ako zdieľať nastavenia medzi kurzami?

Použite **JSON export/import**:

1. Na zdrojovom kurze kliknite **"Export JSON"**
2. Na cieľovom kurze kliknite **"Import JSON"** a nahrajte súbor
3. JSON obsahuje compliance kontroly, termíny a prahy

### Môžem pridávať vlastné kontroly?

Áno. GitPulse podporuje vlastné kontroly (C01+) s konfigurovateľnými pravidlami a váhami.

---

## Súkromie a GDPR

### Aké sú práva študentov?

Podľa GDPR majú študenti právo na:

- **Prístup** - môžu požiadať o svoje dáta
- **Opravu** - ak sú dáta nesprávne
- **Výmaz** - v odôvodnených prípadoch
- **Prenosnosť** - export dát v štandardnom formáte

### Ako dlho sa dáta uchovávajú?

Dáta sa uchovávajú počas trvania akademického kurzu plus 6 mesiacov pre prípad odvolaní. Potom sú automaticky zmazané.

### Čo s AI obohatením a súkromím?

AI obohatenie spracováva len agregované metriky (počet commitov, MR, atď.), nie obsah kódu. Osobné údaje študentov (mená, emaily) sú automaticky redakované pred odoslaním do AI modelu.

---

## Problémy a podpora

### Dashboard je pomalý

**Riešenia:**

1. Obnovte stránku (F5)
2. Vyčistite cache prehliadača
3. Skúste iný prehliadač
4. Nahláste problém administrátorovi

### Ako nahlásiť bug?

1. Použite **in-app podporu** na [gitpulse.kpi.fei.tuke.sk/dashboard/support](https://gitpulse.kpi.fei.tuke.sk/dashboard/support)
2. Priložte screenshot a kroky na reprodukciu
3. Uveďte prehliadač a operačný systém

---

## Kontakty

| Typ podpory | Kontakt |
|-------------|---------|
| Technická podpora | [mykyta.olym.work@gmail.com](mailto:mykyta.olym.work@gmail.com) |
| Bug reports | [Podpora v systéme](https://gitpulse.kpi.fei.tuke.sk/dashboard/support) |
| Feature requests | [Podpora v systéme](https://gitpulse.kpi.fei.tuke.sk/dashboard/support) |
| Dokumentácia | Táto stránka |
