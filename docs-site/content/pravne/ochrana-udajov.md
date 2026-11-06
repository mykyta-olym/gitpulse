---
title: "Vyhlásenie o ochrane osobných údajov"
description: "Vyhlásenie o ochrane osobných údajov platformy GitPulse"
---
{{< details >}}
- Pre: Všetci
- Vyžaduje: Nič
{{< /details >}}
*Posledná aktualizácia: 20. októbra 2026*

---

## Úvod

V GitPulse berieme ochranu vašich osobných údajov a bezpečnosť informácií vážne. Toto vyhlásenie o ochrane osobných údajov (ďalej len "Vyhlásenie") vysvetľuje, ako Katedra počítačov a informatiky (KPI), Fakulta elektrotechniky a informatiky (FEI), Technická univerzita v Košiciach (TUKE) (ďalej len "Prevádzkovateľ", "my", "nás") spracúva vaše osobné údaje pri používaní platformy GitPulse (ďalej len "Služba").

"Osobné údaje," ako sa používajú v tomto Vyhlásení, sú informácie, ktoré identifikujú alebo môžu byť primerane priamo alebo nepriamo spojené s identifikovateľnou osobou.

Toto Vyhlásenie sa vzťahuje na webovú aplikáciu GitPulse dostupnú na [gitpulse.kpi.fei.tuke.sk](https://gitpulse.kpi.fei.tuke.sk) a všetky súvisiace služby vrátane webhook integrácií, e-mailových notifikácií a API endpointov.

---

## Aké osobné údaje GitPulse zhromažďuje?

### Informácie poskytnuté prostredníctvom autentifikácie

Keď sa prihlásite do GitPulse cez GitLab OAuth (Single Sign-On), získavame z univerzitnej inštancie GitLab nasledujúce údaje:

- Celé meno a zobrazované meno
- E-mailovú adresu
- GitLab používateľské meno a ID
- URL profilovej fotografie (avatar)

{{< alert type="note" >}}
**Heslá.** GitPulse nezhromažďuje, neukladá a nemá prístup k vášmu heslu do GitLabu. Autentifikácia je úplne zabezpečená poskytovateľom GitLab OAuth.
{{< /alert >}}
### Údaje o kurzoch a aktivite synchronizované z GitLabu

Na zabezpečenie funkcionalít správy kurzov a hodnotenia GitPulse synchronizuje z GitLab repozitárov nasledujúce údaje:

| Kategória údajov | Príklady |
|---|---|
| Git commity | Autor, správa, dátum, štatistiky zmien |
| Merge requesty | Názov, popis, recenzie, komentáre |
| Issues | Názov, popis, štítky, účastníci |
| CI/CD pipelines | Výsledky behu, logy úloh |
| Metadáta repozitára | Vetvy, tagy, milestony |
| Členstvo | Skupiny a projektové členstvo |

### Automaticky zhromažďované informácie

Pri používaní Služby automaticky zhromažďujeme obmedzené technické údaje nevyhnutné pre prevádzku:

- **IP adresu** - uchovávame v serverových logoch pre bezpečnosť a prevenciu zneužitia
- **Typ prehliadača** - z hlavičky User-Agent
- **Jazyková preferenciu** - pre zobrazenie správneho jazyka
- **Časové pečiatky** - prístupu a vykonaných akcií
- **Metadáta HTTP požiadaviek** - metóda, cesta, stavový kód, čas odozvy

{{< alert type="note" >}}
**Žiadne sledovanie.** GitPulse nepoužíva žiadne analytické služby, sledovacie pixely, nástroje na zaznamenávanie relácií ani technológie fingerprintingu.
{{< /alert >}}
### E-mailové notifikácie

Ak sú pre váš kurz povolené e-mailové notifikácie, spracúvame vašu e-mailovú adresu na doručenie:

- Uvítacích e-mailov pri zápise do kurzu
- Periodických správ o hodnotení a spätnej väzbe
- Administratívnych oznámení od vyučujúceho

Všetky e-maily obsahujú mechanizmus odhlásenia. Nesledujeme otvorenie e-mailov ani kliknutia na odkazy.

---

## Aké osobné údaje GitPulse nezhromažďuje?

GitPulse úmyselne nezhromažďuje citlivé osobné údaje, ako napríklad:

- Heslá alebo autentifikačné údaje
- Finančné alebo platobné informácie
- Biometrické údaje, zdravotné informácie alebo genetické údaje
- Politické názory, náboženské presvedčenie alebo členstvo v odboroch
- Údaje odhaľujúce rasový alebo etnický pôvod

{{< alert type="warning" >}}
**Údaje v repozitároch.** Uvedomujeme si, že používatelia môžu zahrnúť citlivé osobné údaje do správ commitov, popisov issues alebo iného voľného obsahu v repozitároch GitLab. Ak citlivé osobné údaje existujú v synchronizovanom obsahu repozitára, za ich spracovanie zodpovedá vlastník repozitára (váš vyučujúci).
{{< /alert >}}
GitPulse nie je určený pre osoby mladšie ako 16 rokov. Pozrite si sekciu [Ochrana súkromia detí](#ochrana-sukromia-deti) pre viac informácií.

---

## Ako GitPulse používa moje osobné údaje?

GitPulse zhromažďuje a spracúva osobné údaje na nasledujúce účely:

| Účel spracovania | Kategórie použitých údajov |
|---|---|
| Overenie vašej identity a poskytnutie prístupu k Službe | Informácie o účte (meno, e-mail, GitLab ID) |
| Zobrazenie vášho profilu v kurzoch | Informácie o účte, URL avataru |
| Synchronizácia a zobrazenie aktivity a pokroku v kurze | Údaje o kurzoch a aktivite z GitLabu |
| Generovanie automatizovanej spätnej väzby na DevOps praktiky | Commity, merge requesty, CI/CD pipeline dáta |
| Spätná väzba asistenta cvičení priamo v GitLabe, ak ho vyučujúci v kurze zapne | Commity, merge requesty, issues, GitLab používateľské meno |
| Umožnenie vyučujúcim hodnotiť prácu študentov | Údaje o aktivite, výsledky hodnotenia |
| Odosielanie e-mailových notifikácií o pokroku | E-mailová adresa, údaje o zápise |
| Udržovanie bezpečnosti Služby a prevencia zneužitia | IP adresa, prístupové logy |
| Zlepšovanie spoľahlivosti a výkonu Služby | Agregované, neidentifikujúce metriky |

---

## Právny základ spracovania

Keď naše spracúvanie podlieha Všeobecnému nariadeniu o ochrane údajov (GDPR), opierame sa o nasledujúce právne základy:

### Oprávnený záujem (článok 6(1)(f) GDPR)

- Poskytovanie funkcionalít hodnotenia a správy kurzov ako súčasť univerzitného vzdelávania
- Zabezpečenie bezpečnosti, dostupnosti a integrity Služby
- Generovanie agregovaných, neidentifikujúcich analytík na zlepšenie Služby

### Súhlas (článok 6(1)(a) GDPR)

- Odosielanie voliteľných e-mailových notifikácií o pokroku v kurze (súhlas môžete kedykoľvek odvolať odhlásením)
- Ukladanie nepodstatných cookies (jazyková preferencia)

### Plnenie úlohy vo verejnom záujme (článok 6(1)(e) GDPR)

- Spracúvanie údajov na účely vzdelávacieho hodnotenia ako súčasť verejnej misie univerzity

Voči spracúvaniu na základe oprávneného záujmu môžete kedykoľvek namietať kontaktovaním nás na adrese uvedenej v sekcii [Kontaktujte nás](#kontaktujte-nas).

---

## S kým GitPulse zdieľa moje údaje?

### Vyučujúci a administrátori kurzu

Vaše meno, e-mail, GitLab používateľské meno, aktivity v kurze a výsledky hodnotenia sú viditeľné pre vyučujúcich a administrátorov kurzov, do ktorých ste zapísaní. Toto je nevyhnutné pre vzdelávací účel Služby.

### Ostatní študenti

V rámci kurzu môžu ostatní zapísaní študenti vidieť vaše meno a avatar. Detailné údaje o aktivite a výsledky hodnotenia sú viditeľné iba pre vyučujúcich, pokiaľ nastavenia kurzu výslovne nepovoľujú vzájomný prístup.

### Univerzitná inštancia GitLab

GitPulse komunikuje s univerzitnou inštanciou GitLab na [gitlab.example.com](https://gitlab.example.com) za účelom synchronizácie údajov o kurzoch. Táto komunikácia využíva šifrované pripojenia a autentifikované API tokeny.

Ak vyučujúci v kurze zapne asistenta cvičení, GitPulse do projektov tímov aj zapisuje, a to cez bot účet, ktorý si kurz vytvorí v GitLabe. Bot komentuje commity a merge requesty, zakladá a zatvára issues cvičenia, pri cvičení s konfliktom pridá commit do vetvy a ak to vyučujúci povolí, merge request schváli a zlúči. Token bot účtu je uložený šifrovaný a študenti ho nikdy nevidia.

### Žiadne zdieľanie s tretími stranami

{{< alert type="note" >}}
**Vaše údaje sú v bezpečí.** GitPulse nepredáva, nepožičiava, nevymieňa ani inak nezdieľa vaše osobné údaje so žiadnymi externými spoločnosťami, inzerentmi, dátovými maklérmi alebo externými službami. Všetko spracúvanie údajov prebieha výlučne v rámci univerzitnej infraštruktúry Technickej univerzity v Košiciach.
{{< /alert >}}

Panel Podpora a návrhy odkazuje na dobrovoľné dotazníky k diplomovej práci v Google Forms. GitPulse im neposiela žiadne údaje a dotazníky nezbierajú meno, e-mail ani prihlasovacie údaje.

### Zákonné sprístupnenie

Vaše osobné údaje môžeme sprístupniť, ak to vyžaduje zákon, v reakcii na platný právny postup, alebo na ochranu práv, majetku alebo bezpečnosti univerzity, jej študentov alebo verejnosti.

---

## Ako GitPulse zabezpečuje moje údaje?

Používame technické a organizačné opatrenia na ochranu vašich osobných údajov:

| Opatrenie | Popis |
|---|---|
| **Šifrovanie prenosu** | Všetky pripojenia sú šifrované pomocou TLS (HTTPS) |
| **Bezpečné cookies** | Session cookies sú označené HttpOnly, Secure a SameSite=Lax |
| **CSRF ochrana** | Na všetkých operáciách meniace stav |
| **Bezpečnostné hlavičky** | Content Security Policy (CSP), HSTS, X-Frame-Options, X-Content-Type-Options |
| **Rate limiting** | Na autentifikačných a API endpointoch |
| **Validácia vstupov** | Server-side validácia a kódovanie výstupov |
| **Šifrovanie tajomstiev** | Prihlasovacie údaje k databáze a API tokeny sú šifrované |
| **Bezpečnostné skenovanie** | Pravidelné bezpečnostné skenovanie a aktualizácie závislostí |
| **Obmedzený prístup** | Prístup k produkčnej infraštruktúre je obmedzený na oprávnený personál |

{{< alert type="warning" >}}
**Žiadny systém nie je 100 % bezpečný.** Napriek týmto opatreniam žiadny systém nie je úplne bezpečný. Ak objavíte zraniteľnosť, prosím nahláste ju na [mykyta.olym.work@gmail.com](mailto:mykyta.olym.work@gmail.com).
{{< /alert >}}
---

## Uchovávanie údajov

GitPulse uchováva vaše osobné údaje iba tak dlho, ako je nevyhnutné na splnenie účelov popísaných v tomto Vyhlásení:

| Kategória údajov | Doba uchovávania |
|---|---|
| Informácie o účte | Do zrušenia účtu alebo 12 mesiacov od posledného prihlásenia |
| Údaje o aktivite v kurze | Trvanie akademického kurzu + 6 mesiacov na odvolania |
| Výsledky hodnotenia | Trvanie akademického kurzu + 6 mesiacov |
| Serverové prístupové logy | 90 dní (priebežne) |
| Session cookies | Do zatvorenia prehliadača alebo manuálneho odhlásenia |

Po uplynutí doby uchovávania sú údaje trvalo vymazané alebo anonymizované. Kedykoľvek môžete požiadať o predčasné vymazanie (pozrite [Vaše práva a možnosti](#ake-su-moje-prava-a-moznosti)).

---

## Cookies a podobné technológie

GitPulse používa výlučne nevyhnutné cookies na fungovanie Služby. Nepoužívame žiadne sledovacie, reklamné alebo cookies tretích strán.

| Cookie | Účel | Typ | Trvanie | Atribúty |
|---|---|---|---|---|
| `__Host-gitpulse_session` | Autentifikácia relácie | Nevyhnutný | Relácia | HttpOnly, Secure, SameSite=Lax, Path=/ |
| `gp_lang` | Jazyková preferencia | Funkčný | 365 dní | SameSite=Lax |
| `gp_cookie_consent` | Stav súhlasu s cookies | Nevyhnutný | 365 dní | SameSite=Lax |

Cookies môžete spravovať prostredníctvom nastavení prehliadača. Vypnutie nevyhnutných cookies môže zabrániť správnemu fungovaniu Služby.

---

## Aké sú moje práva a možnosti?

Podľa GDPR a platného slovenského zákona o ochrane údajov máte nasledujúce práva. Tieto práva poskytujeme bezplatne, pokiaľ požiadavky nie sú zjavne neopodstatnené alebo nadmerné.

| Právo | Popis |
|---|---|
| **Prístup** | Požiadať o kópiu osobných údajov, ktoré GitPulse o vás uchováva |
| **Oprava** | Požiadať o opravu nepresných alebo neúplných údajov |
| **Vymazanie** | Požiadať o vymazanie vašich osobných údajov ("právo na zabudnutie") |
| **Obmedzenie** | Požiadať o obmedzenie spôsobu spracovania vašich údajov |
| **Prenosnosť** | Získať vaše údaje v štruktúrovanom, strojovo čitateľnom formáte |
| **Námietka** | Namietať voči spracovania na základe oprávneného záujmu |
| **Odvolanie súhlasu** | Kedykoľvek odvolať súhlas tam, kde je spracovanie založené na súhlase |

### Ako uplatniť vaše práva

1. **Kontaktujte vyučujúceho** - môže odstrániť váš zápis a súvisiace údaje
2. **Napíšte nám** na [mykyta.olym.work@gmail.com](mailto:mykyta.olym.work@gmail.com) s predmetom "Žiadosť o ochranu údajov"

Na vašu žiadosť odpovieme do 30 dní. Ak budeme potrebovať ďalší čas, budeme vás informovať o predĺžení a dôvode.

### Dozorný orgán

Ak sa domnievate, že vaše práva na ochranu údajov boli porušené, máte právo podať sťažnosť príslušnému dozornému orgánu:

{{< alert type="note" >}}
**Úrad na ochranu osobných údajov Slovenskej republiky.** Hraničná 12, 820 07 Bratislava 27   Telefón: +421 2 3231 3214   Web: [dataprotection.gov.sk](https://dataprotection.gov.sk)
{{< /alert >}}
---

## Ochrana súkromia detí 

GitPulse je určený pre univerzitných študentov a nie je zameraný na osoby mladšie ako 16 rokov. Vedome nezhromažďujeme osobné údaje od osôb mladších ako 16 rokov. Ak zistíme, že sme neúmyselne zhromaždili údaje od osoby mladšej ako 16 rokov, tieto údaje bezodkladne vymažeme.

---

## Zmeny Vyhlásenia

Toto Vyhlásenie môžeme z času na čas aktualizovať v reakcii na zmeny v našich postupoch, Službe alebo platnom práve. Pri podstatných zmenách:

- Aktualizujeme dátum "Posledná aktualizácia" v hornej časti tejto stránky
- Zverejníme oznámenie v rámci Služby
- Ak to vyžaduje zákon, požiadame o váš súhlas pred uplatnením zmien

---

## Kontaktujte nás 

Vaše informácie spravuje Katedra počítačov a informatiky (KPI), Fakulta elektrotechniky a informatiky (FEI), Technická univerzita v Košiciach.

**Prevádzkovateľ:**  
Katedra počítačov a informatiky (KPI)  
Fakulta elektrotechniky a informatiky (FEI)  
Technická univerzita v Košiciach (TUKE)  
Letná 1/9, 042 00 Košice, Slovensko  
E-mail: [mykyta.olym.work@gmail.com](mailto:mykyta.olym.work@gmail.com)  
Web: [kpi.fei.tuke.sk](https://kpi.fei.tuke.sk)

Pri kontaktovaní uveďte do predmetu "Žiadosť o ochranu údajov" alebo "Ochrana osobných údajov", aby sme mohli vašu požiadavku správne nasmerovať.
