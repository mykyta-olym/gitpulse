---
title: "FAQ pre študentov"
description: "Často kladené otázky pre študentov GitPulse"
---
{{< details >}}
- Pre: Študent
- Vyžaduje: Školský GitLab účet
{{< /details >}}
## Prístup a prihlásenie

{{< alert type="note" >}}
**Ako sa prihlásim do GitPulse?.** Navštívte [gitpulse.kpi.fei.tuke.sk](https://gitpulse.kpi.fei.tuke.sk/) a kliknite na **Prihlásiť sa cez GitLab**. Budete presmerovaní na GitLab, kde autorizujete prístup.
{{< /alert >}}
{{< alert type="note" >}}
**Nevidím žiadne kurzy ani projekty po prihlásení. Čo mám robiť?.** Váš učiteľ vás musí najprv pridať do kurzu v GitPulse. Kontaktujte svojho učiteľa alebo cvičiaceho.
{{< /alert >}}
{{< alert type="note" >}}
**Môžem pristupovať k GitPulse z mobilu?.** Áno, GitPulse je responzívna webová aplikácia a funguje v mobilnom prehliadači. Pre najlepší zážitok odporúčame desktop verziu.
{{< /alert >}}
{{< alert type="note" >}}
**Môj avatar alebo meno je nesprávne. Ako ho zmením?.** GitPulse synchronizuje vaše údaje z GitLabu. Zmeňte avatar alebo meno v nastaveniach profilu na [gitlab.example.com](https://gitlab.example.com) a údaje sa aktualizujú pri ďalšej synchronizácii.
{{< /alert >}}
## Metriky a hodnotenie

{{< alert type="note" >}}
**Čo je compliance skóre?.** Compliance skóre je percentuálne vyjadrenie toho, ako dobre váš tím dodržiava osvedčené DevOps praktiky. Vyššie skóre znamená lepšie praktiky. Viac v sekcii [Pochopenie metrík](metriky.md).
{{< /alert >}}
{{< alert type="note" >}}
**Je compliance skóre mojou známkou?.** Nie. Compliance skóre je podkladom pre učiteľa, ktorý o konečnom hodnotení rozhoduje samostatne. Učiteľ môže zohľadniť aj ďalšie faktory.
{{< /alert >}}
{{< alert type="note" >}}
**Prečo je moje individuálne skóre nízke?.** Skontrolujte na dashboarde rozpis pravidiel. Najčastejšie dôvody:
{{< /alert >}}

- Málo commitov alebo nerovnomerné rozloženie v čase
- Chýbajúce issues alebo merge requesty
- Nefunkčný CI/CD pipeline
- Neprepojené commity s issues
{{< alert type="note" >}}
**Kedy sa aktualizujú metriky?.** Metriky sa aktualizujú po každej synchronizácii s GitLabom, zvyčajne do niekoľkých minút po push, vytvorení issue alebo merge requestu.
{{< /alert >}}
{{< alert type="note" >}}
**Môže učiteľ prepísať automatické hodnotenie?.** Áno. Compliance skóre je iba podklad; učiteľ môže zohľadniť manuálnu kontrolu kódu, demo, obhajobu a pravidlá konkrétneho kurzu.
{{< /alert >}}
## Práca s GitLabom

{{< alert type="note" >}}
**Aké GitLab akcie GitPulse sleduje?.** GitPulse sleduje: commity, issues, merge requesty, CI/CD pipeline, komentáre a review na merge requestoch, a branch operácie.
{{< /alert >}}
{{< alert type="note" >}}
**Sleduje GitPulse aj súkromné repozitáre?.** GitPulse pristupuje len k projektom, ktoré učiteľ zaregistroval v kurze. Vaše osobné alebo iné projekty nie sú prístupné.
{{< /alert >}}
{{< alert type="note" >}}
**Počítajú sa commity na iných vetvách ako main?.** Áno, GitPulse sleduje aktivitu na všetkých vetvách registrovaného projektu.
{{< /alert >}}
{{< alert type="note" >}}
**Kto je bot, ktorý komentuje moje commity?.** Ak vyučujúci v kurze zapne asistenta cvičení, v GitLabe sa správa ako kolega na projekte. Je to bot účet kurzu (napríklad `group_123_bot_…`): komentuje commity a merge requesty, pridelí vám tiket cvičenia a pri cvičení s konfliktom pridá do projektu vlastný commit. Keď mu v merge requeste odpoviete komentárom, pozrie sa naň znova a odpíše. Jeho komentáre sa do hodnotenia nepočítajú, hodnotí sa vaša práca na tikete a merge requeste rovnako ako každá iná.
{{< /alert >}}
{{< alert type="note" >}}
**Čo ak som commitoval pod iným emailom?.** GitPulse mapuje commity podľa GitLab identity. Ak používate iný email v Git konfigurácii, commity nemusia byť správne priradené. Nastavte si správny email v Git:
{{< /alert >}}

```bash
git config user.email "vas.email@student.university.edu"
```
## Súkromie a bezpečnosť

{{< alert type="note" >}}
**Aké údaje GitPulse zbiera?.** GitPulse zbiera iba údaje z vašich GitLab projektov: commity, issues, merge requesty, pipeline výsledky. Nesleduje vašu aktivitu mimo GitLabu. Podrobnosti nájdete v [Ochrane osobných údajov](../pravne/ochrana-udajov.md).
{{< /alert >}}
{{< alert type="note" >}}
**Kto vidí moje dáta?.** Vaše dáta vidia: vy, členovia vášho tímu, a učitelia/cvičiaci kurzu. Iné tímy ani študenti nemajú prístup k vašim dátam.
{{< /alert >}}
{{< alert type="note" >}}
**Môžem požiadať o vymazanie svojich údajov?.** Áno, podľa GDPR máte právo na výmaz. Kontaktujte [mykyta.olym.work@gmail.com](mailto:mykyta.olym.work@gmail.com) s predmetom "Žiadosť o vymazanie údajov".
{{< /alert >}}
## Technické problémy

{{< alert type="note" >}}
**Dashboard sa nenačítava alebo je pomalý..** Skúste:
{{< /alert >}}

1. Obnoviť stránku (Ctrl+F5)
2. Vyčistiť cache prehliadača
3. Skúsiť iný prehliadač
4. Ak problém pretrváva, nahláste ho učiteľovi
{{< alert type="note" >}}
**Vidím chybu "403 Forbidden" alebo "Prístup zamietnutý"..** Toto znamená, že nemáte prístup k danému zdroju. Najčastejšie dôvody:
{{< /alert >}}

- Nie ste pridaní do kurzu - kontaktujte učiteľa
- Vaša session vypršala - odhláste sa a prihláste znova
- Pokúšate sa o prístup k cudziemu projektu

{{< alert type="note" >}}
**Emailové notifikácie mi neprichádzajú..** Skontrolujte priečinok spam/junk vo vašom emailovom klientovi. Notifikácie prichádzajú z adresy systému. Ak stále nič neprichádza, kontaktujte učiteľa.
{{< /alert >}}