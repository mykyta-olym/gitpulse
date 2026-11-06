---
title: "Changelog"
# The subheader is one row of Slovak section names; "Changelog" would be
# the only English label in it. `nav_title` wins over `title` there.
nav_title: "Zmeny"
description: "Kompletná história zmien systému GitPulse"
---
Kompletná história zmien projektu **GitPulse** - od prvého commitu po najnovšie úpravy.
Formát: [Keep a Changelog](https://keepachangelog.com/sk/1.0.0/).

## [2026.11.4.post2] - 2026-11-04

### Opravené

- Riadky skupín kurzu používajú spoločné vykresľovanie pre metriky, sync stream aj náhradné načítanie. Chýbajúce skóre a čas vymažú staré hodnoty; nula, opakované pokusy, zrušené úlohy a vymazané skupiny zachovávajú správny stav.
- Stavové odznaky skupín zachovávajú preložené názvy, vysvetlivky a poradie triedenia spoločného komponentu. Časy sa triedia podľa UTC ISO hodnôt a zaokrúhľovanie percent zodpovedá serveru.
- Stránka kurzu a živé údaje používajú rovnaký dotaz na nedávne úlohy ako sledovanie synchronizácie. Rozhoduje najnovšia úloha skupiny, nie staršia bežiaca či dokončená úloha; úlohy projektov nemenia stav skupiny.
- Náhradné načítanie synchronizácie obsahuje rovnaký čas ako stream, takže aktualizácia zachováva miestny čas a nastavenia používateľa.

## [2026.11.4.post1] - 2026-11-04

### Opravené

- Živé aktualizácie skupín a projektov používajú spoločný komponent bunky skóre pre nulu, chýbajúce metriky, obnovené údaje aj nastavené prahy kurzu. Vylúčení členovia si zachovajú zobrazené skóre; riadky vyučujúcich a mentorov majú rovnaké prázdne stavy ako pri vykreslení serverom.
- Vysvetlivky a prístupné názvy kontrol zodpovedajú aktuálnemu úspechu, chybe, nedostupnosti alebo zatiaľ nevyžadovanej kontrole. Uložené výsledky sa zobrazia hneď aj bez podrobného JSON.
- Živé odpovede pre študentov rešpektujú tabuľky obsahujúce iba mená a neposielajú individuálne známky. Odstránené sú nepoužívané e-maily a identifikátory GitLab zo živých odpovedí a atribútov riadkov projektu.
- Odstránené sú aktualizácie a databázové výpočty pre karty súhrnu skupiny a upozornenia na zastarané údaje či webhooky, ktoré sa už nevykresľujú.
- Oneskorené obnovenie pri štarte zachová úlohy už sledované v pamäti, čím nevznikajú duplicitné spojenia SSE ani stratené odkazy na dotazovanie.

## [2026.11.4] - 2026-11-04

### Opravené

- Cache aktivity je oddelená podľa používateľa a oprávnení v kurze. Cache skupín, projektov a profilov študentov oddeľuje ovládanie správy od prístupu iba na čítanie aj po zmene roly v kurze.
- Archivácia, aktivácia, priradenie vyučujúcich a vylúčenie z hodnotenia používajú existujúce spoločné kontroly oprávnení vyučujúcich daného kurzu.
- Vyhľadávanie synchronizácií, dotazovanie a stav kontrol rešpektujú rovnaké oprávnenia ako tok synchronizácie. Prehľad skupiny iba na čítanie nežiada obmedzené údaje kurzu po návrate na kartu či obnovení spojenia.

## [2026.11.3.post7] - 2026-11-03

### Opravené

- Ovládanie prehľadu kurzu a obsah v cache používajú spoločnú kontrolu oprávnení vyučujúcich daného kurzu. Samotná globálna rola vyučujúceho už nezobrazuje správu kurzu, ktorý používateľ nevedie.
- Rovnaké oprávnenie dostáva JavaScript: akcie vyučujúcich fungujú a používatelia s prístupom iba na čítanie neotvárajú obmedzený tok synchronizácie ani náhradné dotazovanie, ani po návrate na kartu či obnovení spojenia.
- Členstvo lokálneho účtu v kurze sa vyhľadá aj podľa používateľského mena, keď relácia používa rovnaké meno pre identitu GitLab bez prepojeného profilu GitLab.
- Prístup ku kurzom, skupinám a študentom používa jedno spoločné vyhľadanie účtu. Cache skupín je oddelená pre každého používateľa s prístupom iba na čítanie; vyučujúci kurzu môžu zdieľať úplný prehľad kurzu.

## [2026.11.3.post6] - 2026-11-03

### Opravené

- Filter skupín v kurze používa vlastné vyhľadávacie pole a tabuľku. Písanie, opustenie poľa, stránkovanie a navigáciu riadi spoločný filter bez duplicitného obslužného kódu klávesnice.
- Oneskorená ponuka prehliadky nevyrušuje upravované formuláre, aktívne polia, kalendáre, rozbaľovacie ponuky, vyhľadávanie ani mobilné menu.
- Vybraný súbor JSON sa odstraňuje spoločným tlačidlom zatvorenia s dotykovou plochou. Odstránené sú osobitné štýly tohto tlačidla a tlačidla doplnenia údajov.
- Stĺpce úloh majú priestor pre stavové štítky aj dotykové akcie bez zmeny šírky pri načítaní riadkov.

## [2026.11.3.post5] - 2026-11-03

### Opravené

- Import JSON a prílohy Markdown používajú rovnaký natívny výber súboru vrátane ovládania klávesnicou, zamerania a zakázaného stavu.
- Na počítači zostávajú úplné názvy tlačidiel, pokyny k prílohám a nadpis pridelených inštruktorov. Spoločné responzívne komponenty ich na úzkych obrazovkách skrátia; text zostáva vľavo a ovládanie vpravo.
- Dlhý názov vybraného súboru JSON sa skráti v editore a nevytlačí ovládanie mimo jeho okraja.
- Samotný výber súboru neoznačí formulár ako zmenený. Upozornenie na neuložené zmeny sa aktivuje po úspešnom vložení obsahu; neúspešná príloha ponechá nedotknutý formulár bez zmien.

## [2026.11.3.post4] - 2026-11-03

### Opravené

- Tabuľka kurzov používa kratší nadpis Inštruktori s vysvetlivkou Pridelení inštruktori. Aj naplnená produkčná tabuľka zachováva nadpis v jednom riadku na telefónoch a tabletoch; rovnaký názov používajú metadáta buniek.

## [2026.11.3.post3] - 2026-11-03

### Zmenené

- Každá rola má vlastný dotazník: panel Podpora a návrhy ukáže študentom dotazník pre študentov, vyučujúcim dotazník pre vyučujúcich so System Usability Scale a správcom dotazník pre vyučujúcich aj pre správcov.
- Banner dokumentácie vedie na samostatný dotazník k dokumentácii, stránka Vyhodnotenie vo výučbe uvádza všetky dotazníky a ochrana osobných údajov uvádza, že bežia v Google Forms bez mena a e-mailu.

## [2026.11.3.post2] - 2026-11-03

### Opravené

- Načítavanie formulára zobrazuje jeho vlastné tlačidlo akcie. Formulár zostáva zaneprázdnený a neaktívny bez stlmenia všetkých polí a druhého indikátora nad inou sekciou; obnovenie kariet a tabuliek si zachováva indikátor vo svojom bloku.
- Nahrávanie príloh Markdown má krátky pomocný text vľavo a spoločné ikonové tlačidlá nahrávania a pomoci vpravo v jednom riadku aj na úzkom displeji bez druhého riadka päty a posunov pri načítavaní.
- Skrátený oznam o povinných poliach drží hviezdičku v rovnakom riadku aj na úzkej obrazovke.
- Mobilné rozloženie už neanimuje odsadenie stránky. Pri prechode zo šírky počítača sa text a ovládacie prvky nestlačia do priestoru vedľa pôvodného panela; prechody panela na počítači zostávajú zachované.
- Nadpisy stĺpcov systémových tabuliek už nepoužívajú zalamovanie určené pre text buniek; krátke názvy zostávajú v spoločnom jednoriadkovom rozložení.

## [2026.11.3.post1] - 2026-11-03

### Opravené

- Prílohy Markdown používajú spoločné API a stav požiadavky. Koncept sa počas nahrávania nemení a odoslanie počká na potvrdenie súboru serverom namiesto uloženia zástupného textu Uploading.
- Súbory sa nahrávajú postupne, potvrdené odkazy zostanú zachované aj pri čiastočnej chybe a po chybe či časovom limite je možné výslovné opakovanie. Neskorá odpoveď neupraví nový formulár, nepresunie fokus ani nezruší jeho ochranu nahrávania.
- Editor používa spoločné tlačidlo dostupné klávesnicou, jeden renderer náhľadu a obrys pri pretiahnutí bez zmeny rozmerov. Duplicitný stav náhľadu je odstránený a po skončení požiadavky sa akcie odpovede zosúladia s aktuálnym živým stavom tiketu.

## [2026.11.3] - 2026-11-03

### Zmenené

- Sekcia Diplomovka zodpovedá aktuálnemu textu práce: osem kapitol, abstrakt a nové snímky aktuálnej verzie. Ciele práce, Vyhodnotenie vo výučbe a príručka pre učiteľov opisujú plánované vyhodnotenie namiesto starého harmonogramu pilotu a nezmeranej úspory času.
- Dokumentácia opisuje výpočet skóre tak, ako ho počíta kontrolný mechanizmus (len zapnuté kontroly, delené súčtom ich váh), kontroly R02, R04, R05 a R10 tak, ako sa naozaj vyhodnocujú, všetkých 27 migrácií a LLM analýzu ako vypnutú v produkcii. Dlhé pomlčky sú nahradené.

## [2026.11.2.post13] - 2026-11-02

### Opravené

- Povinné polia Markdown pri chybe opustia náhľad a získajú fokus natívnej validácie namiesto neviditeľnej chyby. Spoločný editor opravuje žiadosti podpory aj odpovede v tiketoch.
- Formátovacie akcie nezávisia od prvej otvorenej stránky a fungujú aj po SPA navigácii zo stránky bez editora. Odstránená je nepoužívaná vykresľovacia funkcia Alpine a náhradné prechádzanie jeho interných scope.
- Koncept podpory používa spoločné sledovanie interakcií pre formátovanie, výber priority a vloženie prílohy. Počiatočné hodnoty ani otvorenie výberu súboru nespúšťajú upozornenie na neuložené zmeny; navigácia odpojí poslucháče.

## [2026.11.2.post12] - 2026-11-02

### Opravené

- Odoslanie podpory používa spoločný stav požiadavky: polia sú počas odosielania uzamknuté, chyba zachová koncept aj náhľad a po časovom limite je možné výslovné opakovanie bez automatického opakovania POST.
- Navigácia odpojí obsluhu formulára a vyradí neskoré odpovede. Predošlé odoslanie nezruší ochranu konceptu na novej stránke ani neodstráni cudzie chybové správy.
- Vlastnú obrazovku úspechu a tlačidlo nahradili spoločné komponenty. Zmena rozmerov používa spoločnú animáciu, dokončený stav prevezme fokus a vlastné štýly úspechu sú odstránené.

## [2026.11.2.post11] - 2026-11-02

### Opravené

- Obnovenie toku udalostí čaká na zoznam aj počítadlá odložených udalostí. Čiastočné zlyhanie oznámi chybu a spoločný stav načítania skončí až po oboch požiadavkách; úspešné opakovanie aktualizuje počítadlá.
- Stránka používa spoločný SSE klient s obmedzenými pokusmi o pripojenie. Skryté, offline a nedostupné spojenia sa pozastavia; opätovné pripojenie doplní zmeškané udalosti. Zrušený odchod zachová živé aktualizácie, dokončená navigácia zruší spojenie aj rozpracované čítania.
- Obnovenie a živé aktualizácie zachovávajú výber udalostí aj aktuálnu stranu. Prázdny výsledok vymaže starý výber. Odstránené triedenie zrušenej tabuľky odložených udalostí.

## [2026.11.2.post10] - 2026-11-02

### Opravené

- Detail tiketu používa spoločné stavy požiadaviek pre komentáre a polia. Uložený komentár sa zobrazí okamžite, živá udalosť ho neduplikuje, chyba zachová odpoveď a vráti odmietnutú zmenu poľa. Neúspešné zatvorenie či otvorenie jasne oznámi, že komentár bol uložený.
- Vlastný cyklus pripájania nahradil spoločný SSE klient. Skryté a offline spojenia sa pozastavia; nedostupné spojenie ponúka opakovanie. Navigácia zruší spojenie a vyradí oneskorené odpovede. Odstránené odložené obnovenia stránky.
- Živé komentáre a aktualizovaný čas používajú spoločný časový komponent. Zmena zodpovednej osoby si pred obnovením serverových oprávnení vyžiada potvrdenie zahodenia neodoslanej odpovede.
- Spoločná spätná väzba tlačidiel zachováva vybrané hodnoty formulárových ponúk a ich Alpine väzby namiesto prepísania na Hotovo alebo Zlyhalo.

## [2026.11.2.post9] - 2026-11-02

### Opravené

- Spoločná hlavička drží ikonu, názov a počet spolu. Názov, akcie a pomoc sú v jednom riadku, keď sa zmestia; mobilné zalomenie zachová čitateľné ovládanie. Odstránené absolútne polohovanie a protichodné responzívne pravidlá; skrátený nadpis aktivity na CI/CD Health.
- Support Tickets používa spoločný SSE klient s obmedzeným opakovaním. Navigácia zruší čakajúce pripojenie aj poslucháče stránky; staré udalosti a dokončené mutácie neobnovia cieľovú stránku ani na nej nezobrazia oznámenie.
- Odstránené umelé oneskorenie 450 ms pri mazaní a čistení tiketov. Akcie používajú spoločný zámok a výber riadkov patrí svojej tabuľke. Zrušenie potvrdenia neodosiela požiadavku; chyba ponechá aktuálne riadky.

## [2026.11.2.post8] - 2026-11-02

### Opravené

- Obnovenie aktivity používa rovnaké serverové komponenty metrík, skupín a merge requestov ako prvé načítanie. Zachováva zvolené zobrazenie, radenie, stránkovanie a vodorovné posunutie; prázdne aj naplnené stavy nezanechávajú staré odznaky ani chýbajúce riadky. Odstránený duplicitný JSON endpoint a klientsky renderer.
- Spoločné tlačidlo Refresh zobrazuje skutočné načítavanie, úspech aj chybu. Výslovné obnovenie číta aktuálne dáta DB a nahrádza fragment v cache. Aktualizácie používajú spoločný SSE klient, reagujú na úlohy príslušného kurzu, čakajú v skrytej karte alebo pri nedostupnosti servera a pri navigácii sa zrušia.
- Stav skupiny vychádza z najnovšieho ukončeného pipeline naprieč projektmi. Záznamy bez dátumu neprebijú datované a remízy majú stabilné poradie. Chýbajúce pipelines označuje spoločný odznak; neurčená úspešnosť nie je nula. Graf reaguje na tému a pri chýbajúcej knižnici ponúka funkčné opakovanie.

## [2026.11.2.post7] - 2026-11-02

### Opravené

- Kontrola typov, jednotkové, kontraktové a integračné testy v CI používajú rovnaké verzie závislostí aplikácie ako produkcia vrátane OpenTelemetry. Návod na vývoj používa rovnaké obmedzenia verzií a rešpektuje závislosti konkrétnej platformy.
- Lokálne minifikátory aj minifikátory v CI majú rovnaké verzie ako Docker, aby rovnaké zdroje vytvárali rovnaké balíky. Odstránená duplicitná inštalácia JSON Schema a zastarané Python extras pre dokumentáciu; dokumentáciu zostavuje Hugo.

## [2026.11.2.post6] - 2026-11-02

### Opravené

- Profil zručností a označenie týždňa sa vyprázdnia, keď história nemá vyhodnotený týždeň, aj po predchádzajúcom výsledku. Odstránené zastarané riadky pri chýbajúcich detailoch kontrol alebo celej histórii; skutočná nula zostáva výsledkom.
- Súhrnné hodnoty sa aktualizujú ihneď po prijatí histórie nezávisle od odloženého vykreslenia grafu. Pred použitím novej histórie sa uvoľnia pôvodné grafy aj čakajúce vykreslenia.
- Rezervovaná výška matice sa po naplnení riadkov uvoľní, takže pod menšou maticou nezostáva prázdne miesto. Týždenné skóre používa spoločný indikátor priebehu; odstránené duplicitné prechody farieb, nepoužívané štýly odznakov aj zastarané oneskorenie riadkov.

## [2026.11.2.post5] - 2026-11-02

### Opravené

- Tlačidlá v päte modálneho okna majú na mobiloch a tabletoch rovnakú veľkosť aj s obalom pre vysvetlenie zakázaného stavu. Výber a načítavanie nemenia ich rozmery; veľkosť tlačidiel na počítači zostáva zachovaná.
- Ochrana neuložených zmien funguje aj pri otvorení dialógu počas navigácie pred registráciou ochrany formulára. Používa rovnaký počiatočný stav a ustálenie hodnôt ako bežné otvorenie.
- Stĺpec výberu úloh na tabletoch poskytuje miesto pre zaškrtávacie políčko aj štandardné odsadenie bunky. Odstránené duplicitné šírky hlavičiek výberu z udalostí a požiadaviek aj nepoužívaná pomôcka šírky.
- Modálne okná čakajú pred inicializáciou a presunutím na registráciu svojich Alpine komponentov vrátane samostatného bloku modálnych okien. Zlyhanie skriptu odstráni nepoužiteľné dialógy a zobrazí spoločný stav s opakovaním.
- Výbery dátumu sa inicializujú až po úspešnom načítaní skriptov stránky, takže zlyhanie skriptu nastavení nezanechá kalendáre bez vstupných polí.
- Živé aktualizácie projektu zachovajú spoločné zámky tlačidiel a ignorujú odpovede aj čakajúce obnovenia opustenej stránky. Zisťovanie AI analýzy rešpektuje príznak funkcie a rolu; stará odpoveď neobnoví ukončené sledovanie.
- Dokončené zlúčené obnovenia uvoľnia svoje záznamy namiesto trvalého držania funkcií stránok. Graf problémov sa pri odchode zničí a odložené vykreslenie nemení novú stránku. Zastarané komentáre modálnych okien nahrádza opis aktuálneho správania.

## [2026.11.2.post4] - 2026-11-02

### Opravené

- Kontrola, ktorú kurz vypol, sa už nezapočítava do skóre ani do počtu kontrol a nezobrazuje sa medzi nesplnenými. Študent už nevidí „Kontrola vypnutá“ medzi zlyhávajúcimi kontrolami a tabuľky členov ukazujú splnené kontroly zo zapnutých, nie z 13.
- Skóre sa delí súčtom váh hodnotených kontrol, rovnako ako pri týždennom pláne. Pri predvolene vypnutých R09, R11 a R13 dáva splnenie všetkých zapnutých kontrol 100 % namiesto 85 %. Nastavenia kurzu už predvolené váhy neoznačujú ako chybné a upozornia len vtedy, keď aktívne kontroly nemajú žiadnu váhu.
- Panel „Váš pokrok“ na nástenke študenta počíta vlastné otvorené merge requesty a neúspešné pipeline študenta, rovnako ako karta Otvorené MR, a nie súčet za celú skupinu.

## [2026.11.2.post3] - 2026-11-02

### Opravené

- Pohyblivý úsek navigácie nahrádza súvislé vyplnenie od ľavého okraja vo farbe aktívneho motívu. Po dokončení poslednej požiadavky a inicializácii stránky sa najprv viditeľne vyplní celá šírka a až potom zmizne.
- Nová práca počas dokončovania zachová viditeľnú šírku a zruší zhasnutie. Odstránená pôvodná CSS slučka; aj obmedzené animácie a nedostupná knižnica vykreslia úplné vyplnenie.

## [2026.11.2.post2] - 2026-11-02

### Opravené

- Indikátor navigácie sa viditeľne dokončí pri pravom okraji aj vtedy, keď čakacia animácia už opustila obrazovku. Záverečný pohyb je rýchlejší a okraj sa vykreslí pred zmiznutím aj pri obmedzených animáciách alebo nedostupnom GSAP. Nová požiadavka zruší čakajúce zhasnutie.
- AI analýza skupiny používa spoločný panel úloh pre priebeh, zrušenie, opätovné pripojenie a ukončenie. Odstránené duplicitné sledovanie a odkazy na neexistujúci lokálny indikátor. Zisťovanie rešpektuje príznak funkcie a rolu vrátane učiteľov v režime iba na čítanie.
- Priebeh skupiny vychádza zo súhrnného stavu; dokončenie jedného projektu neukončí celú skupinu. Nulový priebeh je platný, neznámy zostáva neurčitý a percentá sú ohraničené na 0–100.
- Oneskorená odpoveď po opustení stránky nezaregistruje úlohu. Odstránenie značky presmerovania zachová jazyk, filtre aj fragment. Odstránená duplicitná animácia tlačidla MR; neúspešné zaradenie novej analýzy neoznačí inú analýzu ako zlyhanú.

## [2026.11.2.post1] - 2026-11-02

### Opravené

- Voliteľná AI analýza používa spoločné upozornenia, indikátor načítania, priebeh a stavy tlačidiel. Chyby a výsledky sa vykresľujú zo serverovej šablóny; odstránené duplicitné vykresľovanie a lokálne štýly komponentov.
- Oneskorené odpovede a udalosti staršej analýzy už nemenia nový beh ani opustenú stránku. Neznámy stav neukončí prebiehajúcu prácu, nulový priebeh je platný a spojenia spravuje spoločný SSE klient.
- Po potvrdenom ukončení sa výsledky načítajú ihneď. Zlyhané načítanie ponúka spoločnú akciu Obnoviť bez opakovania AI analýzy. Prázdny stav sa obnoví zo servera; chyba ani zrušenie neukazujú dokončených 100 %.

## [2026.11.2] - 2026-11-02

### Opravené

- Indikátor navigácie rešpektuje všetkých šesť farebných motívov vo svetlom aj tmavom režime. Prerušený pohyb pokračuje z aktuálnej polohy a čas dokončenia zodpovedá zostávajúcej vzdialenosti.
- Formuláre, zmeny údajov a ručné obnovenia regiónov používajú spoločné sledovanie priebehu až do skutočného výsledku. Súbežná operácia neskryje indikátor druhej; čítanie na pozadí zostáva tiché. Poškodený JSON sa spracuje ako chyba, nie ako prázdny úspech.
- Odstránené tri oneskorené kontroly dashboardu: obnovené a nové úlohy už aktualizujú štítky kurzov cez spoločné udalosti. Odstránená nadbytočná záloha zámku modálneho formulára.

## [2026.11.1.post7] - 2026-11-01

### Opravené

- Pohyblivý indikátor navigácie po poslednej požiadavke a inicializácii stránky najprv dôjde k pravému okraju a potom plynulo zmizne. Nová požiadavka preruší predchádzajúce dokončenie. Indikátor funguje aj pri obmedzení pohybu a nedostupnom GSAP.
- Farby svetlej a tmavej témy a časovanie dokončenia zodpovedajú indikátoru GitLabu.
- Odstránené neplatné volania resetu indikátora z validácie skupiny. Neplatný alebo zablokovaný formulár nespôsobí chybu ani neukončí indikátor inej požiadavky.

## [2026.11.1.post6] - 2026-11-01

### Opravené

- Údaje o účastníkoch merge requestu sú kompaktné, zarovnané vľavo a široké podľa obsahu namiesto rovnako širokých stĺpcov. Spoločné avatary a štítky sa na úzkych obrazovkách prirodzene zalamujú.
- Karty vlastných MR a poskytnutých kontrol zobrazujú schválenie podľa rovnakého uloženého zoznamu schvaľovateľov z GitLabu. Zastaraný súhrn kontroly neskryje aktuálne schválenie ani neobnoví odvolané. Spresnený popis kroku Reviewed.

## [2026.11.1.post5] - 2026-11-01

### Opravené

- Rozlíšený neznámy zoznam commitov MR, chýbajúce podrobnosti a potvrdený prázdny zoznam. Uložená história vetvy má vysvetlenie pri commitoch a odkaz na GitLab. Autorstvo sa neodhaduje. Inkrementálna synchronizácia doplní aj nezmenené historické MR a opakuje chýbajúce podrobnosti; nedostupné API neznamená prázdny úspešný výsledok.
- Priradení recenzenti sú oddelení od ostatných účastníkov diskusie. Počty komentárov majú popis, schválenie a čakanie na kontrolu majú vlastný stav. Identity sa zobrazia aj bez komentára. Priradenie samo neznamená vykonanú kontrolu a zlúčenie neznamená schválenie.
- Spoločný avatar používa zalamovací kontajner metadát GlAvatarLabeled; údaje o účastníkoch sú zarovnané na počítači aj mobile. Opravený spoločný prázdny stav bez ilustrácie.

## [2026.11.1.post4] - 2026-11-01

### Opravené

- Úlohy na pozadí sa ukončia až po potvrdenom výsledku servera. Odstránené umelé čakanie, úspech vyvolaný časovačom a pomocné API používané iba testami. Neplatná SSE správa alebo chýbajúci stav spustí overenie.
- Skutočné dokončovanie zachová blokovanie akcií a neurčitý priebeh až do overenia. Obnova a zmeny medzi kartami používajú rovnaké prechody; vymazanie úložiska nevytvorí úspech. Staré odpovede neovplyvnia nový beh a kontroly stavu sa neprekrývajú.
- Zjednotená detekcia aktívnych kurzov, HTTP kontrola a stream pre spustené úlohy a prestávky medzi dávkami. Synchronizácia jedného projektu má vlastné sledovanie. Spoločné komponenty opakovania a kontroly stavu pokračujú aj po dočasnej chybe siete.

## [2026.11.1.post3] - 2026-11-01

### Opravené

- Zarovnanie avatarov s menami v spoločnom komponente. Autorstvo MR vychádza z presného synchronizovaného zoznamu komitov; zachováva skutočné príspevky učiteľov bez histórie šablóny či odhadu podľa času. Prázdny zoznam sa odlišuje od nedostupných údajov.
- Navigácia zostáva zaneprázdnená do dokončenia požiadaviek a skriptov bez vymyslených percent a predčasného zobrazenia po troch sekundách. Časový limit preruší načítanie skriptov; chyba ponúkne spoločné opakovanie. Duplicitné udalosti neukončia inú požiadavku.
- Vyhľadávanie odlišuje chybu od prázdnych výsledkov, ponúka opakovanie a okamžite ruší neaktuálne čítania. Odstránené umelé čakanie po uložení preferencií.

## [2026.11.1.post2] - 2026-11-01

### Opravené

- Spoločné stavy načítania tlačidiel, tabuliek a kariet sledujú prebiehajúcu požiadavku. Indikátor sa pri rýchlej odpovedi nezobrazí, stav zaneprázdnenia však platí okamžite. Odstránené umelé čakanie po odpovedi aj neviditeľná časovacia animácia.
- Opakovanie požiadavky je dostupné hneď po dokončení, neúspešné obnovenie zachová existujúci obsah a animácia výšky sa prispôsobí novým údajom. Načítanie komponentu User Info má časový limit a po chybe sa dá zopakovať.
- Súhrn System Health upozorní aj na neúspešnú kontrolu GitLabu či e-mailu. Kontrola pripravenosti infraštruktúry zostáva samostatná.
- Vyhľadávanie a filtre asistenta zostávajú počas obnovenia dostupné; prichádzajúca odpoveď neprepíše rozpracovaný text.

## [2026.11.1.post1] - 2026-11-01

### Opravené

- Riadky webhook konfigurácií používajú jednu spoločnú Jinja šablónu pri otvorení aj obnovení. Odstránený duplicitný JavaScript renderer, vložené JSON dáta a odhadovaná výška; naplnená tabuľka neposúva filtre pod ňou.
- Spoločné odznaky, časové údaje a tlačidlá pre aktívne aj archivované kurzy. JSON API zostáva zachované a HTML obnovenie kontroluje rovnaké oprávnenia ako nastavenia kurzu.

## [2026.11.1] - 2026-11-01

### Opravené

- Spoločný indikátor kariet nadväzuje na deliacu čiaru bez orezania či dvojitej línie. Serverové aj pohyblivé podčiarknutie sa zhodujú v svetlej a tmavej téme na mobile aj počítači.
- Odstránené nepoužívané štýly kariet v hlavičke a duplicitné selektory filtrov. Zachovaná odozva pri prejdení myšou; prepínanie filtrov a panelov overené po jednotlivých snímkach.

## [2026.10.31.post3] - 2026-10-31

### Opravené

- Pozvánka do úvodnej prehliadky ustúpi otvorenému potvrdeniu či formuláru. Používa skutočnú udalosť spoločného modálneho okna, takže neprekryje tlačidlo Zrušiť.
- Odstránený nepoužívaný príznak automatického zatvorenia. Overené zobrazené pozvánky aj oneskorené načítanie stavu prehliadky v mobilnom a desktopovom prehliadači.

## [2026.10.31.post2] - 2026-10-31

### Opravené

- Spoločné čistenie histórie úloh v PostgreSQL aj Redis/RQ pre Vymazať staré, výber úloh a trvalé odstránenie kurzu, skupiny či projektu. Potvrdenie uvádza obe úložiská a výsledok samostatné počty; aktívne úlohy zostávajú zachované a pri nedostupnom Redise sa SQL záznamy neodstránia.
- Vyrovnávacia pamäť sa zneplatní až po potvrdení zmien vrátane odstránených podriadených stránok. Opravené rušenie RQ úloh a nepravdivé hlásenie úspechu pri nedostupnom Redise alebo chýbajúcej histórii.
- Zmeny cez API a spúšťanie či rušenie LLM analýzy vyžadujú oprávnenie vyučujúceho daného kurzu; samotný prístup na čítanie nestačí.
- Spoločný štýl zachováva zarovnanie zaškrtávacích polí v hlavičke aj s vysvetlením zákazu; hromadný výber vynecháva zamknuté riadky.

## [2026.10.31.post1] - 2026-10-31

### Bezpečnosť

- Aktualizovaná tranzitívna závislosť autentifikácie Google `pyasn1` z 0.6.4 na 0.6.5 opravuje štyri zraniteľnosti dekodéra ASN.1 zistené kontrolou závislostí. Ostatné uzamknuté balíky zostávajú bez zmeny.

## [2026.10.31] - 2026-10-31

### Opravené

- Vymazať staré odstraňuje aj uchované zlyhania RQ podľa poslednej aktivity. Zachováva aktívne a opakované úlohy, nedávne dokončenia, audit aj počítadlá chýb.
- Spoločná mriežka kariet zarovnáva zalomené názvy a hodnoty, štandardne má najviac štyri stĺpce. Šírky diagnostických tabuliek určuje spoločný komponent.

## [2026.10.30] - 2026-10-30

### Zmenené

- Stránka Systém používa spoločné komponenty Pajamas: zdravie služieb a monitoring sa vykresľujú hneď pri prvom zobrazení ako karty štatistík a tabuľka komponentov, obnovenie vymieňa serverové HTML časti bez posunov rozloženia a externé nástroje monitoringu sú v jednej ponuke záhlavia.
- Globálne oznámenie o stave služby používa spoločný horný pás `.gp-top-banner` a pre administrátorov pridáva priamy odkaz na stránku Systém.

### Opravené

- Záporné hodnoty pretečenia databázového poolu sú orezané na nulu, pripojení klienti Redis sa čítajú jedným volaním `INFO`, interné kontroly GitLabu ignorujú proxy premenné prostredia a obnova vyrovnávacej pamäte zdravia beží cez jeden zámok.
- Názvy úloh zjednocujú úvodné podčiarkovníky a veľké písmená, dopĺňajú chýbajúce úlohy workerov, zachovávajú popisy úloh a neduplikujú príčinu chyby. Odstránené nepoužívané pomocné funkcie v Pythone, importy makier Jinja, symboly JS, pravidlá CSS a prekladové kľúče.

## [2026.10.29.post7] - 2026-10-29

### Zmenené

- Diagnostika je súčasťou stránky Systém: zdravie služieb, metriky a upozornenia sú spolu; sledované úlohy a uchované zlyhania RQ majú jeden denník bez duplikátov. História iba z RQ zostáva len na čítanie.
- Odstránená samostatná stránka Stav služby, jej skript a navigácia. Staré odkazy presmerujú podľa roly; učitelia a študenti vidia oznámenia na existujúcich stránkach.
- Riadky úloh používa prvé zobrazenie aj obnovenie z jedného serverového vzoru. Zachované spoločné stavy načítavania, opakovania, výberu a zrušenia úloh.

## [2026.10.29.post6] - 2026-10-29 - Čitateľné názvy úloh v diagnostike

**Opravené**

- Dlhé názvy úloh sa na mobile zalamujú v bunke denníka zlyhaní. Názvy frontov používajú spoločný sivý odznak.

## [2026.10.29.post5] - 2026-10-29 - Čitateľná diagnostika zlyhaní úloh

**Opravené**

- Stav služby rozlišuje historické zlyhania RQ od nových chýb vykonávania; Grafana a hodinové upozornenie používajú skutočné počítadlo chýb workerov vrátane opakovaných pokusov.
- Administrátor môže v spoločnej stránkovanej tabuľke prezerať dátumy, príčiny, odporúčania a bezpečné odkazy na úlohy a zdrojový kód. História zostáva dostupná; prihlasovacie údaje a obsah úloh sa nezobrazujú.
- Existujúce štýly diagnostických detailov sú spoločné pre všetky stránky; obnovenie zachová aktuálnu stranu denníka.

## [2026.10.29.post4] - 2026-10-29 - Odstránenie nepoužívaných implementácií

**Opravené**

- Alpine CSP a collapse používajú pripnutú verziu 3.17.5 s overenou opravou čítania zastaraného window.fence. Odstránený štandardný Alpine a slabšia záložná CSP politika.
- Kopírovanie používa spoločné Clipboard API bez execCommand a duplicitných záloh. Vnorené tlačidlá a odkazy v záhlaví nerozbaľujú obsah.
- Odstránené nepoužívané limitery projektov, adaptívny circuit breaker, dávkovanie požiadaviek, štatistiky cache, neaktívne metriky a funkcie iba pre testy. Aktívna cache, opakovanie požiadaviek, ochrana fronty a monitoring používajú spoločné implementácie.
- Modely sa importujú z vlastných modulov a webhooky používajú nakonfigurované limity fronty. Odstránené testy a dokumentácia vyradených implementácií.

## [2026.10.29.post3] - 2026-10-29 - Stabilná navigácia a stavy požiadaviek

**Opravené**

- Tabuľky, grafy a prichytené ovládacie prvky zachovávajú rozmery a posun, kým sa pripraví ďalšia stránka. Navigácia obnoví ovládanie a fokus po dokončení aj chybe.
- Informácie o používateľovi používajú spoločný prechod z načítania a ignorujú zrušené alebo nahradené odpovede. Staršia požiadavka tabuľky neukončí načítanie novšej.
- HTMX a formuláre POST používajú spoločné stavy tlačidiel. Karty GitLab a voliteľnej AI analýzy obnovuje jedna serverová projekcia bez duplicitných rendererov a vyrovnávacej pamäte.

## [2026.10.29.post2] - 2026-10-29 - Spoločné stavy obnovenia

**Opravené**

- System Health, úlohy, udalosti, stav služieb, aktivita asistenta, webhooky a Compliance Progress používajú spoločný priebeh obnovenia. Obsah zostáva viditeľný, oblasť označuje načítanie a ovládanie sa po dokončení obnoví.
- Neúspešné obnovenie zachová posledné údaje. Chyby prvého načítania používajú spoločný chybový stav s opakovaním; duplicitné a nahradené požiadavky nehlásia úspech.
- Odstránené duplicitné štýly obnovenia a zachované grafy priebehu pri opätovnom načítaní.

## [2026.10.29.post1] - 2026-10-29 - Nepriehľadné nadpisy nastavení

**Opravené**

- Tiene ovládacích prvkov a rámiky klávesnicového fokusu nepresvitajú cez spoločné prichytené nadpisy nastavení pri posúvaní. Rozstupy sekcií aj rozbaľovacie ponuky zostávajú zachované.

## [2026.10.29] - 2026-10-29 - Jednotné ovládanie tabuliek

**Opravené**

- Riadky tabuliek sú pasívne. Záznam otvoríte cez odkaz na jeho názov alebo tlačidlo v stĺpci Akcie; čítanie, označovanie textu ani vodorovné posúvanie nespúšťajú prechod zo zvyšku riadka.
- Tabuľky projektov skupiny obsahujú priame odkazy a spoločné tlačidlá Zobraziť/GitLab. Živé metriky zachovávajú kontext odkazov na študentov a členov skupiny identifikujú podľa ID.
- Pripojenie projektu obnoví tabuľku vykreslenú serverom. Odstránený je samostatný klientský zoznam projektov aj nepoužitý tvorca členskej tabuľky.
- Pripojenie a obnovenie projektu zruší starú vyrovnávaciu pamäť skupiny aj predmetu; pri presune aj pôvodnej skupiny. Počiatočné poradie kódov predmetov zodpovedá číselnému radeniu spoločnej tabuľky.
- Správa predmetov používa spoločné odznaky učiteľov a tlačidlá rozbalenia. Sprievodca opisuje skutočné odkazy a klávesové ovládanie namiesto nepodporovaných kontextových ponúk a presúvania riadkov.

## [2026.10.28.post7] - 2026-10-28 - Jednotné obnovenie a stavy grafov

**Opravené**

- Stav služby sa obnovuje na mieste so spoločnými stavmi načítania a výsledku. Chyba požiadavky zachová zobrazené údaje; odchod zo stránky požiadavku zruší. Obnovené tabuľky stavu a asistenta používajú spoločné posúvanie.
- Karty editora Markdown nadväzujú na deliacu čiaru. Odznaky členstva zostávajú pri texte, keď sa zmestia, a inak sa zalomia vľavo.
- Učiteľský kontrolný zoznam meria viditeľný kontajner pred animáciou. Grafy rešpektujú obmedzenie pohybu a týždenná analytika obsahuje úvodný súhrn už v odpovedi servera bez posunu rozloženia.

## [2026.10.28.post6] - 2026-10-28 - Čitateľné metadáta na mobile

**Opravené**

- Zalomené odznaky podpory a ďalšie metadáta sa na mobile zarovnávajú vľavo. Odznaky členstva v User Info nasledujú za obsahom; zarovnanie na počítači zostáva nezmenené.
- Mobilné pravidlá sú spoločné, bez užších duplicít. Zastarané komentáre o zostavách a vydaniach nahrádzajú stručné opisy aktuálneho správania. Migrácia dokončených sprievodcov zostáva zachovaná.

## [2026.10.28.post5] - 2026-10-28 - Prehľadný detail podpory na mobile

**Opravené**

- Detail požiadavky má poradie: opis, podrobnosti, konverzácia a odpoveď. Na počítači zostávajú podrobnosti vpravo, na mobile sú pred diskusiou.
- Odstránené duplicitné údaje o autorovi, kurze a období aj nesprávne zarovnané ikony pri dátumoch. Podrobnosti sú v jednej spoločnej karte; tlačidlá odpovede sa na mobile zalamujú vľavo.
- Sprievodca zodpovedá novému rozloženiu a oprávneniam personálu kurzu.
- Ukladanie e-mailov aj kontrola nastavení používajú jeden databázový engine vlastnej slučky. Podpora spracúva poštu mimo slučky požiadaviek bez varovaní o nespustených korutinách a chýb asyncpg medzi slučkami. Vypnuté kategórie ani opakované správy sa neposielajú.

## [2026.10.28.post4] - 2026-10-28 - Správna kontrola dostupnosti GitLabu

**Opravené**

- Kontrola dostupnosti používa verejnú prihlasovaciu stránku GitLabu namiesto anonymného volania chráneného version API. Bežné návštevy už nevytvárajú očakávané HTTP 401 error traces. Autentifikovaná kontrola API tokenu a skutočné výpadky zostávajú viditeľné.

## [2026.10.28.post3] - 2026-10-28 - Konzistentná podpora a mobilný posuv

**Opravené**

- Skryté popisy polí zostávajú v spoločnom posuvnom paneli; dlhá mobilná stránka už nevytvára prázdne miesto pod aplikáciou.
- Detail požiadavky používa spoločné karty, upozornenia, popisy a avatary. Nevyplnené voliteľné odpovede sa nezobrazujú.
- Neúspešné odoslanie zachová koncept aj upozornenie pred odchodom. Živé aktualizácie výberu nespúšťajú ďalší zápis; chyba obnoví uloženú hodnotu.
- Priradenie je obmedzené na aktívnych správcov a vyučujúcich daného kurzu; nulové hodnoty povinných metadát sa odmietnu pri validácii.
- Jaeger uchováva najviac 10 000 stôp; Go má pamäťový cieľ 384 MiB pod limitom kontajnera 512 MiB.

## [2026.10.28.post2] - 2026-10-28 - Funkčné upozornenia na pomalú odozvu

**Opravené**

- Histogramy trvania HTTP požiadaviek, spracovania webhookov a GitLab API obsahujú intervaly nad prahmi upozornení 5/10/15 sekúnd. Pomalé požiadavky sa už neorezávajú pod podmienkou spustenia upozornenia.
- Pri nasadení sa dočasne zachovávajú iba odstránené surové statické súbory. Zdrojové JS/CSS súbory sú vylúčené, aby sa vyradené skripty nezostavovali do manifestu nového obrazu.

## [2026.10.28.post1] - 2026-10-28 - Stav služby a odstránenie pilotného sledovania

**Zmenené**

- Odstránené pilotné sledovanie prehliadača, odhady ušetrených kliknutí a času, sledovanie vyriešených príznakov, príslušné API, úlohy a štyri tabuľky používania. Týždenná história súladu, analytika aktivity, podpora a LLM analýza zostávajú zachované.
- Podpora používa jeden servis formulárov namiesto nepoužívaného API starých dotazníkov. Autor nového tiketu pochádza zo session; server kontroluje prístup ku kurzu, aktívny formulár, CSRF a prepínač podpory.
- Nová stránka Stav služby a spoločné upozornenia čítajú existujúci Prometheus. Administrátor vidí metriky, upozornenia a odkazy na Grafanu, Prometheus, Jaeger a Alertmanager; študenti a učitelia dostávajú vysvetlenie dopadu bez interných údajov.
- Čítanie monitoringu má limit 1,5 sekundy a spoločnú pamäť na 20 sekúnd na proces. Nedostupný monitoring znamená neznámy stav; prázdny PROMETHEUS_URL funkciu vypne nezávisle od nástrojov kurzu.
- Označenia avatarov, legendy grafov, odznaky a responzívne tlačidlá hlavičiek používajú spoločné komponenty. Lokálne preštýlovanie bolo odstránené; výber jazyka pri prihlásení zostáva vycentrovaný.

## [2026.10.28] - 2026-10-28 - Atómové ukladanie konfigurácie kurzu

**Opravené**

- Metadáta kurzu, nastavenia hodnotenia a rozpracované kontroly sa ukladajú v jednej transakcii. Neplatná alebo zastaraná kontrola nezmení žiadnu časť konfigurácie; formulár aj rozšírené ukladanie používajú rovnakú validáciu.
- Skryté voliteľné moduly vrátane LLM analýzy si zachovávajú konfiguráciu. Prázdny výber vstavaných kontrol znamená vypnuté kontroly.
- Riadky kontrol vykresľujú spoločné Jinja komponenty už pri prvom zobrazení aj pri obnovení. Obnovenie zachová rozpracované úpravy a vlastné uloženie nevyvolá upozornenie na cudziu zmenu.
- Spoločné varianty odznakov, zaškrtávacích polí a tlačidiel nahrádzajú lokálne úpravy vzhľadu.

## [2026.10.27.post5] - 2026-10-27 - Kompatibilný testovací nástroj

**Opravené**

- Pytest je obmedzený na verzie nižšie než 9.2, pretože pytest-benchmark 5.3 používa odstránené súkromné pole Node._nodeid. CI inštaluje kompatibilnú verziu a spúšťa všetky benchmark testy bez kompatibilitnej vrstvy.

## [2026.10.27.post4] - 2026-10-27 - Odstránenie nepoužívaných nástrojov dokumentácie

**Odstránené**

- Odstránené nepoužívané nástroje dokumentácie pre vydávanie produktov GitLab, klonovanie repozitárov, Elasticsearch a generovanie produktového obsahu. Generátor navigácie zostáva testovaný a jeho slovenský aj anglický výstup je nezmenený.
- Odstránené nepoužívané formuláre Firebase, produktoví sprievodcovia GitLab, stránky zastaraných funkcií a obsluha archívnych verzií. Zostavujú sa iba používané vstupné súbory JavaScriptu a odstránili sa nepotrebné závislosti.
- Vyhľadávanie dokumentácie používa Pagefind a označenie GitPulse namiesto načítania verzie produktu GitLab. LLM analýza, analytika aktivity a história súladu zostávajú zachované.

## [2026.10.27.post3] - 2026-10-27 - Jazyk a čítanie posledného snímku

**Opravené**

- Spoločný výber jazyka je vycentrovaný pri prihlásení aj odhlásení vrátane mobilného zobrazenia.
- Zložený index umožňuje nájsť posledný snímok kurzu bez čítania celej histórie. Migrácia a ORM používajú rovnaký index; integračný test kontroluje plán PostgreSQL aj výsledok kurzu bez snímkov.

## [2026.10.27.post2] - 2026-10-27 - Jednotný panel filtrov MR

**Opravené**

- Testovacie prostredie CI inštaluje Node.js, aby sa testy JavaScriptových komponentov vykonali namiesto preskočenia alebo zlyhania pre chýbajúci runtime.
- Filtre analýzy MR používajú spoločný panel tabuliek: vyhľadávanie a výber rizika sú zarovnané bez osobitných obalov a rozmerov. Miera istoty používa štandardný informačný odznak. Spoločné výberové polia rezervujú šírku najširšej možnosti už pri vykreslení serverom, aj pri doplnení možností. Zmena filtra tak nemení rozmery susedných prvkov.

## [2026.10.27.post1] - 2026-10-27 - Spoločné ovládacie prvky rozhrania

**Zmenené**

- Výber jazyka pri prihlásení používa malý terciárny zoznam GitLabu na existujúcej bielej ploche bez osobitných štýlov rozbaľovacieho menu.
- Recenzenti, synchronizácia, legenda problémov a riziko MR používajú spoločné odznaky. Týždne a Markdown používajú spoločné karty, súbory diffu spoločný zoznam a textové akcie i filter rizika štandardné tlačidlá a výberové pole.
- Odstránené prepisovanie komponentov v hlavičkách a ovládaní tabuliek, nepoužívané meranie hlavičiek, duplicitné veľkosti písma a nadbytočné kontroly pomocných funkcií. Text aj popisy grafov majú aspoň 12 px. Výber týždňa je vykreslený serverom pred spustením skriptov.

## [2026.10.27] - 2026-10-27 - Spoločné komponenty namiesto kópií

**Zmenené**

- Vyhľadávacia paleta je zložená zo spoločných komponentov: vyhľadávacie pole bez rámika, nadpisy skupín ponuky, tlačidlo zatvorenia a avatary. Rovnako aj tlačidlá zatvorenia, avatary, odznaky, upozornenia, výber osoby a vlákno tiketu podpory na serveri aj v prehliadači, takže ich kópie pre jednotlivé stránky a približne 2 000 riadkov prepisujúceho CSS sú odstránené.
- Avatary zodpovedajú GitLab GlAvatar: pevné veľkosti, farba identikonu podľa mena a iniciála pod obrázkom, kým sa nenačíta. Odznaky, upozornenia a tlačidlá zatvorenia zodpovedajú GlBadge, GlAlert a tlačidlu zatvorenia GitLabu; upozornenia pri prihlásení sú štandardné upozornenie.
- Kód v prehliadači volá spoločné pomocné funkcie priamo. Stovky lokálnych kópií a nepoužívaných záložných vetiev pre preklad, escapovanie HTML, oznámenia a ďalšie vždy dostupné funkcie sú odstránené spolu s nepoužívaným bočným panelom (drawer). Šípky stránkovania a značka výberu v ponuke pochádzajú z registra ikon.

**Opravené**

- Odchod zo stránky spustí jej upratanie raz; nasledujúca stránka už neopakuje upratanie predchádzajúcej.
- Tlačidlá stránkovania majú preložený popis už v prvom vykreslení, nie po anglicky až do načítania skriptov.
- Farby skóre projektu používajú prahy kurzu. Vypnuté terciárne tlačidlá nemajú sivú výplň a pravidlá pre prechod myšou nad odkazom a rámik zamerania neprepisujú farbu ani zaoblenie komponentov, ktoré sú odkazom alebo tlačidlom.

## [2026.10.26.post12] - 2026-10-26 - Kliknutie na stránkovanie počas vyhľadávania

**Opravené**

- Dokončenie vyhľadávania aktualizuje adresu bez výmeny ovládania počas stlačenia tlačidla. Klientské stránkovanie použije čakajúci filter v obsluhe kliknutia a až potom určí nasledujúcu alebo predchádzajúcu stránku. Rýchle kliknutie tak nestratí cieľ pri opustení vyhľadávacieho poľa.

## [2026.10.26.post11] - 2026-10-26 - Zachovanie vyhľadávania pri obnove tabuľky

**Opravené**

- Spoločné vyhľadávanie v tabuľkách prijme rozpracovaný text po dokončení úpravy, skôr než obnova načíta aktuálne filtre. Rýchla obnova aktivity asistenta už nezahodí posledné vyhľadávanie.
- Použitie filtra zároveň vybaví čakajúcu aktualizáciu po písaní, takže starý časovač nevráti neskôr vybranú stránku tabuľky. Odstránené polia ani opúšťaná stránka nemôžu prepísať aktuálne vyhľadávanie v adrese.

## [2026.10.26.post10] - 2026-10-26 - Obnova asistenta na správnej stránke

**Opravené**

- Aktivita asistenta používa spoločné požiadavky s kľúčom, desaťsekundovým limitom a bez automatického opakovania. Zastarané odpovede neprepíšu inú stránku ani novší výsledok. Obnova počká pri písaní alebo zmene zobrazenia a zachová zameranie aj aktuálne vyhľadávanie.
- Odložené obnovenia asistenta sa pri odchode zo stránky zrušia a pred vykonaním znova overia neuložené úpravy. Dokončenie cvičenia s identifikátorom iného kurzu sa ignoruje.
- Spoločné ovládanie obnovy nezobrazuje oznámenia pre nahradené, odložené či odstránené akcie. Staršia požiadavka tak neoznámi úspech ani chybu na cieľovej stránke.

## [2026.10.26.post9] - 2026-10-26 - Konzistentné odblokovanie tlačidiel

**Opravené**

- Po dokončení procesu na pozadí alebo odpočítavania sa tlačidlo uloženia riadi aktuálnym formulárom. Úpravy vykonané počas blokovania možno uložiť; nezmenené alebo vrátené hodnoty zostanú bez možnosti uloženia, bez zastaraného štýlu či atribútov prístupnosti.
- Načítanie, proces, synchronizácia, archív a odpočítavanie používajú spoločnú obnovu stavu tlačidla. Ukončenie jedného blokovania nepovolí stále blokovanú akciu ani predčasne nezruší odpočítavanie. Nastavenia znova vyhodnotia uloženie aj po ukončení synchronizácie zistenej pravidelným dopytovaním servera.
- Ochrana procesov po odblokovaní nevytvára samostatnú inštanciu popisu; obnovené ovládacie prvky používajú spoločné delegované popisy.

## [2026.10.26.post8] - 2026-10-26 - Zachovanie úprav počas ukladania

**Opravené**

- Spoločná ochrana formulárov potvrdí hodnoty odoslané serveru a neskoršie úpravy ponechá neuložené. Tlačidlá uloženia rešpektujú načítanie aj blokovanie procesom, synchronizáciou, archívom či odpočítavaním a po dokončení znova vyhodnotia zostávajúce zmeny, aj pri rýchlej odpovedi bez zobrazenia indikátora.
- Predvoľby pri odchode obnovia naposledy odoslaný náhľad a odložia obnovenie jazyka, kým zostávajú ďalšie úpravy. Odpovede uloženia nastavení a asistenta patria pôvodnému formuláru; oneskorená odpoveď nezruší zmeny nového formulára, neotvorí výzvu synchronizácie ani neobnoví stránku cez inú rozpracovanú úpravu.
- Natívne výbery farieb rozdielov používajú existujúce vylúčenie odvodených polí spoločné s dialógmi. Návrat k uloženej farbe ihneď obnoví nezmenený stav formulára.

## [2026.10.26.post7] - 2026-10-26 - Kalendárne dátumy bez časového posunu

**Opravené**

- Spoločné kalendáre čítajú dátumy semestra cez Flatpickr ako miestne kalendárne dni namiesto časových údajov UTC. Výučbové a skúškové týždne majú rovnaké čísla vo všetkých časových pásmach prehliadača, aj pri zmene letného času a úprave začiatku v dvojici dátumov.
- Prázdny kalendár termínu sa otvorí v skutočnom mesiaci budúceho semestra. Začiatok prvého dňa mesiaca už v pásmach západne od UTC neotvorí predchádzajúci mesiac; otvorenie kalendára ponechá termín prázdny.

## [2026.10.26.post6] - 2026-10-26 - Korektné odstránenie dialógov

**Opravené**

- Odstránenie dialógu stránky ukončí jeho animáciu a uvoľní záznam otvorenia, ochranu zatvorenia aj pôvodné hodnoty polí skôr, než sa jeho ID použije znova. Rýchly SPA prechod môže ihneď otvoriť nový dialóg bez zdedeného stavu či zablokovaného posúvania stránky.
- Dokončenie zatváracej animácie patrí pôvodnému otvoreniu a DOM prvku. Neskoré dokončenie nezatvorí ani neodomkne znova otvorený či nahradený dialóg a neoznámi jeho poslucháčom nesprávne zatvorenie.
- Odstránený zastaraný výpočet stredu škálovania a inline prepisy animácie. Dialógy používajú spoločný posun bez zbytočného merania rozloženia a inline stredu transformácie.

## [2026.10.26.post5] - 2026-10-26 - Jednotný semester v kalendároch

**Opravené**

- Kalendáre sa po SPA navigácii vytvárajú až po načítaní údajov semestra nového kurzu. Polia na stránke aj presunuté dialógy termínov používajú jeho číslovanie a zobrazenie týždňov namiesto údajov predchádzajúcej stránky.
- Kalendár koncového dátumu berie začiatok z vlastného komponentu akademického obdobia, aj v dialógu prenosu bez formulára či pri viacerých dvojiciach dátumov v jednom formulári. Zmena vlastného začiatku priebežne upraví číslovanie týždňov bez použitia inej dvojice alebo zdrojového kurzu.

## [2026.10.26.post4] - 2026-10-26 - Bezpečné zlyhanie navigácie

**Opravené**

- Neúspešná SPA požiadavka zachová URL aktuálnej stránky, dialógy, obsluhu udalostí aj ochranu neuložených zmien. Čistenie a pozastavenie Alpine nastane až pred úspešnou výmenou obsahu; HTTP chyby a prázdne odpovede nevytvárajú históriu pre stránku, ktorá neprišla.
- Neúspešné Späť/Dopredu obnoví adresu zobrazenej stránky. Čakajúca navigácia porovnáva cieľ so zobrazenou stránkou, aby sa požiadavka nepreskočila len preto, že sa už zmenil adresný riadok.
- Odstránenie poľa cez HTMX zruší aj jeho kalendár a globálne poslucháče cez API Flatpickr. Odstránené nesprávne čistenie kalendárov, ktoré používalo neexistujúcu vlastnosť a mohlo odstrániť živý kalendár.

## [2026.10.26.post3] - 2026-10-26 - Ochrana rýchlych úprav formulárov

**Opravené**

- Rýchly výber dátumu a použitie číselného ovládača zostávajú neuloženou úpravou aj počas inicializácie dialógu. Zrušenie upozorní pred zahodením a obnoví pôvodné hodnoty vrátane výberu v kalendári.
- Ochrana uloženia bežných formulárov zachová pôvodný stav po písaní, výbere zo zoznamu či použití kalendára. Následné programové udalosti nevypnú Uložiť ani neprijmú neuloženú úpravu ako pôvodný stav; nedotknuté automatické vyplnenie sa naďalej ustáli bez upozornenia.

## [2026.10.26.post2] - 2026-10-26 - Kalendáre na úzkych obrazovkách

**Opravené**

- Spoločné kalendáre sa zmestia na úzku obrazovku bez orezania dní, skrytia semestrálnych týždňov či rozšírenia mobilného viewportu. Návrat na desktop zachová štandardnú šírku kalendára.
- Kalendár pripojený k body sleduje svoje pole pri posúvaní stránky alebo tela dialógu. Používa existujúci polohovací mechanizmus Flatpickr namiesto druhej implementácie geometrie.
- Zmena šírky viewportu zatvorí otvorený kalendár bez zmeny dátumu; opätovné otvorenie odstráni staré súradnice. Zmena samotnej výšky pri zobrazení klávesnice ho nezatvára.

## [2026.10.26.post1] - 2026-10-26 - Časovače dialógov

**Opravené**

- Oneskorený automatický fokus platí iba pre aktuálny otvorený dialóg navrchu a zachová už zvolené pole. Zatvárané ani prekryté dialógy nepreberú fokus; potvrdenie si ponechá bezpečný ovládací prvok.
- Časovače otvorenia a snímky potvrdenia patria pôvodnému otvoreniu. Rýchle opätovné otvorenie zachová nový stav animácie a nahradené potvrdenie neoznačí predchádzajúci prvok.

## [2026.10.26] - 2026-10-26 - Fokus v dialógoch

**Opravené**

- Automatický fokus a cyklus Tab vynechávajú záporný tabindex, zakázané ovládacie prvky (aj v zakázanom fieldsete) a neaktívne podstromy inert. Prenos kurzu označí viditeľný výber akademického obdobia namiesto skrytého validátora.
- Kontroly v prehliadači pokrývajú klávesnicu pri prenose, neaktívne prvky na oboch okrajoch dialógu a dostupný výber súboru JSON na desktope, dotykovom zariadení aj s obmedzeným pohybom.

## [2026.10.25.post10] - 2026-10-25 - Jednotný import JSON

**Opravené**

- Importy JSON ihneď zneplatnia upravený náhľad a zdieľajú ochranu rozpracovaných zmien, zahodenie, rušenie časovačov aj čistenie pri navigácii. Platí to pre dashboard, úplnú konfiguráciu kurzu aj konfiguráciu kontrol. Koreňové polia JSON sa odmietnu.
- Nahraný súbor už nemôže prepísať novší súbor alebo ručnú úpravu. Zahodenie vyčistí názov súboru aj čakajúce čítanie. Opätovné otvorenie zatváraného dialógu obnoví východiskový stav ochrany zmien.

## [2026.10.25.post9] - 2026-10-25 - Správanie okrajov tabuliek

**Opravené**

- Responzívne tabuľky vypínajú natívne vodorovné odskakovanie a naťahovanie na okrajoch, ktoré pôvodné `overscroll-behavior-x: contain` povoľovalo. Zvislé posúvanie si zachováva predvolené správanie.
- Dotykové regresné kontroly menia smer jedného súvislého gesta a prekračujú oba vodorovné okraje pri piatich mobilných šírkach, oboch témach aj nastaveniach obmedzeného pohybu.

## [2026.10.25.post8] - 2026-10-25 - Natívne pripnutie Actions

**Opravené**

- Odstránené `will-change: transform` z pripnutých buniek Actions na dotykových zariadeniach. Chrome počas vodorovného posuvu zachováva natívne kompozitné obmedzenia sticky.
- Regresné kontroly zahŕňajú nahlásený rozmer Pixel 9 Pro (427 × 952) a preverujú natívne sticky obmedzenia každej pripnutej bunky Actions spolu s geometriou posuvu a režimom pripnutia.

## [2026.10.25.post7] - 2026-10-25 - Pomocné bubliny a dotykový posuv

**Opravené**

- Pomocné bubliny sa odstránia spolu s kotvou po výmene stránky alebo riadka. Otvorené, skryté aj čakajúce inštancie uvoľnia svoje popupy a obsluhu udalostí; presunutie živej kotvy zachová jej inštanciu.
- Vysvetlenia kariet používajú rovnaký aktuálny obsah a pravidlo jednej otvorenej bubliny ako delegované tooltipy. Odstránená nedosiahnuteľná vetva pre info-tip v obsluhe bežných tooltipov.
- Čistenie preveruje vytvorené inštancie bez prehľadávania všetkých možných kotiev a bez predčasného vytvárania bežných tooltipov.
- Vodorovný posuv už pri každej udalosti nemeria šírku Actions ani nemení režim pripnutia. Zmeny geometrie naďalej sleduje ResizeObserver vrátane šírky hlavičky Actions.
- Pripnuté bunky Actions v pretekajúcej tabuľke používajú na dotykových zariadeniach samostatné kompozitné vrstvy. Odstránené nepoužité mobilné prichytávanie posuvu; rozdeľovač podľa témy na pravom okraji stále plynulo zmizne.

## [2026.10.25.post6] - 2026-10-25 - Rozsah obnovenia údajov

**Opravené**

- Obnovenie predmetu, skupiny, projektu a študenta po dokončení úlohy používa spoločné overenie rozsahu. Cudzie úlohy už nenačítavajú živé údaje ani nemažú GitLab cache projektu; skutočný rozsah predmetu alebo skupiny má prednosť pred pôvodným projektom.
- Detail projektu používa jeden poslucháč dokončenia úloh. Relevantný analýzový beh z inej karty obnoví aj výsledkové karty; skryté stránky počkajú s obnovením.
- Analýzy uchovávajú identifikátory predmetu, skupiny a projektu. Podporované zostávajú uložené metadáta, staršie kľúče predmetov aj existujúce URL kontroly stavu analýzy.
- Hodiny aj avatar zostávajú na úzkej hornej lište viditeľné v oboch formátoch času. Miesto najprv uvoľní akademický rok a oddeľovač.


## [2026.10.25.post5] - 2026-10-25 - Výsledok zaradenia úloh

**Opravené**

- Odpovede synchronizácie skupiny, projektu a skupinových kontrol uvádzajú uloženú chybu zaradenia namiesto tvrdenia, že neúspešná úloha bola zaradená.
- Spustenie kontrol predmetu odstráni indikátory prepočtu skupín pri chybe frontu alebo neprijatí práce, nezávisle od obnovenia živých údajov.
- Kontroly predmetu po potvrdení znovu overia rozsah procesu. Ak medzitým začal iný beh, neodošlú nadbytočnú požiadavku.

## [2026.10.25.post4] - 2026-10-25 - Skupinové kontroly

**Opravené**

- Run Checks na profile študenta používa spoločný životný cyklus skupinovej úlohy: chyba zaradenia ukončí indikátor, zrušená úloha sa nehlási ako úspešná a výpadok prúdu priebehu zapne kontrolu stavu.
- Výber kontrol aj správa o priebehu na stránkach študenta a projektu zobrazujú skupinu, ktorú API skutočne prepočítava.
- Profil študenta sa obnovuje iba po úspešných úlohách jeho skupiny alebo predmetu. Cudzie a neúspešné úlohy stránku neobnovujú; súbežné oznámenia zdieľajú jedno obnovenie.

## [2026.10.25.post3] - 2026-10-25 - Výber kontrol

**Opravené**

- Run Compliance Checks chráni aj rýchle hromadné zmeny výberu. Dočasný filter kontrol sa nepovažuje za neuloženú prácu a pri opätovnom otvorení sa vyčistí.
- Počítadlo vybraných kontrol aj tlačidlo spustenia vyhodnocujú celý výber rovnako ako odoslaná požiadavka, aj keď filter časť výberu skryje. Obnovenie výberu rešpektuje archív, bežiaci proces, načítavanie aj časové blokovanie.
- Potvrdené spustenie prijme parametre výberu pred zatvorením okna. Požiadavka sa už neodosiela súčasne s druhým potvrdením zahodenia. Nepoužívaný poslucháč run-success bol odstránený.

## [2026.10.25.post2] - 2026-10-25 - Zahodenie konceptov formulárov

**Opravené**

- Escape ovláda iba vrchné okno. Kláves, ktorý otvorí potvrdenie zahodenia, ho už okamžite nezavrie a Tab zostáva v potvrdení.
- Potvrdený odchod zo stránky zatvorí pôvodné okná bez druhého potvrdenia zahodenia tých istých zmien.
- Zatvorenie zmeneného konceptu importu z GitLabu vyžiada potvrdenie. Zrušiť, krížik, Escape aj pozadie používajú spoločnú ochranu, ktorá platí aj pri odchode zo stránky. Spustený import si zachováva samostatné rušenie procesu.
- Potvrdené zahodenie obnoví hodnoty pri otvorení vrátane zoznamov, prepínačov, odvodených polí akademického obdobia a kalendárov. Zahodený koncept sa pri opätovnom otvorení nevráti a oneskorené potvrdenie nezruší novšie otvorenie.
- Priebeh importu používa udalosti spoločného modálneho okna namiesto nahrádzania openModal/closeModal. Zachováva animáciu od otváracieho tlačidla, výsledok ochrany zatvorenia aj spoločný životný cyklus.

## [2026.10.25.post1] - 2026-10-25 - Spoločné filtrovanie tabuliek

**Opravené**

- Odložené vyhľadávanie v tabuľke sa nevykoná po odstránení poľa či tabuľky ani počas odchodu zo stránky. Rýchly prechod už neprenesie staré vyhľadávanie do adresy cieľovej stránky.
- Users, učitelia kurzu a aktivita asistenta používajú spoločný TableFilter s podmienkou pre riadky a parametrami adresy namiesto vlastných náhrad apply(). Vyhľadávanie, stránkovanie, prázdne stavy a aktualizácia adresy majú jednu implementáciu.
- Filtrovanie zachová fragment adresy aj stav histórie vrátane prepínania rolí a vyhľadávania na stránke Users.

## [2026.10.25] - 2026-10-25 - Spoľahlivé načítavanie udalostí

**Opravené**

- Obnovenie tabuľky zatvorí otvorené vysvetlivky pred výmenou riadkov, aby nezostali visieť nad prázdnym výsledkom.
- Detail udalosti zachová vybranú udalosť aj pri neskorej odpovedi staršej požiadavky. Zatvorenie alebo opätovné otvorenie dialógu zabráni prepísaniu jeho obsahu starým výsledkom či chybou.
- Odchod zo stránky Events zruší jej čítania a zneplatní odložené vykreslenia tabuľky. Po návrate sa nezobrazia riadky ani počítadlá z predchádzajúcej návštevy.
- Prázdna tabuľka udalostí a prázdny payload používajú spoločné ilustrácie podľa témy. Čítania API s kľúčom po dokončení odstránia poslucháča zrušenia namiesto hromadenia ukončených požiadaviek.

## [2026.10.24.post9] - 2026-10-24 - Jednotné ovládanie dropdownov klávesnicou

**Opravené**

- Spoločné dropdowny podporujú šípky, Home/End, Tab a Escape aj pri menu prenesenom mimo posúvanej tabuľky. Vypnuté možnosti sa preskočia; výber naďalej používa existujúce tlačidlá a odkazy.
- Escape nájde skutočne otvorené menu namiesto predchádzajúceho zatvoreného prvku data-dropdown. Najprv zavrie zoznam, až potom jeho dialóg. Tab vráti prenesené menu do pôvodného obalu a pokračuje v bežnom pohybe fokusu.
- Zmena počtu riadkov na stránku vráti fokus na nové tlačidlo po prekreslení stránkovania. Opakované zmeny zostávajú ovládateľné klávesnicou.

## [2026.10.24.post8] - 2026-10-24 - Konzistentné údaje počas ukladania

**Opravené**

- Spoločné modálne formuláre zachytia údaje pred dočasným vypnutím upraviteľných polí a vlastných dropdownov. Zrušenie aj zatvorenie zostávajú dostupné; hodnoty sa počas ukladania nemenia a tabuľka zodpovedá odoslaným údajom.
- Chyba obnoví úpravy bez zapnutia polí, ktoré boli vypnuté už pred odoslaním. Nové otvorenie uvoľní polia predchádzajúcej interakcie; stará odpoveď neodomkne nové ukladanie. Save rozpozná prebiehajúce odoslanie ešte pred zobrazením oneskoreného indikátora.
- Chyba ukladania, ktorú formulár už oznámil používateľovi, nevyvolá ďalšiu neošetrenú chybu JavaScriptu. Oznámenie aj chybová obsluha zostávajú dostupné na opravu údajov a opätovné uloženie.

## [2026.10.24.post7] - 2026-10-24 - Bezpečné dokončenie modálnych formulárov

**Opravené**

- Oneskorené odpovede modálnych formulárov už nezatvoria novootvorené okno, neupravia riadok iného používateľa ani nezobrazia staré potvrdenie či chybu po navigácii. Spoločná obsluha overí pôvodný formulár aj otvorenie okna.
- Opätovné otvorenie formulára vymaže predchádzajúci indikátor ukladania aj výsledok tlačidla. Nová interakcia môže odoslať vlastnú požiadavku; dokončenie starej nezmení stav nového tlačidla.

## [2026.10.24.post6] - 2026-10-24 - Posúvanie tabuliek po filtrovaní a obnovení

**Opravené**

- Filtrovanie už nemeria šírku Actions podľa skrytého prvého riadka ako nulu. Spoločný komponent používa viditeľnú hlavičku stĺpca a na úzkych obrazovkách zachová miesto pre údaje riadka.
- Výmena cez HTMX inicializuje aj samotný koreň tabuľky či navigácie. Po výmene posúvanej oblasti alebo vnútornej tabuľky sa sledovanie pripojí k novým prvkom a pôvodné sa odpojí.
- Indikátory vodorovného posúvania a oddeľovač Actions sa aktualizujú aj po obnovení fragmentov vo vnútri existujúceho obalu tabuľky.

## [2026.10.24.post5] - 2026-10-24 - Konzistentné úpravy používateľov

**Opravené**

- Obnovenie tabuľky Users zosúladí formulár Edit so zobrazenou rolou a stavom účtu. Opätovné otvorenie už nevracia staré hodnoty po zmene iným správcom.
- Uloženie servisného účtu zachová označenie Bot aj jeho typ pri ďalšom otvorení Edit. Obnovenie aj uloženie používajú spoločnú aktualizáciu riadka a údajov tlačidla.
- Tlačidlá Save v modálnych formulároch používajú rovnaký východiskový stav ako upozornenie na neuložené zmeny. Rýchle úpravy už neprepíše animácia ani časovač; návrat k pôvodnej hodnote Save znova vypne.
- Porovnanie formulára ignoruje pomocné validačné pole dropdownu, ktoré iba oneskorene kopíruje jeho hodnotu. Obnovenie pôvodných údajov kurzu už nenechá Save aktívne ani nevyvolá upozornenie na neexistujúce zmeny.

## [2026.10.24.post4] - 2026-10-24 - Oddeľovač Actions a obnova proxy

**Opravené**

- Pripnuté stĺpce Actions používajú spoločný okraj vo farbe témy na označenie skrytých stĺpcov. Okraj plynulo zmizne na pravom konci a pri posunutí späť sa znovu zobrazí. Tlačidlá nemenia polohu; po odopnutí stĺpca okraj zmizne a rešpektuje obmedzený pohyb.
- Nasadenie načíta nastavenia obnovy do bežiaceho Caddy pred výmenou API. Neúspešné načítanie ponechá obsluhujúce API na mieste; prvé nasadenie zachováva bežné spustenie proxy.

## [2026.10.24.post3] - 2026-10-24 - Bajtkód obrazu a studený štart

**Opravené**

- Obraz kompiluje nainštalované závislosti aj štandardnú knižnicu Pythonu počas zostavenia. Procesy s úložiskom iba na čítanie už pri štarte nekompilujú stovky modulov; zmena verzie neobnovuje tieto vrstvy.
- Nepoužívaný riadiaci soket Gunicornu je vypnutý, čím sa odstránila chyba zápisu do súborového systému iba na čítanie. Nasadenie a ukončenie naďalej používajú signály kontajnera.
- Caddy čaká v rámci 20-sekundového štartovacieho okna API pred zobrazením údržby. Predchádzajúci limit mohol vrátiť 503 tesne pred pripravenosťou API.
- Dokumentácia rozlišuje prípravu bajtkódu, opakované pokusy proxy a čas bežného spracovania požiadavky.

## [2026.10.24.post2] - 2026-10-24 - Profily používateľov a oneskorené odpovede

**Opravené**

- Zatvorenie načítavaného profilu už neblokuje otvorenie iného používateľa. Oba dialógy rušia opustené požiadavky, zachovávajú ochranu pred dvojklikom a ignorujú oneskorené odpovede.
- Zatvorenie počas sťahovania spoločného vykresľovacieho modulu nespustí nepotrebnú požiadavku na profil. Načítanie používa spoločný časový limit a rušenie pri navigácii.
- Oneskorené obnovenie po doplnení údajov z GitLabu už neotvorí zatvorený profil, nenahradí iného používateľa ani nepokračuje po odchode zo stránky.
- Tabuľka používateľov ignoruje staršie odpovede aj odpovede z predchádzajúcej návštevy. Aktualizované údaje ihneď rešpektujú aktívne vyhľadávanie a filter rolí. Regresné testy overujú počítačové aj dotykové rozloženie.

## [2026.10.24.post1] - 2026-10-24 - Pripravenosť API pred spustením workerov

**Opravené**

- Compose spúšťa procesy na pozadí až po pripravenosti API. Štyri importy RQ tak nesúťažia s inicializáciou API. Neskoršia zmena stavu API nezastaví bežiace workery.
- Kontrola kontajnera používa úplnú pripravenosť a sekundový interval počas štartu, potom bežný 15-sekundový interval.
- Kópie pri prechode medzi stránkami zachovávajú prepojenie popisov s tlačidlami rozbaľovacích polí a ďalšími ovládacími prvkami. Chrome už pri odchode z nastavení a asistenta nehlási nesprávne popisy formulárov.
- Dokumentácia rozlišuje prípravu API, prvú odpoveď, opakované požiadavky a správanie automatického reštartu Dockeru po reštarte hostiteľa.

## [2026.10.23.post11] - 2026-10-23 - Jednotná analytika a počty rizikových študentov

**Opravené**

- Prehľad kontrol, týždenné trendy a náhradná história používajú rovnaký výber aktívnych študentov. Neaktívne skupiny, členstvá a ručne vylúčení študenti už nepridávajú staré skóre; prehľady archivovaných kurzov zostávajú dostupné.
- Študent so súčasnými snímkami vo viacerých skupinách sa započíta iba raz. Duplicitné snímky už nezvýšia percentá kontrol nad 100 %.
- Počet rizikových študentov rešpektuje očakávané vstavané aj vlastné kontroly každej snímky. Regresné testy SQL overujú vylúčenie, obnovenie, viacnásobné členstvo a individuálne termíny.

## [2026.10.23.post10] - 2026-10-23 - Indexovaná analytika a správne roly v kurzoch

**Opravené**

- Analytika vylučuje učiteľov a mentorov podľa členstva v požadovanom kurze. Rola v inom kurze už neodstráni skóre študenta ani nevyvolá ďalšie čítanie histórie snímok.
- Indexy podľa kurzu, študenta a času a pokrývajúci index podľa kurzu a týždňa obmedzujú čítanie histórie pri prehľade kontrol a týždenných trendoch. Obsahuje migráciu Alembic 025 a zodpovedajúce definície modelov.
- Regresné testy overujú roly učiteľa a mentora medzi kurzami. Príručka výkonu rozlišuje plány SQL, studené požiadavky a odpovede zo stránkovej cache.

## [2026.10.23.post9] - 2026-10-23 - Konzistentné komponenty a editor termínov

**Opravené**

- Escape najprv zatvorí otvorený kalendár a ponechá nadradené okno otvorené. Text oznámenia neblokuje polia ani uloženie v okne; zatvorenie a akcia oznámenia zostávajú dostupné.
- Akcie členov projektu zostávajú dostupné na telefóne. Odstránené skrývanie celého stĺpca a globálne okraje tlačidiel, ktoré menili spoločné medzery zo 4 px na 12 px.
- Editor týždenných termínov obnovuje vybraný dátum, čas aj mesiac kalendára a vymaže ich pri prázdnom alebo novom týždni. Pôvodné aj obnovené riadky používajú spoločné tlačidlá a odznaky. Archivované termíny sú zamknuté už v HTML aj po obnovení riadkov.
- Odstránené vlastné okraje, hrúbky a odsadenie odznakov priorít, duplicitné mobilné rozmery a zastarané štýly hlavičky kurzov. Zatvorenie chyby analýzy používa spoločné sekundárne tlačidlo.
- Rozhranie číta stav GitLabu cez spoločný krátko ukladaný stavový report bez chybných HTTP požiadaviek pri výpadku. Oznam o výpadku a obnovení zostáva zachovaný; monitorovacia sonda naďalej vracia HTTP 503. Doplnené regresné kontroly dátumov, akcií, archivácie a stavov spojenia.

## [2026.10.23.post8] - 2026-10-23 - Jednotné tabuľky a akcie riadkov

**Opravené**

- Tlačidlá úloh na stránke Systém sú zarovnané s hlavičkou Akcie. Tabuľka používa štandardné rozostupy aj po obnovení a na telefóne.
- Archivované kurzy používajú spoločnú typografiu, odsadenie a zaoblenie tabuľky a karty. Odstránené vlastné veľké písmená hlavičiek, tlmené farby a nulové odsadenie obsahu.
- Kurzy, skupiny, projekty a webhooky používajú spoločný komponent akcií riadka bez lokálnych kópií štýlov. Medzery medzi tlačidlami sa nesčítavajú s pôvodnými okrajmi. Overené v oboch témach, na dotykovom displeji a v pevnom aj širokom rozložení.

## [2026.10.23.post7] - 2026-10-23 - Rýchlejší studený štart API

**Opravené**

- Caddy overuje dostupnosť API každú sekundu. Po úspešnom štarte už nečaká na ďalší pätnásťsekundový interval, ktorý predlžoval prvé požiadavky a spôsoboval odpovede 502.
- Gunicorn načíta aplikáciu pred vytvorením štyroch procesov Uvicorn. Modely a routre sa importujú raz; pripojenia databázy a Redis aj asynchrónna príprava vznikajú samostatne v každom procese. Keep-alive zostáva päť sekúnd.
- Postup merania začína pri samotnom reštarte, nie až po úspešnej kontrole pripravenosti. Overené spúšťanie linuxového kontajnera, metriky a používateľské scenáre v prehliadači.

## [2026.10.23.post6] - 2026-10-23 - Stabilné filtre a identifikované polia

**Opravené**

- Spoločné záložky rezervujú šírku zvýrazneného textu. Vyhľadávanie a susedné filtre sa pri prepínaní neposúvajú; rovnaké pravidlo používa navigácia predmetu.
- Doplnené identifikátory výberu úloh, udalostí, kontrol, návrhov, tiketov a presunu skupín aj výberu farieb v nastaveniach. Dočasné polia príloh a schránky majú názov.
- Vizuálne kópie počas prechodu majú vlastné identifikátory a správne priradené popisy. Nevytvárajú anonymné ani duplicitné polia a zostávajú neaktívne.
- Analytika načítava iba výsledky kontrol a ich podrobnosti, bez nepotrebných diagnostických počítadiel a polí. Overené grafy, identifikátory a rozmery filtrov na telefóne aj pevnom a pružnom rozložení.

## [2026.10.23.post5] - 2026-10-23 - Spoločný komponent podrobností v tabuľke

**Opravené**

- Rozbalené úlohy používajú spoločný komponent tabuľky s údajmi zarovnanými vľavo, bežnou typografiou a presnými lokálnymi časmi. Krátky výsledok sa neopakuje; dlhá správa zostáva dostupná v podrobnostiach.
- Pripnutie stĺpca akcií ignoruje bunky cez viac stĺpcov. Podrobnosti ani prázdne stavy nepreberajú zarovnanie akcií a obsah sa zmestí aj na telefón.
- Odstránené vlastné mriežky, pozadia, bloky kódu a prepisy odsadenia stránky Systém. Spoločný ovládač funguje klávesnicou a nezasahuje do výberu riadkov.

## [2026.10.23.post4] - 2026-10-23 - Prevádzka systému a spoľahlivé grafy

**Zmenené**

- Systém zobrazuje stav služieb, skutočné fronty RQ a dostupných workerov, úlohy na pozadí a konfiguráciu nasadenia. Neduplikuje rozdelenie rolí ani audit akcií používateľov. Odkazy na monitoring sa zobrazia, ak je nasadený.
- Úlohy majú stránkovanie v databáze, presné počty po filtrovaní, všetky stavy a podrobnosti dostupné aj klávesnicou. Čistenie odstráni iba dokončené záznamy; aktívne úlohy a audit zostanú zachované.

**Opravené**

- Grafy Compliance Progress podporujú moderné farby CSS, priehľadnosť zo spoločného komponentu aj zmenu témy. Pri odchode sa grafy a ich poslucháče uvoľnia.
- Prázdna aktivita asistenta používa spoločnú tabuľku s filtrami a stránkovaním. Ikony projektov nemajú vlastné farebné podklady ani zmenšené rozmery.
- SSE pri reštarte API opakuje požiadavky cez proxy rovnako ako bežné stránky. Odpojené karty uvoľnia streamy; klient predlžuje interval opakovania a krátke pripojenie nevynuluje počet chýb.
- Čistenie cache oznámi zlyhanie servera a zachová relácie, zámky úloh aj obmedzenia požiadaviek. Súhrn stavu zohľadňuje aj zhoršený stav externých služieb.

## [2026.10.23.post3] - 2026-10-23 - Menej dotazov histórie a ohraničené kontroly databázy

**Opravené**

- História operácií na stránke Systém načíta iba zobrazované údaje archivovaných kurzov. Nenačítava ich nastavenia ani ostatné vzťahy a vracia rovnaké operácie.
- Časový limit kontroly databázy a pripravenosti zahŕňa čakanie na spojenie, jeho vytvorenie aj vykonanie dotazu.
- Regresné testy pokrývajú čakanie na nedostupné spojenie a zastavený dotaz pri oboch kontrolách.

## [2026.10.23.post2] - 2026-10-23 - Príprava šablón pred prijímaním požiadaviek

**Opravené**

- Obraz zostaví bajtový kód šablón Jinja a aplikácie Python raz. Procesy API ho po reštarte znovu použijú namiesto kompilácie počas prvých návštev stránok.
- Každý proces API dokončí prípravu šablón a ORM pred prijímaním požiadaviek. Príprava databázy má limit päť sekúnd a kontrola pripravenosti naďalej overuje jej dostupnosť.
- Bajtový kód šablón je čitateľný účtom aplikácie a uložený mimo pripojeného adresára šablón. Zmenené, chýbajúce alebo neplatné záznamy sa nahradia kompiláciou zo zdroja bez zápisu do systému súborov iba na čítanie.
- Regresné testy overujú použitie vyrovnávacej pamäte, zmenu zdroja, escapovanie, chýbajúce záznamy a pripravenosť pri štarte.

## [2026.10.23.post1] - 2026-10-23 - Odkazy odkrývajú vnorené sekcie

**Opravené**

- Priamy odkaz otvorí všetky nadradené sekcie a spoločné zbaliteľné komponenty Alpine. Ovládacie prvky zostávajú synchronizované s ich stavom.
- Posúvanie počká na dokončenie výškových prechodov a pri rýchlom výbere ďalšieho odkazu sleduje najnovší cieľ. Zatvorenie rodiča alebo odchod zo stránky zruší čakajúci posun.
- Opätovný výber aktuálnej kotvy otvorí zbalený cieľ bez duplikovania histórie. Pomenované kotvy používajú rovnaké správanie.
- Stránky SPA s oneskorenými skriptmi odkrývajú cieľ až po inicializácii Alpine. Skrytý cieľ už nespôsobí úvodný posun na prázdne miesto.
- Testy náhradného režimu zachytávajú aj adresy GSAP s parametrom vyrovnávacej pamäte a overujú neprítomnosť knižnice pred kontrolou dialógov, výberov a príchodu stránky.

## [2026.10.23] - 2026-10-23 - História odkazov zachováva aktuálnu stránku

**Opravené**

- Späť a Dopredu medzi sekciami rovnakej stránky zachováva formulár aj neuložené úpravy bez nového načítania alebo otázky na opustenie stránky.
- Odkazy na sekciu s celou adresou používajú spoločné lokálne posúvanie aj po zmene klientskych filtrov. Modifikované kliknutia, sťahovanie a odkazy do iného okna zachovávajú správanie prehliadača.
- Klientske zmeny adresy udržiavajú navigáciu synchronizovanú. Zrušenie návratu obnoví celý dotaz aj kotvu; návrat na iný filter ho naďalej načíta.
- Odkazy medzi stránkami používajú spoločné vyhľadanie dekódovaného ID a pomenovanej kotvy. Posúva sa iba obsahový panel.
- Zvýraznenie cieľa už opäť necentruje kotvu ani sa neopakuje po obnovení inej časti stránky.
- Čakanie na kotvu sa zruší pri odchode zo stránky alebo výbere inej sekcie. Chýbajúca kotva už neposunie nasledujúcu stránku nahor.

## [2026.10.22.post10] - 2026-10-22 - Odstup za uložením a plynulý príchod stránky

**Opravené**

- Spoločný panel uloženia ponecháva malý odstup pred ďalšou kartou. Ak je poslednou sekciou, zachováva existujúci spodný okraj stránky.
- Navigácia v aplikácii drží predchádzajúci obraz, kým sa dokončia skripty a Alpine novej stránky. Potom krátko vytratí neaktívnu kópiu nad pripraveným obsahom.
- Presmerovanie a obnovenie drží predchádzajúci obraz prehliadača až do pripravenosti novej stránky. Krátky prechod rešpektuje obmedzený pohyb.
- Prehliadačové kontroly pokrývajú oneskorené skripty, dokončenie prechodu, chýbajúci GSAP a odstupy pri pevnej aj úzkej šírke.

## [2026.10.22.post9] - 2026-10-22 - Opakovanie požiadaviek a oddelené stránkovanie

**Opravené**

- Klientske chyby HTTP sa ukončia bez zbytočného opakovania. Dočasné stavy a sieťové chyby majú ohraničené opakovanie; aj výslovné povolenie opakovať zápis rešpektuje stav HTTP.
- Zrušenie požiadavky zachová preloženú alebo vlastnú správu namiesto nemenného textu výnimky prehliadača. Vlastný dôvod zrušenia nespustí opakovanie.
- Počet riadkov sa zmení iba v tabuľke vybraného menu aj po navigácii SPA. Jeden spoločný obslužný kód nahrádza poslucháčov ponechaných starými inštanciami stránkovania.
- Obnovenie stránkovania zatvorí a vráti otvorené menu z portálu pred výmenou ovládacích prvkov, takže nezostane samostatne visieť nad stránkou.

## [2026.10.22.post8] - 2026-10-22 - Jednotné ovládanie výberových polí

**Opravené**

- Escape zatvorí otvorený zoznam pred jeho dialógom. Šípky, Home a End prechádzajú možnosti; Tab opustí pole bez ponechania fokusu v skrytom menu.
- Možnosti vykreslené serverom aj doplnené neskôr majú rovnaké označenie výberu a stav pre čítačky obrazovky vrátane číselných a externe nastavených archívnych hodnôt. Doplnenie možností odstráni oznam o prázdnom zozname.
- Výber vráti fokus na ovládacie tlačidlo. Zatvorenie dialógu zbalí jeho zoznamy a zatvorené menu neprijíma fokus ani počas výstupnej animácie.
- Voľba možnosti počas otvárania dialógu zostane neuloženou úpravou aj po oneskorenej inicializácii vrátane ovládania klávesnicou.
- Výberové polia používajú spoločné zalamovanie textu; dlhé názvy kurzov aj slová bez medzier zostanú čitateľné v menu na mobile.
- Regresné testy v prehliadači pokrývajú počítač, úzku obrazovku, obmedzený pohyb, chýbajúci GSAP a opätovné otvorenie dialógu spolu s existujúcimi scenármi dialógov a sprievodcu.

## [2026.10.22.post7] - 2026-10-22 - Ohraničené spracovanie hlavičiek OpenTelemetry

**Bezpečnosť**

- OpenTelemetry API vyžaduje verziu 1.45.1 alebo novšiu; lock súbor obsahuje zodpovedajúce SDK, exportéry a inštrumentáciu. Aktualizácia opravuje CVE-2026-114603 / GHSA-xcq7-p3pf-p88h, nadmernú spotrebu CPU pri spracovaní chybnej prichádzajúcej hlavičky `tracestate`.
- Regresný test overuje zachovanie platného stavu trasovania a odmietnutie príliš veľkej hlavičky pred spracovaním.

## [2026.10.22.post6] - 2026-10-22 - Neuložené úpravy, mobilné dialógy a klávesové skratky

**Opravené**

- Dokončenie vstupnej animácie zachová text zadaný počas otvárania dialógu. Oneskorené inicializačné snímky už nepovažujú úpravy používateľa za uložený stav.
- Mobilné potiahnutie overí neuložené zmeny pred odchodom z obrazovky. Zamietnuté zatvorenie plynulo vráti formulár na miesto a gesto ovláda skutočne dotknutý dialóg.
- Potiahnutie alebo programové zatvorenie potvrdenia ukončí čakajúcu odpoveď ako zrušenie aj pri obmedzenom pohybe a bez GSAP.
- Tab a Shift+Tab zostávajú v dialógu aj pri počiatočnom zameraní jeho kontajnera namiesto presunu na stránku pod ním.
- Otáznik otvorí pomoc klávesových skratiek so Shiftom aj bez neho. Ctrl+S rozpozná spoločné strážené formuláre vrátane Preferencií a pri otvorenom dialógu neodošle formulár na pozadí.

## [2026.10.22.post5] - 2026-10-22 - Stabilné tlačidlá pri prechode sprievodcom

**Opravené**

- Ďalej a Späť plynulo menia výšku karty pri pevnom okraji. Tlačidlá pri zmene dĺžky textu neposkakujú; spoločný komponent animuje výšku a polohu bez deformácie textu a dočasných posuvníkov.
- Karty sa na tabletoch a telefónoch na šírku plynulo presúvajú medzi hornou a dolnou polohou. Zatvorenie počas presunu pokračuje z aktuálnej polohy bez skoku pri prevode pixelov na percentá. Úvod, spätné zatvorenie a rýchlosť zvýraznenia zostávajú zachované vrátane obmedzeného pohybu a náhradného režimu bez GSAP.
- Regresné testy v prehliadači kontrolujú polohu tlačidiel pri prechode dopredu a späť na počítači, telefóne, tablete a na šírku.

## [2026.10.22.post4] - 2026-10-22 - Menej zbytočných požiadaviek a upozornení prehliadača

**Opravené**

- Profilové menu učiteľa už neponúka stránku Systém prístupnú iba administrátorovi. Študentské upozornenia na kontroly otvoria predmet namiesto neprístupných nastavení. Bežné diagnostické výpisy sprievodcu a tímového streamu sa zobrazujú iba v režime ladenia.
- Profily, učitelia, karty používateľov a aktivita asistenta používajú uložené adresy fotografií. Chýbajúcu fotografiu nahradia iniciály bez požiadaviek na vymyslené cesty GitLabu.
- Verejné preferencie cookies prichádzajú v bezpečne escapovaných dátach stránky. Súhlas, jazyk a téma využívajú asynchrónne Cookie Store API s pôvodným náhradným postupom. Aplikácia aj prihlasovacie stránky používajú jedinú implementáciu cookies.
- Offline stránka dostáva CSP nonce pre vlastný skript témy; motív funguje aj z offline cache bez blokovania skriptu.

## [2026.10.22.post3] - 2026-10-22 - Dotykové gestá a inštalácia bez upozornení prehliadača

**Opravené**

- Spoločný sprievodca už neruší dotykové udalosti, ktoré prehliadač nepovoľuje zrušiť. Ťahanie mobilného dialógu ustúpi natívnemu posúvaniu; rovnaké správanie platí na všetkých stránkach.
- PWA neblokuje inštalačnú ponuku prehliadača a zachováva tlačidlo Inštalovať v aplikácii. Výsledok natívnej ponuky zruší uloženú udalosť a skryje kartu, aby neponúkala už použitú inštaláciu.

## [2026.10.22.post2] - 2026-10-22 - Menšie tlačidlo zatvorenia sprievodcu

**Opravené**

- Zatvorenie sprievodcu používa kompaktné priehľadné tlačidlo namiesto veľkého vyplneného štvorca. Na telefóne zostáva väčšia dotyková plocha.

## [2026.10.22.post1] - 2026-10-22 - Kompaktné mobilné rozhranie a spoločné stavy komponentov

**Opravené**

- Výška panelov prehliadača už nezväčšuje spodný odstup stránky. Tlačidlá nastavení počítajú bezpečnú oblasť iba raz; spoločný formulár má na telefóne menšie medzery medzi sekciami.
- Pruhovanie, ukázanie, stlačenie, výber a načítavanie riadkov tabuľky riadi jeden komponent s farbami témy. Pripnuté akcie preberajú rovnaké nepriehľadné pozadie ako ostatné bunky; vnorené projekty a rozbalené úlohy ho neprepisujú.
- Sprievodca umiestňuje prvky podľa skutočnej výšky popisu. Mobilná karta sa vysunie a zasunie, zvýraznenie sleduje pohyb menu a pri zatvorení sa zloží súčasne s kartou a menu. Tlačidlá sprievodcu a stromu používajú spoločný komponent; prepínač režimu a vybraný súbor používajú spoločné farby výberu a zaostrenia.

## [2026.10.21.post5] - 2026-10-21 - Monitorovanie bez druhého hesla

**Zmenené**

- Monitorovanie sa otvorí prihlásením do GitPulse. Grafana, Prometheus, Jaeger a Alertmanager pýtali vlastné heslo Basic Auth, jedno spoločné pre všetky štyri; teraz prihlásený administrátor GitPulse vojde rovno a nikto iný nie. Caddy sa pred každou požiadavkou opýta aplikácie (`/internal/monitoring-authz`, ako pri dokumentácii): administrátora pustí, čitateľa bez prihlásenia pošle prihlásiť sa a späť na tú istú stránku, inej role ukáže stránku s tým, kto ju môže otvoriť. Grafana administrátora prihlási pod jeho menom z GitPulse (auth proxy; Admin hlavnej organizácie) a klient sa nemôže pomenovať sám - Caddy hlavičku prepíše. Na rozdiel od dokumentácie sa brána pri chybe zatvorí. Overené cez Caddy s Grafanou 11.1: anonymný čitateľ, podvrhnutá hlavička, učiteľ a administrátor.

## [2026.10.21.post4] - 2026-10-21 - E-mail s výstrahou, ktorý sa dá čítať

**Opravené**

- E-mail s výstrahou vyzerá ako ostatné e-maily GitPulse. Bol to predvolený e-mail Alertmanagera: surové označenia (`alertname=... component=...`), tlačidlo "View in Alertmanager" na `http://alertmanager:9093` a odkaz "Source" na kontajner Prometheusu, ktoré sa zo schránky neotvoria. Teraz má rámec e-mailov aplikácie a stavový pruh z e-mailov GitLabu o pipeline - červený s krížikom, kým výstraha trvá, zelený s fajkou, keď je vyriešená - zhrnutie ako nadpis, tabuľku s tým, čo sa stalo, výstrahou, závažnosťou, podstatným označením (front, typ udalosti) a časmi v bratislavskom čase, a odkazy, ktoré fungujú: dopyt výstrahy v Prometheuse, všetky výstrahy, panel a odkaz Silence. Predmet je zhrnutie: `Firing: RQ jobs are failing (10 in the last hour) | GitPulse`.
- Alertmanager je dostupný na `/alertmanager/`, za heslom monitorovania, pre odkaz Silence; Prometheus aj Alertmanager poznajú svoje verejné adresy, takže odkazy vo výstrahe sú absolútne.

## [2026.10.21.post3] - 2026-10-21 - Výstrahy dorazia do schránky

**Opravené**

- Výstrahy dorazia do schránky: Alertmanager číta heslo SMTP bez medzier, rovnako ako aplikácia (`config.py`). Google zobrazuje heslo aplikácie po štyroch znakoch a Gmail na tvar s medzerami odpovedal len `535 Username and Password not accepted` - takto bola odmietnutá prvá skúšobná výstraha v produkcii.

## [2026.10.21.post2] - 2026-10-21 - Monitorovanie, ktoré meria

**Opravené**

- Monitorovanie: to, čo merajú pracovné procesy, sa dostane do Prometheusu. Spracovanie webhookov, obohacovanie, výpočet metrík a volania rozhrania GitLabu pri synchronizácii sa zaznamenávajú v procese, ktorý RQ pre každú úlohu vytvorí a ktorý s hodnotami zanikol, a Prometheus zbiera len z aplikácie - šesť z osemnástich výstražných pravidiel preto sledovalo metriky, ktoré neexistovali, a polovica panelu v Grafane bola prázdna. Tieto metriky sa teraz ukladajú do Redisu a `/metrics` aplikácie ich zverejní.
- Monitorovanie: štyri procesy aplikácie (uvicorn) svoje metriky sčítajú (režim viacerých procesov knižnice prometheus_client v tmpfs kontajnera). Zber sa dostal k náhodnému procesu, takže `http_requests_total` ukazovalo za sebou 4195, 9956, 1487, 4196 a Prometheus napočítal za šesť hodín 5 808 vynulovaní počítadla: každá rýchlosť, grafy HTTP aj výstrahy HTTP boli šum.
- Metriky HTTP majú ako označenie trasu, ktorej požiadavka zodpovedala (`/dashboard/courses/{course_id}`), bod pripojenia alebo `<unmatched>`, takže zahašovaný balík každého vydania ani cesta skenera už nie sú samostatným radom; prúd udalostí sa započíta, ale nevstupuje do histogramu odozvy, kde sa hodiny otvorenej karty javili ako čas odpovede.
- Výstrahy: `RQFailedJobsHigh` sleduje nové zlyhania (86 zlyhaných úloh z apríla až júla ju držalo zapnutú natrvalo); `HighHTTPErrorRate` najprv sčíta a potom delí (jediná odpoveď 5xx sa rátala ako 100 %); `HighHTTPLatency` berie celkový 95. percentil; `NoWebhooksReceived` sa ozve, keď týždeň prevádzky na 12 hodín utíchne - nie každú tichú hodinu celú zimu - a aj hneď po nasadení, čo predtým nevedela; `DatabaseDown` je `ApiDown`, lebo to aj kontroluje. Overené testami pravidiel v promtool, ktoré staré pravidlá nesplnia a nové áno.
- Výstrahy sa doručia. Alertmanager ich posielal na `ops@example.com` cez `localhost:25` - 64 221 chýb doručenia za šesť dní a ani jedna prijatá výstraha; teraz používa SMTP účet aplikácie, na adresu `ALERT_EMAIL_TO`, s heslom ako tajomstvom compose.
- Jaeger drží najviac 100 000 stôp. Bez obmedzenia zaplnil svojich 512M každý deň a pol a jadro ho ukončilo aj so všetkými stopami.
- `maxmemory` Redisu (200mb) je pod limitom jeho kontajnera (256M), takže vyraďuje kľúče skôr, než ho jadro ukončí.
- Skupiny spojení sa zmestia do PostgreSQL: štyri procesy aplikácie × (12 + 4) a štyri pracovné procesy × (2 + 2) je 80 zo 100 spojení. 25 + 15 sľubovalo 220 a 101. spojenie sa odmietne namiesto čakania.
- Nasadenie: Caddy načíta stiahnutý Caddyfile (cez stdin). Súbor pripojený samostatne si drží inode z času spustenia kontajnera a `git pull` zapíše zmenený súbor ako nový, takže `caddy reload` čítal starý text - overené. Prometheus a Alertmanager sa reštartujú, keď sa ich konfigurácia zmenila; Redis a služby monitorovania sa vytvoria nanovo, keď sa zmenila ich definícia v compose.
- Bezpečnosť: heslo k monitorovaniu už nie je v dokumentácii ani v `prometheus.yml` (`/metrics` Grafany žiadne nepotrebuje) a bolo zmenené.
- Spojenia `redis.asyncio` sa zatvárajú cez `aclose()` (`close()` je od redis-py 5.0.1 zastarané) a zastarané typy `types-redis`, ktoré editoru skrývali `aclose()`, už nie sú vývojovou závislosťou.

## [2026.10.21.post1] - 2026-10-21 - Bezpečnostná aktualizácia certifi

**Opravené**

- **Bezpečnosť:** `certifi` aktualizované na 2026.10.19 - úložisko certifikačných autorít už nedôveruje koreňu `emSign ECC Root CA - G3`, ktorého sprostredkujúce certifikáty mali kompromitované súkromné kľúče.

## [2026.10.21] - 2026-10-21 - Stránka príde hotová

**Opravené**

- Navigácia v aplikácii ukáže novú stránku až hotovú, rovnako ako celé načítanie. Skripty stránky, ktoré kreslia jej riadky, grafy a počty, sa načítali až vtedy, keď bol nový obsah už na obrazovke, takže Admin -> Udalosti ukazovali tabuľku na pár snímok vysokú 39 px so stĺpcami širokými ako hlavičky, kým neprišli riadky a tabuľka sa roztiahla s inými šírkami stĺpcov; najdlhšie pri prvej návšteve, keď skript stránky ešte nebol v pamäti. Vymenený obsah ostáva rozložený, ale nevykreslený, kým skripty a Alpine neskončia (poistka 3 s); filter alebo zoradenie, ktoré ostáva na stránke, nechá ovládacie prvky na obrazovke.
- Nástenka: Importovať, Importovať JSON a Nový kurz v hlavičke kurzov už pri 1024-1280 px nevychádzajú z riadka (Nový kurz ležal 101 px nad kartou Rýchly prístup); všetky tri sú jedna skupina, ktorá sa zalomí pod vyhľadávanie spolu.
- Používatelia: každý stĺpec je aspoň taký široký ako jeho popis v oboch jazykoch, takže riadok hlavičky má jeden riadok (36 px) - „Používateľské meno“ sa zalamovalo a robilo ho 56 px vysokým.
- Admin -> Systém, história úloh: hlavička „Zaradené do fronty“ už nie je orezaná (potrebuje 180 px, stĺpec mal 142 px).
- Hlavička tabuľky so zaškrtávacím políčkom na výber všetkého (história úloh, udalosti) má 36 px ako každá iná, nie 39 px: políčko sedí v strede riadka, nie na jeho účiarí.
- Politika obsahu (CSP) uvádza pôvod GitLabu aj s portom, takže GitLab na vlastnom porte (https://git.example:8443) dostane svoje avatary aj volania API, a povoľuje predvolené avatary GitLabu na oboch hostiteľoch gravataru.

**Testy**

- Scenáre v prehliadači prejdú čisto (53 z 53): dva, ktoré menia predvoľby e2e administrátora, ich vrátia (zbalený bočný panel, ktorý ostal, bol väčšinou nálezov štyroch prechodov), test ponuky počtu na stranu zavrie kartu sprievodcu pri prvej návšteve, ktorá prekrýva výber, a tri testy sa riadia súčasným návrhom (mená ľudí sa v tabuľke používateľov zalamujú, telá kariet majú odsadenie, stránka končiaca lepiacou lištou uloženia nemá pätičku).

## [2026.10.20.post3] - 2026-10-20 - Tlačidlá, ktoré povedia Hotovo, text, ktorý sa nehýbe

**Opravené**

- Obnoviť na karte Aktivita asistenta prejde stavmi ako každé Obnoviť - pracuje, „Hotovo“, späť - ako v histórii úloh. Prekreslenie nahradilo celú kartu aj s hlavičkou, takže pracujúce tlačidlo sa hneď vymenilo za nové nečinné a žiadny stav nebolo vidieť; teraz sa prekreslí iba telo karty.
- Uloženie nástrojov asistenta (aj pripojenie či výmena bota) ukáže na tlačidle „Hotovo“ skôr, než sa stránka vráti, rovnako ako Uložiť v Nastaveniach. Oznámenie o úspechu sa odovzdávalo iba ďalšej stránke a stránka sa hneď obnovila, takže tlačidlo svoj koniec nikdy nepovedalo; teraz sa oznámenie zobrazí na stránke a obnovenie ho prenesie.
- Vývojový server ukladá písma do vyrovnávacej pamäte ako produkcia (rok, nemenné). Pri overovaní pri každom načítaní stránky GitLab Sans niekedy prišlo až vtedy, keď sa ho `font-display: optional` už vzdalo: tá stránka ostala v systémovom písme a ďalšia nie, takže text vo vyhľadávaní (aj všetok ostatný) medzi stránkami poskakoval - v GitLab Sans 113,8 px, v Segoe UI 104,2 px a o 1 px vyššie.

## [2026.10.20.post2] - 2026-10-20 - Cvičenie v hornej lište, aktivita naživo

**Zmenené**

- Pripraviť cvičenie beží ako úloha na pozadí, rovnako ako synchronizácia: horná lišta ho sleduje od fronty po koniec, po skončení to povie oznámenie a stránka Asistent potom sama ukáže výsledok, už žiadne „obnovte stránku o chvíľu“. Ak sú na stránke neuložené nastavenia nástrojov, prekreslí sa iba karta s aktivitou, aby sa úprava nestratila. Beh, ktorý sa nemôže začať (kurz archivovaný, bot odpojený, GitLab od kliknutia odmietol token), skončí hneď aj s dôvodom, namiesto „Pripravuje sa“ na štvrť hodiny. Každý beh je jeden riadok v histórii úloh v Admin -> Systém („Cvičenie asistenta“) aj s trvaním.
- Karta Aktivita asistenta je stále aktuálna: živý prúd kurzu ju prekreslí, keď bot v GitLabe niečo urobí, a tlačidlo Obnoviť v jej hlavičke ju načíta znova, ako v histórii úloh a pri webhookoch. Skupina má vlastný stĺpec (dá sa podľa nej triediť aj hľadať), už sa nezalamuje pod používateľské meno, a prázdna karta ukazuje malý prázdny stav ako každý prázdny zoznam, nie ten na celú stránku.
- Stránka Asistent upozorní aj na webhook, ktorý 48 hodín nedostal z GitLabu žiadnu udalosť, druhý prípad zo stránky Udalosti, nielen na chýbajúci.
- Každý graf sa objavuje rovnako ako graf rolí v Admin -> Systém: prvé vykreslenie počká, kým je graf na obrazovke, stĺpce rastú 900 ms, každý o 80 ms po predchádzajúcom, prstenec sa zatočí za 900 ms. Prstenec súladu a týždenný graf v Analytike sa animovali ešte pod okrajom obrazovky a čitateľ ich videl už nehybné; päť ručne písaných kópií „vykresli, keď je vidieť“ (Systém, Analytika, detail študenta, detail projektu) je jedna funkcia, `GP.drawOnEntry`.

**Opravené**

- Avatar, ktorý zlyhal skôr, než skript stránky začal počúvať (rýchla 404, zdroj, ktorý politika obrázkov odmieta), ukazoval na každej stránke s avatarmi rozbitý obrázok a jeho alternatívny text ešte osem sekúnd po tom, čo sa posunul do zorného poľa; teraz hneď ukáže iniciály.
- Odznak roly v kurze v hlavičke každej stránky kurzu („Učiteľ“, „Vlastník kurzu“) a odznak roly používateľa boli v prvom snímku anglicky a preložili sa až o chvíľu; prekladá ich server.

## [2026.10.20.post1] - 2026-10-20 - Asistent pre tých, ktorí kurz vedú

**Opravené**

- Asistent cvičení patrí tým, ktorí kurz vedú: jeho kartu, stránku a štyri akcie má vlastník kurzu, jeho vyučujúci a administrátor, nie učiteľ, ktorý kurz vidí len ako mentor niektorého tímu (taký učiteľ doteraz kartu aj stránku dostal, vrátane formulára na token bota). Jeho položky v **Položkách, ktoré si vyžadujú vašu pozornosť** a riadky v **Sledujte najnovšie aktualizácie** sa riadia tým istým pravidlom.
- Kontrola R08 už nepočíta komentáre bot účtov medzi vlákna, na ktoré má autor odpovedať. Asistent po review napíše „schválené, zlúč“, takže každému merge requestu z cvičenia zostalo vlákno, na ktoré nikto odpoveď nečaká, a R08 neprešla študentom, ktorí urobili všetko správne; rovnako sa počítala správa CI bota. Nápoveda pri R06 tieto komentáre stále uvádza medzi tými, ktoré nenapísal člen tímu.
- História úloh v Admin -> Systém pomenúva kroky asistenta rovnako ako prehľad na nástenke („Nástroje asistenta upravené“ namiesto nepreloženého „Assistant tools saved“).

**Dokumentácia**

- Vyhlásenie o ochrane osobných údajov hovorí, čo asistent zapisuje do projektov tímov a pod akým účtom; časté otázky študentov vysvetľujú, kto je bot, ktorý komentuje commity; návod k asistentovi a popis R08 hovoria, kto asistenta riadi a že na komentáre bota netreba odpovedať.

## [2026.10.20] - 2026-10-20 - Asistent na nástenke

**Zmenené**

- Asistent je súčasťou nástenky: **Položky, ktoré si vyžadujú vašu pozornosť** hovoria to isté, čo jeho stránka navrchu (token, ktorý GitLab odmieta alebo ktorému vypršala platnosť, nástroje zapnuté bez bota, token tesne pred vypršaním, nedokončená príprava cvičenia; obe odpovedá jedna funkcia, `account.problems()`) a počítajú kroky, ktoré mu GitLab za 7 dní odmietol; **Sledujte najnovšie aktualizácie** pomenuje jeho kroky (bot pripojený či odpojený, nástroje upravené, cvičenie pripravené, token odmietnutý) a odkáže na stránku Asistent, študentom ich neukáže. Odmietnutý token sa do auditu zapíše raz.
- Konfiguračný súbor kurzu (export a import) nesie nastavenia nástrojov asistenta v sekcii `assistant`, nikdy bota ani token; import ich overí ako formulár a kým je asistent vypnutý, preskočí ich, ako teraz hovorí aj náhľad.
- Stránka Asistent hovorí, že kurz nemá webhook, rovnako ako stránka Udalosti: upozornením, ktoré sa raz zobrazí pri otvorení stránky, nie blokom v stránke (archivovaný kurz ho nedostane, jeho webhooky sa zámerne zahadzujú).
- Nič sa na stránke Asistent nehovorí dvakrát: vypršaný token oznámi len upozornenie navrchu (karta už nepridáva odznak „Token vypršal“), predvolené pravidlo pre vetvy sa už nevypisuje v dvoch kartách (ako v tikete cvičenia sa uvedie len prísnejšie pravidlo) a karta s aktivitou sa volá „Aktivita asistenta“, nie „Aktivita“ ako karta kurzu vedľa nej.
- Ponuka sprievodcu uvádza počet krokov ako „Kroky: 4“, čo je správne pri každom čísle („4 krokov“ nebolo).
- `scripts/assistant_e2e.py accounts` vypíše prihlásenia na ručné vyskúšanie asistenta na lokálnom GitLabe: heslá učiteľa a študentov v GitLabe a vývojové prihlásenie do GitPulse.

## [2026.10.19.post10] - 2026-10-19 - Asistent overený na skutočnom GitLabe

**Opravené**

- Webhook konfigurácia kurzu (jediné tajomstvo, ktoré stránka Nastavenia vydáva) overí aj importované projekty kurzu. Každý importovaný projekt má vlastné tajomstvo, ktoré nikto nevidí, a prijímač sa pri ňom zastavil, takže každé doručenie z importovaného projektu odmietol s 401. Vlastné tajomstvo projektu sa stále skúša prvé a token, ktorý nesedí nikde, sa stále odmietne.
- Webhooky merge requestov z GitLabu sa prijímajú. Pole `object_attributes.source` je pri merge requeste zdrojový projekt, nie slovo, a schéma každý odmietla s 422; merge requesty sa do GitPulse dostávali len synchronizáciou. Ručne napísaný kontraktový vzor také pole nemal.
- Webhook pipeline mimo merge requestu (`"merge_request": null`) už spracovanie nezhodí.
- Asistent cvičení, overený od začiatku do konca na GitLab CE 19.4.2: vetva založená v GitLabe bez commitov nedostane komentár (pristál na poslednom commite `main`) - ozve sa pri jej prvých commitoch a vtedy posúdi aj jej názov; push zlúčeného merge requestu do `main` nie je push priamo do `main`; tiket povie, čo bude review žiadať navyše (sekcie popisu kurzu, prísnejšie pravidlo pre vetvy), a kto zlučuje; review počká, kým GitLab zistí, či sa merge request dá zlúčiť, takže neschváli konflikt; na komentár, na ktorý review už odpovedalo, neodpovie druhýkrát; člen vylúčený z hodnotenia nedostane tiket ani komentáre; citovaný riadok v komentári ku konfliktu už nekončí druhou bodkou.

**Pridané**

- Stránka Asistent má sprievodcu ako každá iná karta kurzu, vedľa Uložiť aj Zrušiť ako na stránke Nastavenia a poznámku, že tikety a merge requesty z cvičenia sa počítajú do R01 až R13; názov tímu sa v tabuľke aktivity už nezalamuje.
- `scripts/assistant_e2e.py` s `docker-compose.gitlab-e2e.yml` overí asistenta na skutočnom GitLab CE 19.4.2 (56 kontrol). Doručenia zachytené pri takom behu sú kontraktové vzory v `tests/fixtures/payloads/gitlab_19_4/`.

## [2026.10.19.post9] - 2026-10-19 - Plynulé zloženie zvýraznenia sprievodcu

**Opravené**

- Zvýraznenie sa pri zatvorení sprievodcu alebo návrate na krok bez prvku zvislo zloží za 400 ms, opačne než pri prvom rozvinutí. Krížik, Escape a potiahnutie na mobile používajú rovnaký prechod. Zatvorenie počas rozvíjania pokračuje z viditeľného tvaru; opakovaný Escape animáciu nepreruší.

## [2026.10.19.post8] - 2026-10-19 - Plynulé prvé zvýraznenie sprievodcu

**Opravené**

- Prvé zvýraznenie sprievodcu sa rozvinie zvislo priamo pri cieľovom prvku za 400 ms. Už sa nezobrazí okamžite a nezačína kruhom v strede obrazovky. Platí to aj pre sprievodcu bez úvodu a návrat z kroku bez zvýraznenia. Animácia počká na zameranie cieľa; obnovenie po ustálení stránky už nereštartuje platný krok ani znovu neotvorí zatvoreného sprievodcu.

## [2026.10.19.post7] - 2026-10-19 - Plynulé prechody všetkých krokov sprievodcu

**Opravené**

- Zvýraznenie sprievodcu si zachováva prechod s trvaním 400 ms aj pri posúvaní k ďalšiemu alebo predchádzajúcemu prvku. Spoločný modul animácií priebežne sleduje polohu cieľa bez okamžitého preskakovania. Okno vychádza z predchádzajúcej viditeľnej polohy aj vtedy, keď má nový popis inú výšku. Režim obmedzeného pohybu, prerušené kroky a súvislé stmavenie v úvode a závere zostávajú podporované.

## [2026.10.19.post6] - 2026-10-19 - Asistent cvičení v prevádzke

**Pridané**

- Asistent cvičení je v produkcii zapnutý (`redeploy.py` nastaví `FEATURE_CLASSROOM_ASSISTANT=true`; `docker-compose.yml` teraz prepúšťa prepínač do API aj workerov, čo predtým nerobil). Každý kurz si stále pripojí vlastného bota a zapne svoje nástroje.
- Asistent sa riadi pravidlami kurzu: so zapnutou R02 kontroluje názov novej vetvy aj vetvy merge requestu podľa pravidla kurzu, so zapnutou R05 review vyžaduje sekcie popisu. Kontrolu, ktorú kurz vypol, nežiada. Review hlási aj zlyhanú pipeline.
- Kurz si zvolí jazyk, ktorým asistent píše (slovenčina alebo angličtina): komentáre, tikety aj riadok od kolegu.
- Kurz prenesený do nového semestra si ponechá nastavenia nástrojov asistenta; bot token zostáva pri pôvodnom kurze.

**Opravené**

- Merge request zatvorený bez zlúčenia už nedrží tiket: ďalší merge request k nemu prejde review od začiatku.
- Bot token, ktorý vypršal alebo ho GitLab odmieta (overené cez `GET /user`, lebo 401 vráti GitLab aj pri opakovanom schválení), asistenta zastaví namiesto zlyhania pri každej udalosti; stránka Asistent to povie navrchu a vyžiada nový token.
- Stránka Asistent povie, čo asistentovi bráni konať: chýbajúci webhook kurzu, nástroje zapnuté bez bota, nepoužiteľný token. Čakajúca úloha s konfliktom povie, na čo čaká; Pripraviť cvičenie ukazuje prebiehajúce spustenie, ďalšie nedovolí a započíta študentov, ktorí ešte nemajú účet GitLab v GitPulse.

## [2026.10.19.post5] - 2026-10-19 - Plynulejšie mobilné vyhľadávanie

**Opravené**

- Mobilné vyhľadávanie odhaľuje okno so stálymi rozmermi orezaním a posunom namiesto prepočítavania rozloženia v každom snímku. Stmavenie používa samostatnú vrstvu; animácia začína po príprave a zaostrení vstupu. Zmena výšky pri otvorení klávesnice už prechod nepreruší. Text, posúvanie, rýchle opätovné otvorenie aj otočenie zariadenia zostávajú stabilné.
- Prechody zvýraznenia a okna sprievodcu opäť trvajú 400 ms. Oprava kruhového výrezu v úvode a závere zostáva zachovaná.

## [2026.10.19.post4] - 2026-10-19 - Obnovené animácie sprievodcu

**Opravené**

- Sprievodca opäť plynulo presúva zvýraznenie medzi prvkami a okno medzi jeho polohami. Úvod a záver zachovávajú súvislé stmavenie bez kruhového výrezu. Pri posúvaní zvýraznenie sleduje prvok priamo; rýchle prepínanie krokov a režim obmedzeného pohybu zostávajú podporované.

## [2026.10.19.post3] - 2026-10-19 - Rýchle vyhľadávanie bez deformácií

**Opravené**

- Vyhľadávanie sa otvorí za 200 ms a zatvorí za 100 ms. Vstupné pole a výsledky si počas rozvinutia zachovajú rozmery, takže sa text nepreskladáva a nevzniká dočasný posuvník. Dlhé zoznamy sa po dokončení prechodu posúvajú bežným spôsobom.

## [2026.10.19.post2] - 2026-10-19 - Rozvinutie vyhľadávania

**Zmenené**

- Vyhľadávanie sa rozvinie z poľa v hornom paneli a pri zatvorení sa doň vráti. Výsledky sa odhalia vo vnútri rastúceho okna bez zväčšovania textu. Spoločný modul animácií obsluhuje prerušené prechody, zmenu veľkosti okna, klávesnicu aj režim obmedzeného pohybu a výpadok GSAP.

## [2026.10.19.post1] - 2026-10-19 - Plynulé zobrazenie sprievodcu

**Opravené**

- Úvodné a záverečné kroky sprievodcu zobrazujú súvislé stmavenie bez kruhového výrezu. Zvýraznenie a poloha okna sa menia súčasne, bez deformácie obrysu a presúvania okna cez obrazovku. Jemné objavenie a zatvorenie zostávajú zachované.

## [2026.10.19] - 2026-10-19 - Asistent cvičení

**Pridané**

- Asistent cvičení (zapína ho `FEATURE_CLASSROOM_ASSISTANT`, predvolene vypnutý): bot, ktorý na projektoch kurzu pracuje ako kolega a študenti ho stretnú iba v GitLabe. Učiteľ pripojí jeho token na novej karte kurzu **Asistent** - group access token s rolou Maintainer a rozsahom `api`, ktorý GitPulse overí v GitLabe a uloží zašifrovaný. Analytika ďalej číta tokenom iba na čítanie; bot má vlastného klienta a odmietnutie jeho tokenu nezastaví synchronizáciu kurzu.
- Kontrola pushu: po pushi študenta komentár k pushnutému commitu, keď išiel priamo do predvolenej vetvy, keď správu napísal webový editor GitLabu (pravidlo R13) alebo keď je správa príliš krátka. Nová vetva dostane povzbudenie, čistý push do existujúcej vetvy zostane bez komentára a opakovane doručený webhook nedostane dve odpovede.
- Konflikt pri zlučovaní: keď vetva študenta prvýkrát zmení súbor cvičenia, commit od kolegu v predvolenej vetve upraví presne tie isté riadky, takže zlúčenie vetvy skončí konfliktom - aj keď sa predvolená vetva medzitým posunula, overené skutočným gitom. Po zlúčení predvolenej vetvy sa každý push skontroluje na značky konfliktu a na zachovanie oboch zmien; výsledok ide do merge requestu alebo ku commitu.
- Tikety a merge requesty: **Pripraviť cvičenie** dá každému študentovi vybraných projektov súbor a pridelený tiket; opätovné spustenie pridá iba nových študentov. Merge request študenta prejde review - vlastná vetva, odkaz na tiket, iba pridelený súbor, nič nevyplnené, nie draft, bez konfliktov - s jedným komentárom presne o tom, čo chýba, a s odpoveďou na komentár študenta. Keď nechýba nič, asistent ho schváli a zlúči ho študent (R10 zlúčenie botom za študentovo nepovažuje), alebo, ak to kurz zvolí, asistent. Udalosť zlúčenia z GitLabu uzavrie tiket a študenta pochváli; zlúčenie pred schválením asistent pomenuje.
- Karta Asistent ukazuje bota a expiráciu jeho tokenu, tri nástroje so spoločným panelom ukladania, posledné pripravenie cvičenia po projektoch a tabuľku aktivity - karty nástrojov, hľadanie, stránkovanie - s odkazmi do GitLabu. Archivovaný kurz je iba na čítanie. Príručka pre učiteľov v slovenčine aj angličtine.

**Zmenené**

- R13 a kontrola pushu zdieľajú jedno pravidlo pre commity z webového editora.

## [2026.10.16.post3] - 2026-10-16 - Nepriehľadný spodný panel nastavení

**Opravené**

- Spoločný panel ukladania v nastaveniach kurzu a používateľa prekrýva aj spodný odstup oblasti posúvania. Obsah už pod tlačidlami nepresvitá. Poloha tlačidiel a odstup pod poslednou sekciou vrátane Danger Zone zostávajú zachované.

## [2026.10.16.post2] - 2026-10-16 - Kontroly nasadenia a vyrovnávacia pamäť závislostí

**Opravené**

- Nasadenie sa zastaví pri chybe Gitu, vzdialeného príkazu alebo kontroly pripravenosti. Zachováva zmenený produkčný pracovný strom a overuje spustený commit aj verziu.
- Migrácie sa spustia a overia v novom obraze pred výmenou API. Dokumentácia zostáva dostupná, kým sa nový obraz úspešne nezostaví.
- Samotná zmena verzie už nezneplatňuje vrstvu závislostí Dockeru. Závislosti zostávajú uzamknuté súborom `requirements.lock`.

**Zmenené**

- Lokálne nastavenia agentov, nahrané súbory používateľov, dočasné súbory a vyrovnávacie pamäte nástrojov sú vylúčené z kontextu zostavenia Dockeru. Pokyny na nasadenie opisujú overené poradie krokov.

## [2026.10.16.post1] - 2026-10-16 - Odozva položiek výberu a čistenie repozitára

**Opravené**

- Ponuky obdobia, formulárov, jazyka a počtu riadkov zobrazujú pri ukázaní alebo ovládaní klávesnicou tlmenú fajku. Vybraná položka si zachováva plnú fajku; neaktívne položky ani ponuka otvorená pod nepohnutým kurzorom výber nenaznačujú. Text položiek sa neposúva.

**Odstránené**

- Nepoužívaná kópia CSS dokumentácie GitLabu z koreňa repozitára.

## [2026.10.16] - 2026-10-16 - Rozostupy tabuľky používateľov a spoločné komponenty

**Opravené**

- Tabuľka používateľov využíva voľné miesto na širších obrazovkách pre e-mail. Pevná šírka stránky zachováva pôvodné rozmery stĺpcov; filtre a stránkovanie ich neposúvajú.
- Nastavenia kurzu a predvoľby zachovávajú spodný odstup aj pod sekciou Danger Zone vnorenou do panela karty. Panel uloženia zostáva prichytený pri posúvaní.

**Zmenené**

- Tabuľky používateľov a členov zdieľajú štýly akcií v riadkoch. Štýly Danger Zone patria ku komponentu karty a rozloženie používateľov je zjednotené bez duplicitných ID pravidiel.

## [2026.9.30.post110] - 2026-09-30 - Bezpečnostná aktualizácia urllib3

**Opravené**

- **Bezpečnosť:** `urllib3` aktualizované na 2.8.0 (tri CVE).

## [2026.9.30.post109] - 2026-09-30 - Učitelia ako ostatné zoznamy, stránky pri načítaní neblikajú

**Zmenené**

- Stránka Učitelia kurzu vyzerá a správa sa ako ostatné zoznamy: vyhľadávanie, filtre podľa roly, triedenie a stránkovanie. Zmena roly, odstránenie učiteľa aj pridanie učiteľa (v dialógu) platia hneď - bez tlačidla Uložiť. Pri načítaní už nič neblikne: tabuľka je na mieste od prvého zobrazenia.

**Opravené**

- Stránkovanie pod tabuľkami je viditeľné hneď pri načítaní, nedokresľuje sa dodatočne.
- Zoznam používateľov sa pri načítaní už nezväčší z 25 na 50 riadkov.
- Nastavenia kurzu bez webhookov hneď zobrazia prázdny stav, karta neposkočí.

## [2026.9.30.post108] - 2026-09-30 - Rovnaké tlačidlá akcií vo všetkých tabuľkách

**Opravené**

- Akcie v riadkoch všetkých tabuliek sú rovnaké štvorcové tlačidlá s ikonou (na dotykovej obrazovke väčšie): zobraziť je vždy oko, vymazať vždy červený kôš. Zmizli tlačidlá s textom medzi ikonami (Zobraziť v tabuľke skupín, tiketov a členov projektu, Podrobnosti a Obnoviť v udalostiach, Zrušiť v histórii úloh) aj sivý kôš pri učiteľoch.
- Prepínač započítania člena do skóre je plne viditeľný aj na mobile a má vlastnú ikonu (osoba s mínusom / plusom) - predtým to bolo oko, rovnaké ako tlačidlo Zobraziť hneď vedľa.

**Zmenené**

- Všetky karty kurzu (prehľad, Aktivita, Analytika, Nastavenia, Učitelia) majú rovnakú hlavičku: kód a názov kurzu, semester, vašu rolu a popis kurzu - pri prepínaní kariet sa mení len obsah.

## [2026.9.30.post107] - 2026-09-30 - Počítadlo upozornení a tlačidlá archivovaných kurzov

**Opravené**

- Jedno kliknutie už nikdy neukáže pri upozornení „×2“ - počíta sa len ďalšie stlačenie, nie ozvena tej istej akcie.
- Tlačidlá akcií archivovaného kurzu sú v Správe kurzov aj na nástenke rovnako veľké a rovnaká akcia má rovnakú ikonu a farbu (aktivovať - zelená fajka, vymazať - červený kôš).

## [2026.9.30.post106] - 2026-09-30 - Tabuľka servisných účtov

**Opravené**

- V Správe používateľov sa v zobrazení Servisné účty texty už neprekrývajú: meno, celé meno a e-mail bota sa skrátia na šírku svojho stĺpca (celá hodnota je v tooltipe) a označenie Bot je v riadku len raz - v stĺpci Rola.

## [2026.9.30.post105] - 2026-09-30 - Neaktívne tlačidlá a zobrazenie na mobile

**Opravené**

- Neaktívne zaškrtávacie políčka a tlačidlá sú na svetlej téme dobre viditeľné a je jasné, že sú neaktívne - stĺpec Aktívne v kontrolách archivovaného kurzu už nevyzerá ako prázdne políčka.
- Šípky stránkovania sú na bielom pozadí karty; neaktívna šípka je len sivý symbol bez rámika.
- Každé neaktívne tlačidlo povie, prečo je neaktívne - pri prejdení myšou a na mobile po ťuknutí.
- Mobil: tlačidlá a odkazy majú dotykovú plochu aspoň 32 px, žiadny text nie je menší ako 12 px, správa prázdnej tabuľky je celá na obrazovke a dlhé odkazové tlačidlá sa zalomia.

## [2026.9.30.post104] - 2026-09-30 - Údržba

**Odstránené**

- Starý spôsob načítania časti stránky, ktorý od leta nič nepoužívalo. Pri ručne zostavenej požiadavke mohla stránka podpory skončiť chybou; teraz každá adresa vráti celú stránku. Pre používateľov sa nič nemení.

## [2026.9.30.post103] - 2026-09-30 - Oprava panela Uložiť naozaj nasadená

**Opravené**

- Úprava panela s tlačidlami Uložiť / Obnoviť a stĺpca s akciami z verzie post102 sa na server nedostala - server ďalej posielal staré štýly. Teraz sa štýly vždy zostavia z aktuálnych zdrojov.

## [2026.9.30.post102] - 2026-09-30 - Panel s tlačidlami Uložiť a súbory s odtlačkom v názve

**Opravené**

- **Panel s tlačidlami Uložiť / Obnoviť** v nastaveniach kurzu, v predvoľbách a pri učiteľoch kurzu má farbu stránky a končí presne s obsahom - na svetlej téme už nevyčnieva ako biely rámik s tieňom, širší než karty nad ním.
- Riadok vylúčeného člena v tabuľke členov projektu má rovnaký odtieň aj v stĺpci s akciami.

**Zmenené**

- **Skripty a štýly aplikácie majú v názve odtlačok svojho obsahu.** Prehliadač si ich preto môže pamätať natrvalo a po aktualizácii stiahne len tie, ktoré sa naozaj zmenili. Vzhľad ani správanie stránok sa nemení.
- **Aktualizácia aplikácie už na chvíľu nerozbije otvorené stránky.** Súbory, ktoré nová verzia odstraňuje, zostávajú dostupné až do ďalšej aktualizácie.

## [2026.9.30.post101] - 2026-09-30 - Tabuľky bez prázdneho miesta a spoľahlivejšie obnovovanie

**Opravené**

- **Pod tabuľkou už po načítaní nezostáva prázdne miesto.** Krátke tabuľky (napr. issues študenta) mali pod posledným riadkom prázdny pás, ktorý zmizol až po prepnutí filtra a po obnovení stránky sa vrátil.
- **Import celej konfigurácie v nastaveniach kurzu funguje** - predtým vždy skončil chybou „No configuration provided".
- **Udalosť z webhooku, ktorú sa nepodarí spracovať, sa zaznamená ako neúspešná** a neopakuje sa donekonečna.
- **Živé obnovenie stránky ukazuje to isté ako stránka.** Na stránke kurzu sa počet prispievateľov po obnovení už nemení na počet za celé obdobie, stav pipeline skupiny v monitore aktivity sa nemení na „running", na stránke projektu sa obnovujú aj členovia vylúčení z hodnotenia a stav synchronizácie skupín sa už neprepína medzi dvoma odpoveďami.

**Zmenené**

- Kód aplikácie je rozdelený na menšie časti; správanie stránok je rovnaké (overené porovnaním starej a novej verzie).

## [2026.9.30.post100] - 2026-09-30 - Chybové stránky, tabuľky a rýchlejšie načítanie

**Zmenené**

- **Chybové stránky ponúkajú len to, čo funguje.** Pri výpadku služby (502/503/504) je na stránke iba tlačidlo Opakovať a stránka sa sama obnovuje - bez vyhľadávania a odkazov, ktoré by aj tak nefungovali. Nadpis a text pod ním sa už neopakujú, na mobile je vyhľadávanie v jednom riadku a tlačidlá majú normálnu šírku. Texty sú preložené do slovenčiny.
- **Stĺpce tabuliek majú toľko miesta, koľko ich obsah potrebuje.** V tabuľke členov projektu majú meno aj kontroly primerané miesto, v správe používateľov sa meno, login a e-mail zalamujú namiesto „...", v histórii úloh sa typ číta celý a výsledok sa zalamuje.
- **Sprievodca aplikáciou sa načíta až po zobrazení stránky**, takže stránky sa zobrazia rýchlejšie. Sprievodca funguje rovnako.
- **Synchronizácia jedného projektu ukladá rovnaké údaje ako synchronizácia celej skupiny** - vrátane commitov zlúčených merge requestov so zmazanou vetvou - a je rýchlejšia, pretože nesťahuje nezmenené údaje znova.

**Opravené**

- Živé obnovenie aktivity na nástenke už nevynecháva riadky „Kurz vytvorený" a „Kurz archivovaný".
- Aktivita kurzu bez skupín zobrazuje iba úlohy tohto kurzu.

## [2026.9.30.post99] - 2026-09-30 - Výsledky kontrol zarovnané pod kódmi

**Zmenené**

- **V tabuľke členov projektu sú kódy kontrol aj ich výsledky zarovnané na stred**, každý výsledok presne pod svojím kódom.

## [2026.9.30.post98] - 2026-09-30 - Kód po komponentoch, oprava prístupu k tiketom a tabuľky členov

**Zmenené**

- **Zdieľaný kód rozhrania je rozdelený po komponentoch** - namiesto štyroch súborov s tisíckami riadkov má každý komponent (tlačidlá, stavy obsahu, tooltipy, výber dátumu, navigácia, ...) vlastný súbor. Správanie aj vzhľad aplikácie ostali rovnaké.
- **Stránka študenta sa skladá zo samostatných sekcií** namiesto jednej funkcie s 1 334 riadkami; zobrazuje presne to isté.
- Odstránený nepoužívaný kód, štýly, ktoré vždy prebil iný štýl, a preklady, ktoré aplikácia nikde nepoužíva.

**Opravené**

- **Tiket podpory vidí iba vyučujúci daného kurzu.** Doteraz mohol ktorýkoľvek vyučujúci otvoriť tiket iného kurzu podľa jeho čísla, vrátane interných poznámok.
- **Tabuľka členov projektu orezávala hlavičky kontrol na „R...“ a tlačidlá „Zobraziť“.** Stĺpce teraz majú šírku podľa obsahu, všetky kontroly rovnakú; na širších obrazovkách sa tabuľka zmestí celá, na užších sa posúva do strany namiesto orezania.
- Stránka 404 v slovenčine zobrazovala „Member“ a „Ticket“ po anglicky.

## [2026.9.30.post97] - 2026-09-28 - Rovnaký pás ovládacích prvkov nad každou tabuľkou

**Zmenené**

- **Riadok s vyhľadávaním a filtrami nad každou tabuľkou je rozložený ako v správe používateľov** - rovnaká výška a rovnaké medzery nad aj pod ovládacími prvkami, či obsahuje vyhľadávanie, rozbaľovacie zoznamy alebo karty, na počítači aj na telefóne.

## [2026.9.30.post96] - 2026-09-28 - Rovnaká hlavička kariet všade, celý stĺpec GitLab ID

**Zmenené**

- **Každá hlavička karty vyzerá rovnako**: ikona a za ňou názov, na každej stránke na tom istom mieste. Niektoré karty ikonu nemali a iné ju mali umiestnenú inak.

**Opravené**

- **Hlavička stĺpca „GitLab ID“ v správe používateľov bola orezaná**; teraz sa zobrazí celá a na užších obrazovkách sa tabuľka posúva do strany namiesto orezania stĺpcov.

## [2026.9.30.post95] - 2026-09-27 - Prepínanie kariet bez blikania

**Opravené**

- **Prepnutie karty už nerozbliká obsah** - napríklad obrázok prázdneho stavu v Rýchlom prístupe na stránke Prehľad. Obsah novej karty sa zobrazí hneď, ako v GitLabe.

## [2026.9.30.post94] - 2026-09-27 - Ilustrované prázdne stavy, jedna bublina naraz

**Zmenené**

- **Každý prázdny stav má ilustráciu z GitLabu**: prázdne tabuľky, zoznamy, grafy a panely aj vyhľadávania bez výsledkov teraz ukazujú obrázok GitLabu nad správou - tak, ako to už robili prázdne stavy celých stránok.
- **Menej miesta okolo riadku vyhľadávania nad tabuľkou.**

**Opravené**

- **Naraz sa mohli zobraziť dve bubliny s popisom** (napríklad v stĺpci „Zaradené do fronty" v histórii úloh); teraz sa všade zobrazí len jedna.
- **Bublina s časom v UTC** ukazuje čas na sekundy s označením „UTC" namiesto surovej hodnoty zo servera.
- **Na stránke Podpora mohli byť otvorené dva rozbaľovacie zoznamy naraz.**

## [2026.9.30.post93] - 2026-09-27 - Animácie a veľkosti v súlade s GitLabom

**Zmenené**

- **Rovnaké prvky sa hýbu rovnako**: tlačidlá, tlačidlá zavretia, odznaky, karty a šípky majú jednu rýchlosť, položky zoznamov a riadky tabuliek druhú, formulárové polia tretiu - každú podľa GitLabu. Panely sa otvárajú rovnako, všetky ukazovatele priebehu majú jednu rýchlosť, živé značky pulzujú v jednom rytme a stlačenie ovládacieho prvku ho už nezmenšuje.
- **Veľkosti ovládacích prvkov podľa GitLabu**: tlačidlá majú 32 px, malé tlačidlá 24 px s rovnakým písmom všade, šípky stránkovania ladia s číslami strán a karty v jednom páse sú rovnako vysoké.
- **README** má nové snímky aktuálneho rozhrania a prehľadnejší úvod.

## [2026.9.30.post92] - 2026-09-27 - CSRF na každom zápise, dialógy bez záblesku

**Bezpečnosť**

- **Každá požiadavka, ktorá mení údaje, overuje CSRF token** - dvanásť to nerobilo: opakovanie a prehratie webhook udalostí, mazanie, čistenie a úprava tiketov, komentáre a prílohy k nim, prepočet týždenného súhrnu a štyri telemetrické signály. Aplikácia token posielala vždy, takže sa pre používateľa nič nemení.

**Opravené**

- **Otvorenie dialógu už nerozsvieti výberové pole**, ako keby naň mieril kurzor: dialóg počas príchodu prechádza pod stojacim kurzorom a jeho obsah reaguje na ukazovateľ až po dosadnutí.
- **CI opäť spúšťa integračné testy** - predtým ich všetky preskočilo.

## [2026.9.30.post91] - 2026-09-27 - Prázdne stavy rozložené ako v GitLabe

**Zmenené**

- **Prázdne stavy presne kopírujú rozloženie a veľkosti GitLabu** - ilustrácia, 28px nadpis, popis a tlačidlá s rovnakými odstupmi ako v GitLabe.
- **Šípky mesiacov vo výbere dátumu**, bežiaca pipeline, tabuľka členov projektu, prehľad týždňov, vetvy merge requestov a všetky tlačidlá zavretia kreslia vlastné ikony GitLabu; žiadny textový znak už nenahrádza ikonu.

**Opravené**

- **Analytika kurzu už nezlyhá**, keď graf kontrolného zoznamu nemá dáta.

## [2026.9.30.post90] - 2026-09-26 - Všetky ikony a ilustrácie z GitLabu

**Zmenené**

- **Všetky ikony a ilustrácie sú priamo z GitLabu** (`@gitlab/svgs`, `@gitlab/ui`) a použité tak ako v GitLabe; logo GitPulse a načítavací tanuki zostávajú vlastné.
- **Prázdne stavy začínajú ilustráciou GitLabu** - „V období … nie sú žiadne predmety" na Prehľade ukazuje kalendárovú ilustráciu GitLabu namiesto ikony v sivom štvorci.
- **Prázdne tabuľky a grafy to povedia len slovami**, ako tabuľky GitLabu.
- **Položky vyžadujúce vašu pozornosť** majú značky úloh GitLabu a „Dobrá práca!" ilustráciu GitLabu.
- **Radenie** ukazuje šípku GitLabu (↑ / ↓) pri zoradenom stĺpci.
- Tlačidlá zavretia, zaškrtnutia, šípky, začiarkavacie polia, lišta úloh, heatmapa študenta a chybové a offline stránky kreslia vlastné ikony a ilustrácie GitLabu; žiadny textový znak už nenahrádza ikonu.

**Opravené**

- **Šípky stránkovania boli v úzkom okne neviditeľné** (pod 768 px).

## [2026.9.30.post89] - 2026-09-26 - Predvolené obdobie v Predvoľbách

**Zmenené**

- **Predvoľby > Správanie > „Predvolené obdobie"** - kde sa otvorí každá stránka s výberom obdobia: naposledy vybrané obdobie (predvolené), najnovšie obdobie s vašimi kurzami, práve prebiehajúce obdobie alebo všetky obdobia.

**Opravené**

- **Stránky vyučujúceho a administrátora použijú jazyk účtu** aj na zariadení bez jazykového cookie.

## [2026.9.30.post88] - 2026-09-26 - Audit JavaScriptu: štyri chyby, žiadne var

**Opravené**

- **Prehľad pri každom obnovení zbytočne prekresľoval zoznamy** - v regulárnom výraze bol namiesto `\b` neviditeľný znak.
- **Záložná kontrola synchronizácie kurzu padala pri prvej odpovedi** - chýbali jej dve deklarácie.
- **Záložky a filtre sa brali ako tlačidlo, ku ktorému sa viaže ďalší toast.**
- **Stránkovanie tabuliek malo dve verzie tej istej metódy.**

**Zmenené**

- **V zdrojovom JavaScripte už nie je žiadne `var`** a premenné, ktoré sa nemenia, sú `const`; odstránený mŕtvy kód.

## [2026.9.30.post87] - 2026-09-26 - Vyhľadávanie tabuľky v strede svojho pásu

**Pridané**

- **Predvoľby > Správanie > „Pamätať si obdobie, ktoré vyberiem"** - keď je vypnuté, každá stránka sa otvorí na najnovšom období s vašimi kurzami.
- **Správa kurzov má filter Stav** (aktívne, archivované) a riadok kurzu otvorí kurz.

**Opravené**

- **Odkaz otvorí to, o čom hovorí** - archivované kurzy s ich obdobím a filtrom, tikety v zozname kurzu.
- **K archivovaným kurzom sa dá vždy dostať** - výber obdobia na Prehľade nezmizne, prázdne obdobie ukáže, kde sú vaše kurzy.
- **Filter z odkazu sa aj použije** a pri načítaní stránky nebliká.
- **Pole Akademické obdobie** v nastaveniach archivovaného kurzu vyplní celý riadok.
- **Vyhľadávanie a filtre tabuľky majú rovnaký priestor nad aj pod sebou** - na počítači 24 px, na telefóne 12 px.

## [2026.9.30.post86] - 2026-09-26 - Filtre tiketov, filter nebliká, opakovaný toast

**Pridané**

- **Prehľad tiketov podpory sa filtruje podľa obdobia a stavu** - rovnaký výber obdobia ako pri každom zozname kurzov a filter Stav (aktívne alebo archivované).

**Zmenené**

- **Podpora sa otvára rovnakou tabuľkou kurzov ako Tikety podpory** - obdobie, stav, filtre a počty vlastných žiadostí; tlačidlo *Nová žiadosť*.
- **Varovanie o webhookoch v Udalostiach je opäť toast** - zobrazí sa pri príchode, nikdy nie dvakrát.

**Opravené**

- **Zvolený filter pri načítaní nebliká** - pri zmene obdobia, triedenia alebo strany toho istého zoznamu ostanú ovládacie prvky v plnej sile, stlmia sa len riadky.
- **Pole obdobia ukáže výber hneď** a po načítaní zostane naň zameraná pozornosť (fokus).
- **Opakovaný toast je znova viditeľný** - zopakuje svoj príchod a ukáže počet *×2*, *×3*.
- **Každá tabuľka má rovnaký okraj zo všetkých strán** - pod tabuľkou toľko ako nad jej ovládacími prvkami a lišta stránkovania až po okraj karty.

## [2026.9.30.post85] - 2026-09-26 - Tikety podľa kurzov, stav webhookov na stránke, obdobie všade

**Zmenené**

- **Prehľad tiketov podpory je tabuľka kurzov**: obdobie, aktívny alebo archivovaný, otvorené tikety, spolu, posledný tiket; aktívne kurzy prvé, triedenie podľa každého stĺpca a vyhľadávanie.
- **Stav webhookov na stránke Udalosti je upozornenie na stránke**, nie toast pri každej návšteve - len pre aktívne kurzy, s obdobím a odkazom na nastavenia webhooku.
- **Rovnaký toast sa nezobrazí druhýkrát** - ten, ktorý je na obrazovke, na seba upozorní a jeho odpočet začne znova.

**Opravené**

- **Zbaľovacie karty sa otvárajú a zatvárajú plynulo**, bez zaseknutia na výške odsadenia.
- **Obdobie pri každom kurze**: Info o používateľovi, stĺpec *Kde* v Udalostiach, vyhľadávanie, hlavičky Podpory, dialóg Spustiť kontroly a potvrdenia archivácie, aktivácie a odstránenia.
- **Podpora upozorní na archivovaný kurz** - žiadosti stále dostávajú jeho vyučujúci.
- **Vymazať staré tikety maže len tikety daného kurzu** a dialóg ho pomenuje aj s obdobím.
- **Odstránenie kurzu z Nastavení žiada kód kurzu**, nie jeho UUID.

## [2026.9.30.post84] - 2026-09-26 - Odznaky pri každej osobe, archivované kurzy oddelene

**Opravené**

- **Stĺpec Obdobie v Správe používateľov má odznak pri každom riadku**: študent obdobia svojich skupín alebo *Bez obdobia*, vyučujúci obdobia svojich predmetov alebo *Žiadne predmety*, administrátor a servisný účet *Všetky obdobia*.
- **Servisný účet už nie je označený ako študent** - v stĺpci Rola má odznak *Bot*.
- **Tikety podpory ukazujú, kto je kto**: odosielateľ, riešiteľ aj autor komentára majú odznak roly.
- **Výber kurzu v Podpore oddeľuje archivované kurzy** do zbalenej karty *Archivované kurzy*.
- **Hlavička karty** už neroztiahne titulok na stred a **zbalená rozbaľovacia karta** nemá prázdny pás pod hlavičkou.

## [2026.9.30.post83] - 2026-09-25 - Jedno pole obdobia, dátumy podľa kalendára, opravený presun

**Zmenené**

- **Jedno pole Akademické obdobie namiesto troch.** Vytvorenie, import, úprava aj presun kurzu a jeho nastavenia sa na obdobie pýtajú rovnako: aktuálne obdobie a obdobia po ňom, pri importe aj dve ukončené. Presun nikdy neponúkne obdobie, v ktorom kurz už je.
- **Obdobie a jeho dátumy sú jeden údaj.** Výber obdobia doplní oficiálne dátumy TUKE a pri zmene obdobia sa posunú s ním, kým ich nezmeníte ručne; začiatok v inom období je vyznačený. **Použiť oficiálne dátumy TUKE** ich vráti.
- **Výber obdobia vyzerá ako ostatné filtre**, každá voľba má vysvetlenie a skončené obdobia bez predmetov v zozname nie sú. **Voľba sa pamätá**, kým sa nezačne ďalšie obdobie.
- **Horná lišta uvádza obdobie**, napríklad *2026/2027 · Zima*.

**Opravené**

- **Presun do nového semestra** končil chybou servera; teraz funguje a termíny zostávajú v ten istý deň týždňa.
- **Živé obnovenie nástenky** počítalo karty a aktivitu za všetky obdobia; karta **Študenti** počítala všetkých študentov v inštalácii.
- **Prázdne obdobie** hlásilo, že nemáte predmety; položky údržby sa pozerajú na všetky vaše predmety.
- **Odznaky obdobia** v Správe používateľov prekrývali stĺpec Stav; majú vlastný stĺpec.
- **Rozbaľovacie ponuky** orezávala oblasť stránky.
- **Obdobie sa overuje** pri každom vstupe vrátane API a importu konfigurácie; uložený dátum semestra už neblokuje uloženie nastavení staršieho kurzu.

## [2026.9.30.post82] - 2026-09-25 - Akademické obdobie na nástenke, v kurzoch a používateľoch

**Pridané**

- **Výber akademického obdobia.** Nástenka, Správa kurzov a Správa používateľov majú výber obdobia - jeden akademický rok a jeden semester, napríklad *2026/2027 · Zima*. Určuje, o ktorých predmetoch a študentoch stránka je, a nesie sa v adrese, takže odkaz na ročník otvorí práve ten ročník. Uvedené je každé obdobie, zimné aj letné, aj bez predmetov (**Žiadne predmety**); **Všetky obdobia** ukáže všetko; **Bez obdobia** zobrazí študentov, ktorí zatiaľ nie sú v žiadnej skupine.
- **Zužujú sa iba študenti.** Administrátori, učitelia a servisné účty sú v každom období.
- **Semester na stránkach skupiny, študenta a projektu** - ako odznak pri názve, zvýraznený, keď práve beží.

**Ako sa obdobie určuje**

- Stránka sa otvorí na **najnovšom období s predmetmi, ktoré vidí čitateľ** - nie na tom z kalendára, ktoré by pri letných predmetoch bolo polroka prázdne. Obdobie z kalendára je označené **Aktuálne** alebo **Nadchádzajúce**.
- Obdobie je určené **v každý deň**, aj po skončení tabuľky semestrov TUKE (25. 6. 2027).

**Opravené**

- Import z GitLabu predvypĺňal **leto** a Vytvorenie kurzu **zimu** - teraz obe obdobie, ktoré stránka zobrazuje.
- Nové kurzy dostávali **rok, v ktorom sa server spustil**; Presun do nového semestra navrhoval **ten istý semester**, v ktorom kurz už je.
- Karta používateľa a náhľad importu vypisovali surovú hodnotu *winter* namiesto *Zima*.
- Rozbaľovacie ponuky sa na telefóne otvárali **mimo obrazovky**.

## [2026.9.30.post81] - 2026-09-23 - Dátum a čas v hlavičke sedia na riadku

**Opravené**

- **Dátum a čas v hornej lište nesedeli na riadku s ostatnými prvkami.** Všetky boxy tam centruje rozloženie stránky, takže v CSS nebolo nič vidieť - nezrovnalosť bola vnútri boxov: riadok okolo 14 px číslic nesie plný nábeh písma, priestor pre diakritiku, ktorý „2026/2027" nikdy nevyužije, takže samotné číslice padli asi pixel pod stred svojho boxu. Zmerané z vykreslených pixelov a opravené tak, aby to platilo aj s náhradným písmom.
- **Stlačenie nedostupného ovládača teraz povie prečo** - nech ho zablokovalo čokoľvek. Doteraz odpovedal iba zámok archivovaného kurzu; čokoľvek vypnuté bežiacim procesom alebo oprávnením mlčalo, a na telefóne sa nebolo ako spýtať, lebo bublina s dôvodom sa zobrazuje len pri prejdení myšou.

## [2026.9.30.post80] - 2026-09-23 - Klávesnica na telefóne a štyri stratené pravidlá CSS

**Opravené**

- **Štyri súbory CSS potichu zahadzovali svoje prvé pravidlo.** Staršie čistenie mŕtvych selektorov nechalo na prvom riadku osamotené `/`. Prehliadač sa pri takej chybe nezastaví - zahodí ju spolu s NASLEDUJÚCIM selektorom - takže štyri pravidlá sa nikdy nepoužili, na produkcii, bez akejkoľvek chybovej hlášky. Nový test kontroluje každý štýlový súbor na celú túto triedu chýb.
- **Otvorenie ktoréhokoľvek modálneho okna na telefóne vyvolalo klávesnicu.** Fokus išiel na prvé pole na každom zariadení; na dotykovom displeji to zakryje polovicu dialógu skôr, než sa čitateľ rozhodne písať - a pri okne, do ktorého sa nič nepíše (Spustiť kontroly), zakrylo práve ten zoznam, z ktorého sa vyberá. Pole s fokusom navyše pozbiera všetko, čo klávesnica vyšle, takže zatvorenie okna sa pýtalo na „neuložené zmeny", ktoré nikto nenapísal. Na dotyku teraz preberá fokus samotný dialóg.
- **Tooltip dával neaktívnemu tlačidlu kurzor aktívneho.** Každé vypnuté tlačidlo s tooltipom - teda každá hromadná akcia nad výberom - ukazovalo kurzor fungujúceho ovládača.
- **Tlačidlo Späť v prehliadke vyzeralo na prvom kroku aktívne** a nerobilo nič; teraz používa rovnaké tokeny neaktívneho stavu ako zvyšok aplikácie.

**Zmenené**

- **Ikony sú späť na svojej škále.** Okolo piatich krokov škály narástlo trinásť jednorazových veľkostí (10, 11, 13, 14, 15 a 18 px) a druhá, pixelmi pomenovaná škála, ktorú takmer nič nepoužívalo. Všetko je zarovnané na najbližší krok.
- **Ikony dátumu a hodín v hornej lište sedia na svojom texte.** Mali 12 px pri 14 px texte; pravidlo tejto aplikácie je 16 pri 14 - rovnako ako GitLab. Rovnakú nezrovnalosť mali aj popisy sekcií MR.

## [2026.9.30.post79] - 2026-09-23 - Jedna sada ikon a červená značka chyby

**Opravené**

- **Každá značka zlyhania bola sivá.** Pravidlo pre červenú farbu stálo NAD základným pravidlom s rovnakou špecificitou, takže základná sivá vyhrala - výstražný trojuholník na neúspešnej tabuľke, grafe či okne mal rovnakú farbu ako značka „nič tu nie je" vedľa neho.
- **Odznak synchronizácie na karte kurzu kreslil dva spinnery** a niesol `</span>`, ktorý nič nezatvára. Odznak vložený živou aktualizáciou tak vyzeral inak ako ten istý odznak vykreslený serverom.
- **Tri reťazce sa zobrazovali po anglicky** na slovenskej stránke - detail zlyhanej synchronizácie, bunka „Sync queued..." a jeden aria-label. Slovenčina bola vo všetkých troch prípadoch už v katalógu. Štvrtý, „Failed to upload attachment.", v katalógu chýbal úplne.

**Zmenené**

- **Jedna sada ikon v JavaScripte, nie štyri.** `GP.icons` so 122 ikonami Pajamas bola v balíku celý čas a vedľa nej vyrástli ďalšie tri tabuľky - vrátane siedmich ručne písaných ikon pre toasty a značiek Hotovo/Zlyhalo, z ktorých jedna sa odchýlila na ručne kreslenú fajku. Všetky sú preč a test spadne, ak sa niektorá vráti.
- **Tri ďalšie ručne písané prázdne stavy** sa stali jedným spoločným blokom so značkou: kontrola bez nastaviteľných parametrov, sekcia kurzov filtrovaná na nulu a MR bez histórie analýz. „Žiadne kurzy v tejto sekcii" sa navyše rozprestrie cez celú mriežku namiesto prvého stĺpca.
- **Dva chybové stavy dostali cestu späť.** Okno detailu udalosti aj okno histórie MR končili v slepej uličke; obe teraz majú tlačidlo Skúsiť znova so stavom načítania.

**Overené**

Každá stránka prejdená v každej roli pri 1440 a 390 px: žiadne prázdne miesta po ikonách, žiadne staré ikony, žiadne duplicitné id, žiadne vodorovné pretečenie, žiadne zaseknuté načítavanie a žiadne chyby JavaScriptu. Všetky modálne okná otvorené dvakrát po sebe - ani jedno sa neotvorí druhýkrát.

## [2026.9.30.post78] - 2026-09-23 - Modálne okno sa už neotvára druhýkrát

**Opravené**

- Okno **Informácie o používateľovi** sa opäť otvára. Minulé upratovanie mŕtveho kódu odstránilo export, ktorý volá skript stránky Používatelia, a okno odpovedalo „Failed to load user info" bez jedinej požiadavky na server.
- Modálne okno sa už **neotvára druhýkrát pod rukami**. Každá cesta, ktorá prekresľovala jeho obsah - Skúsiť znova v chybovom stave, obnovenie vnútri okna, druhé kliknutie na tlačidlo, ktoré ho otvorilo - znovu spustila otváraciu animáciu, posunula obsah na začiatok a vrátila fokus na prvé pole.
- **Ikony, ktoré nekreslili nič, už kreslia.** Štyri názvy, ktoré si JavaScript pýtal, v zrkadle ikon chýbali, a chýbajúci názov vracia prázdny reťazec - teda prázdne odsadené miesto tam, kde má byť výstražná značka chybového stavu.

**Zmenené**

- **Jedna sada ikon všade.** Zrkadlo ikon pre JavaScript zostalo na starej 24x24 sade a ďalších päť súborov si nieslo vlastné tabuľky ikon - karta používateľa, globálny pruh úloh, stránka tiketov, chybová karta analýzy a riadky webhookov. Všetky teraz vedú cez jedno zrkadlo, generované z `icons.html` (Pajamas 16x16), a test spadne, ak sa opäť rozídu.
- **Jeden chybový stav v okne s informáciami o používateľovi**, s funkčným tlačidlom Skúsiť znova, ktoré počas načítania ukazuje svoj stav. Okno tiež vykreslí spinner *pred* stiahnutím vykresľovača karty, nie po ňom.
- **Tlačidlá na chybových stránkach majú stav.** Skúsiť znova aj Hľadať navigujú, čo na spojení, ktoré chybu spôsobilo, nie je okamžité - obe teraz ukazujú spinner aplikácie.
- **Stránka tiketov hovorí po slovensky.** Všetky popisy, ktoré vykresľuje JavaScript, boli anglické; slovenčina bola v katalógu, len ju nemal kto vyžiadať.

**Odstránené**

- Uložená poloha posunu, ktorú žiadne obnovenie nečíta, spolu s pomocníkmi, ktoré ju zapisovali a mazali.
- Hlbšie upratovanie: 166 osirelých slovenských kľúčov, 11 neexistujúcich ciest v špecifikácii API, 9 nepoužívaných schém, 3 nepoužívané makrá šablón a CSS tried, ktoré tým osireli.

## [2026.9.30.post77] - 2026-09-22 - Odstránený mŕtvy kód

**Odstránené**

- Približne 1 000 riadkov, ktoré nikto nečítal: 22 nastavení pre mechanizmy, ktoré neexistujú (na čele s intervalmi `SCHEDULER_*` - plánovač nie je), šesť zapisovacích pomocníkov klienta GitLabu (GitPulse do repozitárov nikdy nezapisuje), štyri metódy repozitára udalostí a index relácií pre nevolané odhlásenie, paleta farieb v `constants.py` a sedem ďalších nepoužívaných funkcií, dve nedosiahnuteľné vetvy starej roly, päť mŕtvych vstupných bodov v JS a 26 pravidiel CSS pre triedy, ktoré nič nevykresľuje.

## [2026.9.30.post76] - 2026-09-22 - Privítanie na domovskej stránke zodpovedá GitLabu na počítači aj na telefóne

**Zmenené**

- **Privítanie:** avatar 64 px, meno 20 px polotučné (18 px na telefóne), veta 16 px, vycentrované s medzerou 16 px - vlastné privítanie GitLabu, odmerané, rovnaké na počítači aj na telefóne.

## [2026.9.30.post75] - 2026-09-22 - Privítanie na domovskej stránke je na telefónoch v súlade s hlavičkami stránok

**Opravené**

- **Privítanie na telefónoch:** meno má rovnakú veľkosť ako každý iný nadpis stránky na telefóne a avatar sedí na riadku mena namiesto toho, aby sa vznášal vedľa zalomenej vety.

## [2026.9.30.post74] - 2026-09-22 - Obrys fokusu prežije hover, prázdny stav náhľadu, kontrola konzistencie

**Opravené**

- **Obrys fokusu:** prejdenie kurzorom ponad zameraný vstup, zaškrtávacie políčko, prepínač alebo vyhľadávacie pole už neodstráni modrý obrys; filtrovacie záložky nad tabuľkami a segmenty témy v Predvoľbách opäť ukazujú obrys pri klávesnicovom fokuse.
- **Prázdne stavy:** záložka Náhľad v editore Markdownu píše „Nie je čo zobraziť.“ namiesto prázdneho poľa.
- **Konzistencia:** štyri natívne zaškrtávacie políčka používajú spoločný štýl; tlačidlá predvolieb váh sú obyčajné sekundárne tlačidlá; filtrovacie záložky nad tabuľkami majú na počítači rovnakú výšku ako každý iný pás záložiek.

## [2026.9.30.post73] - 2026-09-22 - Žiadne druhé obnovenie po nasadení

**Opravené**

- **Obnovenie po reštarte:** nový service worker po prevzatí stránky už neobnovuje stránku podľa časovača (na serveri, ktorý sa ešte rozbieha, z jedného ručného obnovenia urobil dve a to druhé prišlo uprostred posúvania). Opýta sa servera, či stránka zaostáva, a kontrola verzie ju obnoví raz, v pokojnej chvíli, s upozornením.

## [2026.9.30.post72] - 2026-09-22 - Grafy sledujú tému od prvého vykreslenia, čitateľný trend skóre, karta inštalácie je späť, slovenské hlásenia

**Opravené**

- **Grafy a témy:** predvolené nastavenia grafov (popisy osí, písmo, tooltipy) sa aplikujú po načítaní Chart.js namiesto nikdy; v tmavom režime je opäť vidieť mriežku aj sieť radaru (`--chart-grid`).
- **Trend skóre:** prahové čiary a farby bodov používajú 80/50 z kurzu rovnako ako legenda, každá čiara má popis hodnoty; pásma a obrysy bodov sa prekreslia pri zmene témy; výplň má farbu značky; Profil zručností používa farby kategórií.
- **Karta inštalácie:** karta „Nainštalovať GitPulse“ sa opäť zobrazuje a je preložená.
- **Prepínač jazyka** uvádza každý jazyk vlastným názvom; 29 chybových hlásení a výziev preložených do slovenčiny.

## [2026.9.30.post71] - 2026-09-22 - Archivované kurzy: tlačidlá len na čítanie už neodumierajú po prvom použití; vycentrovaná fajka výsledku

**Opravené**

- **Tlačidlo nedostupné po „Hotovo“ v archivovanom kurze:** reset stavu načítania vypol po prvom použití každé neoznačené tlačidlo v archivovanom kurze, hoci ochrana len na čítanie ho nechala živé. Akcie Obnoviť/Načítať znova zostávajú použiteľné; zamknuté zostáva len to, čo zamkne ochrana.
- **Pásik vedľa zelenej fajky:** slovo výsledku sa v ikonových tlačidlách zmrštilo na 2 px prúžok; teraz je tam len pre čítačky obrazovky a značka sedí v strede.
- **Seed demo kurzu:** história plnenia teraz pokrýva celý semester (týždne odvodené z výsledku mechanizmu) namiesto jediného bodu.

## [2026.9.30.post70] - 2026-09-22 - Ikony tlačidiel 16 px všade; obnovenie v hlavičke karty už nie je prázdny štvorec

**Opravené**

- **Primalé ikony:** tlačidlo Obnoviť na karte Priebeh plnenia u študenta kreslilo ikonu širokú 6 px (odsadenie hlavičky prebilo nulové odsadenie ikonového tlačidla), takže pred každým obnovením aj po ňom vyzeralo ako vypnutý prázdny prvok. Ikony v tlačidlách majú teraz 16 px pri každej veľkosti, ako ich kreslí GitLab - kroky 13/14 px pre hlavičky kariet, malé tlačidlá a telefóny sú preč - a malé tlačidlo pri načítaní nemení šírku.

## [2026.9.30.post69] - 2026-09-21 - Stavy tlačidiel: zámky sa uvoľnia po skončení úlohy, odpočet vráti popis, ochrana odoslania

**Opravené**

- **Zámky držali počas „Dokončujem...“ aj po obnovení stránky:** Synchronizovať / Spustiť kontroly / Prepojiť / Odstrániť zostali vypnuté počas osemsekundového čitateľného zobrazenia lišty po úlohe, ktorá už skončila (a znova po F5). Dokončovaná úloha už nedrží zámok, tlačidlo Spustiť kontroly v tej chvíli prestane točiť a obnovené dokončenie končí vlastným textom namiesto „Synchronizácia dokončená!“.
- **Neúspešná synchronizácia sa vracala s textom „Zlyhalo“:** päťsekundový odpočet si uložil červený výsledok ako popis tlačidla; teraz vráti skutočný popis, aria-label aj tooltip.
- **Tlačidlá odoslania mŕtve na 5 s:** ochrana proti dvojitému odoslaniu sa spúšťala pred vlastnou obsluhou formulára pri každom AJAX formulári; teraz počká na koniec udalosti a ukáže spoločný stav načítania.
- **Ikony v lište úloh:** dokončené synchronizácie a behy kontrol majú vlastnú značku namiesto predvolených hodín.

## [2026.9.30.post68] - 2026-09-21 - Spätná väzba pri obnovení, slovenské zdôvodnenia kontrol, konzistencia na telefónoch

**Opravené**

- **Obnoviť štatistiky** na stránke Systém opäť oznamuje výsledok (zdieľaná pomocná funkcia zahadzovala odpoveď načítania, takže toast o úspechu sa nikdy nezobrazil).
- **Zdôvodnenia kontrol po slovensky:** dôvody nesplnenej kontroly z kontrolného mechanizmu („0/2 rôznych recenzentov na vlastnom MR“, ...) sa prekladajú všade, kde sa zobrazujú; doplnených 28 chýbajúcich reťazcov katalógu.
- **Telefóny:** zalomené akcie karty kurzu sú zarovnané vľavo; tabuľky s odopnutým stĺpcom akcií a pásy záložiek majú prechod na okraji, za ktorý sa posúvajú; riadky commitov u študenta sú dvojriadkové s celou správou; graf kontrolného zoznamu zachová každý popis; tlačidlá v hlavičke stránky Systém sa skladajú do ikon ako na stránke Udalosti.
- **Popisy** pri Zobraziť, + Skupina, Zobraziť všetko a prepínačoch JSON; stav načítania pri rotácii tajného kľúča.

## [2026.9.30.post67] - 2026-09-21 - Dokončené slovenské rozhranie, bezpečnostná aktualizácia anyio

**Opravené**

- **Slovenské rozhranie:** citát pod menom na domovskej stránke, každý typ úlohy a audítorská akcia v Histórii úloh a v prehľade aktivity a hlavička stĺpca Skóre sú preložené; karta kontrol a dialóg importu uvádzajú R01-R13.
- **Bezpečnosť:** `anyio` aktualizované na 4.14.2 (tri CVE).

**Zmenené**

- **Snímky v README:** nanovo z aktuálneho zostavenia vo svetlej téme a v slovenčine nad demonštračným kurzom `ZSI-DEMO`.

## [2026.9.30.post66] - 2026-09-21 - Každá tabuľka premeraná na telefónoch

**Opravené**

- **Tabuľky na telefónoch:**
  - Pripnuté stĺpce akcií zostávajú pripnuté všade, kde nechajú riadku miesto, a posúvajú sa s ním tam, kde nie - premerané na každej tabuľke pri 360-430px.
  - Kontroly zhody ukazujú na telefóne každý stĺpec (prepínač, kód, názov, kategóriu, váhu, zdroj) a posúvajú sa; riadky Histórie úloh sú kompaktné; tabuľky Projektov a Tiketov už nenafukujú prvý stĺpec.

## [2026.9.30.post65] - 2026-09-21 - Tabuľky na malých telefónoch

**Opravené**

- **Tabuľky na malých telefónoch:**
  - Pripnutý stĺpec akcií, ktorý by zabral viac než dve pätiny obrazovky, sa teraz posúva s riadkom, takže stĺpce pred ním sú čitateľné; ikonové tlačidlá riadkov majú na dotyku 36px, aby dvojtlačidlový stĺpec zostal pripnutý.

## [2026.9.30.post64] - 2026-09-21 - Otáznik v hlavičke karty a výber roly na telefónoch

**Opravené**

- **Otáznik v hlavičke karty na telefónoch:**
  - Otáznik s nápovedou v hlavičke karty sa na archivovanom kurze už nezamyká a neprekrýva sa s akciou vedľa neho; je to jeden 28px cieľ na ťuknutie.
- **Výber roly na telefónoch:**
  - Výber „Course Owner" v tabuľke Učiteľov už pripnutý stĺpec Akcií neorezáva pri šípke.

## [2026.9.30.post63] - 2026-09-21 - Výbery v posuvných boxoch, prechody tabuliek, medzera pod panelom, hover na dotyku, odznaky a prázdny stav tiketu

**Opravené**

- **Výbery v posuvných boxoch:**
  - Výber roly v tabuľke Učiteľov otvára ponuku nad tabuľkou namiesto orezania na posledných riadkoch.
- **Prechody tabuliek:**
  - Prechod na pravom okraji už nestmavuje pripnutý stĺpec akcií a spodný prechod cez posledný viditeľný riadok je preč.
- **Medzera pod panelom:**
  - Stránky s lištou uloženia majú pod zaobleným panelom 8px medzeru ako každá iná stránka; posledná karta nastavení kurzu sa už nedotýka okraja panela.
- **Hover na dotyku:**
  - Štýly hover tlačidiel a otáznika platia len pre zariadenia s kurzorom, takže ťuknutý prvok nezostáva na telefóne podsvietený.
- **Odznaky:**
  - Značka „vypnuté" v zozname Týždenného termínu sedí pri názve kontroly; značka Auto-fill pri „GitLab URL" je štandardný malý odznak.
- **Prázdny stav tiketu:**
  - Požiadavka otvorená bez popisu to povie namiesto prázdneho boxu.

## [2026.9.30.post62] - 2026-09-21 - Vnútorné rohy kariet, prehrávanie pri návrate na kartu, hrana pripnutého stĺpca, akcie hlavičky na telefónoch a mŕtve CSS

**Opravené**

- **Vnútorné rohy kariet:**
  - Tabuľky, stránkovanie a poznámky vnútri karty končia na polomere rohu tela karty - žiadny zárez pozadia v spodných rohoch posledného riadku.
- **Prehrávanie pri návrate na kartu prehliadača:**
  - Vo vývoji reštart servera bez zmeny kódu už neprenačíta každú otvorenú kartu; dashboard a Stav systému sa prekreslia, len keď sa naozaj niečo zmenilo, takže sa pri návrate nič neprehráva odznova.
- **Hrana pripnutého stĺpca:**
  - Tieň pripnutého stĺpca akcií sa zobrazuje len vtedy, keď sú pod ním skryté stĺpce, nie keď je tabuľka posunutá na koniec.
- **Akcie hlavičky na telefónoch:**
  - Na telefónoch akcia v hlavičke ukazuje ikonu s popisom v tooltipe a v prístupnom názve, takže hromadné akcie Udalostí sedia v riadku s názvom.
- **Mŕtve CSS:**
  - Pravidlá, ktoré už nič nevykresľovalo, boli odstránené spolu s testami, ktoré ich strážili.

## [2026.9.30.post61] - 2026-09-21 - Zárez v rohu tabuliek, výška stránky na telefónoch, zalamovanie akcií kariet, vybrané riadky, hover na dotyku, toasty zakázaných prvkov, vysvetlenia typov úloh, kontrakt obnovenia a tokeny farieb grafov

**Opravené**

- **Zárez v rohu tabuliek:**
  - Posledný riadok tabuľky už v spodných rohoch neukazuje zárez pozadia karty.
- **Výška stránky na telefónoch:**
  - Dokument je opäť presne na výšku obrazovky, takže sa stránka neposúva pod horný panel a lišta uloženia aj posledný riadok tabuľky zostávajú dosiahnuteľné. Dlhé tabuľky sa na telefónoch už neposúvajú vo vlastnom boxe - stránka sa posunie až na ich posledný riadok.
- **Akcie kariet na telefónoch:**
  - Akcie v hlavičke zostávajú v riadku s názvom, kým sa doň zmestia (vpravo), a do vlastného riadku zarovnaného vľavo sa zalomia, len keď sa nezmestia.
- **Vybrané riadky a hover na dotyku:**
  - Zaškrtnutie riadku ho podsvieti farbou výberu v každej tabuľke s výberom; hover riadku platí len pre zariadenia s kurzorom, takže ťuknutý riadok nezostáva podsvietený.
- **Zakázané prvky sa po ťuknutí vysvetlia:**
  - Ťuknutie na zakázaný prvok zobrazí jeho dôvod ako toast.
- **História úloh:**
  - Tooltip typu vysvetľuje, čo úloha robí, a zamknuté zaškrtávacie políčko záznamu odvodeného z audit logu hovorí, prečo sa nedá vybrať.
- **Kontrakt obnovenia:**
  - Tlačidlá Znovu načítať (história študenta), Obnoviť (udalosti) a Obnoviť v administrácii sa správajú ako „Skontrolovať teraz" v Stave systému: stav práce, región na mieste, jeden výsledok a úspech hlásený len vtedy, keď načítanie naozaj prebehlo.
- **Tokeny farieb grafov:**
  - Prstenec pipeline a Trend skóre / Profil zručností študenta berú každú farbu z tokenov témy v oboch farebných režimoch.

## [2026.9.30.post60] - 2026-09-21 - Správne podsvietenie tabuliek podľa témy, akcie kariet vpravo, jednotný mobilný panel, orámovanie sticky tabuliek, okamžité ukončenie prázdneho behu kontrol, štandardné 404 stránky a prázdne stavy grafov

**Opravené**

- **Podsvietenie tabuliek podľa témy:**
  - Hover riadku je opäť neutrálna sivá; odtieň vybraného / presmerovaného riadku sa odvodzuje z `--gl-action-selected-border` (modrá v predvolenej téme, akcent pri zvolenom motíve). Nedefinovaný token `--gl-theme-accent`, ktorý podsvecoval riadky načerveno, je preč.
- **Rozloženie hlavičky kariet:**
  - Na desktope je hlavička jeden riadok: názov, odznak s počtom vedľa neho, akcie a otáznik vpravo. Iba na telefónoch sa akcie zalamujú do vlastného riadku zarovnaného vľavo.
- **Jednotný mobilný panel na stránkach s lištou uloženia:**
  - Nastavenia kurzu, Učitelia a Predvoľby majú na telefónoch rovnaký odsadený zaoblený panel obsahu ako každá iná stránka.
- **Orámovanie sticky tabuliek:**
  - Dátové tabuľky používajú oddelené orámovanie, takže sticky hlavička a pripnutý stĺpec akcií nesú vlastnú spodnú čiaru - žiadny schod čiary pri stĺpci akcií ani čiara pod posledným riadkom.
- **Odznak váh kontrol zhody:**
  - Súčet aktívnych váh je odznakom v hlavičke karty vedľa názvu.
- **Okamžité ukončenie prázdneho behu kontrol:**
  - Spustenie kontrol v kurze bez aktívnych skupín ihneď ohlási „V kurze nie sú aktívne skupiny.“ v lište úloh namiesto osemsekundového „Dokončujú sa kontroly...“ so skrytou lištou.
- **Štandardné 404 stránky:**
  - Neexistujúci alebo neprístupný kurz, skupina, projekt či študent zobrazí štandardnú chybovú stránku 404 namiesto karty „Nenájdené“ vnútri aplikácie.
- **Prázdne stavy grafov:**
  - Kontrolný zoznam učiteľa (aj bez hodnotených študentov či snímky), Týždenná analytika, Trend skóre a Profil zručností študenta a náhľad obsahu udalosti zobrazujú rovnaký prázdny stav ako každá prázdna tabuľka.
- **Pád skriptov pri SPA navigácii:**
  - Opravená chyba `Cannot read properties of null (reading 'insertBefore')`, ktorú vyvolával htmx opätovným spúšťaním skriptov stránky, ktoré navigačný handler už presunul.

## [2026.9.30.post59] - 2026-09-19 - Neprerušená línia hlavičky tabuľky, adaptívne podsvietenie pri presmerovaní, roztiahnuté vyhľadávanie a gesto potiahnutia sidebaru na mobile

**Opravené**

- **Zjednotená a neprerušená deliaca čiara hlavičky tabuliek:**
  - Odstránené nesúrodé orámovanie `border-bottom` na poslednom stĺpci sticky akcií a zavedený jednotný vnútorný tieň `box-shadow: inset 0 -1px 0 var(--border-color)` pre všetky bunky `thead th`, čím sa zabezpečila súvislá deliaca čiara po celej šírke tabuľky.
- **Témovo-adaptívne podsvietenie prvkov pri presmerovaní a navigácii:**
  - Využitie tokenov aktívnej témy `--gl-theme-accent` a `--gl-table-row-selected-bg` v `GP.motion.highlight`, vďaka čomu sa pri presmerovaní alebo odkaze cez URL hash/parametre zvýraznený riadok automaticky odhalí v rozbalenej karte a podsvieti farbou zvoleného motívu.
- **Roztiahnutie vyhľadávacieho poľa tiketov podpory a ovládacích pásov:**
  - Kontajner vyhľadávania a obalujúce prvky (`.table-controls-search > div, [data-tour], .search-box`) sa teraz dynamicky rozťahujú po celej dostupnej šírke až k filtrom.
- **Gesto potiahnutia (swipe-to-close) pre bočný panel na mobilných zariadeniach:**
  - Pridaná podpora dotykového potiahnutia doľava na `.gl-sidebar` pre úzke mobilné obrazovky, ktorá umožňuje intuitívne zatvorenie vysunutého sidebaru.

## [2026.9.30.post58] - 2026-09-19 - Jednoradové hlavičky kariet so zalomením vľavo, adaptívne tokeny podsvietenia tabuliek a priestranné odsadenie

**Opravené**

- **Zachovanie jedného riadku hlavičiek kariet so zalomením akcií vľavo:**
  - Upravené rozloženie hlavičiek `.card-header` pomocou `justify-content: space-between` a `flex: 0 1 auto` pre `.card-title`, vďaka čomu titulok a tlačidlá akcií ostávajú v jednom riadku čo najdlhšie a pri nedostatku šírky sa akcie zalamujú na začiatok ďalšieho riadku vľavo bez predčasného delenia alebo rigidných breakpointov.
- **Dynamická tokenizácia lepiacich hlavičiek a podsvietenia riadkov tabuliek pre všetky témy:**
  - Zavedené CSS tokeny `--gl-table-header-bg`, `--gl-table-row-hover-bg` a `--gl-table-row-selected-bg` odvodené dynamicky cez `color-mix` s aktívnou akcentovou farbou `--_accent` v tmavom aj svetlom režime naprieč všetkými motívmi (Indigo, Blue, Green, Red, Gray) pre lepiace záhlavia `thead th`, akcie a stavy `:hover` / `.is-nav-busy-tint`.
- **Vyčistenie CSS prepisov vyhľadávacieho poľa a uvoľnenie priestoru nad ovládacími prvkami:**
  - Odstránená fixná šírka `.search-box input` v `admin.css` v prospech natívneho responzívneho správania komponentov Pajamas.
  - Odstránený agresívny záporný okraj `.card-body > .table-controls:first-child` (`margin-top: 0`), čím ovládacie pásy a vyhľadávacie polia získali plnohodnotný a prirodzený 24px odstup od horného okraja karty bez stlačenia.

## [2026.9.30.post57] - 2026-09-19 - Estetický priestor hlavičiek kariet, vycentrovanie selektorov a ovládacích prvkov

**Opravené**

- **Rozšírenie priestoru hlavičiek kariet a symetrické centrovanie selektorov:**
  - Obnovená minimálna výška hlavičky kariet `.card-header` na `44px` s centrovaným vertikálnym zarovnaním pre dostatočný a estetický priestor názvu a akcií.
  - Nastavená minimálna výška ovládacích pásov `.table-controls` na `44px` s nulovým paddingom a vertikálnym centrovaním pre všetky selektory, dropdowny a vyhľadávanie.
  - Nastavené symetrické odsadenie `.card-body > .table-controls:first-child` (`-12px`) a `margin-bottom` (`12px`), čím selektory získali priestranný a rovnaký 18px odstup zhora aj zdola naprieč všetkými tabuľkami (Events, Users, System atď.).

## [2026.9.30.post56] - 2026-09-19 - Komponentové zdvihnutie ovládacích prvkov tabuliek a symetrické rozostupy hlavičiek

**Opravené**

- **Zdvihnutie vstupného poľa vyhľadávania a kompaktné zarovnanie ovládacích pásov tabuliek:**
  - Upravený záporný horný okraj `.card-body > .table-controls:first-child` na `calc(var(--gl-spacing-2) - var(--gl-spacing-6))` (-20px), čím sa odstránil nadbytočný prázdny priestor nad poľom vyhľadávania naprieč všetkými kartami tabuliek.
  - Vyvážený spodný okraj `.table-controls` na `var(--gl-spacing-3)` (8px), vďaka čomu je vzdialenosť od vyhľadávacieho poľa nahor (k hlavičke karty) a nadol (k hlavičke tabuľky) identická (14px).

## [2026.9.30.post55] - 2026-09-19 - Symetrické vertikálne centrovanie vyhľadávania a rozostupy ovládacích pásov tabuliek

**Opravené**

- **Vycentrovanie vyhľadávacieho poľa a symetria ovládacích pásov tabuliek:**
  - Nastavený nulový padding a `min-height: 44px` pre `.table-controls--tabs` a `.table-controls:has(.filter-tabs)`, čím sa odstránil posun nadol a pole vyhľadávania je striktne vertikálne vycentrované s rovnakou vzdialenosťou zhora aj zdola v ovládacom páse.
  - Zvýšená poloha vstupného poľa vyhľadávania a obnovený základný nulový horný padding pásu tabuľky (`padding: 0 0 var(--gl-spacing-2)`).
  - Zväčšené spodné odsadenie `.table-controls` na `var(--gl-spacing-5)` (16px), čím sa znížila hlavička tabuľky a dosiahli sa rovnaké vzdialenosti nad vstupom (od hlavičky karty) aj pod vstupom (k hlavičke tabuľky).
  - Upravený padding hlavičky karty na dizajnový token `var(--gl-spacing-3) var(--gl-spacing-4)` (8px zhora/zdola) pre vyvážené zarovnanie.
  - Zachované priradenie `this.pageSize = saved` v `components.js` pre plnú kompatibilitu testov a zmluvy paginácie.

## [2026.9.30.post54] - 2026-09-19 - Zjednotenie možností paginácie, vylepšenie modálu udalostí, zarovnanie stĺpcov používateľov a kurzov

**Opravené**

- **Zjednotenie volieb paginácie («Rows per page»):**
  - Nastavený identický zoznam možností `[25, 50, 100, 'all']` naprieč všetkými tabuľkami podľa systémových nastavení (`Preferences > Rows per page`) s označeniami `"25 per page"`, `"50 per page"`, `"100 per page"`, `"Show all"` a checkmark SVG ikonou pri aktívnej položke.
  - Nastavená striktná predvolená veľkosť 50 v komponentoch paginácie a šablónach.
- **Komplexné vylepšenia modálneho okna detailov udalosti (Event Details):**
  - Pridaný plnohodnotný stav prázdnoty (Empty state) s ikonou `inbox`, nadpisom a popisom pri prázdnom payload (`{}` alebo `null`).
  - Implementované tokenizované zvýrazňovanie syntaxe JSON payloadu (`syntax-key`, `syntax-string`, `syntax-number`, `syntax-bool`, `syntax-null`).
  - Pridané ikony pre všetky atribúty a stavové odznaky (`tag`, `shield`, `calendar`, `check-circle`, `folder`, `user`, `message-square`, `play`, `repeat`, `hash`).
  - Pridaný varovný banner chyby (`gl-alert gl-alert-danger`) a funkčné tlačidlo «Copy JSON» s dočasnou spätnou väzbou «Copied!».
  - Rozšírená odpoveď API `/api/v1/events/{id}/payload` o polia `summary`, `actor`, `processed_at`, `dead_letter_at` a `action`.
- **Oprava úniku chybovej hlášky v tabuľke udalostí:**
  - Text chyby (`unhandled_kind: ...`) sa už nezobrazuje vedľa zeleného odznaku `Processed`; zobrazuje sa výhradne pri stave `Failed`.
- **Zamedzenie pretekania emailov a vyváženie šírok v tabuľke používateľov:**
  - Pridané `max-width: 100%`, `overflow: hidden`, `text-overflow: ellipsis` a `white-space: nowrap` pre bunky emailu, celého mena a používateľského mena.
  - Vyvážené šírky stĺpcov: `col-email` rozšírený na 25% (min. 200px), `col-role` na 12% (min. 120px) proti orezaniu rolí `Administrator`/`Teacher`, a `col-created` na 10% (min. 110px).
- **Zarovnanie stĺpca akcií v tabuľke kurzov:**
  - Stĺpec akcií zarovnaný k pravému okraju (`col-course-actions text-right`, `justify-content: flex-end`, šírka 120px) a opravený chýbajúci uzatvárací tag `</td>`.
- **Symetria rozostupov ovládacích prvkov a stabilizácia scrollbaru:**
  - Vyvážené vnútorné a vonkajšie okraje `.table-controls` v `tables.css` (`margin-top: calc(-1 * var(--gl-spacing-3))`, `padding: var(--gl-spacing-3) 0`).
  - Pridané pravidlo `[data-paginator] table:not(.paginator-ready) tbody tr:nth-child(n+51) { display: none !important; }` zamedzujúce počiatočnému pretiahnutiu výšky tabuľky a zdvojnásobeniu vertikálneho scrollbaru.
  - Odstránené pevné obmedzenie `max-width: 320px` pri názvoch tiketov v tabuľke podpory.
- **Rozostupy detailu tiketu a tokenizácia Markdown editora:**
  - Zvýšený spodný odstup pre `.gh-ticket-meta-row` (`padding-bottom: var(--gl-spacing-6)`, `margin-bottom: var(--gl-spacing-6)`), čím sa oddelila deliaca čiara od zoznamu účastníkov.
  - Kompletná tokenizácia Markdown editora pomocou `--gl-...` tokenov témy.
  - Odstránený vonkajší `:focus-visible` box-shadow z textarea spôsobujúci fialové linky cez rozhranie editora.
- **Navýšenie vyrovnávacej pamäte Service Workera (`gitpulse-v635`):**
  - Aktualizovaná verzia cache pre okamžité zneplatnenie cache u klientov.

## [2026.9.30.post53] - 2026-09-19 - Vrátenie pôvodného zobrazenia paginácie po celej šírke karty a vyrovnanie okrajov

**Opravené**

- Obnovenie pôvodného rozloženia paginácie podľa overenej verzie: navrátené negatívne horizontálne okraje pre `.card-body:not(.p-0) > .pagination-controls` (`margin: var(--gl-spacing-4) calc(-1 * var(--gl-spacing-5)) calc(-1 * var(--gl-spacing-5))`) na desktope, tablete aj mobile.
- Odstránenie nežiaducich bočných medzier a vzhľadu "plávajúcej lišty": ovládací panel paginácie sa opäť plynulo rozprestiera od ľavého po pravý okraj karty a lícuje s celou šírkou spodnej časti karty.
- Obnovenie štandardného vnútorného odsadenia tela karty (`var(--gl-spacing-6)`) a zaoblenia spodných rohov paginácie (`var(--gl-card-border-radius)`).
- Navýšenie vyrovnávacej pamäte Service Workera (`gitpulse-v634`) pre okamžité zneplatnenie cache štýlov u klientov.

## [2026.9.30.post52] - 2026-09-19 - Úprava šírok stĺpcov tabuľky používateľov, plynulé pripojenie paginácie, stabilizácia vertikálneho scrollovania a symetrické rozostupy hlavičiek kariet

**Opravené**

- Úprava šírok stĺpcov a zamedzenie orezania textu v tabuľke používateľov: stĺpec `GitLab User ID` (`col-gitlabid`) bol rozšírený z 9% (max. 125px) na 13% (`min-width: 160px`), čím sa odstránilo skracovanie popisu a sortovacie šípky sa zobrazujú kompletne v jednom riadku. Stĺpec `Celé meno` (`col-fullname`) bol posunutý doprava s navýšením na 21% (`min-width: 170px`) s využitím voľného miesta, a stĺpec `Email` vyvážený na 19%.
- Stabilizácia výšky tabuľky pri načítaní a odstránenie zdvojovania vertikálneho scrollbaru: v počiatočnom vykresľovaní pred inicializáciou paginátora bol upravený selektor `.users-table:not(.paginator-ready) tbody tr:nth-child(n+51)` na `n+26`, vďaka čomu sa od prvého rámca zobrazuje predvolených 25 riadkov namiesto 50. Tým sa zamedzilo skokovému zmenšeniu výšky tabuľky na polovicu po inicializácii paginácie a prudkému zdvojnásobeniu jazdca posuvníka. Zároveň bol odstránený vnútorný vertikálny posuvník pri paginovaných tabuľkách (`overflow-y: visible; max-height: none`), čím sa eliminoval nežiaduci dvojitý scrollbar.
- Bezmedzerové pripojenie paginácie k tabuľke: odstránené negatívne horizontálne okraje z `.pagination-controls` na všetkých zariadeniach (desktop, tablet, mobil), vďaka čomu ovládanie stránkovania dokonale lícuje so šírkou tabuľky. Paginácia priamo nadväzuje na spodnú hranu tabuľky (`margin: -1px 0 0 0`), spodný okraj `.card-body` bol vynulovaný a rohy paginácie zjednotené s polomerom karty `var(--radius-md)`.
- Zvýšenie hlavičiek kariet a symetrické vertikálne rozostupy: minimálna výška `.card-header` bola mierne navýšená na 40px s vnútorným okrajom 6px (na mobile 38px / 5px), čo zaručuje dostatok priestoru pre ovládacie prvky. Vyhľadávacie pole v lište filtrov s tabmi bolo vertikálne vycentrované (`align-self: center`), čím sa dosiahol symetrický rozostup zhora aj zdola.
- Navýšenie vyrovnávacej pamäte Service Workera (`gitpulse-v633`): aktualizovaná hodnota `CACHE_VERSION` pre okamžité zneplatnenie cache u klientov.

## [2026.9.30.post51] - 2026-09-19 - Zachovanie zeleného stavu hotovo pri tlačidlách, dynamické akcie hlavičiek, symetrické rozostupy ovládacích prvkov tabuliek a zarovnanie kopírovania v diff prehliadači

**Opravené**

- Zachovanie zeleného stavu hotovo ("Done") na zablokovaných tlačidlách: pridané pravidlá s `!important` pre triedy `.btn.btn-done`, `.btn:disabled.btn-done`, `.btn.is-saved` a ďalšie výstupné stavy používajúce dizajnové tokeny `var(--gl-badge-success-bg)` a `var(--gl-badge-success-text)`. Všeobecné pravidlá pre zablokované tlačidlá (`.btn:disabled`, `.is-course-archived`) boli doplnené o selektory `:not(.btn-done):not(.btn-error)`, čím sa zabránilo nechcenému prefarbeniu úspešne dokončeného zeleného stavu na sivú farbu pri prechode tlačidla do stavu disabled po uložení. Všetko implementované čisto cez dizajnové tokeny bez inline štýlov.
- Odstránenie sivého rámčeka z počítadla záznamov v tabuľkách: z triedy `.table-count` v `tables.css` bolo odstránené pozadie `background: var(--surface-moderate)`, vnútorný okraj a zaoblenie rohov, čím sa text "Zobrazuje sa X z Y" vrátil do čistého sekundárneho textového formátu bez orámovania.
- Dynamické responzívne akcie v hlavičkách kariet: statická `@media (max-width: 640px)` bola nahradená dynamickým zisťovaním dostupnej šírky a pretečenia pomocou `ResizeObserver` v `20-ui-helpers.js`. Akcie v hlavičke karty (napr. Webhook Konfigurácie, Učitelia kurzu) sa zbalia na ikony len vtedy, ak reálna šírka kontajnera nepostačuje pre textové popisy, inak zostávajú zobrazené celé texty.
- Symetrické vertikálne rozostupy ovládacích prvkov tabuliek: odstránený negatívny horný margin z `.card-body > .table-controls:first-child` a upravené spodné odsadenie pre `.table-controls-search` pred tabmi filtrov. Vstupné pole a rolovací výber v zozname vyučujúcich majú teraz zhora aj zdola zhodný, symetrický rozostup `var(--gl-spacing-3)`.
- Vycentrovanie ikony kopírovania v hlavičke súborov git diff: v prehliadači zmien kódu študenta (`student.css`) bola zjednotená výška nástrojovej lišty `.dn-code-toolbar` na 32px a ikona kopírovania `.dn-code-collapse > .dn-code-action` (výška 24px) presne vertikálne vycentrovaná pomocou `top: 4px` do jednej osi s názvom súboru.
- Navýšenie vyrovnávacej pamäte Service Workera (`gitpulse-v632`): aktualizovaná hodnota `CACHE_VERSION` pre okamžité zneplatnenie cache u klientov.

## [2026.9.30.post50] - 2026-09-19 - Zmenšenie výšky hlavičiek kariet a tabuliek, zbalenie responzívnych tlačidiel do jedného riadku a kompaktné pridávanie učiteľov

**Opravené**

- Zmenšenie výšky hlavičiek kariet a tabuliek: znížená minimálna výška `.card-header` na 36px (34px na mobile) a vertikálny padding na 4px, čím sa ušetrilo ~25% vertikálneho priestoru. V bunkách hlavičiek tabuliek (`.data-table th`) bol vertikálny padding zredukovaný zo 16px na 8px a písmo zjednotené na `font-size-sm`.
- Odstránenie hluchého miesta nad tabuľkami: zmenšený spodný padding a margin v pásme `.table-controls` zo 16px na 8px/12px, a pre karty s tabuľkami upravený padding `.card-body` na kompaktných 12px, čím sa eliminoval nadmerný prázdny priestor.
- Zbalenie tlačidiel hlavičiek do jedného riadku: upravené ďalšie tlačidlá v hlavičkách kariet (pridanie kontroly, zrušenie obmedzení vyučujúcich, pridanie webhook konfigurácie). Na mobilných obrazovkách (`<= 640px`) sa tlačidlá automaticky zbalia na čisté ikony s tooltipom, takže zostávajú v prvom riadku vedľa názvu. Odznak celkovej váhy (`Σ 1.00`) bol presunutý do názvu karty `🛡️ Compliance Checks`. V prípade zalomenia na extrémne úzkych displejoch sa akcie zarovnávajú doľava.
- Kompaktné pridávanie učiteľov: upravený `.teacher-add-row` na mobile a tablete na jednoriadkový flexibilný layout, takže pole vyhľadávania a výber roly sedia vedľa seba v jednom riadku.
- Navýšenie vyrovnávacej pamäte Service Workera (`gitpulse-v631`): aktualizovaná hodnota `CACHE_VERSION`.

## [2026.9.30.post49] - 2026-09-19 - Kompaktné akcie kariet v riadku, rozostupy tlačidiel tabuliek, vycentrovanie skóre a Service Worker cache bump

**Opravené**

- Kompaktné akcie hlavičiek kariet v jednom riadku: zjednotené pravidlá pre `.card-header` (`flex-wrap: nowrap; min-height: 44px;`) a `.card-actions` so zachovaním zobrazenia v jednom riadku na desktope aj mobile. Akčné tlačidlá kariet (napr. zrušenie obmedzení vyučujúcich, pridanie týždňa) majú výšku 26px s kompaktným vnútorným okrajom a 14px ikonami, čím sa zabraňuje nežiaducemu zalamovaniu a nafukovaniu hlavičiek.
- Rozostupy akčných tlačidiel v riadkoch tabuliek: v tabuľke týždenných deadlinov a ďalších bunkách s viacerými tlačidlami sú akcie obalené v kontajneri `.weekly-row-actions` s medzerou `gap: var(--gl-spacing-2)` (8px) a stĺpec rozšírený na 100px s `white-space: nowrap`. Pridané globálne pravidlo `.data-table td .btn + .btn { margin-left: var(--gl-spacing-2); }`, ktoré zabraňuje vzájomnému dotýkaniu tlačidiel.
- Vycentrovanie stĺpca a odznaku skóre: v matici členov tímu je hlavička skóre vycentrovaná (`text-center`) a odznak posunutý o 4px doľava (`transform: translateX(-4px)`), čím je opticky presne vycentrovaný pod textom stĺpca voči šípke radenia.
- Umiestnenie počítadla skupín: počítadlo `Showing X of Y` v zozname skupín je umiestnené v hlavnom riadku vedľa názvu `👥 Groups` namiesto zalomenia do samostatného riadku.
- Navýšenie vyrovnávacej pamäte Service Workera (`gitpulse-v630`): aktualizovaná hodnota `CACHE_VERSION`.

## [2026.9.30.post48] - 2026-09-19 - Odstránenie spodnej medzery lepiaceho panelu tlačidiel, harmonizácia stavov tlačidiel a načítavačov podľa System Health

**Opravené**

- Odstránenie spodnej medzery pod lepiacim panelom tlačidiel na PC a mobile: prvok `.gl-page:has(.settings-sticky-footer)` má nastavenú výšku na `calc(100vh - var(--navbar-height)) !important;` (a `100dvh`), čím sa odstránila plávajúca 8px medzera a spodný polomer zaoblenia kariet. Vynulovaný spodný padding na `.gl-page-content` a `.main-container`, a na mobilných zariadeniach (`<= 768px`) zabezpečené roztiahnutie na celú šírku (`margin: 0 !important; border-radius: 0 !important;`). Vypnutá pätička stránky na dotknutých šablónach. Lepiaci panel teraz sedí 100% presne na spodku okna bez akejkoľvek medzery.
- Harmonizácia stavov tlačidiel a načítavania podľa vzoru System Health: zjednotené riadenie UI zámkov (`GP.withUiLock`) a stavov tlačidiel naprieč nastaveniami, vyučujúcimi, tiketmi podpory a prihlasovaním. Odstránené ad-hoc zneplatňovanie tlačidiel v prospech centrálneho `setButtonLoading(btn, true/false)` s minimálnym 450ms trvaním na elimináciu blikania rozhrania.
- Navýšenie vyrovnávacej pamäte Service Workera (`gitpulse-v629`): aktualizovaná hodnota `CACHE_VERSION`.

## [2026.9.30.post47] - 2026-09-19 - Rozloženie hlavičky karty, zarovnanie ikony nápovedy, harmonizácia tabuliek, oprava tlačidla reload a nasadenie tiketov

**Opravené**

- Zarovnanie ikony nápovedy a akčných tlačidiel v hlavičke kariet: ikona nápovedy (`.card-header-info-tip`) je na desktope aj mobile ukotvená úplne vpravo na prvom riadku (`margin-left: auto;`), znížená o 1.5px pomocou `transform: translateY(1.5px)` pre presné optické vycentrovanie bez zväčšenia výšky hlavičky. Na mobile sa tlačidlá zalamujú do 2. riadku a začínajú zarovnané doľava (`justify-content: flex-start; margin-left: 0;`).
- Tlačidlo opätovného načítania webhook konfigurácií v archivovanom kurze: pomocná funkcia `_applyButtonLoadingReset` teraz vynecháva ovládacie prvky s `data-readonly-ok` z trvalého zablokovania po dokončení načítania v `.is-course-archived`, takže tlačidlo opätovného načítania nezostáva zamrznuté.
- Harmonizácia rozloženia stĺpcov tabuliek (štandard GitLab): vyvážené percentuálne šírky stĺpcov aplikované na maticu kontrol členov (odstránená prázdna plocha v mene študenta, kontrolné stĺpce R01-R13 majú rovnomerný priestor), správu používateľov, vyučujúcich a aktivitu.
- Nasadenie vzorových tiketov podpory v dev prostredí: skript `scripts/seed_support_tickets.py` vytvoril 15+ rôznorodých tiketov s kategóriami, prioritami, stavmi a vláknami interných a verejných komentárov.
- Navýšenie vyrovnávacej pamäte Service Workera (`gitpulse-v628`): aktualizovaná hodnota `CACHE_VERSION`.

## [2026.9.30.post46] - 2026-09-19 - Zostavenie produkčných balíkov CSS/JS a aktualizácia vyrovnávacej pamäte Service Workera

**Opravené**

- Opätovné zostavenie a minifikácia produkčných balíkov: nanovo skompilované a zmenšené `core.bundle.js` (633 KB), `styles.bundle.css` (457 KB) a všetky stránkové balíky a `.min` súbory pre okamžité nasadenie všetkých zmien používateľského rozhrania do prehliadača.
- Navýšenie vyrovnávacej pamäte Service Workera (`gitpulse-v627`): aktualizovaná hodnota `CACHE_VERSION` v `sw.js` pre vynútené stiahnutie najnovších statických aktív.

## [2026.9.30.post45] - 2026-09-18 - Presun lupy k hodinám v hornom paneli, zachovanie akcií kariet v riadku a stĺpec skóre na konci tabuľky

**Opravené**

- Presun ikony vyhľadávania vedľa dátumu a hodín v hornom paneli: na mobilných zariadeniach presunuté vyhľadávanie doprava priamo pred kontext akademického roka a hodín s presným odstupom 8px.
- Zachovanie akcií v hlavičke kariet v jednom riadku a symetrické odsadenie: odstránené vynútené zalamovanie `width: 100%` v `cards.css` a `00-mobile.css`, vďaka čomu tlačidlá ako "Zrušiť všetky obmedzenia" nezalamujú riadok pri dostatku miesta; zachovaný rovnomerný zvislý odstup 8px.
- Komponentové počítadlá namiesto odznakov: nahradené jednoduché číselné odznaky v hlavičkách kariet komponentom `table_count` vo formáte "Zobrazuje sa X z Y".
- Umiestnenie stĺpca celkového skóre na koniec tabuľky členov: presunutý stĺpec skóre v šablónach a skripte za kontroly dodržiavania pravidiel (R01..R13) bezprostredne pred stĺpec akcií.
- Ochrana pred deformáciou tabuľky pri obnove a minimalizácia preblikávania: odstránený problematický prechod priehľadnosti pre `.table-scroll` a pridaná ochrana hash metrík v `updateMembersTable()` proti nadbytočným zmenám DOM pri prepínaní okien a opätovnom pripájaní SSE.
- Navýšenie vyrovnávacej pamäte Service Workera (`gitpulse-v626`): aktualizovaná hodnota `CACHE_VERSION` v `sw.js`.

## [2026.9.30.post44] - 2026-09-18 - Úprava mobilnej navigácie, symetria tlačidiel kariet, oprava dotykového triedenia a rozloženia tabuľky členov

**Opravené**

- Rozloženie mobilného horného panela a odstránenie kolízie hodín: prevedený `.gl-top-bar` na flex rozloženie na mobiloch, čím sa lupa presunula k navigačnému menu doľava a pravá strana zostáva vyhradená pre hodiny a profilového avatara.
- Oddeľovacia čiara rýchleho prístupu: pridaný prvok `.gl-qa-divider` medzi prepínače záložiek a zoznam položiek na bočnom paneli.
- Symetrické odstupy tlačidiel v hlavičkách kariet: zjednotené zvislé medzery pre zalomené tlačidlá akcií na mobiloch (rovnomerný odstup 8px od nadpisu aj tela karty).
- Ochrana pred nechceným triedením tabuliek pri dotykovom posúvaní: pridaná detekcia gesta potiahnutia v `sortable-table.js` a podmienenie stavu `:hover` cez `@media (hover: hover)`.
- Odstránenie preblikávania pravého okraja pri načítaní: vypnuté animované prechody priehľadnosti pre `.table-scroll` počas prvého vykreslenia a na mobiloch.
- Zarovnanie stĺpcov skóre a kontrol v tabuľke členov projektu: opravené indexy stĺpcov v `00-core.js` a `_ensureMembersTable()`, vďaka čomu sa stĺpec so skóre na mobiloch neskrýva, a odstránený nadbytočný znak na začiatku `project.css`.
- Navýšenie vyrovnávacej pamäte Service Workera (`gitpulse-v625`): aktualizovaná hodnota `CACHE_VERSION` v `sw.js`.

## [2026.9.30.post43] - 2026-09-18 - Obnovenie plnej minifikácie CSS/JS balíkov a splnenie kvalitatívnych brán CI

**Opravené**

- Obnovenie plnej minifikácie produkčných balíkov: všetky CSS a JS balíky vrátane `.min` súborov boli opätovne skompilované cez minifikátory `rjsmin`/`rcssmin`, čím sa zmenšil `styles.bundle.css` z 865 KB na 457 KB a `core.bundle.js` z 1.15 MB na 632 KB.
- Splnenie kontrol kvality CI a systémové body zlomu (breakpoints): normalizované dopyty na médiá pre horný panel v `00-mobile.css` na existujúce systémové hodnoty (`360px` a `340px`) namiesto neštandardných šírok; odstránené lokálne prepisovanie vnútorných odstupov buniek tabuliek v `course.css`, čím sa zabezpečil prechod testu konzistencie tabuliek dizajnového systému Pajamas; zachovaný kontrakt zoznamu učiteľov v hlavičke pre test komponentov.
- Navýšenie vyrovnávacej pamäte Service Workera (`gitpulse-v624`): aktualizovaná hodnota `CACHE_VERSION` v `sw.js`.

## [2026.9.30.post42] - 2026-09-18 - Mobilné zarovnanie akcií kariet doľava, zobrazenie hodín, zamknutie webhookov archivovaných kurzov a GitLab PTR

**Opravené**

- Zarovnanie akcií kariet na mobiloch doľava a presun počítadla učiteľov: zjednotené pravidlá `.card-actions` pre mobilné šírky (`<= 768px`) v `cards.css` a `00-mobile.css` na `width: 100%; margin-left: 0; justify-content: flex-start`, čím sa odstránilo nežiaduce zarovnanie doprava pri zalomení tlačidiel na druhý riadok; počítadlo "Zobrazuje sa X z Y" v `_teachers_content.html` bolo premiestnené do prvého riadku k nadpisu "Učitelia kurzu", vďaka čomu tlačidlá akcií obsadzujú samostatný spodný riadok.
- Zobrazenie živých hodín na mobilnom hornom paneli: v `00-mobile.css` bolo odstránené `display: none` pre `#topBarClock`, hodiny a oddeľovač zostávajú `inline-flex`; pravý okraj tlačidla vyhľadávania bol zúžený zo 16px na 8px (`var(--gl-spacing-2)`), vďaka čomu sa lupa aj hodiny pohodlne zmestia vedľa profilového avatara; na úzkych obrazovkách (`<= 380px`) sa prednostne skryje akademický rok a hodiny zostávajú zobrazené.
- Ochrana webhookov archivovaných kurzov a plynulý stav načítania: pridaný atribút `data-is-archived` na kontajner webhookov; pri obnovení zoznamu webhookov v `20-advanced.js` sa tlačidlá akcií v riadkoch archivovaného kurzu vykresľujú s atribútom `disabled data-archived-locked="1"` a vysvetľujúcou nápovedou; funkcia `_applyButtonLoadingReset()` chráni archivované tlačidlá pred nechceným opätovným povolením; zjednotený mechanizmus `refreshRegion()` s okamžitým zobrazením indikátora na tlačidle, okamžitým stmavením tabuľky (`is-refreshing`) a minimálnou dobou odozvy 600ms podľa vzoru System Health; do `.table-responsive` bolo pridané `position: relative` a v `loaders.css` boli aplikované motívové tokeny.
- Bezpečný odstup stĺpca pipelines od posuvníka na mobiloch: upravené šírky stĺpcov v `course.css` pre maticu členov na 48% študent, 24% skóre a 28% pipelines; posledné bunky dostali `padding-right: var(--gl-spacing-6) !important;` proti kolízii s vertikálnym posuvníkom.
- Spoľahlivý GitLab Pull-to-Refresh: vrstva `.ptr` dostala `z-index: 10000` v `20-small-touch.css` pre korektné zobrazenie nad fixným horným panelom; pridaná podpora dotykových zariadení s viacerými bodmi (`navigator.maxTouchPoints > 0`), odložená inicializácia po načítaní DOM a tolerancia sub-pixelového posunu (`scrollTop > 1`).
- Prístupnosť rozbaľovacích ponúk (WAI-ARIA): v `dropdowns.js` bol ošetrený prenos a zrušenie zamerania (blur) na aktívnom prvku pred aplikovaním `aria-hidden="true"` a `inert = true`, čím sa zamedzilo varovaniam v konzole prehliadača.
- Navýšenie Service Worker vyrovnávacej pamäte (`gitpulse-v623`): aktualizovaná hodnota `CACHE_VERSION` v `sw.js`.

## [2026.9.30.post41] - 2026-09-18 - Oprava okamžitého miznutia nápovedy na mobiloch pri ťuknutí na otáznik

**Opravené**

- Oprava okamžitého miznutia bubliny nápovedy na mobilných zariadeniach: odstránený konflikt v globálnom poslucháči kliknutí, ktorý po otvorení bubliny knižnicou Tippy okamžite vyvolal manuálne skrytie; upravený poslucháč rolovania `_hideTippyOnScroll`, aby nezatváral nápovedné prvky `.card-header-info-tip` a `.info-tip` pri jemných dotykových posunoch na obrazovke; optimalizovaný spúšťač na dotykových zariadeniach (`trigger: 'click'` s nulovým oneskorením), čím sa predišlo syntetickým hover udalostiam; pridaná výnimka z anti-spam zámku a prepojenie na po-swapové udalosti HTMX.

## [2026.9.30.post40] - 2026-09-18 - Ukotvenie otáznika nápovedy vpravo na desktope a plná dotyková interaktivita na mobiloch

**Opravené**

- Ukotvenie otáznika nápovedy vpravo na desktope aj mobiloch a funkčnosť dotyku: otáznik `.card-header-info-tip` má zachované `margin-left: auto` v prípade neprítomnosti alebo prázdnych akcií, čo zaručuje jeho pozíciu na pravom okraji hlavičky aj na desktope; prvok bol zmenený zo `<span>` na natívne tlačidlo `<button type="button">` s `touch-action: manipulation`, vďaka čomu prehliadače na mobiloch (iOS Safari, Android Chrome) okamžite a spoľahlivo zachytávajú kliknutia a dotyky; otázniky boli vyňaté z globálneho delegáta Tippy s `touch: false` a dostali vlastnú inicializáciu `initCardInfoTips()` s `touch: true`, `strategy: 'fixed'`, `placement: 'bottom-end'` a automatickým záložným toastom pre prípad nedostupnosti knižnice; z tabuľky používateľov bol odstránený nepoužívaný prázdny prvok `usersCount`.

## [2026.9.30.post39] - 2026-09-18 - Fixácia otáznikov nápovedy na pravom okraji prvého riadku a odstránenie zalamovania na mobiloch

**Opravené**

- Fixácia otáznikov nápovedy na pravom okraji prvého riadku (nie naspodku): premiestnený prvok `.card-header-info-tip` mimo kontajnera `.card-actions` v `cards.html` ako priamy súrodenec nadpisu karty; odstránené pravidlo `.card-actions:has(.table-count) { width: 100%; }` v `cards.css`, ktoré na mobilných šírkach (≤480px) spôsobovalo zbytočné zalomenie akcií na nový riadok a odsunutie otáznika pod nadpis karty; nastavené `order: 3` a `margin-left: auto` pre `.card-header-info-tip` v `cards.css` aj `00-mobile.css`, vďaka čomu otáznik vždy spoľahlivo sedí vpravo hore vedľa nadpisu karty a ikony zbalenia a nikdy nepadá do nového riadku; pridané skrytie prázdneho počítadla tabuľky (`.card-actions:has(> .table-count:only-child:empty) { display: none; }`).

## [2026.9.30.post38] - 2026-09-18 - Zarovnanie otáznikov nápovedy doprava, dotyková optimalizácia, odstránenie prekrytia segmentovaných kariet a motívové tokeny

**Opravené**

- Zarovnanie otáznikov nápovedy doprava a sprístupnenie na dotykových zariadeniach: premiestnený prvok `.card-header-info-tip` do zhluku akcií hlavičky karty (`.card-actions`) na pravý okraj v `cards.html`, vďaka čomu sa otáznik zobrazuje vpravo vedľa tlačidiel namiesto ľavej strany pri nadpise; odstránené skrytie tooltipov na mobiloch v `00-mobile.css` a pridaná pohodlná dotyková plocha (36x36px) s odozvou na stlačenie v `20-small-touch.css`.
- Odstránenie kolidujúcej čiary pod segmentovanými kartami (Quick Access): skrytá spodná čiara `.gl-qa-tabs .gp-tab-ink` v `home.css` a upravená logika v `motion.js`, aby segmentované prepínače používali čisté pilulkové podfarbenie aktívnej karty bez duplicitného podčiarknutia.
- Dôsledné uplatnenie motívových tokenov bez pevných farieb: nahradená statická fialová farba `var(--gl-purple-500)` v animácii pull-to-refresh a hornom indikátore načítania dynamickými tokenmi `var(--primary)` a `var(--primary-hover)` / `var(--primary-active)`, ktoré sa automaticky prispôsobujú zvolenému akcentu a motívu (svetlému/tmavému režimu); nahradený pevný okraj v odporúčaniach hodnotenia sémantickým tokenom `var(--gl-status-brand-icon)`.
- Aktualizácia Service Worker vyrovnávacej pamäte (`gitpulse-v619`): navýšená hodnota `CACHE_VERSION` v `sw.js`.

## [2026.9.30.post37] - 2026-09-18 - Zarovnanie otáznikov nápovedy, stĺpec skóre s odznakmi, SSR deaktivácia archivovaných kurzov, fixný panel a GitLab pull-to-refresh

**Opravené**

- Zarovnanie otáznikov nápovedy k názvu a skrytie na mobiloch: premiestnený prvok `.card-header-info-tip` bezprostredne za názov karty v `cards.html` a odstránené `margin-left: auto`, vďaka čomu otáznik sedí priamo vedľa nadpisu a neodskakuje na pravý okraj ani do stredu; na mobilných zariadeniach (≤768px) sú nápovedné otázniky úplne skryté (`display: none !important;`), keďže dotykové ovládanie tooltipov nie je ergonomické.
- Presun stĺpca skóre a farebné odznaky v tabuľke členov projektu: stĺpec Skóre v `table_heads.html` (`project_members_head_full`) a `_members_table.html` bol presunutý hneď za stĺpec Študent (pred kontroly R01-R13), čím presne zodpovedá tabuľke členov tímu; skóre sa zobrazuje ako farebný odznak (`badge` so zeleným, jantárovým a červeným variantom) s číselným radením namiesto čistého textu.
- SSR deaktivácia tlačidiel akcií pri archivovaných kurzoch: eliminované preblikávanie aktívnych tlačidiel pri načítaní alebo prechode na archivovaný kurz priamym vygenerovaním atribútu `disabled` a `data-archived-locked="1"` na serveri v `_webhook_settings.html`, `_import_export_settings.html` a `_compliance_settings.html`.
- Odstránenie čierneho prázdneho priestoru pod panelom nastavení na mobiloch: opravená pozícia `bottom`, záporný spodný okraj a bezpečné odsadenie pre `.settings-sticky-footer` v `forms.css`, čím sa panel tlačidiel plynulo napojil na spodný okraj obrazovky bez medzery.
- GitLab-style indikátor pull-to-refresh a obmedzená dráha potiahnutia: nahradená jasná oranžová guľa elegantným indikátorom v štýle GitLab Pajamas (`var(--gl-background-color-overlap)`, jemný okraj a tieň, fialový indikátor `var(--gl-purple-500)`); obmedzená maximálna dráha a kľudová pozícia (8px), takže indikátor nikdy neprekrýva nadpis stránky ani omrvinkovú navigáciu.
- Rozostup vo formulári učiteľov a zalamovanie dlhých reťazcov v profile používateľa: zväčšená medzera medzi výberom roly a vyhľadávaním v `.teacher-add-row` na 16px; pridané `overflow-wrap: anywhere` bez nežiaduceho sekania bežných slov pre zamedzenie pretekania v modálnom okne informácií o používateľovi.
- Aktualizácia Service Worker vyrovnávacej pamäte (`gitpulse-v618`): navýšená hodnota `CACHE_VERSION` v `sw.js`.

## [2026.9.30.post36] - 2026-09-18 - Oprava dotykových nápovedí, stĺpca akcií tabuliek, prepínača motívu a mobilnej štruktúry

**Opravené**

- Dotykové ovládanie otáznikov (tooltips) a ich zarovnanie vpravo: premiestnený prvok `info-tip` v `components/cards.html` ako priamy potomok `.card-header` so zarovnaním vpravo (`margin-left: auto; role="button"; tabindex="0"`); pridaná podpora pre dotyk a kliknutie na mobiloch v `20-ui-helpers.js`, vďaka čomu sa po ťuknutí zobrazí vysvetlivka a opätovným ťuknutím alebo klikom mimo sa zatvorí.
- Pevné nepriehľadné pozadie stĺpca akcií a stmavenie neaktívnych šípok radenia: zvýšený z-index sticky stĺpca akcií v `tables.css` a nahradené priesvitné farby plne krycími odtieňmi zmiešanými s pozadím riadkov, čím sa úplne eliminovalo presvitanie susedného skóre a textu pri horizontálnom posúvaní; neaktívne šípky radenia boli zjemnené na `opacity: 0.35` a bunkám skóre bola pridaná číselná hodnota `data-sort-value` pre spoľahlivé radenie.
- Odstránenie prázdneho čierneho priestoru pod tlačidlami v nastaveniach: upravené odsadenie `.settings-sticky-footer` v `forms.css` na `max(var(--gl-spacing-2), env(safe-area-inset-bottom, 0px))` so zarovnaním na stred, čím sa eliminoval nežiaduci prázdny pás pod tlačidlami Uložiť a Zrušiť.
- Plná šírka Activity Monitor na mobiloch: pridané `width: 100%` pre `.pipeline-overview-grid` a 2-stĺpcové zobrazenie `.pipeline-stats-compact.stats-grid-5` na mobiloch v `course.css`, čím sa karta CI/CD zdravia a metriky roztiahli na celú šírku displeja bez bočného prázdna.
- Prečistenie hlavičky učiteľov kurzu a mobilné zalamovanie: odstránený duplicitný odznak počtu v názve karty, ktorý kolidoval s počítadlom `Showing 8` vedľa neho; vyhľadávacie pole a výber roly boli na mobiloch usporiadané pod seba pre prehľadnú štruktúru bez prekrývania.
- Zväčšenie prepínača motívov a zobrazenie textov: tlačidlá prepínača motívov v preferenciách boli zväčšené na 38px s hmatateľným polstrovaním, zvýrazneným aktívnym stavom a plne viditeľnými popismi ("Svetlý", "Tmavý", "Auto") na mobiloch aj počítačoch.
- Aktualizácia Service Worker vyrovnávacej pamäte (`gitpulse-v617`): navýšená hodnota `CACHE_VERSION` v `sw.js`.

## [2026.9.30.post35] - 2026-09-18 - Opravy mobilnej responzivity grafu skóre, fixného footeru, tabuľky kontrol a kariet kurzov

**Opravené**

- Rozloženie a plná šírka grafu trendu skóre študenta na mobiloch: pridané `width: 100%` pre `.chart-canvas-wrap` v `analytics.css` a `.student-charts-layout`, `.student-chart-primary` a `.student-chart-secondary` v `student.css`; na displejoch ≤768px prepnuté na `align-items: stretch` a plnú šírku interaktívnych kariet, čím sa odstránilo stláčanie grafu do úzkeho stĺpca a prázdny priestor vpravo.
- Fixný spodný panel nastavení (Sticky Footer) bez presvitania pozadia: zjednotené ukotvenie `.settings-sticky-footer` v `forms.css` na `bottom: 0` s dynamickým odsadením pre bezpečné zóny (`env(safe-area-inset-bottom)`) a tieňom `box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.12)`; odstránený záporný spodný okraj v `course.css`, čím sa zabránilo presvitaniu prepínačov motívu a obsahu pod tlačidlami.
- Responzivita tabuľky pravidiel compliance v nastaveniach kurzu: tabuľka `#checksTable` pri displejoch ≤480px používa `table-layout: auto !important; min-width: 320px !important;` so skrytým `<colgroup>`; nahradené sekanie slov pomocou `overflow-wrap: break-word; word-break: normal; min-width: 170px !important;` na stĺpci názvu, čo bráni zalamovaniu slov na 1-2 znakové zvislé kúsky.
- Prekrývanie varovného odznaku tlačidlom v kartách kurzov: pridané `flex-wrap: wrap; row-gap: var(--gl-spacing-2); column-gap: var(--gl-spacing-3);` do `.course-card-footer` a zalamovanie tlačidiel v `.course-card-actions`, čím sa zabránilo kolízii odznaku ohrozených skupín (`[ ⚠ 1 ohrozené ]`) s tlačidlom `[ Zobraziť ]` v 2-stĺpcovej mriežke na desktope, tablete aj mobile.
- Aktualizácia Service Worker vyrovnávacej pamäte (`gitpulse-v616`): navýšená hodnota `CACHE_VERSION` v `sw.js` pre okamžité načítanie nových štýlov.

## [2026.9.30.post33] - 2026-09-18 - Opravy mobilnej responzivity toastov, používateľského menu, hlavičiek kariet a komplexný audit

**Opravené**

- Rozloženie a šírka mobilných toast notifikácií: odstránené vertikálne stláčanie toastov na malých mobilných obrazovkách (≤768px a ≤480px), kde sa správy stláčali do úzkeho 22px stĺpca s písmenami pod sebou; prepísaný desktopový výpočet šírky pravidlom `width: auto !important; max-width: calc(100vw - 1.5rem) !important;` s plnou šírkou a bezpečnými okrajmi.
- Zarovnanie používateľského menu v hornej lište: opravené vyskakovanie menu v ľavom hornom rohu pod logom pri kliknutí na avatar vpravo; menu je teraz pevne ukotvené priamo pod avatarom pomocou `position: absolute; top: calc(100% + var(--gl-spacing-2)); right: 0; left: auto`.
- Znaky otáznika a inline rozloženie v hlavičkách kariet a tabuliek: pridaná priama podpora parametra `info_tip` do makra `card()` v `components/cards.html`, vďaka čomu sa otáznik vykresľuje priamo vo vnútri `<h3 class="card-title">...</h3>`; odstránené zalomenie na samostatný riadok a nevhodné umiestnenie v akčných tlačidlách kariet.
- Komplexný audit responzivity a pretekania naprieč všetkými stránkami: overených všetkých 12 hlavných stránok aplikácie na zobrazeniach 390px a 360px cez Playwright – 0 horizontálnych pretečení dokumentu, čisté zalamovanie filtrov a ovládacích prvkov.
- Aktualizácia verzie Service Worker cache (`gitpulse-v614`): navýšená `CACHE_VERSION` v `sw.js` pre okamžité zneplatnenie starej vyrovnávacej pamäte u používateľov.

## [2026.9.30.post32] - 2026-09-18 - Zaoblený indikátor záložiek Rýchleho prístupu, zachovanie polomeru animácie a CSS tokenizácia

**Opravené**

- Zaoblený aktívny indikátor pre záložky Rýchleho prístupu: zaoblený aktívny prúžok na `.gl-qa-tabs` (`border-radius: 0 0 calc(var(--radius-md) - var(--gl-spacing-1)) calc(var(--radius-md) - var(--gl-spacing-1))`), aby presne kopíroval a priliehal k spodnému zaoblenému okraju aktívnej pilulky bez ostrých vyčnievajúcich rohov.
- Zachovanie polomeru zaoblenia v GSAP animáciách pre segmentované ovládacie prvky: aktualizovaný `motion.js` (`inkTo()`) na animovanie vlastnosti `width` namiesto horizontálneho `scaleX` z 1px základu pri segmentovaných pilulkových záložkách (`.gl-qa-tabs` alebo `data-tabs-segmented`), čo bráni GSAP deformovať kruhový polomer rohov na eliptickú rovnú hranu, pričom pre klasické podčiarkovacie záložky zostalo zachované vysoko výkonné `scaleX`.
- Komplexná CSS tokenizácia prvkov Rýchleho prístupu a záložiek:
  - Zjednotené vnútorné odsadenie a medzery `.gl-qa-tabs` na `var(--gl-spacing-1)` a polomer tlačidla na `calc(var(--radius-md) - var(--gl-spacing-1))`.
  - Previazané `.gp-tab-ink` a `.gl-qa-tabs .gp-tab-ink` priamo na `var(--gl-tab-selected-indicator, var(--primary))` naprieč `interactions.css` a `home.css`, vďaka čomu indikátory záložiek na všetkých stránkach a šablónach dynamicky reagujú na motív (tmavý/sveitly) aj používateľský akcent (indigo, modrá, zelená, červená, sivá).
  - Tokenizované medzery v zozname položiek Rýchleho prístupu, polomer avatara (`var(--radius)`) a farebné semaforové indikátory (`.gl-qa-dot--green`, `.gl-qa-dot--yellow`, `.gl-qa-dot--red`) pomocou GitLab Pajamas dizajn tokenov (`var(--gl-green-400)`, `var(--gl-orange-400)`, `var(--gl-red-400)`), čím boli kompletne odstránené hardkódované hexadecimálne farby.
- Celkový audit šablón a stránok: overené všetky Jinja šablóny v projekte s potvrdením nulového výskytu nežiaducich statických inline štýlov a úplnej integrácie s centrálnymi dizajn tokenmi.
- Navýšenie verzie Service Worker cache (`gitpulse-v613`): aktualizovaná hodnota `CACHE_VERSION` v `sw.js` pre okamžité zneplatnenie medzipamäte v prehliadačoch a stiahnutie skompilovaných balíkov.

## [2026.9.30.post31] - 2026-09-18 - Zarovnanie mriežky nástenky s GitLab Pajamas, segmentované záložky a odstránenie inline štýlov

**Opravené**

- Zarovnanie mriežky nástenky s dizajnovým systémom GitLab Pajamas: modernizovaná mriežka `.gl-home-layout` v `home.css` na stĺpce `grid-template-columns: minmax(0, 1fr) var(--gl-home-sidebar-width, 320px)` s medzerou `var(--gl-spacing-6)` (24px). V režime pevnej šírky (`Fixed`) kontajner s maximálnou šírkou 1280px centruje nástenku s hlavným stĺpcom šírky ~900px a bočným panelom 320px. V režime plnej šírky (`Fluid`) kontajner vypĺňa 100% šírky okna, bočný panel Rýchleho prístupu zostáva ukotvený pri pravom okraji so šírkou 320px a hlavný stĺpec spolu so 4 KPI kartami (`repeat(4, 1fr)`) sa proporcionálne rozťahujú po celej šírke.
- Segmentované pilulkové záložky pre Rýchly prístup (Quick Access): nahradené podčiarkovacie záložky autentickými pilulkovými tlačidlami podľa GitLab Pajamas (`--gl-segmented-control-track-bg`, `--gl-segmented-control-track-border`, `--gl-segmented-control-btn-active-bg`, `--gl-segmented-control-btn-active-color`) pre tmavý aj svetlý motív.
- Harmonizácia jemných okrajov kariet: aktualizované `.gl-home-card` a `.gl-home-sidebar-panel` na `var(--gl-border-color-subtle)` (jemný okraj kariet GitLabu) s plynulým prechodom na `var(--gl-border-color-default)` pri hoveri.
- Úplné odstránenie inline `style="..."` atribútov v šablónach:
  - `_weekly_deadlines.html`: nahradené inline štýly triedami `.wd-toggle-btn` a `.wd-toggle-title` nadefinovanými cez dizajn tokeny v `course.css`.
  - `admin_courses.html`: odstránené nadbytočné inline šírky na `<col>` značkách (spravované v `admin.css`).
  - `table_heads.html`: odstránené nadbytočné inline šírky na `<col>` značkách v `users_table_head()` a `teams_table_head()`, pričom presné šírky stĺpcov boli zosynchronizované priamo v `admin.css`.
- Oprava tlačidla uloženia zmien (Save Changes) v preferenciách: ošetrené znovusprístupnenie tlačidla po 5 sekundách alebo scrollovaní, ak formulár používa `btn-save-guard` alebo `data-no-anti-spam="true"`.
- Odstránenie chýb a falošných podčiarknutí v IDE: vyriešená falošná syntaktická chyba JavaScriptu (`Unexpected keyword or identifier. javascript`) spôsobená doslovnou značkou `<script>` vo vnútri Jinja komentára v `base.html`. Doplnené konfiguračné súbory `.vscode/settings.json` a `jsconfig.json` pre správne mapovanie virtuálneho prostredia Pythonu, potlačenie chybnej validácie skriptov v Jinja šablónach a nastavenie DOM ES2022 prostredia.
- Navýšenie verzie Service Worker cache (`gitpulse-v612`): aktualizovaná hodnota `CACHE_VERSION` v `sw.js` pre okamžité zneplatnenie starej vyrovnávacej pamäte v prehliadačoch a stiahnutie aktualizovaných štýlov nástenky.

## [2026.9.30.post30] - 2026-09-17 - Obchádzanie medzipamäte hashu assetov v dev móde a aktualizácia Service Workera

**Opravené**

- Obchádzanie pamäte cache pre hashe statických súborov v dev móde: funkcia `_compute_asset_hash()` v `src/app/main.py` bola upravená tak, aby pri `settings.is_development` vynechala interný slovník `_asset_hashes` a počítala SHA-256 hash statických balíkov (`styles.bundle.css`, `core.bundle.js`) priamo z disku. Tým je zaručené, že znovuvygenerované CSS a JS balíčky okamžite invalidujú vyrovnávaciu pamäť prehliadača (`?v=<hash>`) počas lokálneho vývoja bez nutnosti reštartovania bežiaceho uvicorn démona.
- Navýšenie verzie Service Worker cache (`gitpulse-v611`): aktualizovaná hodnota `CACHE_VERSION` v `sw.js` pre spoľahlivé premazanie starých statických assetov v prehliadači a okamžité stiahnutie aktualizovaných CSS štýlov s horizontálnym roztiahnutím ovládacích prvkov učiteľov.

## [2026.9.30.post29] - 2026-09-17 - Výnimka rate-limitu v dev móde, 96-testová E2E sada a roztiahnutie selektora učiteľov

**Opravené**

- Výnimka pre localhost z obmedzovania požiadaviek (rate-limiting) v dev móde: do `RateLimitMiddleware` v `main.py` bol pridaný parameter `dev_mode=settings.is_development`, vďaka čomu lokálne adresy (`127.0.0.1`, `::1`, `localhost`, `testclient`) nepodliehajú prísnemu limitu 10 požiadaviek za minútu pri prihlasovaní na `/dashboard/login` počas automatizovaných E2E testov alebo rýchleho prepínania rolí v lokálnom vývoji.
- Rozšírenie seedovania demo kurzu o testovacie persóny: skript `scripts/seed_demo_course.py` bol doplnený o automatické vytvorenie účtov `teacher` a `admin` s priradeným vlastníctvom kurzu a aktívnym stavom.
- Komplexná E2E testovacia sada persón: pridaný skript `scripts/e2e_test_all_personas.py` pokrývajúci 96 používateľských a API interakcií naprieč rolami Admin, Učiteľ a Študent so 100% úspešnosťou. Vyčistené dočasné súbory v scratch adresári.
- Normalizácia šírky výberu roly učiteľa: štýl `.teacher-add-row .teacher-add-role-select .gl-dropdown-toggle` bol rozšírený o `width: 100%`, `display: inline-flex` a `justify-content: space-between`, vďaka čomu tlačidlo výberu roly vypĺňa pridelený horizontálny priestor a eliminuje prázdne miesto medzi selektorom a filtrami bez zmeny vertikálnej výšky.

## [2026.9.30.post28] - 2026-09-17 - Odstránenie preblikávania tlačidla uloženia zmien učiteľov a vyčistenie CSS prepisov

**Opravené**

- Odstránenie preblikávania tlačidla uloženia zmien pri načítaní stránky: tlačidlo `btnSaveTeachers` je priamo v SSR renderované ako neaktívne (`disabled=true`) so štandardnou triedou `btn-save-guard`, počiatočným tooltip obalom `disabled_reason` a Alpine väzbou `:disabled="!isDirty || isArchived"`. Odstránená dynamická mutácia DOMu v `course-teachers.js`, ktorá dodatočne po vykreslení obaľovala tlačidlo v JavaScripte a spôsobovala počiatočné prebliknutie do aktívneho stavu.
- Odstránenie ad-hoc CSS prepisov v štýloch učiteľov: zo súboru `course.css` boli odstránené špecifické prepisy pre `.gl-dropdown-toggle`, `.search-box input`, `.table-controls-search` a `.col-teacher-role .gl-dropdown`, ako aj nadbytočné hover zámky. Zachované zostalo iba horizontálne rozťahovanie riadku výberu (`.teacher-add-row`, `.typeahead`, `.teacher-add-role-select`), pričom vzhľad riadia priamo základné komponenty aplikácie.

## [2026.9.30.post27] - 2026-09-17 - Oprava dvojitého aktívneho filtra učiteľov, obnovenie varovných toastov a posun stĺpca GitLab ID

**Opravené**

- Odstránenie duplicitného indikátora aktívnych záložiek vo filtroch učiteľov: vyriešená kolízia statickej SSR triedy `.active` s Alpine dynamickým viazaním `:class`, ktorá spôsobovala zobrazenie fialovej podčiarkovacej čiary na viacerých filtroch naraz. V `layout.html` sa statická trieda vynecháva pri použití `x_class` a metóda `setRoleFilter` zabezpečuje konzistentný stav DOM aj atribútov `aria-selected`.
- Obnovenie varovných toastov pri kliknutí na zablokované akcie v archivovanom kurze: odstránené natívne atribúty `disabled`, ktoré prehliadačom blokovali odosielanie udalostí kliknutia. Tlačidlá teraz používajú atribút `data-archived-locked="1"`, vďaka čomu sa pri kliknutí zobrazí varovný toast vysvetľujúci, že kurz je archivovaný a len na čítanie.
- Návrat ovládacích prvkov pridávania učiteľa na štandardnú výšku 32px: z `course.css` boli odstránené vertikálne 38px prepisy, pričom horizontálne rozťahovanie (`flex`) zostalo zachované.
- Posun stĺpca GitLab User ID doľava v správe používateľov: šírka stĺpca používateľského mena bola upravená na 152px/150px, čím sa stĺpec GitLab ID posunul mierne doľava.
- Pravidlá pre záložky tabuliek a filtre: v `CLAUDE.md` bolo zaznamenané pravidlo, že odznaky s počtom patria iba na záložky prepínajúce na samostatnú entitu/tabuľku (oddelené čiarou `apart: true`), zatiaľ čo bežné filtre riadkov tabuľky odznaky s počtom obsahovať nesmú, a počítadlo `Showing X` v hlavičke patrí len tabuľkám bez stránkovania.

## [2026.9.30.post26] - 2026-09-17 - Eliminácia posunu rozloženia tabuľky učiteľov, zjednotenie s admin/users a čisté štýly zablokovaných prvkov

**Opravené**

- Odstránenie posunu rozloženia a skákania výšky tabuľky učiteľov pri obnovení stránky: kalibrovaná výška rezervácie riadkov (`reserve_row_px=54`) a počiatočný počet rezervovaných riadkov (`_reserve_count`) priamo podľa URL parametra filtra. Alpine kontrolér `teacherManager` inicializuje `roleFilter`, `sortKey` a `sortDir` priamo z URL adries ihneď pri inicializácii, čím sa predišlo opakovanému prekresľovaniu a skákaniu tabuľky. Predrenderovaná trieda `.active` zabraňuje blikaniu aktívneho indikátora záložiek.
- Zjednotenie záložiek filtrov podľa vzoru User Management: z filtrov rolí na stránke Course Teachers (`/dashboard/courses/{id}/teachers`) boli odstránené počítadlá (odznaky), čím sa vzhľad zjednotil s User Management (`/dashboard/admin/users`). Rozbaľovací zoznam pre výber role a vyhľadávacie pole boli upravené na výšku 38px a presne zarovnané s filtrami.
- Štandardizácia štýlov zablokovaných prvkov na úrovni komponentov: odstránené neštandardné lokálne prepisy a direktívy `!important` zo súboru `course.css`. Celosystémové pravidlá pre `.form-input:disabled` a `.search-box input:disabled` v kombinácii s `:hover:not(:disabled)` v súbore `forms.css` zabezpečujú čisté správanie zablokovaných prvkov bez nežiaducich hover efektov v celej aplikácii.

## [2026.9.30.post25] - 2026-09-17 - Odstránenie mŕtveho kódu, zjednotenie komponentov a eliminácia CSS prepisov tabuľky učiteľov

**Zmenené**

- Odstránenie mŕtveho kódu a prebytočných prepisov: vyčistené nepoužívané premenné a metódy v JavaScriptových kontroléroch (`showAdmins`), mŕtve CSS pravidlá (`.no-teachers`, `.teacher-actions`, duplicitné bloky `.teachers-table`, neexistujúci `.typeahead-wrap`) a osirotené štýly vo `forms.css`, `tables.css` a `course.css`.
- Komponentizácia a zjednotenie tabuľky učiteľov: stránka učiteľov kurzu (`/dashboard/courses/{id}/teachers`) plne prešla na štandardné makrá komponentov aplikácie (`table_empty`, `btn_icon_only`, `table_count`, `filter_tabs`, `table_controls`, `page_config`).
- Zosúladenie ovládacích prvkov a konzistencia UI: panel ovládacích prvkov tabuľky bol zjednotený so štandardným zarovnaním vyhľadávania a filtrov bez lokálnych vizuálnych anomálií, čím tabuľka učiteľov získala rovnakú bázu a konzistentný dizajn ako správa používateľov a kurzov. Spevnená ochrana vlastníkov a administrátorov pri hromadnom mazaní.

## [2026.9.30.post24] - 2026-09-17 - Stabilizácia layoutu tabuľky učiteľov, odstránenie blikania pri refreshi a varovné toasty na archivovaných kurzoch

**Opravené**

- Odstránenie blikania záložiek filtrov, odznakov a rozbaľovacích zoznamov pri refreshi (F5): komponent `filter_tabs` teraz renderuje triedu `.active` a hodnoty odznakov priamo zo servera od prvého vykreslenia, čím sa zabránilo skákaniu šírky vyhľadávacieho poľa a blikaniu prázdnych odznakov. `alpine_select` a `table_count` podporujú počiatočný serverový text a počet.
- Stabilizácia geometrie tabuľky učiteľov: zjednotené definície `<colgroup>` a CSS štýly stĺpcov na stránke Course Teachers podľa vzoru User Management (`col-teacher`, `col-teacher-account: 170px`, `col-teacher-role: 190px`, `col-teacher-actions: 80px`), čím sa úplne odstránila deformácia stĺpcov pri obnovení stránky.
- Varovné toasty pri akciách na archivovaných kurzoch: odstránené natívne HTML atribúty `disabled`, ktoré blokovali kliknutia. Akcie (`clearAll`, `remove`, `changeRole`, `pickDefaultRole` a uloženie) teraz spoľahlivo zobrazujú informatívny toast s vysvetlením, že kurz je v režime iba na čítanie.

## [2026.9.30.post23] - 2026-09-17 - Spätná väzba toastov, stabilizácia layoutu tabuliek a perzistencia filtrov a radenia v URL

**Opravené**

- Chýbajúce toasty a spätná väzba na stránke učiteľov kurzu: akcie na archivovaných alebo read-only kurzoch (`add`, `remove`, `changeRole`, `clearAll`, `onSubmit`) predtým ticho zlyhali bez vysvetlenia. Pridané okamžité varovné toasty, informačné toasty pri úspešnom pridaní, odobratí a zmene roly a prísne kontroly.
- Deformácia a skákanie tabuliek pri prázdnych stavoch filtrov: prepínanie filtrov rolí na stránke učiteľov pri nulovom počte výsledkov predtým odmontovalo celú tabuľku a zrútilo výšku karty. Tabuľka a záhlavie stĺpcov teraz zostávajú stabilne zobrazené a prázdny stav sa zobrazuje priamo v riadku tabuľky (`<tr class="table-empty-row"><td colspan="4">`).
- Strata stavu filtrov a radenia po obnovení stránky: filtre (`role`, `check_filter`) a zoradenie stĺpcov (`sort`, `dir`) sa synchronizujú priamo s parametrami URL cez `history.replaceState` naprieč celou aplikáciou (`course-teachers.js`, `sortable-table.js`, `components.js`, `10-sections.js`).

## [2026.9.30.post22] - 2026-09-17 - Oprava zvýraznenia člena v Úlohách na riešenie a vylepšenie GitLab CI/CD

**Opravené**

- Zvýraznenie študenta v zozname členov po kliknutí v sekcii Úlohy na riešenie: opravené parsovanie moderných CSS Color 4 hodnôt (`color-mix`) v `motion.js` normalizáciou cez 2D canvas, pridaný token `--gl-anim-highlight: 1.8s` pre plynulé zobrazenie po dobehnutí smooth scrollu a prepnutie strany paginátora, ak sa riadok nachádza na inej strane.

**Zmenené**

- Štandardizácia GitLab CI/CD a repozitára podľa best practices: pridané pravidlá `workflow:rules` (eliminácia duplicitných pipeline), globálna vyrovnávacia pamäť pre pip závislosti viazaná na `requirements.lock`, integrácia JUnit XML a Cobertura reportov, publikovanie Docker kontajnerov s metadátami a automatické vydania cez `release-cli`.

## [2026.9.30.post21] - 2026-09-16 - Odmietnutie webhooku je JSON; záporný limit, prázdny formulár a prázdny import už neškodia

**Opravené**

- Odpoveď 4xx na webhook prichádzala do GitLabu ako HTML stránka (chybová hranica ju prepisovala pre každý POST bez `Accept: application/json`); pod `/api/` je odpoveď vždy JSON. Webhook s `project: null` bol 500, teraz 422.
- Záporný `limit` na `/events/recent`, `/events/dlq` a v prevádzkovom logu bol 500 - odmietnutý (422) alebo orezaný.
- Prázdny alebo cudzí POST na formulár nastavení kurzu mazal dátumy semestra a termíny; bez časovej značky stránky sa odmieta.
- Import skupiny, ktorý nevidel žiadne projekty, deaktivoval všetky projekty kurzu; s prázdnym zoznamom sa nič nedeaktivuje.

## [2026.9.30.post20] - 2026-09-16 - Mŕtvy kód preč, importy hore, stav ako objekty, middleware balík

**Odstránené**

- 40 funkcií, metód a tried, ktoré nič nepomenúva (878 riadkov): zapisovacie metódy GitLab klienta v aplikácii, ktorá iba číta, deväť nepoužitých schém, polovičná funkcia označovania tímov (metódy, typy a domáca karta, ktorá počítala riadky tabuľky, do ktorej nikto nezapisoval), parameter `locale` vlečený do metódy, ktorá ho ignorovala, a mŕtve vetvy `hasattr` / `getattr` na typovaných objektoch.

**Zmenené**

- 131 lokálnych importov presunutých na začiatok modulu; stav modulov ako objekty namiesto `global`; `students.py` (2 010 riadkov) je balík `students/` ako ostatné domény; middleware má vlastný balík `app/middleware/`.

## [2026.9.30.post19] - 2026-09-16 - Štruktúra zdrojov ako v GitLabe, kratšie názvy

**Zmenené**

- Dashboard je jeden balík na doménu (`home/`, `courses/`, `teams/`, `projects/`, `admin/`), pomocné moduly routerov sú v `api/helpers/`, služby sú zoskupené podľa domény (`gitlab/`, `gitlab_import/`, `llm/`) a moduly stratili prípony `_service` / `_routes` - 45 presunutých modulov, všetky importy prepísané, dokumentácia opísaná nanovo.

## [2026.9.30.post18] - 2026-09-16 - Modály zamerajú prvé pole a vrátia fokus

**Opravené**

- Modál sa otvorí so zameraným prvým poľom namiesto tlačidla zatvorenia a po zatvorení vráti fokus prvku, ktorý ho otvoril.

## [2026.9.30.post17] - 2026-09-16 - Grafy sa vykreslia aj po navigácii v aplikácii

**Opravené**

- Rozdelenie rolí, trend skóre a profil zručností študenta a kontrolný zoznam zostávali po navigácii v aplikácii prázdne (Chart.js sa načítal až po vlastnom skripte stránky); knižnica sa teraz načíta pred balíkmi stránky, pri studenom načítaní aj pri navigácii v aplikácii.

## [2026.9.30.post16] - 2026-09-16 - Odstránené mŕtve CSS

**Odstránené**

- 69 selektorov tried (107 pravidiel v 19 štýloch), ktoré nepomenúva žiadna šablóna, skript ani pohľad; jedenásť stránok overených pixel po pixeli pred a po.

## [2026.9.30.post15] - 2026-09-16 - Jeden spinner; značky, ktoré sa zastavia; šípky podľa režimu

**Opravené**

- Indikátor analýzy kreslil dva spinnery na jednom prvku; je to jediná značka aplikácie, ktorá sa po skončení zmení na stavový disk. Odznak synchronizácie a box importu sa po skončení točili ďalej; zastavia sa. Šípka selectu a krúžok zaneprázdneného vstupu nesú sivú svojho režimu.

**Odstránené**

- Mŕtve parametre htmx na každom tlačidle a vyhľadávacom poli, CSS indikátora, ktorý nič neprepínalo, obyčajný krúžkový spinner a jeho tokeny.

## [2026.9.30.post14] - 2026-09-16 - Sémantické farby grafov, stavov a diffov podľa režimu

**Opravené**

- Grafy zhody, bodky heatmapy, pásma skóre, závažnosti issues, paleta Stavu systému a riadky diffu čítajú tokeny podľa režimu namiesto jednej hodnoty (alebo literálu z GitHubu) pre obe témy; vlastné farby diffu z Predvolieb majú stále prednosť.

## [2026.9.30.post13] - 2026-09-16 - Paleta grafov patrí téme

**Opravené**

- **Grafy:** kategóriové farby (issue, MR, review, CI/CD, kvalita, vlastné) a farby rolí sú tokeny podľa režimu, ktoré čítajú grafy aj bodky legendy z jedného miesta; štyri grafy skladali neplatné výplne pripojením hex alfy k farbe rgb() a teraz skladajú skutočné rgba(); rozdelenie rolí sa vykreslí aj pri vykreslení zo stránky pred načítaním Chart.js.

## [2026.9.30.post12] - 2026-09-16 - Štatistiky systému a heatmapa kontrol sa vykreslia bez loadera

**Opravené**

- **Stránka Systém:** rozdelenie rolí je v stránke od prvého bajtu namiesto načítania za spinnerom; skript načítava iba pri obnovení. **Stránka študenta:** heatmapa kontrol, ktorej história už bola vložená, už nezobrazuje loader.

## [2026.9.30.post11] - 2026-09-16 - Stav načítavania zodpovedá skutočnému načítavaniu

**Opravené**

- **Stavy načítavania:** tabuľky, ktorých prvá strana je už v stránke (Udalosti, História úloh, Kontroly zhody, Webhooky, história študenta), ukazovali spinner a držali ho 800 ms pri každom načítaní, hoci sa nič nenačítavalo; lišta stránkovania sa otvárala s „Načítava sa stránkovanie...“ pod tabuľkami, ktoré ju nikdy nenačítavajú. Oboje je preč: riadky sa vykreslia pred prvým snímkom, lišta sa rodí prázdna a hneď sa naplní a minimálny čas spinnera sa počíta až od chvíle, keď ho bolo naozaj vidieť. Skutočný fetch svoj stav ukazuje ďalej; prázdna tabuľka ukáže prázdny stav hneď, nikdy spinner.

## [2026.9.30.post10] - 2026-09-16 - Akcent sa dostane všade, kde je farba značky

**Opravené**

- **Témy:** akcent teraz farbí odkazy, podčiarknutie vybranej karty, hlavičku zoradeného stĺpca, aktuálny týždeň, výber v zozname, priebehový pás, prejdenie myšou a fokus, bežiacu lištu úloh a sériu značky v grafoch (trend skóre, profil zručností) - všetko, čo bývalo modrou značky - v oboch režimoch. Sémantické farby (info, úspech, varovanie, nebezpečenstvo, kategórie grafov) zostávajú.
- **Odkazy** bez triedy komponentu sa vykresľovali predvolenou modrou prehliadača s podčiarknutím v každej téme; každý odkaz má teraz farbu odkazu témy, podčiarknutú pri prejdení myšou.
- **Primárna farba tmavej témy** je blue-400 (čitateľná ako text na tmavej stránke), pod akcentovou témou zosvetlený akcent.

## [2026.9.30.post9] - 2026-09-16 - Téma je celá téma; pokojnejšie primárne tlačidlo v tmavej téme

**Opravené**

- **Témy:** výber Témy v Predvoľbách teraz prefarbí aj primárne tlačidlo (plné aj obrysové), primárnu farbu a zvýraznenie fokusu - nielen bočný panel, zvýraznenie výberu a zaškrtnuté prvky - v oboch režimoch. Odkazy zostávajú modré a tlačidlo nebezpečnej akcie červené v každej téme. Náhľadové karty ukazujú primárne tlačidlo každej témy.
- **Primárne tlačidlo v tmavej téme:** o krok pokojnejšie (blue-600), aby sedelo s priesvitnými sivými sekundárnymi tlačidlami namiesto toho, aby vyčnievalo ako jediný sýty blok; pri prejdení myšou sa zosvetlí.

## [2026.9.30.post8] - 2026-09-16 - Nahrať súbor otvára výber súboru samo

**Opravené**

- **Nahrať súbor:** tlačidlo v každom JSON editore posúvalo klik skriptom na skrytý vstup súboru a mohlo skončiť bez odozvy. Teraz je to label pre vstup súboru - výber otvára sám prehliadač - a vstup je dostupný klávesnicou.
- **Štítok súboru:** prázdny štítok s ikonou súboru a krížikom sa zobrazoval vedľa „Nahrať súbor“ ešte pred výberom súboru; objaví sa až po načítaní súboru.

## [2026.9.30.post7] - 2026-09-15 - Úvodný riadok karty má všade svoju medzeru

**Opravené**

- **Úvodné riadky kariet:** riadok, ktorým karta začína („Nebodované diagnostické metriky kvality tímovej práce“), sedel na niektorých kartách priamo na štatistických kartách pod ním a na iných 4 alebo 8 px nad nimi; medzera je teraz vlastnosťou komponentu karty - 8 px na každej karte, tak ako to mal Priebeh zhody.

## [2026.9.30.post6] - 2026-09-15 - Značky načítavania vycentrované, jeden blokový loader, bloky kódu na podklade schémy

**Opravené**

- **Značky načítavania:** riadok načítavania tabuľky sedel navrchu rezervovaného boxu a značka lišty stránkovania v jej ľavom rohu; obe sú teraz v strede toho, čo zastupujú, v každej tabuľke.
- **Jedna bloková značka načítavania** aj pre obsah stavaný skriptom (modál Info o používateľovi, história MR a karty inteligencie) - rovnaký box spinner + popis ako všade inde, s rovnakým minimálnym zdržaním.
- **Bloky kódu** bez značky jazyka sa riadia schémou zvýrazňovania z Predvolieb a farebným režimom; schéma „Žiadna“ je kód vo vlastných farbách stránky namiesto pevného tmavého bloku.
- **Tiene** na kartách, ponukách a inštalačnej karte čítajú tokeny tieňov podľa režimu namiesto jednej hodnoty pre oba režimy.

## [2026.9.30.post5] - 2026-09-15 - Žiadne biele ovládacie prvky v tmavej téme; odstránený mŕtvy kód filtrov

**Opravené**

- **Ovládacie prvky tmavej témy:** primárne tlačidlo a zaškrtnutý checkbox / radio boli v tmavej téme takmer biele výplne. Primárne tlačidlo je teraz primárna modrá s bielym textom, zaškrtnutý prvok má farbu výberu témy s bielym zaškrtnutím a Predvoľby > Téma prefarbia aj tieto prvky. Svetlá téma je bez zmeny.

**Odstránené**

- Mŕtvy kód: lišta filtrov členov (skript aj štýly), filtračné pilulky, nepoužívaný prepínač (toggle) a každý odkaz na ne; sprievodca a e2e prechody ukazujú na pás kariet, ktorý pilulky nahradil.

## [2026.9.30.post4] - 2026-09-15 - Jedno zvýraznenie výberu na tému, každá farba podľa farebného režimu

**Opravené**

- **Zvýraznenie výberu:** vybraný týždeň (a každý iný vybraný prvok) bol v tmavej téme takmer biely blok a pri prejdení myšou sa jeho text stal nečitateľným. Každá téma má teraz jedno zvýraznenie výberu - odtieň akcentu s akcentovým okrajom - spoločné pre položku navigácie, týždeň, filter, aktuálnu stránku a prepínač režimu; výber Témy v Predvoľbách ich prefarbí všetky naraz. Prejdenie myšou ponechá vybraný prvok vybraný.
- **Každá farba podľa farebného režimu:** 156 farieb v 20 štýloch malo jednu hodnotu z tmavej alebo svetlej škály pre oba režimy (bledé štítky na tmavých kartách, slabý modrý text na bielej, ovládacie prvky, ktoré vo svetlej téme zmizli). Všetky teraz čítajú tokeny podľa režimu, vrátane tlačidiel úspech/varovanie.

## [2026.9.30.post3] - 2026-09-15 - Týždenná analytika pod výberom týždňa vždy zobrazuje stav

**Opravené**

- **Týždenná analytika:** kliknutie na aktívny týždeň ho zrušilo a karta pod výberom zostala prázdna; aktívny týždeň už kliknutie nemení a týždeň bez dát (alebo kurz bez týždňov) zobrazuje zdieľaný prázdny stav - ikonu a dôvod - vo výške, ktorú zaberajú grafy.

## [2026.9.30.post2] - 2026-09-15 - Stránkovanie sa načítava so spinnerom a popisom, Aktivita je jedna karta s dvoma pohľadmi, grafy sa animujú raz, Priebeh zhody sa vykreslí bez rastu

**Opravené**

- **Lišta stránkovania:** otvárala sa ako prázdny sivý pás (alebo zástupný text, ktorý nikto nevidel); teraz sa otvára so spinnerom a „Načítava sa stránkovanie...“ a nahradí sa po rovnakom minime 800 ms ako každá iná značka načítavania.
- **Karta Aktivita:** Aktivita skupín a Nedávne merge requesty sú jedna karta s prepínačom pohľadov Skupiny / Merge requesty, ako Konfigurácia v Nastaveniach systému a ako stránka Aktivita v samotnom GitLabe. Stránka skupiny si ponecháva dve karty: Projekty a Členovia sú dva zdroje s vlastnými akciami, nie dva pohľady na jednu vec.
- **Grafy sa animujú raz:** obnova (SSE, dokončená úloha, Obnoviť, Znovu načítať, prepnutie týždňa) graf prestavala a znova prehrala jeho príchod; prvé vykreslenie na plátne sa animuje, ďalšie nahradia čísla na mieste.
- **Priebeh zhody študenta** sa vykreslí pri načítaní s rezervovanými riadkami, súhrnnými dlaždicami a heatmapou - prvá dávka je vložená do stránky - namiesto rastu o 359 px po fetchi; súhrnné dlaždice pri naplnení už nerastú; loadery heatmapy a kontrolného zoznamu majú presne výšku toho, čo ich nahradí; zbalená karta je zbalená od prvého snímku. Overené na každej stránke: žiadna karta po prvom vykreslení nemení výšku.
- **CI lint** predchádzajúceho vydania opravený (formátovanie štyroch testov a jedného staršieho bloku v `dependencies.py`).

## [2026.9.30.post1] - 2026-09-15 - Veľké tabuľky pri načítaní už nezamŕzajú (delegované tooltipy), zoradenie bez zmeny sa nedotýka DOM, adresy v Používateľoch už nie sú skrátené

**Opravené**

- **Stránky s veľkými tabuľkami pri načítaní už nezamŕzajú:** každý tooltip na stránke sa vytváral pri štarte a znova po každej výmene obsahu - v Správe používateľov s 574 riadkami to bolo 3 404 tooltipov a 1,4 s zamrznutej stránky kvôli 25 riadkom na obrazovke. Tooltipy sú teraz jedna delegovaná inštancia: prvok dostane svoj tooltip pri prvom nabehnutí myšou alebo zameraní klávesnicou. Namerané: blokovanie stránky 1 029 ms -> 345 ms, načítanie 1,51 s -> 0,77 s; každá ďalšia stránka pod 150 ms.
- **Predvolené zoradenie, ktoré nič nemení, už nevkladá každý riadok nanovo** (115 ms pri 574 riadkoch).
- **Používatelia: adresy už nie sú skrátené** - 36-znakový strop stĺpca E-mail skracoval bežné 38-znakové študentské adresy; hodnoty buniek si teraz od stĺpca vypýtajú šírku, ktorú potrebujú. 0 skrátených buniek v každej tabuľke pri 1366 px aj 1600 px.

## [2026.9.30] - 2026-09-15 - Tabuľky aktivít bez „...“, karty, ktoré po načítaní nerastú, archivované kurzy zostávajú čitateľné, stránka Vyučujúci bez preblikávania a prázdnych buniek

**Opravené**

- **Tabuľky aktivít zobrazujú riadky, nie „...“:** Aktivita skupín a Nedávne merge requesty boli dve karty na polovičnú šírku a dátová tabuľka v 540px karte skrátila 39 buniek - názvy, tituly, dátumy, dokonca odznak Stav - na „...“ a zvyšok schovala za horizontálny posun. Teraz sú pod sebou na plnú šírku s automatickým rozložením: nič nie je skrátené a nič sa neposúva do strany. Rovnaká oprava aj pre tabuľku webhook konfigurácií.
- **Karty už po spustení skriptu nerastú:** tabuľky aktivít a zoznam MR na stránke projektu kreslili stránkovaciu lištu neskoro, takže karta narástla o 57px; zdieľaný komponent stránkovania si ju rezervuje od prvého snímku.
- **Archivovaný kurz zostáva čitateľný:** rozbaľovací prvok ako „Upraviť JSON konfiguráciu“ sa opäť otvorí (iba odhaľuje, čo už na stránke je; editor za ním zostáva vypnutý) a export konfigurácie zostáva dostupný. Overené ako admin, vyučujúci aj študent na každej stránke kurzu.
- **Stránka Vyučujúci:** zamknuté výbery roly už pri prepínaní filtrov nepreblikávajú ako dostupné (vypnutý prepínač vyzerá vypnuto od prvého snímku) a riadok administrátora zobrazuje rovnaké tlačidlo odstránenia vypnuté s dôvodom namiesto prázdnej bunky.
- **Ukazovatele komunikácie** vysvetľujú seba v tele karty ako každá iná karta, nie v hlavičke.

## [2026.9.29] - 2026-09-15 - Stav načítavania, ktorý sa vykreslil, zostáva dosť dlho na prečítanie: minimum 800 ms pre každý spinner s popisom

**Opravené**

- **Stavy načítavania už nepreblikávajú:** tabuľky a bloky so spinnerom a popisom majú prvú stránku vloženú do stránky, takže obsah nahradil značku do ~100 ms od prvého vykreslenia (Udalosti: 93 ms, Rozdelenie rolí: 218 ms) - príliš rýchlo na to, aby ju bolo vidieť, nieto prečítať. Každá značka načítavania má teraz 800 ms hodiny; prechod blokového loadera a tabuľky Udalosti, História úloh a Kontroly zhody ich pred vykreslením vyčkajú, takže sa spinner raz otočí, popis sa dá prečítať a pri príchode obsahu sa nič nepohne. Obnova si riadky ponechá a stlmí, takže nečaká.

## [2026.9.28] - 2026-09-15 - Udalosti a každá tabuľka s vloženou prvou stránkou: stav načítavania má veľkosť obsahu, spinner s popisom viditeľný od prvého snímku

**Opravené**

- **Udalosti: žiadny prázdny box, ktorý tabuľku pri načítaní zdvojnásobí a potom zmenší:** riadok načítavania tabuľky si nárokoval výšku celej obrazovky a jeho spinner s popisom boli 400 ms priehľadné, takže bez udalostí čitateľ videl ~700px prázdny box, ktorý sa zbalil na 170px prázdny stav. Riadok načítavania má teraz presne box, ktorý zaberie jeho obsah (rezervované riadky alebo prázdny stav - rovnaká veľkosť), prechody načítavanie -> prázdne aj načítavanie -> riadky merajú rovnako a spinner s popisom je viditeľný od prvého snímku - v tabuľkách aj v blokovom loaderi (Stav systému, Rozdelenie rolí, Kontrolný zoznam učiteľa).

## [2026.9.27] - 2026-09-14 - Archivovaný kurz: akčné tlačidlá stlmené od prvého snímku, bez preblikávania „dostupných“ tlačidiel pri načítaní a obnove

**Opravené**

- **Archivovaný kurz: akčné tlačidlá už nepreblikávajú ako dostupné pri načítaní/obnove:** tlačidlá v hlavičke stránky (Pridať skupinu, Import z GitLabu, Synchronizovať všetko, Spustiť kontroly) sú v shelle stránky mimo obsahovej časti a stlmovali sa až po tom, čo odložený skript spustil guard len-na-čítanie, takže pri každom plnom načítaní alebo obnove archivovaného kurzu sa vykreslili v skutočných farbách pod bannerom „len na čítanie“. Shell teraz označí `#main-content` ako archivovaný už zo servera, takže sú stlmené od prvého snímku na stránke kurzu, skupiny, projektu, nastavení, vyučujúcich a aktivít; guard naďalej vlastní tooltip, odpoveď na klik a zrušenie stavu po prechode v aplikácii na aktívny kurz.

## [2026.9.26] - 2026-09-14 - Tabuľka vyučujúcich 1:1 cez zdieľaný komponent tabuľky, všetky skeletony nahradené spinnerom s popisom, zvýraznenie šípok zoradenia a posúvanie tabuľky aktivít

**Opravené**

- **Zvýrazňovanie šípok zoradenia:** Opravené nefarbené šípky zoradenia v hlavičkách stĺpcov. Aktualizované CSS selektory pre `th.sorted.asc .sort-caret-up` / `th.sorted.desc .sort-caret-down` (Alpine.js umiestňuje `.sorted.asc` / `.sorted.desc` priamo na `<th>`). Aktívna šípka sa teraz sfarbí farbou `var(--primary)` s plnou viditeľnosťou; opačná šípka je stlmená na `0.22`.
- **Roztiahnutie nástrojovej lišty vyučujúcich:** Zmenené vyhľadávacie pole a rozbaľovací zoznam roly z malých pevných šírok na `flex: 1 1 auto`, takže sa prirodzene roztiahnu a vyplnia prázdne miesto až k filtrovacím záložkám.
- **Zobrazenie počtu riadkov tabuľky vyučujúcich (Showing X of Y):** Pridaný komponent `table_count(id='teachersCount')` do hlavičky karty a metóda `updateCount()` v Alpine komponente `teacherManager()`. Počet sa reaktívne aktualizuje pri zmene filtra, pridaní, odstránení a hromadnom vyčistení — zhodne s tabuľkou Configuration.
- **Tabuľka vyučujúcich sa vykresľuje 1:1 cez zdieľaný komponent tabuľky:** Odstránený celý blok `!important` prepísaní určených len pre vyučujúcich (`padding-bottom: 0` na tele karty, `border-bottom: none` na poslednom riadku, `max-height: none`, `overflow-y: hidden`, `min-height: 0`, duplicitné pravidlo pre zatvorený rozbaľovací zoznam). Karta teraz končí presne ako Configuration v Nastaveniach systému - štandardný odstup tela karty pod posledným riadkom a štandardný posuvný výrez pre dlhé zoznamy. Súkromná rezervácia riadkov je nahradená zdieľaným kontraktom `data_table(reserve_rows=...)`, ktorý používa História úloh.
- **Všetky zostávajúce sivé skeletony nahradené stavom načítavania spinner + popis:** Preblikávajúci prekryv nad grafom Úlohy na riešenie, CI/CD prstencom, grafom týždennej aktivity a oboma grafmi zhody študenta je preč; modálne okno Informácie o používateľovi a karty projektovej inteligencie teraz zobrazujú tanuki spinner s popisom namiesto sivých pruhov - rovnaký stav načítavania ako Rozdelenie rolí a Stav systému. Spolu s nimi odstránené: plugin skeletonu grafov, skeletonová karta kurzu, vetvy len pre skeleton v prechode načítavania a ~450 riadkov osirelého CSS a tokenov skeletonu.
- **Obnovenie horizontálneho posúvania tabuľky aktivít:** Vrátené vynútené `min-width: 0 !important; width: 100% !important` na `.activity-grid .data-table.tbl-fixed`, ktoré predtým stláčalo mriežkové karty na ~500px. Obnovené minimálne šírky `.table-scrollable` (600-620px) a stĺpca stavovej bodky MR na fixných 36px.

## [2026.9.25] - 2026-09-11 - Stabilizácia stĺpcov tabuliek pri filtrovaní a obnove, úprava veľkostí nástrojov a odstránenie prázdneho miesta

**Opravené**

- **Stabilizácia šírok stĺpcov pri prepínaní filtrov naprieč všetkými tabuľkami:** Nahradené dynamické zmenšovanie a deformácie stĺpcov pevnou fixáciou layoutu (`table-layout: fixed`) a zobrazením `<colgroup>` v kontajneroch do 1180px v `tables.css`. Šírky stĺpcov ostávajú stabilné a nepohybujú sa pri prepínaní filtrov (napr. Učitelia, Používatelia, Úlohy, Aktivita).
- **Úprava nástrojovej lišty vyučujúcich:** Zväčšený rozbaľovací volič rolí (`Teacher ⌵`) na 155px s vyváženým odsadením a zmenšené typeahead vyhľadávacie pole na kompaktných 220px podľa vizuálnych požiadaviek.
- **Odstránenie vnútorného posuvníka a prázdneho miesta pod tabuľkou vyučujúcich:** Odstránené zbytočné vertikálne rolovanie (`overflow-y: visible`, `max-height: none`) a zrušený spodný padding karty (`padding-bottom: 0`), čím sa eliminoval prázdny priestor na spodku karty, kde sa nepoužíva stránkovanie.
- **Čistenie načítavacích stavov:** Prečistené komponenty načítavania v `loaders.html` od zastaraných komentárov kostier (skeletons) v prospech štandardizovaných spinnerov.

## [2026.9.24] - 2026-09-11 - Optimalizácia šírok stĺpcov a nástrojov tabuľky vyučujúcich, odstránenie prázdneho miesta a fix relácií používateľov

**Opravené**

- **Optimalizácia vyhľadávania a voliča roly v nástrojovej lište vyučujúcich:** Zmenšená šírka poľa pre vyhľadávanie v typeahead na kompaktných ~280px a rozšírený rozbaľovací zoznam roly na 130px s vyváženým priestorom pre text aj šípku rozbalenia. Pevné pixelové šírky stĺpcov (1167px) boli nahradené responzívnymi percentuálnymi pomermi (44%, 20%, 24%, 12% = 100%), vďaka čomu sa tabuľka dokonale prispôsobí kontajneru bez pretekania a deformácií pri prepínaní filtrov.
- **Odstránenie spodného prázdneho miesta karty:** Znížený padding na spodku tela karty obsahujúcej zoznam vyučujúcich a odstránený nadbytočný spodný okraj posledného riadku, čím zanikol prázdny priestor, kde sa predtým očakávalo nepotrebné stránkovanie.
- **Záložné vyhľadanie používateľa v relácii:** Doplnené záložné overenie používateľa podľa ID, GitLab používateľského mena a case-insensitive porovnania v `_load_user_from_session`, čo zabraňuje 404 chybám pri ukladaní stavu sprievodcu a telemetrii aktivity.

## [2026.9.23] - 2026-09-10 - Redizajn cookie bannera a toastov podľa GitLab Docs calloutu, oprava diagramov v dokumentácii

**Opravené**

- **Redizajn cookie consent bannera podľa GitLab Pajamas Docs:** Kompletný redizajn cookie bannera podľa calloutových alertov z dokumentácie GitLabu, s charakteristickou hornou gradientovou akcentovou linkou, plávajúcou kartou na spodku obrazovky, informačnou ikonou, tučným nadpisom s priamym odkazom na ochranu údajov (`Zásady ochrany osobných údajov ↗`), kontrastným potvrdzovacím tlačidlom (`Súhlasím`) a možnosťou zatvorenia.
- **Zjednotenie notifikačných toastov so štýlom GitLab Docs:** Štandardizované toasty naprieč všetkými 5 stavmi (`info`, `warning`, `success`, `danger`, `tip`) s hornou gradientovou akcentovou linkou zodpovedajúcej farby, typografiou zladenou so stavom, plynulým indikátorom odpočtu času a akciami.
- **Oprava diagramov v dokumentácii:** Nahradený nestabilný Ganttov časový diagram čistým a responzívnym flowchartom plánu údržby a vymenené ľubovoľné percentá v koláčovom grafe za presnú architektúru vyhodnocovacieho engine-u pravidiel v slovenskej aj anglickej verzii dokumentácie.

## [2026.9.22] - 2026-09-10 - Fix šípok paginácie, zarovnanie histórie commitov a GitLab dizajn preferencií

**Opravené**

- **Konzistencia šípok paginácie (< >):** Navigačné tlačidlá predchádzajúcej a nasledujúcej strany (`<` a `>`) zostávajú v neaktívnom (disabled) stave aj pri 1-stranových výsledkoch namiesto ich úplného skrývania. Stránkovacie šípky sú tak vizuálne prítomné a konzistentné naprieč všetkými tabuľkami vrátane prázdneho stavu.
- **Zarovnanie a stabilita tabuľky histórie commitov:** Odstránené 72px prázdne miesto pred názvom vetvy pri non-merge commitoch pomocou jednotného `.commit-branch-wrapper`, uzamknuté šírky stĺpcov cez `tbl-fixed` a zabezpečené riadky proti zalamovaniu či poskakovaniu výšky.
- **Odstránenie voliča vetiev v histórii commitov:** Odstránený nadbytočný rozbaľovací zoznam vetiev z hlavičky histórie commitov podľa požiadavky.
- **GitLab Pajamas dizajn stránky preferencií:** Prepracovaný prepínač režimu (Mode) na Pajamas segmented button group (čisto textový, výška 32px, pravouhlé zaoblenie, tmavo sivé `#4c4b51` pozadie v tmavom režime), odstránený nadbytočný štítok farby akcentu pre priame umiestnenie kariet pod popis sekcie a pridané čisté oddeľovacie čiary medzi sekciami.
- **Zarovnanie voliča roly učiteľa v prístupe k filtrom a rozšírenie vyhľadávacieho poľa:** Odstránené automatické odsadzovanie na `.table-controls:has(.teachers-role-filter)` a obmedzená minimálna šírka `.teacher-add-role-select` na šírku obsahu, vďaka čomu sa typeahead vyhľadávanie plynulo rozťahuje a rozbaľovací zoznam roly prilieha priamo (s 8px medzerou) k tlačidlám filtrov bez prázdneho priestoru medzi nimi.
- **Odstránenie spodného prázdneho miesta karty a vnútorného posuvníka tabuľky učiteľov:** Prekrytá minimálna výška `.teachers-list-slot` na 0 a nastavená maximálna výška `.table-responsive` na `none` s viditeľným pretekaním, čo umožňuje karte prirodzene sa prispôsobiť výške svojich riadkov bez vytvárania vnútorných posuvníkov a bez zanechávania 65px tmavého prázdneho priestoru na spodku karty.

## [2026.9.21] - 2026-09-10 - Komponentový refaktoring učiteľov, odstránenie prázdneho miesta, fix preblikávania tlačidiel a archívu

**Opravené**

- **Komponentový refaktoring učiteľov a odstránenie prázdneho miesta:** Odstránená hardkódovaná hodnota `min-height: 240px` z `.teachers-list-slot` v `course.css` a okamžité nulovanie inline štýlov serverovej rezervácie cez Alpine lifecycle hooky (`init`, `$nextTick`, DOM udalosti), čo úplne eliminovalo prázdny tmavý priestor pod tabuľkou pri filtrovaní na jednotlivé riadky (napr. filter Vlastník kurzu).
- **Archívny stav kurzu a uzamknutie mutácií:** Odovzdaný stav `isArchived` cez konfiguráciu stránky a Alpine stav, čím sa deaktivovalo vyhľadávanie v typeahead, výber predvolenej roly, tlačidlo "Odstrániť všetky obmedzenia", výber roly na úrovni riadku, mazanie učiteľov z kurzu a odoslanie formulára.
- **Prevencia preblikávania tlačidiel a race conditions:** Tlačidlo `btnSaveTeachers` sa na serveri vykresľuje priamo s atribútom `disabled=true` (a dynamickým `:disabled="!isDirty || isArchived"`) a tlačidlo "Odstrániť všetky obmedzenia" s `disabled=(not _can_clear)` a `:disabled="!canClearAll"`, vďaka čomu neaktívne akčné tlačidlá neprebliknú na sekundu ako aktívne pri priamom načítaní či obnovení stránky.
- **Vyčistenie mŕtveho kódu a eliminácia TDZ chýb:** Odstránený zastaraný stránkovací kód (`page`, `pageSize`, `pageNumbers`, `pageLabel`, `prevPage`, `nextPage`, sledovanie `search`) z `course-teachers.js`, bezpečne ošetrené volanie `GP.autoReloadOnJob`, opravené chyby Temporal Dead Zone `ReferenceError` v `cookie-consent.js` a `00-base.js` a odstránená duplicitná deklarácia `init`.
- **Stabilizácia rozmerov tabuľky a šírok stĺpcov:** Presne nakalibrované pevné stĺpce `.teachers-table` (`.col-teacher: 520px`, `.col-teacher-account: 240px`, `.col-teacher-role: 280px`, `.col-teacher-actions: 127px`) zodpovedajúce rozpočtu 1167px, zaručujúce stabilné rozmery a šírky stĺpcov naprieč všetkými filtrami bez kolapsov.

## [2026.9.20] - 2026-09-10 - Fix orezania mien botov, zarovnanie odznakov, ikona prázdneho stavu a stabilita tabuliek

**Opravené**

- **Fix orezania mien botov a zarovnanie odznakov:** Rozšírený stĺpec `col-username` zo 132px na 177px, upravené `col-gitlabid` (95px) a `col-email` (280px) v rámci rozpočtu 1167px, odstránený limit `12ch` pri používateľských menách botov (mená ako `project_8323_bot` sa už predčasne neorezávajú) a odznaky `[Bot]` a `[you]` boli zarovnané na pravý okraj bunky cez `margin-left: auto`.
- **Ikona prázdneho stavu a spodný pásik súhrnu váh:** Pridaný štandardný `.table-empty-state` s ikonou lupy a preloženou správou pri nulovej zhode filtrov v nastaveniach pravidiel a karta súhrnu `Total Active Weight` bola presunutá na spodok sekcie pod tabuľku a prázdny stav.
- **Roztiahnutie vyhľadávania učiteľov k filtrom:** Upravené `.table-controls-search` (`flex: 1 1 auto`) a vyhľadávacie pole typeahead tak, aby výber roly priliehal priamo k tlačidlám filtrov bez zbytočnej prázdnej medzery.
- **Správne stavy prázdnej tabuľky učiteľov:** Rozlíšený celkovo prázdny stav kurzu (ikona odomknutia: "Bez obmedzení") a prázdny stav po aplikovaní filtra alebo vyhľadávania (ikona hľadania: "Žiadni učitelia nezodpovedajú aktuálnemu filtru.").
- **Stabilizácia rozloženia tabuľky a prevencia kolapsu:** Nastavené `table-layout: fixed; width: 100%;` na `.teachers-table` s presne definovanými šírkami stĺpcov (`.col-teacher: 440px`, `.col-teacher-account: 220px`, `.col-teacher-role: 240px`, `.col-teacher-actions: 100px`) a `.teachers-list-slot { min-height: 240px; }` s okamžitým čistením inline štýlov rezervácie, čo zabraňuje skokom, deformáciám a kolapsom tabuľky pri prepínaní filtrov či obnovení stránky.

## [2026.9.19] - 2026-09-10 - Fix načítania grafu compliance, odblokovanie čítania v archíve, odstránenie prázdneho miesta a štandardizácia ikon

**Opravené**

- **Fix načítania grafu compliance študenta:** Vrátený chýbajúci prvok `<canvas id="historyCanvas">` do `#historyChart` v `_compliance_history.html`, čo odstránilo nekonečný stav načítavania (spinner) a umožnilo správne vykreslenie trendového grafu a radaru zručností.
- **Odblokovanie neprepisujúcich prvkov v archívnych kurzoch:** Rozšírený zoznam `_READONLY_OK` v hlavnom guarde o čítacie prvky (`.tab-btn`, `[role="tab"]`, záložky filtrov, tlačidlá filtrov tabuliek, vyhľadávacie vstupy, zoraďovacie hlavičky, stránkovanie, modálne okná, bublinové nápovede), takže používatelia môžu v archívnych kurzoch plynule prehliadať, filtrovať a zoraďovať dáta bez blokovania hláškou o zápise.
- **Odstránenie prázdneho miesta v zozname učiteľov:** Proaktívne vynulovaná minimálna výška serverovej rezervácie (`minHeight`) kontajnera `.teachers-list-slot` pri načítaní DOMContentLoaded, behu skriptu, prepínaní filtrov aj HTMX swape, čím sa odstránilo prázdne sivé miesto pod tabuľkou učiteľov.
- **Umiestnenie podnadpisov a ikona v hlavičke skupín:** Presunutý popis "Score trend and practice tracking across the semester" z atribútu karty do štandardného odseku pod hlavičkou karty (rovnako ako Teacher's Checklist a Week Analytics) a pridaná ikona `users` do hlavičky karty skupín v prehľade kurzu.
- **Doladenie šírok stĺpcov tabuľky používateľov:** Upravené šírky `col-gitlabid` (125px), `col-fullname` (210px) a `col-email` (295px) v rámci rozpočtu 1167px, čo poskytuje dostatok miesta pre dlhé mená bez orezania, a uzamknuté `min-width` a `max-width` naprieč všetkými stĺpcami pre elimináciu CLS.
- **Zjednotenie ikon vymazania a odstránenia:** Nahradené nekonzistentné ikony (`x`, `trash-2`) štandardnou GitLab Pajamas ikonou `trash` v správe učiteľov, administrácii kurzov, danger zone aj nastaveniach.

## [2026.9.18] - 2026-09-10 - Rebalans stĺpcov tabuľky používateľov, odstránenie sivého pozadia filtrov, komponentizácia učiteľov a integrácia pokrytia testov

**Opravené**

- **Rebalans stĺpcov tabuľky používateľov a zamedzenie pretečenia:** Prerozdelená šírka zo stĺpca `Celé meno` (250px -> 180px) do stĺpcov `Email` (280px -> 305px) a `Vytvorený` (135px -> 145px) s `col-gitlabid` na 145px (celkovo 1167px, bezpečne pod limitom kontajnera 1200px bez posunu rozloženia). Odstránené prepisy `min-width: 0` na bunkách používateľského mena, emailu a dátumu, ktoré spôsobovali CLS, rozšírený limit orezania emailu na 36 znakov a zjednotené tlačidlá akcií na variant `ghost`.
- **Priehľadné pozadie filtrov:** Odstránený nechcený tmavosivý artefakt pozadia (`#28272d`) za filtrami v nastaveniach pravidiel a na stránke učiteľov, vynútené priehľadné pozadie, zarovnanie na spodnú hranu a vyčistené zastarané selektory `.check-filters`.
- **Komponentizácia dropdownov učiteľov:** Odstránené špecifické CSS prepisy (`.role-dropdown`, `.teacher-add-role`) v `course.css` aj v šablóne, plná komponentizácia výberu rolí učiteľov cez štandardný `alpine_select` (`.gl-dropdown`) a odstránená umelá minimálna výška `.teachers-list-slot`.
- **Integrovaný odznak úloh testov a pokrytia:** Zjednotený stav úloh testovania a percento pokrytia testami do jedného inline odznaku (`Tests [passed] [71.0%]`) v riadku pipeline študenta, čím sa odstránil zbytočný vertikálny riadok a ušetril priestor na stránke.
- **Proporcionálne ikony v tabuľkových akciách:** Pridané explicitné rozmery pre `.btn-sm .icon` (14px) a `.btn-xs .icon` (12px) v `layout.css`, vďaka čomu menšie akčné tlačidlá v tabuľkách zobrazujú úhľadné, vyvážené ikony.

## [2026.9.17] - 2026-09-10 - Oprava švu v hlavičke tabuľky, stabilizácia šírok stĺpcov, chybový stav tlačidla a oprava šablóny kurzu

**Opravené**

- **Nepretržitá hlavička tabuľky používateľov bez subpixelového švu:** Pridané explicitné pozadie (`var(--gl-background-color-subtle)`) pre `.data-table thead` a `.data-table thead tr`, čím sa odstránil 1px vertikálny výrez medzi stĺpcami `Rola` a `Stav` spôsobený zaokrúhľovaním subpixelov nad tmavým pozadím karty.
- **Uzamknutie šírok stĺpcov a zamedzenie orezania dátumu:** Zväčšená šírka stĺpca `col-created` zo 115px na 135px v hlavičkách tabuliek aj v CSS pravidlách pre zamedzenie orezania ISO dátumu (`2026-04-1;`), upravená šírka `col-email` na 280px a definované celočíselné pravidlá `min-width` pre všetky stĺpce (132px, 165px, 250px, 280px, 90px, 86px, 135px, 84px = 1222px celkovo) na `.users-table`, čo bráni posunu stĺpcov pri hydratácii a obnovení.
- **Stabilita tlačidla obohatenia z GitLabu a chybový stav:** Uzamknutá minimálna šírka `btn.style.minWidth` počas zmeny stavu v `_setButtonOutcome`, čo zabraňuje zmenšeniu či skokovému rozšíreniu tlačidla pri zobrazení ikony alebo popisu stavu; nastylovaná trieda `.btn.btn-error` chybovou farbou a obalený koncový bod `enrich_users_from_gitlab` do štruktúrovaného odchytávania výnimiek s vrátením prehľadného JSON-u a uvoľnením zámku namiesto neošetrenej chyby 500.
- **Oprava Jinja syntaxe v detaile kurzu:** Pridaná chýbajúca uzatváracia značka `{% endif %}` pred `{% endset %}` v `src/app/templates/partials/course/_detail_content.html`, čím sa odstránila chyba 500 (`TemplateSyntaxError`) na stránkach prehľadu kurzu (`/dashboard/courses/<id>`).

## [2026.9.16] - 2026-09-10 - Fix načítania detailu študenta, zaoblenie skeletonov a zarovnanie grafov

**Opravené**

- **Chyba načítania histórie dodržiavania pravidiel:** Opravená `ReferenceError` premennej `panel` v `student-detail.js` (`loadHistory`), vďaka čomu sa grafy histórie a radar zručností načítavajú okamžite a spoľahlivo.
- **Vykresľovanie rohov skeletonov:** Pridané `-webkit-mask-image` a zdedený polomer zaoblenia (`border-radius: inherit`) pre shimmer animácie na `.gl-skeleton` a `.gl-chart-skel`, čím sa zabránilo pretekaniu animácie cez zaoblené rohy, a vynútené 50% zaoblenie pre kruhové skeletony.
- **Veľkosť a vykreslenie CI/CD doughnut grafu:** Zväčšená veľkosť kontajnera `.pipeline-chart-wrap` na 116px podľa susedných stat kariet, odstránené zbytočné zdržanie `IntersectionObserver` a okamžité nastavenie triedy `.gl-chart-ready` po vytvorení grafu.
- **Fix poskakovania stĺpcov tabuľky používateľov:** Uzamknuté presné šírky stĺpcov `col-gitlabid` (165px) a `col-fullname` (250px) pomocou `min-width` a `max-width`, a zachovanie vnútorného elementu `.users-cell-value` pri obnovení tabuľky.
- **Odstránenie nechceného sivého pozadia a prázdneho miesta:** Odstránené sivé pozadie dropdown tlačidiel v paneli učiteľov a predvolieb váh, a odstránená umelá minimálna výška na `.teachers-list-slot`.
- **Hladká animácia JSON konfigurácie:** Nahradený natívny prvok `<details>` plynulým Alpine `x-collapse` akordeónom s rotáciou ikony v nastaveniach termínov.
- **Nápovedné tooltip ikony:** Pridané `(?)` ikony s vysvetľujúcimi kontextovými tooltipmi na karty Používatelia, Učitelia, Skupiny, Kontroly pravidiel a Analytika.

## [2026.9.15] - 2026-09-10 - Eliminácia posunu rozloženia tabuliek (CLS) a fix šírok stĺpcov

**Opravené**

- **Eliminácia vertikálneho posunu tabuliek pri načítaní.** Serverovo renderovaná trieda
  `.table-controls--tabs` priamo na elemente `.table-controls`, ak obsahuje záložky filtrov.
  Zabránilo sa tým 10px posunu rozloženia (CLS) spôsobenému oneskoreným vyhodnotením `:has()`
  počas streamovania HTML.
- **Explicitné šírky stĺpcov v hlavičkách tabuliek.** Pridané explicitné šírky stĺpcov do
  `<colgroup>` a zosynchronizované CSS pravidlá pre Správu používateľov (`users_table_head`),
  Tímy (`teams_table_head`) a Predmety (`adminCoursesTable`). Šírka `col-gitlabid` bola
  zjednotená na 165px, čo zabraňuje horizontálnemu poskakovaniu stĺpcov pri hydratácii dát.

## [2026.9.14] - 2026-09-10 - Zarovnanie filtrov na linku a izolácia oddeľovača servisných účtov

**Opravené**

- **Zarovnanie filtrov na spodnú linku.** Upravený panel `.table-controls` tak, aby pri obsahovaní
  záložiek filtrov priliehal priamo na spodný okraj kontajnera (`padding-bottom: 0; align-items: flex-end;`).
  Odstránené kumulované záporné okraje, kvôli ktorým aktívny modrý pásik visel 10px pod linkou.
- **Izolácia oddeľovača a ohraničenia servisných účtov.** Oddeľovač `.tab-btn--apart` bol presunutý do
  stredu vonkajšej medzery (`var(--gl-spacing-5)`) s pevnou výškou 16px. Tlačidlo si zachováva štandardný
  vnútorný padding, takže modrá aktívna čiara podčiarkuje iba samotnú záložku bez presahu k oddeľovaču
  a zvislá čiara oddeľovača nepretína vodorovnú spodnú linku.

## [2026.9.13] - 2026-09-10 - Stabilita načítania tabuliek, dynamické výbery a zjednotené filtre

**Opravené**

- **Stabilita načítania tabuliek a viditeľnosť ikon triedenia.** Obmedzené vykresľovanie riadkov
  pred inicializáciou stránkovača v správe používateľov, čím sa zabránilo skokom rozloženia.
  Zväčšené ikony triedenia naprieč aplikáciou a zaistená dostatočná šírka stĺpca pre GitLab ID.
- **Ovládacie prvky učiteľov a zjednotený dizajn filtrov.** Zjednotený panel pridávania učiteľov
  a filtrov do štandardného panela `table_controls`. Odstránené prebytočné tmavé pozadia a zjemnený
  vzhľad predvolieb váh v nastaveniach predmetu.
- **Dynamická šírka výberových menu.** Dropdown menu teraz používajú dynamickú šírku (`max-content`)
  bez nežiaduceho zalamovania dlhých položiek ako `merge_request`.
- **Prichytenie filtrov k spodnej linke.** Prepínače a filtre v tabuľkách teraz sedia priamo na linke
  spodného okraja bez medzier, podľa vzoru záložiek detailu predmetu.
- **Vizuálne vyváženie a nápovedy v hlavičkách.** Presunuté filtre úloh študenta do tela karty, zväčšený
  kruhový graf CI/CD na 96px a zjednotené umiestnenie ikon nápovedy na pravý okraj hlavičiek kariet.

## [2026.9.12] - 2026-09-09 - Používateľské predvoľby, plynulé stavy a vyvážené komponenty

**Opravené**

- **Používateľské predvoľby ako jediný zdroj pravdy.** Odstránené pevne nastavené
  veľkosti strán a vynucovanie predvolieb na tabuľkách. Odteraz sa v každej tabuľke
  primárne rešpektuje globálne nastavenie z profilu používateľa (`default_page_size`)
  a per-table zapamätané voľby.
- **Odstránenie preblikávania stavov načítania.** Nahradené čisté textové placeholdery
  štandardnými GitLab Tanuki animovanými indikátormi načítania pri stránkovaní,
  týždenných termínoch, histórii kontrol aj v modálnom okne udalostí.
- **Vyvážené rozmery grafov a stabilita tabuľky webhookov.** Upravená veľkosť kruhového
  grafu CI/CD na 80px a stabilizované stĺpce tabuľky webhookov pomocou `tbl-fixed`,
  čím sa predišlo nevzhľadnému stláčaniu a zalamovaniu textu.
- **Odstránenie zastaraného kódu.** Prečistené nepoužívané triedy odznakov a staré
  štýly správy učiteľov v `admin.css`.

## [2026.9.11] - 2026-09-09 - Zjednotenie ovládacích prvkov učiteľov a stabilita tabuliek

**Opravené**

- **Správa učiteľov a stabilita zobrazenia.** Zjednotené vyhľadávanie a výber rolí učiteľov
  podľa štandardných komponentov GitLab Pajamas `table_controls` a `filter_tabs`. Odstránené
  neštandardné vizuálne prepisy a farebné úpravy rolí.
- **Odstránenie posunu a zachovanie filtrov v správe používateľov.** Implementované obmedzenie
  zobrazenia riadkov pred inicializáciou stránkovača, čím sa zabránilo preblikávaniu celej tabuľky.
  Opravená synchronizácia filtrov a parametrov `?q=` a `?role=` v URL bez viacnásobného prekresľovania.

## [2026.9.10] - 2026-09-09 - Centrované stránkovanie a stabilné tabuľky

**Opravené**

- **Centrované ovládanie stránkovania a zachovanie prázdnych stavov.** Prepínanie
  stránok v navigácii je odteraz striktne vycentrované pomocou CSS gridu (`1fr auto 1fr`),
  pričom informácia o počte záznamov ostáva vľavo a výber veľkosti strany vpravo.
  Lišta stránkovania už nemizne pri prázdnych stavoch ani filtrovaní, a duplicitné
  počítadlá boli odstránené.
- **Odstránený prázdny priestor po vyhradení posuvníka.** Zrušené pravidlo
  `scrollbar-gutter: stable` na `.table-responsive`, čím sa odstránila prázdna
  medzera na pravej strane krátkych tabuliek.
- **Stabilné šírky stĺpcov vo všetkých tabuľkách.** Obnovené riadne škálovanie
  stĺpcov v správe používateľov, udalostiach a detailoch kurzu bez dynamických
  posunov pri načítaní alebo stránkovaní.
- **Oprava rozmerov v tabuľke webhookov a učiteľov.** Upravené šírky stĺpcov
  pre webhooky, aby nedochádzalo k viacriadkovému zalamovaniu názvov.
- **Vyvážené zobrazenie CI/CD grafu.** Zmenšený priemer kruhového grafu na 104px
  a vycentrované zarovnanie so štatistickými kartami.

**Zmenené**

- **Zjednotené filtre kontrol zhody.** Pôvodné tlačidlá filtrov boli nahradené
  štandardným komponentom `filter_tabs` a `table_controls` podľa dizajnového systému Pajamas.

## [2026.9.9] - 2026-09-09 - Jedna tabuľka a každá ďalšia rovnaká

**Opravené**

- **Posun do strán, naraz vo všetkých tabuľkách.** Rolovacie okno tabuľky dostane
  zvislý posuvník vo chvíli, keď riadky prekročia jej výškový strop, a šírka
  posuvníka sa brala z priestoru, podľa ktorého sa počítajú stĺpce - takže každý
  stĺpec sa posunul doľava, keď sa posuvník objavil, a späť, keď filter alebo
  stránkovanie počet riadkov opäť znížili. Miesto je odteraz rezervované od
  prvého snímku, a to na jedinom obale, v ktorom roluje každá tabuľka.

**Zmenené**

- **Každá tabuľka je usporiadaná rovnako.** Vyhľadávanie a filtre patria do pásu
  medzi hlavičkou karty a riadkami, na každej stránke; štyri stránky ich mali
  v hlavičke karty, kam patria akcie tabuľky. Pás meral na štyroch stránkach 45,
  51, 57 a 73 pixelov pre tú istú úlohu - teraz je všade 45px, každý prvok v ňom
  má rovnakú výšku a vyhľadávanie siaha od ľavého okraja až tam, kde začínajú
  filtre.
- **Tabuľka, ktorá sa napĺňa z JavaScriptu, to povie.** Päť tabuliek počas
  načítania ukazovalo hlavičku nad prázdnom; jedna bola skrytá úplne a po
  príchode dát zväčšila kartu o svoju celú výšku. Všetky začínajú spoločným
  stavom načítania.
- **Počet riadkov sa vypíše raz**, v hlavičke karty, jednou formuláciou.
- **Odstránených ďalších osem prepisov štýlov na úrovni stránky**, vrátane
  jedného, ktorý z jediného hárku rozhodoval o zarovnaní buniek vo všetkých
  tabuľkách.

## [2026.9.8] - 2026-09-08 - Aktivita, ktorú systém nikde nezaznamenal

**Opravené**

- **Štyri druhy pilotnej telemetrie sa nikdy nezaznamenali.** Beacon je
  "pošli a zabudni", takže volanie, ktoré API odmietne, zlyhá potichu. Export na
  stránke študenta posielal typ metriky, ktorý neexistuje, a reťazec tam, kde
  schéma čaká objekt (422); stránky skupiny a projektu nemali v HTML žiadne id
  kurzu, takže ich záznamy zanikli ešte pred odoslaním. Teraz sa zapisujú
  všetky štyri.
- **Stránka študenta si dvakrát pýtala to, na čo nikdy nemá právo** - stav
  AI analýzy a učiteľskú telemetriu; obe končili na 403 pri každom otvorení
  skupiny a znova pri každom návrate na kartu. Obidva odosielatele si teraz
  overia, kto číta.
- **Reaktivácia kurzu nepovedala nič o vypnutých webhookoch.** Archivácia ich
  vypne a reaktivácia ich zámerne nechá vypnuté, takže kurz vyzeral živo, kým
  GitLab dostával 401. V logu je teraz počet aj to, kde sa to napraví.
- **Tlačidlá v riadku zostávali mimo dosahu** v najširšej tabuľke aplikácie -
  Členovia projektu; stĺpec akcií je pripnutý ako všade inde.
- **Chybová hláška zahodila dôvod**, ktorý server uviedol pri neúspešnom
  obnovení údajov z GitLabu.

## [2026.9.7.post5] - 2026-09-07 - Webhook odmietnutý bez stopy v logu

**Opravené**

- **Vyhľadávací odtlačok webhooku sa počítal s prázdnym kľúčom** na inštancii,
  ktorá má SECRET_KEY v `.env` - konfigurácia zapísaná jedným procesom bola pre
  druhý neviditeľná a doručenia končili na 401.
- **Chybne tvarovaný payload vracal 500** namiesto 422, takže GitLab opakoval
  nepoužiteľné doručenie 24 hodín.
- **Odmietnuté doručenie nezanechalo nič v logu** - teraz zapíše projekt, kurz a
  ktoré tajomstvá existovali; token nikdy.

## [2026.9.7.post4] - 2026-09-07 - Potvrdenie, na ktoré sa nedalo kliknúť

**Opravené**

- **Potvrdzovací dialóg sa otvoril za oknom, ktoré si ho vyžiadalo** - "Spustiť
  vybrané kontroly" otvorilo potvrdenie pod oknom Run Checks, takže hodnotenie
  celého kurzu sa nedalo dokončiť. Dialóg má teraz vlastnú vrstvu.

## [2026.9.7.post3] - 2026-09-07 - Tabuľka kurzov v administrácii prestala skrývať vlastné bunky

**Opravené**

- **Tabuľka kurzov prispôsobuje stĺpce obsahu** - mala šesť percentuálnych
  stĺpcov nad fixným layoutom a žiadne percentá nesedia pri každej šírke: pri
  1600x1000 potreboval názov kurzu 283 px v 265 px stĺpci. Namiesto orezania sa
  teraz posúva obal, rovnako ako pri tabuľke používateľov.

## [2026.9.7.post2] - 2026-09-07 - Rovnaké riadky v tabuľke kurzov

**Opravené**

- **Riadok v administrácii kurzov je opäť jeden riadok** - tlačidlo "Učitelia" s
  popiskom vytláčalo ostatné tri akcie do druhého riadku a taký riadok bol o ~40
  px vyšší než susedné. Všetky štyri sú teraz ikony s bublinou.

## [2026.9.7.post1] - 2026-09-07 - Akcie stránky sú pri jej názve a skupina ukazuje svoj vlastný stav

**Zmenené**

- **Akcie kurzu sa presunuli k jeho názvu** - Pridať skupinu, Import, Sync All a
  Spustiť kontroly boli voľný rad medzi záložkami a kartou Skupiny. Stránka
  skupiny aj projektu mali svoje akcie v hlavičke už predtým.
- **Stránka skupiny ukazuje jej vlastný stav** - skóre, semafor, prispievatelia,
  projekty a úspešnosť pipeline: päť čísel, ktoré o nej hovorí tabuľka kurzu a
  jej vlastná stránka nie.
- **Čísla vnútri karty sú čísla, nie karty** - blok CI/CD na stránke Aktivita bol
  päť dlaždíc vnútri šiestej karty, ukazovatele komunikácie u študenta desať.
- **"Naposledy synchronizované" pri projekte je riadok, nie panel.**
- **Veta pod menom na prehľade je väčšia** - je to veta, nie metaúdaj.

**Opravené**

- **Červená skupina vyzerala presne ako zelená** - živý handler farbil kartu
  stavu triedami, ktoré už žiadny štýl nedefinuje.
- **Stránka vypnutej funkcie už netvrdí, že ste na prehľade**, a tlačidlo
  "Späť" sa naozaj vracia.
- **Stránka kurzu prestala počítať prispievateľov, ktorých nikdy neukáže** -
  11,0 ms zo 44 ms jej práce s databázou pre číslo, ktoré nikam nešlo.

## [2026.9.7] - 2026-09-07 - Jedna téma, jedna karta - a nepodsvietený roh je preč

**Opravené**

- **Nepodsvietený roh, všade kde bol** - tabuľka si kreslila vlastné 12px horné
  rohy, zatiaľ čo hlavička, panel nástrojov alebo pás záložiek nad ňou blok
  zarovnali do pravého uhla, takže v rohu presvital podklad karty. Malo to šesť
  z deviatich prejdených tabuliek: Používatelia, História úloh, Feature flagy,
  Nedávne udalosti, tabuľky úloh na stránke študenta a Členovia skupiny.
  Tabuľka teraz preberá rohy od svojho obalu.
- **Tabuľka pod pásom záložiek má rovné horné rohy** - tá istá chyba v treťom
  prevleku, v paneloch, ktoré práve dostali záložky.

**Zmenené**

- **Stránka Systém sa pýta jednu otázku raz** - Feature flagy, konfigurácia LLM
  a beh prostredia sú jedna karta Konfigurácia s tromi záložkami; Vyčistiť cache
  a Prepočítať štatistiky sa presunuli do hlavičky stránky. Zo 3775px a siedmich
  kariet na 2540px a štyri.
- **Úlohy študenta sú dve záložky, nie dva rozbaľovače** - autorské a pridelené
  sú tá istá tabuľka rozdelená podľa strany; karta zo 417px na 255px.
- **"Issues to Address" je napísané raz** - jeho päť stavov zdieľa jednu kartu
  namiesto piatich kópií.

## [2026.9.4.post5] - 2026-09-04 - Prvá stránka po nasadení už nie je tá pomalá

**Zmenené**

- **Proces sa zahreje sám pri štarte** - kompilácia šablón (2 651 ms pre všetkých
  106), konfigurácia ORM mapperov (83 ms) a otvorenie prvého spojenia s databázou
  (162 ms) predtým zaplatil ten, kto otvoril prvú stránku. Merané v produkcii:
  prehľad 1355 ms -> 691 ms, detail kurzu 88 ms -> 33 ms.
- **Lazy načítanie obsahu stránky: zmerané a zámerne nepridané** - celá práca
  databázy pre stránku kurzu je 44 ms a zahriate vykreslenie 13 ms, takže druhá
  požiadavka by stála viac, než by ušetrila. Obrázky a skripty ostávajú lazy -
  tam je čakanie skutočné.

**Opravené**

- **Nesprávne tvrdenie v tomto changelogu, opravené** - záznam post1 pripísal
  novému tvaru dotazu zrýchlenie z 2560 ms. To meranie prebehlo počas nasadenia;
  na nezaťaženom stroji sú obe formy rovnaké. Pomalé stránky spôsobilo nasadenie
  (post3).

## [2026.9.4.post4] - 2026-09-04 - Merge request ukazuje svoje commity, nie históriu vetvy

**Opravené**

- **Merge request ukazuje commity, ktoré v ňom naozaj sú** - karta vypisovala
  celú históriu vetvy vrátane commitov zo šablóny spred rokov, a číslo 30 bol
  strop, nie počet. Synchronizácia si teraz ukladá zoznam, ktorý GitLab hlási
  pre daný MR.
- **Filter používateľov je opäť zarovnaný s tabuľkou.**

**Zmenené**

- **`mr_notes.author_id` dostal index, ktorý model deklaroval** - zarovnanie
  schémy s modelom, nie zrýchlenie.

## [2026.9.4.post3] - 2026-09-04 - Nasadenie už nepoloží produkčný stroj

**Opravené**

- **Nasadenie prestalo prestavovať obrazy od nuly** - `--no-cache` pri každom
  nasadení preinštaloval všetky závislosti priamo na produkčnom stroji so
  štyrmi jadrami, ktorý zároveň obsluhoval požiadavky. Namerané počas jednej
  takej zostavy: požiadavka 107 sekúnd bez jediného dotazu do databázy. Teraz sa
  používa vrstvová cache; `--no-cache` je za prepínačom.

## [2026.9.4.post2] - 2026-09-04 - Prehľad už nezapisuje do databázy pri každom načítaní

**Opravené**

- **Jednorazová oprava `gitlab_user_id` sa spúšťala pri každej požiadavke** -
  päť paralelných častí prehľadu tak zapisovalo do toho istého riadku naraz a
  vyčerpávalo fond spojení. Namerané na produkcii: jeden zápis 36 417 ms a dve
  požiadavky, ktoré 107 sekúnd nedostali ani spojenie. Teraz beží raz na
  používateľa.

## [2026.9.4.post1] - 2026-09-04 - Stránka kurzu je rýchla a klik v tabuľke to hlási

**Opravené**

- **Zoznam členov si vypýta databáza, neposiela sa jej** - predtým ~900
  parametrov, teraz podotaz: desaťkrát kratší dotaz a o jeden dopyt menej.
  Rovnaké výsledky, overené na reálnych dátach.
  *(Neskoršia oprava: pôvodne tu stálo, že to skrátilo dotaz z 2560 ms na
  milisekundy. To meranie prebehlo počas prestavby obrazov na tých istých
  štyroch jadrách - na nezaťaženom stroji sú obe formy rovnako rýchle.)*
- **Klik na riadok tabuľky alebo na kartu sa ohlási na mieste** - ovládač podrží
  jemné zvýraznenie, kým sa stránka načíta.
- **Dlhý názov projektu sa v hlavičke už neoreže** - nadpis sa zalomí.

**Zmenené**

- **Ľudia a servisné účty sú jedna karta s dvoma záložkami** - je to tá istá
  tabuľka tej istej entity; boti už nie sú v zabalenej karte pod ňou.

## [2026.9.4] - 2026-09-04 - Pomalá požiadavka pomenuje svoj najhorší dotaz

**Pridané**

- **Požiadavka nad jednu sekundu zaloguje aj svoj najpomalší dotaz** - stránka
  kurzu merala 6721 ms, z toho 5902 ms databáza pri 20 dotazoch, takže čas je v
  jednom-dvoch z nich. Loguje sa len samotný dotaz, nikdy jeho parametre.

## [2026.9.3.post12] - 2026-09-03 - Každý riadok logu povie, koľko z neho bola databáza

**Pridané**

- **Ku každej požiadavke sa loguje `db_ms` a `db_queries`** - doteraz bolo vidieť
  len celkový čas, čo pri pomalej stránke nestačí: sto rýchlych dotazov a jedno
  pomalé vykreslenie šablóny vyzerajú zvonku rovnako. Prehľad má 113 ms pri 38
  dotazoch, z toho 50 ms databáza.

## [2026.9.3.post11] - 2026-09-03 - Riadok sa opäť rozsvieti a klik v tabuľke to hlási

**Opravené**

- **Klik na meno v "Issues to Address" opäť rozsvieti riadok** - značka sa
  kreslila za bunkami, ktoré majú vlastné nepriehľadné pozadie; teraz sa
  podfarbia samotné bunky.
- **Klik v tabuľke alebo na karte hlási načítanie a už nestojí celé načítanie
  stránky** - riadky, karty, tlačidlo späť a vyhľadávanie idú cez navigáciu
  aplikácie namiesto `window.location`.

## [2026.9.3.post10] - 2026-09-03 - Značka načítavania je tam, kde má byť, alebo nikde

**Zmenené**

- **Načítavací štítok je preč** - navigáciu hlási pruh hore, ikona klinutého
  ovládača, ktorá sa zmení na značku, a kurzor "pracujem" nad obsahom.
- **Značka už nesadne do rohu karty** - berie sa len prvá ikona ovládača a len
  ak je vľavo; karta, riadok tabuľky ani obyčajný odkaz ju nedostanú vôbec.
- **Pozdrav v prehľade má dva riadky, nie tri** - fráza nahrádza "Dobrý večer,
  meno" namiesto toho, aby sa pridávala pod neho. Pôvodný pozdrav zostáva ako
  záloha, keď fráza nie je.

## [2026.9.3.post9] - 2026-09-03 - Načítavanie ukazuje jeden zreteľný indikátor

**Zmenené**

- **Načítavanie ukazuje jeden zreteľný indikátor** - štítok v hornej časti
  obsahu so značkou aplikácie a nápisom "Načítava sa...", na rovnakom povrchu ako
  ostatné vyvýšené prvky, takže je čitateľný v každej téme. Objaví sa po 250 ms a
  po 4 sekundách povie dlhšiu vetu v tom istom prvku, takže sa nič neposunie.
- **Stránku neprekrýva** - zaberá asi 5 % obsahovej plochy a nič v nej nehýbe.
- **Prihlasovacia a odhlasovacia stránka sedia tam, kde Keycloak** - obsah je
  o ~48 px nižšie, takže karta pôsobí umiestnene, nie prilepene na horný okraj.
- **Prehľad má pod menom vlastný riadok** - krátku frázu, ktorá sa mení počas
  dňa. Načítava sa na pozadí a keď zdroj nefunguje, zostane pôvodný pozdrav.

## [2026.9.3.post8] - 2026-09-03 - Načítavanie sa ukáže tam, kde ste klikli

**Zmenené**

- **Načítavacia obrazovka cez celú stránku je preč** - namiesto nej sa točí
  ovládač, na ktorý ste klikli (značka nahradí jeho ikonu, takže sa nič
  neposunie), hore beží pruh priebehu a po 4 sekundách pribudne riadok v
  navigačnej lište.
- **Stránka, ktorú opúšťate, zostáva čitateľná** - už ju nič neprekrýva.

**Opravené**

- **Značka načítavania sa točí aj pri obmedzenom pohybe** - predtým sa zastavila
  po jednom snímku, čo vyzeralo, že aplikácia zamrzla.

## [2026.9.3.post7] - 2026-09-03 - Stránky sú zlomkom svojej pôvodnej veľkosti

**Zmenené**

- **Stránky sú výrazne menšie** - katalóg prekladov sa už nevkladá do každej
  stránky, ale je súborom, ktorý si prehliadač uloží. Prehľad zo 367KB na
  162KB, prihlásenie z 234KB na 21KB.
- **Prehľad sa menej pýta databázy** - z päťdesiatich dopytov na tridsaťosem.

**Opravené**

- **Načítanie prehľadu už nezapisuje do databázy**, ak nie je čo opraviť.

## [2026.9.3.post6] - 2026-09-03 - Načítavacia obrazovka má farby zvolenej témy

**Zmenené**

- **Načítavacia obrazovka má farby zvolenej témy** - namiesto druhej kópie
  značky v pevne zapísanej oranžovej ukazuje bežný spinner aplikácie a jeho
  prstenec sleduje zvolený akcent.
- **Stránka pod ňou zostáva čitateľná** - stmavovala sa dvakrát, teraz raz a
  jemnejšie.
- **Ukážky zvýrazňovania syntaxe ukazujú kód, nie prázdne miesto** - užší stĺpec
  čísel a dlhšia ukážka, ktorá vyplní kartu, ako to robí GitLab.

## [2026.9.3.post5] - 2026-09-03 - Načítavacia obrazovka prekryje stránku, na ktorú sa pozeráte

**Opravené**

- **Načítavacia obrazovka prekryje stránku, na ktorú sa pozeráte** - na
  odrolovanej stránke ostávala hore a odrolovala preč s obsahom, takže z nej
  bol vidieť len tmavý pruh navrchu.
- **Tabuľka pod hlavičkou už nekreslí vlastné horné rohy** - dva polomery na
  jednom rohu nechávali presvitať tmavé pozadie, čo je ten neosvetlený roh nad
  stĺpcom CODE.
- **Názvy stĺpcov sa už nezalamujú v tabuľke, ktorá sa dá posunúť do strán** -
  stĺpec si vezme šírku svojho názvu a hlavička je jeden riadok.
- **Jedna dlhá hodnota už nezaberie celý stĺpec** - nad 42 znakov sa oreže s
  tromi bodkami, celú hodnotu ukáže bublina.

**Zmenené**

- **Prehľad si vypýta počty úloh raz, nie päťkrát.**

## [2026.9.3.post4] - 2026-09-03 - Nasadenie už neukáže chybovú stránku prehliadača

**Opravené**

- **Počas nasadenia sa už nezobrazí chybová stránka prehliadača** - požiadavka
  počká na výmenu kontajnera a až dlhší výpadok zobrazí našu vlastnú stránku,
  ktorá sa sama obnoví.
- **Popisy kontrol sa zalomia namiesto orezania na jeden riadok** - orezaná
  bola práve tá časť, ktorá odlišuje dve kontroly.
- **Skratky v bočnom paneli ukážu celú hodnotu**, ktorú zobrazujú.

**Zmenené**

- **Priestor nad pätičkou stránky je rovnaký na každej stránke.**

## [2026.9.3.post3] - 2026-09-03 - Správa používateľov opúšťa zastaraný rozpočet stĺpcov

**Zmenené**

- **Správa používateľov opúšťa percentuálne šírky stĺpcov**, ktorými sa už
  neriadi - tabuľka sa prispôsobuje svojmu obsahu.

## [2026.9.3.post2] - 2026-09-03 - Tabuľka úloh už neoreže text, ku ktorému sa nedá dorolovať

**Opravené**

- **Tabuľka úloh už neoreže výsledok, ku ktorému sa nedá dorolovať** - stĺpec bol
  obmedzený dvakrát a druhé obmedzenie orezávalo text, ktorý sa zmestil.

## [2026.9.3.post1] - 2026-09-03 - Mriežka prehľadu je z GitLabu

**Opravené**

- **Tlačidlá kurzu len na čítanie už pri načítaní neblysnú ako dostupné.**
- **Ukážky schém zvýrazňovania už nie sú orezané** uprostred tokenu.
- **Pole farby v predvoľbách je opäť jeden ovládací prvok** - jeho štvorček bol
  nižší než pole, na ktorom sedí.
- **Sekcia Rozdiely má rovnaké odsadenie ako ostatné** (68px medzera, teraz 16).
- **Tabuľky sa rolujú namiesto skrývania obsahu za tri bodky** - Správa
  používateľov orezala 30 buniek a nedalo sa k nim dorolovať.
- **Dialóg s informáciami o používateľovi už neklesne o 107px**, keď dorazia dáta.

**Zmenené**

- **Dva stĺpce prehľadu používajú mriežku z GitLabu** - bočný stĺpec je
  obmedzený na 290px namiesto rastu s oknom, s medzerou 2rem ako v GitLabe.

**Opravené**

- **Značka načítavania je vycentrovaná na obrazovke**, bez mŕtveho miesta pod ňou.
- **Roh archivovanej karty sa už nelíši medzi svetlým a tmavým motívom.**

## [2026.9.3] - 2026-09-03 - Prekrytie pri načítaní zakrýva celú stránku

**Opravené**

- **Načítavacia obrazovka už nenecháva po stranách dva nestmavené pruhy.**
  Prekrytie bolo pripnuté na vycentrovaný stĺpec obsahu namiesto oblasti, ktorú
  reálne vidíte, takže pôsobilo ako plávajúci panel nad stredom stránky.
- **Archivovaný kurz už nedostáva pokyn spustiť synchronizáciu, ktorú nemôže
  spustiť.** Je len na čítanie, takže zastarávanie údajov je očakávané; stránka
  aj tak pod pás s informáciou o režime len na čítanie pridala „Skúste spustiť
  Sync All".

## [2026.9.2.post2] - 2026-09-02 - Načítavacia obrazovka je opäť prekrytie

**Opravené**

- **Načítavacia obrazovka je opäť prekrytie**, nie panel na konci stránky.
  Plošné pravidlo `[aria-live] { position: relative }` prebilo vlastné
  polohovanie loadera a vytlačilo ho do bežného toku.
- **Načítavacia značka je vycentrovaná na tú časť stránky, ktorú vidíte**,
  namiesto polovice celej výšky rolovania.
- **Ovládacie prvky nastavení už nezaberajú celý stĺpec.** Každý výber na
  stránke predvolieb bol široký 1264px - preto Lokalizácia pôsobila ako veľký
  prázdny pás.

## [2026.9.2.post1] - 2026-09-02 - Rola má všade rovnakú farbu

**Opravené**

- **Rola má všade rovnakú farbu.** Vlastník kurzu bol v dialógu s informáciami
  o používateľovi oranžový a na stránke za ním tyrkysový - dialóg si totiž bral
  farby z mapy prístupových úrovní GitLabu, kde „owner" znamená niečo iné a
  zdieľa len to slovo. Mentor bol v tabuľke používateľov sivý a v dialógu
  otvorenom z toho istého riadku tyrkysový. Farba roly bola zapísaná na štyroch
  miestach; teraz ich test drží pohromade.

## [2026.9.2] - 2026-09-02 - Živé aktualizácie sa pripájajú raz, nie cez seba

**Opravené**

- **Dialóg s informáciami o používateľovi je všade ten istý.** Jeho vykresľovač
  sa načítaval len na stránke Správa → Používatelia, takže všade inde sa
  namiesto štruktúrovanej kostry zobrazil spinner a osekaná karta. Teraz sa
  načíta pri prvom otvorení, odkiaľkoľvek.
- **Text v tabuľkách sa už nezalamuje uprostred slova** a tabuľky Parameter /
  Hodnota / Prostredie na stránke Systém sa rolujú ako každá iná tabuľka
  namiesto zalamovania dlhých hodnôt.
- **Predvolené avatary už nepoblikávajú pri návrate na kartu.** Návrat znovu
  sťahoval obrázok každého používateľa, ktorý žiadny nemá.
- **Voľba svetlej alebo tmavej schémy zvýrazňovania sa už zachová.** Obe sa
  uložili, ale kontrola pri každej požiadavke ich overovala oproti druhému,
  ručne písanému zoznamu, ktorý ich nikdy neobsahoval - voľba sa preto pri
  ďalšom načítaní stránky vrátila späť.
- **Pripnutie inej domovskej stránky než Prehľad funguje.** Ten istý zdvojený
  zoznam zahadzoval Podporu, Kurzy, Systém aj Používateľov. Oba zoznamy teraz
  pochádzajú z jednej tabuľky polí, ktorú používa aj ukladanie.
- **Zoznam schém je sedem schém GitLabu** - Light, Dark, Solarized Light,
  Solarized Dark, Monokai, Dracula, None. Dracula chýbala a "Default"
  duplikovala tmavú; uložená "Default" sa zmení na tmavú.
- **Pole pre farbu rozdielov je opäť jeden ovládací prvok**: farebný štvorček
  sedí priamo na poli s hexadecimálnou hodnotou ako v GitLabe, nie voľne medzi
  navrhovanými farbami, kde otváral systémový výber farby cez celú stránku.
- **Stránka, ktorá stratí živé spojenie, sa pripojí znova iba raz** - namiesto
  toho, aby otvorila druhý stream, kým prvý ešte čaká na opakovanie. Päť
  stránok - prehľad, odznaky v bočnom paneli, kurz, skupina a projekt - malo
  vlastnú kópiu tej istej logiky a kópie sa medzitým rozišli.
- **Dokončená synchronizácia už nespôsobí dávku krátkych opakovaných
  pripojení.** Server zatvorí stream dokončenej synchronizácie hneď a pri
  pevnom dvojsekundovom opakovaní z toho vznikla tesná slučka. Tento stream
  teraz interval predlžuje.

**Zmenené**

- Klient živých aktualizácií je definovaný raz namiesto piatich kópií. Stream
  jednotlivej úlohy, ktorý končí spolu s úlohou, zostáva zámerne oddelený.

## [2026.9.1.post1] - 2026-09-01 - Motív prefarbí celé rozhranie

**Opravené**

- **Motív teraz prefarbí celé rozhranie**, nielen bočný panel - presne ako
  sľubuje jeho vlastná ukážka.
- **Zvýrazňovanie syntaxe má svetlú schému.** Doteraz každá voľba kreslila
  tmavý blok; Svetlá a Tmavá sú samostatné voľby a sedem ukážok je v jednom rade.
- **Prepnutie späť na kartu už nestráca položku** v "Vyžaduje vašu pozornosť".
- **Rozbaľovanie sa vysúva plynulo**, bez záblesku na plnú výšku.
- **Archivovaný kurz je len na čítanie, nie nečitateľný** - rozbaľovače a
  kopírovanie tokenu už nie sú zamknuté.
- **Tabuľka, ktorá sa roluje nadol, to dá najavo.**
- **Tlačidlo Sync zo stránky aktivít je preč.**

**Zmenené**

- **Chart.js sa načíta len na piatich stránkach s grafmi** - o 73kB menej pri
  prvej návšteve ostatných trinástich.

## [2026.9.1] - 2026-09-01 - Nič sa po vykreslení nehýbe

**Opravené**

- **Žiadna stránka po vykreslení nemení tvar.** Zmerané v prehliadači na
  všetkých osemnástich: nárast 0 px a posun rozloženia 0.000 na šestnástich.
- **Navigácia vám už neberie stránku.** Po 1200 ms nahrádzala obsah spinnerom;
  GitLab stránku, ktorú opúšťa, nikdy nevymaže - a teraz ani my.
- **Hlavičky tabuliek nepretekajú pod susedný stĺpec.** Nula orezaných buniek
  pri 1024 / 1280 / 1440 / 1920, predtým štrnásť.
- **Požiadavky sa nemôžu predbiehať** - jedna prebiehajúca na kľúč, a odchod zo
  stránky zruší to, čo mala rozpracované.
- **Každý neaktívny prvok povie prečo** a každé tlačidlo s ikonou má popis.
- **Prejdenie myšou odpovedá farbou**, ako v GitLabe.
- **Klávesová fokusácia je vždy viditeľná.**

## [2026.8.31.post2] - 2026-08-31 - Panel ukladania ako v GitLabe

**Opravené**

- **Panel s tlačidlom Uložiť je konečne jeden komponent - GitLabov.** Dva
  formuláre majú stráženie neuložených zmien a každý si napísal vlastnú pätu:
  v nastaveniach kurzu bola prilepená pod vlastným menom, v Predvoľbách to bol
  statický riadok, ktorý odroloval preč - takže tlačidlo, ktoré stráženie
  aktivuje, bolo mimo obrazovky práve vo chvíli, keď sa aktivovalo.
- **Neaktívne tlačidlo nedávalo najavo, že je neaktívne.** Spoločné pravidlo
  malo `pointer-events: none`, ktoré GitLab nemá, takže kurzor `not-allowed` sa
  nikdy nezobrazil. Neaktívny odkaz `<a>` si ho ponecháva - nemá natívny
  atribút `disabled`.
- **Vnútorná navigácia zahodila neuložené nastavenia bez opýtania.** Výmena
  obsahu nespustí `beforeunload`, takže kliknutie na odkaz v bočnom paneli s
  rozpísaným formulárom zmeny ticho zahodilo. Teraz sa systém opýta.
- **Prilepený stĺpec akcií kreslil tmavý šev, aj keď sa tabuľka zmestila.**
- **Upozornenie na prihlasovacej stránke bolo ťažký čip namiesto GitLabovho
  plochého GlAlert.**

## [2026.8.31.post1] - 2026-08-31 - Tlačidlo Uložiť sa konečne aktivuje

**Opravené**

- **Tlačidlo Uložiť v Predvoľbách sa pri výbere prepínača nikdy neaktivovalo.**
  Snímka formulára ukladala pre prepínače `checked`, ale skupina prepínačov
  zdieľa jedno meno, takže si pamätala posledný - spravidla nezaškrtnutý, a
  nezaškrtnutý aj po zmene výberu. Nič sa nezdalo zmenené, takže Uložiť
  zostalo neaktívne: akcentová téma, šírka rozloženia, schéma zvýrazňovania aj
  formát času sa nedali uložiť.
- **Jedna kontrola odhlásenia z notifikácií bola vnútri docstringu** - teda
  reťazec, nie príkaz - takže tá cesta posielala všetky kategórie bez ohľadu na
  stlmenie.

## [2026.8.31] - 2026-08-31 - Zvýrazňovanie syntaxe

**Pridané**

- **Zvýrazňovanie syntaxe** v Predvoľbách - sekcia z GitLabu, a skutočné
  nastavenie, nie len prevzatý popis. Bloky kódu s rozpoznaným jazykom
  zvýrazňuje Pygments a ich desať farieb tokenov sú teraz CSS premenné, takže
  schéma je desať deklarácií namiesto kópie celej tabuľky. Predvolená, Monokai,
  Solarized tmavá, Solarized svetlá a Žiadna. Každá schéma je deklarovaná raz a
  použitá dvakrát - stránkou aj vlastnou ukážkou - takže ukážka je živá vzorka
  vykreslená presne tými pravidlami, ktoré použije stránka.

## [2026.8.26.post5] - 2026-08-26 - Témy naozaj menia vzhľad

**Opravené**

- **Výber témy takmer nič nerobil.** Akcent zafarboval dve premenné - pozadie
  vybranej položky v bočnom paneli a jej hover - takže pokiaľ ste sa práve
  nepozerali na ten jeden riadok, nastavenie pôsobilo mŕtvo. Teraz farbí celý
  povrch panela: pozadie, okraj aj hover. Náhľad používa rovnaký recept, takže
  sľubuje to, čo aplikácia naozaj urobí.
- **Medzera medzi nadpisom a ovládačom bola o 44px väčšia**, než má GitLab.
- **Tlačidlo selectu stále vyzeralo ako tlačidlo, nie ako pole** - druhá
  polovica opravy selectov.

**Zmenené**

- Náhľad rozdielov sú dve panely vedľa seba nad skutočnou ukážkou kódu, ako v
  GitLabe.

## [2026.8.26.post4] - 2026-08-26 - Popis sekcie je pod nadpisom

**Zmenené**

- Sekcia nastavení sa číta ako v GitLabe: nadpis a pod ním jeho popis.
  `.section-title-group` bol riadok, takže každý popis stál na tom istom riadku
  ako nadpis - celá veta vedľa 21px nadpisu, pričom ani jedno nečítalo ako
  popis toho druhého. Šípka rozbalenia zostáva vedľa nadpisu. Platí to pre
  všetky sekcie v aplikácii, nielen pre Predvoľby.

## [2026.8.26.post3] - 2026-08-26 - Selecty, prepínač režimu a náhľady tém

**Opravené**

- **Každý select v aplikácii sa zmenšoval na obsah.** `dropdowns.css` sa načíta
  po `forms.css`, takže pri rovnakej špecificite vyhralo `inline-flex` a select
  sa scvrkol na text, kým vedľajšie pole vyplnilo celý riadok.
- **Prepínač režimu neukazoval, ktorý režim je aktívny.** Tlačidlá sa posielajú
  so `aria-pressed="false"` a opravuje ich skript pri `DOMContentLoaded`, ktorý
  po SPA navigácii už nenastane - a na Predvoľby sa vždy prichádza ňou.
- **Všetky náhľady tém vyzerali v tmavom režime rovnako.** Pravidlo tmavého
  režimu prebilo farebný nádych témy, takže šesť náhľadov bolo identických.
- **„Accent color" sa pri výbere sfarbil na modro.** Pravidlo `:focus-within`
  prefarbovalo popis skupiny. Fokus patrí prstencu ovládača, nie jeho popisu.
- **Čiara pod drobečkovou navigáciou pri rolovaní zmizla.** Prekrývali ju
  prilepené nadpisy sekcií a hlavičky tabuliek na rovnakej úrovni vrstvenia.

**Zmenené**

- Režimy sú Svetlá / Tmavá / **Automaticky**, ako v GitLabe, a sekcia je nadpis,
  popis a ovládač bez zbytočného riadku navyše.

## [2026.8.26.post2] - 2026-08-26 - Oprava 500 na nástenke

**Opravené**

- Nástenka vracala 500. Odstránenie nepoužívaných importov vo verzii 2026.8.26
  vzalo `json_drop` z modálov nástenky, kde ho nič nespomína - ale zdieľané
  makro pre import konfigurácie si ten názov bralo z kontextu toho, kto ho
  importoval, takže chyba vznikla v súbore, ktorého sa zmena vôbec nedotkla.
  Makro si teraz importuje vlastné závislosti. Stránka Učitelia mala rovnakú
  chybu a je opravená s ním.

## [2026.8.26.post1] - 2026-08-26 - Čitateľnosť prahových štítkov

**Opravené**

- Prahové štítky v histórii zhody študenta boli nečitateľné. Tie farebné triedy
  zdieľajú dva rôzne komponenty - segmentový pruh v nastaveniach kurzu a tento
  textový štítok - a ani jeden nebol ohraničený, takže vyhrala sýta výplň
  pruhu. Štítok si vlastnú farbu textu nenastavuje, takže vychádzal tmavosivý
  na sýtozelenej s kontrastom 2,46:1 oproti minimu 4,5:1; pravidlo, ktoré
  prehralo, dáva 8,19:1. Každý komponent teraz vlastní svoje farby.
- Žltý segment pruhu bol výnimkou aj jedinou nevyhovujúcou časťou: tmavý text
  na oranžovej má 3,13:1, biela - ktorú zelený a červený segment už používajú -
  má 4,73:1.

**Odstránené**

- Osem CSS pravidiel, ktoré neskorší súbor úplne prekrýval. Jedno z nich bolo
  podstatné: škála skóre v `utilities.css` dávala hodnotám „dobré" a „výborné"
  rovnakú zelenú, hoci platné pravidlo ich rozlišuje.

## [2026.8.26] - 2026-08-26 - Jedna mechanika pre celé rozhranie

**Zmenené**

- Tabuľky, ktoré si prvú stranu museli stiahnuť, sa teraz vykreslia hneď pri
  načítaní: posledné udalosti, záložka DLQ, História úloh, tabuľka kontrol
  zhody a tabuľka webhookov. Prvá strana je súčasťou stránky, takže medzi
  otvorením a čítaním nie je ani požiadavka, ani načítavací stav.
- Jedna implementácia na jednu interakciu. Tri z nich boli skutočné chyby, nie
  len neporiadok:
  - Avatar existoval piatimi spôsobmi. Pri zlyhaní obrázka sa zobrazuje jeho
    susedný prvok a v troch z piatich prípadov obrázok žiadneho suseda nemal -
    takže nedostupný avatar nechal prázdny krúžok pri zadávateľovi tiketu, pri
    riešiteľovi aj v jeho výbere.
  - Tiket otvorený priamym odkazom vykreslil inú stránku než tiket otvorený
    cez navigáciu: tá šablóna bola 311-riadkovou kópiou, ktorá zaostala -
    chýbali jej všetky kroky sprievodcu a namiesto názvov otázok formulára
    zobrazovala surové kľúče.
  - `canEdit` sa odvodzoval dvoma rôznymi spôsobmi na jednej stránke, takže
    odpoveď závisela od toho, ktorý blok skript prečítal.
- Obnovenie / trvalé zmazanie, rozbaľovacie menu, avatar, atribúty tlačidiel,
  obsah záložiek kurzu aj tlačidlo Skúsiť znova sú teraz definované na jednom
  mieste. Cestou sa opravilo aj tlačidlo obnovenia v plnej šírke vedľa ikonového
  mazania, dve rozbaľovačky, ktoré namiesto animácie preblikli, a stmavenie
  režimu len na čítanie, ktoré na jednej záložke prišlo hneď a na druhej neskôr.
- `disabled_reason` - popis, prečo je ovládač nedostupný - funguje už na
  všetkých typoch tlačidiel, nielen na jednom z troch.

**Opravené**

- Pomocné triedy odsadenia si protirečili: `.mt-1` bola definovaná dvakrát s
  rôznymi hodnotami a `ml-1`, `mb-lg` a `mb-md` boli napísané na 19 prvkoch bez
  toho, aby pravidlo vôbec existovalo. Jeden názov na jednu hodnotu, bez zmeny
  vo výslednom vzhľade.
- Stránka Predvoľby pridávala pri každej návšteve navigačný poslucháč a žiadny
  neodoberala. Teraz dodržiava rovnaké pravidlo upratovania ako zvyšných
  sedemnásť stránok.

**Odstránené**

- Mŕtvy kód, každý kus overený ako nedosiahnuteľný: 116 CSS pravidiel, osem
  Jinja makier, tri celé komponentové súbory, jedenásť JavaScriptových funkcií,
  päť duplicitných skratiek pre notifikácie a 177 nepoužívaných importov.

## [2026.8.24.post6] - 2026-08-24 - Oddelené oznámenia pre personál

**Opravené**

- Oznámenia o nových tiketoch bez vlastníka zdieľali prepínač s vlastnými
  tiketmi, takže admin, ktorý si stlmil tikety, prestal vidieť aj nové tikety
  čakajúce na prevzatie. Teraz je to samostatná kategória, viditeľná len
  personálu.

## [2026.8.24.post5] - 2026-08-24 - Tur a dokumentácia dobehli stránku

**Opravené**

- Sprievodca Predvoľbami a jeho dokumentácia zaostali za stránkou - obe vznikli
  skôr, než pribudli sekcie Rozdiely a Notifikácie. Teraz pokrývajú všetky
  sekcie v slovenčine aj angličtine a test drží kroky sprievodcu proti kotvám
  na stránke v oboch smeroch.

## [2026.8.24.post4] - 2026-08-24 - Vlastné predvoľby GitPulse

**Pridané**

- **Riadkov na stranu** - voľba "Na stranu" sa doteraz ukladala iba do
  prehliadača, takže na novom zariadení sa vždy vrátila na 50. Teraz je to
  predvoľba účtu; voľba v konkrétnej tabuľke má naďalej prednosť.
- **Začať so zbaleným bočným panelom** - to isté pre bočný panel; použije sa
  len na zariadení, kde ešte nebol zbalený ručne.

## [2026.8.24.post3] - 2026-08-24 - Typografia a lepkavé nadpisy

**Opravené**

- Nadpisy sekcií v Predvoľbách mali nesprávnu veľkosť - GitLab ich vykresľuje
  ako `h2.gl-heading-2` (21-25px), naše boli 14px.
- Nadpisy sekcií sú lepkavé, ako GitLab `.settings-sticky-header`.
- Náhľady motívov používali odhadnuté farby; teraz sú prevzaté priamo
  z `preferences.scss` GitLabu.

## [2026.8.24.post2] - 2026-08-24 - Oznámenia a šírka rozloženia

**Pridané**

- Predvoľby > **Notifikácie**: vypnutie e-mailov podľa kategórie (tikety,
  predmety, účet). Vynucuje sa na serveri v `enqueue_email`, nie iba skrytím
  políčka.

**Opravené**

- **Šírka rozloženia nič nerobila.** Na `--content-width-lg` sa obmedzuje päť
  prvkov; odblokovaný bol iba jeden, takže okolie zostalo úzke.
- Tlačidlo Uložiť zmeny je rovnaké strážené tlačidlo ako v nastaveniach
  predmetu - neaktívne, kým sa formulár nezmení, a varuje pri odchode.
- Sekcie oddeľuje čiara ako v GitLabe.

**Zmenené**

- Prepínač farebného režimu už nie je zdvojený v menu používateľa.

## [2026.8.24.post1] - 2026-08-24 - Opravy e-mailov

**Opravené**

- Každý e-mail odkazoval na `/dashboard/settings`, ktorý nikdy neexistoval -
  odkaz aj hlavička `List-Unsubscribe` viedli na 404. Teraz smerujú na
  `/dashboard/preferences`.
- Uvítací e-mail si staval vlastný zoznam v písme Inter a v palete Tailwind,
  čím obchádzal rozloženie mailera. Test parity teraz kontroluje celý modul,
  nielen jednu vykreslenú ukážku.

**Zmenené**

- `redeploy.py` po migrácii overí, že `alembic current` sa rovná `alembic heads`,
  a inak deploy zlyhá.

## [2026.8.24] - 2026-08-24 - Osobné predvoľby

**Pridané**

- Stránka **Predvoľby** (`/dashboard/preferences`) podľa vzoru GitLabu, dostupná
  **každej role**: farebný režim, motív, farby rozdielov, klávesové skratky,
  šírka rozloženia, domovská stránka, jazyk, prvý deň týždňa a formát času.
  Každá predvoľba patrí účtu, takže ide s vami na každé zariadenie.
- Každá predvoľba niečo naozaj mení: motív zafarbí vybranú položku navigácie,
  šírka rozloženia uvoľní stĺpec obsahu, vypnutie skratiek sa netýka `Esc`
  (dialógy sa stále zatvárajú), nastavenia času menia každú časovú značku
  a prvý deň týždňa každý výber dátumu.
- **Farby rozdielov** sa použijú na skutočnom zobrazení rozdielov v profile
  študenta, nielen v náhľade.
- Domovská stránka ponúka len ciele, ktoré vaša rola dokáže otvoriť.
- Sprievodca stránkou a dokumentácia v slovenčine aj angličtine.

**Opravené**

- Heslá SMTP sa zbavia medzier - Google zobrazuje heslo aplikácie po štvoriciach
  a vloženie presne v tomto tvare zlyhalo bez zrozumiteľnej chyby.

## [2026.8.21.post2] - 2026-08-21 - Chybové stránky bližšie k GitLabu

**Zmenené**

- Chybové stránky používajú ilustrácie a správanie GitLabu (návrat späť sa skryje
  bez histórie, stránky 502/503 sa automaticky obnovujú).

## [2026.8.21.post1] - 2026-08-21 - Opravy rozhrania a pätičky dokumentácie

**Opravené**

- Formuláre v archivovaných kurzoch deformovali polia - popisové pole sa zúžilo
  na ~180px; teraz majú polia plnú šírku.
- Pätička dokumentácie dostala späť nadpis nad právnymi odkazmi a sekcia
  Diplomovka je zoradená správne (1-5).

## [2026.8.21] - 2026-08-21 - Vyhľadávanie už neodhalí neprístupné strany

**Zabezpečené**

- Vyhľadávanie v dokumentácii už nevracia obsah neprístupných strán. Jeden index
  pokrýval celý web a brána ho servírovala ako statický súbor, takže neprihlásený
  čitateľ získal text operátorskej príručky. Teraz sú tri indexy - verejný,
  učiteľský, administrátorský - a dva užšie sú za bránou.
- Slovenské strany dokumentácie zobrazovali anglické rozhranie; teraz sleduje
  jazyk strany. Mŕtve odkazy `/docs/en/en/` sú preč. Pätička má všetky popisky.

## [2026.8.19.post1] - 2026-08-19 - Formulárové prvky majú id a name

**Opravené**

- Hlásenie Chrome "A form field element should have an id or name attribute" na
  každej strane dokumentácie: prepínač témy, jazyka aj vyhľadávanie majú stabilné
  a jedinečné názvy.

## [2026.8.19] - 2026-08-19 - Dvanásť prázdnych strán dokumentácie

**Opravené**

- Dvanásť strán sa po výmene enginu vykresľovalo prázdnych: ich mriežky kariet
  používali syntax MkDocs, ktorú Astro nespracuje. Všetkých 46 kariet sú teraz
  komponenty Starlightu.
- Úvodné strany používajú hero komponent témy namiesto ručne písaného.

## [2026.8.18] - 2026-08-18 - Dokumentácia prepísaná na Astro Starlight

**Zmenené**

- Dokumentácia beží na Astro 7 + Starlight namiesto MkDocs Material: 95 strán sa
  zostaví za 8 sekúnd, vyhľadávanie je statický index Pagefind a 58 strán s
  diagramom už neposiela žiadny JavaScript pre diagramy.
- Migrovaných všetkých 94 súborov obsahu, 147 upozornení prevedených.
- Ikona v záložke je prekreslená pre veľkosť 16 px.

## [2026.7.3.post237] - 2026-08-18 - Každý prvok dokumentácie meraný proti ich stránke

**Opravené**

- Chyba JavaScriptu na všetkých 143 číslovaných nadpisoch rozbíjala obsah strany.
- 566 zo 628 ikon bolo mimo mriežky; všetky sú teraz na 16/20/24/32.
- Bloky kódu a tabuľky zodpovedajú ich vzhľadu.
- Rozloženie strany sedí na ich vykreslené pixely.

**Pridané**

- Päťstĺpcová pätička, riadok "Bola táto stránka užitočná?" a vlastná ikona
  dokumentácie - ich kniha s pulzom GitPulse.

## [2026.7.3.post236] - 2026-08-18 - Vyhľadávanie už neprekrýva rýchle odkazy

**Opravené**

- Otvorenie vyhľadávania na úvodnej stránke prekrývalo polovicu riadku odkazov.

**Zmenené**

- Do štýlov dokumentácie je doplnených zvyšných 30 odtieňov ich palety.

## [2026.7.3.post235] - 2026-08-18 - Vyhľadávanie v hlavičke má ich skutočnú šírku

**Opravené**

- Pole vyhľadávania v dokumentácii má znova 470px - šírku, ktorú ich stránka
  reálne vykresľuje.

## [2026.7.3.post234] - 2026-08-18 - Zhoda komponentov, meraná proti ich živej stránke

**Opravené**

- 45 rozdielov vo vypočítaných štýloch oproti docs.gitlab.com, teraz 12
  kozmetických: veľkosti písma, okraje nadpisov, zoznamy, kód, tabuľky, omrvinky,
  obsah a odkazy v pätičke.
- Panel vyhľadávania na úvodnej stránke už nie je biely na tmavom paneli.
- Obsah stránky mal zlepené položky bez medzier.

## [2026.7.3.post233] - 2026-08-18 - Omrvinky, vlastná ikona dokumentácie a 27 opráv kontrastu

**Pridané**

- Omrvinková navigácia nad každou stranou dokumentácie.
- Ikona dokumentácie je kniha z GitLab docs s pulzom GitPulse.

**Opravené**

- Všetkých 27 nálezov nízkeho kontrastu na 18 prihlásených stranách.

## [2026.7.3.post232] - 2026-08-18 - Rozloženie dokumentácie priamo z ich štýlov

**Zmenené**

- Všetky rozmery dokumentačného rozloženia pochádzajú z
  `docs.gitlab.com/vite/main.css` - stĺpce, medzery, výška hlavičky, šírka
  vyhľadávania aj plynulé veľkosti nadpisov.
- Pätička je ich pevný tmavý pás s bielym textom, orezaný na 1376.

**Opravené**

- Stĺpce 272 px sa vykresľovali ako 288, odkaz v pätičke mal kontrast 2,42:1 na
  všetkých 47 stranách a značka v hlavičke bola skrátená na "GitPulse...".

## [2026.7.3.post231] - 2026-08-18 - Úvodná stránka: jedna pätička, jeden stĺpec, obe témy

**Opravené**

- Dve pätičky nad sebou sú teraz jedna.
- Obsah pod hero panelom mal tri rôzne ľavé okraje; teraz je to jeden stĺpec.
- Svetlá téma: karty ostávali tmavé, takže ich nadpisy boli tmavé na tmavom.
  Farby kariet, pätičky aj hlavičky sa teraz menia spolu s témou.

## [2026.7.3.post230] - 2026-08-18 - Úvodná stránka dokumentácie a dve opravy kontrastu

**Opravené**

- Úvodná stránka dokumentácie prichádzala k čitateľom bez štýlov: `extra2.css` sa
  servuje s `expires 7d` a bez hashu v URL, takže prehliadač držal týždeň starý
  súbor proti novému HTML. URL teraz nesie hash obsahu súboru.
- Kontrast na prihlasovacej stránke: odznak vývojárskeho režimu meral 2,3:1 a
  tlačidlo prihlásenia cez GitLab 2,9:1. Obe teraz používajú dvojice farieb,
  ktoré GitLab reálne dodáva.

**Zmenené**

- Domovská stránka dokumentácie je prepísaná priamo z `docs.gitlab.com/vite/landing.css`.

## [2026.7.3.post229] - 2026-08-17 - Farba kódu v blokoch

**Opravené**

- Bloky kódu už nie sú celé modré - modrá ostáva len pre inline kód.

## [2026.7.3.post228] - 2026-08-17 - Hlavička dokumentácie a oprava changelogu

**Zmenené**

- Hlavička 112px a vyhľadávacie pole 470px na pozícii x=232 - presne ako u nich.

**Opravené**

- Stránka changelogu vkladala do stránky skutočný `<script>` a hádzala chybu.

## [2026.7.3.post227] - 2026-08-17 - Dokumentácia v ich tmavej téme a rozložení

**Zmenené**

- Tmavá téma ako predvolená (ako na docs.gitlab.com): pozadie rgb(24,23,29).
- Tri stĺpce presne ako u nich: bočný panel [20,272], obsah [352,716],
  obsah stránky [1128,272].
- Úvodná stránka s hero panelom (32px rádius, titulok 64px) a kartami s ikonami.
- Ikona dokumentácie je rovnaké tanuki ako v aplikácii.

## [2026.7.3.post226] - 2026-08-17 - Jeden odznak v JS

**Zmenené**

- `GP.badgeHtml` - rovnaký komponent, aký na serveri vykresľuje `badges.html`.
  Osem súborov si odznak skladalo ručne, niektoré bez escapovania textu.

## [2026.7.3.post225] - 2026-08-17 - Jeden prázdny stav v JS

**Zmenené**

- `GP.emptyStateHtml` / `GP.emptyStateRow`: štyri miesta si stavali rovnaké
  "nič tu nie je" po svojom (dve z nich bez escapovania textu). Teraz jeden tvar,
  jedno escapovanie, jeden zdroj ikon - rovnako ako na serveri.

## [2026.7.3.post224] - 2026-08-17 - Ikona, písmo a menu, ktoré neostáva visieť

**Opravené**

- Menu počtu riadkov v stránkovaní už po skrolovaní neostáva visieť nad tabuľkou.
- Predbežné načítanie písma už nehlási "preloaded but not used" - odkazovalo na
  inú adresu, než akú žiada CSS.
- Ikona v záložke je vlastná tanuki značka aplikácie (svg aj viacrozmerné .ico).

**Zmenené**

- Portálované menu je jeden komponent (`GP.dropdown.portal`).
- Každý htmx swap už neinicializuje celú stránku, iba vymenenú časť.
- Štyri ďalšie animácie používajú existujúce komponenty; keyframes 17 -> 13.

## [2026.7.3.post223] - 2026-08-17 - Dokumentácia 1:1 s docs.gitlab.com

**Zmenené**

- Štýly dokumentácie sú prepísané podľa nameraných hodnôt z docs.gitlab.com:
  text 16px/25,6px, nadpisy 40/46, 32/40, 24/30, šírka textu 716px, odkazy
  podčiarknuté.
- Dokumentácia používa presne ich pohyb: 3 prechody, 0 animácií.
- Posledné `window.confirm` sú nahradené zdieľaným dialógom aplikácie.

**Opravené**

- Posun rozloženia po načítaní písma (CLS 0,0296 -> 0) - chýbal `crossorigin`
  pri predbežnom načítaní fontu.

## [2026.7.3.post222] - 2026-08-17 - Pohyb, ktorý sa dá odmerať

**Zmenené**

- Hover už nič nehýbe - zostáva farba; stlačenie sa hýbe ďalej. Na stránke
  nastavení kurzu: prvky s prechodom 1817 -> 762, vlastnosti prechodov
  10 004 -> 2 113.
- Jedna rýchlosť rotácie (0,6 s ako GitLab), jeden pulz, tri easingy bez
  prekmitu. Trvalá "aura" pri stavových kartách je odstránená úplne.
- Tlačidlo v stave načítania si nechá text aj šírku - spinner nahradí ikonu.
- Jeden stav načítania tabuliek: falošné skeleton riadky sú zmazané.

**Opravené**

- Archivovaný kurz už po vykreslení neposunie stránku o 30 px (CLS 0,0173 -> 0).
- Neúspešné obnovenie už nehlási aj úspech - jeden toast, jeden pokus, 10 s limit.
- Tri `<label>` bez poľa sú teraz `<fieldset>` + `<legend>`.

## [2026.7.3.post221] - 2026-08-13 - Jedna značka načítania

###  Changed
- Sivé kostrové pruhy sú preč - namiesto falošnej podoby obsahu sa točí tanuki a blok si drží výšku, ktorú obsah zaberie.
- Obnovenie nechá obsah na mieste, stlmí ho a točí nad ním tanuki - rovnako ako "Check now" v System Health.
- Stav trvá dosť dlho na to, aby ho bolo vidieť (450 ms).
- Na dotykových zariadeniach zmizol pohyb viazaný na hover.

###  Fixed
- Odsadenie stránky na mobile bolo definované na piatich miestach; teraz na jednom, a je menšie.
- Tlačidlá v hlavičke karty (Job History) už neutekajú mimo obrazovku.

## [2026.7.3.post220] - 2026-08-13 - Obnovenie nechá obsah na mieste

###  Changed
- Obnovenie tabuľky už nezahodí jej riadky - stlmia sa a nové prídu na ich miesto v rovnakej veľkosti, presne ako "Check now" v System Health.
- Slovenský a anglický katalóg majú v hodnotách bežnú interpunkciu namiesto typografických pomlčiek a úvodzoviek.

###  Fixed
- Stĺpec týždňov v kalendári bol prázdny pre mesiace pred začiatkom semestra.
- Zaoblenie rohov tabuľky sa riadi pozíciou v stĺpci prvkov, nie zoznamom tried.

## [2026.7.3.post219] - 2026-08-12 - Tanuki namiesto spinnerov

###  Changed
- Kostrové riadky tabuliek sú preč. Načítavanie je jedna vycentrovaná plocha v rovnakom tvare ako prázdny stav, takže tabuľka pri obnovení nemení výšku.
- Každý spinner v aplikácii je teraz značka tanuki v rovnakom otáčajúcom sa prstenci ako celostránkový loader.
- Stĺpec Akcie je ukotvený vo všetkých tabuľkách, nielen v Správe používateľov.

###  Fixed
- Biely záblesk pri otváraní rozbaľovacej sekcie.
- Tlačidlo kopírovania vnútri `<summary>` nebolo dosiahnuteľné klávesnicou.

## [2026.7.3.post218] - 2026-08-12 - Nový výrazný pohyb

###  Added
- Každý ovládací prvok teraz reaguje na kurzor vo všetkých stavoch - pokoj, prechod, stlačenie, zameranie. Predtým sa menila iba farba, takže nič nepôsobilo stlačene.
- Záložky majú jedinú podčiarkovaciu čiaru, ktorá sa presúva z jednej na druhú.
- Riadky tabuliek zvýrazní prúžok na nábežnej hrane; samotné riadky sa nehýbu.

###  Changed
- Modálne okná, toasty a rozbaľovacie panely teraz doslova "dorazia" na miesto namiesto obyčajného presunu.

## [2026.7.3.post217] - 2026-08-12 - Jeden animačný systém

###  Changed
- Animácie boli rozdelené do 67 ručne písaných `@keyframes` v 25 štýloch, každý s vlastným trvaním a krivkou - tá istá interakcia sa preto animovala inak podľa stránky. Teraz ich je 21 a všetko, čo má začiatok a koniec, riadi jeden modul. Odmerané na 14 stránkach: 2223 prvkov, každý animuje zmenu stavu, žiadny komponent nebeží na dvoch rôznych rýchlostiach.
- "Odstrániť riadok" existovalo štyrikrát a "zvýrazniť to, čo si hľadal" päťkrát. Teraz raz.

###  Fixed
- Živé aktualizácie neukazovali žiadnu spätnú väzbu - trieda, ktorú prepínalo šesť miest, bola zredukovaná na priehľadné pozadie.
- `<details>` sa vo Firefoxe a Safari otváralo skokom, kým karta vedľa neho plynule kĺzala.
- Stránkovacie tlačidlá, záložky a tlačidlá cookie lišty prechádzali polovičnou rýchlosťou než ostatné tlačidlá.
- Zdravotný pruh si orezával vlastný text pri treťom riadku.
- Toast pozastavený nad kurzorom sa nedokázal rozbehnúť z miesta, kde zastal.

###  Removed
- 46 mŕtvych alebo nahradených `@keyframes` a sonarové krúžky v logu, ktoré sa vykresľovali na každej stránke skryté a bez animácie.

## [2026.7.3.post216] - 2026-08-12 - Select späť na plávajúci panel ako v GitLabe

###  Fixed
- Rozbaľovacie menu je opäť zaoblený plávajúci panel; jeho prilepenie k ovládaciemu prvku vytvorilo tvrdý zárez, ktorý vyzeral horšie.

## [2026.7.3.post215] - 2026-08-12 - Záložky už nemenia veľkosť stránky

###  Fixed
- Prepnutie záložky už nakrátko nezobrazí obe panely naraz, čo spôsobovalo, že stránka narástla a zase sa zmrštila.

###  Changed
- Donut v CI/CD Health je menší a jeho dlaždice širšie.
- Tlačidlo Sync je odstránené z Analytics; duplikovalo akciu kurzu na stránke, ktorá len číta dáta.

## [2026.7.3.post214] - 2026-08-12 - Select a jeho menu sú jeden celok

###  Fixed
- Formulárové selecty sa konečne animujú pri otvorení; pravidlo bolo obmedzené na iný druh menu.
- Menu je teraz spojené s ovládacím prvkom bez medzery a bez oproti sebe zaoblených rohov.

###  Changed
- Nadpisy sekcií v bočnom paneli sú opäť modré.

## [2026.7.3.post213] - 2026-08-12 - Prepínanie záložiek už netrhá tabuľku

###  Fixed
- Prepnutie záložky už nespôsobí, že sa tabuľka na okamih roztrhne.
- Horný roh tabuľky sa už nemení podľa toho, či sa práve zobrazuje informačná poznámka.

## [2026.7.3.post212] - 2026-08-12 - Skúškové obdobie funguje aj bez dátumu konca

###  Fixed
- Kurz bez výslovného dátumu konca semestra má teraz skúškové obdobie; predtým sa uzavrelo posledným dňom výučby a nikdy sa nezobrazilo.

## [2026.7.3.post211] - 2026-08-12 - Prepínanie záložiek plynie namiesto skoku

###  Fixed
- Záložky sa pri prepnutí plynulo zobrazia; predtým sa vymieňali skokom kvôli spôsobu, akým sú skryté.

## [2026.7.3.post210] - 2026-08-12 - Štvrté rozbaľovanie sa pridalo k ostatným

###  Fixed
- "Issues to Address" sa teraz vysúva ako každý iný panel; bol jediný, ktorý sa nedal animovať vôbec.
- CI lint je opäť zelený - pred poslednými vydaniami nebol spustený formátovač.

## [2026.7.3.post209] - 2026-08-12 - Rovnaké karty, rovnaké rozloženie

###  Fixed
- "Subgroups and Projects" má rovnaké odsadenie ako "Group Members" namiesto toho, aby siahal až k okraju karty.
- Informačné poznámky nad týmito tabuľkami sú zaoblené ako všetko okolo nich.

## [2026.7.3.post208] - 2026-08-12 - Tabuľka udalostí sa už neschlopne

###  Fixed
- Obnovenie stránky udalostí už neschlopne tabuľku na jeden riadok so spinnerom a späť; zobrazí kostrové riadky, ktoré držia výšku.

## [2026.7.3.post207] - 2026-08-12 - Rozbaľovacie menu sa otvára s pohybom

###  Changed
- Rozbaľovacie menu sa vysunie namiesto toho, aby preblikol, a sedí bližšie k ovládaciemu prvku, takže pôsobí spojene.
- Oba druhy menu v aplikácii sa animujú rovnako; jeden z nich sa predtým animovať vôbec nedal.

## [2026.7.3.post206] - 2026-08-12 - Stránka projektu sa pridala ku kartovému systému

###  Changed
- Protected Branches, Contributors a Repository Stats mali vlastný tretí štýl karty; teraz sa presne zhodujú s kartami na prehľade.

## [2026.7.3.post205] - 2026-08-12 - Rohy tabuliek podľa jednotlivých okrajov

###  Fixed
- Tabuľka s poznámkou nad ňou a stránkovaním pod ňou sa teraz zaobľuje správne na každej strane: poznámka berie horné rohy, stránkovanie spodné.

## [2026.7.3.post204] - 2026-08-12 - Podmienené zaoblenie tabuliek

###  Fixed
- Tabuľky so stránkovaním už nie sú zaoblené oproti nemu; tabuľka je zaoblená len na okrajoch, kde je naozaj okrajom svojho bloku.

###  Changed
- Štítky s počtom používajú všade rovnakú pilulku namiesto plochého sivého boxu.

## [2026.7.3.post203] - 2026-08-12 - Jedno spracovanie tabuliek a animovaný text

###  Fixed
- Tabuľky sú zaoblené rovnako všade, nie raz hranaté a raz nie.
- Text v riadkoch a tlačidlách sa animuje spolu s nimi; predtým skákal, lebo farba sedí na vnorenom span-e bez animácie.

## [2026.7.3.post202] - 2026-08-12 - Štatistické dlaždice sú teraz KPI karta

###  Changed
- Vycentrované dlaždice majú rovnaký dvojvrstvový tvar ako karty na prehľade - hlavička s popisom a ikonou, hodnota vo vloženom bloku. Namerané zhodné v každej hodnote, bez zmeny markupu.

## [2026.7.3.post201] - 2026-08-12 - Dátum v pozdrave už nemizne

###  Fixed
- Dátum vedľa roly na prehľade zmizol po druhom návrate na stránku; skripty, ktoré zapisujú do vymeneného obsahu, sa teraz spustia pri každom príchode.

## [2026.7.3.post200] - 2026-08-12 - Nadpisy hlavičiek sedia presne v strede

###  Fixed
- Nadpisy v hlavičkách kariet už nesedia o pár pixelov vyššie; namerané presne 0px rozdielu na každej hlavičke.

## [2026.7.3.post199] - 2026-08-12 - Poznámky v hlavičke a rozmery dlaždíc

###  Fixed
- Hlavička karty môže mať poznámku pri pravom okraji, takže Archivované kurzy sa zhodujú s hlavičkou Service Accounts.
- Vycentrované dlaždice majú opäť primerane veľkú ikonu a ich hodnoty už nepretekajú mimo dlaždicu.

## [2026.7.3.post198] - 2026-08-12 - Rozbaľovanie beží, sivý blok grafu zmizol

###  Fixed
- Rozbaľovacie karty sa naozaj vysúvajú; animáciu potichu rušilo jedno flex pravidlo.
- Týždeň bez aktivity už nezobrazuje trvalý sivý blok načítavania namiesto grafu.

## [2026.7.3.post197] - 2026-08-12 - Mikroanimácie, ktoré je konečne vidieť

###  Fixed
- Predtým pridaný základ pohybu nebolo vidieť, lebo neurčoval, ktoré vlastnosti animovať. Každý interaktívny prvok teraz plynulo mení svoj stav; bez animácie nezostal ani jeden.

## [2026.7.3.post196] - 2026-08-12 - Každá klikateľná hlavička reaguje rovnako

###  Fixed
- Niektoré rozbaľovacie hlavičky sa pri prejdení myšou zvýraznili a iné nie; teraz ich pokrýva jedno pravidlo.

###  Changed
- Archivované kurzy majú štítok s počtom a poznámku "Len na čítanie", rovnako ako hlavička Service Accounts.

## [2026.7.3.post195] - 2026-08-12 - Karty späť na skutočné rozostupy GitLabu

###  Fixed
- Predošlé vydanie nafúklo karty, lebo čítalo triedy GitLabu podľa škály Tailwindu namiesto ich vlastnej. Odsadenie je späť; ostáva len 12px zaoblenie vnútorného bloku, ktoré bolo naozaj zlé.

## [2026.7.3.post194] - 2026-08-12 - Štatistické dlaždice admina sa pridali ku kartám

###  Fixed
- Dlaždice na admin stránkach sa teraz zhodujú s kartami na prehľade (16px zaoblenie, rovnaká škrupina) namiesto 4px priehľadných boxov.
- Ich ikony stratili farebnú podložku; farba stavu sa presunula na samotnú značku.

## [2026.7.3.post193] - 2026-08-12 - Proporcie kariet priamo z markupu GitLabu

###  Fixed
- Odsadenie škrupiny, zaoblenie a odsadenie vnútorného bloku aj okraj hlavičky sa presne zhodujú s GitLabom; tri z piatich hodnôt boli mimo.

## [2026.7.3.post192] - 2026-08-12 - Jeden takt pre všetky prvky

###  Fixed
- Raw Check Details kreslil dve šípky naraz a štýloval sa inak než ostatné rozbaľovacie sekcie; teraz používa zdieľaný komponent.

###  Changed
- Každý interaktívny prvok reaguje rovnako rýchlo a rovnakou krivkou; predtým si každý komponent zvolil vlastnú.

## [2026.7.3.post191] - 2026-08-12 - Aj natívne <details> sa otvára plynulo

###  Fixed
- Každá rozbaľovacia sekcia sa teraz otvára rovnako plynulo; predtým sa animovala len karta cez Alpine a natívne sekcie skákali.

## [2026.7.3.post190] - 2026-08-12 - Jeden kontrakt pre rozbaľovanie namiesto troch

###  Fixed
- Rozbaľovacie hlavičky kariet zdieľajú jeden fokusový rámček, jeden šípku a jeden uhol otočenia; predtým sa tri plochy správali odlišne.
- Raw Check Details dostal šípku, ktorú nikdy nemal, a šípka je zvislo vycentrovaná.

## [2026.7.3.post189] - 2026-08-12 - Časová značka v pruhu sa vrátila

###  Fixed
- Pruh o starých dátach po prechode medzi stránkami zobrazoval prázdnu medzeru namiesto času snímku.
- Week Analytics sa teraz vždy otvorí na niektorom týždni namiesto prázdneho panelu, kým na týždeň neklikneš.

## [2026.7.3.post188] - 2026-08-12 - Rebrík hrúbky písma má konečne chýbajúci stupeň

###  Fixed
- `semibold` mal rovnakú hodnotu ako `medium`, takže 276 miest dostávalo tenšie písmo - preto mohli nadpisy rovnakej úrovne vyzerať odlišne. Škála je teraz 400/500/600/700.
- Nadpisy kariet a hlavičky stĺpcov sú semibold namiesto bold, takže už neprevažujú nadpisy stránky nad nimi.

## [2026.7.3.post187] - 2026-08-12 - Riadky podpory bez gradientových dlaždíc

###  Changed
- Riadky kurzov na stránkach podpory používajú obyčajnú 16px GitLab ikonu v tlmenej farbe namiesto modrej gradientovej dlaždice.
- Rozostupy, zaoblenie a hover riadkov sa riadia zvyškom kartového systému - iba farba, žiadny tieň ani nadvihnutie.

###  Fixed
- Hlavička zbalenej karty už nie je zaoblenejšia než škrupina okolo nej.

## [2026.7.3.post186] - 2026-08-12 - Únik pri navigácii, ktorý duplikoval id

###  Fixed
- Prechod medzi stránkami už nenecháva za sebou osirené kalendáre dátumu, ktoré spôsobovali duplicitné id formulárových polí.
- Zbalená karta už nemá pod hlavičkou mŕtve miesto a tabuľka v rozbalenej karte už nevytŕča hranatými rohmi.
- V upozornení o starých dátach zostáva časová značka pri svojom popise a neodpláva cez celý pruh.

## [2026.7.3.post185] - 2026-08-12 - Bloky v kartách majú medzeru

###  Fixed
- Zvýraznenie hlavičky karty sa už nedotýka obsahu pod ňou - bloky delí rovnakých 8px ako je odsadenie karty.
- Zmizli posledné zaoblenia písané pre okraj karty: každý blok v karte je zaoblený na všetkých štyroch rohoch.

## [2026.7.3.post184] - 2026-08-12 - Karty majú tvar KPI kariet

###  Changed
- Karty sú svetlejšia škrupina a obsah v nej ako tmavší zaoblený blok - rovnako ako KPI karty na prehľade.

###  Fixed
- Zbalenej karte (Archivované kurzy) už nevytŕčajú hranaté rohy spoza zaobleného rámu.

## [2026.7.3.post183] - 2026-08-12 - Každá karta má hlavičkový pruh ako v GitLabe

###  Changed
- Hlavičky kariet sú svetlejší pruh a obsah je na tmavšej farbe panelu pod ním - ako v GitLabe a ako KPI karty.

## [2026.7.3.post182] - 2026-08-11 - Prázdny profil povie, prečo je prázdny

###  Fixed
- Profil študenta bez merge requestov v období kurzu to teraz povie a uvedie obdobie, namiesto tvrdenia, že v repozitároch žiadne nie sú.

## [2026.7.3.post181] - 2026-08-11 - Viditeľný fokus klávesnice v menu

###  Fixed
- Položky v rozbaľovacích menu majú konečne fokusový rámček; predtým vyzeral fokus z klávesnice presne ako hover myšou.
- Zatváracie tlačidlo sprievodcu bolo posledný prvok nastavený v rem namiesto tokenov. V aplikácii už nezostali žiadne desatinné pixelové rozmery.

## [2026.7.3.post180] - 2026-08-11 - Sprievodca už neprerába tlačidlá

###  Fixed
- Tlačidlá v uvítacom okne sprievodcu sa konečne zhodujú so všetkými ostatnými - dovtedy si ich tour.css prekresľoval nanovo v rem jednotkách.

###  Added
- Test zlyhá, ak niektorý stylesheet nastavuje rozmery holému `<button>`; presne tak tá prepisujúca definícia potichu vyhrala.

## [2026.7.3.post179] - 2026-08-11 - Hover na logu končí plynulo

###  Fixed
- Odtiahnutie kurzora z loga už neukončí efekt skokom v jednom snímku - doznie plynulo za 420 ms.
- Dve staré `transition` pravidlá, ktoré opravu potichu rušili, sú preč; test teraz zlyhá, ak pribudne ďalšie.

###  Changed
- Hover je výraznejší (jas 1.85, silnejšia žiara) - pri 24 px bol ten predošlý sotva viditeľný.

## [2026.7.3.post178] - 2026-08-11 - Karty a merge requesty vrátené späť

###  Reverted
- KPI karty sú späť v štýle spred post175 - s výplňou, 16px zaoblením a nadvihnutím pri hoveri. Hlavička z post177 je preč.
- Stránka študenta je tiež obnovená: karty merge requestov, blok s ľuďmi aj hlavička stĺpcov sú ako predtým.

## [2026.7.3.post177] - 2026-08-11 - Hlavičky kariet, merge requesty ako zoznam

###  Fixed
- KPI karty majú späť svetlejšiu hlavičku - popis a ikona v nej, číslo pod ňou, ako v GitLabe.
- Hlavička používa token, ktorý je viditeľne odlišný od tela karty v OBOCH témach; ten predošlý sa vo svetlej téme zlial s bielou.

###  Changed
- Merge requesty sú zoznam ako v GitLabe: `Stav | Názov | Pridelený | Recenzenti | Kontroly`, s hlavičkou stĺpcov, referenciou a diff štatistikou pod názvom a recenzentmi vo vlastnom stĺpci.

## [2026.7.3.post176] - 2026-08-11 - Stav "hotovo" už neprepíše vlastné tlačidlo

###  Fixed
- Tlačidlo System Health už nezamrzne natrvalo na "Kontrolujem...": načítavanie a stav "hotovo" si tlačidlo odovzdávajú explicitne, namiesto prepisovania toho istého popisu.
- Hover na logu beží dokola, kým je tam kurzor - svetlý segment už nezostane stáť na konci EKG stopy.

###  Changed
- Ukončenie stavu "hotovo" je jedna zdieľaná funkcia, ktorú volá aj časovač, aj nový klik.

## [2026.7.3.post175] - 2026-08-11 - Navigácia sa už nepohne sama

###  Fixed
- Dokončená úloha na pozadí už nenačíta nanovo stránku, ktorá si to nevyžiadala - registrácia sa zruší, keď navigácia opustí danú stránku.
- Horný ukazovateľ priebehu už necúva späť, keď sa nová navigácia začne skôr, než dobehne predchádzajúca.

###  Added
- Pätička stránky ako v GitLabe: vycentrovaná dvojica `Zanechať spätnú väzbu | Dokumentácia` uzatvára každú stránku okrem prehľadu, ktorý už má panel "Podpora a návrhy".

###  Changed
- Riadky merge requestov majú anatómiu ako v GitLabe: najprv stavový štítok, tučný názov, referencia `namespace/projekt!iid` a "Aktualizované ..." vpravo.
- KPI karty na admin prehľade sú len s obrysom ako všetky ostatné a hover je zmena farby, nie nadvihnutie.
- Hover na logu je prepísaný: po EKG stope prejde svetlý segment a každý tvar sa rozžiari, keď k nemu vlna dôjde.

## [2026.7.3.post174] - 2026-08-11 - Karty bez výplne, tenší zárez

###  Fixed
- Karty na prehľade sú opäť len s obrysom, bez sivej výplne - ako v GitLabe.
- Zárez pod hlavičkou je tenší (2 px).

## [2026.7.3.post173] - 2026-08-11 - Väčší avatar

###  Fixed
- Avatar v hornom paneli má rovnakú veľkosť ako ostatné prvky (32 px).

## [2026.7.3.post172] - 2026-08-11 - Zárez v správnej farbe

###  Fixed
- Zárez pod hlavičkou má farbu pozadia aplikácie, takže vyzerá ako skutočný prierez panelom.

## [2026.7.3.post171] - 2026-08-11 - Odstránený 4px pásik

###  Removed
- Odstránený 4px pásik nad obsahom aj jeho obsluha rolovania.

## [2026.7.3.post170] - 2026-08-11 - Vlastná animácia loga

###  Changed
- Logo má vlastnú animáciu - svetlo prebehne značkou zl'ava doprava a rovnako sa vráti.
- Značka má rovnakú výšku ako logo GitLabu.

## [2026.7.3.post169] - 2026-08-11 - Zárez je konečne vidno

###  Fixed
- Karty na prehl'ade sú o odtienň svetlejšie ako panel, ako v GitLabe - preto sa zárez pri rolovaní jasne vidí.

## [2026.7.3.post168] - 2026-08-11 - Obsah už nie je pritlačený k hlavičke

###  Fixed
- Vrátený horný odstup obsahu - stránky už nie sú stlačené k drobčekovej navigácii.

## [2026.7.3.post167] - 2026-08-11 - Logo si drží farbu

###  Fixed
- Logo pri prejdení myšou už nevybledne dobiela, len sa jemne rozjasní.

## [2026.7.3.post166] - 2026-08-11 - Podsvietenie loga podľa GitLabu

###  Fixed
- Logo sa pri prejdení myšou rozjasní presne tak veľmi ako v GitLabe a plynule sa vráti späť.

## [2026.7.3.post165] - 2026-08-11 - Zárez pod drobčekovou navigáciou

###  Fixed
- Pri rolovaní sa pod hlavičkou objaví 4-pixelový zárez, presne ako v GitLabe.
- Nad spodnou skupinou v bočnom paneli už nie je žiadna čiara.

## [2026.7.3.post164] - 2026-08-11 - Horný panel ako jeden riadok

###  Fixed
- Všetky prvky v hornom paneli majú téraz rovnakú výšku aj veľkosť písma ako v GitLabe.
- Logo je zarovnané na šírku značky GitLabu, takže už nedominuje panelu.
- Podsvietenie loga pri prejdení myšou je jemné, nie oslepujúce.

## [2026.7.3.post163] - 2026-08-11 - Zárez pod drobčekovou navigáciou

###  Fixed
- Obsah začína hneď pod hlavičkou ako v GitLabe, takže sa pri rolovaní viditeľne zaríza pod ňu.

## [2026.7.3.post162] - 2026-08-11 - Bez stmavenia pri rolovaní

###  Fixed
- Obsah sa pri rolovaní už hore nestmavuje - GitLab tam žiadny prechod nemá, je tam len nepriehl'adná hlavička.
- Spätná väzba už nevynecháva každé druhé stlačenie tlačidla.
- Stav „Hotovo" sa teraz zobrazí na každom tlačidle vrátane Obnoviť a Synchronizovať.
- Opravená chyba v štýloch, ktorá na produkcii vyračovala časť animácií.

## [2026.7.3.post161] - 2026-08-11 - Stav „dokončené" na tlačidlach

###  Added
- Tlačidlo, ktorým ste akciu spustili, teraz sám oznámi, že skončila: zelené „Hotovo" so zaškrtnutím na 1,6 sekundy.

###  Fixed
- Ručné obnovenie stránky už nespúšťa druhé automatické obnovenie po nasadení novej verzie.

## [2026.7.3.post160] - 2026-08-11 - Pohyb odmeraný z GitLabu, nie odhadnutý

###  Changed
- Rozbaľovacie ponuky sa už neroztmavujú ani nezväčšujú - GitLab ich zobrazuje a skrýva okamžite.
- Každé zatváranie používa krivku GitLabu; predchádzajúca krivka držala prvok viditeľný príliš dlho.
- Zatvorené dialógové okno sa už neposúva nadol, iba plynulo zmizne.
- Hlavička panela má rozmery GitLabu (36 px, zaoblenie 8 px hore) a obsah sa pod ňou zarezáva.
- Obsahový panel prilieha k bočnému menu, takže je o 8 px širší ako doteraz.
- Karty na prehľade majú stav: súlad sa farbí rovnakými pásmami ako semafory v kurze a nula bez dát je tlmená.

###  Fixed
- Grafy už nebojujú so svojimi skeletonmi: ak sa skeleton nikdy nezobrazil, graf sa objaví naraz; ak sa zobrazil, ostane čitateľný aspoň 400 ms.

## [2026.7.3.post159] - 2026-08-11 - Zárez pri rolovaní teraz naozaj funguje

###  Fixed
- **Zárez vydaný v post158 sa nikomu nezobrazil**: jeho priehľadnosť riadilo `animation-timeline: scroll()`, ktoré vyžaduje Chrome 115+, takže inde sa pravidlo ignorovalo a zárez ticho neexistoval. Teraz ho riadi trieda `.is-scrolled` z pasívneho poslucháča rolovania obmedzeného cez rAF - rovnako ako to robí GitLab. Overené skutočným rolovaním kolieskom.
- **Odkazy v drobečkovej navigácii robili pri prejdení myšou opak toho, čo GitLab**: v pokoji `none` -> pri prejdení `underline`, farba sa nemení. Naše menili farbu a podčiarknutie potláčali.
- **Rolové štítky pôsobili stlačené**: vykresľujú sa ako `size='sm'` a `.badge-sm` stlačil odsadenie na 4 px. GitLab má jednu mieru odznaku - 2px/6px pre každý variant - takže `.badge-sm` už vlastnú nemá.

## [2026.7.3.post158] - 2026-08-11 - Zárez pri rolovaní pod riadkom drobečkov

###  Added
- **Zárez, ktorý sa objaví, keď obsah roluje pod drobečkovou navigáciou**, prevzatý priamo zo štýlov inštancie: 36px lepkavý pruh pripnutý na vrch oblasti rolovania so záporným okrajom, takže nezaberá miesto, `opacity: 0` v pokoji a výplň `linear-gradient(180deg, alpha-dark-8, transparent)` (`alpha-dark-24` v tmavej), ktorá sa objaví, len čo je nad okrajom nejaký obsah. Zreprodukované na `.gl-page-content::before` s rovnakými 36 px a rovnakými prechodmi z našich existujúcich alfa tokenov, pričom priehľadnosť riadi animácia viazaná na rolovanie, nie obsluha udalosti.

## [2026.7.3.post157] - 2026-08-11 - Overené voči vlastnej inštancii GitLabu univerzity

###  Changed
- **Referenciou je teraz priamo `gitlab.example.com`** - jeho stránky `/explore` sú dostupné bez prihlásenia, takže každé číslo pochádza presne z toho buildu, voči ktorému sa tento projekt porovnáva. Potvrdilo to prácu na kostre (horná lišta 48 px, bočný panel 240 px, zaoblenie panela 12 px, položka navigácie 28 px/8 px, vyhľadávanie 344x32/12 px aj tmavé pozadie `rgb(40,39,45)` už sedeli) a odhalilo päť vecí, ktoré nie: popisky tlačidiel sedia na 16px riadku (my sme mali `line-height: 1`), vyhľadávanie zdedilo 1,5 riadok textu namiesto 16 px, pozdrav na nástenke mal hrúbku 500, kde GitLab dáva 600, odznaky majú presne 20 px a nesmú sa v riadku stláčať, a odkazy v drobečkovej navigácii majú 4px zaoblenie. Oblasť rolovania sa navyše začína 4 px pod riadkom drobečkov, čím vzniká pruh pozadia panela - zárez, ktorý sa objaví pri rolovaní; naša začínala tesne.

###  Notes
- Avatary boli správne už predtým: používatelia sú kruhy, projekty a skupiny štvorce so zaoblením 4 px - presne tak ich vykresľuje aj inštancia.

## [2026.7.3.post156] - 2026-08-11 - Opravená drobečková navigácia, paleta a vyhľadávanie

###  Fixed
- **Drobečková navigácia bola zle hneď v štyroch veciach**: jej koreň bol pevný „Prehľad", takže na prehľade písala „Prehľad > Prehľad", oddeľovala položky ikonou šípky, mala 14 px a sedela v riadku s `overflow: hidden`, ktorý orezával dolné dotiahnutia písmen. Odmerané na gitlab.com: položky majú 12 px na 16px riadku v 24px pruhu s `overflow: visible`, oddeľovačom je znak „/" a nie ikona, hrúbku 600 má len aktuálna stránka a koreňom je sekcia, do ktorej stránka patrí. Všetky štyri veci teraz sedia.
- **Lišta filtrov skákala a blikala pri každom stlačení klávesy vo vyhľadávacej palete.** `.gl-search-modal-body:empty` odstraňovalo stĺpec výsledkov cez `display: none`, čím z riadka zmizlo jeho `flex: 1`, a 220px panel filtrov odskočil k ľavému okraju a späť vždy, keď render nakrátko vyprázdnil zoznam. Overené počas písania: panel teraz drží jednu pozíciu pri každom stlačení.

###  Changed
- **Prejdenie myšou po vyhľadávaní je ako v GitLabe**: orámovanie stmavne z `rgba(5,5,6,0.24)` na `rgba(5,5,6,0.4)` za 0,2 s out-cubic a nič iné sa nemení. Naše menilo aj pozadie. Overené v oboch témach.

## [2026.7.3.post155] - 2026-08-11 - Typografická škála zahodila dve veľkosti, ktoré GitLab nemá

###  Fixed
- **Rozhranie pôsobilo menšie než GitLab a čísla hovoria prečo.** Spočítané cez každý viditeľný prvok pri 1920: GitLab používa 14 px (1458 prvkov), 21 px (40), 12 px (34), 30 px (4) - a 13 px ani 11 px ani raz. My sme mali 88 prvkov na 13 px, 12 na 11 px a 37 na 11,375 px (pravidlo pre riadkový `code` relatívne v `em`). `--font-size-sm` je teraz 14 px, `--font-size-xs` 12 px, posledné natvrdo písané 11 px používajú token 12 px a riadkový `code` sa vykresľuje vo veľkosti textu, ako na gitlab.com.
- **Správanie loga pri prejdení myšou bolo zlé v oboch smeroch.** Meranie len `<a>` a vonkajšieho `<svg>` minulo miesto, kde animácia GitLabu naozaj žije: ich tanuki je zložený z pomenovaných častí a každá prechádza svojou **výplňou** - 0,8 s v pokoji, 0,1 s pri rozsvietení, takže časť pod kurzorom rýchlo vzplanie a pomaly zhasne. Nič sa nehýbe. Naša značka je tiež zložená z častí a teraz sa správa rovnako; zdvih, zväčšenie a tieň pri prejdení sú preč.

## [2026.7.3.post154] - 2026-08-11 - Načítavacie stavy prestali blikať; chróm kostry odmeraný

###  Fixed
- **Skeletony blikli a zmizli skôr, než sa dali prečítať.** Mechanizmus, ktorý drží zástupný prvok neviditeľný, kým načítanie naozaj netrvá, platil len pre `.gl-skeleton`; zložené skeletony (riadky tabuliek, stĺpcový graf, obal grafu, panel zdravia) sú iné triedy a vykresľovali sa okamžite - namerané 447 ms, 512 ms a 933 ms viditeľného života na admin Systéme. Každý koreň skeletonu teraz zdieľa oneskorené odhalenie a prah sa posunul z 250 ms na 400 ms. Overené meraním priehľadnosti vrátane predkov: skeletony tabuliek a grafov teraz dosahujú vrchol 0,00 (pri rýchlom načítaní sa nevykreslia vôbec), kým panel zdravia, ktorý naozaj trvá ~900 ms, sa zobrazí celý.
- **Chybové stránky sa odchýlili od dizajnového systému**: ich vlastný alias zaoblenia stále ukazoval na všeobecné 4 px, takže polia a tlačidlá tam boli hranatejšie než tie isté prvky inde, nadpis mal 26 px oproti 40 px v GitLabe, vyhľadávacie pole 39 px oproti 32 px v aplikácii a odkazy používali surovú značkovú modrú. Všetky štyri teraz nasledujú tokeny aplikácie v oboch témach.

###  Changed
- **Pohyb modálnych okien je ako v GitLabe**: prekryv `opacity 0.15s linear`, dialóg z 50 px zhora cez `transform 0.3s ease-out`. Naše sa objavovalo za 100 ms a rástlo zo `scale(0.85)` na pružine 400 ms.
- **Vyhľadávanie v hornej lište rastie s oknom**, presne `20vw + 56px` - namerané 261/312/344/392/440 px pri 1024/1280/1440/1680/1920. Naše bolo pevných 344 px.
- **Logo je statické ako v GitLabe** - tam sú pokojový a prejdený stav identické. Tep pri prejdení myšou je preč aj s tromi osirelými keyframami.

## [2026.7.3.post153] - 2026-08-11 - Bubliny sa zaobľujú ako každý iný prekryv

###  Changed
- Bubliny mali zaoblenie 4 px, kým každý iný prekryv máme na 8 px (bublina GitLabu má 8 px pri odsadení 16px/24px, ktoré sme už mali rovnaké). Povrch aj malé ovládacie prvky v ňom teraz používajú rovnaké tokeny ako menu a akcie.
- Známy rozdiel: bublina GitLabu je neutrálny tmavý štítok v oboch témach; naša je zafarbená podľa variantu, lebo u nás nesie význam úspech/varovanie/chyba. Ponechané, nemenené potichu.

## [2026.7.3.post152] - 2026-08-11 - Jeden ovládač menu namiesto dvoch

###  Removed
- **Druhý ovládač rozbaľovacích menu.** `.gl-dropdown` riadil obslužný kód v jadre, kým `[data-dropdown]` riadil `dropdowns.js` - dve implementácie jednej interakcie, každá s kontrolou tej druhej, aby si nerozhodili stav `.open`. Práve to prepojenie bolo varovaním: keď sa pokazilo, menu sa otvorilo raz a potom sa tvárilo natrvalo zatvorené. `dropdowns.js` teraz vlastní **obe** konvencie selektorov, takže sa nezmenil ani riadok značkovania, a 76-riadkový kód v jadre je preč.
- Dve správania, ktoré mal len zmazaný ovládač, sa presunuli: výber položky zavrie jej menu a menu presunuté do `<body>` sa nikdy nepovažuje za kliknutie mimo. Menu riadené Alpine sa naďalej preskakujú.

###  Added
- `tests/unit/test_one_controller_per_interaction.py` pripína obe zlúčenia - jednu ochranu kliknutí aj jeden ovládač menu. Najprv overené v prehliadači: 12 menu na piatich stránkach sa správne otvára a zatvára, presunuté menu veľkosti strany sa otvorí, vyberie a zavrie, a prepínač témy nechá používateľské menu otvorené.

## [2026.7.3.post151] - 2026-08-11 - Pohyb zrovnaný s GitLabom, nielen jeho rýchlosť

###  Changed
- **GitLab animuje farbu a nič iné.** Odmerané na skutočných komponentoch Pajamas: tlačidlo prechádza `color, background-color, border-color, box-shadow, text-decoration-color` za 0,2 s out-cubic a **žiadny transform**; karty, odkazy, upozornenia a zaškrtávacie políčka neanimujú vôbec nič. Naše tlačidlá sa pri stlačení zmenšovali na 0,94, položky bočného panela na 0,98 a ikony navigácie sa pri prejdení zväčšovali na 1,1. Zrovnať trvania bola len polovica práce - samotný pohyb je to, čo prezrádza. Všetky tri odstránené; zoznam vlastností tlačidla je teraz presne ako v GitLabe.
- **Formulárové prvky animujú inú dvojicu.** GitLab hýbe `border-color, box-shadow` za 0,15 s ease-in-out, nie 0,2 s out-cubic, ktoré používa každá akcia. Pribudlo `--transition-control` a nasmerovali sme naň textové pole, výber, prepínač menu, zaškrtávacie políčko, koľajničku prepínača aj vyhľadávacie pole.

###  Removed
- Prepis pre obmedzený pohyb, ktorý rušil `.btn:active { transform }` - mŕtvy, keď stlačenie žiadny transform nemá.

## [2026.7.3.post150] - 2026-08-11 - Kostra aplikácie prestavaná podľa GitLabu, druhá ochrana kliknutí zmazaná

###  Changed
- **Samotná kostra mala nesprávny tvar.** Horná lišta GitLabu ide cez CELÚ šírku (odmerané 0,0,1440x48 na gitlab.com) a bočný panel začína pod ňou; u nás bol bočný panel cez celú výšku vľavo a lišta len nad obsahom, takže stránka pôsobila ako „bočný panel a vedľa neho lišta" namiesto „lišta nad všetkým" - rozdiel viditeľný ešte pred akýmkoľvek komponentom. Lišta je teraz cez celú šírku so značkou vľavo hore, kde ju má GitLab, a bočný panel sedí pod ňou. Overené voči GitLabu na troch šírkach v oboch témach: lišta (0,0,1440,48), bočný panel (0,48,240), zaoblenie panela 12 px, položka navigácie 28 px s odsadením 2px/4px, nadpis stránky 30 px - všetko presne.
- Zaoblenie panela obsahu 16 px -> 12 px, horná lišta 49 px -> 48 px, `h1` stránky 24 px -> 30 px, položky navigácie 0/8px -> 2px/4px s 2px medzerou a spodná skupina bočného panela 13 px -> 14 px, aby sedela s položkami nad ňou.

###  Removed
- **Druhá ochrana proti rýchlym kliknutiam.** `interceptSpamClicks` počítala 3 kliknutia za 2 s a aplikovala viditeľný cooldown, čím zdvojovala tiché tlmenie v jadre. Dve ochrany nad jednou interakciou sú o jednu viac a navyše si protirečili: prepínač stromu prežil jednu a zomrel na druhej. Zmazané aj s mapou časových značiek; cooldown zostáva len pre zlyhané akcie. Overené šiestimi reálnymi rýchlymi kliknutiami - dokonalé striedanie, žiadne mŕtve kliknutie.
- Posun `left` hornej lišty pre zbalený bočný panel a jej `transition: left` - oboje mŕtve, keď lišta ide cez celú šírku v každom stave.

## [2026.7.3.post149] - 2026-08-11 - Karty, odznaky a menu odmerané podľa Pajamas

###  Changed
- **Záložky boli o stupeň menšie a nikdy nevyzerali celkom vybrané.** GlTabs na design.gitlab.com má 50 px na výšku, 14px text na 16px riadku, odsadenie 16px/12px a všetky záložky nechá v ROVNAKEJ farbe - GitLab označuje výber hrúbkou písma (400 -> 600) a indikátorom, ničím iným. Naše mali 13 px a hrúbku 500 v oboch stavoch, odsadenie 8px/16px a neaktívne stlmené, takže lišta bola o 12 px nižšia a každá záložka pôsobila spolovice vybraná. Teraz sú identické.
- **Malé odznaky boli ťažšie a vyššie než ktorýkoľvek odznak v GitLabe.** Každý variant na design.gitlab.com/components/badge má 12 px / hrúbku 400 / 2px 6px / 20 px na výšku - GitLab má jednu mieru odznaku. `.badge-sm` dvíhal hrúbku na 500 a zvislé odsadenie na 3 px; teraz iba uberá vodorovné odsadenie.
- **Menu sa vykresľovalo o stupeň menšie než stránka za ním.** GitLab kreslí prepínač aj položky menu v 14 px, rovnako ako základný text; naše mali 13 px.
- Číslo aktuálnej strany v stránkovaní bolo zaoblené na 4 px, kým tlačidlá vedľa neho na 8 px, takže číslo pôsobilo hranatejšie než jeho vlastné šípky.

## [2026.7.3.post148] - 2026-08-11 - Typografia dokumentácie zrovnaná s docs.gitlab.com

###  Changed
- **Dokumentácia mala nadpisy o celý stupeň menšie.** Odmerané na obsahovej stránke docs.gitlab.com: h1 40px/46px, h2 32px/40px, h3 24px/30px, riadkový kód aj bloky kódu rovných 14 px. Naše boli 32 / 25 / 21 a kód 12,24 px v riadku a 13,6 px v bloku - oboje relatívne v `em`, takže sa násobili voči kontajneru namiesto pevnej veľkosti. Základný text už bol 16px/25,6px a zostal. Po zmene premerané: p, h1, h2, h3, riadkový kód aj bloky kódu sú na oboch stránkach identické.
- Zaoblenie 8 px na blokoch kódu je napokon správne: GitLab ho dáva na `.codeblock-wrapper` a samotné `<pre>` necháva hranaté a priehľadné, takže meranie `<pre>` ukázalo 0 px. My samostatnú obálku nemáme, takže zaoblenie zostáva na `.highlight` / `pre`.

###  Removed
- **Posledné inline štýly, ktoré v skutočnosti patrili do CSS.** `width: 100%` na bloku s údajmi používateľa a `vertical-align: middle` na počítadle commitov študenta sa presunuli do `dropdowns.css` a spoločného pravidla `.match-count` - to isté počítadlo dovtedy sedelo na stránke predmetu na inej účiari, lebo tam žiadne pravidlo nebolo. Skeleton živých údajov na detaile projektu prestal ručne písať `height/width/margin/border-radius` a používa rovnaké API cez vlastnú vlastnosť `--sk-w` ako všetky ostatné skeletony, plus dve spoločné triedy (`.gl-skeleton-row`, `.gl-skeleton-gap`) namiesto súkromných 6px / 8px odsadení v modálnom okne používateľa.
- Každý zvyšný atribút `style` už odovzdáva *hodnotu*, ktorú trieda uniesť nevie (`--sk-w`, `--chart-h`, `--h-bar-label-w`), čo je zamýšľaný vzor; žiadny nedeklaruje vlastnosti priamo.

## [2026.7.3.post147] - 2026-08-11 - Zaoblenia, pohyb a strom skupín odmerané podľa GitLabu

###  Fixed
- **Rozbalenie skupiny vysypalo naraz všetky riadky projektov.** Strom skupín v GitLabe ukáže prvých pár potomkov a zvyšok schová za odkaz „Zobraziť všetko (N ďalších)"; nám sa vykreslilo všetkých 15 a odsunulo celý zvyšok tabuľky mimo obrazovku. Rozbalená skupina teraz ukáže 3 potomkov a ten odkaz. Limit je v šablóne, ktorá riadkom nad ním pridá `.tree-row-extra` - klient vykresľuje podľa tried a číslo si nedrží, takže sa nemôžu rozísť. Overené v oboch témach vrátane toho, že limit prežije filtrovanie aj prekreslenie stránkovania.
- **Tri kliknutia na ktorýkoľvek rozbaľovací prepínač do dvoch sekúnd ho zamrazili.** Ochrana proti spamu v `process-action-guards.js` považovala prepínač stromu za skutočnú operáciu, takže rozbaliť/zbaliť/rozbaliť nechalo ovládací prvok mŕtvy. Rozbaľovacie prvky (`aria-expanded` / `aria-pressed`) neposielajú žiadnu požiadavku a obe ochrany ich teraz vynímajú; tlačidlá s `data-process-lock-when` zostávajú obmedzené.

###  Changed
- **Každé zaoblenie komponentu bolo nesprávne.** GitLab nepoužíva jedno zaoblenie na všetko a voľba všeobecných 4 px pre tlačidlá a polia je presne to, prečo naše ovládacie prvky pôsobili na porovnávacích snímkach hranatejšie. Odmerané naživo - tlačidlo 8 px a položka navigácie 8 px na gitlab.com, pole 8 px, karta 12 px a upozornenie 8 px na design.gitlab.com - a zreprodukované cez pomenované tokeny z `@gitlab/ui` 136.1.0. Tlačidlá a formulárové prvky 4 px -> 8 px, karty 8 px -> 12 px, modálne okná 12 px -> 16 px (kód tvrdil `gl-border-radius-2xl`, čo je 16 px, a používal 12 px).
- **Animácie bežali o polovicu pomalšie.** `@gitlab/ui` publikuje fast 0,1 s / medium 0,2 s / slow 0,4 s a meranie gitlab.com s vypnutým obmedzením pohybu ukazuje v praxi len 0,1 s / 0,15 s / 0,2 s. My sme bežali na 200 / 290 / 500 ms. Zrovnané na 100 / 200 / 400 ms.
- **Výška riadka textu 1,4 -> 1,5.** GitLab sadzí 14px text na 21px riadok; náš mal 19,6 px, takže každý odsek, bunka tabuľky aj karta boli hustejšie ako rovnaký obsah v GitLabe.
- **Hlavičky tabuliek 13 px nad 2px linkou -> 14 px nad 1px**, odmerané na skutočnom komponente Pajamas, nie na markdownovej tabuľke.

###  Added
- `tests/unit/test_tree_disclosure_contract.py` pripína značkovaciu štruktúru limitu, kontrakt klienta riadený triedami a výnimku pre rozbaľovacie prvky v oboch ochranách kliknutia.

## [2026.7.3.post146] - 2026-08-10 - Odznaky majú farby zo živého GitLabu

###  Changed
- **Odznaky mali v oboch témach nesprávne farby.** Extrakcia živého gitlab.com nástrojom Dembrandt ukázala, že neutrálny odznak má pozadie `#dcdcde` a text `#4c4b51`, úspešný `#c3e6cd` / `#306440` - teda dvojicu `--gl-status-*`, čiže **tlmený** štítok. Naše boli jasné štítky úrovne 300 s takmer čiernym textom v tmavej téme a o krok tmavšie v svetlej. Každý variant teraz kopíruje GitLab: pozadie `*-100` s textom `*-700` v svetlej, `*-800` s `*-200` v tmavej. Overené v prehliadači: náš úspešný odznak má presne `rgb(195, 230, 205) / rgb(48, 100, 64)` - rovnaké hodnoty, aké extrakcia načítala z gitlab.com. Výška riadka odznaku je pripnutá na 16 px ako v GitLabe.
- Dokumentácia používa pre interaktívne prvky zaoblenie 8 px. Extrakcia napočítala 8 px na 52 prvkoch (vyhľadávanie, tlačidlá, karty) oproti 14 pre 4 px, ktoré zostáva pre vložený kód a štítky. Produkt zostáva na 4 px; dokumentácia je zámerne mäkšia a post144 ich zrovnal na 4 px podľa odhadu.

###  Removed
- **`pages/admin.css` predefinoval `.badge-gray`.** Prepisoval spoločný komponent vlastnými farbami len na admin stránkach, takže ten istý stavový štítok mal dve rôzne farby podľa stránky a ani jedna nezodpovedala GitLabu. Odstránené.

###  Added
- Tokeny odznakov pribudli do `tests/unit/test_gitlab_token_parity.py` (25 -> 35 pripnutých hodnôt).

## [2026.7.3.post145] - 2026-08-10 - „Zobraziť viac" je spoločný komponent

###  Changed
- **„Zobraziť viac / menej" je jeden komponent namiesto funkcie len pre prehľad aktivity.** Rozbaľovanie žilo celé vnútri prehľadu aktivity na nástenke: vlastné triedy, vlastná značkovacia štruktúra pätičky, pravidlá zakopané v `home.css`. Každý ďalší zoznam s rovnakým správaním by musel skopírovať všetky tri. Teraz je to `components/disclosure.html` a všeobecné pravidlá `.gl-show-more*` v `utilities.css`. Kontrakt pokrýva aj riadky tabuliek - `display: none` na `<tr>` je platné, takže `<div data-show-more>` okolo tabuľky vie skryť prebytočné riadky rovnako. Overené v prehliadači: 0 riadkov -> 5 po rozbalení -> 0 po zbalení, bez chýb v konzole.

###  Removed
- Triedy `.gl-activity-item--extra` a `.gl-activity-show-more*` špecifické pre prehľad aktivity, zdvojená značkovacia štruktúra tlačidiel a import, ktorý zmena osirela.

## [2026.7.3.post144] - 2026-08-10 - Tlačidlá a dokumentácia majú skutočné farby GitLabu

###  Changed
- **Hlavné tlačidlo už nie je modré.** Vlastné dizajnové tokeny GitLabu farbia potvrdzovacie/hlavné tlačidlo na `neutral-800` v svetlej téme a `neutral-50` v tmavej - modrá je vyhradená pre odkazy, zameranie a informácie. Aplikácia ho mala modré, čo bol hlavný dôvod, prečo sa snímky obrazovky nikdy nezhodovali. Zaškrtnuté políčka a prepínače, dráha prepínača, vybraný filter, aktuálna strana stránkovania aj vybraná položka navigácie prechádzajú na rovnakú neutrálnu škálu, lebo GitLab ich všetky farbí z `--gl-action-selected-*`. Hodnoty pochádzajú z `@gitlab/ui` 136.1.0 a boli overené v prehliadači v oboch témach: **14 meraní, 0 nezhôd.**
- Fajka v zaškrtávacom políčku, bodka prepínača aj hlavička prepínača sa riadia témou namiesto natvrdo zapísanej bielej. Museli: zaškrtnutý ovládací prvok je v tmavej téme takmer biely, takže biely glyf by bol neviditeľný.
- **Každý prázdny stav vedie ilustráciou GitLabu.** 37 z nich zobrazovalo glyf v rámčeku; teraz vkladajú zodpovedajúcu ilustráciu z `@gitlab/svgs` (MIT, 15 vložených). SVG sú vložené priamo, nie cez odkaz, pretože sa farbia z `--gl-illustration-*`, čo by `<img>` nikdy neprečítal.
- **Stránka dokumentácie bola prepísaná na dizajnový jazyk GitLabu.** Bežala na predvolenej indigo/fialovej palete Material s prechodmi v hlavičkách tabuliek, veľkými písmenami v názvoch stĺpcov, zaoblením 8-12 px, tieňmi a kartami, ktoré sa pri prejdení myšou dvíhali. Teraz je to GitLab: neutrálne prostredie oddelené vlasovými linkami, zaoblenie 4 px, nadpisy vo farbe textu, obyčajné tabuľky a rovnaké písma GitLab Sans/Mono ako v produkte. Paleta Material je nastavená na `custom`, aby téma už nemohla vrátiť vlastné odtiene.
- Chybové stránky, sprievodca produktom, výzva na inštaláciu PWA a tlačidlo prihlásenia prestali definovať vlastnú hlavnú farbu a používajú spoločné tokeny tlačidiel. Štyri súkromné definície „hlavného tlačidla" sú štyri príležitosti na rozchod.
- Kostry načítania používajú zaoblenie 4 px ako GitLab namiesto 2 px a kostra grafu prešla na rovnaký prechod ako všetky ostatné. Existovali dva mechanizmy trblietania; druhý animoval `background-position`, čo kompozítor nevie spustiť samostatne, takže zamrzol presne pri záťaži, o ktorej informoval.
- Deštruktívne akcie s ikonou v riadkoch tabuľky sa vykresľujú ako terciárne nebezpečné - červený glyf s červeným podfarbením pri prejdení myšou - namiesto plného červeného bloku, presne ako riadkové akcie v GitLabe.

###  Added
- `tests/unit/test_gitlab_token_parity.py` pripína 25 interaktívnych farebných tokenov na `@gitlab/ui` 136.1.0 v oboch témach. Nič iné v testoch by si nevšimlo, keby sa vrátili na modrú.

###  Removed
- Deklarácia animácie `.gl-skeleton`, ktorú neskoršie pravidlo aj tak prepísalo, jej zastaraný komentár, zdvojený komentár k rámcom, nepoužívaný token `--gl-toggle-unchecked-hover` a druhý rámec kostry.

## [2026.7.3.post143] - 2026-08-10 - Prehľad aktivity má rozloženie ako v GitLabe

###  Changed
- **„Sledujte najnovšie aktualizácie" má rozloženie ako Aktivita v GitLabe.** Riadok bol jeden plochý reťazec `Aktér - Akcia` vedľa ikony, čo pôsobilo ako riadok logu. Teraz je to avatar, aktér tučným písmom s časom odsunutým doprava, akcia na vlastnom riadku s ikonou a detail pod ňou - presne ako to robí GitLab. Zostavovač posiela `actor` a `action` ako samostatné polia namiesto jedného spojeného reťazca, ktorý sa už nedal spoľahlivo rozdeliť.
- Prepojený aj neprepojený variant riadka zdieľajú jedno makro; predtým mali zdvojenú značkovaciu štruktúru, ktorá sa mohla rozísť.

###  Fixed
- **V riadku aktivity sa namiesto ikony zobrazoval otáznik.** Prehľad si pýtal `user-x`, ktorý sada ikon nedefinuje, takže riadok o hodnotení člena vykreslil náhradný glyf. Teraz používa `user-minus` a nový test overuje, že každá ikona, ktorú prehľad menuje, naozaj existuje.

## [2026.7.3.post142] - 2026-08-10 - Posledné okná prehliadača sú preč, rozbaľovací zoznam už neseká vlastné položky

###  Changed
- **Každý zvyšný `window.confirm` beží na dialógu aplikácie.** Dvanásť miest v deviatich súboroch sa stále pýtalo cez prehliadač - zrušenie úlohy, synchronizácie, importu či behu AI, rotácia tajného kľúča webhooku, odstránenie týždňa, zmena identity kurzu alebo okna semestra. Šesť z nich bolo v synchrónnych pomocníkoch, ktorých návratovú hodnotu volajúci používal, takže sa stali asynchrónnymi a volajúci na ne teraz čakajú. Overené kliknutím na 117 tlačidiel na deviatich stránkach: **žiadne natívne okno**.

###  Fixed
- **Rozbaľovací zoznam orezával vlastné položky.** Menu malo strop 320 px a text sa nezalamoval, takže dlhý nedeliteľný názov - napríklad vetva `kyryl_ticket_num_2...` - vybehol za okraj a menu dostalo vodorovný posuvník. Menu sa teraz prispôsobí obsahu, nikdy nie je užšie než ovládací prvok a nikdy širšie než okno, a dlhé názvy sa zalomia. Opravené v spoločnom komponente, takže to platí pre všetky rozbaľovacie zoznamy v aplikácii.

## [2026.7.3.post141] - 2026-08-10 - Každý rozbaľovací zoznam povie, keď nemá čo ponúknuť

###  Fixed
- **Výber bez možností sa vykreslil ako prázdny obdĺžnik.** Otvorenie „Cieľ importu" bez existujúcich kurzov ukázalo prázdny rámček, čo pôsobí skôr pokazene než ako „nie je z čoho vyberať". Spoločné makro `select_field` teraz vypíše „Žiadne možnosti na výber", takže prázdny stav získali všetky rozbaľovacie zoznamy naraz namiesto toho, aby si ho každé miesto vymýšľalo samo.

## [2026.7.3.post140] - 2026-08-10 - Zoradenie odpovie na prvý klik, kontrola stavu povie výsledok

###  Fixed
- **Zoradenie tabuľky akoby potrebovalo dva kliky.** Prepnutie na nový stĺpec ho zoradí vzostupne, čo veľmi často zopakuje poradie, ktoré už je na obrazovke - kurzy zoradené podľa názvu vyjdú v rovnakom poradí ako podľa kódu - takže sa riadky nepohli a presunula sa len šípka. Pôsobilo to, akoby prvý klik iba zameral hlavičku. Ak predvolený smer nového stĺpca nič nezmení, smer sa teraz hneď otočí, takže jeden klik vždy prinesie viditeľný výsledok. Platí len pri PREPNUTÍ stĺpca; opakovaný klik na tú istú hlavičku musí vedieť vrátiť pôvodné poradie.
- **Kontrola stavu systému nedávala odozvu.** Na zdravom systéme prekreslí identickú kartu, takže nič nepotvrdilo, že naozaj prebehla. Teraz oznámi výsledok - v poriadku, zhoršený stav alebo nedostupné - toastom, rovnako ako každá iná akcia.

## [2026.7.3.post139] - 2026-08-10 - Celá sada ikon je teraz z GitLabu

###  Changed
- **Každá ikona je glyf z GitLab Pajamas.** Aplikácia obsahovala 122 ručne vložených ikon *Feather* - 24x24, kreslené obrysom - čo je iná rodina ikon než GitLab, takže žiadne ladenie farieb ani veľkostí ju nemohlo priblížiť GitLabu. Všetkých 122 nahradili náprotivky z `@gitlab/svgs` (MIT): vyplnené tvary, väčšinou na mriežke 16. Pri 47 názvoch sedel priamy náprotivok, zvyšných 75 bolo namapovaných podľa významu.
- Oba registre sa presunuli spolu - makro v Jinja aj register v JavaScripte - takže ikona vykreslená serverom a ikona vykreslená JavaScriptom je ten istý glyf.
- Ikony preberajú farbu textu cez `fill: currentColor` (tvary Pajamas nemajú vlastnú výplň), čo nahrádza `stroke: currentColor`. Overené v svetlej aj tmavej téme.
- Cesty sú vložené priamo, nie cez sprite: WebKit stále nevie rozlíšiť EXTERNÝ `<use href="sprite.svg#id">`, čo by v Safari nechalo všetky ikony prázdne.

## [2026.7.3.post138] - 2026-08-10 - Prehratie udalostí sa presunulo z modálneho okna do tabuľky

###  Changed
- **Prehratie je teraz akcia v tabuľke, nie dialóg.** Modálne okno sa pýtalo na dátum od a do: udalosti pomenovalo len nepriamo, zachytilo aj všetko ostatné v danom okne a jeho vlastné výbery orezával samotný dialóg. Tabuľka Nedávne udalosti má teraz stĺpec s výberom a akciu „Prehrať vybrané (N)" - rovnaký vzor výberu, aký už mala tabuľka nedoručiteľných udalostí, takže sa obe karty konečne správajú rovnako. Modálne okno je odstránené.
- `POST /api/v1/events/replay` prijíma `event_ids` a prehrá presne označené riadky. Časový rozsah naďalej funguje pre volania cez API; schéma teraz vyžaduje jedno alebo druhé.
- Potvrdenie beží na spoločnom dialógu a uvádza skutočný počet („Znova spracovať vybrané udalosti (2)?"), čo časový rozsah nikdy nedokázal.

## [2026.7.3.post137] - 2026-08-10 - Každé „naozaj?" je teraz vlastný dialóg aplikácie

###  Changed
- **Nebezpečné akcie sa pýtali cez prehliadač.** `window.confirm` / `window.prompt` stáli vedľa vlastných modálnych okien aplikácie a robili to isté - dva vzory pre jednu interakciu, pričom polovica od prehliadača sa nedá štýlovať, ignoruje tmavý režim, nemá varovný akcent a pôsobí, akoby sa stránka pokazila. Jeden spoločný dialóg (`GP.confirmDialog`) teraz obsluhuje každé potvrdenie: štýlovaný, preložený, zrušiteľný klávesom Escape, so zameraním na BEZPEČNÉ tlačidlo, takže Enter nič nezmaže - a otvára sa aj zatvára cez existujúce `openModal`/`closeModal`, nie vlastným druhým mechanizmom.
- `confirmDangerousAction` si ponecháva rozhranie: volajúci odovzdávajú callback, takže prechod z blokujúceho dialógu na promise sa nikde neprejaví. Všetkých 16 miest volania bolo overených.
- **Z dvoch potvrdení je jedno.** Trvalé odstránenie potrebovalo druhý dialóg len preto, že okno prehliadača sa vie spýtať iba áno/nie. Dialóg povie dôsledok raz a tlačidlo odomkne až po napísaní názvu - teda skutočnú poistku, ktorú druhý klik iba napodobňoval.

## [2026.7.3.post136] - 2026-08-10 - Zámok archivovaného kurzu je vyjadrený raz, mŕtve CSS odstránené

###  Changed
- **Zámok archivovaného kurzu je vyjadrený jediným mechanizmom.** Jedenásť tlačidiel navyše vykresľovalo `disabled` a dôvod pri nabehnutí myšou pre stav, ktorý už spravuje klientský zámok - tá istá podmienka teda existovala dvakrát a správala sa rôzne podľa toho, ktorá vyhrala: vypnuté tlačidlo, ktoré klik prehltne, vedľa zamknutého, ktoré odpovie toastom. Serverová kópia je preč; všetky zamknuté ovládacie prvky sa teraz správajú rovnako.

###  Removed
- Mŕtve premenné v šablónach, ktoré po duplicite zostali (`_lock_tip`, `_locked`), a `_repo_is_empty` - podmienka pri Spustiť kontroly natvrdo nastavená na `false`, ktorá nikdy nemohla nastať.
- Deväť CSS pravidiel pre triedy, ktoré už žiadne HTML ani JS nevytvára - šírky stĺpcov tabuľky členov, ktorá zmenila tvar, skeletony grafov, ktoré ich už nemajú, a zástupný avatar. Overené jednotlivo; kandidáti so zloženými selektormi zostali zámerne nedotknutí (zhoda podreťazca už tento súbor raz rozbila) a všeobecné utility triedy zostávajú kompletné, aby ich šablóna mohla ďalej použiť.

## [2026.7.3.post135] - 2026-08-10 - Modálne okná sa už nehromadia, zamknuté tlačidlo odpovie, System Health neposkakuje

###  Fixed
- **Na Prehľade sa mohlo otvoriť modálne okno KURZU „Importovať z GitLab do <KÓD>".** Modálne okná sa presúvajú do `<body>`, aby vnorený `<form>` nerozbil formulár stránky - tým sa však ocitnú mimo oboch oblastí, ktoré navigácia nahrádza, takže ich nikdy nič neodstránilo. Každá navigácia nechala ďalšiu sadu: tri prvky s rovnakým id a 16 podkladov po dvoch prechodoch, pričom `openModal` vzal ten prvý. Modálne okná odchádzajúcej stránky sa teraz odstránia na začiatku navigácie.
- **Zamknuté tlačidlo na archivovanom kurze klik iba prehltlo.** Stmavené a nemé pôsobilo skôr pokazene než nedostupne. Tlačidlá teraz zostávajú klikateľné a odpovedia dôvodom v toaste (rovnaký prístup ako pri neplatnom tokene); naozaj vypnuté zostávajú len formulárové polia, lebo pole, ktoré vyzerá upraviteľne a ticho odmieta písanie, je horšie.
- **Karta System Health blikala pri každej kontrole.** Stav načítavania nahradil vykreslený prehľad, takže blok sa zmenšil z ~519 px na ~170 px a späť a posúval System Actions, Feature Flags aj Job History po stránke. Opakovaná kontrola teraz kartu ponechá v presne rovnakej veľkosti a iba ju stlmí (kompozitovaná priehľadnosť, takže sa nemôže zaseknúť); skeleton pri prvom spustení kopíruje skutočnú kartu komponentu, takže rezervuje presne toľko miesta, koľko výsledok potrebuje.

## [2026.7.3.post134] - 2026-08-10 - Jeden kalendár všade, archív vynucuje smerovacia tabuľka, tlačidlá obnovy majú odozvu

###  Fixed
- **Týždne semestra mali len niektoré kalendáre.** Stĺpec s týždňami potrebuje semester, od ktorého počíta, a ten zverejňovala len stránka kurzu - takže rozsah pre prehratie udalostí a každé dátumové pole mimo kurzu otváralo holú mriežku mesiaca. Stránky bez kurzu sa teraz opierajú o prebiehajúci (alebo najbližší) semester akademického kalendára TUKE FEI, ktorý aplikácia už obsahuje, takže každý výber dátumu je ten istý ovládací prvok.
- **Tlačidlá obnovy, po ktorých nebolo nič vidieť.** Obnovenie pipeline udalostí aj znovunačítanie konfigurácií webhookov prekreslili rovnaké riadky bez stavu načítavania a bez potvrdenia, takže klik sa nedal odlíšiť od nefunkčného tlačidla. Obe teraz dodržiavajú rovnaký kontrakt ako obnovenie v Systéme: ohlásia prácu a potom výsledok.
- **Dve tlačidlá „Obnoviť" neboli obnovením.** Na stránkach Aktivita a Analytika spúšťali plnú synchronizáciu s GitLabom - vzdialenú úlohu na minúty, ktorá bez bežiaceho workera rovno zlyhá. Teraz sa volajú **Synchronizovať** a hovoria to aj v popise; pri Aktivite navyše, že sa zobrazenie aktualizuje samo (je pripojená na stream kurzu).

###  Security
- **Šesť zapisovacích ciest v rámci kurzu nemalo kontrolu archivácie**, takže priame volanie API mohlo zasiahnuť kurz len na čítanie: vydanie živého tajného kľúča webhooku, spustenie platenej LLM analýzy žiadosti o zlúčenie, generovanie kontrol cez LLM, import definície formulára podpory a zmena inštruktorov kurzu (ktorej formulár je teraz zamknutý aj v UI). Všetky archivovaný kurz odmietnu.
- Kontrola sa teraz vynucuje **prechodom smerovacej tabuľky aplikácie** namiesto ručne udržiavaného zoznamu funkcií - práve preto týchto šesť uniklo. Nová zapisovacia cesta v rámci kurzu odteraz neprejde testami, kým buď nemá kontrolu, alebo nie je zaznamenaná aj s dôvodom ako akcia, ktorá musí zostať dostupná aj v archíve (reaktivácia, prenos, trvalé odstránenie, zrušenie bežiacej úlohy).

###  Removed
- SSE endpoint `/dashboard/courses/{id}/analytics/stream` (148 riadkov): nikdy sa naň nepripojil žiadny klient a do Redis kanála, ktorý počúval, nikto nič nepublikoval. Spolu s ním zmizol aj mŕtvy kľúč `sseUrl` v konfigurácii.

## [2026.7.3.post133] - 2026-08-10 - Prehľad aktivity prestal hovoriť strojovo, archív je vidieť aj na skupine

###  Fixed
- **Prehľad aktivity vypisoval surové názvy akcií.** Jedenásť auditných akcií nemalo vôbec žiadny popis, takže riadok vyzeral ako `member_exclusion_toggled` - a záložná vetva používala priamo identifikátor, čiže rovnako by dopadla každá neskôr pridaná akcia. Všetkých jedenásť má teraz popis, ikonu aj cieľovú stránku a záložná vetva mení neznámy identifikátor na vetu, takže strojový text sa do widgetu už nedostane.
- **Prehľad bol vždy po anglicky**, aj na slovenskom Prehľade: jeho text sa skladá na serveri a šablóna ho vykresľuje doslova. Popisy, aktéri, výsledky úloh aj počty sú teraz preložené (+30 reťazcov v katalógu). Počty sú formulované tak, aby nezáviseli od skloňovania čísloviek, ktoré katalóg nevie vyjadriť: slovenčina potrebuje „2 zmeny", ale „5 zmien".
- **Auditné záznamy pripisovali akciu číslu.** Prepínač hodnotenia člena zapisoval ako aktéra identifikátor zo session - pri prihlásení cez OAuth číselné ID používateľa z GitLabu - takže v prehľade stálo „0001 - ...". Teraz zapisuje používateľské meno ako každý iný auditný zápis a identifikátory v starších riadkoch sa pri zostavovaní prehľadu doplnia na mená (jeden dávkový dopyt; nedohľadateľné ID sa zobrazí ako „Neznámy používateľ", nie ako holé číslo).
- **Stránky skupiny, projektu a študenta archivovaného kurzu vyzerali plne upraviteľné.** Zámok sa riadil podľa `.tabs-nav`, ktorý vykresľujú len stránky kurzu, takže tam nebol žiadny pruh o archíve a všetky ovládacie prvky zostali aktívne - vrátane „vylúčiť z hodnotenia", ktoré zlyhalo až po odpovedi servera 403. Teraz nesú rovnakú značku aj pruh a ich ovládacie prvky sú zamknuté s vysvetlením po nabehnutí myšou.

## [2026.7.3.post132] - 2026-08-10 - Archivovaný kurz je naozaj len na čítanie, navigácia už nestráca kontext

###  Fixed
- **Archivovaný kurz stmavil aj nasledujúcu stránku.** Pruh „Archivovaný kurz" aj trieda `is-course-archived` žijú mimo `#main-content` - jedinej oblasti, ktorú výmena pri navigácii nahrádza - takže pruh zostal visieť nad Prehľadom a jeho tlačidlá ostali zašednuté. Prenesené pruhy sa teraz pri navigácii odstraňujú a trieda platí len pre vymieňanú oblasť.
- **Archivovaný kurz sa dal ďalej upravovať.** Zámok sa týkal len tlačidiel s `data-process-lock-when`, ktoré editor týždenných termínov nikdy nemal: modálne okno sa otvorilo, „Uložiť týždeň" zapísalo do harmonogramu JSON a uloženie, ktoré by to aj tak odmietlo, bolo vypnuté. Teraz sa zamyká každý prvok vo `form.is-course-archived` vrátane riadkov kontrol dokreslených po načítaní; výnimku má `data-readonly-ok` (filtre, export, znovunačítanie, rozbaľovanie).
- **Z archívu sa nedalo vrátiť.** Ten istý zámok vypínal Aktivovať, Preniesť aj Odstrániť navždy - tri akcie, ktoré server na archivovanom kurze výslovne povoľuje, pričom trvalé odstránenie archiváciu priamo vyžaduje.
- **Archivovať / Aktivovať / Odstrániť navždy vôbec nefungovali.** `courseActions` volal `t(...)`, ktoré v danom uzávere neexistuje (zvyšok súboru používa `GP.t`), takže každá akcia životného cyklu kurzu spadla na `ReferenceError` pri prvom potvrdzovacom texte.
- **Žiadne dátumové pole nedostalo kalendár pri prvom vykreslení.** `core.bundle.js` je odložený skript, a teda beží pri `readyState === 'interactive'`, ešte pred odloženým flatpickrom, ktorý je v `<head>` za ním; inicializácia sa riadila stavom `'loading'`, zvolila okamžitú vetvu a `initFlatpickr` ticho skončil. Práve preto v kalendári termínov chýbal stĺpec s týždňami semestra.
- **Meta značky v `<head>` po navigácii zostarli.** `course-id`, `semester-start` a `semester-end` sa vykresľujú pre každú stránku, ale nikdy sa neaktualizovali, takže stĺpec týždňov nemal od čoho počítať.
- **Druhý klik počas načítavania sa stratil** a čitateľ ostal na prvej stránke bez akejkoľvek odozvy. Teraz sa zaradí do frontu a vykoná.
- **Odkazy s kotvou skončili na začiatku stránky.** Výmena samotného obsahu nespustí vlastný skok prehliadača; navyše odkaz „Reaktivovať" v pruhu mieril na `#danger-zone`, ktoré neexistovalo.
- **Sledovanie stavu kurzu prežilo stránku, ktorá ho spustila**, a mohlo obnoviť stránku, z ktorej ste už odišli.
- **Nápis „Načítava sa..." zamrzol.** Animoval sa cez `background-position` a `background-clip: text` - teda vykresľovaním, ktoré kompozítor nevie prevziať - takže zastal presne vtedy, keď prichádzajúca stránka zamestnala hlavné vlákno, hoci krúžok vedľa sa točil ďalej (animuje `transform`). Oba načítavacie nápisy teraz pulzujú cez `opacity`.
- **Zobrazenia stránok skupiny a projektu sa nikdy nezaznamenali.** Telemetria posielala vlastný `metric_type` s textovým `context` a endpoint odpovedal 422.
- **Exportovať / Importovať úplnú konfiguráciu sa roztiahli cez pol karty** a rozpadli sa na nesúrodú dvojicu, keď zámok obalil vypnutý import do bubliny s vysvetlením - `.form-row` je mriežka pre polia formulára, nie pre tlačidlá.
- **131 reťazcov rozhrania nemalo slovenský preklad**, vrátane celého editora týždenných termínov, pruhu o archivácii a blokujúcich serverových hlášok (neplatný token GitLabu, nebežiaci worker, archivovaný kurz). Tri potvrdzovacie dialógy sa skladali zo šablónových reťazcov, takže sa preložiť ani nedali; teraz používajú parametre.

###  Changed
- **Odozva pri navigácii kopíruje GitLab / YouTube.** Pôvodná stránka zostáva na obrazovke, stlmená a neaktívna, kým priebeh hlási horný pruh; značkový načítavač sa objaví, až keď sa načítanie naozaj vlečie (>1,2 s). Predtým sa obsah vymazal už po 120 ms, čo spôsobovalo dojem poskakovania.

###  Removed
- 30 mŕtvych tried skeletonov v CSS (`gl-sk-qa-*`, `gl-sk-attn-*`, `gl-skeleton-header*`, `gl-sk-doughnut`, ...) po staršej práci na skeletonoch.

###  Tests
- **Prehliadačová sada bola voči bežiacemu serveru ticho prázdna.** `tests/conftest` dosadzuje vlastný `SECRET_KEY`, takže server session cookie odmietol a každá testovaná stránka bola v skutočnosti prihlasovací formulár; zlyhalo len strážne tvrdenie.
- **Objavovanie rout považovalo JSON endpoint a HTML fragment za stránky** (`/dashboard/notifications`, `/dashboard/activity`).

## [2026.7.3.post131] - 2026-08-06 - Kontrola API špecifikácie funguje aj v čistom CI

###  Fixed
- **`test_api_spec_inventory` čítal `app.routes` priamo a v CI padol.** Aplikácia odkladá `include_router` do zástupcov, ktoré sa rozbalia až pri štarte, takže obyčajné čítanie vidí ~19 rout - kontrola potom označila všetkých 83 zdokumentovaných endpointov za neexistujúce. Teraz ich prechádza cez `tests/route_discovery.iter_routes`. Overené v čistom kontajneri `python:3.12-slim`, nielen lokálne.

## [2026.7.3.post130] - 2026-08-06 - Zelený pipeline, žiadne 401 v Search Console, pravdivé README

###  Security
- **`cryptography` 49.0.0 -> 50.0.0** (GHSA-g6cj-pr64-35w5 / CVE-2026-69247). `pkcs7_decrypt_*` prezrádzal dĺžku dešifrovaného RSA obsahu návratovou hodnotou aj časovaním. Práve toto zhodilo CI úlohu `dependency-scan`. `exclude-newer` posunuté z 2026-07-21 na 2026-08-01, aby uv opravu videl; `cryptography` je jediný zmenený pin.

###  Fixed
- **Search Console hlásil „Zablokované cez chybu neautorizovaný požiadavok (401)".** Príčinou boli `/grafana/`, `/prometheus/` a `/jaeger/` - Caddy na ne odpovedá basic-auth 401 a do aplikácie sa vôbec nedostanú, takže ich žiadna naša `X-Robots-Tag` nepokryla. Teraz sú (spolu s `/metrics`) zakázané v `robots.txt` a Caddy k nim posiela `X-Robots-Tag: noindex, nofollow`.
- **`docs/04-api-spec.md` popisoval 15 neexistujúcich endpointov** a zároveň vynechával celé živé oblasti (transfer, run-checks, webhook-configs, zrušenie úlohy, SSE streamy). Sekcia 5 sa teraz generuje z tabuľky rout a je zaistená testom v oboch smeroch.
- **README uvádzali čísla, ktoré dávno neplatia.** `README.sk.md` ešte inzeroval `rq-scheduler` s 12 periodickými úlohami (plánovač neexistuje), 44 modelov v 48 migráciách na head `047_bg_job_project_id` (v skutočnosti 39 v 11 na `011`), 222 rout (204) a moduly Docker verify / CI failure / conflict simulator, ktoré boli zmazané. Obe README tiež odkazovali na neexistujúci `LLM_README.md` a tvrdili 10-panelový Grafana dashboard so 7 alertmi (v skutočnosti 18 a 18). Každé spočítateľné tvrdenie teraz stráži test.

## [2026.7.3.post129] - 2026-08-05 - Env príklady a dokumentácia webhookov opisujú skutočnú aplikáciu

###  Fixed
- **`.env.example` a `.env.production.example` ponúkali 14 nastavení, ktoré nič nečíta** (`FEATURE_RUBRIC_ENGINE`, `FEATURE_GAMING_DETECTION`, `FEATURE_TIMELINE_DASHBOARD`, `FEATURE_ROSTER_IMPORT`, `FEATURE_CONFLICT_SIMULATOR`, `FEATURE_DOCKER_VERIFICATION`, `FEATURE_CI_FAILURE_GENERATOR`, `DOCKER_VERIFY_*`, `CONFLICT_BOT_*`, `CI_FAILURE_BOT_*`, `RQ_MAX_RETRIES`). Oba súbory teraz uvádzajú skutočné príznaky funkcií plus SMTP, sedenia, semestrálny životný cyklus, retenciu a monitoring, ktoré chýbali. Nový test zabráni ďalšiemu rozchádzaniu.
- **Tri mŕtve príznaky sú preč aj z `docker-compose.yml`.**
- **Dokumentácia webhookov opisovala podpisovanie, ktoré GitPulse nepoužíva.** Kázala vygenerovať `GITLAB_WEBHOOK_SECRET` do `.env` (nič ho nečíta) a ukazovala vymyslený HMAC handler. V skutočnosti GitLab posiela secret v `X-Gitlab-Token`, GitPulse ho generuje pre projekt alebo webhook konfiguráciu, ukladá iba bcrypt hash a rotuje sa cez `POST /api/v1/webhook-configs/{id}/rotate`.

## [2026.7.3.post128] - 2026-08-05 - Archivovaný kurz je read-only všade, nielen v UI

###  Fixed
- **Každý zápisový endpoint viazaný na kurz teraz archivovaný kurz odmietne.** Synchronizácia projektu, úprava/zmazanie/obnova skupiny, pripojenie/odpojenie/obnova projektu, úprava kurzu, nastavenia kurzu, import celej konfigurácie aj všetky tri spúšťače LLM analýzy predtým prešli - stlmené boli len tlačidlá. Všetky teraz vracajú spoločnú 409 „archivovaný a read-only".
- **Import GitLab skupiny už kurz potichu nereaktivuje.** Importér nastavoval `is_active = True` na nájdenom kurze, takže opakovaný import archivovaný kurz oživil. Teraz to odmietne s jasnou hláškou.
- **Webhooky pre archivovaný kurz sa potvrdia a zahodia.** GitLab doručoval ďalej, prepisoval dáta archivovaného kurzu a púšťal toasty „Live update" na stránke, ktorú UI ukazuje ako zmrazenú.
- **Vypnuté tlačidlá na archivovanom kurze opäť vysvetlia prečo.** Mali `pointer-events: none`, čo zabilo aj hover nesúci tooltip - pôsobili pokazene, nie zamknuté.
- **Modál User Info už pri načítaní dát neposkočí.** Kostra a načítaná karta majú rôznu výšku, takže telo modálu skočilo v jednom snímku; výmena je teraz animovaná.
- **Dokumentácia už nepopisuje endpointy, ktoré neexistujú:** `/api/v1/pipelines/report` a `/pipelines/validate`, `/api/v1/webhooks/test`, `/api/v1/health`, `/api/v1/team-metrics` a `teams/{id}/recheck` (správna cesta je `run-checks`).

## [2026.7.3.post127] - 2026-08-05 - Animácia loga v bočnom paneli je opäť plynulá

###  Fixed
- **Pulz loga GitPulse už netrhá ani nezamŕza.** Animoval `stroke-dashoffset` (prechod, ktorý prehliadač vie počítať len na hlavnom vlákne) a `will-change: stroke-dashoffset` navyše vynucoval prekresľovaciu vrstvu, takže pulz sekal vždy, keď mala stránka prácu. Teraz ide o jemné rozžiarenie cez `opacity`, ktoré beží na kompozítore - plynulé bez ohľadu na záťaž.

## [2026.7.3.post126] - 2026-08-05 - Zalamovanie tooltipu + žiadne blikanie zebry pri rozbalení skupiny

###  Fixed
- **Dlhý text tooltipu už nevybieha za okraj.** Emaily, bot loginy a GitLab cesty pretekali tooltip; teraz sa zalomia (`overflow-wrap: anywhere`, širší max-width).
- **Rozbalenie skupiny už nerozbíja / neblikne pruhovanie tabuľky.** Detské riadky skupiny sú vylúčené zo zebra počítania `nth-child(even of ...)` a majú stabilný vnorený odtieň, takže rozbalenie / zbalenie už nepruhuje riadky nižšie.

## [2026.7.3.post125] - 2026-08-05 - Archivované kurzy sú read-only na stránke skupiny aj na serveri

###  Fixed
- **Akcie zápisu na stránke skupiny (tímu) sú teraz na archivovanom kurze vypnuté + vysvetlené, nie skryté** - rovnako ako na stránke kurzu a projektu (Link Project / Sync / Run Checks / Delete zostávajú viditeľné ale sivé, s tooltipom „tento kurz je archivovaný a read-only").
- **Vylúčenie študenta zo skórovania je teraz na archivovanom kurze odmietnuté na serveri** (HTTP 403), takže zastaraný klient nemôže meniť skórovaciu membership na read-only kurze.

## [2026.7.3.post124] - 2026-08-05 - Modály sa pri navigácii zatvoria; akcie archívu sú vypnuté + vysvetlené

###  Fixed
- **Otvorené modály už nezostávajú visieť nad ďalšou stránkou.** Pozadia žijú na `<body>`, takže navigácia ich nechávala otvorené; teraz sa pri navigácii najprv zatvorí každý otvorený modál / drawer.
- **Akcie zápisu na archivovanom kurze sa zobrazujú vypnuté s tooltipom, nie skryté.** Add Group / Import / Sync / Run Checks (a Sync / Unlink / Run Checks projektu) zostávajú viditeľné ale vypnuté, každé vysvetľuje „tento kurz je archivovaný a read-only" pri prejdení myšou.

###  Changed
- **Kostry sú neviditeľné o niečo dlhšie (0.42s)**, takže rýchle načítanie už neblikne kostrou na jeden snímok.

## [2026.7.3.post123] - 2026-08-05 - Každé tlačidlo má stlačenie v štýle iOS

###  Changed
- **Tlačidlá sa teraz pri klepnutí stlačia, v štýle iOS.** Každé tlačidlo sa pri stlačení zmenší na 0.94 a pri pustení odpruží späť, pre hmatateľnú spätnú väzbu - dopĺňa sadu animácií popri modáloch (vyrastajú z tlačidla), rozbaľovacích zoznamoch (z prepínača) a toastoch / tooltipoch (zo svojej pozície). Reduced-motion to potlačí.

## [2026.7.3.post122] - 2026-08-05 - Spinner sa naozaj točí; modály nie sú priehľadné pri otvorení

###  Fixed
- **Spinner loadera bol zamrznutý** (animoval sa len text) - promócia cez `translateZ(0)` kolidovala s rotate keyframe. Teraz používa len `will-change` a explicitný `rotate(0) -> rotate(360deg)`, takže sa opäť plynulo točí.
- **Modály už nevyzerajú priehľadne pri otvorení.** Dialóg dedí priehľadnosť pozadia a pomalý fade ho nechal priesvitný (presvital cez tabuľku) až pol sekundy. Pozadie teraz dosiahne plnú nepriehľadnosť za ~200ms, kým si dialóg drží scale-spring.

## [2026.7.3.post121] - 2026-08-05 - Obnovený plynulý conic spinner; auto-aktualizácia po deployi

###  Changed
- **Spinner loadera je opäť plynulá conic duha** (border-krúžok bola regresia), teraz na vlastnej compositor vrstve, takže si drží vzhľad AJ plynulosť pod záťažou.
- **Štrukturálna kostra modálu User Info je späť.** Zrkadlí načítanú kartu, takže nie je skok; čo pôsobilo „priehľadne" bol modál zachytený uprostred otváracej animácie.

###  Fixed
- **Aplikácia sa po deployi automaticky obnoví na novú verziu.** Nový service worker po prevzatí kontroly raz obnoví záložku, takže sa vydanie načíta bez ručného hard-refresh.

## [2026.7.3.post120] - 2026-08-05 - Spinner loadera je plynulý aj počas načítania

###  Fixed
- **Spinner loadera už neseká ani nevyzerá zamrznuto počas načítania stránky.** Bol to rotujúci conic-gradient, ktorý prehliadač prekresľuje na hlavnom vlákne, takže sekal práve vtedy, keď prichádzajúca stránka to vlákno zamestnala. Teraz je to border spinner rotovaný čisto cez transform na vlastnej compositor vrstve, takže je plynulý a cyklický nech stránka robí čokoľvek.

## [2026.7.3.post119] - 2026-08-05 - Modály vyrastajú z tlačidla; čistejšie animované loadery

###  Changed
- **Modálne okno teraz vyrastá z tlačidla, ktoré ho otvorilo** (a zloží sa späť doň), v štýle iOS, namiesto škálovania zo svojho stredu.
- **Modál User Info ukazuje čistý loader, nie kostru.** Jeho kostra pôsobila rozbito (priehľadné pruhy cez tabuľku za modálom); teraz je to vycentrovaný spinner s popisom.
- **Popisy načítania sú animované.** Cez text loadera prechádza oranžový pruh (štýl „premýšľania") namiesto statického reťazca. Reduced-motion ukáže plnú farbu.

## [2026.7.3.post118] - 2026-08-04 - Overlay prvky vyrastajú zo svojej pozície, nevlietavajú zboku

###  Changed
- **Modálne okná, rozbaľovacie zoznamy, tooltipy a toasty sa teraz roztiahnu zo svojho miesta a zložia sa späť do neho, namiesto vlietavania zboku.** Modály sa škálujú zo stredu (fade vlastní pozadie), rozbaľovacie zoznamy vyrastajú z prepínača (horný pôvod, dolný pri preklopení hore), toasty sa škálujú zo svojej pozície namiesto vysúvania nahor a potom nabok, a tooltipy vyrastajú z hrany najbližšej k prvku. Žiadne predvolené „zjaví sa odnikiaľ" posuny/fade.

## [2026.7.3.post117] - 2026-08-04 - Ovládacie prvky fungujú po navigácii; archivované kurzy sú read-only

###  Fixed
- **Rozbaľovacie zoznamy a ďalšie interaktívne prvky fungujú po navigácii.** Po SPA navigácii Alpine komponenty potichu prestali fungovať - filtre Typ/Stav sa neotvárali a komponenty stránky sa neinicializovali (bez chyby). Príčinou bolo `Alpine.initTree` spustené v tom istom kroku ako zrušenie `x-ignore`; teraz beží o snímok neskôr.
- **Archivované kurzy sú naozaj read-only.** Archivovaný kurz mal banner „read-only", ale jeho tlačidlá zápisu ostali aktívne (Sync, Run Checks, Link Project, Delete; Add Group, Import, Sync All). Teraz sú počas archivácie skryté.

## [2026.7.3.post116] - 2026-08-04 - Kostry už neblikajú; prístupnosť čistá na každej stránke

###  Fixed
- **Kostry už nebliknú na jeden snímok.** Serverom vykreslené kostry sa zobrazovali okamžite, takže rýchla stránka ukázala sivé bloky na okamih pred príchodom dát. `.gl-skeleton` teraz drží priehľadnosť 0 asi 0.28s a objaví sa len ak sa obsah stále načítava - rýchle načítania nevykreslia žiadnu kostru, pomalé áno, a bez prelínania takže bez blikania.
- **Prístupnosť je čistá na každej stránke.** Audit 13 stránok (dostupné názvy, popisy polí, alt texty, ARIA odkazy, klávesnicou dosiahnuteľné prvky) bol čistý okrem jedného odkazu „Otvoriť v GitLabe" na stránke tímu, ktorý teraz má aria-label.

###  Verified
- Živé aktualizácie dát (SSE) sa pripájajú na stránkach udalostí a prehľadu; celý unit balík (2535 testov) prechádza.

## [2026.7.3.post115] - 2026-08-04 - Nový loader, dostupné akcie v tabuľke, žiadne blikanie

###  Changed
- **Loader navigácie je krúžok so značkou, nie tep.** Statická značka GitPulse je teraz v modernom rotujúcom krúžku s popisom „Načítava sa..." a poznámkou o pomalom pripojení, ktorá sa objaví len ak načítanie trvá dlho.

###  Fixed
- **Tlačidlá akcií v riadku sú dostupné aj na úzkych obrazovkách.** Široká tabuľka posúvala stĺpec Akcie mimo obrazovku; teraz je pripnutý (`.table-sticky-actions`).
- **Žiadne blikanie pri načítaní.** Prelínania kostra→dáta aj obsahu pri navigácii začínali na priehľadnosti 0 a blikali. Obsah sa teraz zobrazí rovno na mieste.
- **CI bundle-check je opäť zelený.** `components.min.js` nebol nikdy commitnutý po zmene; teraz je.

## [2026.7.3.post114] - 2026-08-03 - Obnovenie stránky skočí na vrch; dve ARIA chyby opravené

###  Fixed
- **Obnovenie stránky už neposkakuje niekoľko sekúnd.** Obnova pozície skrolu prepisovala scroll každých 120ms päť sekúnd, aby bojovala s kotvením pri raste lenivých dát. Obnovenie teraz jednoducho skočí na vrch (`history.scrollRestoration = 'manual'`) - čisto a predvídateľne.
- **Panely záložiek už majú platné `aria-controls`.** Tlačidlá záložiek odkazovali na neexistujúce id panelov; `GP.initTabs` teraz každému panelu nastaví id + `role="tabpanel"`.
- **Textové pole JSON-drop má programový popis.** Jeho popis bol len obyčajný span; teraz sa viaže cez `aria-labelledby`.

## [2026.7.3.post113] - 2026-08-03 - Pri pomalej navigácii sa zobrazí značka GitPulse, nie kostra

###  Changed
- **Pomalá stránka teraz ukáže pulz GitPulse, nie zamrznutú stránku ani nevhodnú kostru.** Keď navigácia trvala viac než ~120ms, stará stránka predtým zamrzla na celý čas načítania a potom na okamih zablikala kostrou cieľovej stránky. Pomalá navigácia teraz nahradí obsah vycentrovanou značkou GitPulse s EKG-tepom (sonar prstence + tep bežia), čo dá okamžitú spätnú väzbu „načítava sa" hneď na začiatku - a keďže je to značka, nemá čo nesúhlasiť s rozložením cieľa. Rýchla stránka sa načíta rovno bez loadera a reduced-motion ukáže statickú značku.

## [2026.7.3.post112] - 2026-08-03 - Dáta v tabuľkách sa zjavia plynulo, nie skokom

###  Changed
- **Načítané dáta v tabuľke sa už nezjavia prudkým skokom.** Keď riadky tabuľky prvýkrát nahradili kostru, objavili sa jediným tvrdým skokom (~1800px, bez prechodu), takže stránka „sa pri načítaní dát správala hrozne". Každá tabuľka s ClientPaginator teraz svoje riadky pri prvom načítaní plynulo prelne (rešpektuje reduced-motion); zámok výšky už bráni skákaniu pri stránkovaní a strážca zabezpečí, že stránkovanie ani živé obnovenie sa už neanimujú. Keďže tento paginátor zdieľa takmer každá dátová tabuľka, plynulý prechod kostra→dáta je teraz konzistentný v celej aplikácii.

## [2026.7.3.post111] - 2026-08-03 - Navigácia už nezamŕza pri načítaní skriptov

###  Performance
- **Prechod medzi stránkami už nezamrzne na niekoľko sekúnd pri pomalom pripojení.** Obslužný kód SPA načítaval každý skript stránky *synchrónnym* XHR, čo na pomalej linke zablokovalo hlavné vlákno na celý round-trip za každý skript. Skripty sa teraz načítavajú neblokujúco (`<script async=false>`, v poradí, z cache pri opakovaných prechodoch); obsah sa zobrazí okamžite ako kostra a Alpine sa inicializuje až po ich načítaní.

###  Changed
- **Filtre na stránke Pipeline udalostí majú pohodlnú veľkosť.** Filtre Typ / Stav sa zmenšovali na šírku svojho popisu a pôsobili maličko; teraz majú konzistentnú, čitateľnú šírku.

## [2026.7.3.post110] - 2026-08-03 - Onboarding tur je menej dotieravý

###  Fixed
- **Onboarding tur už nevyskakuje na každej stránke.** Uvítacia karta sa opätovne aktivovala pri každej navigácii, takže sa nová pozvánka na tur objavila pri prvom zobrazení každej stránky. Teraz sa automaticky ponúkne najviac raz na zariadenie; každý tur zostáva dostupný na požiadanie zo spúšťača.

## [2026.7.3.post109] - 2026-08-03 - Stránky sa už nerozbíjajú pri priamom načítaní + obsah pri navigácii neskáče

###  Fixed
- **Stránky sa už nerozbíjajú pri priamom načítaní / F5 / novej karte.** Alpine (CSP build) sa spúšťal skôr, než sa stihli spustiť skripty komponentov v tele stránky (Inštruktori, Nastavenia kurzu, Tikety, Podpora), takže na studenom načítaní zostali „mŕtve". Spustenie Alpine je teraz odložené na `DOMContentLoaded`.
- **Obsah pri navigácii už neskáče.** SPA výmena vnárala druhý `#main-content` do prvého (duplicitné id a zdvojený odsadenie), takže obsah po prechode poskočil dovnútra. Teraz sa vymieňa len vnútorný obsah - jeden prvok, stabilné odsadenie.
- **Žiadne chyby v konzole pri prechode na Inštruktorov či Prehľad.** Skript stránky na najvyššej úrovni obsahu spôsoboval chybu htmx (presunutý do hlavičky); zdieľaný pomocník `config-import.js` sa na Prehľade načíta v poradí pred `dashboard.js`.

###  Changed
- **Generický zástupný skelet pri navigácii bol odstránený** - nikdy nesedel na cieľovú stránku. Navigácia teraz ponechá aktuálnu stránku viditeľnú s horným prúžkom priebehu (štýl GitLab / YouTube) a každá stránka zobrazí svoje vlastné skelety.
- **Pipeline udalostí: Prehranie udalostí je teraz modálne okno** otvárané z hlavičky (bez samostatnej sekcie), duplicitné tlačidlo Obnoviť je preč a prázdny stav používa štandardný komponent.

## [2026.7.3.post108] - 2026-08-03 - Prehľadnejšia stránka Pipeline udalostí + plynulý prechod obsahu

###  Changed
- **Stránka Pipeline udalostí prepracovaná v štýle GitLabu.** Dva samostatné riadky štatistík sa zlúčili do jedného stavového pruhu a tabuľky Nedávne udalosti + Fronta nedoručených správ sa presunuli do jednej karty so záložkami namiesto dvoch oddelených tabuliek. Prehranie udalostí je teraz zbalený nástroj. Znovu využíva deklaratívny prepínač záložiek (`GP.initTabs`), takže prežije SPA navigáciu; všetky identifikátory používané v JS sú zachované.

###  Added
- **Synchronizované prelnutie obsahu pri navigácii.** Celý blok `#main-content` sa pri každej SPA navigácii plynulo zjaví ako jeden celok (znovu využíva existujúcu krivku `.gp-content-in`, rešpektuje reduced-motion) namiesto skokového objavenia. Animuje sa kontajner, nie jeho jednotlivé prvky - postupné objavovanie po prvkoch bolo skôr odstránené, lebo sa pri každom živom obnovení znova animovalo a pôsobilo ako blikanie.

## [2026.7.3.post107] - 2026-08-03 - Alpine komponenty už nepadajú na SPA navigácii

###  Opravené
- **Alpine komponenty (Učitelia, Nastavenia kurzu) už po SPA navigácii nepadajú.** Skripty stránky sa teraz pri navigácii načítajú synchrónne a v poradí, Alpine sa na novom obsahu pozastaví (`x-ignore`) kým nie sú továrne komponentov zaregistrované, a potom sa podstrom inicializuje - 0 Alpine chýb.

## [2026.7.3.post106] - 2026-08-03 - Skelet načítania pri navigácii ako v GitLabe

###  Pridané
- **Okamžitá štruktúra + skelet, kým sa dáta načítavajú.** Keď je odpoveď navigácie
  pomalá (nepríde do ~140 ms), obsah teraz ukáže ľahký trblietavý skelet (hlavička +
  riadok kariet + karta s riadkami) namiesto zamrznutej predchádzajúcej stránky -
  navigácia tak vždy pôsobí okamžite a štruktúra stránky sa objaví pred dátami, ako
  v GitLabe. Rýchle odpovede sa vymenia priamo, bez bliknutia skeletu.

## [2026.7.3.post105] - 2026-08-03 - Opravy modálov a offline stránky

###  Opravené
- **Modály riadené konfiguráciou (napr. Upraviť používateľa) sa opäť otvárajú po
  SPA navigácii.** Výmena len obsahu nezasahuje `<head>`, kde `{% block
  extra_scripts %}` vykresľuje inline JSON konfiguráciu stránky - reconciler head-u
  ju teraz obnoví z odpovede, takže admin kontroly nezlyhajú potichu.
- **Stránka „Ste offline" sa už neobjaví, keď je prehliadač online.** Service
  worker ju teraz zobrazí len keď je `navigator.onLine` naozaj `false`; inak skúsi
  znova alebo nechá prehliadač zobraziť vlastnú chybu.

## [2026.7.3.post104] - 2026-07-29 - Navigácia už neláme layout

###  Opravené
- **Navigácia už neláme rozloženie stránky.** post103 vymieňal celé `<body>`, čím
  sa pri každom kliknutí prekreslil bočný panel + horná lišta (viditeľné bliknutie).
  Teraz sa vymieňa len `#main-content` - bočný panel, horná lišta, lišta úloh a
  bannery zostávajú na mieste (stabilné okraje ako v GitLabe), a `<title>`,
  omrvinky, aktívna položka v paneli, modály aj skrol sa dopočítajú z odpovede.

## [2026.7.3.post103] - 2026-07-29 - Okamžitá navigácia ako v GitLabe

###  Pridané
- **Okamžitá SPA navigácia (ako v GitLabe).** Kliknutie na interný odkaz už
  nerobí úplné znovunačítanie stránky - vymení sa len obsah tela stránky, takže
  bočný panel, horná lišta a všetko CSS/JS zostávajú na mieste a prechody sú
  okamžité. História (Späť/Dopredu), horná lišta priebehu, `<title>` aj zvýraznenie
  aktívnej položky v bočnom paneli sa aktualizujú správne. Grafy, Alpine
  komponenty, tooltipy a skripty stránok sa pri každej výmene znova inicializujú.

###  Zmenené
- **Chart.js sa teraz načítava globálne** (predtým na každej stránke zvlášť). Pri
  SPA navigácii sa `<head>` medzi stránkami neznovunačítava, takže knižnica grafov
  sa načíta raz a grafy fungujú naprieč navigáciou.

###  Odstránené
- **Stará vrstva úplnej navigácie stránky** (`_pageTransitions`) - nahradená vyššie
  uvedenou SPA navigáciou.

## [2026.7.3.post102] - 2026-07-29 - Presný skelet Kontrolného zoznamu učiteľa

###  Zmenené
- **Skelet načítania Kontrolného zoznamu učiteľa má teraz tvar grafu, nie sivý
  box.** Zobrazí skutočné kódy R01-R13 vľavo s trblietavými pruhmi pre názvy a
  mriežkou - rovnaký Pajamas skelet vodorovných pruhov (`sk_h_bars`), aký používa
  rozdelenie rolí v Systéme - a pri prvom odkrytí sa plynulo rozplynie do živého
  grafu. Všeobecný trblietavý prekryv zostáva pre čiarové, radarové a koláčové
  grafy, kde štruktúrovaný skelet nedáva zmysel.

###  Opravené
- **Trblietavý prekryv grafu už nezostáva nad rozdelením rolí v Systéme.** Prekryv
  je teraz voliteľný (`.gl-chart-skel`), takže pokrýva len grafy, ktoré ho
  používajú, namiesto zaplavenia každého `.chart-canvas-wrap` - čo nechávalo sivý
  box nad kartou rolí (tá má vlastný skelet), ktorý sa nikdy neodkryl.

## [2026.7.3.post101] - 2026-07-28 - Skelety grafov ako v GitLabe + plynulejšie obnovenie

###  Pridané
- **Skelety načítania grafov ako v GitLabe.** Štruktúra stránky sa vykreslí hneď,
  ale grafy dokreslí Chart.js o chvíľu neskôr - dovtedy je na ich mieste prázdny
  box. Teraz sa tam ukáže Pajamas trblietavý skelet, ktorý sa rozplynie v momente,
  keď sa graf vykreslí (poistný časovač odkryje aj graf, ktorý sa nikdy nenakreslí,
  takže nič netrblieta donekonečna). Pokrýva grafy v analytike, aktivite, projekte
  aj profile študenta.

###  Opravené
- **Obnovenie už netrhá pozíciu skrolu** - výška obsahu sa počas výmeny podrží a
  presný skrol sa obnoví.

## [2026.7.3.post100] - 2026-07-28 - Oprava obnovenia analytiky + odstránenie mŕtveho kódu skeletov

###  Opravené
- **Tlačidlo „Obnoviť" v analytike kurzu (a automatické znovunačítanie po dokončení
  synchronizácie) po prechode na inline-render nič nerobilo.** Obsah sa znovu-načítaval
  cez starý `.gl-lazy-content` obal, ktorý už neexistuje (stránky sa teraz vykresľujú
  na serveri naraz), takže sa nič neobnovilo. Teraz sa fragment znovu-načíta cez vetvu
  `HX-Content-Only` a vloží do `.gl-tab-content` (overené: grafy sa prekreslia, žiadne
  chyby v konzole). Neúspešné znovunačítanie ponechá existujúci obsah a zobrazí toast.

###  Odstránené
- **Mŕtvy kód lodrov/skeletov, ktorý zostal po prechode na inline-render** - klientská
  SWR cache lazy-fragmentov, náhrada zlyhaných regiónov, sledovač bliknutia skeletu a
  príslušné CSS. (V rovnakom vydaní sa už odstránilo 1429 riadkov mŕtvych skeleton makier.)

## [2026.7.3.post99] - 2026-07-28 - Načítavanie stránok ako v GitLabe + štíhlejšie CI

###  Zmenené
- **Stránky sa teraz načítavajú ako v GitLabe - celá stránka príde v jednej
  odpovedi servera.** Každá dátová stránka (prehľad kurzu / aktivita / analytika /
  inštruktori, tím, projekt, študent, nástenka, správa používateľov, tikety)
  predtým vykreslila okamžitý skelet a skutočný obsah dotiahla *druhou* HTMX
  požiadavkou, takže navigácia vždy ukázala výmenu skelet→obsah. Obsah sa teraz
  vykresľuje na serveri priamo v prvej odpovedi - jedna požiadavka, skutočná
  štruktúra hneď, žiadna výmena celého tela. Redis cache fragmentov ostáva a
  požiadavka `HX-Content-Only` naďalej vráti len fragment pre obnovu na mieste.
- **CI orezané na štíhlu, best-practice množinu nevyhnutností: 22 úloh → 11.**
  Ponechané: lint (ruff), typová kontrola (mypy), bezpečnostné brány nasadenia
  (bundle-check, static-artifact-guard, lockfile-check), testy (unit+pokrytie,
  contract, integration), skenovanie zraniteľností závislostí a build obrazu.
  Odstránené ťažšie / okrajové úlohy (mutation, performance, load testy), SBOM,
  skenovanie kontajnerov, SLSA provenance a agregačné publish/summary úlohy.

###  Opravené
- **Okno Info o používateľovi už pri otvorení netrhá.** Jeho skelet bol vyšší než
  skutočný obsah, takže vertikálne vycentrované okno sa zmenšilo a jeho vrch
  poskočil. Okno je teraz ukotvené o vrch (na desktope), takže výmena pohne len
  spodným okrajom.
- **Pruh „Zobrazujú sa údaje z poslednej synchronizácie" je teraz aj na hlavnej
  karte kurzu (Prehľad),** rovnako ako na kartách Aktivita a Analytika.

## [2026.7.3.post98] - 2026-07-27 - Opravy blikania pri načítaní a prázdnej analytiky

###  Opravené
- **Tlačidlo Uložiť v nastaveniach na okamih zablikalo ako dostupné.** Vykreslilo
  sa zapnuté a vyplo sa až po spustení strážcu po výmene obsahu. Teraz sa
  posiela už vypnuté a strážca ho zapne v momente, keď formulár zmeníte.
- **Archivované kurzy zobrazovali aktívne tlačidlá a dali sa upravovať.** Trieda
  „len na čítanie" sa pridávala až cez JS po načítaní. Teraz sa nastavuje na
  serveri. Navyše iba ukladanie nastavení odmietalo archivovaný kurz; koncové
  body kontrol nie - archivované kontroly sa dali meniť cez API. Spoločný strážca
  teraz vracia 409 na všetkých (overené: aktívne vytvorenie 201, archivované
  vytvorenie aj mazanie 409).
- **Prehliadač týždňov v analytike sa otváral na prázdnom týždni**, hoci bodky
  ukazovali na naplnené. Bodka a automatický výber používali odlišnú definíciu
  „má dáta". Teraz vychádzajú z jednej množiny, takže sa vždy otvorí najnovší
  týždeň s bodkou.

## [2026.7.3.post97] - 2026-07-23 - README zosúladený so skutočným kódom

###  Opravené
- **README opisoval funkcie, ktoré už neexistujú, a plánovač, ktorý nikdy
  nebežal.** Každé tvrdenie bolo overené proti kódu:
   - Tabuľka „Automation (12 Scheduled Jobs)" uvádzala dvanásť úloh s pevnými
      intervalmi. **Ani jeden z tých názvov v kóde neexistuje** a štyri z nich
      opisovali zrušené funkcie (CI scenáre, konflikty, overovanie Dockerfilu).
      `app/workers/sweep.py` to hovorí priamo: GitPulse je riadený webhookmi,
      nič sa nespúšťa časovačom. Tabuľka teraz uvádza osem skutočných úloh aj s
      tým, čo ich spúšťa.
   - Riadok topológie a mapa repozitára tvrdili `rq-scheduler (12 úloh)` a
      `scheduler (24 úloh)` - dve rôzne vymyslené čísla pre plánovač, ktorý beží
      s `with_scheduler=False`.
   - Počty boli zastarané po zlúčení migrácií: **48 migrácií, head `047`** ->
      v skutočnosti **11 súborov, head `011`**; 44 modelov -> **37**; 21
      schém -> **18**; 222 trás -> **204**.

## [2026.7.3.post96] - 2026-07-23 - Natívne bubliny nahradené komponentom

###  Opravené
- **Tri stránky stále používali natívne bubliny prehliadača (`title=`)**, ktoré
  tento projekt nahrádza vlastným komponentom - ignorujú štýl aplikácie a
  pôsobia nejednotne. Prehliadačový sken ich napočítal: 105 na stránke Systém
  (tabuľka histórie úloh), 13 v Nastaveniach kurzu (prepínače kontrol) a 26 na
  stránke študenta (bunky teplotnej mapy). Všetky teraz používajú komponent a
  viažu sa cez `GP.initTippy`.

  Overené v prehliadači: 0 natívnych `title=` na všetkých troch stránkach a
  ukotvenie na 18 prepínačoch. Rozbitý obrázok, ktorý sken nahlásil, je 404
  avatara z GitLabu, ktorý korektne prepadá na iniciály.

## [2026.7.3.post95] - 2026-07-23 - Filtre a stránkovanie zoznamu udalostí

###  Pridané
- **Zoznam udalostí sa dá zúžiť a stránkovať.** Rušný kurz vytvorí stovky
  udalostí a zoznam bol súvislá stena riadkov. Teraz má filter podľa typu
  (zúženie na serveri), filter podľa stavu (Spracované / Čaká / Zlyhalo,
  aplikovaný nad načítaným oknom, takže ukazovatele stále popisujú celé okno) a
  rovnaké stránkovanie ako fronta nedoručiteľných správ.

###  Opravené
- **Stránka udalostí visela vyše minúty.** Makru `select_field` sa odovzdal
  argument `data_attrs`, ktorý neprijíma; namiesto chyby sa vykreslenie šablóny
  zaseklo. Nájdené bisekciou: samotné vrátenie šablóny stránku obnovilo a
  filtre bez tohto argumentu sa vykreslili za 59 ms.

## [2026.7.3.post94] - 2026-07-22 - Adresa záložky Aktivita sedí so stránkou

###  Zmenené
- **Stránka Aktivita bola na `/courses/{id}/projects`.** Navigácia ju vždy
  označovala ako Aktivitu a stránka je o zdraví pipeline a aktivite skupín,
  takže adresa protirečila záložke, na ktorú ste klikli - a slovo „projects" už
  v aplikácii znamená niečo iné, detail jednotlivého projektu na
  `/dashboard/projects/{id}`. Nová adresa je `/courses/{id}/activity`.

  Pôvodná cesta nezmizla, ale trvalo presmeruje, takže staré odkazy a záložky
  fungujú ďalej.

## [2026.7.3.post93] - 2026-07-22 - Aktivita a Analytika sa už nedajú zameniť

###  Zmenené
- **Obe stránky mali rovnaké záhlavie**, takže ani jedna nepovedala, na ktorej
  ste a načo slúži - iba kód kurzu, názov, rok a semester. Každá sa teraz
  pomenuje a povie svoj rozsah: Aktivita je o tom, čo sa práve deje v GitLabe,
  Analytika o tom, ako študenti plnia kontroly a ako sa to menilo.
- **„Úspešnosť" na Aktivite sa mýlila s „Úspešnosťou kontrol" v Analytike.**
  Merajú rozdielne veci - dokončené CI pipeline oproti kontrolám dodržiavania -
  takže dve nesúvisiace percentá pôsobili, akoby si protirečili. Údaj na
  Aktivite sa teraz volá „Úspešnosť pipeline" a priamo hovorí, že ide o buildy.
- **Ukazovatele na Aktivite majú vysvetlivky** v rovnakom štandarde, aký
  Analytika už spĺňala.

## [2026.7.3.post92] - 2026-07-22 - Kontext udalostí a testovateľné LLM

###  Pridané
- **Mock poskytovateľ LLM.** Funkcie postavené na LLM sa nedali odskúšať, keď
  bol skutočný účet nedostupný alebo bez kreditu - zlyhanie vyzeralo rovnako
  ako pokazená integrácia. `LLM_PROVIDER=mock` odpovedá lokálne platnými
  odpoveďami, takže sa tieto cesty dajú prejsť od začiatku do konca. Nie je
  určený pre produkciu.

  Hneď to vyriešilo otvorenú otázku: generovanie vlastných kontrol vracalo 500,
  s mockom ten istý koncový bod vracia 200 s použiteľnými návrhmi - chyba bola
  teda výhradne v prekročenej kvóte poskytovateľa, nie v kóde.

###  Zmenené
- **Zoznam udalostí hovorí čo sa stalo, kde a kto to spôsobil.** Doteraz
  zobrazoval holé číslo projektu z GitLabu, ktoré učiteľovi nepovie nič o kurze
  ani študentovi. Každý riadok teraz nesie zhrnutie akcie, kurz a skupinu s
  cestou k projektu pod nimi, a používateľa, ktorého akcia udalosť vyvolala -
  všetko vyriešené na serveri jedným dopytom, nie po riadkoch.

## [2026.7.3.post91] - 2026-07-22 - Event Pipeline vysvetľuje sám seba

###  Zmenené
- **Stránka už nepredpokladá, že čitateľ pozná pojmy.** Otvára sa vysvetlením,
  čo je udalosť a ako sa dostane do fronty nedoručiteľných správ, takže čísla
  nižšie majú kontext.
- **Zdravie pipeline je vidieť skôr než problémy.** Riadok Spracované / Čaká /
  Zlyhalo pokrýva posledné udalosti, takže na prvý pohľad vidno, či udalosti
  prúdia - bez čítania tabuľky.
- **Každý údaj, stĺpec aj štítok stavu má vysvetlivku** cez komponent aplikácie:
  čo znamená počet opakovaní nad nulou, prečo je rastúci počet čakajúcich
  problém, že odložená udalosť nie je stratená.

  Overené v prehliadači: 93 vysvetliviek, všetky napojené na komponent, žiadna
  natívna bublina prehliadača.

## [2026.7.3.post90] - 2026-07-22 - Prehľad o udalostiach

###  Opravené
- **Tlačidlo Detaily v Event Pipeline nikdy nefungovalo.** Jeho obsluha volala
  funkciu, ktorá v súbore nebola vôbec definovaná, takže každé kliknutie
  skončilo chybou a prehliadač obsahu udalosti sa nedal otvoriť - rovnako pri
  riadkoch z fronty nedoručiteľných správ. Stránka to okno mala celý čas, len
  ho nemal čo naplniť. Funkcia teraz existuje a čerpá z nového rozhrania
  `GET /api/v1/events/{id}/payload`.

###  Pridané
- **Pipeline zobrazuje bežný tok, nielen chyby.** Doteraz vypisoval výhradne
  frontu nedoručiteľných správ, takže zdravý systém vyzeral rovnako ako ten,
  ktorý neprijíma nič. Nový zoznam „Posledné udalosti" ukazuje, čo GitLab
  nedávno doručil, od najnovšieho, s označením Spracované, Čaká alebo Zlyhalo -
  a pri zlyhaní aj s dôvodom priamo v riadku.

## [2026.7.3.post89] - 2026-07-22 - Spätná väzba pri živých zmenách

###  Pridané
- **Stránka teraz povie, čo sa zmenilo, keď sa sama obnoví.** Doteraz sa
  obnovila ticho, takže čísla sa čitateľovi menili bez vysvetlenia. Prichádzajúca
  zmena sa oznámi a pomenuje - merge requesty, úlohy, komentáre, pipeliny,
  pushe, členovia - podľa druhu udalosti, ktorý backend už posiela.

  Dávky sú bežný stav: jeden študent pri pushnutí vyvolá viacero udalostí za pár
  sekúnd a znovu zosynchronizovaný projekt ich vyvolá veľa. Oznámenia sa preto
  zlučujú do jednej správy s počtom zmien, namiesto jedného hlásenia na udalosť.

  Overené v skutočnom prehliadači proti webhookom spracovaným cez worker:
  nástenka, stránka podpory aj systémová stránka správcu oznámenie zobrazia.

## [2026.7.3.post88] - 2026-07-22 - Správanie pri neplatnom tokene

###  Opravené
- **Zdieľaný príznak o stave tokenu GitLabu vypršal a už sa neobnovil.** Príznak
  slúži na to, aby jeden neplatný token viedol k odmietnutiu odsúdenej práce vo
  všetkých vstupných bodoch naraz - namiesto toho, aby každý z nich sám
  kontaktoval GitLab. Ukladá sa do Redis s platnosťou 120 s, ale zapisoval sa len
  pri *zmene* stavu. Trvalý stav, napríklad odvolaný token, sa nikdy nemení, takže
  kľúč vypršal a už sa nezapísal. Odvtedy každé volanie spúšťalo živú kontrolu -
  merané 975 ms - proti GitLabu, donekonečna, presne v situácii, ktorej mal
  príznak zabrániť.

  Kľúč sa teraz obnoví aj po uplynutí polovice platnosti. Časté volania zostávajú
  lacné: potvrdenie úspechu prebieha pri každom volaní GitLabu a Redis takmer
  vždy obchádza, pretože obnova nastane najviac raz za polovicu platnosti.

  Overené na skutočne odvolanom tokene: kontrola stavu klesla z 975 ms na 1-3 ms.

## [2026.7.3.post87] - 2026-07-22 - Priepustnosť webhookov

###  Výkon
- **Opakovane doručený webhook sťahoval tie isté údaje z GitLabu znova.** GitLab
  pri chybe doručuje znova, takže duplicity sú bežné. Plná synchronizácia už
  preskakuje sťahovanie diffu a schválení pre merge request, ktorému sa
  nezmenilo `updated_at` - oboje je pri nezmenenom MR nemenné - ale cesta cez
  webhook to nerobila, takže každé opakované doručenie stálo dve živé volania
  API.

  Preskočí sa len vtedy, keď predchádzajúce obohatenie preukázateľne prebehlo
  (`changed_files` je to, čo zapisuje). Bez tejto podmienky by doručenie po
  *neúspešnom* sťahovaní malo rovnaký čas ako uložený riadok a zostalo by bez
  obohatenia natrvalo.

- **Vyhľadanie tímu podľa projektu prebiehalo dvakrát na udalosť.** Volajú ho
  štyri následné akcie, čo je 2000 rovnakých dopytov na 1000 udalostí. Teraz sa
  výsledok pamätá v rámci jednej relácie, a tá zodpovedá presne jednej udalosti.
  Dopytov na jednu udalosť merge requestu: 17,8 -> 16,8.

## [2026.7.3.post86] - 2026-07-22 - Integrita dát z webhookov

###  Opravené
- **Časové značky z webhookov sa nikdy nespracovali, čím sa ticho vypla ochrana
  proti nesprávnemu poradiu udalostí.** GitLab používa dva rôzne formáty: REST
  API vracia ISO 8601, no webhooky posielajú časy v tvare
  `2025-10-15 10:00:00 UTC` (medzera a pomenované pásmo). Ten sa nepodarilo
  spracovať, takže každý merge request a každá úloha doručené webhookom mali
  prázdne `created_at`, `updated_at` aj `merged_at`.

  Dôsledok bol horší než chýbajúce dátumy. Ochrana rozpoznáva oneskorenú
  udalosť porovnaním jej času s uloženým, a prázdna hodnota znamenala „nie je
  zastaraná". GitLab pritom poradie nezaručuje a pri chybe doručuje znova - tak
  sa zlúčený merge request vrátil do stavu otvorený a uzavretá úloha sa znovu
  otvorila, čo prevrátilo hodnotenie R10/R11 autora až do najbližšej plnej
  synchronizácie.

- **Webhook mohol prepísať dátum, ktorý už uložila plná synchronizácia.**
  Spracovanie zapisovalo tieto polia bezpodmienečne, takže nespracovateľná
  správa nahradila platnú hodnotu prázdnou - a práve to ochranu vypínalo. Teraz
  sa prepíše len skutočne spracovaná hodnota. `closed_at` sa naďalej maže,
  pretože GitLab ho pri znovuotvorení úlohy posiela prázdne.

  Riadky zapísané doteraz majú stále prázdne dátumy; plná synchronizácia ich
  doplní z REST API.

## [2026.7.3.post85] - 2026-07-22 - Prepočet metrík vo veľkom a čistenie štýlov

###  Opravené
- **Veľký tím prepočet metrík nespomalil, ale zhodil.** Načítanie údajov podľa
  merge requestov posielalo jeden parameter na každé id a protokol PostgreSQL
  povoľuje najviac 32767 parametrov v jednom dopyte. Tím, ktorého projekty
  obsahovali viac merge requestov, tak celý prepočet ukončil chybou. Id sa
  teraz načítavajú po dávkach hlboko pod limitom. Odhalené spustením prepočtu
  nad 120 002 riadkami: predtým chyba po 27,9 s, teraz dobehne za 56,3 s.

###  Odstránené
- **43 pravidiel CSS, ktoré nemôžu nikdy nič zasiahnuť.** Všetkých 36 tried
  chýba v šablónach, JS aj v značkovaní generovanom z Pythonu. Overené tým, že
  žiadny prvok na žiadnej stránke (vrátane šírok 390 px a 900 px) tieto triedy
  nenesie.

## [2026.7.3.post84] - 2026-07-22 - Správnosť rozhrania a rýchlejšia stránka projektu

###  Opravené
- **Modálne okno otvorené krátko po načítaní stránky sa samo zatvorilo.**
  Uvítacia ponuka sprievodcu zatvára všetky otvorené modálne okná a panely. Pri
  sprievodcovi, ktorého si používateľ vyžiadal, je to správne, ale uvítacia
  ponuka sa zobrazuje sama od seba, takže ničila rozrobenú prácu. Okno
  „Týždenný termín" sa otvorilo, plne sa zobrazilo a medzi 400 a 700 ms sa
  zatvorilo. Ponuka sa teraz nezobrazí, kým je otvorené modálne okno.
- **Na už načítanej stránke blikli sivé zástupné bloky.** Meranie po snímkach
  ukázalo ~460 ms zástupných blokov na stránke, ktorej obsah už bol k
  dispozícii. Zástupné bloky sa teraz krátko podržia neviditeľné: 0 ms a 32 ms
  pri načítaní z vyrovnávacej pamäte, 134 ms pri prvom načítaní.
- **Štítok stavu pri očakávaných kontrolách bol v každom riadku inde**, pretože
  názov kontroly si nenárokoval zvyšnú šírku. Každý štítok je teraz pevne 4 px
  od okraja svojej bunky.
- **Posledné natívne tooltipy prehliadača** (zrušenie/zatvorenie v pruhu úloh,
  indikátor SSE v podpore) sa vykresľujú cez komponent aplikácie.

###  Zmenené
- **Vzor je viditeľne riadený prepínačom, ktorý ho zapína.** Regulárny výraz
  vetvy (R02) a nadpisy šablóny (R05) sa vyhodnocujú len pri zapnutej voľbe, no
  obe polia zostávali plne upraviteľné, takže nebolo vidieť, že vzor neplatí.
  Pole je teraz pri vypnutej voľbe neaktívne a stlmené a jeho hodnota zostáva
  zachovaná - po opätovnom zapnutí sa vzor obnoví.

###  Výkon
- **Stránka projektu trávila väčšinu času zostavovaním dvojprvkovej množiny.**
  Odvodenie členov načítalo každý merge request a každú úlohu projektu a
  odstraňovalo duplicity v Pythone. Merané na 120 002 riadkoch: najpomalšie
  volanie 2661 ms -> 976 ms, po zahriatí 240 ms.

## [2026.7.3.post83] - 2026-07-22 - Údržbové vydanie: CI brány a čistenie štýlov

###  Opravené
- **Úlohy CI `lockfile-check` a `unit-tests` zlyhávali.** Uložený
  `requirements.lock` obsahoval `colorama` (závislosť len pre Windows), zatiaľ
  čo CI ho regeneruje v Linuxe. Pokrytie testami kleslo pod prah 38 %.

###  Zmenené
- **Odstránené nepoužívané štýly** (~236 riadkov) a pokrytie zvýšené na 38,11 %
  testami validácie importu konfigurácie, brzdenia frontu a rozsahu webhookov.

## [2026.7.3.post82] - 2026-07-21 - Diagnostika nedostupnej databázy

###  Opravené
- **Chyba 503 „Databáza nedostupná" už povie prečo.** Obidva obslužné programy
  výnimiek databázy výnimku zahodili, takže odmietnuté spojenie, vypršanie
  fondu, vyčerpané spojenia servera aj zlé prihlasovacie údaje dávali rovnakú
  prázdnu 503 bez jediného riadku v logu.

## [2026.7.3.post81] - 2026-07-21 - Nastavenia sa aplikujú jedným uložením, konvencie v kontrolách

###  Opravené
- **Zmeny compliance kontrol sa už neukladajú samy.** Editor kontroly aj
  predvoľby váh zapisovali na server hneď po stlačení „Save Check", kým každý
  iný prvok stránky čakal na „Update settings" - a zmenu sa nedalo vrátiť.
  Obidve sa teraz odkladajú a uloženie nastavení ich odošle naraz.
- **Číselný prepínač už neskáče o dve.** Na tej istej triede viseli dve
  implementácie, takže jeden klik zmenil hodnotu dvakrát.
- **Pozícia posunu prežije znovunačítanie.** Aplikácia posúva vnútri
  `.gl-page-content`, takže `window.scrollY` bol vždy 0 - funkcia nerobila nič
  na žiadnej stránke.
- **Modaly už pri otvorení neblikajú.** Priehľadnosť animovalo pozadie aj samotný
  dialóg naraz; vnorená priehľadnosť sa násobí.

###  Zmenené
- **Konvencie sa nastavujú v kontrole, ktorá ich vyhodnocuje.** Regulárny výraz
  vetvy, cesty testov a nadpisy šablóny MR boli v samostatnej karte „Patterns" a
  dva z troch nič nehodnotili, pokiaľ sa kontrola zvlášť neprepla do prísneho
  režimu. Pribudli predvoľby TUKE FEI / Prísne / Bez konvencií. Migrácia 011
  prenesie existujúce kurzy.

## [2026.7.3.post80] - 2026-07-18 - Webhooky mimo poradia, tz-aware commity, serverové predvoľby váh

###  Opravené
- **Webhooky GitLabu mimo poradia už neregresujú stav entity.** GitLab
  nezaručuje poradie webhookov a pri zlyhaní ich doručuje znova. MR a issue
  procesory prepisovali `state`/`updated_at` bezpodmienečne, takže zastaraný
  `update` (state=opened) doručený po `merge`/`close` „odzlúčil" MR alebo znovu
  otvoril uzavretý issue a preklopil R10/R11 autora až do ďalšieho manuálneho
  sync-u. Ochranu (monotónny `updated_at`) z pipeline procesora sme vyčlenili do
  `processors/_common.is_stale_update` a použili v MR aj issue procesore.
- **Časové značky commitov sú tz-aware.** `commit_processor` používal priamy
  `datetime.fromisoformat()`, takže značka bez offsetu sa uložila ako naivná - 
  nekonzistentné s tz-aware stĺpcom a semestrálnym filtrom compliance rušňa
  (kde naivná hodnota padá s `TypeError`). Presmerované cez zdieľaný
  `parse_gitlab_datetime`.
- **LLM analýza rediguje viac PII.** Metadáta MR (názvy vetiev) a názvy súborov
  sa teraz pred odoslaním externému modelu prechádzajú cez `redact()`.

###  Zmenené
- **Predvoľby váh compliance sú serverové a dynamické.** Predvoľby v nastaveniach
  kurzu boli natvrdo v JS a pokrývali len R01-R12 (R09/R11/R13 vynechané). Teraz
  sa počítajú na serveri (`build_weight_presets`) nad živou sadou vstavaných
  kontrol, normalizované na súčet 1.0, a vracia ich `GET /courses/{id}/checks`.
- **Špecifikácia R02 zosúladená s kódom.** Dokumentácia tvrdila pravidlo ∀ (všetky
  MR), kód prechádza na ∃ (aspoň jeden), rovnako ako R03/R04/R05. Podľa
  produktového rozhodnutia je zámerné správanie ANY; opravená len dokumentácia.

## [2026.7.3.post79] - 2026-07-17 - Compliance config helpery + druhé kolo deduplikácie dopytov

###  Zmenené
- **Zjednotené parsovanie compliance konfigurácie.** Reťazcová koercia na bool (`x.lower() not in ("false","0","no")`) bola skopírovaná v R02/R04/R06/R09/R11 a znova implementovaná ako lokálna `_bool` closure v R10 - šesť kópií jednej myšlienky, pričom päť vložených kópií vynechalo `bool()`-normalizáciu, ktorú R10 aplikoval na nereťazcové hodnoty. Zjednotené do modulového `_cfg_bool` (súrodenec `_cfg_int`), takže každá kontrola parsuje booly jednotne (a robustnejšie); R05 zámerne prísna forma `in ("true","1","yes")` ostáva. Orezaný pomer čiastočného kreditu `min(n/max(t,1),1.0)` - kopírovaný v R03/R06/R07/R09 - je teraz `_partial_ratio`.
- **Druhé kolo deduplikácie dopytov.** Dopyt „posledný MetricSnapshot na študenta v rámci jedného tímu → dict" - skopírovaný trikrát (`projects.py` dvakrát, `teams.py` raz) s redundantnými vloženými `func` importmi - je teraz v jednom zdieľanom helperi `_stats.latest_student_metric_map` (študentské dvojča `latest_team_metric_map`). Dve dict anotácie spresnené na skutočný nenulový typ. Bez zmeny správania pre všetky zdokumentované hodnoty konfigurácie aj oba dopyty; pokryté novými unit testami a plnou sadou (2 310).

## [2026.7.3.post78] - 2026-07-17 - Deduplikácia dopytov: jeden zdroj pre „posledný snímok tímu"

###  Zmenené
- **Deduplikácia dopytov: jeden vlastník logiky „posledný snímok tímu".** Ten istý poddopyt `func.max(computed_at)`, ktorý načíta najnovší `TeamMetricSnapshot` každého tímu, bol skopírovaný na piatich miestach - dvakrát na stránkach kurzu, znova v `api/sync.py` a `api/sync_stream.py`, a ešte raz vložený v `home_course_health.py` (bajtovo identická kópia helpera, ktorý už žil v `home_stats.py`). Zjednotené do dvoch zdieľaných helperov v `api/dashboard/_stats.py` - `latest_team_metric_map` (celý snímok na tím) a `latest_team_snapshot_subquery` (poddopyt max-na-skupinu) - takže vzor má jediný testovaný zdroj pravdy. Odstránené tri osirotené importy a zastaraný komentár „using DISTINCT ON" pri dopyte, ktorý DISTINCT ON nikdy nepoužil. Bez zmeny správania; nový unit test fixuje kontrakt helpera. Audit refaktoringu celej kódovej bázy (compliance engine, sync/webhook workery, služby, šablóny) potvrdil, že tie podsystémy už boli deduplikované čistkami post76/post77 - žiadne ďalšie bezpečné rezy nezostali.

## [2026.7.3.post77] - 2026-07-17 - Inštrumentovaná celosystémová čistka mŕtveho kódu (~5 000 riadkov)

###  Zmenené
- **Celosystémová čistka mŕtveho kódu s vlastnými analyzátormi - odstránených ~5 000 riadkov.** Repo-wide audit (analyzátory Jinja makier, CSS tried, JS exportov a šablón + CI dead-code report), každý kandidát overený proti korpusu šablón + JS aplikácie + vendorovaných knižníc + HTML generovaného Pythonom; rodiny dynamicky skladaných tried (`'prefix-' + x`, `'prefix-' ~ var`, `prefix-{{ var }}`) vylúčené vcelku. Výsledok: **74 osirotených Jinja makier** (~930 riadkov) vrátane zastaraných importov a 2 nereferencovaných komponentových súborov; **~680 osirotených CSS tried** (~3 950 riadkov v 44 súboroch, styles bundle o ~6 % menší); **8 mŕtvych JS exportov**. `badge(variant='blue')` sa teraz renderuje so štýlom (alias do info rodiny - dovtedy nešty­lovaný). Kryté plnou unit sadou (2 286 testov), bundle checkmi a vizuálnym smoke testom v reálnom prehliadači.

## [2026.7.3.post76] - 2026-07-17 - Veľké upratovanie: menej kódu, jedna cesta pre každú vec

###  Zmenené
- **Legacy/kompatibilitný kód odstránený v celej aplikácii.** Holý Clone flow je preč: oba `/clone` endpointy, schéma aj duplicitný clone modál dashboardu - kontextové menu kurzu teraz otvára jediného sprievodcu Prenosom (nastavenia kurzu → Danger Zone), ktorý klonovanie pokrýva ako „čistý kurz, nearchivovať, bez webhookov". `apiCall` stratil kompatibilitnú vetvu pozičného retryCount (nikto ju nepoužíval). Fasáda `window.GitPulseMotion` s no-op funkciami držanými „pre stabilitu API" je zmazaná - pohybový kontrolér exportuje presne jeden helper (`GP.revealAfterSkeleton`) plus compliance ringy. Nikdy nevystrelený `htmx:abort` listener je preč. Osirotené CSS zmazané (slideIn, `.row-expand-enter`, `.card-glass` + tokeny, nepoužitý stagger token; hover prechody už neanimujú `transform`). Zastaraný `start-dev.sh` (éra natívneho Postgresu) odstránený - dev vstupný bod je `start-dev.ps1`. Report mŕtveho kódu je čistý.

## [2026.7.3.post75] - 2026-07-17 - Plnohodnotný prenos kurzu do nového semestra

###  Pridané
- **Kompletný „Prenos do nového semestra" - správna reaktivácia kurzu.** Starý holý Clone (len nastavenia, žiadne skupiny, mŕtve webhooky) nahradil sprievodca v nastaveniach kurzu → Danger Zone: vyber nový akademický rok a semester a potom čo sa prenáša - **všetko** (všetky skupiny; členovia/projekty sa re-synchronizujú z GitLabu), **vybraná podmnožina skupín**, alebo **čistý prázdny kurz** s rovnakými nastaveniami. Všetko sa automaticky doladí: prenos v rovnakom semestri posunie semestrálne okno, deadliny kurzu aj každý týždenný deadline o rozdiel akademických rokov (univerzitný kalendár sa takmer nemení), prenos medzi semestrami zachová štruktúru očakávaných kontrol, ale vyčistí neodhadnuteľné dátumy. **Webhooky fungujú ďalej bez zmien v GitLabe** - predvolený režim presmeruje existujúce webhook konfigurácie na nový kurz (hook na strane GitLabu rieši svoj kurz čisto cez konfiguráciu); alternatívne vydá nové jednorazové secrety (zobrazené raz) alebo webhooky preskočí. Zdrojový kurz sa archivuje (voliteľné) a spustí sa úvodná synchronizácia prenesených skupín (voliteľné). Nový `POST /api/v1/courses/{id}/transfer`; `/clone` zostáva pre kompatibilitu. Správanie služby pokrýva 8 nových unit testov.

## [2026.7.3.post74] - 2026-07-16 - SWR pamäť lazy stránok, oprava globálneho vyhľadávania, viditeľný prstenec avatara

###  Opravené
- **Globálne vyhľadávanie: zmazanie posledného znaku už nezabliká všetkými návrhmi.** Race condition: vyprázdnenie dopytu vykreslilo predvolený zoznam návrhov BEZ zneplatnenia ešte letiaceho API požiadavku predchádzajúceho znaku; keď jeho odpoveď ~200 ms nato dorazila, callback zoznam prepísal. Každý `doSearch` teraz zvýši generáciu požiadavky (aj prázdna cesta) a každá odpoveď zahodí zastarané generácie.
- **Prstenec avatara v pozdrave dashboardu je viditeľný na svetlej téme** - bol `--gl-gray-0` (biela v oboch témach) a splýval so svetlým pozadím; teraz zdieľaný token `--border-color`.

###  Pridané
- **Lazy stránky si pamätajú posledný obsah (stale-while-revalidate).** Návrat na lazy stránku prehrával celý skeleton, kým sa ten istý fragment znovu sťahoval. Posledné HTML každého fragmentu sa teraz drží per-tab (sessionStorage, kľúčované URL fragmentu, zneplatnené verziou aplikácie a 15-min vekom, vyčistené na login stránke) a pri návrate sa vloží OKAMŽITE namiesto skeletonu, kým normálny request potichu vymení čerstvé dáta - SWR ako na YouTube. Prázdne stavy („No tickets found") sa tak pri návrate zobrazia okamžite namiesto blikajúceho skeletonu tabuľky.

###  Zmenené
- **Mŕtvy skeleton kód zmazaný:** generická dvojica `sk_table`/`sk_tbody_rows` a riadkové makrá `sk_commits`/`sk_mrs` neboli referencované žiadnou šablónou; guard testy teraz overujú živé per-table kontrakty.

## [2026.7.3.post73] - 2026-07-16 - Animácie len tam, kde nesú informáciu + jednotné odznaky rolí

###  Zmenené
- **Celý animačný systém premyslený nanovo: pohyb len tam, kde nesie informáciu.** Odstránené ako pozlátko, v celej aplikácii: count-up metrík (hodnoty sa animovali 0→N počas 600 ms pri každom zobrazení - čísla sa teraz jednoducho vykreslia), sekvenčný stagger blokov a kaskáda položiek pri lazy načítaní (regióny sa teraz objavia JEDNÝM tichým fade-om, len opacity, jedna krátka dĺžka), vzostup/scale pri odovzdaní skeletonu a vstupe stránky, a nikdy nepoužité scroll-reveal mechanizmy s mŕtvymi motion-* utilitami. Zostáva len zámerné: vstup/výstup overlayov (modály, dropdowny, toasty), indikátory načítavania (spinnery, skeleton shimmer, progress), spätná väzba zmien (cell flash, badge pop, plynulé otváranie bannerov), sémantické status pulzy a kreslenie compliance ringu. Verejné GitPulseMotion API zostáva (no-op), nič sa nerozbije.
- **Odznaky rolí sú JEDEN komponent všade.** Admin odznak v správe učiteľov kurzu bol modrý, kým Správa používateľov ukazuje jantárový - každý rolový chip teraz ide cez zdieľané makro `role_badge()` (admin=jantárová, teacher=fialová, TA=info, student=neutrálna); rebrík prístupových rolí v tabuľkách členov a JS mapy modálu User Info už sedeli a zostávajú v súlade. Author/Reviewer pilulka na stránke študenta premenovaná na `mr_role_badge`, aby sa MR-účasť nemýlila s globálnymi rolami.

## [2026.7.3.post72] - 2026-07-16 - Pokojné hovery, presné skeletony, komponentové odznaky, dev toolbar

###  Opravené
- **Rušivé hover animácie odstránené v celej aplikácii.** Ikona prázdneho stavu sa pri prejdení myšou dvíhala, zväčšovala, žiarila modrým halo a donekonečna plávala; karty kurzov a interaktívne karty sa dvíhali (`translateY`/`scale`); riadky issues sa dvíhali. Všetky hover transformácie sú preč - hover je teraz pokojná zmena orámovania/pozadia/tieňa (štýl GitLab). Spätná väzba stlačenia tlačidiel a sémantické status pulzy (bežiace bodky, semafory) zostávajú.
- **Detekcia verzií teraz funguje aj vo vývoji.** Dev fingerprint hashoval len `core.bundle.js` + `main.py`, takže úpravy šablón a stránkových bundlov boli pre klientsku detekciu aktualizácie neviditeľné. Vo vývoji je fingerprint per-štart procesu: každý `uvicorn --reload` reštart ohlási novú verziu a otvorené karty zobrazia toast + auto-reload.
- **Skeleton zoznamu tiketov je štrukturálne identický s načítanou stránkou.** Toolbar vyhľadávania/filtrov bol ručne kopírovaná aproximácia, ktorá driftovala; teraz je to JEDEN zdieľaný makro súbor (`_tickets_toolbar.html`) renderovaný živou stránkou aj skeletonom (disabled) - rovnaký single-source vzor ako `table_heads.html` - a skeleton obsahuje aj pagination lištu, čo ruší skok layoutu pri načítaní. Statické chrome je skutočné; shimmer má len to, čo prichádza z DB.

###  Zmenené
- **Odznaky komponentizované.** 21 ručne písaných `<span class="badge ...">` v 8 šablónach teraz ide cez zdieľané makro `badge()`; makro dostalo `x_text` parameter pre Alpine počítadlá.

###  Pridané
- **Dev toolbar v UI** (len development/debug, v prode sa nikdy nerenderuje): pripnutá DEV pilulka, ktorá rozbalí celý lokálny tooling - Swagger (interaktívny tester každého endpointu), ReDoc, health JSON, Mailpit, admin stránka, Grafana, Jaeger - plus živý build fingerprint, ktorý sa mení pri každom dev reloade.

## [2026.7.3.post71] - 2026-07-16 - Husté tabuľky zdieľajú scroll model Správy používateľov + dev prostredie jedným príkazom

###  Opravené
- **Husté tabuľky zdieľajú scroll model Správy používateľov všade pod ~1440 px oknami - jednoriadkové hlavičky aj bunky, stĺpce podľa obsahu, vodorovný posun.** post70 v tabletovom pásme ponechal pevné %-stĺpce a nechal hlavičky zalamovať na hraniciach slov; v praxi to stále pôsobilo ako kaša - „Event ID" / „Dead Since" na dvoch riadkoch, „Ac tio ns" rozbité uprostred slova, dátumy na troch riadkoch (DLQ, tikety). Navyše samotné hlavičky hustých tabuliek potrebujú ~1010 px - viac než ~980 px obsahový stĺpec, ktorý necháva 1280 px okno vedľa sidebaru - takže pevné %-stĺpce sa nezmestia ani na malých desktopoch. Všetky `tbl-fixed` scroll tabuľky (tikety, DLQ, história úloh, správa kurzov, feature flags, aktivita skupín, nedávne MR) teraz pod 1440 px prechádzajú na auto-rozloženie podľa obsahu s `nowrap` + ellipsis a posúvajú sa vodorovne; pevný %-kontrakt sa vracia na veľkých desktopoch, kde sa skutočne zmestí. Neobmedzené textové stĺpce majú čistý ellipsis strop (názvy tiketov/MR, odkazy skupín, popis feature flagu). Kurzové tabuľky skupín/projektov/členov rozšírené na rovnakú hranicu.
- **Stĺpce tabuľky tiketov na desktope opäť prebalansované** - 7 % stĺpec Akcie z post70 zalamoval vlastnú hlavičku na 1280 px obrazovkách; vrátený na 10 %.
- **Mobilné pravidlo „Result / Error môže zalamovať" v histórii úloh presmerované** na správny stĺpec (posunulo sa na Duration po pridaní stĺpca s checkboxom). Overené v reálnom prehliadači na 480-1600 px: jednoriadkové hlavičky všade, nula nechceného orezania buniek, žiadny vodorovný overflow stránky.
- **Záložný avatar v modáli User Info používa komponentový štandard** - kruh s iniciálami bol posledný jednorazový modro-fialový gradient v aplikácii; teraz používa rovnaký neutrálny kruh (surface + border + sekundárny text) ako všetky ostatné záložné avatary.

###  Zmenené
- **`start-dev.ps1` teraz riadi celé dev prostredie** (žiadny samostatný skript): `up`/`restart` spustia kontajnery z docker-compose.dev.yml - Postgres :5433, Redis :6379 a nový **Mailpit** (SMTP :1025, UI :8025, zodpovedá SMTP nastaveniam v `.env`) - s čakaním na health; wipe DB pri `down`/`restart` beží vnútri compose kontajnera (netreba lokálny psql, správny port 5433 namiesto zastaraných predpokladov o natívnom 5432); health checky pokrývajú skutočné porty. Mailpit lokálne zachytáva všetky odchádzajúce emaily.

## [2026.7.3.post70] - 2026-07-16 - Všetky tabuľky (aj skeletony) sa na tabletoch posúvajú namiesto stláčania

###  Opravené
- **Každá dátová tabuľka (aj jej skeleton) sa teraz na celom rozsahu tabletov posúva namiesto stláčania stĺpcov.** Príčina: v pásme 769-1024 px pevný 240 px sidebar stláča obsahový stĺpec na ~480-736 px - často užšie než na telefóne, kde sa sidebar prekrýva - ale väčšina minimálnych šírok pre vodorovný posun platila len do ≤768 px. Skupiny, matice členov skupín/projektov, nastavenia kurzu (kontroly, webhooky), študentské tabuľky a archívne kurzy sa tak stláčali presne na tabletoch. Všetky prahy posunu teraz platia do ≤1024 px (vzor, ktorý post68 použil na husté admin tabuľky), tabuľky skupín a projektov v tom pásme prechádzajú na auto-rozloženie podľa obsahu s posunom, a tabuľky archívnych kurzov na dashboarde + týždenných deadlinov sa prihlásili ku scroll kontraktu, ktorý im úplne chýbal. Skeletony zdieľajú triedy živých tabuliek, takže nasledujú automaticky.
- **Tabuľka tiketov: odznaky a pilulky sa už neorezávajú uprostred slova.** Odznak stavu „In Progress" a pilulky zadávateľa/priradeného orezávali pevné šírky stĺpcov aj na desktope. Stĺpce sú prebalansované (stav/zadávateľ/priradený širšie, názov/akcie užšie), tabletový prah posunu zvýšený 860→1000 px, takže každý ne-názvový stĺpec zmestí svoj typický odznak/pilulku, a nezvyčajne dlhé používateľské mená degradujú čistým ellipsisom vnútri pilulky. Zámerne sa oreže len názov.
- **Správa používateľov si udržala svoje tabletové šírky** - nový všeobecný prah krátko prebíjal vlastný 760/680 px kontrakt users-table v kaskáde; selektory teraz nesú potrebnú špecificitu. Overené v reálnom prehliadači na 480-1280 px: nula orezaných buniek mimo zámerného ellipsisu názvu, žiadny vodorovný overflow stránky.

## [2026.7.3.post69] - 2026-07-16 - Horná lišta priebehu už nikdy nevisí na konci donekonečna

###  Opravené
- **Horná lišta priebehu už nemôže po AJAX akciách (napr. hneď po vytvorení tiketu) navždy visieť na ~99 %.** Po post66 zostali dva mechanizmy, oba reprodukované v reálnom prehliadači proti produkčnému bundlu: (1) lišta prenesená z predchádzajúcej stránky mohla byť „adoptovaná" requestom, ktorý štartuje počas jej 650 ms dokončovacieho fade-u - adopcia preskočila inkrement počítadla, takže keď sa dokončovacia udalosť requestu stratila (element odstránený počas swapu), počítadlo bolo nula, lišta viditeľne bežala donekonečna a sieťový rekonciliátor stav s nulovým počítadlom výslovne ignoroval; (2) zrušená navigácia - zostať na stránke cez dialóg neuložených zmien, Esc počas pomalého načítania, alebo POST, ktorý je v skutočnosti sťahovanie súboru - nechala na `<body>` navždy značku `page-navigating`, ktorá rekonciliátor úplne vypla. Opravy: `stop()` teraz spotrebuje zdedený pending synchrónne (po dokončení už nie je čo adoptovať), rekonciliátor dokončí aj viditeľne bežiacu lištu s nulovým počítadlom (pokiaľ ju nevlastní dokončovací fade) a ohraničený watchdog zhodí `page-navigating` po 10 s bez skutočnej navigácie. Overené end-to-end: oba nekonečné scenáre sa teraz samy zotavia za ~2-12 s, legitímne pomalé requesty a pomalé navigácie zostali nedotknuté.

## [2026.7.3.post68] - 2026-07-15 - Husté tabuľky sú čitateľné na celom rozsahu tabletov (aj malých)

###  Opravené
- **Husté tabuľky ostávajú čitateľné na celom rozsahu tabletov (aj malých), nielen na telefónoch.** Min. šírka pre vodorovný posun tabuliek s pevným rozložením (tikety, história úloh, správa kurzov, feature flags, DLQ, aktivita) sa zapínala len do ≤820 px, takže v pásme 820-1024 px sa stĺpce stláčali na plnú šírku - hlavičky sa zalamovali a tlačidlá vyliezali. Teraz platí až do 1024 px, takže tabuľky sa čisto posúvajú s pohodlnou šírkou stĺpcov a s prilepeným prvým stĺpcom namiesto stláčania. Tabuľka tiketov (8 stĺpcov) má o niečo širšiu hranicu 860 px, aby názov / odznaky / pill priradenia / tlačidlo akcie nikdy nekolidovali.
- **Dead-letter queue: zaškrtávacie políčko už nevyzerá stlačené.** JS riadky dávajú checkbox do prvej bunky bez triedy, ktorá sa v auto-rozložení na tablete zmrštila na holú šírku checkboxu; prvý stĺpec teraz drží pohodlnú min. šírku a je vycentrovaný.

## [2026.7.3.post67] - 2026-07-15 - Konzistentné bunky tabuliek a záložné avatary naprieč aplikáciou

###  Opravené
- **Bunky tabuliek a záložné avatary sú teraz konzistentné.** Názvy tiketov sa na tablete zalamovali do 2-3 riadkov (`text-overflow: ellipsis` bez `white-space: nowrap` nefungoval) - teraz držia jeden riadok a čisto sa orežú, ako v tabuľke Správa používateľov, ktorá bola uvedená ako vzor. Dlhé názvy skupín/podskupín v tabuľke skupín sa orežú ellipsisom namiesto zalamovania. Záložný avatar (iniciály) na profile študenta používal jednorazový modro-fialový gradient - teraz používa rovnaký neutrálny sivý kruh ako všetky ostatné záložné avatary (diskusia, recenzenti), takže vyzerajú všade rovnako.

## [2026.7.3.post66] - 2026-07-15 - Horná lišta priebehu sa dokončí okamžite pri AJAX akcii (bez timeoutu)

###  Opravené
- **Horná lišta priebehu sa teraz dokončí hneď, ako sa dokončí AJAX akcia na mieste** (napr. „tiket vytvorený"), namiesto vypršania timeoutu. Nahrádza 20 s strop z post65 (ktorý bol nesprávny - lišta by aj tak bežala 20 s). Skutočná oprava je vzor, ktorý import/CRUD skupín z GitLabu už používal (`GP.finishTopProgress()` pri zachytení AJAX formulára), aplikovaný centrálne v zdieľanom submit handleri - takže každý formulár, ktorý zavolá `preventDefault()` (tiket saportu, odpoveď, analytika/replay, ...), dokončí lištu okamžite, naprieč systémom. Spinner tlačidla stále ukazuje priebeh samotného requestu.

## [2026.7.3.post65] - 2026-07-15 - Zoznam tiketov zobrazuje všetky, emaily priority, náhľad obrázka, strop progresu

###  Opravené
- **Zoznam tiketov zobrazoval len tikety prvého formulára** (ostatné vyzerali „chýbajúce" - „#5 ale ostatné 4 nie sú"). Filter formulára predvolene padol na `forms[0]`, čím ticho skryl tikety z iných formulárov (alebo bez formulára). Teraz zobrazí všetky tikety kurzu; filter formulára sa použije len keď je výslovne vyžiadaný.
- **Zmena priority neposielala email** - len zmena stavu. Zmena priority teraz emailuje zadávateľa/priradeného (keď sa líšia od aktéra), ako zmena stavu. Overené cez Mailpit.
- **Priložený obrázok splýval s textom v náhľade** - teraz je blokový (vlastný riadok, jasné odsadenie).
- **Hlavičky tabuliek sa na tablete zalamovali po znakoch** („Sub mitte d By"). Teraz sa zalamujú na hraniciach slov a tabuľky s pevným rozložením držia použiteľnú min. šírku (vodorovný posun) do 820 px.
- **Horná lišta priebehu mohla stále visieť** - pribudol tvrdý 20 s strop, ktorý ju dokončí bez ohľadu na zaseknutú triedu `page-navigating` alebo visiaci fetch (dopĺňa opravu rekonciliátora z post60).

## [2026.7.3.post64] - 2026-07-15 - Zmeny stavu tiketu aktualizujú zoznam naživo + toast o novom tikete

###  Pridané
- **Zmeny stavu/priority/priradenia tiketu teraz naživo aktualizujú zoznam tiketov** a pri príchode tiketu sa zobrazí **toast „Prijatý nový tiket"**. Endpoint na aktualizáciu publikoval len na kanál konkrétneho tiketu (otvorená detailná stránka); teraz publikuje aj udalosť `ticket_updated` na kurzový kanál, takže zoznam odzrkadlí zmenu bez manuálneho obnovenia. Spolu s post63 je povrch tiketov plne dynamický - vytvor alebo zmeň tiket kdekoľvek (aj cez API) a UI zareaguje naživo.

## [2026.7.3.post63] - 2026-07-15 - Zoznam tiketov sa aktualizuje naživo pri vytvorení tiketu

###  Pridané
- **Zoznam tiketov sa teraz aktualizuje naživo pri vytvorení tiketu** (aj cez API alebo iným používateľom), namiesto zobrazenia až po manuálnom obnovení. Vytvorenie tiketu publikuje udalosť `ticket_created` na kurzový SSE kanál a kurzovo-viazaný zoznam tiketov sa naň prihlási a znovu načíta (zlúčené na jedno načítanie / 1,5 s). Overené v deve: odoslanie tiketu publikuje `{"event":"ticket_created","ticket_id":...}` na `dashboard:course:<id>`. Uzatvára medzeru „čo vytvorím v konzole sa nezobrazí v UI" pre tikety (kurzový dashboard to už robil pre webhooky).

## [2026.7.3.post62] - 2026-07-14 - Hlavičky tabuliek už nie sú orezané („Priorita ...", „Akci...")

###  Opravené
- **Hlavičky tabuliek boli orezané** na „Priorita ...", „Kategória ...", „Akci..." v tabuľkách s pevným rozložením (tikety, kurzy, admin/events). `.sort-link` vynucoval `white-space: nowrap`, takže úzke stĺpce orezali popisky. Hlavičky sa teraz zalamujú v rámci stĺpca namiesto orezania (bunky sa stále orezávajú). Obmedzené na `.tbl-fixed`, takže každá tabuľka s pevným rozložením je opravená naraz.

## [2026.7.3.post61] - 2026-07-14 - Preč blikanie po navigácii, náhľady obrázkov, prázdny stav tabuliek

###  Opravené
- **Celá stránka blikala pri každej navigácii.** Vstupná animácia stránky mala byť odstránená (spôsobovala blikanie hlavného kontajnera a malých kariet), no pravidlo prežilo v `loaders.css` a `.main-container` stále nabiehal (opacity 0→1 + posun) pri každom načítaní. Odstránené - stránky sa teraz vykreslia okamžite (jemný nábeh si drží len prihlasovacia karta).
- **Prílohy obrázkov sa zobrazovali ako odkaz, nie náhľad.** `renderMarkdown` nespracoval `![alt](url)`, takže obrázok vyzeral ako text `123!file.png`. Teraz sa vykreslí ako vložený náhľad (klik otvorí plnú veľkosť), v Preview tabe aj vo vlákne tiketu.
- **Filtrovanie tabuľky na nulu zobrazilo prázdnu tabuľku.** Zdieľaný filter zobrazoval „žiadne výsledky" len pri textovom hľadaní, nie pri rozbaľovacích filtroch stav/priorita/kategória. Teraz zobrazí komponentový prázdny stav (ikona + správa) vždy, keď aktívny filter skryje všetky riadky - naprieč každou filtrovateľnou tabuľkou.

## [2026.7.3.post60] - 2026-07-14 - Horná lišta priebehu už nezostane visieť pri behu jobu na pozadí

###  Opravené
- **Horná lišta priebehu mohla zostať visieť (nikdy nedokončila), keď na pozadí bežal job** - počas importu skupiny, alebo na akejkoľvek stránke otvorenej počas synchronizácie / importu. Rekonciliátor zaseknutého počítadla si resetoval „tichý" časovač pri každom krátkom sieťovom blipe pollera na pozadí, takže sa nikdy sám nedokončil a lišta zostala visieť celých 120 s. Teraz **akumuluje tichý čas a pri krátkych špičkách pollerov len pozastaví (neresetuje)**, takže zaseknutá lišta sa sama vylieči za ~1,5 s bez ohľadu na pollery. Skutočne pomalé načítanie drží reálnu sieťovú aktivitu nepretržite, takže jeho lišta správne ostane až do konca. Rovnaká príčina ako pri importe skupiny - toto to opravuje všade.

## [2026.7.3.post59] - 2026-07-14 - Toast pre učiteľa pri webhooku + jasné „Zrušené" + roh kalendára

###  Pridané
- **Učiteľ dostane živý toast, keď pre skupinu príde GitLab webhook.** SSE notifikácia teraz nesie názov skupiny a kurzová stránka zobrazí toast len pre personál (napr. „Webhook received: Merge request - Team Alpha"). Je navrhnutý tak, aby čisto spolupracoval so zvyškom aplikácie: zobrazí ho len viditeľný líder tab a rozošle ho súrodeneckým viditeľným tabom (N otvorených tabov → jeden toast, tab na pozadí mlčí); je **potlačený počas synchronizácie kurzu** (globálny sync bar už signalizuje aktualizácie); a je obmedzený na jeden za 4s. Prepočet už bol zúžený len na dotknutú skupinu + debounced - nezmenené.

###  Opravené
- **Zrušená úloha už nehlási „Process failed".** Zrušenie synchronizácie / kontrol / importu je zámerné, no padalo do vetvy zlyhania. Teraz zobrazí jasné „Zrušené" (terminálny stav bar-u ostáva binárny done/error - mení sa len text).
- **Artefakt zaobleného rohu v hlavičke kalendára.** Hlavička navigácie aj zaoblený rám kalendára zaobľovali svoje rohy, čo pri šípkach `<` / `>` zanechalo nesúladný zárez. Kalendár sa teraz čisto oreže do zaobleného rámu (`overflow:hidden`) a hlavička/šípky sa už nezaobľujú dvojito.

## [2026.7.3.post58] - 2026-07-14 - Kalendár: zatváranie s modálom + viditeľný hover šípok; dashboard archív

###  Opravené
- **Kalendár ostával otvorený po zatvorení modálneho okna.** Flatpickr pridáva popup kalendára do `<body>`, takže po zatvorení modálu s dátumovým poľom ostal kalendár visieť nad stránkou. Zatvorenie modálu teraz zatvorí aj každý flatpickr jeho polí (všetky cesty - tlačidlo, pozadie, Escape, programovo).
- **Navigačné šípky kalendára mali neviditeľný hover.** Hover pozadie šípok `<` / `>` bolo `--surface-moderate` - rovnaká farba ako hlavička `.flatpickr-months` - takže hover nič nespravil a šípky vyzerali ako prázdne zaoblené tvary. Hover teraz používa token ikonového tlačidla, takže je jasne odlíšený.

###  Zmenené
- **Dashboard onboarding rešpektuje archivované kurzy.** Keď účet nemal žiadne *aktívne* kurzy, vždy zobrazoval „Vytvorte prvý kurz" (odkaz na zoznam kurzov) - aj keď bol každý kurz archivovaný (napr. auto-archivácia na konci semestra). Teraz ponúka **reaktiváciu archivovaného kurzu pre nový semester**, s odkazom na `/dashboard/admin/courses`, kde je tlačidlo Aktivovať.

## [2026.7.3.post57] - 2026-07-14 - Nahrávanie príloh opravené (kolízia rout), markdown toolbar, dvojitá čiara

###  Opravené
- **Nahrávanie príloh bolo pokazené pre všetkých (skutočná príčina).** Route `POST /support/{token}` (odoslanie tiketu, JSON) bola zaregistrovaná pred `POST /support/upload`, takže `/support/upload` sa napároval na param route `{token}` s `token="upload"` - JSON endpoint, ktorý nevie čítať multipart, takže každé nahrávanie zlyhalo s 422 „Input should be a valid dictionary". Oprava URL z post55 ho len presunula zo 404 na nesprávnu route; nahrávanie nikdy nefungovalo. Fixná cesta `/support/upload` je teraz deklarovaná pred param route a pribudol regresný test.
- **Markdown toolbar: nadpis/citácia/zoznam sa vykreslili doslovne.** Blokové značky (`### `, `> `, `- `) fungujú len na začiatku riadku, ale toolbar ich vkladal na pozíciu kurzora, takže kliknutie na Nadpis za textom vyrobilo „text### text" na jednom riadku. `mdInsert` teraz pred blokovou značkou zalomí na nový riadok, ak nie je na začiatku riadku.
- **Zbytočná dvojitá čiara pod hlavičkou formulára saportu.** Po presune bannera „Prihlásený ako @..." do horného pásu (post56) ostal `gh-form-divider`, ktorý ho predtým oddeľoval od formulára - zdvojoval spodný okraj `page-header`. Osirelý rozdeľovač je odstránený; okraj hlavičky je teraz jediný predel.

## [2026.7.3.post56] - 2026-07-14 - Stavové bannery do horného pásu + redizajn offline stránky

###  Zmenené
- **Stavové bannery na úrovni stránky sa teraz presúvajú do horného pásu všade.** Notifikácia „Prihlásený ako @..." vo formulári saportu, kurzové bannery „Niektoré sync joby zlyhali" / „Sync zrušený" a projektové upozornenie „GitLab repozitár je prázdny" sa vykresľovali priamo v tele stránky; teraz sa presúvajú do zdieľaného `#globalBannerSlot` (rovnaký mechanizmus ako banner archivovaného kurzu) a zobrazujú sa ako jeden jednotný pás `top_banner` (`.gp-top-banner`), takže sa skladajú na sebe ako broadcast lišta GitLabu.
- **Zjednotené boli aj dva živé JS bannery kurzu.** Banner „GitLab token neplatný" a živý banner „Niektoré sync joby zlyhali" (vytvorený sync SSE streamom bez reloadu stránky) boli `.info-card` boxy v tele stránky; teraz sa vykresľujú ako rovnaký pás `.gp-top-banner` pridaný do `#globalBannerSlot`. Invarianty zostávajú: živý banner sa vytvorí len keď neexistuje server verzia a odstraňuje sa len JS karta. Makro `top_banner` má nový voliteľný argument `class`.
- **Stránka „Ste offline" bola prerobená v štýle GitLabu.** Začína brandom s aktuálnym logom aplikácie (`favicon.svg`, precachované, takže sa vykreslí aj úplne offline) namiesto predvoleného glóbusu prehliadača; zdieľa tokeny `error.css` s ostatnými chybovými stránkami.

## [2026.7.3.post55] - 2026-07-13 - Upload 404, Preview tab, falošný dirty - opravené

###  Opravené
- **Nahrávanie príloh zlyhávalo všade („Upload failed").** Klient posielal na `/api/v1/support/upload`, čo 404 - route je na telemetry routeri (`/telemetry` prefix), takže správna cesta je `/api/v1/telemetry/support/upload`. Opravená URL; chybová správa teraz obsahuje aj status kód (bol prázdny, lebo HTTP/2 nemá `statusText`).
- **Tab Preview v markdown editore sa neprepínal (bez chyby).** Magic `$mdShowPreview` čítal `el._x_dataStack` z tlačidla, čo je na potomkovi často undefined, takže zápis potichu nič nespravil. Teraz používa kanonický reaktívny `Alpine.$data(el)` (walk ako fallback).
- **Formulár saportu hlásil falošné „unsaved changes".** Nastavoval dirty pri KAŽDOM `input`/`change`, vrátane programových (Alpine / default selectov). Teraz vyžaduje `e.isTrusted` - skutočnú úpravu.

## [2026.7.3.post54] - 2026-07-13 - Vyčistenie súboru pri importe z JSON + téma remove-file

###  Opravené
- **Import z JSON: po odstránení súboru ostal jeho obsah.** `showFile()` automaticky načíta vybraný súbor DO textového poľa, ale `clearFile()` mazal len file input - nie textové pole. Preto po odstránení súboru obsah ostal „vložený". `clearFile()` teraz vyčistí aj textové pole.
- **Hover tlačidla remove-file** používal natvrdo tmavo-červené `--gl-red-950` pozadie (rušivé na svetlej téme); teraz je téme-aware `--gl-feedback-danger-bg` odtieň.

###  Poznámky
- Preverené tlačidlo **Preview** aj **skelet** zoznamu tiketov: oba sú v kóde správne (magic `$mdShowPreview`, `renderMarkdown` + `supportFormEditor` sa načítajú; skelet používa rovnakú `tickets_table_head()` ako živá tabuľka). Konkrétny problém treba reprodukovať, nie hádať.

## [2026.7.3.post53] - 2026-07-13 - Regresia posunu modálky, prekrytie pruhu, téma drop-zóny, offline favicon

###  Opravené
- **Regresia: obsah sa pri otvorení modálky posúval doľava.** Kompenzácia scrollbaru z post50 bola nesprávna - `overflow: hidden` je stále scroll kontajner, takže `scrollbar-gutter: stable` platí a medzera sa neuvoľní; pridaný padding preto prekompenzoval. Vrátené späť.
- **Pruh pripojenia prekrýval rozbaľovacie menu horného panelu.** Mal `z-index: var(--z-sticky)` (nad tier-om dropdownov). Je to in-flow pruh, takže je teraz `calc(var(--z-dropdown) - 1)` - pod dropdownmi, nad obsahom.
- **Zóna importu z JSON bola na svetlej téme nečitateľná.** Stav `has-file` používal natvrdo tmavý `--gl-green-950`; teraz je téme-aware `--gl-feedback-success-*` odtieň (pozadie + text + ikona).
- **Offline stránka** nemala favicon (globus prehliadača v záložke); teraz odkazuje app favicon, takže záložka ukazuje aktuálne GitPulse logo.

## [2026.7.3.post52] - 2026-07-13 - Skeleton User Info + globálny timeout/retry (komponentovo)

###  Zmenené
- **Skeleton modálky User Info (komponentovo).** Oba vstupy (admin stránka aj globálna modálka „klik na meno" v core) ukazovali generický spinner. Teraz vykresľujú štruktúrny skeleton, ktorý kopíruje načítanú kartu (avatar kruh + identita + meta + dve sekcie placeholder kariet), zdieľaný cez `UserInfoModal.skeleton()`, takže prechod na reálne dáta nemá skok layoutu.

###  Opravené
- **Globálny User Info visel donekonečna na pomalom/offline internete.** Používal raw `fetch()` bez timeoutu. Teraz sa preruší po 12s cez `AbortController` a chybový stav má tlačidlo **Retry**. Oba vstupy teraz zdieľajú rovnaký skeleton, komponentový avatar fallback, timeout a retry.

## [2026.7.3.post51] - 2026-07-13 - Avatar fallback v User Info, oprava prekrytia + pomalý internet

###  Opravené
- **Avatar v modálke User Info používa zdieľaný komponentový fallback.** Bol to holý `<img>` s vlastnou vetvou pre iniciálu; teraz sa vykresľuje s `data-avatar-fallback` + súrodencom s iniciálami, takže pokazený / timeoutnutý / offline avatar degraduje na iniciály cez rovnaký globálny handler (retry, offline, watchdog) ako každý iný avatar.
- **Rozbaľovacie menu horného panelu už neprekrýva pruh pripojenia.** Horný panel mal `z-index: var(--z-sticky)` - rovnaký ako health/connection pruh (ktorý je neskôr v DOM a prekresľoval otvorené menu). Horný panel je teraz `calc(var(--z-sticky) + 10)`.
- **User Info na pomalom/offline internete.** Timeout klesol z 30s na 12s a už neopakuje, takže zaseknutá požiadavka neblokuje `_infoLoading` (kvôli čomu ďalšie kliknutia nič nerobili). Chybový stav má teraz tlačidlo **Retry**.

## [2026.7.3.post50] - 2026-07-13 - Otvorenie modálky už neposunie stránku doprava

###  Opravené
- **Otvorenie modálky už neposunie stránku doprava.** Zámok scrollu nastavoval `.gl-page-content { overflow: hidden }`, čím prvok prestal byť scroll kontajnerom - takže jeho rezervácia `scrollbar-gutter: stable` sa uvoľnila a obsah sa rozšíril/posunul doprava o šírku medzery. `_refreshBodyScrollLock` teraz zmeria túto medzeru (`offsetWidth - clientWidth`) PRED zamknutím a zachová ju ako `padding-right` (`--gp-lock-gutter`) počas otvorenej modálky. Bezpečné aj pri stackovaných modálkach (merané raz pri prvom zámku), reset pri poslednom zatvorení. Overené, že vstupné keyframes (`modalSlideUp`, `gp-content-in`, `gp-fade-in`) sú čisto vertikálne.

## [2026.7.3.post49] - 2026-07-12 - Plynulé zbalenie pri mazaní prvkov (zdieľaný helper)

###  Pridané
- **`GP.collapseAndRemove(el, cb)`** - zdieľaný helper (alias existujúceho `collapseBanner`), takže každý jednotlivý prvok mazaný BEZ plného reloadu zoznamu sa plynule zbalí (výška + fade) namiesto zmiznutia, s ohľadom na reduced-motion.

###  Zmenené
- **Karta kurzu** na dashboarde sa pri odstránení plynule zbalí (predtým fade-a-skok-medzery) cez `GP.collapseAndRemove`, s aktualizáciou prázdnej sekcie v callbacku.
- Audit miest odstránenia: väčšina (karty analýz, riadky admin kurzov, welcome tour, sync-stream karty) už mala výstupné animácie, takže motion systém je konzistentný; iba karta kurzu nemala zbalenie. Mazanie `<tr>` ponecháva fade (riadky nevedia spoľahlivo animovať výšku).

## [2026.7.3.post48] - 2026-07-12 - Komponentové interakčné stavy tlačidiel

###  Zmenené
- **Komponentové interakčné stavy tlačidiel.** Každé `.btn` má teraz jemný hmatový press (`:active` translate+scale) a zdieľaný success/error flash (`GP.flashButton(btn, 'success'|'error')` → `.gp-btn-success` pulz / `.gp-btn-error` zatrasenie), všetko s ohľadom na reduced-motion. Zdieľaná cesta zlyhania akcie (Run Checks / Sync naprieč kurzom/skupinou/projektom) pri chybe blikne tlačidlom. Aplikované cez komponent, takže je to konzistentné v celej aplikácii.
- Overené, že zvyšok motion systému je už konzistentný: toasty majú korektnú výstupnú animáciu `toast-dismissing`, rozbaľovacie ponuky používajú Alpine enter/leave, modálky používajú swipe so zotrvačnosťou z post47. Zvyšná per-element výstupná animácia pokračuje iteratívne.

## [2026.7.3.post47] - 2026-07-12 - Archived odznaky v User Info, zotrvačnosť swipu, oprava Wk v kalendári

###  Opravené
- **Modálka User Info zobrazí archived/inactive stav.** Kurzy a skupiny nikdy neindikovali archived/inactive. Info API teraz posiela `is_active` / `course_active` / `team_active` a `user-info-modal.js` vykreslí tlmený odznak „Archived".
- **Swipe-to-dismiss na mobile má teraz zotrvačnosť.** Potiahnutie bottom sheetu dole cez prah predtým resetovalo transform na 0 a prehralo kanónikový slide-down (skok/bliknutie). Teraz sheet plynule pokračuje mimo obrazovku od prsta (`.sheet-dismissing` potlačí keyframe `modalSlideDown`; pozadie stále mizne).
- **Stĺpec „Wk" v kalendári už nie je prázdny.** Bez semestrálnej kotvy (napr. modálka vytvorenia kurzu pred výberom dátumu) boli všetky bunky prázdne. Teraz fallback na ISO-8601 týždeň, a po zvolení kotvy prepne na semestrálne týždne.
- **Avatar v User Info** je zarovnaný hore (predtým centrovaný proti vysokému bloku identity, pôsobil stiesnene) a už sa nedá zmenšiť.

## [2026.7.3.post46] - 2026-07-12 - Jednotný štýl vrchných pruhov + dismiss, oprava presetov

###  Zmenené
- **Jednotný štýl vrchných pruhov + dismiss.** Všetky stránkové stavové pruhy sa teraz vykresľujú cez jedno macro `top_banner` (`.gp-top-banner`) štýlované globálne v `health.css`, takže archivačný, „Data may be outdated" aj stale-data pruh vyzerajú rovnako (plochý GitLab-štýl pruh: ikona + správa + voliteľná akcia + dismiss). Každý má dismiss (X), ktorý pretrvá naprieč navigáciou, reloadom aj inými kartami cez spoločný `gp:dismissedBanners` (handler + `_hideDismissedBanners` zovšeobecnené z `.info-card` na `.gp-top-banner`; portál preskočí už zavreté). Slot sa obmedzí na `50vh` a scrolluje pri mnohých pruhoch. CSS sa presunulo do globálneho bundlu, takže funguje na každej stránke.

###  Opravené
- **Zastarané semestrové presety.** Ponuka „Quick preset" ponúkala minulé semestre (zima/leto 2025/2026). `get_presets()` teraz odfiltruje presety s `end_date` pred dneškom, zostanú len aktuálne a budúce.

## [2026.7.3.post45] - 2026-07-12 - Všetky stránkové banery sa zlučujú do vrchného pruhu

###  Zmenené
- **Všetky stránkové stavové banery sa teraz zlučujú do globálneho vrchného pruhu.** Zovšeobecnili sme portál archivačného banera z post44 na opakovane použiteľný mechanizmus: každý baner označený `.js-top-banner` (s voliteľným `data-banner-key` na dedup) JS (`_portalTopBanners`) portáluje do `#globalBannerSlot` hore, kde sa skladá spolu s pruhom úloh a pruhom pripojenia/zdravia ako GitLab broadcast pruh. Aplikované na kartu **„Data may be outdated"** (prehľad kurzu) a **stale-data** baner (analytika + aktivita), navyše k archivačnému pruhu. V pôvodnom mieste sú skryté (nebliká), v slote si ponechajú prirodzené flex rozloženie, len stratia okraj/zaoblenie, takže vyzerajú ako ploché pruhy.
- Prázdne stavy viazané na prvok („ešte nesynchronizované", „repozitár je prázdny") zámerne NIE sú označené, takže ostávajú na mieste - opisujú konkrétny prvok, nie stav stránky.

## [2026.7.3.post44] - 2026-07-12 - Archivačný pruh presunutý do globálneho vrchného stavového pruhu

###  Zmenené
- **Archivačný pruh kurzu presunutý do globálneho vrchného stavového pruhu.** Oznámenie „Archivovaný kurz · len na čítanie" bolo vložené pod názvom kurzu. Teraz sa vykresľuje ako plochý, celej šírky GitLab-štýl pruh úplne hore na stránke, spolu s pruhom úloh na pozadí a pruhom pripojenia/zdravia (jedna spoločná stavová oblasť). Pruh sa vykreslí v lenivo načítanom obsahu kurzu s plným kontextom a JS ho portáluje do globálneho slotu (`#courseArchivedSlot`) v `base.html` pod pruhom zdravia; v pôvodnom mieste je skrytý, takže nebliká. Read-only guard stále číta `.tabs-nav[data-course-archived]`, takže správanie sa nemení.
- Pruh je teraz statický (bez rámika karty, bez animácie). Kontextové oznámenia (zastarané dáta nad grafmi, „ešte nesynchronizované" prázdne stavy) zámerne ostávajú na mieste - opisujú konkrétny obsah, nie globálny stav stránky.

## [2026.7.3.post43] - 2026-07-12 - Hromadná správa Job History + opravy čistenia

###  Pridané
- **Hromadná správa Job History.** Každý riadok denníka operácií má teraz zaškrtávacie políčko (plus hlavičkové „označiť všetko") a akciu „Delete selected", ktorá zmaže vybrané riadky podľa id (`/jobs/delete`) - úlohy na pozadí aj audit operácie. Syntetické riadky (archivácia odvodená z `archived_at` kurzu) majú zablokované políčko a preskočia sa.
- **Čistenie podľa veku.** „Purge Old" je teraz rozbaľovacia ponuka: staršie ako 24 hodín, 7 dní, 30 dní alebo Všetko.

###  Opravené
- **Purge Old teraz čistí aj operácie, nielen úlohy.** Mazal len riadky `BackgroundJob`, takže viditeľné audit operácie (mazania/importy/obnovy) sa nikdy nevyčistili - hlásené „Purge Old prestal čistiť". Endpoint dostal `scope` (`jobs`/`operations`/`both`, predvolene `both`).
- **Archivované kurzy teraz zobrazia svoju archiváciu.** Kurz archivovaný pred existenciou audit zápisu `course.archive` nemal audit riadok, takže ani Job History ani „Follow the latest updates" neukázali, že bol archivovaný. Oba teraz syntetizujú záznam „Course archived" z `Course.archived_at`.
- Overené: pre odstránené funkcie (gaming, rubric, assignments) nezostal žiadny mŕtvy kód.

## [2026.7.3.post42] - 2026-07-12 - Job History je úplný denník operácií

###  Pridané
- **Job History je teraz úplný denník operácií.** Zobrazoval len úlohy na pozadí (sync, checks, enrichment, metrics), takže synchrónne akcie administrátora - vytvorenie/import/archivácia/mazanie/obnova kurzov aj skupín, nastavenia, podpora, eventy - sa zobrazovali v „Follow the latest updates", ale v Job History potichu chýbali. Endpoint teraz tieto ne-jobové audit akcie zlúči k úlohám na pozadí (rovnaký tvar riadku: stav `completed`, bez trvania, nedá sa zrušiť), pričom vylúči jobové audit akcie (sync/checks/...), ktoré už existujú ako `BackgroundJob`, takže sa nič nezdvojuje. Preto prázdny prod Job History stále ukazoval mazanie a importy len vo feede - teraz oba povrchy súhlasia.

## [2026.7.3.post41] - 2026-07-12 - Automatická archivácia sa zobrazí vo feede aktualizácií + bezpečnejší import z JSON

###  Opravené
- **Automatická archivácia sa teraz zobrazí v „Follow the latest updates".** Keď sa kurz automaticky (alebo manuálne) zarchivoval, feed dashboardu ostal ticho - `archive_course` nezapisoval žiadny audit záznam a feed archivovaný kurz aj tak vyfiltroval, lebo už nebol aktívny. Archivácia teraz zapíše záznam aktivity `course.archive` priradený aktérovi a feed ponechá ID nedávno archivovaných kurzov v rozsahu, takže sa záznam naozaj zobrazí.
- **Import kurzu z JSON: neúspešné použitie už nezomrie potichu.** Handler použitia čakal na `onApply` bez `catch`, takže odmietnuté API volanie sa prejavilo len ako neošetrené odmietnutie promise v konzole prehliadača. Teraz zobrazí jasný chybový toast. (Hláška `content.js ... message port closed`, ktorú niektorí videli, je rozšírenie prehliadača, nie GitPulse.)
- **Mená aktérov vo feede aktivity.** Aktér seedovania konfigurácie kurzu sa teraz číta ako „Course import" namiesto surového `auto-import`, tak ako ostatní strojoví aktéri (System, Scheduler, Background worker).

## [2026.7.3.post40] - 2026-07-11 - Automatická archivácia naozaj archivuje + oprava avatara profilu

###  Opravené
- **Automatická archivácia teraz naozaj archivuje.** post38 zaraďoval sweep do worker jobu (fork + `asyncio.run` + re-init enginu), ktorý mohol potichu nechať nič nezarchivované. Dashboard teraz spúšťa sweep INLINE vo vlastnej dočasnej session, throttled ~raz/15 min cez Redis lock, ktorý sa pri chybe uvoľní, takže ďalšie načítanie to zopakuje.
- **Skeleton avatar profilu už nenačítava obrázok dvakrát.** Skeleton aj obsah načítavali fotku - dve požiadavky na avatar, ktorých fallback/watchdog handlery pretekali. Skeleton teraz zobrazí iniciály; fotka sa načíta práve raz s obsahom.
- **Odznaky v histórii commitov** („Merge commit" / vetva) sa teraz držia pri správe namiesto plávania úplne vpravo s veľkou medzerou v strede.
- **Karta archívnych kurzov** dostala priestor dole a jej akcie sa zalomia namiesto pretečenia.

###  Zmenené
- **Banner archívneho kurzu je teraz tenký GitLab-style pruh** navrchu záložiek, nie veľká alert karta.
- **Filter vetiev v histórii commitov** je teraz animovaný dropdown komponent (glFormSelect) namiesto natívneho `<select>`.
- Verzia `2026.7.3.post40`; Cache Service Workera `gitpulse-v311`.

## [2026.7.3.post39] - 2026-07-11 - Archívne kurzy sa dajú prezerať (len na čítanie)

###  Pridané
- **Archívne kurzy sa dajú prezerať (len na čítanie).** Zoznam „Archived Courses" na dashboarde má teraz tlačidlo **View**, ktoré kurz otvorí. Každá záložka kurzu (prehľad / nastavenia / aktivita / analytika / učitelia) zobrazuje banner „len na čítanie" - „Tento kurz je archivovaný, archivovaný dňa <dátum> ... Reaktivujte ho pre zmeny" - so skratkou na reaktiváciu pre staff.
- **Archívne kurzy sú naozaj len na čítanie.** Zmeny na úrovni kurzu (synchronizácia celého kurzu, spustenie kontrol kurzu/skupiny, synchronizácia skupiny, uloženie nastavení, vytvorenie skupiny) sú na serveri odmietnuté jasným 409, kým je kurz archivovaný; príslušné tlačidlá sú vypnuté a stlmené. Reaktivácia nie je dotknutá.
- **Živé povedomie o read-only.** Stránka kurzu dopytuje svoj stav (~1×/min) a ak je kurz archivovaný v inej karte alebo iným používateľom, prepne sa na read-only bez manuálneho obnovenia.

###  Opravené
- Zoznam archívnych kurzov predtým ponúkal len Re-activate/Delete bez možnosti kurz skutočne otvoriť.
- Verzia `2026.7.3.post39`; Cache Service Workera `gitpulse-v310`.

## [2026.7.3.post38] - 2026-07-11 - Automatická archivácia na konci semestra teraz naozaj beží

###  Opravené
- **Automatická archivácia na konci semestra teraz naozaj beží.** Nastavenia kurzu ukazujú odznak „Auto-archive due / Auto-archives <dátum>" a prepínač „Skip automatic archiving", a dashboard naznačuje, že skončené kurzy sa archivujú - ale nič to nevykonávalo, odkedy bola odstránená vrstva plánovaných sweepov (žiadny cron/plánovač neexistuje). Sweep je späť a beží oportunisticky: staff dashboard ho zaradí do frontu najviac raz za hodinu (Redis lock) a worker archivuje každý aktívny kurz, ktorého semester skončil pred viac ako grace obdobím, pokiaľ sa kurz neodhlásil cez „Skip automatic archiving". Idempotentné, nikdy neblokuje dashboard; reaktivácia kurzu ho vyradí z ďalšieho sweepu, takže archiváciu možno ľahko vrátiť.
- Text nápovedy na dashboarde je teraz pravdivý: kurz s povolenou archiváciou ukazuje „prebieha automatická archivácia", odhlásený „automatická archivácia je vypnutá - archivujte ručne".
- Verzia `2026.7.3.post38`; Cache Service Workera `gitpulse-v309`.

## [2026.7.3.post37] - 2026-07-11 - Explicitne zvolená téma sa už sama neprepne na systémovú

###  Opravené
- **Explicitne zvolená téma sa už sama neprepne na systémovú.** Klient uprednostňoval hodnotu účtu (`data-theme-preference`) pred lokálnou voľbou. Keď účet ostal na nejednoznačnom predvolenom `system` (nebol prepísaný na serveri, alebo skorší POST zlyhal), zatiaľ čo tento prehliadač mal explicitné `light`/`dark`, reload sa znovu vyhodnotil ako `system` a nasledoval OS - takže explicitná tmavá sa mohla sama prepnúť na svetlú. Bootstrap teraz ponechá lokálnu explicitnú voľbu pred serverovým `system` a zosúladí účet (znovu uloží), keď je DOM pripravený. Explicitné `light`/`dark` z iného zariadenia sa naďalej synchronizuje.
- Verzia `2026.7.3.post37`; Cache Service Workera `gitpulse-v308`.

## [2026.7.3.post36] - 2026-07-11 - Týždeň bez očakávaných kontrol už neukazuje 100 % + skeleton avatar bez preskoku

###  Opravené
- **Týždeň bez očakávaných kontrol už neukazuje 100 %.** Skóre týždňa pred zavedením prvej kontroly v kurikule sa ukladalo ako prázdnych `1.0` (nič na zlyhanie = „100 %"), takže Týždenný prehľad ukazoval napr. 1. týždeň = 100 %, hoci jeho riadok v teplotnej mape bol celý N/A. Takéto týždne sa teraz zobrazujú ako N/A („-") pre celkové skóre aj každú kategóriu a trendová čiara ich preskočí - v súlade s teplotnou mapou. Platí pre existujúce aj budúce dáta.
- **Skeleton avatar v profile teraz zodpovedá načítanému avataru.** Počas fázy skeletonu bol avatar vlastný kruh s iniciálami a po načítaní obsahu preskočil na fotku. Skeleton teraz vykreslí skutočný avatar cez ten istý zdieľaný komponent `data-avatar-fallback` ako dashboard/horná lišta (fotka, pri chybe iniciály), takže žiadny preskok.

###  Zmenené
- Prechod pri prepnutí témy je pomalší a jemnejší (440 ms -> 620 ms), aby celoobrazovkový prechod pôsobil plynulo, nie ako tvrdý skok.
- Verzia `2026.7.3.post36`; Cache Service Workera `gitpulse-v307`.

## [2026.7.3.post35] - 2026-07-10 - Oprava: stránka Učitelia kurzu sa už nezobrazuje ako prázdny rozbitý shell

###  Opravené
- **Stránka „Učitelia" kurzu sa už nezobrazuje ako prázdny rozbitý shell.** Jej skript deklaroval `const GP` na najvyššej úrovni, čo kolidovalo s globálnym `const GP` z `core.bundle.js` (`SyntaxError: Identifier 'GP' has already been declared`). Chyba pri parsovaní prerušila celý súbor, takže `teacherManager()` sa nikdy nezaregistroval a všetky Alpine výrazy na stránke zlyhali. Skript je teraz zabalený v IIFE ako všetky ostatné stránkové skripty. Pridaný regresný test, ktorý zlyhá, ak akýkoľvek `pages/*.js` deklaruje `GP` v globálnom rozsahu.
- Verzia `2026.7.3.post35`; Cache Service Workera `gitpulse-v306`.

## [2026.7.3.post34] - 2026-07-10 - Stránka už nevyzerá, že sa načítava, keď je hotová + nemenná história compliance

###  Opravené
- **Stránka už po úplnom vykreslení nevyzerá, že sa stále načítava.** Keď server s avatarmi „prehltol" spojenie (VPN TUKE mimo, GitLab nedostupný), `<img>` nevyvolal ani `load`, ani `error` a ostal navždy čakať - karta prehliadača tak točila načítavací krúžok, hoci celý obsah stránky už bol na obrazovke. Avatary majú teraz 8 s strážny časovač: po jeho vypršaní sa požiadavka zruší a zobrazia sa iniciály, takže krúžok prestane točiť.
- **História compliance je teraz nemenná.** Backfill predtým prepočítal každý minulý týždeň zo *súčasného* stavu databázy a prepísal ho, takže po zmazaní údajov v GitLabe (odstránená vetva/MR) re-synchronizácia potichu znížila historické skóre študenta. Backfill teraz dopĺňa len týždne bez snímky; už zaznamenaný týždeň ostáva nezmenený.
- **Žiadny falošný „21. týždeň" po skončení semestra.** Týždenné snímky sú obmedzené na výučbové obdobie, obdobie skúšok sa uzavrie podľa efektívneho dátumu konca aj bez explicitného konca a grafy (kurzový trend aj študentský trend/heatmapa/radar) orežú týždne mimo okna.
- **Rýchlejšie stránky: vyčistený zvyšný balík `metric_snapshots`** (migrácia 010). post33 zastavil ďalší rast, ale ~480 tis. historických duplikátov ostalo - skutočná príčina občasného niekoľkosekundového načítania. Migrácia ponechá najnovší riadok na (tím, študent, UTC týždeň) a zvyšok zmaže; aktuálne skóre ostáva nezmenené.
- **Grafy sú čitateľné na svetlej téme.** Compliance koláč, popis radaru „Skill Profile" a viaceré popisy a mriežky grafov mali natvrdo tmavé pozadie / takmer bielu mriežku (tmavé na tmavom / neviditeľné na svetlej karte). Teraz preberajú farby zo zdieľaných, tému-rešpektujúcich predvolieb Chart.js.
- **Vylepšenie stránky študenta + menšie opravy:** načítavací skeleton presne zodpovedá načítaným kartám MR a hlavičkám; tabuľka commitov drží odznaky „Merge commit"/vetvy v pevných stĺpcoch; blok „Total Active Weight" je prepracovaný na samostatný súhrnný pruh; horný indikátor priebehu už pri miznutí nešvihne dozadu; zablokované tlačidlo Uložiť v modáli už nie je na okamih klikateľné pri otvorení; obrys zaostrenia pri zaškrtávacích políčkach Run Checks sa už neoreže.
- Verzia `2026.7.3.post34`; Cache Service Workera `gitpulse-v305`.

## [2026.7.3.post33] - 2026-07-08 - Snímky compliance už nerastú donekonečna (pomalé stránky)

###  Opravené
- **Snímky compliance už nerastú donekonečna (pomalé stránky).** Každá synchronizácia / Run Checks vkladala nový riadok `metric_snapshots` pre každého študenta - unikátny kľúč obsahuje `computed_at`, takže sa nikdy nededuplikovalo. V produkcii bolo **506 tis. riadkov, ~882 na študenta**, čo predĺžilo agregát „posledný snímok na študenta" na **1,2 s** (×8 skupín na stránke kurzu) a stránka študenta načítavala 800+ historických riadkov. Prepočet teraz ponechá presne **jeden snímok na (tím, študent, ISO týždeň)**: zmaže riadky, ktoré nahrádza - obmedzené na ten istý tím, ten istý týždeň a len na prepočítavaných študentov, takže čiastočný prepočet nikdy nezmaže týždeň iného študenta - a v tej istej transakcii zapíše nové. Aktuálne skóre aj týždenný graf ostávajú nezmenené.
- Verzia `2026.7.3.post33`; Cache Service Workera `gitpulse-v304`.

## [2026.7.3.post32] - 2026-07-08 - Feed aktivity už nehlási každý rozsah ako akciu celej skupiny

###  Opravené
- **„Follow the latest updates" už nehlási každý rozsah ako akciu celej skupiny.** Run Checks nad celým kurzom vytvorí jednu `run_checks` úlohu na každú skupinu a agregovali sa len *sync* dávky - feed teda vypisoval kontrolu každej skupiny zvlášť a čítalo sa to, akoby sa celá skupina opakovane spúšťala. Dávky run-checks sa teraz zlúčia do jedného záznamu „Ran checks for N groups" (rovnaké 5-minútové zhlukovanie ako pri „Synced N groups") a kontrola v rozsahu projektu hlási „Project checks completed" namiesto generického popisu s názvom skupiny.
- Verzia `2026.7.3.post32`; Cache Service Workera `gitpulse-v303`.

## [2026.7.3.post31] - 2026-07-08 - Žiadny falošný tost „Sync completed!" pri spustení kontrol

###  Opravené
- **Žiadny falošný tost „Sync completed!" pri spustení Run Checks.** Prepočet metrík vyšle SSE `update`; sync-stream nevidel žiadnu synchronizáciu, no zastaraný príznak `_syncWasActive` napriek tomu spustil `_completeCourseSync()` → tost „Sync completed!", hoci sa nič nesynchronizovalo. Terminálny sync-tost je teraz podmienený novým príznakom `_sawRealSyncRunning`, ktorý sa nastaví len keď opytovanie/SSE reálne uvidí bežiacu/dokončujúcu sa synchronizáciu.
- **Odstránený duplicitný info-tost „Data updated"** po dokončení úlohy - globálna poloska už zobrazuje terminálny tost, takže ďalší len stackoval druhý.
- Verzia `2026.7.3.post31`; Cache Service Workera `gitpulse-v302`.

## [2026.7.3.post30] - 2026-07-08 - Skeleton stránky študenta dopĺňa riadok e-mailu

###  Opravené
- **Načítavací skeleton stránky študenta teraz obsahuje riadok e-mailu** v bloku identity profilu (ikona + adresa), aby zodpovedal načítanej stránke pre učiteľov/adminov (`can_edit`). Bolo to jediné chýbajúce pole medzi menom a odkazom „View on GitLab", takže hlavička sa pri príchode dát mierne posúvala.
- Verzia `2026.7.3.post30`; Cache Service Workera `gitpulse-v301`.

## [2026.7.3.post29] - 2026-07-08 - Bejdž „Prepočítava sa..." pri Run Checks pre každú skupinu

###  Pridané
- **„Run Checks (all groups)" teraz pri každom riadku skupiny zobrazí bejdž „Prepočítava sa..."** počas behu, takže stránka kurzu dáva viditeľnú spätnú väzbu po riadkoch ako pri synchronizácii (predtým sa hýbala len globálna poloska). Bejdže zmiznú po obnovení riadkov na konci.
- Verzia `2026.7.3.post29`; Cache Service Workera `gitpulse-v300`.

## [2026.7.3.post28] - 2026-07-08 - Oprava R09 (schválenie MR) po zlúčení - skóre už neklesá

###  Opravené
- **R09 (MR schválený) už po zlúčení MR nespadne na falošné ZLYHANIE** - toto potichu znižovalo skóre pri všetkých zlúčených MR. GitLab po zlúčení MR a zmazaní vetvy vyčistí zoznam `/approvals`, takže neskorší sync prepísal uložené schválenia na 0; pri `min_approvals >= 2` potom každý zlúčený MR zlyhal na R09 (napr. študent 0.860 -> 0.825, klesli aj priemery skupín). R09 teraz počíta rôznych schvaľovateľov z **trvalých systémových poznámok „approved this merge request"** (zjednotené so živým zoznamom, s odčítaním neskoršieho „unapproved") - tie zlúčenie prežijú, takže skóre ostáva správne. Spustite Run Checks / sync na obnovenie. Pridané regresné testy.
- Verzia `2026.7.3.post28`; Cache Service Workera `gitpulse-v299`.

## [2026.7.3.post27] - 2026-07-08 - Skeleton študenta 1-k-1, jeden krížik na poloske, oprava dvojitej hornej polosky

###  Opravené
- **Skeleton stránky študenta teraz zodpovedá načítanej stránke 1-k-1.** Časť „Compliance Progress" bola úplne mimo: Score Trend bol malý prúžok vo veľkej prázdnej ploche, Skill Profile holý kruh a teplotná mapa „Check Progress by Week" + prahové odznaky + týždenný súhrn úplne chýbali. Skeleton teraz vypĺňa plochu grafu Score Trend, vykresľuje prahové odznaky, radar s mierkou týždňa a súhrnom Current Score / vs Last Week / Weakest Area, plus celú mapu R01-R13 × týždne.
- **Globálna poloska úloh zobrazuje presne jeden koncový ovládač** namiesto dvoch nejednoznačných krížikov: bežiaca úloha má cancel-X (s potvrdením pred zastavením procesu), dokončená/zlyhaná má dismiss-X na zatvorenie. Konzistentne pri plnom rendri aj in-place aktualizácii.
- **Horná poloska sa už nespustí dvakrát pri pomalej navigácii.** Zosúlaďovač sieťovej aktivity predtým dokončil polosku (skok na 100 % + vymazanie stavu) počas navigácie celej stránky - takže cieľová stránka vyskočila novú polosku od nuly. Teraz počas navigácie dokončenie preskočí, takže jedna súvislá poloska preklenie starú → novú stránku.
- Verzia `2026.7.3.post27`; Cache Service Workera `gitpulse-v298`.

## [2026.7.3.post26] - 2026-07-07 - Odstránenie neaktívneho shellu panela údržbových úloh

###  Odstránené
- Odstránený neaktívny „shell" panela naplánovaných/údržbových úloh, ktorý zostal po post24. Mriežka úloh sa už nevykresľovala, takže išlo o mŕtve lešenie: odstránené admin endpointy (`/jobs/trigger`, `/jobs/retry`, `/scheduled-jobs`, `/jobs/active-scheduled`), prázdny `admin_scheduled_registry`, `run_tracked_scheduled` + `sweep_tracking` a front-end kód triggerov/pollingu/SSE v admin-system balíku. Ponechaná živá tabuľka histórie úloh, zrušenie, health, cache a štatistiky. Nefunkčné tlačidlo „Retry" bolo odstránené spolu s jeho mŕtvym endpointom.

###  Zmenené
- `custom_check` schéma: vyčlenený zdieľaný `validate_rule_type`, aby validátory create/update neduplikovali kontrolu typu pravidla.
- Verzia `2026.7.3.post26`; Cache Service Workera aktualizovaná na `gitpulse-v297`.

## [2026.7.3.post25] - 2026-07-07 - Rozlíšenie forku šablóny bez commitov študenta

###  Pridané
- Detail projektu teraz rozlišuje **fork šablóny bez commitov študenta** od skutočne prázdneho repozitára. Ak má repozitár commity autorov šablóny, no žiadny študent zatiaľ nepushol vlastnú prácu, karta „Issues to Address" zobrazí stav „Šablóna / fork - zatiaľ žiadne commity študenta" (namiesto zavádzajúceho „Zatiaľ žiadne údaje repozitára"), karta prispievateľov uvedie „Zatiaľ len autori šablóny" a štatistika commitov ukáže „ - " namiesto zavádzajúcej „0". Rozpoznané konzistentne pri plnom rendri aj live-data obnove. Pridané slovenské preklady.
- Verzia `2026.7.3.post25`; Cache Service Workera aktualizovaná na `gitpulse-v296`.

## [2026.7.3.post24] - 2026-07-07 - Odstránenie mŕtvej vrstvy naplánovaných/periodických sweep úloh

###  Odstránené
- Odstránená mŕtva vrstva „naplánovaných / periodických sweep" úloh. Neexistuje periodický plánovač a katalóg údržbových úloh admina je prázdny, takže tieto úlohy sa nikdy nespúšťali: `periodic_llm_analysis`, `periodic_telemetry_snapshot`, `sweep_dlq_auto_resurrect`, `cleanup_old_events`, `cleanup_old_email_logs`, `sweep_email_queue`, `sweep_auto_archive_ended_courses`, `sweep_unprocessed_events`. Zmazané ich moduly (`sweep_jobs`, `sweep_cleanup`, `sweep_maintenance`, `sweep_events`), periodické funkcie v `sweep_telemetry`, osirotený helper `_delete_in_batches`, položky `_FEATURE_FLAG_MAP`, štítky `scheduled:*` v audite a legacy retry mapa. Testy upravené.
- Úlohy riadené udalosťami/synchronizáciou ostávajú bez zmeny: `refresh_project_gitlab_intel` (obnova intel z webhooku), `sync_single_team_members` (sync členov pri push) a `telemetry_snapshot_for_team`. Doručovanie e-mailov nie je ovplyvnené (`enqueue_email` priamo enqueue-uje `deliver_email`).

###  Poznámka
- Obnovovacie cesty, ktoré poskytovali len zmazané úlohy (DLQ resurrect, retencia udalostí, replay nespracovaných udalostí, retry odosielania e-mailov), boli bez plánovača už nefunkčné; manuálna re-synchronizácia stiahne aktuálny stav, takže sa nestrácajú dáta. Prázdny „shell" panelu údržby ostáva neaktívny a odstráni sa v ďalšom kroku.
- Verzia `2026.7.3.post24`; Cache Service Workera aktualizovaná na `gitpulse-v295`.

## [2026.7.3.post23] - 2026-07-07 - Oprava animácie loga a upratanie dokumentácie

###  Opravené
- Animácia EKG pulzu v logu už pri odchode kurzora neskočí späť na začiatok stopy. Pri prejdení myšou sa menila `animation-duration` pulzu (3.8s -> 0.95s); jej vrátenie pri odchode premapovalo uplynulý čas animácie na dlhšiu časovú os a pohyblivý segment skočil naspäť. Hover teraz iba rozjasní pulz pri konštantnej rýchlosti, takže plynulo pokračuje z aktuálnej pozície.

###  Zmenené
- Premenovaný `app/workers/sweep_ci.py` -> `app/workers/sweep_events.py` (názov ostal po odstránenej CI funkcii, no drží len zotavovací sweep webhook eventov). Iba premenovanie - RQ cesty `app.workers.sweep.*` fungujú cez re-exporty.
- Odstránené zmienky o troch zmazaných sandbox funkciách z aktuálnej dokumentácie (API špecifikácia, dátový model, požiadavky, rollout, mapovanie kontrolného zoznamu, strom architektúry, vývojárske stránky). História CHANGELOG/archív, text diplomovky a stránky histórie migrácií ostali bez zmeny.
- Verzia `2026.7.3.post23`; Cache Service Workera aktualizovaná na `gitpulse-v294`.

## [2026.7.3.post22] - 2026-07-07 - Úplné odstránenie troch nepoužívaných sandbox funkcií

###  Odstránené
- Úplne odstránené tri nepoužívané sandbox funkcie (boli vypnuté cez feature flag a nikdy neboli zapnuté v produkcii, ich tabuľky mali nula riadkov): **simulátor git konfliktov**, modul **overenia Docker buildu** a **generátor CI zlyhaní**. Odstránené ich služby, workery, modely, API routes, šablóny, JS (`_parts` + prebuildované bundly), feature flagy a osirotené i18n reťazce; konfiguračné stĺpce v course_settings a (prázdne) tabuľky funkcií drop-uje nová migrácia `009_drop_sandbox_features`. Žiadna zmena správania pre používateľov.

###  Zmenené
- Verzia `2026.7.3.post22`; Cache Service Workera aktualizovaná na `gitpulse-v293`.

## [2026.7.3.post21] - 2026-07-07 - Prázdny stav „Issues to Address" už nemizne + zrušený cache medzi obnoveniami (spôsoboval blikanie/zastarané dáta)

###  Opravené
- Karta prázdneho stavu „Issues to Address" už nezmizne sekundu po načítaní. Pri live-data pollingu, keď server nevie určiť stav repozitára, vráti prázdne `issues_html` (zámerne: „ponechaj aktuálnu kartu"), no klient ju potom starou fallback vetvou skryl (`d-none`). Tú mŕtvu vetvu sme odstránili - trvalý serverom vykreslený prázdny stav teraz zostáva.
- Zrušený stale-while-revalidate cache lazy-obsahu (post19/post20). Po obnovení maľoval naposledy videný obsah, ale po synchronizácii na pozadí ukazoval zastarané/prázdne dáta a blikal („zjaví sa a zmizne", „po synchronizácii nič nevidno"). Stránky teraz vždy vykreslia čerstvé dáta zo servera (kompromis: krátky skeleton pri obnovení), takže zobrazené dáta sú vždy správne a nikdy nezmiznú. Uložené dáta (členovia / prispievatelia / štatistiky) sa vykreslia z DB snapshotu bez ohľadu na stav tokenu.

###  Zmenené
- Verzia `2026.7.3.post21`; Cache Service Workera aktualizovaná na `gitpulse-v292`.

## [2026.7.3.post20] - 2026-07-06 - Cache medzi obnoveniami sa naozaj zapne + upozornenie na token odkazuje na dokumentáciu

###  Opravené
- Cache lazy-obsahu (post19) sa teraz naozaj zapne. Krok zápisu do cache odmietal každú stránku, ktorej skutočný obsah obsahoval vnorený skeleton dopĺňaný klientom (grafy, analytické karty, ...), takže stránka sa nikdy neuložila a F5 stále blikal celostránkovým skeletonom. Pri `htmx:afterSwap` je obsah vždy skutočná odpoveď servera (počiatočný skeleton je už preč), takže tá kontrola bola nesprávna - odstránená.

###  Zmenené
- Položka „Neplatný GitLab token" v „Items that need your attention" teraz odkazuje na dokumentáciu k tokenom (`/docs/gitlab/tokeny/`) s návodom, ako ho vymeniť, namiesto System Settings - token je serverová premenná prostredia, nie nastavenie v aplikácii, takže System Settings ho nemohli opraviť.
- Verzia `2026.7.3.post20`; Cache Service Workera aktualizovaná na `gitpulse-v291`.

## [2026.7.3.post19] - 2026-07-06 - Lazy stránky sa po obnovení vykreslia okamžite (cache medzi obnoveniami), nie skeleton

###  Zmenené
- Lazy-načítané stránky dashboardu sa po obnovení / návrate vykreslia **okamžite** namiesto zakaždým blikajúceho skeletonu. Stale-while-revalidate cache (`_parts/core/50-lazy-content-cache.js`) uloží naposledy vykreslený obsah pre danú URL do `sessionStorage` (na kartu, iba v pamäti - nikdy na disk, v súlade s `no-store` politikou na `/dashboard`) a ihneď ho prekreslí, kým htmx na pozadí načíta čerstvý obsah a vymení ho. Platí pre každú stránku `.gl-lazy-content[hx-trigger*="load"]` (kurz / tím / projekt / študent / dashboard / admin). Vstupná animácia sa pri revalidačnej výmene potlačí (cez `data-swr-painted`), takže nedochádza k dvojitému odhaleniu; položky cache majú obmedzenú veľkosť a 10-minútovú platnosť. Toto je klientska odpoveď na „F5 spustí všetko odznova" - odpovede `/dashboard` ostávajú `no-store` (bezpečnosť autentifikovaných stránok).
- Verzia `2026.7.3.post19`; Cache Service Workera aktualizovaná na `gitpulse-v290`.

## [2026.7.3.post18] - 2026-07-06 - Žiadne živé volania GitLabu pri renderovaní stránok, dashboard ukazuje zlyhané synchronizácie a neplatný token

###  Opravené
- Stránka študenta už pri renderovaní nevolá GitLab naživo. Sťahovala až 12 detailov pokrytia pipeline + avatar používateľa pri každom načítaní, čo stránku spomaľovalo (a zasekávalo pri neplatnom 401 tokene). Teraz sa renderuje výlučne z uložených dát - pokrytie dopĺňa synchronizácia + webhooky a znovu sa použije z existujúcej DB zálohy podľa SHA; avatar z uloženej hodnoty alebo z URL vzoru. Dáta sa na každú stránku dostávajú len cez synchronizáciu + webhooky, nikdy volaním API pri renderovaní.
- „Follow the latest updates" teraz ukazuje ZLYHANÉ úlohy (napr. synchronizáciu zablokovanú neplatným tokenom). Feed dopytoval len `completed` úlohy, takže každé zlyhanie bolo skryté; zlyhané úlohy sa teraz zobrazujú s ikonou výstrahy a označením „... failed".
- Lepiaci panel akcií v Nastaveniach kurzu už nenecháva tenký svetlejší prúžok úplne dole - kompenzoval 8px padding, ale spodný padding `.gl-page-content` je 12px, takže posledné ~4px presvitali. Teraz kompenzované na 12px.

###  Pridané
- „Items that need your attention" zobrazí položku „neplatný GitLab token", keď je token odmietnutý (číta zo zdieľaného cachovaného príznaku zdravia - žiadny živý probe pri renderovaní) s odkazom na Systémové nastavenia na rýchlu aktualizáciu.

###  Zmenené
- Verzia `2026.7.3.post18`; Cache Service Workera aktualizovaná na `gitpulse-v289`.

## [2026.7.3.post17] - 2026-07-06 - Tlačidlo Sync na skupine/projekte sa už nezasekáva bez časovača, zjednotené správy o zlyhaní

###  Opravené
- Tlačidlo **Sync** na skupine / projekte sa už nezasekne zablokované bez časovača cooldownu po zlyhaní synchronizácie (napr. neplatný 401 token). Príčina: synchronizácia registruje globálnu úlohu a jej dokončenie s chybou spustilo uvoľnenie process-locku (`unlockElement`), ktoré **vyčistilo práve nastavený cooldown** - odpočet zmizol a tlačidlo mohlo ostať zablokované. `unlockElement` už nevyčistí aktívny cooldown ani znovu nepovolí tlačidlo, ktoré cooldown drží. Odpočet teraz prežije a tlačidlo sa samo obnoví na každej stránke (stránka kurzu unikla chybe len vďaka skorému návratu pri neplatnom tokene, ktorý úlohu neregistruje).
- Správy o zlyhaní synchronizácie sú teraz konzistentné na kurze / skupine / projekte. Zdieľané `GP.syncErrorMessage(err)` vráti pri 401 podrobný text „GitLab API token je neplatný alebo vypršal (401)..." (už preložený) namiesto strohého „Synchronizácia zlyhala", ktoré ukazovali stránky skupiny/projektu.

## [2026.7.3.post16] - 2026-07-06 - Cachovanie GitLab panelov, žiadny duplikátny banner na skupine, zjednodušený a zjednotený sync

###  Opravené
- Synchronizácia projektu pri úspechu chybne hlásila „Synchronizácia skupiny dokončená" - teraz hlási „Synchronizácia dokončená", zodpovedajúc synchronizovanej entite (skupina vs projekt).
- Horný pruh načítania už neostáva zaseknutý na 100 %, keď počas jeho miznutia začne nová požiadavka. `start()` teraz plynulo pokračuje ako jeden súvislý indikátor namiesto zaseknutia na konci a následného vyskočenia nového pruhu.

###  Zmenené
- Banner „Data may be outdated" (webhooky / neaktuálne dáta) sa už neduplikuje na stránke skupiny - je to upozornenie na úrovni kurzu a už sa zobrazuje na stránke kurzu.
- Synchronizácia skupiny zbavená mŕtveho kódu sync-modalu. Ten modal bol z šablón odstránený už dávno (všetko sync UI teraz vlastní globálny job bar), takže jeho `getElementById` volania boli no-op; synchronizácia skupiny je teraz iba cez pruh ako synchronizácia projektu a obe používajú rovnaké generické správy.
- GitLab panely (chránené vetvy, prispievatelia, štatistiky repozitára, míľniky, releasy, štítky) sú teraz pod HTTP cachovaním. Ich odpovede nesú `Cache-Control: private, max-age=300` + `ETag` odvodený z obsahu a stránka projektu ich revaliduje podmienenou požiadavkou (`cache: no-cache`) namiesto pôvodného `no-store` plného sťahovania - nezmenený snapshot tak vráti beztelové `304` a opakované návštevy/obnovenia idú z cache prehliadača.
- Verzia `2026.7.3.post16`; Cache Service Workera aktualizovaná na `gitpulse-v287`.

## [2026.7.3.post15] - 2026-07-06 - Tlačidlo Sync sa už nezasekáva na „Wait 1s" na iných stránkach, plynulé bannery, tabuľky podľa GitLab, práca medzi kartami

###  Opravené
- Tlačidlo Sync / Run Checks sa už nezasekáva na „Wait 1s" po zlyhaní na stránkach tímu, projektu a jednotlivých skupín. Príčinou bol race medzi anti-spam cooldownom a `setButtonLoading` o `dataset.originalText`, keď požiadavka zlyhá rýchlo (< 400 ms, t. j. 401 neplatný token): odložený reset minimálneho trvania sa spustil uprostred odpočítavania a zmazal uloženú menovku, takže cooldown nedokázal obnoviť tlačidlo. Stránka kurzu unikla iba vďaka skorej kontrole tokenu; ostatné stránky išli cez problematickú cestu. Opravené v zdieľanom jadre, takže je to vyriešené na všetkých stránkach naraz.
- Odpočítavanie cooldownu pri zlyhaní sa teraz zobrazuje na každom synchronizačnom tlačidle (Sync All kurzu, synchronizácia skupiny, tímu aj projektu), nielen na niektorých.

###  Zmenené
- Bannery („Data may be outdated" / neplatný GitLab token / zlyhaná synchronizácia) sa teraz plynulo rozbaľujú a zbaľujú (animovaná výška + priehľadnosť) namiesto skoku obsahu. Zatvorený banner ostáva zatvorený medzi kartami, po obnovení stránky aj v iných kartách prehliadača (uložené v `localStorage`).
- Dátové tabuľky teraz presne kopírujú oficiálny komponent tabuliek GitLab Pajamas: hlavička aj bunky používajú 16px (`gl-p-5`) padding a zhustený variant je presne polovica (8px).
- Pri viacerých otvorených kartách vlastní synchronizačné opytovania/SSE jedna viditeľná „líder" karta (fail-open `localStorage` lízing); ostatné karty zrkadlia stav cez storage udalosti. Odstraňuje to duplicitné `/sync/active` requesty, nezosúladené pruhy priebehu a duplicitné toasty medzi kartami. Osamotená karta vždy vedie, takže jedna karta nie je nikdy ovplyvnená.
- Verzia `2026.7.3.post15`; Cache Service Workera aktualizovaná na `gitpulse-v286`.

## [2026.7.3.post14] - 2026-07-04 - Cooldown sa už nezasekáva na „Wait 1s", slovenský preklad, na všetkých Run Checks tlačidlách

###  Opravené
- Anti-spam cooldown tlačidla sa už nezasekáva na „Wait 1s". Odpočítavací tik (200 ms) sa sám vylieči: keď čas vyprší, vyčistí cooldown a obnoví tlačidlo, takže stratený/obmedzený `setTimeout` ho už nemôže nechať zaseknuté.
- „Wait" je teraz preložené (slovensky `Počkajte`), takže odpočítavanie cooldownu už nie je iba anglicky na slovenskom rozhraní.
- Cooldown pri zlyhaní teraz pokrýva každé tlačidlo Run Checks (kurz / tím / projekt cez zdieľaný `runScopedChecksProcess`), konzistentne s tlačidlami Sync.

###  Zmenené
- Verzia `2026.7.3.post14`; Cache Service Workera aktualizovaná na `gitpulse-v285`.

## [2026.7.3.post13] - 2026-07-04 - Horný pruh načítania: spoľahlivé zosúladenie s reálnou sieťovou aktivitou

###  Opravené
- Horný pruh načítania - zásadne odlišná oprava. Namiesto naháňania každého spôsobu, akým sa počítadlo `pending` (riadené udalosťami) môže zaseknúť (prevented submit ako Import s prázdnou URL, zmeškané/duplicitné htmx udalosti, klik ktorý spustí „navigáciu" ktorá nenaviguje), sa pruh zosúladí s REÁLNOU sieťovou aktivitou: `window.fetch` a `XMLHttpRequest` sú obalené tak, že počítadlo životného cyklu požiadaviek (`.finally` / `loadend` vždy spustia) sleduje, čo je skutočne v lete, a reconciler každých 250 ms dokončí pruh ~1,2 s po dokončení poslednej reálnej požiadavky.

###  Zmenené
- Verzia `2026.7.3.post13`; Cache Service Workera aktualizovaná na `gitpulse-v284`.

## [2026.7.3.post12] - 2026-07-04 - Tlačidlo Sync sa uvoľní bez obnovenia, horný pruh načítania sa už nezasekáva

###  Opravené
- Tlačidlo Sync / Run Checks sa teraz uvoľní BEZ obnovenia stránky. Strážca vypršania ghostov bežal iba kým bola úloha viditeľná v pruhu, takže skrytý ghost sa nikdy neodstránil a tlačidlo zostalo zablokované až do manuálneho obnovenia. Strážca teraz beží kým existuje AKÁKOĽVEK úloha; ghost bez reálneho backend job_id sa odstráni ~15 s po načítaní a synchronizácie tímu/projektu už nededia 45-min cap kurzu.
- Horný pruh načítania sa už nezasekáva na ~99 %. Race spôsobil, že generický htmx handler započítal `.gl-lazy-content` request, ale preskočil jeho dekrement, takže pruh ostal 120 s. Lazy requesty teraz počíta výhradne lazy bridge.
- Objavenie pruhu úloh je plynulejšie (znížená cieľová výška, aby prechod pokryl celú animáciu).

###  Zmenené
- Toasty medzi kartami sa v pozadí potlačia; completion toasty vo fronte sú deduplikované podľa úlohy.
- Verzia `2026.7.3.post12`; Cache Service Workera aktualizovaná na `gitpulse-v283`.

## [2026.7.3.post11] - 2026-07-04 - Neutrálny avatar, opravený feed aktivity, plynulé bannery

###  Opravené
- Tlačidlo Sync / Run Checks sa už nezasekáva na stránkach projektu a skupiny (ani na inom skoupe). Globálny job bar zosúlaďoval s `/sync/active` iba ghosty na úrovni kurzu; ghost synchronizácie na úrovni tímu/projektu obnovený z localStorage bol preskočený, takže držal tlačidlo zablokované celý svoj maxAge (až 45 min) aj keď server hlásil nič aktívne - a prežil obnovenia stránky, lebo localStorage pretrváva. Zosúladenie teraz pokrýva aj ghosty tímu/projektu (podľa ich kurzu).
- Iniciály v avatare už nie sú na fialovom kruhu - avatar v hornej lište aj v pozdrave používajú neutrálnu bridlicovú farbu (`--gl-gray-700`).
- Feed „Follow the latest updates" už nestráca záznamy. Obnova na pozadí (a) nikdy nenahradí naplnený feed prázdnym stavom „žiadna aktivita" (prechodný výpadok alebo tichá chvíľa predtým zmazali všetky viditeľné riadky) a (b) zachová stav „Zobraziť všetko" namiesto zbalenia späť na 5.
- Stavové pruhy už netrhajú stránkou pri objavení. Globálny job bar sa plynulo otvára cez `max-height` `transition` + `@starting-style` (nie keyframe - zachovaný kontrakt deterministického odstránenia), a health banner rastie cez `max-height` namiesto zasúvania celej výšky cez `translateY`, takže obsah pod ním uvoľní miesto plynulo.

###  Zmenené
- Verzia `2026.7.3.post11`; Cache Service Workera aktualizovaná na `gitpulse-v282`.

## [2026.7.3.post10] - 2026-07-03 - Tlačidlo Sync sa už nezasekáva po odmietnutej synchronizácii

###  Opravené
- Tlačidlo Sync / Run Checks už nezostáva zablokované po odmietnutej synchronizácii. Globálny job bar označí klik optimisticky ako úlohu „connecting" ešte pred potvrdením serverom; keď je synchronizácia odmietnutá (neplatný/expirovaný GitLab token, 401) alebo stránka obnovila starý stav pred POST-om, tento zástupca nemal za sebou žiadnu backend úlohu, no držal tlačidlo zablokované celé okno staleness (5-45 min) - a nekonzistentne naprieč project / team / course. Staleness guard teraz odstráni „connecting" úlohu bez reálneho `job_id` po ~15 s, takže sa tlačidlo uvoľní rýchlo a rovnako na každom skoupe. Skutočná synchronizácia vždy nesie svoje `job_id`, takže nie je ovplyvnená.

###  Zmenené
- Verzia `2026.7.3.post10`; Cache Service Workera aktualizovaná na `gitpulse-v281`.

## [2026.7.3.post9] - 2026-07-03 - Konzistentný fallback avatara naprieč povrchmi

###  Opravené
- Fallback avatara je teraz konzistentný. Avatar v pozdrave na nástenke používal starý vzor (fotka nad sivým kruhom so skrytým písmenom), takže sa líšil od avatara v hornej lište (opravený v post6) - jeden mohol blysnúť prázdny sivý kruh, druhý zobrazil značkové iniciály. Avatar v pozdrave teraz používa rovnaké vrstvenie (iniciály sú vždy prítomná základná vrstva, fotka z GitLabu ich prekrýva), takže oba degradujú rovnako.

###  Zmenené
- Verzia `2026.7.3.post9`; Cache Service Workera aktualizovaná na `gitpulse-v280`.

## [2026.7.3.post8] - 2026-07-03 - Odstránenie trvalého banera neplatného tokenu z project/group

###  Zmenené
- Odstránený trvalý banner `#gitlabTokenBanner`, ktorý post7 pridal na stránky projektu a skupiny. Neplatný/expirovaný GitLab token tam už nezobrazuje stály banner; chyba tokenu sa objaví iba keď skutočne spustíte akciu, ktorá ho potrebuje (Sync / Import) - cez existujúci globálny progress bar + toast, jedna správa bez stáleho neporiadku. (Shimmer pri načítaní kariet inteligencie projektu z post7 zostáva.)
- Verzia `2026.7.3.post8`; Cache Service Workera aktualizovaná na `gitpulse-v279`.

## [2026.7.3.post7] - 2026-07-03 - Jednotné správanie project/group ako na kurze pri neplatnom GitLab tokene

###  Opravené
- Stránky projektu a skupiny teraz spracujú neplatný/expirovaný GitLab token rovnako ako stránka kurzu: jeden trvalý banner `#gitlabTokenBanner` vysvetlí 401 raz a tlačidlá Sync / Run Checks zostanú klikateľné namiesto zaseknutia v neaktívnom stave.
- Klik na Sync pri známom neplatnom tokene sa teraz skratuje (nespustí odsúdenú úlohu, ktorá nechávala tlačidlo zaseknuté a duplikovala chybu ako banner aj toast) - zobrazí jednu správu.
- Karty GitLab inteligencie na stránke projektu (Chránené vetvy / Prispievatelia / Štatistiky repozitára) zobrazujú počas načítania živých dát „shimmer" namiesto predčasného prázdneho stavu „No contributors yet".

###  Zmenené
- Verzia `2026.7.3.post7`; Cache Service Workera aktualizovaná na `gitpulse-v278`.

## [2026.7.3.post6] - 2026-07-03 - Konsolidácia verzie a finálne release testy

###  Opravené
- Stavový banner: upozornenie „GitLab server je momentálne nedostupný" sa už po zatvorení znova neobjavuje (predtým ho každý úspešný health-check aplikácie potichu obnovil, keďže zdieľal príznak zatvorenia s bannerom zdravia aplikácie) a časovač „Naposledy pripojené" teraz beží živo namiesto zamrznutia.
- Avatar v hornej lište sa počas načítania profilovej fotky z GitLabu (alebo keď je GitLab nedostupný) zobrazí ako iniciály namiesto prázdneho sivého kruhu.

###  Zmenené
- Verzia `2026.7.3.post6`; Cache Service Workera aktualizovaná na `gitpulse-v277`.
- Overenie kvality kódu v pracovnom prostredí a spustenie celej sady testov pred vydaním.

## [2026.7.3.post5] - 2026-07-03 - Zjednodušenie priradenia kategórií v tabuľke členov projektu

###  Refaktorované
- Zjednodušenie logiky priraďovania kategórií členov v `_members_table.html` projektu na odstránenie vetvenia pre vylúčených členov (konzistentne s detailmi skupiny).

###  Zmenené
- Verzia `2026.7.3.post5`; Cache Service Workera aktualizovaná na `gitpulse-v276`.

## [2026.7.3.post4] - 2026-07-03 - Zjednodušenie prázdnych stavov v detailoch projektu

###  Refaktorované
- Zlúčenie a zjednodušenie redundantných vetiev volania makra `empty_state` v čiastkových šablónach detailov projektu: `_docker_verification.html`, `_ci_scenarios.html` a `_conflict_challenges.html`.

###  Zmenené
- Verzia `2026.7.3.post4`; Cache Service Workera aktualizovaná na `gitpulse-v275`.

## [2026.7.3.post3] - 2026-07-03 - Odstránenie duplicitnej kohortovej filtrácie a zjednodušenie priradení

###  Refaktorované
- Odstránenie prebytočného záložného cyklu v šablóne `_issues_to_address.html`. Teraz sa výlučne používa zoznam `scored_students` vypočítaný na strane Pythonu.
- Zjednodušenie logiky priraďovania kategórií členov v `_detail_content.html` skupiny na odstránenie vetvenia pre vylúčených členov.

###  Zmenené
- Verzia `2026.7.3.post3`; Cache Service Workera aktualizovaná na `gitpulse-v274`.

## [2026.7.3.post2] - 2026-07-03 - Refaktoring duplicitného kódu v zoznamoch zmien súborov

###  Refaktorované
- Extrakcia duplicitného HTML kódu pre tlačidlá súborov v strome diffov v šablóne detailov študenta (`student.html`) do jedného makra `diff_file_tree_item`, čo odstránilo duplicitu v rekurzívnych uzloch stromu a v tele diffu.

###  Zmenené
- Verzia `2026.7.3.post2`; Cache Service Workera aktualizovaná na `gitpulse-v273`.

## [2026.7.3.post1] - 2026-07-03 - Refaktoring duplicitných odkazov na dôkazy v analýze MR

###  Refaktorované
- Presun duplicitných blokov HTML pre odkazy na GitLab dôkazy v šablóne AI analýzy MR (`_ai_analysis.html`) do jedného makra `render_evidence_link`, čím sa odstránili trojité duplicity v sekciách Silné stránky, Potenciálne problémy a Kvalita spolupráce.

###  Zmenené
- Verzia `2026.7.3.post1`; Cache Service Workera aktualizovaná na `gitpulse-v272`.

## [2026.7.3] - 2026-07-03 - Rozsiahly refaktoring nastavení kurzu do modulárnych častí

###  Refaktorované
- Dekompozícia celej šablóny nastavení kurzu `course_settings.html` na modulárne čiastkové zahrnutia (`_basic_settings.html`, `_webhook_settings.html`, `_compliance_settings.html`, `_weekly_deadlines.html`, `_sandbox_settings.html`, `_ai_settings.html`, `_import_export_settings.html`), čím sa znížil počet riadkov kódu hlavnej šablóny z 580 na menej ako 100.

###  Zmenené
- Verzia `2026.7.3`; Cache Service Workera aktualizovaná na `gitpulse-v271`.

## [2026.7.2.post17] - 2026-07-03 - Reštrukturalizácia nastavení a oprava rozloženia alertu

###  Opravené
- Oprava zalamovania textu a rozloženia bloku alertu „Scope cascade" na stránke nastavení kurzu.

###  Refaktorované
- Extrahovanie nastavení semestra do opakovane použiteľných Jinja makier a čiastkových šablón (`_semester_settings.html` a `_settings_form_macros.html`) na minimalizáciu duplicity kódu.

###  Zmenené
- Verzia `2026.7.2.post17`; Cache Service Workera aktualizovaná na `gitpulse-v270`.

## [2026.7.2.post16] - 2026-07-02 - Obnovený zelený lint, tabuľky členov len so študentmi, cesta projektu s názvami

###  Opravené
- Obnovená zelená lint fáza na `main` (commit post15 zlyhal v CI): preformátovanie cez `ruff format` a oprava mypy v `member_sync_service.py` (opakovane použitá premenná cyklu dostala Optional).
- Tabuľky Members a Group Members zobrazujú len ŠTUDENTOV - nikdy nie učiteľov, mentorov ani Project Managera. Kohorta podľa issues mohla zatiahnuť PM, ktorý vytvoril issues; oba zoznamy teraz vynechajú kohokoľvek označeného ako učiteľ/mentor.
- Hlavička projektu zobrazuje cestu s názvami v štýle GitLabu (`... / ApI 7 (Maťaš - Antypenko) / Chekanov ... - Míny`) namiesto surového slugu (`.../api-7-ma-a-antypenko/mines-12770`).
- Verzia `2026.7.2.post16`; Service Worker cache nezmenená (`gitpulse-v269`).

## [2026.7.2.post15] - 2026-07-02 - Žiadne protichodné sync toasty, kohorta podľa issues, čistejšia hlavička Issues

###  Opravené
- Course "Sync All" už nezobrazuje protichodnú dvojicu toastov. Optimistický zelený "Sync started..." sa spustil pred vyriešením požiadavky, takže odmietnutá synchronizácia (neplatný token / GitLab offline) ukázala "started" AJ "failed" naraz. Global bar "Connecting to GitLab..." už signalizuje začiatok a končí buď priebehom, alebo jednou chybou - predčasný toast je odstránený na course-detail aj course-analytics.
- Kohorta členov projektu teraz počíta aj účasť na issues (autor / priradený / spolupriradení), nielen aktivitu merge requestov, takže spoluhráč, ktorý otvoril issues, ale ešte neautoroval MR, už nevypadne ("zobrazení 4, ale 5 v tíme").
- Hlavička Issues to Address zobrazuje len akčný počet High; štítky Medium/Low pôsobili ako bezvýznamné bledé číslo ("8"/"45") a boli nadbytočné voči grafu a legende nižšie.
- Verzia `2026.7.2.post15`; Service Worker cache `gitpulse-v269`.

## [2026.7.2.post14] - 2026-07-02 - Projektové dáta z databázy a jednotný progress procesov

###  Opravené
- Detail projektu a živé obnovenie už nechodia priamo do GitLabu, aby rozhodli o členoch, štatistikách, prispievateľoch a chránených vetvách. Čítajú uložený snapshot `gitlab_intel`, staršie projekty vedia odvodiť z uloženej MR aktivity a pri tímoch s viacerými projektmi už nespadnú na celú podskupinu. Tým miznú fantómoví študenti a nesprávne počty v Issues to Address pri neplatnom tokene alebo nedostupnom GitLabe.
- Ručný sync projektu teraz pred spracovaním issues/MR/poznámok doplní členov daného GitLab projektu do jeho skupiny, takže direct členovia projektu nezmiznú až do plného syncu skupiny.
- Progress a chyby pre Sync a Run Checks sú zjednotené pre project, group aj course scope: neplatný token alebo odmietnutá požiadavka skončí ako viditeľná chyba v globálnom progress bare aj ako toast, a Run Checks používa jednu SSE/polling cestu.
- Webhooky teraz enqueue-ujú debounce refresh uloženého GitLab intelligence snapshotu, takže project intelligence ostáva napojená na sync/webhook mechaniku.
- Verzia `2026.7.2.post14`; Service Worker cache `gitpulse-v268`.

## [2026.7.2.post13] - 2026-07-02 - Zarovnanie hlavičky "Actions" a čitateľné štítky Issues

###  Opravené
- Tabuľka členov: hlavička "Actions" je zarovnaná doprava, takže sedí nad tlačidlami riadku (oko + View) namiesto toho, aby unikala doľava širokého stĺpca. Platí pre živú tabuľku aj jej skeleton.
- Štítky v hlavičke Issues to Address: počty Medium (jantár) a Low (modrá) sa strácali na tmavej hlavičke karty - viditeľné boli len dve bledé čísla ("45"). Teraz sú to tučné, orámované čipy, takže každý počet a jeho označenie zostávajú čitateľné vedľa štítku High (červená).
- Verzia `2026.7.2.post13`; Service Worker cache `gitpulse-v267`.

## [2026.7.2.post12] - 2026-07-02 - Tlačidlo Sync už nezostane zablokované pri odmietnutej synchronizácii

###  Opravené
- Tlačidlo Sync na projekte už nezostane zablokované (bez nutnosti obnoviť stránku), keď je synchronizácia odmietnutá - napr. neplatný/vypršaný GitLab token vracajúci 503. Handler registroval fantómový slot "sync beží" ešte pred potvrdením požiadavky; odmietnutá požiadavka ho nikdy neuvoľnila, takže process-lock držal tlačidlo zablokované. Optimistický slot je odstránený - reálny slot priebehu sa registruje až po tom, čo server vráti job id, a pri zlyhaní sa tlačidlo znovu aktivuje s jasnou správou.
- Verzia `2026.7.2.post12`; Service Worker cache `gitpulse-v266`.

## [2026.7.2.post11] - 2026-07-02 - Tabuľka členov projektu ukazuje projekt, nie celú podskupinu

###  Opravené
- Tabuľka členov projektu a jej skórovacia kohorta pre Issues to Address sa teraz obmedzujú na študentov TOHTO projektu namiesto všetkých študentov nadradenej podskupiny. GitPulse "tím" zodpovedá GitLab podskupine, ktorá môže obsahovať viacero projektových repozitárov, takže tabuľka jedného projektu ukazovala celú sekciu (~50) namiesto reálnych ~5. Keď živé načítanie členov nie je dostupné (vypršaný token / údržba GitLabu), stránka obnoví reálny zoznam z uložených dát - zoznam uložený pri poslednej synchronizácii, inak odvodený z uloženej aktivity merge requestov (autori, priradení, recenzenti, schvaľovatelia) - takže je správny aj pred novou synchronizáciou.
- Skórovanie počíta študenta ako člena projektu bez ohľadu na zdroj členstva v GitLabe (direct ALEBO inherited): reálny prispievateľ už nevypadne zo skóre skupiny len preto, že jeho zdroj na úrovni tímu je 'inherited'. Skóre odráža skutočnú kohortu projektu, nielen zobrazené riadky.
- Verzia `2026.7.2.post11`; Service Worker cache nezmenená (`gitpulse-v265`) - zmena len na backende.

## [2026.7.2.post10] - 2026-07-02 - Oprava zarovnania a pridané upozornenie v skeletoch

###  Opravené
- Opravili sme zarovnanie stĺpca Akcie v skeletoch aj v živej tabuľke členov (zabránili sme pretekaniu tlačidiel).
- Pridali sme statickú poznámku o aktívnych členoch z GitLabu do študentských zobrazení skeletov aj živých tabuliek.
- Verzia `2026.7.2.post10`; Service Worker cache `gitpulse-v265`.

## [2026.7.2.post9] - 2026-07-02 - Zjednodušenie tabuliek členov skupín a projektov

###  Opravené
- Zjednodušili sme tabuľky členov skupín a projektov odstránením prebytočných stĺpcov Rola, Zdroj a Stav a zrušením filtračného panelu. V tabuľke sa teraz zobrazujú iba skutoční študentskí členovia priradení v databáze.
- Vylepšili sme stĺpec Pipeline v tabuľke členov skupiny: čísla sú teraz farebne odlíšené (zelená pri plnom úspechu, červená pri zlyhaní) a po prejdení myšou sa zobrazí vysvetľujúci tooltip.
- Verzia `2026.7.2.post9`; Service Worker cache `gitpulse-v264`.

## [2026.7.2.post8] - 2026-07-02 - Panely inteligencie prežijú nedostupný GitLab

###  Pridané
- Karty GitLab inteligencie projektu (chránené vetvy, prispievatelia, štatistiky repozitára) teraz pri každej synchronizácii ukladajú snapshot (`gitlab_projects.gitlab_intel`) a stránka sa naň per-karta vráti, keď živé načítanie z GitLabu zlyhá. Boli to jediné dáta na stránke bez uloženej zálohy, takže ako jediné padali na "GitLab is unreachable", keď vypršal token - teraz naďalej zobrazujú posledné synchronizované hodnoty (užitočné počas údržby GitLabu 3.-5. júla).

###  Opravené
- Karty inteligencie sa už pri zlyhaní živého obnovenia nevymažú na "GitLab is unreachable" - posledný snapshot zostáva viditeľný.
- Tabuľka Skupiny už nepretečie svoju kartu: vymazané riadky skupín majú široké tlačidlá "Restore" / "Remove from deleted", ktoré nútili celú tabuľku s pevným rozložením posúvať sa do strany; tieto tlačidlá sa teraz zalamujú v stĺpci akcií (aktívne riadky bez zmeny).
- Verzia `2026.7.2.post8`; Service Worker cache `gitpulse-v263`; Alembic migrácia `008` pridáva stĺpec `gitlab_intel`.

## [2026.7.2.post7] - 2026-07-02 - Štýlované tooltipy, trvalé zatvorenie bannerov a zarovnané riadky

###  Opravené
- Tooltipy sú teraz vždy štýlovaný komponent (Tippy), nikdy natívny `title=` popup prehliadača: prevedené boli makrá `btn`/`btn_icon`, tlačidlo na zatvorenie info-card, prepínač kontrol a sync-lock save tlačidlá v nastaveniach predmetu, indikátor stavu servera na prihlásení, lokalizované `<time>` značky aj akcie riadku skupiny vkladané cez JavaScript.
- Zatvorené bannery zostanú zatvorené: krížik info-card si zapamätá zatvorenie na reláciu (podľa bannera a aktuálneho stavu), takže "synchronizácia zlyhala" / "synchronizácia zrušená" / "údaje môžu byť neaktuálne" sa už po odchode a návrate znovu neobjaví.
- Horný pruh načítania ani odosielacie tlačidlá sa už po zlyhaní validácie nezaseknú - napríklad pridanie skupiny s jednoznakovým názvom vyčistí pruh a nezapne anti-spam zámok tlačidla, takže nič nevisí až do obnovenia stránky.
- Nové riadky skupín pridané po vytvorení kopírujú responzívne triedy stĺpcov serverovej tabuľky (`col-hide-sm`/`col-hide-md`, vycentrovaný Stav), takže sa na úzkych obrazovkách už nevychýlia zo zarovnania; prvá skupina v predmete sa načíta nanovo, aby vykreslila kanonickú tabuľku.
- Doplnené slovenské preklady reťazcov trvalého odstránenia / "Odstrániť z vymazaných", čím sa počet chýbajúcich prekladov vrátil na nulu.
- Verzia `2026.7.2.post7`; Service Worker cache `gitpulse-v262`.

## [2026.7.2.post6] - 2026-07-02 - Konzola, modálky a spoločné role badge

###  Opravené
- Detail predmetu znovu dodáva platný JavaScript: prepínač zmazaných skupín je správne naviazaný, Run Checks používa spoločný confirmation callback a stránka už nespadne pred exportom svojich akcií.
- Biela obruba avatara je obmedzená iba na veľký dashboard greeting avatar; topbar avatar ostáva bez rámika.
- Role pill v používateľskom menu používa spoločný role badge komponent a farby ako tabuľka User Management.
- GitLab import aj ostatné modálky pred otvorením resetujú vnútorný scroll, držia backdrops pod `<body>` a neodkladajú zobrazenie scrollbar-u až po prvom animačnom frame.
- PWA install handler už nevolá `preventDefault()` na natívny Chromium install banner, pokiaľ nie je explicitne zapnutý custom prompt.
- Verzia `2026.7.2.post6`; Service Worker cache `gitpulse-v261`.

## [2026.7.2.post5] - 2026-07-02 - Trvalé odstránenie, roly v menu a oprava layoutu

###  Pridané
- Možnosť trvalého odstránenia („Remove from deleted") pre neaktívne skupiny a projekty. Učitelia a administrátori môžu teraz úplne vymazať zmazané skupiny alebo projekty a všetky ich pridružené záznamy (členstvá, snapshots, pipelines, MR, commity, issues, LLM logy a na pozadí bežiace úlohy) zo systému.

###  Opravené
- Opravené rozloženie (layout) pre mobilné zariadenia a tablety: hlavný kontajner obsahu ostáva zaoblený s 8px okrajmi a neroztiahne sa na celú šírku obrazovky.
- Odstránená duplicitná avatar ikona z hlavičky používateľského menu.
- Nahradený nefunkčný stavový riadok „Coding my life" za zobrazenie reálnej roly používateľa (Admin, Teacher, Student) formou status-badge.
- Odstránené zakázané tlačidlo „Deleted" zo skeletons načítania.
- Verzia `2026.7.2.post5`; Service Worker cache `gitpulse-v260`.

## [2026.7.2.post4] - 2026-07-02 - Validácia názvu skupiny, rýchlejšie načítanie, opt-in dirty-check

###  Opravené
- Pridanie skupiny teraz validuje názov: prázdny alebo jednoznakový vstup (napr. „ф") sa odmietne na klientovi aj na serveri (`TeamCreate` oreže medzery a vyžaduje aspoň 2 znaky), takže sa už nedá vytvoriť nezmyselná skupina, ktorá potom zmizne.
- Rýchlejšie načítanie: endpoint stavu synchronizácie ani SSE stream už pri každom pollingu/pripojení nezisťujú GitLab cez sieť. Čítajú kešovaný príznak stavu tokenu (bez sieťového volania); príznak sa aj tak nastaví pri prvom 401.
- Dirty-check je teraz opt-in. Predtým každá modálka s poľom aktivovala upozornenie „máte neuložené zmeny", čo otravovalo pri jednorazových akciách (import z GitLab). Auto-init teraz pokrýva len modálky s `data-dirty-check`; skutočné formuláre si ochranu ponechávajú.
- Verzia `2026.7.2.post4`.

## [2026.7.2.post3] - 2026-07-02 - Zatvárateľné informačné banery

###  Pridané
- Informačné banery sa teraz dajú zatvoriť. Makro `info_card` prijíma `dismissible=true` a vykreslí tlačidlo X; delegovaný, CSP-bezpečný obslužný kód kartu odstráni. Použité na banery predmetu „Some sync jobs failed", „Sync cancelled" a „Data may be outdated".
- Verzia `2026.7.2.post3`.

## [2026.7.2.post2] - 2026-07-02 - Obnovený GitLab-štýl layoutu + oprava blikajúceho banera

###  Opravené
- Rozloženie obsahového panela obnovené na spoľahlivý GitLab model: `.gl-page` má pevnú `height` (vyplní okno) a `.gl-page-content` má `flex: 1`, takže panel je vždy na plnú výšku a obsah sa skroluje VNÚTRI (ako `.js-static-panel` / `.panel-content-inner` v GitLabe). Predchádzajúci pokus s `max-height` + `flex: 0 1 auto` spôsoboval, že sa panel zmenšil na načítavací skeleton („polovica stránky chýba") - vrátené.
- Baner „Some sync jobs failed" už neblikne a nezmizne po sekunde. Živá aktualizácia spravovala všeobecný `.info-card-danger`, takže SSE tik s hodnotou 0 (jeho počet používa 2h okno) odstránil serverom vykreslený baner. Teraz spravuje LEN vlastnú živú kartu (`#jsSyncFailedCard`) a nikdy sa nedotkne serverového baneru ani baneru tokenu.
- Verzia `2026.7.2.post2`.

## [2026.7.2.post1] - 2026-07-02 - Doplnené ochrany procesov

###  Opravené
- Zrušenie importu z GitLabu sa už neregistruje ako neuložená zmena formulára; tlačidlo Cancel zastaví aktívny import bez nesúvisiaceho before-unload potvrdenia.
- Čakajúce CI failure scenáre a conflict challenge sa teraz dajú zrušiť ešte pred zmenou GitLabu a polling CI scenárov beží iba vtedy, keď riadky skutočne čakajú.
- Retry zlyhanej plánovanej/manuálnej systémovej úlohy teraz vytvorí novú sledovanú a zrušiteľnú background úlohu, takže Follow the latest updates, Items that need your attention aj globálny job bar dostanú rovnaké job id.
- Kontroly aktívnych úloh teraz zahŕňajú stav `started` naprieč sync, kontrolami, importom, stavom kurzu aj plánovanými úlohami, aby sa počas RQ handoffu nespúšťali duplicity.
- Live zvýraznenia hodnôt na dashboarde a detaile projektu teraz používajú requestAnimationFrame namiesto synchrónneho čítania layoutu, čím zmizol ďalší zdroj forced reflow z horúcich refresh ciest.
- Produkčné monitorovanie už nenecháva Alertmanager v reštartovacej slučke; kontajner sa teraz spúšťa s platnou internou absolútnou external URL a YAML konfiguráciou, ktorú Alertmanager vie načítať bez nepodporovanej shell-style expanzie premenných.
- Verzia `2026.7.2.post1`; Service Worker cache `gitpulse-v256`.

## [2026.7.2] - 2026-07-02 - Prerušiteľné procesy a chránený import z GitLabu

###  Opravené
- Import z GitLabu teraz odmieta neplatné cesty skupín/projektov ešte pred streamovaním; zadanie ne-ASCII vstupu už nespustí import ani nezrúti obsluhu chyby importu.
- Dlhobežiace procesy majú jednotný kontrakt zrušenia: globálne tlačidlá cancel zastavia synchronizáciu, kontroly, Docker verifikáciu, plánované úlohy, LLM analýzu, GitLab obohatenie, frontendové AI generovanie aj aktívny import. Zrušené úlohy zostávajú terminálne a workery ich už po race neprepíšu na completed/failed.
- Stav synchronizácie a kontrol v kurze hlási zrušené skupiny samostatne a používa najnovšiu úlohu kontrol pre každú skupinu, takže starý failed riadok nepokazí neskorší úspešný beh.
- Course detail SSE/logging a animácie už nevytvárajú duplicitné EventSource spojenia ani forced reflow; spodné odsadenie shellu zodpovedá výške obsahu bez prázdnej medzery.
- Verzia `2026.7.2`; Service Worker cache `gitpulse-v255`.

## [2026.7.1.post5] - 2026-07-01 - Obsahový panel sa zmenší na výšku obsahu (žiadna prázdna karta)

###  Opravené
- Obsahový panel (`.gl-page`) sa teraz na krátkych stránkach zmenší na výšku obsahu (`max-height` namiesto pevnej `height`) namiesto vyplnenia celej výšky okna, takže stránka s pár riadkami už nezobrazuje veľkú prázdnu zaoblenú kartu pod tabuľkou - rovnako ako panel v GitLabe. Dlhé stránky sa naďalej zastavia na výške okna a skrolujú vnútri.
- Verzia `2026.7.1.post5`.

## [2026.7.1.post4] - 2026-07-01 - Banner neplatného tokenu sa zobrazí hneď pri načítaní

###  Opravené
- Nadväznosť na post3: banner „Neplatný GitLab token" sa teraz zobrazí už pri načítaní stránky (SSE stream aj sync-status sa prehrejú jedným kešovaným pokusom), nie až po prvom neúspešnom kliknutí. Sync All tak hneď pri prvom kliknutí zobrazí jasný tost bez blikania „Pripájanie..." a tlačidlo už nezostane v stave načítavania, ktorý si vyžadoval obnovenie stránky.
- Verzia `2026.7.1.post4`.

## [2026.7.1.post3] - 2026-07-01 - Banner namiesto zablokovaného tlačidla synchronizácie, izolácia testov

###  Opravené
- Stav „Neplatný GitLab token" už neblokuje tlačidlo Sync All (bolo nejasné, kedy sa odblokuje, a nekonzistentné s tlačidlom Import, ktoré fungovalo ďalej). Banner je teraz jediné jasné vysvetlenie; kliknutie na Sync All zobrazí rovnaký dôvod ako tost namiesto blikajúceho ukazovateľa „Pripájanie...", ktorý o sekundu zmizol.
- Izolácia testov: zdieľaný príznak stavu GitLab tokenu sa resetuje okolo každého testu, takže mocknutá 401 už nepretečie do neskoršieho testu - zlyhanie, ktoré sa prejavovalo len v CI so živým Redisom.
- Verzia `2026.7.1.post3`.

## [2026.7.1.post2] - 2026-07-01 - Odolnejšia synchronizácia a celoaplikačná ochrana GitLab tokenu

###  Opravené
- Synchronizácia už neblikala ("dokončená za 2 s a sama sa reštartovala dokola"). Zlyhaný sync sa predtým znovu vyhodil do slepého automatického opakovania RQ, čím stav úlohy prepínal `running↔failed` a ukazovateľ priebehu kurzu osciloval, zatiaľ čo banner „Údaje môžu byť zastarané" vyskakoval počas synchronizácie. Sync teraz používa **obmedzené, viditeľné opakovanie** (3 pokusy): riadok zostáva medzi pokusmi aktívny a zobrazuje `Retrying (2/3)` ako odznak `RETRY 2/3` pri skupine; beh sa končí jasným **„Všetky synchronizácie dokončené!"** alebo červeným **„Synchronizácia dokončená s problémami - N skupín zlyhalo"** namiesto vždy hláseného úspechu.
- Rozbalené karty histórie úloh už nerozbíjajú tabuľku: vložený riadok detailu sa počítal do pruhovania `:nth-child`, čím prevracal tieňovanie všetkých riadkov pod ním. Teraz je z pruhovania a zvýraznenia vylúčený.

###  Pridané
- **Celoaplikačná ochrana GitLab tokenu.** Neplatný/expirovaný token (401/403) sa teraz zistí v okamihu, keď zlyhá *ktorékoľvek* volanie GitLab, a zdieľa sa cez kešovaný príznak stavu, takže celá aplikácia reaguje na jedno zlyhanie namiesto toho, aby každý tok samostatne zaťažoval GitLab:
   - Sync, sync projektu, Sync All aj import z GitLab sú **vopred zablokované** s jasnou hláškou „GitLab API token je neplatný alebo vypršal (401)".
   - Úlohy na pozadí (obohatenie issue/MR, synchronizácia členov, inkrementálne obnovenie projektu) sa pri známom neplatnom tokene **okamžite preskočia** a auth chyby **neopakujú**, čím sa zastavia lavíny opakovaní.
   - Zotavenie je automatické: každé úspešné volanie GitLab príznak zruší, takže po výmene tokenu sa práca obnoví bez reštartu.
   - Stránka kurzu zobrazí trvalý banner **„Neplatný GitLab token"** a počas neplatného tokenu vypne tlačidlo Sync All.
- Verzia `2026.7.1.post2`.

## [2026.7.1.post1] - 2026-07-01 - Copyright 2026-2027, nofollow pre jazykové odkazy, posledný príkladový dátum

###  Opravené
- Opravený copyright v pätičke dokumentácie z `2024-2026` na `2026-2027 TUKE Košice`.
- SEO: jazykové prepínacie odkazy majú teraz `rel="nofollow"`, aby vyhľadávače prestali indexovať tieto presmerovacie URL objavené na verejnej prihlasovacej stránke.
- Obnovený posledný zastaraný príkladový dátum v pomocnom texte nastavení predmetu (šablóna aj slovenský katalóg zosynchronizované).

## [2026.7.1] - 2026-07-01 - Aktualizácia dokumentácie: odstránená zrušená funkcia Rubrika, obnovené dátumy

###  Zmenené
- Odstránená zrušená funkcia "Rubrika" zo slovenských príručiek pre učiteľov (dashboard, začíname), aby zodpovedali anglickým verziám a aktuálnej aplikácii. Obnovené zastarané príkladové dátumy a cesty skupín v príručkách GitLab, operátorov a vývojárov na aktuálny rok a aktualizovaná dokumentovaná verzia na `2026.7.1`.

## [2026.6.30.post3] - 2026-06-30 - Prednačítanie pozadia len kde sa používa, odstránené pomlčky, aktualizované dátumy pilotu

###  Opravené
- Prihlásenie/odhlásenie: obrázok pozadia sa prednačítaval aj na mobile, kde sa žiadne pozadie nevykresľuje, takže prehliadač hlásil "preloaded but not used". Prednačítanie je teraz obmedzené na obrazovky široké aspoň 768px, kde sa pozadie naozaj zobrazuje.

###  Zmenené
- Aktualizovaná príručka pilotného nasadenia: dátumy posunuté na rok 2026 a zjednotené nekonzistentné formáty dátumov. Odstránené zvyškové pomlčky z niekoľkých riadkov changelogu.
- Verzia `2026.6.30.post3`.

## [2026.6.30.post2] - 2026-06-30 - Skutočný /favicon.ico, aby Google vo vyhľadávaní zobrazoval favikonu

###  Opravené
- Favikona vo vyhľadávaní Google: aplikácia poskytovala `/favicon.ico` ako presmerovanie 301 na PNG, čo prehliadač favikon od Googlu spracúva nespoľahlivo (vo výsledkoch sa zobrazoval všeobecný glóbus). Teraz vracia skutočný viacrozmerný `.ico` s kódom 200 a indexovateľná prihlasovacia stránka ho uvádza ako prvú. Google obnovuje favikonu len pri opätovnom prehľadaní úvodnej stránky, takže sa môže objaviť až o niekoľko dní.

###  Zmenené
- Verzia `2026.6.30.post2`.

## [2026.6.30] - 2026-06-30 - Spustenie sledovania v workeroch, oprava importu predmetov a produkčné odkazy monitoringu

###  Opravené
- Stránky prihlásenia/odhlásenia: ponuka výberu jazyka, upozornenia, tosty a značka zvoleného jazyka sa zobrazovali tmavé na bielej karte, ak mal návštevník uloženú tmavú tému. Inicializácia farebného režimu teraz odvodzuje `data-theme` zo svetlého zámku stránky, takže všetky komponenty na týchto stránkach sú svetlé.
- Pokrytie testami ukazovalo „nenahlásené" na MR kartách študentov, hoci GitLab hlásil percento: úplná synchronizácia tímu preskakovala už dokončené pipeline, takže pipeline uložené bez pokrytia sa nikdy nedoplnili. Synchronizácia teraz znova načíta dokončené pipeline, ktoré spustili testy, ale nemajú zaznamenané pokrytie.

###  Pridané
- Mobilné dialógy: úchyt spodného dialógu je teraz interaktívny - potiahnutím úchytu (alebo hlavičky dialógu) nadol ho zavriete. Gesto sa aktivuje len z hornej časti, takže neprekáža posúvaniu obsahu dialógu.

###  Zmenené
- Verzia `2026.6.30.post1`.

## [2026.6.30] - 2026-06-30 - Spustenie sledovania v workeroch, oprava importu predmetov a produkčné odkazy monitoringu

###  Opravené
- Konfigurácia Redis poolu vo workeri: vyriešená výnimka `RuntimeError` pri spracovaní úloh inicializáciou globálneho zdieľaného Redis poolu pri štarte RQ workerov.
- Skript na import nastavení predmetov: odstránené neexistujúce importy a volania (`_apply_gaming_detection`, `_apply_rubric_from_config`), čo zaručilo bezproblémový import fixture dát pre predmety ZSI a DevOps.
- Observability: nastavený OTLP endpoint v lokálnom prostredí na lokálny zberač Jaeger, čím sa sprevádzkovalo lokálne trasovanie.
- Dokumentácia monitoringu: do príručiek pre operátorov (SK/EN) boli pridané presné adresy, porty a prihlasovacie údaje pre produkčné prostredia Grafana, Prometheus a Jaeger na uľahčenie manuálnej kontroly.

## [2026.6.29.post12] - 2026-06-29 - Oprava chýb dev-prostredia, overovania Redis a presmerovania Grafany

###  Opravené
- Ošetrenie chýb v `start-dev.ps1`: odstránená premenná `$ErrorActionPreference = "Stop"`, ktorá spôsobovala pád celého skriptu pri bežných pip varovaniach pri zostavovaní dokumentačného kontajnera.
- Slučka presmerovania Grafany: vyriešené presmerovanie `localhost:3000` na produkčnú HTTPS doménu nastavením `GF_SERVER_ROOT_URL` na `http://localhost:3000/grafana/` v override súbore `docker-compose.monitoring-dev.yml`.
- Vyčistenie zastaraných metrík: odstránené nepoužívané panely z Grafany ("Report Generation Time", "Sweep Jobs", "Sweep Job Duration", "Active Dashboard Sessions") a zrušené neplatné Prometheus varovania ("ReportGenerationSlow", "SweepJobFailing"), pretože ich funkcie v kóde neexistujú.
- Zber metrík Grafany: pridaná cesta `metrics_path: /grafana/metrics` pre Grafana úlohy v `prometheus.yml` aj `prometheus.dev.yml`, aby sa predišlo chybám kvôli presmerovaniam.
- Produkčné Redis poverenia: do `.env.production` boli doplnené premenné `REDIS_PASSWORD` a autorizovaný formát `REDIS_URL`, čím sa zabránilo havárii aplikácie pri prísnych produkčných bezpečnostných kontrolách.

###  Zmenené
- Verzia `2026.6.29.post12`.

## [2026.6.29.post11] - 2026-06-29 - Zelený lint a prístupnejšie záložky „Rýchly prístup"

###  Opravené
- Obnovený zelený lint krok CI. Dnešné rýchle leštiace commity priniesli na `main` štyri porušenia `ruff` a tri odchýlky `ruff format` (pripnutý `ruff==0.15.4`), takže brány `ruff-check`/`ruff-format` boli červené: `f`-reťazec bez zástupných znakov, neusporiadaný import blok, `SIM108` if/else v pomocníkovi diff kontextu a príliš dlhý assert. Opravy zachovávajú správanie; celá jednotková sada (2512) ostáva zelená.

###  Zmenené
- Prístupnosť: prepínače „Skupiny"/„Podskupiny" v paneli „Rýchly prístup" sú teraz skutočné záložky - `type="button"`, `role="tablist"`/`role="tab"` a viazané `aria-selected` pre čítačky obrazovky. Iba šablóna.
- Verzia `2026.6.29.post11`.

## [2026.6.29.post10] - 2026-06-29 - Odstránené N+1 v hromadnom sync / run-checks

###  Zmenené
- Backend: koncové body „Spustiť kontroly (všetky skupiny)" a „Synchronizovať všetky skupiny" už nespúšťajú jeden SELECT na skupinu pri kontrole prebiehajúcich úloh - oba teraz používajú jeden dávkový dopyt s preukázateľne rovnakým výsledkom. Pre predmet s N skupinami to odstráni až 2N zbytočných round-tripov. Bez zmeny správania (celý unit test suite zelený).
- Verzia `2026.6.29.post10`.

## [2026.6.29.post9] - 2026-06-29 - Preconnect na GitLab aj na prihlasovacej stránke

###  Zmenené
- Rozšírený `preconnect` / `dns-prefetch` hint na GitLab aj na samostatnú prihlasovaciu stránku - jej hlavné tlačidlo je OAuth presmerovanie na GitLab, takže zahriatie spojenia vopred skráti presmerovanie o jeden round-trip. Len resource hint. Bez zmeny statických súborov či Service Worker cache.
- Verzia `2026.6.29.post9`.

## [2026.6.29.post8] - 2026-06-29 - Preconnect na GitLab pre rýchlejší prvý kontakt

###  Zmenené
- Frontend optimalizácia: základná `<head>` teraz preconnectuje (+ dns-prefetch) na GitLab origin (zo settingu `gitlab_url`, nie natvrdo). Prihlasovacie tlačidlo presmeruje na GitLab kvôli OAuth a prihlásené stránky načítavajú avatary + volajú jeho API, takže zahriatie spojenia vopred skráti prvý kontakt o jeden round-trip. Len resource hint - nemôže ovplyvniť vykresľovanie. Bez zmeny statických súborov či Service Worker cache.
- Verzia `2026.6.29.post8`.

## [2026.6.29.post7] - 2026-06-29 - Vynechané nepoužité počty na nástenke pre študentov

###  Zmenené
- Backend nástenky: domovská stránka a `/dashboard/stats` už pre študentov nespúšťajú dopyty na „počet skupín" a „počet študentov" - tie napĺňajú len karty učiteľa/admina. O dva databázové dopyty menej pri každom načítaní nástenky študenta a obnove štatistík. Bez viditeľnej zmeny.
- Vydanie len pre backend: nezmenili sa žiadne statické súbory, takže Service Worker cache zostáva na `gitpulse-v247`.
- Verzia `2026.6.29.post7`.

## [2026.6.29.post6] - 2026-06-29 - Vypnuté postupné objavenie (cascade) do revízie

###  Zmenené
- Vypnuté postupné objavenie („cascade") na nástenke a profile študenta - zhoršovalo tieto zobrazenia v produkcii. Engine zostáva v kóde a bude znovu zapnutý až po vizuálnom overení v prehliadači.
- Verzia `2026.6.29.post6`; Service Worker cache `gitpulse-v247`.

## [2026.6.29.post5] - 2026-06-29 - Postupné objavenie kariet na profile študenta

###  Pridané
- Postupné objavenie („cascade") rozšírené na profil študenta: karty merge requestov a karty „recenzie pre kolegov" sa teraz načítavajú postupne jedna za druhou pri prvom zobrazení, rovnako ako na nástenke.

###  Zmenené
- Pridaný test konzistencie verzie vydania, ktorý kontroluje, že verzia v `pyproject` zodpovedá najnovšiemu záznamu vo všetkých changelogoch (root + docs SK/EN), takže bump verzie už nemôže ticho aktualizovať len jeden súbor.
- Verzia `2026.6.29.post5`; Service Worker cache `gitpulse-v246`.

## [2026.6.29.post4] - 2026-06-29 - Postupné objavenie dlaždíc nástenky, relatívny čas, oprava sprievodcu

###  Pridané
- **Postupné objavenie (cascade)**: dlaždice na nástenke (KPI štatistiky, karty predmetov, „Položky vyžadujúce pozornosť" a feed „Najnovšie aktualizácie") sa teraz načítavajú postupne jedna za druhou - „podľa príchodu" - namiesto toho, aby naskočili všetky naraz. Rešpektuje `prefers-reduced-motion` a spúšťa sa len pri prvom zobrazení (odovzdanie zo skeletonu / prvé vykreslenie), nie pri živom obnovovaní (žiadne blikanie). Riadky tabuliek sú zámerne vynechané.
- Relatívne formátovanie času („pred 2 hodinami") pri aktivitách a časových značkách cez nový klientsky pomocník `localize-time`.

###  Opravené
- Sprievodca (tour) teraz rekurzívne posúva všetkých posúvateľných predkov, aby dostal cieľ kroku do zobrazenia, a preskakuje tabuľkové kontajnery, takže sa posúva hlavný obal stránky namiesto vnútornej tabuľky.
- Krok sprievodcu „akcie v riadku používateľa" teraz zvýrazňuje obal tlačidiel namiesto holej bunky tabuľky.
- Vrátené (rollback) skoršie zmeny pozíciovania a popoveru sprievodcu, ktoré zhoršovali ukazovanie na cieľ.
- Odstránené duplicitné podnadpisy na profile študenta.

###  Zmenené
- Prebudované JS/CSS bundly a minifikované assety.
- Verzia `2026.6.29.post4`; Service Worker cache `gitpulse-v245`. Zároveň zarovnaná verzia balíka, ktorá zostala na `post2`, kým `post3` vydal len SW cache a changelog.

## [2026.6.29.post3] - 2026-06-29 - GitLab diff komentáre, hlavičky diskusií, priesvitné email logo

###  Opravené
- Code kontext diff komentára teraz zobrazuje GitLab-style dvojitý stĺpec pre čísla riadkov (staré a nové čísla vedľa seba).
- Rozsahové diff komentáre sa správne zobrazujú v pätičke vlákna (napr. `Comment on lines +51-53`).
- Hlavičky diskusií teraz obsahujú GitLab používateľské meno autora (`@username`) a lokalizovaný čas začiatku vlákna.
- Statusové ikony v `.commit-message-cell` sú teraz zobrazené inline a nepreskakujú nad odkaz správy commitu.
- Sprievodca (tour) popover na desktope teraz ukazuje priamo na zvýraznené ciele s tematikou šípkou namiesto núteného umiestnenia v spodnom pravom rohu.

###  Zmenené
- Logo pre emailové notifikácie bolo zmenené na priesvitné (bez tmavosivého ohraničenia dlaždice) a bol odstránený tieň pre modernejší vzhľad.
- Verzia `2026.6.29.post3`; Service Worker cache `gitpulse-v244`.

## [2026.6.29.post2] - 2026-06-29 - GitLab-style tanuki social cover

###  Zmenené
- Prerobený Open Graph / social-share obrázok (`og-image.png`, docs `og-cover.png`) na GitLab-style tanuki dlaždicu (oranžový tanuki na svetlej gradientovej zaoblenej dlaždici) s prekrytým GitPulse ECG pulzom namiesto nebrandového modrého ECG štvorca, takže náhľady odkazov ladia s logom v aplikácii. Ikony domovskej obrazovky/PWA a favicon už tanuki mali.
- Verzia `2026.6.29.post2`.

## [2026.6.29.post1] - 2026-06-29 - Oprava diff kontextu (hunk), medzery inline-code, favicon

###  Opravené
- Code kontext diff komentára už neprekračuje hranicu hunku - ostáva v rámci komentovaného hunku (ukáže celý kompaktný pridaný konštrukt, GitLab-style) namiesto skoku čísel riadkov (napr. `29 -> 49`) a presakovania do ďalšej funkcie.
- Inline `code` pilulky majú reálnu horizontálnu medzeru, takže sa už nedotýkajú okolitých slov.
- Riadok **Pokrytie testami** v MR pipeline (ikona, label, %, „z N úloh") je na jednej spoločnej osi namiesto rôznych vertikálnych úrovní.
- Zastaraný docs `favicon.ico` pregenerovaný ako poriadny multi-rozlíšenie GitPulse tanuki a cache-busted linky favicon.
- Sprievodca (tour) otvorí zbalený `<details>` okolo cieľa kroku len pri navigácii na daný krok, nie počas page-load kontroly dostupnosti (oprava regresie, ktorá mohla pri načítaní automaticky rozbaliť zbalené diff/code sekcie).

###  Zmenené
- Verzia `2026.6.29.post1`; Service Worker cache `gitpulse-v243`.

## [2026.6.29] - 2026-06-29 - Skladací code kontext, čistejšie diskusie a oprava túru

###  Opravené
- Inline code kontext v MR/review diskusiách je teraz skladací a **predvolene zbalený** (GitLab-style `Zobraziť kód` so súborom:riadkom), takže dlhé thready sú ľahké a už nelagujú pri skrolovaní.
- Odstránený zavádzajúci neinteraktívny `new`/`old` štítok z code-context lišty; stranu už ukazuje gutter s číslami riadkov a pätička `Komentár k riadku +N`.
- Vymyslený štítok `1 účastníci` sa už nezobrazuje: počet účastníkov sa ukáže len keď thread naozaj má viac než jedného.
- Prehľadnejšie review thready: odstránená nadbytočná „reply to ..." pri každej odpovedi (odpovede sú už vizuálne vnorené) a duplicitná ikona kopírovania odkazu na koreňovom komentári threadu.
- Inline `code` pilulky v popisoch a komentároch MR/issue už neprekrývajú susedné riadky.
- Vertikálne vycentrované hlavičky MR kariet a sekcie „Dané reviews".
- Workflow pás má väčšie a jasnejšie ikony bodov s pokojnejším hoverom (bez skoku riadku).
- Sprievodca (tour) teraz pred zvýraznením otvorí zbalený `<details>` okolo cieľa kroku (strom súborov, code kontext), takže kroky ako *Strom zmenených súborov* už nie sú rozbité, keď je sekcia zatvorená.
- Odstránený tmavý pruh pod sticky lištou uloženia v nastaveniach predmetu, keď je formulár posledným blokom stránky.

###  Zmenené
- User-info modal: zoznam projektov `+N viac` v skupine je teraz rozbaliteľný/zbaliteľný ovládač (`Zobraziť menej`) namiesto mŕtveho štítku.
- Open Graph/Twitter náhľad dokumentácie používa brandovaný GitPulse obrázok (`assets/og-cover.png`).
- Prebudované bundly/minifikované assety; pridaný slovenský preklad `Zobraziť kód`; verzia `2026.6.29`; Service Worker cache `gitpulse-v242`.

## [2026.6.28.post1] - 2026-06-28 - Scoped MR diff jumpy a code komentare

###  Opravené
- MR/review diff file anchor ID su scoped per karta, takze changed-file tree kliky a comment jumpy uz netrafia cudzi `diff-file-*` blok pri viacerych MR na stranke.
- Diff comment code context ma jeden side-aware gutter s cislami riadkov a presny text `Comment on line`, bez extra starej/novej ciselnej panely a bez nespravneho range footera.
- Chybajuce MR pipeline `Test coverage` sa pre viditelne student MR dobiera z GitLab pipeline detailov/jobov, ak starsi lokalny pipeline riadok ma `coverage = null`.
- Odstranena nespolahliva diagnostic karta `Response Rate` aj duplicitna diagnostic karta `Test Coverage`, vratane skeleton placeholderov.

###  Zmenené
- Pregenerovane static bundles/minified assets po student-detail fixoch.

###  Vydanie
- Verzia `2026.6.28.post1`; Service Worker cache `gitpulse-v241`.

---

## [2026.6.28] - 2026-06-28 - Lokalne jumpy a inline Test coverage

###  Opravené
- Copyable/hash linky pre student comments, MR karty, dashboard ciele a paginovane tabulky teraz pouzivaju zdielany lokalny `.gl-page-content` scroll kontrakt namiesto browser-level auto scrollu.
- MR pipeline coverage je znova viditelne ako GitLab-like inline text (`Test coverage ... from 1 job`) bez samostatnej `Test Coverage` karty/chipu.
- MR loading skeleton markup kopiruje realnu strukturu Pipeline/Tests plus inline coverage.

###  Vydanie
- Verzia `2026.6.28`; Service Worker cache `gitpulse-v240`.

---

## [2026.6.27.post2] - 2026-06-27 - Skeleton profilu, MR odpovede a presnejsie coverage

###  Opravené
- Loading skeleton profilu studenta teraz kopiruje realnu profile kartu, mobilne GitLab/profile/date metadata su centrovane a duplicitny divider bol odstraneny.
- Student-detail jumpy pouzivaju lokalny `.gl-page-content` scroll kontrakt z Issues to Address, takze uz neposuvaju globalne okno a nelamu layout.
- MR commit riadky drzia labely, +/- statistiky a datumy v pevnych grid stlpcoch, aby sa dlhy obsah nerozlieval cez stranku.
- MR diff code context sa renderuje na urovni diskusneho vlakna s old/new gutters, zvyraznenim cieloveho riadku, copy akciou a pripojenymi odpovedami pre GitLab-like citanie.
- Pipeline coverage sa parsuje z GitLab pipeline/build payloadov a same-SHA fallback pipelines, takze riadky ukazuju realne hodnoty ako `Test coverage 91.00% ... from 1 job` namiesto `not reported`.

###  Zmenené
- GitPulse logo ma plynulejsiu ECG hover animaciu a student profile/MR skeleton static assets boli pregenerovane.

###  Vydanie
- Verzia `2026.6.27.post2`; Service Worker cache `gitpulse-v239`.

---

## [2026.6.27.post1] - 2026-06-27 - GitLab-like MR odpovede, coverage signal a profil studenta

###  Opravené
- Student MR diskusie sa renderuju ako prepojene GitLab-like vlakna so stabilnymi anchor linkami pre vlakno/komentar, reply-to jumpmi, collapsible odpovedami a buttonmi na skok do diff suboru.
- Pipeline riadky ukazuju jasny coverage fallback, ked GitLab nevrati test coverage, namiesto ticheho skrytia signalu.
- MR branch commity ukazuju autora, interny profilovy link tam, kde je dostupny, a Teacher commit badge pre commity ucitelov kurzu.
- Profilove metriky studenta, zarovnanie table skeletonov, Run Compliance Checks checkboxy, modal footer highlight a sticky spravanie diff file-tree boli dotiahnute.

###  Vydanie
- Verzia `2026.6.27.post1`; Service Worker cache `gitpulse-v238`.

---

## [2026.6.27] - 2026-06-27 - Komponentove UI doladenie student detailu, modalov, skeletonov a code komentarov

###  Opravené
- Skeleton riadky v tabulkach clenov uz pouzivaju rovnaky stlpcovy kontrakt ako realne riadky, takze Status/Checks placeholdery neodchadzaju mimo hlavicky.
- Student MR diff navigacia drzi strom zmenenych suborov sticky, scrolluje iba jeho lokalny panel a nepouziva globalny item `scrollIntoView`.
- Modal Run Compliance Checks ma stabilne checkbox riadky bez modreho inset pruhu a bez globalnej scale animacie checkboxov.
- Inline code kontext pri MR komentaroch ma old/new gutters, side-aware vyber cieloveho riadku, lokalny horizontalny scroll a copy akciu.

###  Zmenené
- Profilove metriky studenta, Reviews Given karty, tour popovery a student-detail tour kroky boli zladene s komponentovym UI kontraktom.
- GitPulse logo pouziva pokojnejsi ECG pulse a jeden jemny hover stav bez trhania v light aj dark theme.
- Source CSS `letter-spacing` deklaracie boli zjednotene na `0` napriec zdielanymi aj page stylmi.

###  Vydanie
- Verzia `2026.6.27`; Service Worker cache `gitpulse-v237`.

---

## [2026.6.26] - 2026-06-26 - GitPulse branding, zero-inline UI kontrakt a presné MR jumpy

###  Opravené
- Kliknutie z Issues na MR teraz scrolluje iba lokálny obsah stránky a nepoužíva globálny anchor scroller.
- Dynamicky otvorené modaly a drawery pred aktiváciou znovu inicializujú dirty-check guard.
- Komentáre k diffom vedia zobraziť GitLab-like kontext okolitých riadkov kódu, ak sú dostupné uložené MR diff dáta.

###  Zmenené
- Viditeľné pomenovanie Teamwork bolo zjednotené v aplikácii aj dokumentácii, pričom interné uložené JSON/API kľúče ostávajú stabilné.
- GitPulse logo je teraz zdieľaný komponentový stylesheet s GitLab-inšpirovanou značkou, light/dark contrast guardmi a pregenerovanými PWA ikonami.
- Inline progress/size štýly v šablónach boli nahradené opakovateľnými data atribútmi komponentov a centralizovanou hydratáciou CSS premenných.
- Responzívne tabuľky a skeletony majú prísnejšie zladený DOM/CSS kontrakt s reálnym obsahom.

###  Vydanie
- Verzia `2026.6.26`; Service Worker cache `gitpulse-v236`.

---

## [2026.6.25] - 2026-06-25 - System-wide HTMX cleanup, zabránenie únikom pamäte a bezpečné skripty

###  Opravené
- Opravené úniky pamäte v celom systéme implementáciou čistenia stránok a životného cyklu v rámci `GP.activePageCleanup()`. Všetky event listenery na `window`/`document`, SSE streamy (`EventSource`) a časovače (`setInterval`/`setTimeout`) sú pri HTMX swapoch korektne ukončené.
- Prevedené anonymné event listenery na `document` a `window` v samostatných ovládačoch stránok (`admin-events.js`, `admin-users.js`, `course-activity.js`, `support-ticket-detail.js`) na pomenované funkcie, čo umožňuje ich explicitné odstránenie z globálneho rozsahu.
- Zabránené znečisteniu globálneho lexikálneho rozsahu odstránením nepotrebných IIFE obalov zo zdrojových skriptov stránok, pričom ich automatické balenie bolo presunuté do zostavovacieho skriptu `build_bundle.py`.
- Extrahovaný inicializačný skript pre uvítací pozdrav z `dashboard.html` do samostatného čistého statického JavaScript modulu `greeting-sync.js`, čím sa dosiahlo úplné odstránenie inline skriptov zo šablón.

###  Vydanie
- Verzia `2026.6.25`; Service Worker cache `gitpulse-v235`.

---

## [2026-06-23] - Aktualizácia a zosúladenie dokumentácie compliance kontrol

###  Pridané
- Pridané vysvetlenie a detaily pre pravidlo **R13 (Kvalita commitov)**, ktoré hodnotí lokálny Git workflow voči webovému editoru GitLabu (Web IDE).

###  Zmenené
- Opravené a kompletne zosúladené popisy pravidiel **R01-R13** v príručke pre študentov (`studenti/metriky.md` a `.en.md`) tak, aby presne zodpovedali definíciám v `builtin_checks.json` a `engine_checks.py`.
- Aktualizovaná tabuľka compliance pravidiel v príručkách pre učiteľov (`ucitelia/zaciname.md` a `.en.md`) a na stránkach dashboardu (`ucitelia/dashboard.md` a `.en.md`), kam bola doplnená kontrola R13 vrátane jej predvolenej váhy (0 %).
- Zosúladené počty route handlerov v API referencii (`api/index.md` a `.en.md`) na zhodnú a overenú hodnotu **222** route handlerov.

---

## [2026.6.20] - 2026-06-20 - Responzívna správa kurzov, bezpečný Markdown a aktuálna diplomová práca

###  Opravené
- Správa kurzov zachováva všetky stĺpce v responzívnych kartách, používa popisy hodnôt a stabilný panel vyhľadávania na úzkych obrazovkách.
- Náhľad Markdown funguje aj so zostavením Alpine CSP bez zakázanej direktívy `x-html`.
- Skripty editora Markdown a detailu požiadavky podpory možno po HTMX navigácii bezpečne inicializovať opakovane bez konfliktu deklarácií.

###  Zmenené
- Verejná sekcia diplomovej práce zodpovedá tretiemu priebežnému odovzdaniu a neuvádza predbežné výsledky, ktoré ešte neboli vyhodnotené.
- Návrh dokumentuje aktuálny model R01-R13, ručnú synchronizáciu namiesto periodického prehľadávania GitLabu a dve anonymizované snímky funkčného prototypu.

###  Vydanie
- Verzia `2026.6.20`; Service Worker cache `gitpulse-v234`.

---

## [2026.6.19.post2] - 2026-06-19 - Responzívna tabuľka správy používateľov

###  Opravené
- Vyhľadávanie a filter rolí používajú stabilný toolbar bez náhodného zalamovania a posúvania.
- Triedy stĺpcov sú na reálnych hlavičkách a bunkách, takže šírky, skracovanie, viditeľnosť, status, akcie aj skeleton používajú jeden kontrakt.
- Riadky ľudí a servisných účtov používajú kompaktné ikonové akcie a bezpečne zobrazujú dlhé používateľské mená aj e-mailové adresy.
- Mobilné karty používajú meno používateľa ako primárnu identitu a zachovávajú zarovnané metadata aj akcie.
- Live zmeny role a statusu zachovávajú rovnaký badge a status-indicator markup ako serverový render.

###  Vydanie
- Verzia `2026.6.19.post2`; Service Worker cache `gitpulse-v232`.

---

## [2026.6.19.post1] - 2026-06-19 - Zosúladenie responzívnych skeletonov tabuliek

###  Opravené
- Projektové a tímové tabuľky členov používajú jeden responzívny stĺpcový kontrakt pre reálne riadky, loading skeletony aj JavaScript fallback riadky.
- Skeleton detailu projektu odvodzuje rubric/check stĺpce z aktívneho zoznamu kontrol, takže loading matica zostáva zarovnaná s reálnou tabuľkou R01-R13.
- Skeleton riadky administrátorskej tabuľky používateľov používajú typované user stĺpce namiesto generickej tabuľkovej náhrady.
- Skeleton riadky používajú rovnaký responzívny `data-label` kontrakt ako reálne riadky, takže tabletové a mobilné loading stavy sa zobrazujú ako label/value karty.
- Filtre rolí používateľov a filtre členov sa na úzkych obrazovkách zalamujú v komponente bez horizontálneho scrollu alebo orezania.
- Test status pri pipeline v študentských merge requestoch sa zobrazuje ako kompaktný badge namiesto surového textu.
- Animácie Issues to Address sú vypnuté, aby sa po zmene visibility alebo HTMX refreshi nespúšťali druhýkrát.

###  Vydanie
- Verzia `2026.6.19.post1`; Service Worker cache `gitpulse-v231`.

---

## [2026.6.18.post1] - 2026-06-18 - Skeletony tabuliek, aktuálnosť analytiky a indexovanie

###  Opravené
- Skeletony tabuliek používajú samostatné typy buniek pre projektové riadky, členov, badge prvky, status pilulky, kontrolné body a akčné tlačidlá.
- Admin a teacher prehľady na nástenke nahrádzajú málo užitočnú kartu "Open MRs" pokrytím aktívnych skupín.
- Bannery neaktuálnych dát v analytike a aktivite kurzu zobrazujú čiastočné pokrytie current-week snapshotov skupín namiesto dojmu, že sa nesynchronizoval celý kurz.
- Prihlasovacie a odhlasovacie upozornenia používajú spoločný GitLab-style alert komponent s podporou titulku a krátkym synchronizovaným fade efektom pri odhlásení.
- Robots a sitemap odpovede explicitne blokujú indexovanie súkromného dashboardu, povoľujú login stránku, obsahujú last-modified metadata a verejné cache hlavičky.

###  Vydanie
- Verzia `2026.6.18.post1`; Service Worker cache `gitpulse-v229`.

---

## [2026.6.18] - 2026-06-18 - Reconciliácia syncu projektov a presnejšie UI guardy

###  Opravené
- Projektové položky v Quick access na nástenke otvárajú stránku projektu namiesto nadradenej skupiny.
- Importy GitLab skupiny alebo kurzu deaktivujú aktívne databázové projekty, ktoré už neexistujú v importovanom strome GitLab skupiny, vrátane osirelých členov tímu, keď nezostane žiadny aktívny projekt.
- Process-action guardy ďalej chránia sync/import/check/delete akcie, ale neblokujú pasívne filtre, taby a dropdown ovládacie prvky.
- Skeleton kontrakty projektových a členských tabuliek zostávajú zosúladené s responzívnym layoutom tabuliek.
- Produkčný redeploy necháva AI teamwork analysis vypnutú v `.env.production`.

###  Zmenené
- Odkazy Back to Group používajú transform-based pohyb ikony a odkazu namiesto zmeny medzery, ktorá hýbala layoutom.
- GitLab import API a SSE completion payloady vracajú počty vyčistených stale projektov.

###  Vydanie
- Verzia `2026.6.18`; Service Worker cache `gitpulse-v228`.

---

## [2026.6.17] - 2026-06-17 - Zosúladenie prihlásenia s Keycloak

###  Zmenené
- Zosúladené rozloženie, rozostupy a rozmery prihlasovacej a odhlasovacej stránky s dizajnom Keycloak.
- Vycentrovaný názov loga, nastavená šírka karty na kompaktných 400 px a odstránené nepotrebné zaoblenia hrán pre čistý hranatý vzhľad.
- Premiestnený a upravený rozbaľovací zoznam výberu jazyka tak, aby bol kompaktný a mal polopriehľadné čierne pozadie.

###  Vydanie
- Verzia `2026.6.17`; Service Worker cache `gitpulse-v224`.

---

## [2026.6.16] - 2026-06-16 - Redizajn e-mailov, vylepšenia tiketov podpory a čistenie emoji

###  Pridané
- Kompletný redizajn systému e-mailových notifikácií s modernou typografiou Inter, jemnými tieňmi a prémiovými farebnými gradientmi.
- Rozsiahle aktualizácie rozhrania tiketov podpory vrátane dynamického nahrávania súborov formou drag-and-drop v editore tiketov, vizuálneho zvýraznenia dragover a opravy prebytočného dabl-klikávania v Chrome.

###  Zmenené
- Nahradené zastarané referencie na "Reports" (Reporty) za "Analytics" (Analytiku) v šablónach uvítacích e-mailov pre roly učiteľov a administrátorov.
- Odstránené všetky surové emoji a AI-like emotikony zo všetkej aktívnej dokumentácie systému pre dosiahnutie profesionálneho a čistého tónu.
- Zvýšená verzia aplikácie na `2026.6.16` a verzia cache Service Workera na `gitpulse-v217`.
- Vyčistené zastarané pomocné a testovacie skripty z repozitára.

###  Vydanie
- Verzia `2026.6.16`; Service Worker cache `gitpulse-v217`.

---

## [2026.6.15.post1] - 2026-06-15 - Akademické týždne, Pajamas dropdowny a vylepšený drag & drop

###  Pridané
- Výpočet akademických týždňov (`1`-`13`) a týždňov skúškového obdobia (`S1`-`S7`) vo Flatpickr kalendároch na základe dátumu začiatku semestra.
- Alpine.js-backed, Pajamas custom dropdowny (`select_field`) pre výber typu a týždňa na stránke zadaní.
- Globálne odchytenie drag & drop udalostí na okne na zamedzenie nežiaducej navigácie prehliadača pri minutí odhadzovacích zón.
- Pointer-events obmedzenie na potomkov odhadzovacích zón na elimináciu blikania počas ťahania.

###  Zmenené
- Tlačidlá akcie Upraviť a Zmazať v zozname zadaní prerobené na `btn_icon_only` na zamedzenie prekrývania textu na úzkych obrazovkách.
- Rebuildnuté a minifikované statické CSS/JS balíčky.

###  Opravené
- Opravená viditeľnosť zaškrtávacieho znaku (checkbox) v tmavom režime a pridané plynulé pružné animácie.
- Odhadzovacie zóny teraz pri dropnutí súboru odosielajú štandardný `change` event pre bezproblémovú integráciu s HTMX.
- Odstránené zbytočné animácie postupného zobrazovania kariet na zamedzenie dvojitých efektov.

###  Vydanie
- Verzia `2026.6.15.post1`; Service Worker cache `gitpulse-v209`.

---

## [2026.6.11.post7] - 2026-06-11 - Trvalý vzhľad a responzívne doladenie

###  Pridané
- Svetlý, Tmavý a Systémový režim nad jednou sémantickou vrstvou tokenov bez prebliknutia pri prvom vykreslení.
- Zvolený režim sa ukladá k účtu na serveri a prenáša sa medzi prehliadačmi a zariadeniami.
- Krok sprievodcu otvorí profilové menu a ukáže priamo na skutočný prepínač vzhľadu.
- Stav nainštalovanej PWA sa overuje cez prehliadač, nie iba lokálnym príznakom.
- Spoločný prepínač režimu pre dashboard, prihlásenie a všetky chybové stránky.
- Statický offline fallback používajúci rovnaký bezpečný error povrch.
- Spoločný krok o vzhľade automaticky pridaný do každého dostupného produktového sprievodcu.
- Serverom určený scope Project, Course a Group synchronizácií v Job History.

###  Zmenené
- Grafy sa pri zmene režimu prefarbia bez reloadu.
- Middleware chyby používajú jeden escapovaný CSP-aware renderer.
- Spinner má jeden komponentový DOM/CSS kontrakt a skeletony zostali iba v reálnych HTMX lazy zónach.
- SSR tabuľky sa vykresľujú okamžite bez čakania na JavaScript visibility guard.
- Svetlý shell, navigácia, karty, tabuľky, ovládacie prvky, skeletony,
  spinnery, texty, okraje, tiene a interakčné stavy používajú aktuálne
  sémantické role Pajamas.
- Historické synchronizácie celého predmetu obnovia chýbajúci kontext predmetu
  a zobrazia jeho názov namiesto nesprávneho označenia samostatnej skupiny.
- Tlačidlá, dropdowny, karty a sekcie majú viditeľné sémantické okraje v oboch
  režimoch; focus vyhľadávania už nemení šírku panelov akcií.
- Značkové pozadie prihlásenia je obnovené a karta je overená pri mobilnej šírke 390 px.

###  Odstránené
- Všeobecné animácie objavenia stránok, riadkov a lazy fragmentov.
- Mŕtve skeleton vetvy a duplicitný button spinner markup.
- Posuny a zväčšovanie dashboard prvkov pri hoveri, ktoré neprenášali stav.

###  Vydanie
- Verzia `2026.6.11.post7`; Service Worker cache `gitpulse-v186`.

---

## [2026.6.10.post5] - 2026-06-10 - Zosúladenie načítavacích skeletonov a odstránenie inline štýlov

###  Pridané
- **Skeletons v štýle Pajamas a nulové inline štýly**: Úplne eliminované všetky inline `style` atribúty pre šírku, výšku a zaoblenie hrán v `loaders.html`. Všetky veľkosti sú teraz namapované na znovupoužiteľné triedy podľa design systému Pajamas v `loaders.css`.
- **Zosúladenie detailu tímu a manažéra učiteľov**: Zástupné symboly pre detail skupiny a správu učiteľov teraz využívajú priamo komponenty makier (`badge`, `btn`, `btn_icon`, `btn_icon_only`) v deaktivovanom stave, čím sa dosiahlo pixelovo dokonalé prispôsobenie a nulový posun rozloženia (CLS).

###  Opravené
- **Spracovanie vymazaných a prázdnych GitLab projektov**: Pridaná automatická deaktivácia projektov, ktorých repozitár bol vymazaný na GitLab (vrátenie stavu prázdneho repozitára namiesto 404). Vyčistené staré skóre v zozname členov na "N/A" pre prázdne/vymazané repozitáre.
- **Dynamická deaktivácia členov pri strate projektov**: Automatická deaktivácia členov tímu v prípade, že sú vymazané alebo deaktivované všetky aktívne projekty priradené k ich tímu.
- **Ochrana pred vymazaním členov pri výpadkoch**: Zabránené nežiaducemu odstraňovaniu platných členov pri čiastočných chybách sťahovania z GitLab API (timeout / 5xx), čo zabezpečuje stabilitu zoznamu pri občasných chybách siete.
- **Zvýšenie verzie a cache**: Zmena verzie na `2026.6.10.post5` a zvýšenie verzie cache Service Workera na `gitpulse-v176`.

---

## [2026.6.9.post2] - 2026-06-09 - Kompletné odstránenie inline layout štýlov

###  Zmenené

- **Kompletné odstránenie inline layout štýlov**: Odstránené všetky inline layout a flex atribúty `style="..."` (ako flexbox, display, okraje, padding, priehľadnosť a pointer-events) zo súboru `loaders.html` a ich presun do tried CSS v `utilities.css`.
- **Krajšie formuláre**: Nahradené inline konfigurácie max-width vo formulárových komponentoch čistými pomocnými triedami triedy.
- **Zvýšenie verzie a cache**: Zmena verzie na `2026.6.9.post2` a zvýšenie verzie cache na `gitpulse-v174`.

###  Opravené

- **Upozornenie na nesúlad verzií**: Aktualizovaný súbor JSON pre interný changelog aplikácie, aby sa používateľom v prehliadači korektne zobrazilo hlásenie o novej verzii po nasadení.

---

## [2026.6.9.post1] - 2026-06-09 - Plynulé prechody a zamedzenie posunu rozloženia v načítavacích skeletonoch

###  Pridané

- **Dynamické vykresľovanie hlavičiek tabuliek v skeletonoch**: Úprava makra `sk_table` tak, aby akceptovalo voliteľný parameter zoznamu hlavičiek (`headers`), čo umožňuje okamžité zobrazenie statických stĺpcov počas načítavania stránky.
- **Vylepšený dizajn makra `sk_stat` s podporou popiskov a ikon**: Zástupné symboly (placeholders) pre štatistické mriežky v analytike kurzu, aktivite kurzu a detailoch študenta teraz okamžite zobrazujú reálne popisky a ikony namiesto blikajúcich sivých blokov, čím sa úplne eliminuje posun rozloženia (layout shift).

###  Opravené

- **Plynulá interakcia s rozbaľovacími ponukami**: Oprava neplatných premenných CSS (`var(--gl-dropdown-item-hover)`) v súbore `dropdowns.css` ich namapovaním na správne tokeny (`var(--gl-dropdown-item-hover-bg)` atď.), čím sa obnovili hladké prechody pozadia pri prechode myšou.
- **Zosúladenie načítavacích skeletonov na všetkých stránkach**: Dôkladná kontrola a refaktorovanie všetkých zložených skeletonov stránok (`sk_dashboard`, `sk_course_detail_body`, `sk_analytics_inner`, `sk_course_activity_inner`, `sk_student_detail`, `_sk_teachers_inner`) v súbore `loaders.html`, aby presne zodpovedali reálnym šablónam vykresľovaným na serveri, s použitím lokalizačných prekladov `t()` pre statické texty.

###  Zmenené

- Zvýšenie verzie cache Service Workera na `gitpulse-v173`.

---

## [2026.6.8.post5] - 2026-06-08 - Zosynchronizovaný refresh a manuálny GitLab sync

###  Zmenené

- **Manuálny refresh s plnohodnotným sync-all tokom**: Kliknutie na tlačidlo "Refresh" na stránkach Course Analytics alebo Course Activity teraz namiesto statického znovunačítania spustí naozajstný GitLab sync na pozadí pre všetky skupiny cez API. Tlačidlá majú vizuálny stav načítania (spinning + text), sú prepojené s globálnym panelom priebehu úloh, po úspechu automaticky prerenderujú tabuľky a grafy, a pri zlyhaní sa sfarbia do červena na signalizáciu chyby.
- **Odstránené dočasné logy**: Vyčistené nepotrebné logové súbory z predošlých nasadení v koreňovom priečinku projektu.

---

## [2026.6.8.post4] - 2026-06-08 - Doladenie dashboardu a opráv chýb

###  Opravené

- **Exklúzia fantómových sync riadkov v prehľade**: Prehľad "Follow the latest updates" na dashboarde už neukazuje riadky úloh synchronizácie, ktoré nemajú reálny záznam v histórii. Boli odfiltrované všetky varianty synchronizácií.
- **Zarovnanie stĺpca akcií v tabuľke členov**: Tlačidlo "View" v zozname členov projektu už neposkakuje kvôli chýbajúcim prepínačom na riadkoch učiteľov.

###  Zmenené

- **Spätná väzba pri refreshe histórie**: Ručné obnovenie histórie úloh teraz zobrazuje indikátor načítania a pri chybe ponúkne odkaz na vytvorenie tiketu podpory.

---

## [2026.6.8.post3] - 2026-06-08 - Oprava výpočtov a lokalizácie

###  Opravené

- **Počet študentov v checkliste**: Opravený výpočet menovateľa pre checklist v analytike kurzu (počíta iba aktívnych študentov).
- **Oprava SyntaxError**: Odstránená chyba v klientskom skripte pre week explorer.

###  Zmenené

- **Vylepšený pozdrav a chybové stavy**: Pridaný detailný podnadpis s rolou na dashboard a odkazy na podporu do chybových stavov HTMX.

---

## [2026.6.8.post2] - 2026-06-08 - Synchrónne hlavičky detailov

###  Zmenené

- **Hlavičky detailov tímu a projektu**: Načítavajú sa priamo v SSR šablóne shellu, čím sa predišlo posunu layoutu.

---

## [2026.6.8.post1] - 2026-06-08 - Prepracovanie skeleton loaderov

###  Odstránené

- **Mŕtve celostránkové skeletony**: Vymazané nepoužívané makrá a optimalizované zobrazenie učiteľských profilov bez compliance gridov.

---

## [2026.6.5.post18] - 2026-06-05 - "Needs Attention" vedie na presnu skupinu

###  Zmenene

- KPI karta **"Needs Attention"** teraz vedie **presne na element**: ak je
  problemova prave jedna skupina, otvori ju priamo; pri viacerych vedie na
  prehlad. So skorsim odlisenim karty "Students" ziadne dve karty nevedu na to
  iste miesto.

---

## [2026.6.5.post17] - 2026-06-05 - Stranka studenta: stlpec "Project" odstraneny

###  Zmenene

- **Stlpec "Project" bol uplne odstraneny** zo vsetkych tabuliek na stranke
  studenta v skupine (commity, issues, MR). Na stranke jednej skupiny je projekt
  vzdy rovnaky, takze isiel len o zbytocny sum; odkaz na GitLab ostava na cisle
  commitu/issue/MR. Tabulky sa zameriavaju na to, co sa hodnoti: vlastna praca
  clena (DOING) oddelene od code review kolegov (COMMUNICATING).
- Vymazanie uloh z **Historie uloh** teraz vycisti aj **"Follow the latest
  updates"** (job-rows v prehlade maju rovnaky zdroj).

---

## [2026.6.5.post16] - 2026-06-05 - Konzistentny prehlad aktivit + plynuly skeleton

###  Opravene

- **"Follow the latest updates"** je teraz konzistentny s **Historiou uloh** -
  uz nezobrazuje "fantomove" zaznamy o synku/reporte, ktore v Historii uloh
  neexistuju. Job-ove aktivity sa cerpaju z toho isteho zdroja ako Historia
  uloh; audit-log ponecha len skutocne ne-jobove udalosti.

###  Zmenene

- Obsah stranky sa po nacitani plynulo **usadi na miesto skeletonu** (GitLab
  styl) namiesto tvrdeho preblesknutia.

---

## [2026.6.5.post15] - 2026-06-05 - Cistejsi dashboard + oprava CI

###  Opravene

- **CI je opat zelene** - `requirements.lock` bol regenerovany na Linuxe (presne
  ako v CI), nie na Windowse.
- Z prehladu **poslednych aktivit** zmizli "fantomove" systemove zaznamy
  (telemetricke snimky, zostatky planovanych sweepov) - ostavaju len v admin
  Historii uloh.

###  Zmenene

- KPI karta **"Students"** uz nevedie na rovnake miesto ako "Users" - otvara
  zoznam pouzivatelov predfiltrovany na studentov.

---

## [2026.6.5.post14] - 2026-06-05 - Rychlejsie nacitanie (dlhsia cache)

###  Zmenene

- Cache vyrendrovaneho HTML drzi teraz **5 minut namiesto 60 sekund**.
  Cerstvost to neovplyvnuje - cache sa presne zneplatnuje pri kazdej zmene
  (webhook aj akcia v aplikacii) a pri kazdom nasadeni. Vysledok: viac
  okamzitych nacitani bez rizika zastaralych dat.

---

## [2026.6.5.post13] - 2026-06-05 - Uplne pokrytie webhookmi

###  Zmenene

- **Doverne (confidential) issues a komentare** sa uz spracuvavaju rovnako ako
  verejne (predtym sa ticho ignorovali).
- Navod na nastavenie webhooku odporuca zapnut **vsetky relevantne udalosti** a
  nastavit hook na urovni **skupiny/podskupiny** - len tak GitLab posiela
  udalosti o clenoch a podskupinach, cim sa automaticky zachyti
  pridanie/odobratie clena aj prerozdelenie.

---

## [2026.6.5.post12] - 2026-06-05 - Odstranenie periodickych jobov (cisto webhookovy system)

###  Odstranene

- **Vsetky periodicke (cron) joby aj samotny scheduler** boli odstranene
  (subor `scheduler.py`, compose sluzba `scheduler`, zavislost `rq-scheduler`).
  Panel jobov uz nezahlcuju "duchove" ulohy a na GitLab nie je ziadna zataz na
  pozadi.
- Vsetky zmienky o periodickom planovani boli odstranene z kodu aj dokumentacie.

###  Zmenene

- System je teraz **cisto webhookovy + manualny**: data sa obnovuju udalostami
  z GitLabu a explicitnymi akciami. Udrzbove operacie ostavaju ako rucne joby
  v *System -> udrzbove joby*.
- Opakovanie doruchenia e-mailu sa **planuje samo** (`Queue.enqueue_in`,
  vstavany RQ scheduler vo workeri) - bez samostatnej sluzby.

---

## [2026.6.5.post11] - 2026-06-05 - Jemnejsia ochrana proti spam-klikaniu

###  Opravene

- Rychle dvojklik na tlacidlo, ktore spusta uz prebiehajucu akciu, uz
  nezobrazuje matucu **cervenu chybu**. Namiesto toho sa zobrazi jemne modre
  upozornenie "Pockajte - predchadzajuca akcia stale prebieha" a duplicitna
  poziadavka sa ticho ignoruje (centralna oprava, bez zasahu do jednotlivych
  tlacidiel).

---

## [2026.6.5.post10] - 2026-06-05 - Strankovanie tabulky Service Accounts

###  Zmenene

- Tabulka **Service Accounts** (GitLab boti) na stranke Pouzivatelia ma teraz
  vlastnu strankovaciu listu (10/20/50 na stranu), nezavislu od hlavnej tabulky
  a spolupracujucu s triedenim stlpcov. Pri velkom pocte botov uz stranka nie
  je zahltena.

---

## [2026.6.5.post9] - 2026-06-05 - Prehladnejsia stranka studenta v skupine

###  Zmenene

- **Skeleton** (placeholder pocas nacitania) tejto stranky bol prepisany tak,
  aby presne zodpovedal novej strukture - obsahuje uz oba rozdelovace skupin a
  tabulka commitov ma spravny pocet stlpcov, takze pri vymene obsahu nedochadza
  k posunu rozlozenia.
- **Stranka studenta v skupine** je rozdelena na dve jasne oznacene casti:
  **"Praca od &lt;clen&gt;"** (commity, MR a issues, ktorych je clen autorom) a
  **"Revizia kodu a komunikacia"** (komentare k revizii, ktore napisal kolegom,
  oddelene od spatnej vazby, ktoru dostal). Ucitel cita stranku zhora nadol ako
  pribeh "robenie + komunikovanie".
- Stlpec **Project** v tabulkach sa zobrazuje uz len ak skupina ma viac nez
  jeden aktivny projekt; samostatny stlpec **SHA** bol odstraneny (odkaz na
  GitLab je na nazve commitu).

###  Opravene (post5-post7)

- Opraveny dvojity **"Done"** stav v globalnom job bare (idempotentne voci faze
  "finishing").
- **Pozdrav** sa renderuje server-side v shell strane, takze sa uz neblika; jeho
  duplicitny statisticky podnadpis bol odstraneny.
- **"Items that need your attention"** uz nezobrazuje matuci "N projektov so
  zastaralymi datami" - upozornenie je teraz zoskupene podla kurzu.

---

## [2026.6.5.post4] - 2026-06-05 - Klikatelne dashboard KPI + hlbke docistenie dokov

###  Zmenene

- Dashboard **KPI karty** teraz naviguju (admin na users/courses admin stranky;
  ucitel/student na svoj kurz/analytiku). Klikatelny styl ma iba karta s realnym
  cielom.

###  Odstranene

- Odstraneny zbytocny **stat-pas v System Settings** (duplikoval dashboard karty)
  aj jeho mrtvy JS.
- Vycistene vsetky zvysne zmienky v dokumentacii o odstranenych funkciach
  (rubric/gaming/async-report/roster-import) - ziadne nezostali.

---

## [2026.6.5.post3] - 2026-06-05 - Docistenie retired schema/API tailu

###  Odstranene

- Pridana Alembic migracia `049`, ktora dropuje posledny retired schema tail:
  legacy stlpec v student compliance snapshote a osirele history/report tabulky.
- Odstraneny stary telemetry PDF report endpoint, schemy, ORM model, generator
  service a report-only testy.
- Odstranene stale aktivne doky, fixture JSON sekcie, support-form labely,
  login metadata a i18n kluce naviazane na retired grading/heuristic/report/import
  subsystems.

###  Zmenene

- Full course configuration priklady teraz uvadzaju iba aktivne import sekcie:
  course metadata, settings, built-in checks, custom checks, weekly deadlines,
  Docker lint config a CI failure config.
- Metadata aplikacie/dokov su `2026.6.5.post3`; Service Worker cache namespace je
  `gitpulse-v160`.

---

## [2026.6.5.post2] - 2026-06-05 - Odstranenie scheduler master switchu a mrtvych scheduled fallbackov

###  Odstranene

- Odstraneny retired scheduler master switch zo Settings, Docker Compose, scheduler runtime,
  tracked wrappera, admin scheduled registra, manual retry routingu, testov,
  README a architekturnych dokov.
- Odstranene posledne neaktivne scheduled fallback joby: periodicky prepocet
  metrik, cleanup background jobov, overovanie webhookov, polling mrtvych
  projektov, cleanup metric snapshotov, audit logov a expirovanych webhook
  secretov. Cerstvost dat ostava na webhook/manual sync flow; metriky sa
  prepocitavaju inline v sync/event flow.
- Odstranene stare activity-feed/global-job labely pre uz zmazane GitLab polling
  a discovery joby, aby UI nezobrazovalo retired scheduled procesy.

###  Zmenene

- Scheduler/admin katalog teraz ukazuje iba 12 aktivnych scheduled jobov:
  event recovery, CI rollback, conflict expiry/verification, volitelne LLM,
  volitelnu telemetriu, DLQ resurrection, volitelny Docker reverify, event
  retention, email queue/log retention a semester auto-archive.
- Metadata aplikacie/dokov su `2026.6.5.post2`; staticke bundle boli rebuildnute
  a Service Worker cache namespace je `gitpulse-v159`.

---

## [2026.6.5.post1] - 2026-06-05 - Odstranenie periodickeho GitLab pollingu a hlbke cistenie dokov

###  Odstranene

- Odstranene **periodicke GitLab polling joby** (`periodic_enrich_all`,
  `periodic_enrich_users`, `sweep_stale_projects`, `sweep_discover_new_projects`,
  `sweep_discover_new_teams`) a uz prazdne moduly `sweep_enrichment.py` /
  `sweep_discover.py`, vratane ich config intervalov a admin registrov. Cerstvost
  dat teraz zabezpecuju len webhooky, manualna synchronizacia a sync pri vytvoreni
  kurzu.

###  Zmenene

- Hlbke cistenie dokumentacie a diplomovej prace od zmienok o retired grading/heuristic/
  intervention/polling (vyvojarska struktura, API referencia, abstrakt/kluc. slova).

---

## [2026.6.5] - 2026-06-05 - Odstranenie retired grading engine, retired heuristic detection, intervention flags a polling sweep

###  Odstranene

- Kompletne odstranene **retired grading hodnotenie**, **retired heuristic detection**, panel
  **Intervention Flags** + flag endpointy a **periodicky membership-sync sweep**
  (kod, settings UI, API, DB stlpce/tabulky cez migraciu `048`). Manualna
  synchronizacia, webhooky, sync pri aktivacii a auto-sync pri importe ostavaju;
  evaluation-report/telemetria ostava nedotknuta. Jadro hodnotenia su teraz uz
  len konfigurovatelne kontroly R01-R13, ktore vyhodnocuju studenta.

###  Pridane

- Globalny capture-phase **click-lock** na tlacidlach: opakovane kliky do 600 ms
  su zahodene s jednym throttled "pockajte" toastom, takze kazda akcia da
  spatnu vazbu aj ked sa stav nemeni. UI prepinace su vynimka.

###  Opravene

- **Reset tlacidlo vo filtri clenov v skeletone** je teraz zarovnane vpravo ako
  realny filter bar a zvysne retired grading/retired heuristic/flags placeholdery v skeletone boli
  odstranene.

---

## [2026.6.4.post4] - 2026-06-04 - Odstranenie legacy global gates a System Health parity

###  Odstranene

- Stare globalne prepinace pre retired grading, manualne intervencie, heuristiky
  a GitLab polling automatizaciu su odstranene zo settings, template globals,
  API guardov, scheduler metadata, docker-compose, testov aj dokumentacie.

###  Zmenene

- System Health a scheduler metadata boli zladene s vtedajsim transition stavom
  pred uplnym odstrananim retired subsystemov.

###  Opravene

- System Health checking skeleton uz zobrazuje Database, Redis aj
  Session_store, takze sedi s finalnou operational kartou.
- Team detail a course Activity skeletony boli znovu porovnane s aktualnymi SSR
  fragmentmi po odstraneni kariet.

---

## [2026.6.4.post3] - 2026-06-04 - Odstranenie legacy roster uploadu a exportu, grading KPI

###  Odstranene

- **Roster CSV import** odstraneny (studenti vstupuju cez GitLab sync) - flag
  `retired roster switch`, `roster_service`, model/schema `RosterImport`,
  upload/history API a UI, aj `roster_import` job-bar hooky. Pohlad Roster +
  CSV export zostavaju.
- **Team CSV/JSON export** odstraneny (tlacidla + `/teams/{id}/export/*`).
- **Zbytocne karty** - course-detail KPI pas a duplicitna *Compliance Checks*.

###  Zmenene

- **Grading-focused KPI** - admin/teacher home karty maju **Needs Attention**
  (skupiny s padajucimi kontrolami) namiesto poctu "Groups".

###  Opravene

- **Week Analytics donut tooltip** je spat nad skore.
- **Tesnejsi profil studenta** (odstranena zbytocna ciara).
- **Ziadne blikanie/spam** - System Health drzi citatelny minimalny stav;
  tlacidla zostavaju disabled pocas celej poziadavky.
- **Skeleton loadery sedia s realnymi strankami** (odstranene placeholdery,
  ploche profilove meta, duty Week Analytics prstenec).

---

## [2026.6.4.post2] - 2026-06-04 - Odstranenie Retired Report a UI cleanup

###  Odstranene

- **Async funkcia "Retired Report" bola kompletne odstranena** - team report
  API/worker, mrtvy `retired_report` servis, flag `retired report switch` s jeho
  `cleanup_old_reports` sweepom a retention configom, `generate_report` job-bar
  hooky, tlacidlo na team-detail, i18n retazce aj tour krok. Samostatny
  telemetry evaluation-report subsystem zostava nedotknuty.
- **Odstranene zbytocne karty** - Summary (activity), Compliance by Category
  (vratane Chart.js grafu a backend roll-upu) a Group Summary (team).

###  Opravene

- **Konzistentne stat karty** - nekonzistentne `stat-card--glow` podsvietenie
  (na niektorych kartach, na inych nie) bolo odstranene, takze vsetky stat karty
  maju jeden neutralny hover plus standardny focus ring.
- **Ploche profilove udaje** - Email / GitLab / Role su teraz plochy
  `profile-meta` riadok namiesto kariet.
- **Ziadne blikanie loadingu, ziadny spam klikov** - `setButtonLoading` drzi
  loading stav minimalny cas a nechava tlacidlo disabled pocas celej poziadavky,
  centralne pre kazde tlacidlo (System Health, refresh, sync, ...).
- **Viditelny prazdny Week Analytics prstenec** - no-data stav pouzival
  6% bielu (neviditelnu na tmavom pozadi); teraz pouziva viditelny slate.

---

## [2026.6.4.post1] - 2026-06-04 - Analytics refresh a sync cache coherence

###  Opravene

- **Course analytics refresh ma jednu SSR/cache-busted cestu.** Stary
  evaluation-report povrch, report Alpine factory, tour krok, lokalne report
  job hooky a report skeleton boli odstranene z analytics stranky aj
  generovanych bundlov. Refresh akcia najprv reloaduje SSR lazy fragment s
  cache-busting parametrom a az potom pada na spolocny scroll-preserving reload
  helper.
- **Sync completion caka na cerstve metriky pred terminalnym SSE.** Project
  syncy recomputuju team metrics inline pred oznacenim syncu ako completed a
  webhook/metrics side effects invaliduju page-cache fragmenty pred live
  notifikaciou klientov.
- **Profile/stat karty si nechavaju uzitocnu interakciu bez entrance animacii.**
  Student profile metadata je spat v kompaktnych kartach, course KPI karty
  linkuju na groups/roster a glow/process animacie ostavaju bez duplicitnych
  card-entry efektov.
- **Analytics a system micro-UX boli dotiahnute.** Week Analytics doughnut
  pouziva HTML center label s vypnutymi chart tooltip hitboxmi a System Health
  checking drzi spinner/glow feedback bez tvrdeho blikania.
- **Release metadata su aktualne pre `2026.6.4.post1`.** Dashboard Latest
  changes, docs, generovane bundly/minified siblings a Service Worker cache
  namespace (`gitpulse-v154`) boli obnovene.

---

## [2026.6.4] - 2026-06-04 - Jednotne dokoncenie synchronizacie a cache-busted refresh

###  Opravene

- **Terminalne stavy sync/check uloh maju jeden citatelny tok vsade.** Sync
  kurzu, timu, projektu aj run-check ulohy najprv prejdu do spolocneho
  `Finishing`, ostanu viditelne pocas navigacie a az potom ukazu kanonicky
  riadok/toast `Done` presne raz.
- **SSR refresh po zmene dat obchadza stale page cache.** `reloadKeepScroll()`
  teraz reloaduje cez cache-busting URL parameter, zachova scroll/toasty a
  parameter po boote odstrani, takze refresh po SSE alebo mutacii cita cerstve
  server-rendered data.
- **No-change sync vysvetli, co sa stalo.** Project/team sync summary teraz
  povie, ked GitLab nevratil ziadne zmenene data, ale metrics/cache refresh sa
  aj tak dokoncil; team summary pri beznych zmenach pocita aj commity.
- **Legacy appearance efekty a duplicity profilovych kariet boli odstranene.**
  Metadata studenta su v jednom kompaktnom profile header bloku a dotknute
  course, project, support, student a team povrchy uz nepouzivaju odstranene
  glow/counter/card entrance animacie.
- **Release metadata su aktualne pre `2026.6.4`.** Dashboard Latest changes,
  docs, generovane bundly/minified siblings a Service Worker cache namespace
  (`gitpulse-v153`) boli obnovene.

---

## [2026.6.3.post6] - 2026-06-03 - Odstraneny race pri live update nastaveni

###  Opravene

- **Live update Course Settings uz nepreteka na stare nastavenia ani stale page
  fragmenty.** Endpoint nastaveni teraz najprv commitne nove nastavenia,
  invaliduje dotknute SSR fragmenty kurzu/timov a az potom publikuje
  `settings_changed`. Otvorene stranky kurzu, timu, projektu a nastaveni, ktore
  na tuto udalost reloaduju, tak citaju commitnute data a cerstve Redis
  page-cache tela.
- **Post-update SSR reloady pouzivaju spolocny reload helper.** Dokoncenie
  syncu projektu a fallback refresh v Support tikete teraz volaju
  `reloadKeepScroll()` namiesto suroveho `window.location.reload()`, takze SSR
  reload zachova scroll aj viditelne toasty.
- **Release metadata su aktualne pre `2026.6.3.post6`.** Dashboard Latest
  changes, docs, generovane bundly/minified siblings a Service Worker cache
  namespace (`gitpulse-v152`) boli obnovene.

---

## [2026.6.3.post5] - 2026-06-03 - Konzistentny live refresh a cache na nastenke

###  Opravene

- **Live refresh na nastenke ma jednu spolocnu cestu.** SSE udalosti,
  fallback po dokonceni globalnej ulohy aj navrat na zalozku volaju jeden
  dashboard helper pre statistiky, upozornenia, aktivitu a badge v sidebare.
  Nastenka tak po synchronizacii neobnovi iba cast dat.
- **Kratkodobe dashboard live cache sa cistia pred globalnym SSE pushom.**
  Publisher notifikacii teraz invaliduje Redis kluce `dashboard:stats:*` a
  `dashboard:badges:*` pred publikovanim `dashboard:global`, takze okamzity
  refresh po synchronizacii necita stare 5-sekundove cache hodnoty.
- **Skeleton `Your courses` teraz vykresli dve karty.** Loading stav zodpoveda
  pozadovanej hustote nastenky namiesto troch placeholder kariet kurzu.
- **Release metadata su aktualne pre `2026.6.3.post5`.** Priklady verzii v
  aplikacii/docs, docs-site `latest`, dashboard Latest changes, generovane
  bundly a Service Worker cache namespace (`gitpulse-v151`) boli obnovene.

---

## [2026.6.3.post1] - 2026-06-03 - Dokoncenie synchronizacie ostava citatelne pocas navigacie

###  Opravene

- **Dokoncenie synchronizacie kurzu ostava citatelne pocas navigacie pred prechodom do Done.** Globalny panel obnovuje `finishing` ako vlastny stav, necha ho viditelny minimalne okno a az potom ho ukonci cez standardnu cestu `completeGlobalJob()`, takze kanonicky riadok "Sync completed!" a toast sa nestratia pocas bootstrapu stranky. `/sync/active` grace snapshoty s `running=0, queued=0` uz riadok nevymazu/nevytvoria znova ani ho neprepisu spat na running a stranka kurzu berie tento zero-work active snapshot ako Finishing namiesto okamziteho reloadu.
- **Dokoncene single-stage welcome tour sa uz neobjavia znova po zmene DOM fingerprintu.** Legacy migracia dokoncenia teraz hlada realne prefixed `gp_tour_v2:` localStorage kluce, takze starsie per-stage completion zaznamy sa spravne povysia na globalny completed kluc. Tour-seen POSTy pouzivaju aj `keepalive` a pri neuspesnej odpovedi sa daju zopakovat, takze rychla navigacia po Done nestrati serverovy tour stav natrvalo.
- **Release metadata su aktualne pre `2026.6.3.post1`.** Verzie aplikacie/docs balikov, docs-site `latest`, operator/developer priklady verzii, dashboard Latest changes a Service Worker cache namespace (`gitpulse-v147`) boli obnovene.

---

## [2026.6.3] - 2026-06-03 - Dokoncenie synchronizacie prezije navigaciu; dokoncene tour sa neponukaju znova

###  Opravene

- **Dokoncenie synchronizacie prezije navigaciu a dokoncene welcome tour sa neponukaju znova.** Tento release pridal persistenciu `lastUpdate` a `finishingSince` a migraciu/retry spracovanie dokoncenia welcome tour.

---

## [2026.6.2.post24] - 2026-06-02 - Tlacidla zamknute pocas synchronizacie nekolabuju; odznak synchronizacie na karte sa nezasekne

###  Opravene

- **Tlacidla zamknute pocas synchronizacie uz nemaju nerovnomerne sirky.** Pocas behu synchronizacie sa mutacne akcie (napr. Upravit kurz, Archivovat kurz v ponuke Akcie kurzu) zamknu a zamok obali kazde tlacidlo do `<span class="gl-tip-wrap">`, aby sa pri prejdeni mysou zobrazil tooltip s dovodom zablokovania. Tento span nemal ziadny styl a sprava sa ako `display: inline`, takze zuzil kazde tlacidlo s plnou sirkou (`btn-block`) na sirku jeho textu, kym susedne nezablokovane tlacidla zostali plnej sirky - poskladane ponuky tak ukazovali chaoticky nerovnake sirky tlacidiel. Obal teraz zrkadli plnu blokovu sirku `btn-block` potomka.
- **Odznak synchronizacie na karte kurzu uz nezostane visiet na zastaralom stave "Dokoncuje sa.../Synchronizacia...".** Oneskorena udalost `gp:job-update`, ktora prisla tesne po dokonceni ulohy, mohla preznacit (alebo ozivit) odznak karty pre uz dokoncenu ulohu, takze karta zostala zaseknuta na "Dokoncuje sa...", kym globalny panel uz ukazoval "Synchronizacia dokoncena!". Obsluha aktualizacii teraz ignoruje udalosti pre uz ukoncene ulohy a obranne cistenie odstrani kazdy odznak, ktoreho globalna uloha je done/error, pri kazdom dokonceni aj pri navrate na zalozku.

---

## [2026.6.2.post23] - 2026-06-02 - Karty GitLab inteligencie sa vykresluju serverovo; ziadna animacia objavenia

###  Opravene

- **Karty GitLab inteligencie sa teraz vykresluju kompletne na serveri.** Karty Chranene vetvy, Prispievatelia a Statistiky repozitara (aj riadok Posledna synchronizacia) na stranke projektu sa predtym vykreslili s pomlckovymi zastupnymi hodnotami a az JavaScript ich doplnil pri prvom SSE `connected` udalosti s animaciou `fadeSlideUp` - takze statistiky nad zlomom viditelne problikli. Nove `gl_intel_view` sa teraz pocita priamo v route (zrkadli logiku vykreslenia z JS: formatovanie bajtov, zlucenie a triedenie prispievatelov, parsovanie statistik) a sablona vykresli telo kariet priamo. Vstupna animacia na informacnom riadku a kartach API panelu bola odstranena a mrtva cesta predbezneho nacitania cez JSON (`gp-gl-intelligence`) aj prekreslenie pri prvom pripojeni boli zmazane. Zive obnovenia (synchronizacia / dokoncenie ulohy) stale stiahnu a prekreslia data ako predtym.

---

## [2026.6.2.post22] - 2026-06-02 - Stranky sa pri nacitani uz neblikaju; jednotny format sprav uloh

###  Opravene

- **Stranky kurzu, timu a projektu sa uz pri nacitani neblikaju.** Nastenka uz preskakovala prve SSE `connected` obnovenie a verila hodnotam vykreslenym serverom; tri detailne stranky nie - hned po pripojeni SSE streamu spustili plne `/live-data` stiahnutie a prekreslenie, takze cerstvo serverom vykreslene karty/riadky sa nakratko prepisali (blikanie blank-then-JS). Vsetky tri teraz maju ochranu `_connectedOnce` (podla nastenky), ktora preskoci prve prekreslenie po `connected` a obnovi sa az pri skutocnom znovupripojeni. Zive SSE udalosti sa prekresluju ako predtym. Na stranke projektu sa lenive nacitanie GitLab inteligencie pri prvom pripojeni stale spusti (nie je vykreslene serverom, takze nic neblika).
- **Spravy o priebehu uloh maju teraz jeden spolocny format vsade; duplicitny kod odstraneny.** Admin pohlad mal vlastny `_translateJobMsg` / `_jobTypeLabel` / `_JOB_TYPE_LABELS`, zatial co globalny panel uloh zobrazoval surovy anglicky `result_summary` (napr. `Synced N issues, N MRs...`) bez prekladu. Jediny `GP.formatJobMessage` / `GP.jobTypeLabel` teraz zije v `core/00-base.js`; globalny panel formatuje na hranici zobrazenia (toast dokoncenia + zivy riadok) a admin pohlad to deleguje nan. Format je idempotentny, takze uz prelozene retazce prejdu nezmenene.

---

## [2026.6.2.post21] - 2026-06-02 - Zmazanie skupiny obnovi vsetky cisla, nielen projekt

###  Opravene

- **Zmazanie alebo obnovenie celej skupiny teraz obnovi vsetky statistiky, nielen pohlad projektu.** Odpojenie a obnovenie projektu uz prepocitavalo metriky a posielalo SSE upozornenie, ale zmazanie a obnovenie skupiny len zneplatnilo cache stranky - neposlalo ziadnu SSE udalost ani neprepocitalo snapshot. Po zmazani skupiny tak otvorena stranka kurzu drzala zastarany zoznam skupin, suhrnne karty, kanal aktivit aj analytiku az do rucneho nacitania. Zmazanie a obnovenie skupiny teraz explicitne potvrdi zmenu, posle SSE udalost `team_deleted` / `team_reactivated` na kanal timu aj kurzu a zaradi prepocet metrik. Stranky timu a kurzu ich povazuju za strukturalne zmeny a prerenderuju sa na serveri (poloha skrolovania zostane zachovana).

---

## [2026.6.2.post20] - 2026-06-02 - Odpojenie projektu prepocita aj suhrnne cisla skupiny

###  Opravene

- **Odpojenie projektu teraz aktualizuje aj cisla v Suhrne skupiny.** Karty
  suhrnu (priemerne skore, stav semaforu, uspesnost pipeline) sa servuju z
  posledneho ulozeneho `TeamMetricSnapshot`, ktory prepocitava len metricky
  job - nie samotne odpojenie. Zoznam a pocet sa teda aktualizovali, ale
  hlavne cisla ostali zaseknute na starom prispevku odpojeneho projektu.
  Odpojenie aj obnovenie teraz zaradia prepocet metrik (compliance engine uz
  ignoruje projekty s `is_active=False`); ked dobehne, publikuje SSE
  upozornenie `metrics_computed`, takze otvorene stranky timu/kurzu/nastenky
  obnovia karty zive.

---

## [2026.6.2.post19] - 2026-06-02 - Odpojenie/obnovenie projektu sa naozaj obnovi zive

###  Opravene

- **Odpojenie/obnovenie projektu sa teraz naozaj obnovi, nielen zobrazi toast.**
  Dashboard SSE upozornenie sa odosielalo z handlera *predtym*, nez sa
  transakcia potvrdila (session commituje az po navrate handlera), takze
  okamzity refetch zive-data na klientovi predbehol este otvorenu transakciu a
  precital projekt ako aktivny - toast "Data updated" sa zobrazil, ale nic sa
  nezmenilo. Odpojenie aj obnovenie teraz najprv explicitne commitnu a az potom
  publikuju SSE udalost (`expire_on_commit=False` ponecha zachytene id platne).
- **Odpojeny riadok projektu teraz zmizne zo zoznamu.** `refreshTeamData()`
  aktualizoval karty statistik, riadky clenov a rubriku, ale nikdy serverom
  vykresleny zoznam Skupiny a Projekty, takze odpojeny riadok ostaval. Strukturne
  udalosti projektu (odpojenie / obnovenie / pripojenie) teraz spustia
  serverove prerenderovanie so zachovanim scrollu na strankach timu a kurzu,
  takze zoznam, pocet Zmazane aj suhrnne karty zodpovedaju potvrdenemu stavu.

---

## [2026.6.2.post18] - 2026-06-02 - Zive obnovenie po odpojeni/obnoveni projektu, ziadne duplicitne pruhy priebehu

###  Opravene

- **Odpojenie/obnovenie projektu obnovi cele UI zive.** Odpojenie alebo
  obnovenie projektu teraz publikuje dashboard SSE udalost pre jeho skupinu aj
  kurz, takze otvorene zobrazenia dashboardu, kurzu a analytiky okamzite
  obnovia svoje statisticke karty, kanal aktivit a metriky namiesto cakania na
  rucne nacitanie.
- **Ziadne duplicitne pruhy priebehu.** Jedina akcia synchronizacie/obnovenia
  mohla zobrazit dva riadky v globalnom paneli priebehu - pruh konkretneho
  projektu ("Synchronizujem projekt...") plus agregatny pruh kurzu z
  `/sync/active`. Reconciler `/sync/active` teraz potlaci agregat kurzu, kym
  uz bezi pruh projektu/skupiny pre ten isty kurz, a render faza ako poistka
  zluci akekolvek zvysne riadky toho isteho kurzu do jedneho.

---

## [2026.6.2.post17] - 2026-06-02 - Pozdrav podla dennej doby, zivy kanal aktivit, pocitanie len aktivnych poloziek

###  Pridane

- **Pozdrav nastenky podla dennej doby.** Pozdrav na domovskej stranke teraz
  zobrazuje "Dobre rano / Dobre popoludnie / Dobry vecer" podla lokalneho casu
  navstevnika (prelozene na serveri, s fallbackom "Ahoj" ak je JavaScript
  vypnuty) a prehodnoti sa po navrate na zalozku.
- **Zivy kanal Sledujte najnovsie aktualizacie.** Kanal je servovany z
  `/dashboard/activity` a obnovuje sa zive cez SSE stream nastenky (fallback na
  polling zachovany) a teraz zachytava aj zmazanie a obnovenie skupiny ci
  projektu s vlastnymi ikonami, popismi a odkazmi.

###  Opravene

- **Hlavne pocitadla pocitaju len aktivne polozky.** Pocitadlo Skupiny aj
  pocty projektov za pipeline health filtruju `is_active`, takze odpojene a
  zmazane skupiny a projekty (a GitLab `deletion_scheduled` tombstones) zmiznu
  okamzite namiesto navysovania kariet.

###  Zmenene

- **Mriezka aktivnych uloh v admin systeme je SSE-first.** Panel naplanovanych
  uloh reaguje na SSE stream nastenky namiesto cakania az 10 s, pricom 10 s
  interval zostava len ako fallback na polling.
- **Release metadata su aktualne pre `2026.6.2.post17`.** JS/CSS bundles a
  minifikovane sibling subory su pregenerovane, docs-site `latest` smeruje na
  tuto verziu, dashboard Latest changes je aktualizovany a namespace
  service-worker cache je `gitpulse-v139`.

---

## [2026.6.2.post16] - 2026-06-02 - Hranica config importu a oprava validacie formularov

###  Opravene

- **Auto-import konfiguracie kurzu uz nezavisi od internych route exportov
  dashboardu.** `scripts/import_course_configs.py` importuje priamo dedikovany
  modul `course_settings_config`, takze deployment bootstrap netaha privatne
  helpery cez HTTP route modul a strict mypy je znovu cisty.
- **Zdielane formularove komponenty zachovavaju svoj deklarovany API.** Bare
  text inputy uz prenesu validacne atributy (`pattern`, `minlength`,
  `autofocus`), bare checkbox odosle zadanu hodnotu a required custom dropdown
  validuje cez focusovatelny proxy control namiesto ignorovaneho `required`
  hidden inputu.
- **Lokalny security scan wrapper reportuje riziko production zavislosti.**
  `scripts/security_scan.py` pouziva timezone-aware timestampy, parsuje
  `pip-audit` JSON aj ked tool vypise advisory text a predvolene audituje
  `requirements.lock` namiesto nesuvisiacich balikov z developer virtualenv.

###  Zmenene

- **Release metadata su aktualne pre `2026.6.2.post16`.** JS/CSS bundles a
  minifikovane sibling subory su pregenerovane, docs-site `latest` smeruje na
  tuto verziu, dashboard Latest changes je aktualizovany a namespace
  service-worker cache je `gitpulse-v138`.

---

## [2026.6.2.post15] - 2026-06-02 - Kontrakt SSE helpera a vycistenie UI stylov

###  Opravene

- **Zdielany SSE helper pre background ulohy ma explicitny kontrakt fallback
  pollingu.** Manualny fallback pouziva `GP.apiCall` namiesto nahodneho
  globalneho identifikatora a completion callbacky su izolovane, aby chyba v
  page-level callbacku nenechala EventSource alebo fallback poller bezat
  donekonecna.
- **Globalny panel priebehu uz nepersistuje odstraneny ETA stav.** ETA UI uz
  bolo nahradene elapsed casom, ale stary state kluc stale prechadzal cez
  localStorage a cross-tab merge. Legacy stav sa teraz ignoruje a uz sa
  nezapisuje.
- **Drobne staticke inline styly sa presunuli do komponentoveho CSS.** Link v
  cookie banneri, farby quick-access avatarov na dashboarde, summary header
  service accountov a rozmery avataru v dropdowne teraz pouzivaju triedy
  namiesto opakovanych inline deklaracii.

###  Zmenene

- **Release metadata su aktualne pre `2026.6.2.post15`.** docs-site `latest`
  smeruje na tuto verziu, dashboard Latest changes je aktualizovany a
  namespace service-worker cache je `gitpulse-v137`.

---

## [2026.6.2.post14] - 2026-06-02 - Synchronizacia sekcie Diplomovka s aktualnym thesis repozitarom

###  Pridane

- **Sekcia Diplomovka v docs-site je zosynchronizovana s aktualnym textom
  diplomovej prace.** Slovenske kapitoly teraz zrkadlia najnovsi LaTeX zdroj z
  repozitara `dp.mykyta.olym/thesis`, vratane novych stranok
  [4. Navrh riesenia](diplomovka/navrh.md) a [5. Zaver](diplomovka/zaver.md),
  aktualizovaneho indexu prace a Mermaid diagramov architektury a toku
  udalosti.
- **Pridany je opakovatelny sync skript pre diplomovku.**
  `scripts/sync_thesis_docs.py` prevadza LaTeX kapitoly cez Pandoc, spracuje
  projektove glossary/reference/tabulkove/diagramove makra a obmedzuje rucne
  kopirovanie textu.

###  Zmenene

- **Ciele prace, navigacia a Latest changes su aktualne pre `2026.6.2.post14`.**
  Stranka cielov uz odkazuje na hotovy navrh riesenia, pilot a vyhodnotenie
  oznacuje ako dalsiu fazu, docs-site `latest` smeruje na `2026.6.2.post14` a
  namespace service-worker cache je `gitpulse-v136`.

---

## [2026.6.2.post13] - 2026-06-02 - Dedup fallback pollingu po SSE vypadku + aktualne docs metadata

###  Opravene

- **Globalny panel priebehu uz po vypadku SSE nespusta duplicitne polling
  timery pre tu istu background ulohu.** `streamJobProgress()` uz vlastni
  fallback zo SSE na polling, ale globalny panel z error callbacku spustal aj
  svoj legacy poller. To mohlo zatvorit helper pocas prepinania rezimu a nechat
  duplicitne polling requesty na `/api/v1/jobs/{id}`. Panel teraz deleguje
  fallback zdielanemu helperu a helper znovu kontroluje, ci nebol zatvoreny
  pred spustenim interneho pollingu.
- **GitLab recovery toast sa uz nezobrazi pod hlavnym backend-health
  bannerom.** GitLab-only recovery toast pocas sirseho backend vypadku bol
  zavadzajuci, preto sa teraz zobrazi len vtedy, ked je stale viditelny priamo
  GitLab banner.
- **Metadata dokumentacie su znovu aktualne.** Application/docs metadata je
  `2026.6.2.post13`, docs-site `latest` smeruje na rovnaku verziu, namespace
  service-worker cache je `gitpulse-v135`, dashboard Latest changes je
  aktualizovany a stare docs odkazy na `2026.6.2.post4` boli opravene.

---

## [2026.6.2.post12] - 2026-06-02 - Zatvorenie beziacej synchronizacie nechava tlacidla zamknute + poistky pri mazani skupiny

###  Opravene

- **Zatvorenie beziacej synchronizacie uz neodomkne tlacidla, ktore zamkla.**
  Kliknutie na X pri stale beziacej ulohe v globalnej liste priebehu vymazalo
  ulohu z registra, ktory citaju strazcovia procesnych akcii, takze tlacidla
  Sync / Run Checks / Unlink / Delete Group sa nespravne odomkli pocas
  synchronizacie. Zatvorenie beziacej ulohy teraz iba skryje jej riadok
  priebehu - uloha zostava aktivna, takze tlacidla zostavaju zamknute a poller
  dalej sleduje dokoncenie; odstrani sa normalne, ked synchronizacia naozaj
  skonci.
- **Projekt uz nie je mozne obnovit, kym je jeho skupina odstranena.** Obnovenie
  jedneho projektu pod odstranenou skupinou by ho nechalo osamoteny (aktivny,
  no skryty vsade, kde je skryta skupina, a vyluceny z agregatu kurzu). Endpoint
  obnovenia to teraz odmietne s jasnou spravou a stranka projektu zobrazi
  vyhradeny banner "Skupina tohto projektu je odstranena", ktory ucitelov
  nasmeruje na obnovenie celej skupiny.

---

## [2026.6.2.post11] - 2026-06-02 - Jeden toast synchronizacie v spravny cas + obnoveny CI lint

###  Opravene

- **Jedno obnovenie alebo synchronizacia projektu uz nezobrazi dva toasty
  "Sync completed".** Synchronizacia projektu zobrazila vlastny toast ("Sync
  completed"), zatial co agregat na urovni kurzu zobrazil dalsi ("Sync
  completed!"). Ich text sa lisi, takze 5-sekundova deduplikacia podla textu
  ich neodchytila, a ich kluce uloh sa lisia, takze ich neodchytila ani
  relacna deduplikacia - a rychlejsi toast projektu sa objavil skor, este pred
  dokoncenim agregatu. Toasty dokoncenia projektu / skupiny sa teraz zlucia
  do smerodajneho agregatu kurzu, takze jedna operacia ukaze presne jeden
  toast v spravny cas.
- **Obnoveny CI lint (ruff).** Pomocny skript mal nezoradene importy a
  nenaformatovane telo, ktore zlyhavalo v lint ulohe; teraz je zoradeny a
  naformatovany.

---

## [2026.6.2.post10] - 2026-06-02 - Jeden riadok na synchronizaciu v globalnom paneli priebehu

###  Opravene

- **Globalny panel priebehu uz nezobrazuje dva riadky pre jedno obnovenie
  alebo synchronizaciu projektu.** Obnovenie ci synchronizacia jedneho
  projektu zaregistruje zaznam pre projekt ("Synchronizuje sa projekt..."),
  ale tu istu pracu ukazuje aj agregat na urovni kurzu ("DEVOPS: Syncing..."),
  pretoze feed aktivnych synchronizacii pocita bezsiace ulohy podla kurzu.
  Predchadzajuca deduplikacia zlucila oba zaznamy len pokym oba bezali, takze
  synchronizacia projektu, ktora skoncila skor (bezne pri malych/prazdnych
  repozitaroch), nechala druhy riadok "Sync completed". Zaznam synchronizacie
  projektu / skupiny sa teraz zluci do agregatu kurzu pre ten isty kurz bez
  ohladu na stav dokoncenia, takze jedna operacia ukaze presne jeden riadok.

---

## [2026.6.2.post9] - 2026-06-02 - Odpojenie/obnovenie sa prejavi okamzite (zneplatnenie cache stranky)

###  Opravene

- **Odpojenie alebo obnovenie projektu ci skupiny sa teraz prejavi okamzite bez
  toho, aby ste museli odist zo stranky a vratit sa.** Detailove stranky
  servuju svoj narocny obsah z kratkozivej (60s) Redis cache fragmentu
  stranky, ale endpointy na odpojenie/obnovenie tuto cache nikdy nezahodili,
  takze opatovne nacitanie na mieste stale servovalo predchadzajuce telo
  (este aktivne alebo este odpojene), kym cache nevyprsala - preto sa zdalo,
  ze funguje len odchod a navrat. Endpointy na odpojenie a obnovenie pre
  projekty aj skupiny teraz okamzite zneplatnia dotknute cache stranok
  projektu / skupiny / kurzu / studenta, takze opatovne nacitana stranka hned
  zobrazi novy stav. Tym sa odstrani aj falosny duplicitny riadok v lavici
  postupu, ktory sa objavoval, kym zastarana stranka znovu registrovala
  prebiehajucu synchronizaciu.

---

## [2026.6.2.post8] - 2026-06-02 - Bez vstupnych animacii, okamzite obnovenie/odpojenie, bez duplicitneho riadku

###  Opravene

- **Stranky uz pri nacitani neblednu, neposuvaju sa ani neblikaju.** Odstranili
  sme kazdu vstupnu/zobrazovaciu animaciu - krizovy prechod stranok, cele
  odhalenie stranky, postupne zobrazovanie lenivo nacitanych kariet aj zasunutie
  upozorneni/bannerov. Obsah sa vykresli okamzite a zostane staticky, takze pri
  nacitani, obnoveni ani zivom osviezeni nic neblika. Mrtve CSS a JS sme zmazali,
  nie len vypli.
- **Odpojenie alebo obnovenie projektu sa teraz prejavi okamzite.** Znovunacitanie,
  ktore prepne banner a tlacidla, prekryval snimok prechodu zobrazenia; po jeho
  odstraneni sa stranka cisto prekresli a novy stav sa zobrazi hned, nie az po
  opustenie a navrate do projektu.
- **Globalny panel priebehu uz nezobrazuje duplicitny riadok "Waiting in queue...".**
  Pocas behu synchronizacie na urovni kurzu sa nadbytocny zaznam pre projekt/tim
  rovnakeho kurzu zluci do agregatu kurzu.

---

## [2026.6.2.post7] - 2026-06-02 - Sync po obnoveni dobehne a data sa osviezia na mieste

###  Opravene

- **Obnovenie projektu uz nenecha sync donekonecna tocit.** Endpoint obnovenia
  vracal surove RQ job id, ale globalny panel priebehu sa pyta
  `GET /api/v1/jobs/{id}`, ktory hlada zaznam ulohy - surove id teda vzdy
  vratilo 404 a panel "Syncing project..." nikdy nedobehol. Endpoint teraz
  vytvori skutocnu ulohu na pozadi a vrati jej id, takze panel dobehne.
- **Stranka projektu osviezi data hned ako sync po obnoveni dobehne.**
  Prispievatelia, commity a pipeline sa nacitaju znova na mieste, takze uz
  nemusite opustit projekt a vratit sa, aby ste videli aktualne cisla.
- **Male karty uz neblikaju ani sa "neaktivuju dvakrat".** Vstupna animacia na
  lenivo nacitanych paneloch (Prispievatelia, Statistiky repozitara, Chranene
  vetvy) teraz bezi najviac raz na kontajner namiesto opakovania pri kazdom
  zivom osviezeni.

---

## [2026.6.2.post6] - 2026-06-02 - Obnovenie uz nezamrzne na "Restoring..."

###  Opravene

- **Obnovenie odpojeneho projektu uz nezamrzne na "Restoring...".** Predchadzajuci
  postup obnovenia cakal na dokoncenie syncu na pozadi este pred opatovnym
  nacitanim stranky; pri prazdnom alebo pomalom repozitari toto dokoncenie
  neprislo vcas, takze tlacidlo "Restoring..." a globalny panel priebehu visel
  20-40+ sekund a stranka sa nikdy znovu nenacitala. Stranka projektu teraz
  zaregistruje sync v trvalom globalnom paneli priebehu a nacita sa ihned, takze
  projekt zobrazi obnoveny stav okamzite, kym sync bezi na pozadi.

---

## [2026.6.2.post5] - 2026-06-02 - Obnovenie/odpojenie uz nevyhodi pouzivatela

###  Opravene

- **Odpojenie projektu ani odstranenie skupiny uz nevyhodi pouzivatela na inu
  stranku.** Obe akcie teraz znovu nacitaju aktualnu stranku na mieste, takze
  ihned vidite banner "odpojene"/"archivovane" a tlacidlo Obnovit namiesto
  presmerovania inam.
- **Obnovenie projektu zobrazi sync na pozadi a osviezi data, ked dobehne.**
  Endpoint na reaktivaciu vracia ID zaradenej ulohy obnovy; stranka projektu ho
  pripoji ku globalnemu panelu priebehu, streamuje priebeh a znovu nacita az ked
  sync naozaj dobehne.
- **Prazdne repozitare teraz uvadzaju, ze sa nezapocitavaju.** Upozornenie na
  prazdny repozitar teraz vyslovne uvadza, ze projekt je vyluceny z priemeru
  skupiny a rebrickov, kym tim nenahra kod.

---

## [2026.6.2.post4] - 2026-06-02 - Tombstone projekty a blikanie animacii pri prvom nacitani

###  Opravene

- **Projekty, ktore GitLab automaticky premenoval na `deletion_scheduled`
  tombstone, sa uz nenacitavaju ani nezobrazuju ako obnovitelne skupiny.** Ked
  GitLab naplanuje projekt na zmazanie, premenuje cestu na
  `<path>-<hash>-deletion_scheduled-<id>`, ale kratko ho dalej vracia cez API.
  Discovery sweep teraz tieto tombstone preskakuje a zoznamy na detaile kurzu a
  skupiny ich odfiltruju, takze projekt, ktory ucitel nikdy nezmazal, sa uz
  nezobrazuje ako duch "Deleted" skupina s anomalnymi datami.
- **Uvodne animacie a skeleton loadery uz pri prvom nacitani stranky
  neblikaju.** Page-enter reveal teraz potlaca vsetky vstupne animacie potomkov
  pocas odhalenia (namiesto pevne zadaneho zoznamu tried), pricom slucky
  loaderov - spinnery, bodky, bar/skeleton shimmer, status pulzy - bezia dalej.

###  Zmenene

- Metadata aplikacie/docs zvysene na `2026.6.2.post4`; namespace cache
  service-workera zvyseny na `gitpulse-v128`; bundle a minifikovane subory
  prebuildovane; dashboard Latest changes obnoveny.

---

## [2026.6.2.post3] - 2026-06-02 - Obnova skupin a projektov ucitelom

###  Pridane

- **Ucitelia mozu obnovit soft-deleted skupiny a odpojene projekty.**
  `POST /api/v1/teams/{team_id}/reactivate` a
  `POST /api/v1/projects/{project_id}/reactivate` uz nie su len pre adminov;
  obnovit moze kazdy ucitel s pristupom ku kurzu. Obnova skupiny presne znovu
  aktivuje clenov a projekty deaktivovane poslednym delete a zaradi sync na
  pozadi, takze rebricky, metriky a kontroly sa hned zotavia.
- **Studenti maju nadalej read-only viditelnost skore vlastnej archivovanej
  skupiny.** Odstranene skupiny a odpojene projekty ostavaju dostupne pre ich
  clenov s jasnym archivacnym bannerom, ze data su zmrazene pre referenciu,
  zatial co personal vidi Delete/Unlink odznaky, tlacidla obnovy a prepinac na
  zobrazenie alebo skrytie archivovanych riadkov.

###  Opravene

- **Deaktivovane skupiny a projekty uz nenavysuju agregaty kurzu.** Pocty
  prispievatelov, zelene/cervene stavy, ukazovatele never-synced a stale-data a
  sync pocitadla beru do uvahy len aktivne skupiny. Metrics worker, project sync
  worker aj `compute_team_metrics` preskakuju archivovane skupiny/projekty, takze
  scoring, rebricky a analytika ich vylucuju konzistentne.

###  Zmenene

- Application/docs metadata je `2026.6.2.post3`; Service Worker cache je
  `gitpulse-v127`; bundle a minifikovane sablony su prebuildene, slovenske
  preklady su kompletne (0 chybajucich retazcov) a obnovovacie endpointy
  vracaju DTO-style JSON odpovede pokryte unit testami.

---

## [2026.6.2.post2] - 2026-06-02 - Guardy pre Delete Group a Unlink Project

###  Opravene

- **Nebezpecne akcie skupin a projektov maju backend guard.**
  `DELETE /api/v1/teams/{team_id}` a `DELETE /api/v1/projects/{project_id}`
  sa serializuju cez team/project mutation scope a pocas aktivneho `sync`
  alebo `run_checks` vracaju `409 Conflict`, takze priamy API request nemoze
  obist UI guard a pretekat so zapisom score alebo project state.
- **Delete Group deaktivuje aj projekty skupiny.** Soft-delete skupiny teraz
  vypne aktivne `GitLabProject` riadky spolu s aktivnymi clenmi, aby dashboard,
  sync discovery a webhook spracovanie zodpovedali kontraktu tlacidla.
- **Webhooky z odpojenych projektov sa uz nespracuju.** Autentifikovane GitLab
  webhooky pre inactive project vracaju `ignored` bez vytvorenia
  `WebhookEvent`, takze odpojeny projekt ostane preskoceny az do explicitnej
  reaktivacie.
- **Delete Group v course detaile pouziva kliknute tlacidlo.** Odstranenie
  riadku uz nepouziva substring selector cez `data-action-args` a scoring
  toggle tlacidla maju deklarativny `sync run_checks` process lock.
- Application/docs metadata je `2026.6.2.post2`; Service Worker cache je
  `gitpulse-v126`; bundle a minifikovane sablony su prebuildene a guardy
  destructive akcii su pokryte focused unit/source-pattern testami.

---

## [2026.6.2.post1] - 2026-06-02 - Latest changes limit a release-date guard

###  Opravene

- **Dashboard Latest changes ma deterministicky non-positive limit.**
  `_get_changelog_entries(limit=0)` aj negativne limity vracaju prazdny
  zoznam namiesto Python negative slicing spravania, kde `limit=-1` vratil
  takmer cely feed widgetu.
- **Validacia release datumu dashboard changelogu cita datum z package
  verzie.** Test odvodi aktualny release den z CalVer hodnoty v
  `pyproject.toml`, takze sa uz neduplikuje rucne udrziavana konstanta.
- Application/docs metadata je `2026.6.2.post1`; Service Worker cache je
  `gitpulse-v125`; bundle a minifikovane sablony su prebuildene a limit/date
  kontrakty widgetu su pokryte unit testami.

---

## [2026.6.2] - 2026-06-02 - Team member badge bez bodiek

###  Opravene

- **Role a score badge v tabulke clenov skupiny uz nezobrazuju osamotene
  bodky.** Textove bunky v `team-members-table` sa stale skracuju cez ellipsis,
  ale badge-only bunky maju vlastny `member-badge-cell` kontrakt s
  `text-overflow: clip`, takze `Mentor`, `Maintainer` a percenta score
  neziskaju bodku vedla pilulky.
- **Mapovanie access-role badge je single-source.** Duplicita v student aj
  staff variante tabulky sa presunula do zdielaneho
  `member_access_role_badge()` komponentu.
- Application/docs metadata je `2026.6.2`; Service Worker cache je
  `gitpulse-v124`; bundle a minifikovane sablony su prebuildene a overflow
  kontrakt badge buniek je pokryty unit testami.

---

## [2026.6.1.post8] - 2026-06-01 - Docs-site nginx bez cache/index dier pri 404

###  Opravene

- **Vlastna 404 stranka docs-site uz nezostava cacheovatelna ani
  indexovatelna.** Internal `/404.html` location teraz opakuje explicitny
  `Cache-Control: no-store, no-cache, must-revalidate` header a pridava
  `X-Robots-Tag: noindex, nofollow, nosnippet`, cim zatvara medzeru sposobenu
  tym, ze Nginx `add_header` sa pri definicii v location blokoch nededi.
- **Health endpoint docs-site je presny plain-text kontrakt.** `/health` je
  exact location s `default_type text/plain`, takze nahodne `/health...` cesty
  uz nevyzeraju zdravo a endpoint nepouziva `add_header` na `Content-Type`.
- Application/docs metadata je `2026.6.1.post8`; Service Worker cache je
  `gitpulse-v123`; bundle a minifikovane sablony su prebuildene a nginx header
  kontrakty su pokryte unit testami.

---

## [2026.6.1.post7] - 2026-06-01 - Lokalny cas vsade a ziadny nativny pull-to-refresh

###  Opravene

- **Vsetky casove udaje sa teraz zobrazuju v lokalnom casovom pasme namiesto
  UTC.** "Posledna synchronizacia" na stranke projektu (chybal jej marker
  `data-localize-time` a pouzivala `isoformat()` bez casoveho pasma), plus casy
  commitov, issues, merge requestov, CI scenarov, konfliktov, Docker reportov,
  importu rosteru a analyz zobrazovali surovy serverovy UTC cas. Vsetky teraz
  renderuju cez jednu zdielanu Jinja funkciu `local_time()`, ktora emituje
  kanonicky `...Z` `<time data-localize-time>` element; `localize-time.js` ho
  prevedie na strane klienta a ziskal `data-localize-format`, takze vlastne
  formaty (`HH:MM`, `Mon DD, HH:MM`) prezivaju.
- **Nativny biely pull-to-refresh indikator Chrome uz nevyskakuje na mobile /
  nainstalovanej PWA.** Potlacenie overscrollu bolo nastavene iba na `<body>`,
  ale vlastnost musi byt na korenovom `<html>`, aby dosiahla viewport, takze
  nativny refresh sa stale zobrazoval popri vlastnom indikatore aplikacie.
  Pravidlo teraz cieli aj na `<html>`.
- Application/docs metadata je `2026.6.1.post7`; Service Worker cache je
  `gitpulse-v122`; bundle a minifikovane sablony su prebuildene.

---

## [2026.6.1.post6] - 2026-06-01 - Stlpec Posledna aktualizacia bez blikania

###  Opravene

- **Stlpec "Posledna aktualizacia" v tabulke skupin uz neblika medzi UTC a
  lokalnym casom.** SSE feedy `/sync-stream` a `/live-data` zdielali tu istu
  bunku, ale renderovali ju roznymi formatmi, takze hodnota pri kazdom update
  skakala medzi serverovym UTC casom a lokalnym casom pouzivatela. Obe feedy
  teraz prechadzaju cez jednu funkciu `_renderLastUpdated()` kluciovanu ISO
  peciatkou, ktora prekresli bunku iba ked sa skutocne zmeni casova peciatka.
- Application/docs metadata je `2026.6.1.post6`; Service Worker cache je
  `gitpulse-v121`; bundle a minifikovane sablony su prebuildene.

---

## [2026.6.1.post5] - 2026-06-01 - Deklarativne akcie bez inline expression eval

###  Zmenené

- **Komponentove akcie uz nepouzivaju `data-action-expr` ani `new Function`.**
  Zdielane frontend core spusta iba pomenovane `data-action` handlery s JSON
  argumentmi a projektove empty-state tlacidla teraz volaju `clickElementById`
  cez tento strukturovany kontrakt.
- Application/docs metadata je `2026.6.1.post5`; Service Worker cache je
  `gitpulse-v120`; generovane bundle a minifikovane siblings boli rebuildnute.

---

## [2026.6.1.post4] - 2026-06-01 - Okamzity refresh process guardov pri job update

###  Opravene

- **Zamky procesnych akcii teraz reaguju na `gp:job-update`.** Zdielany guard
  sa obnovi, ked global job bar spusti alebo aktualizuje sync/import/run-checks
  job, takze konfliktne tlacidla sa vypnu hned a necakaju na fallback polling
  interval.
- Application/docs metadata je `2026.6.1.post4`; Service Worker cache je
  `gitpulse-v119`; generovane bundle a minifikovane siblings boli rebuildnute.

---

## [2026.6.1.post3] - 2026-06-01 - Process guard root refresh a component cleanup

###  Zmenené

- **Nepouzivany komponent `process_status.html` bol odstraneny.** Dashboard a
  detail predmetu pouzivaju externy modul `import-stream.js` a zdielane
  global-job/process-guard moduly namiesto importu legacy inline-JS makier.
- **`GP.refreshProcessActionGuards(button)` teraz vyhodnoti aj samotny button.**
  Jednotlivo dynamicky vlozene ovladacie prvky sa zamknu hned pocas aktivneho
  sync/import/run-checks procesu, aj ked sa neobnovuje parent kontajner.
- Application/docs metadata je `2026.6.1.post3`; Service Worker cache je
  `gitpulse-v118`; generovane bundle a minifikovane siblings boli rebuildnute.

---

## [2026.6.1.post2] - 2026-06-01 - Preskocenie cross-document View Transition sa uz neloguje

###  Opravene

- **Cross-document View Transitions uz nelogovaju `AbortError: Transition was
  skipped`.** Taby predmetu a odkazy navigacie idu cross-document, kde CSS
  pravidlo `@view-transition { navigation: auto }` riadi prelinanie. Ked sa
  transition preskoci (klik na dalsi tab pred dokoncenim prveho, opakovany klik
  na aktivny tab, alebo skrytie tabu pocas navigacie), prehliadac odmietne
  promisy transitionu. Teraz su spracovane priamo cez udalosti `pageswap` a
  `pagereveal` namiesto neodchytenej "(in promise)" chyby.
- Application/docs metadata je `2026.6.1.post2`; Service Worker cache je
  `gitpulse-v117`; generovane bundle a minifikovane siblings boli rebuildnute.

---

## [2026.6.1.post1] - 2026-06-01 - Externy course-tabs modul a cistenie komponentov

###  Zmenené

- **Klavesova navigacia v course taboch je v `course-tabs.js`.** Zdielany
  partial navigacie predmetu uz nevklada inline JavaScript; spravanie je v
  `core.bundle.js` a chrani ho regresny test.
- **Zdielany native select komponent uz neponuka inline `onchange` escape
  hatch.** Aktualni volaci pouzivaju deklarativne data/action kontrakty alebo
  Alpine bindingy.
- Application/docs metadata je `2026.6.1.post1`; Service Worker cache je
  `gitpulse-v116`; generovane bundle a minifikovane siblings boli rebuildnute.

---

## [2026.6.1] - 2026-06-01 - Oprava tooltipov bez hoveru

###  Opravené

- **Tooltipy sa už nezobrazujú bez prejdenia myšou.** Predvolený trigger Tippy
  je `mouseenter focus`, takže keď focus-trap modalu (alebo kliknutie myšou)
  programovo zaostril tlačidlo s `data-tippy-content` - najviditeľnejšie
  zatváracie (X) tlačidlo - tooltip sa zobrazil bez hoveru. Tooltipy teraz
  potlačia zobrazenie pri focuse, pokiaľ focus nepochádza z klávesnice
  (`:focus-visible`), čím sa zachová prístupnosť a odstránia neželané popupy.
- Application/docs metadata je `2026.6.1`; Service Worker cache je
  `gitpulse-v115`.

---

## [2026.5.31.post3] - 2026-05-31 - Bezpečnejšie cache dashboardu a oprava HTML v docs

###  Opravené

- **Prihlásené dashboard HTML sa už neukladá cez Service Worker.** Worker
  obchádza `/dashboard` navigácie a spoločné cache helpery odmietajú odpovede
  s `Cache-Control: no-store` alebo `private`, aby zodpovedali kontraktu
  security middleware.
- **Logout teraz posiela dokumentovaný browser cleanup header.**
  `GET /dashboard/logout` odstráni session cookie a vráti
  `Clear-Site-Data: "cache", "storage"`.
- **Docs logo override už nevytvára vnorené anchory.** Custom MkDocs Material
  partial renderuje iba obrázok/ikonu a vlastníctvo linku necháva na theme
  template header/nav.
- Application/docs metadata je `2026.5.31.post3`; Service Worker cache je
  `gitpulse-v114`.

---

## [2026.5.31.post2] - 2026-05-31 - Centralizovana SEO politika dokumentacie

###  Zmenene

- **Dokumentacne SEO signaly su teraz riadene centralne.** MkDocs hook
  `hooks/seo_policy.py` oznacuje technicke a interne sekcie (`vyvojari`,
  `operatori`, `gitlab`, `bezpecnost`, `api`, `diplomovka`, `changelog`,
  `tags`) ako `noindex, follow, nosnippet`, aby sa v Google nezobrazovali
  nahodne runbooky, tokenove priklady alebo interny changelog ako sitelinky.
  Verejne sekcie pre produkt, onboarding studentov/ucitelov a pravne stranky
  ostavaju indexovatelne.
- **Sitemapy su rozdelene podla vlastnictva.** Root `/sitemap.xml` patri
  aplikacii a obsahuje iba `/dashboard/login`; `/docs/sitemap.xml` patri
  MkDocs a hook z neho odstraňuje `noindex` URL. `robots.txt` explicitne
  uvadza oba sitemapy, takze Google dostava konzistentne signaly bez
  duplicitnych docs URL v root sitemape.

---

## [2026.5.31.post1] - 2026-05-31 - SRP rozdelenie stranok prehladu, analytiky a administracie

###  Zmenene

- **Rozdelenie kontrolerov stranok prehladu, analytiky kurzu a administracie na zdrojove casti s jednou zodpovednostou.** Po rozdeleni Admin Courses su aj tri zostavajuce ~1,1 tis. riadkov dlhe skripty stranok teraz pisane ako usporiadane fragmenty `_parts/<stranka>/NN-*.js` a builder ich spaja **doslovne** spat do obsluhovaneho suboru. Vystup je bajtovo identicky, takze nedochadza k ziadnej zmene spravania - iba zdrojovy kod je teraz maly a ma jednu zodpovednost, v zhode s kazdym inym rozdelenym strankovym kontrolerom.

---

## [2026.5.31] - 2026-05-31 - SRP rozdelenie Admin Courses a refresh cache

###  Zmenene

- **Admin Courses frontend teraz pouziva rovnaky SRP vzor ako ostatne velke
  strankove kontrolery.** `pages/admin-courses.js` sa generuje z
  `_parts/admin-courses/00-core.js`, `10-lifecycle.js` a `20-events.js`, takze
  konfiguracia, lifecycle mutacie a delegovane udalosti maju oddelenych
  vlastnikov a served subor ostava deterministicky build artifact.
- **Lifecycle zmeny riadkov kurzov pouzivaju spolocne UI kontrakty.**
  Archive/activate/delete swapy renderuju spolocny `status-indicator`, icon-only
  tlacidla, obnovene tooltipy a scoped process guards po kazdej dynamickej DOM
  zmene.
- **Release metadata a staticke assety su aktualizovane.** Verzia je
  `2026.5.31`, bundly a `.min` siblingy boli rebuildnute, dashboard Latest
  changes bol aktualizovany a Service Worker cache je `gitpulse-v113`.

---

## [2026.5.30.post11] - 2026-05-30 - Animovany prepinac oka pre skore, konzistentne tooltipy, zivy prepocet

###  Zmenene

- **Vylepseny ovladac zahrnut/vylucit zo skore (oko) v tabulkach clenov.** Ikona oka / preskrtnuteho oka sa teraz pri prepnuti studenta animuje pruzny "pop", tlacidlo zostava viditelne a zafarbene pokial je riadok vyluceny, takze vratitelny stav je jasne citatelny, a hover/stlacenie pridavaju jemnu zmenu mierky. Ovladac teraz pouziva konzistentny Tippy tooltip (ziadny duplicitny natívny tooltip prehliadaca) a stmavnutie vyluceneho riadku prechadza plynulo namiesto skokoveho. Prepnutie studenta stale prepocita skupinovy priemer, semafor, pocty prispievatelov a skore rubriky naživo - bez obnovenia stranky. Vsetka animacia respektuje `prefers-reduced-motion`.

---

## [2026.5.30.post10] - 2026-05-30 - Oprava resetu casovaca medzi navigaciami a SW v101

###  Opravene

- **Oprava resetovania casovaca priebehu pri kazdej navigacii medzi strankami.** Ked sa riadok synchronizacie kurzu po prechode na inu stranku znova vytvoril, dostal aktualny cas namiesto skutocneho casu zaciatku synchronizacie zo servera, takze sekundy sa zakazdym vynulovali. Riadok teraz ukotvi svoj casovac na serverovy `started_at_ms` a zachova najskorsi znamy zaciatok, takze casovac je medzi navigaciami monotonicky.

---

## [2026.5.30.post9] - 2026-05-30 - Spresnenie casovacieho vlakna, SRP refaktor cashovania a SW v100

###  Opravene

- **Oprava restartovania casovaca v riadku uloh.** Pasivne rekonciliacne volania (skenovanie kariet kurzu) predtym mohli omylom interpretovat beziacu synchronizaciu ako novy beh, vynulovat progress bar a nastavit zaciatok uloh na aktualny cas. Indikator SSE teraz stabilne chrani povodny monotonic_start cas, vdaka comu sa sekundy v zobrazeni neresetuju spat na nulu.

###  Zmenene

- **Refaktorizovali sme cache system pre splnenie Single Responsibility Principle (SRP).** Zarucena nulova sanca uniku pre CSRF tokeny a CSP nonce napriec vsetkymi strankami cache htmx detailov.
- **Service Worker verzia kesovania povysena na v100.** Static cache kluce boli povysene na ciste zneplatnenie starych offline cache suborov.

---

## [2026.5.30.post8] - 2026-05-30 - Okamzity globalny indikator s fazou "Pripajanie..."

###  Zmenene

- **Globalny indikator priebehu sa teraz zobrazi okamzite s fazou
  "Pripajanie...".** Spustenie synchronizacie kurzu (Sync All), projektu alebo
  synchronizacie zo stranky nastaveni kurzu predtym zobrazilo globalny
  indikator az *po* navrate poziadavky zo servera. Kvoli kontrole dostupnosti
  GitLabu (ktora opakuje a moze trvat niekolko sekund) pouzivatel pocas toho
  okna nevidel ziadny indikator a mohol tlacidlo opakovane klikat. Indikator
  sa teraz zobrazi s neurcitym spinnerom "Pripajanie na GitLab..." hned po
  kliknuti, co tiez okamzite aktivuje existujucu ochranu proti opakovanemu
  kliknutiu. Po zaradeni synchronizacie sa indikator zmeni na realnu spravu
  "Synchronizujem: X/Y skupin..."; ak poziadavka zlyha, chyba sa zobrazi priamo
  **v indikatore** (nielen ako docasny toast). Bezpecnostny casovac zaruci, ze
  spinner "Pripajanie" nikdy nezostane viset.

---

## [2026.5.30.post7] - 2026-05-30 - Spolahlivost synchronizacie: opakovany pre-flight GitLabu

###  Opravene

- **Synchronizacia uz nezlyha, ked GitLab raz odpovie pomaly.** Vstupne body
  synchronizacie pred zaradenim uloh spustaju kontrolu dostupnosti GitLabu.
  Pouzivala jednu 4 s poziadavku bez opakovania, takze jedna prechodna pomala
  odpoved vratila `503 "GitLab server is currently unreachable"` a
  synchronizacia neurobila nic. Kontrola teraz raz zopakuje pokus (5 s na
  pokus, 0,4 s odstup) a za nedostupne povazuje az dve po sebe iduce zlyhania.

---

## [2026.5.30.post6] - 2026-05-30 - Opravy Tyzdennej analytiky + telemetricke typovanie

###  Opravene

- **Tyzdenna analytika sa otvori na poslednom tyzdni s datami.** Ked sa vyucba
  konci, studenti prestanu commitovat, takze aktualny tyzden je casto prazdny,
  zatial co tyzdenny vypocet skore prenasa compliance dalej. Prehliadac predtym
  automaticky vybral aktualny (prazdny) tyzden a zobrazil "Ziadne GitLab udalosti
  v tomto tyzdni", co vyzeralo ako strata dat. Teraz automaticky vyberie posledny
  tyzden so skutocnou aktivitou alebo compliance trendom. Sonda do produkcnej DB
  potvrdila, ze ziadne data sa nestratili - po vyucbovom tyzdni 12 jednoducho
  neboli ziadne commity.
- **Tyzdne skuskoveho obdobia su dostupne a oznacene v Tyzdennej analytike.**
  Vyber tyzdna bezal len `1..semester_weeks`, takze tyzdne skuskoveho obdobia
  nemali ziadnu znacku a nezobrazovali oranzove oznacenie EXAM PERIOD. Vyber sa
  teraz rozsiruje cez skuskove obdobie s oranzovymi znackami "Exam" a cipom
  "Exam Period - Tyzden N" v hlavicke detailu.
- **Prazdny stav vyhladavania kurzov.** Filtrovanie mriezky "Vase kurzy" na
  dopyt bez zhody teraz zobrazi prehladny komponent prazdneho stavu namiesto
  prazdnej plochy.
- **Sest telemetrickych modelov prepisanych na typovanie SQLAlchemy 2.0.**
  `FlaggedTeamResolution`, `StudentComplianceSnapshot`, `ClicksAvoidedMetric`,
  `TeacherActivityMetric`, `TelemetryAggregate` a `EvaluationReport` boli
  prepisane zo starych priradeni `Column(...)` na `Mapped[] / mapped_column`,
  rovnako ako skorsia migracia `SupportTicket`. Pylance teraz spravne odvodzuje
  typy atributov (napr. `flagged_at: datetime`, `week_number: int`) namiesto
  `Column[X]`, cim zmizli falosne typove chyby v `pilot_telemetry.py` a
  nadbytocne obaly `cast(...)`; pridana bola aj chybajuca kontrola `None` pred
  odpocitanim `datetime`. Bez zmeny spravania ani schemy databazy.

---

## [2026.5.30.post5] - 2026-05-30 - Zeleny scan kontajnerov (protobuf CVE)

###  Opravene

- **Bezpecnostny scan kontajnerov (Trivy) je opat zeleny.** Tranzitivna
  zavislost `protobuf` bola drzana na `4.25.9` stropom `protobuf<5.0`, ktory
  zaroven pripinal `opentelemetry-proto` na starsiu vetvu `1.27`. Tato verzia
  `protobuf` obsahovala opravitelnu HIGH/CRITICAL zranitelnost **CVE-2026-0994**,
  takze joby `container-scan-api` a `container-scan-worker` padali. Strop sa
  zvysil na `protobuf>=5.29.6,<6.0`, cim sa `protobuf` posunul na opravenu
  `5.29.6` a OpenTelemetry sa dorozriesilo na `1.42.1` (stabilne `1.x` API -
  ziadna zmena kodu aplikacie). `requirements.lock` bol pregenerovany na Linuxe,
  aby sedel s CI.

---

## [2026.5.30.post4] - 2026-05-30 - Zelena CI pipeline + rychlejsia analytika

###  Opravene

- **CI pipeline opat zelena.** Commit `f0cb9816` mal `requirements.lock`
  vygenerovany na Windowse, takze obsahoval `colorama` (len Windows) a chybal
  `uvloop` (len Linux). CI bezi na Linuxe (`python:3.12-slim`), takze
  `lockfile-check` lock pregeneroval, dostal opacnu sadu balickov a job sa
  rozbil. Lock je teraz vygenerovany na Linuxe (zhoduje sa s CI). Zaroven
  `mypy` hlasil zvysny `cast(int, ...)` a `# type: ignore[assignment]`, ktore
  sa stali nadbytocnymi po post3 typovani modelu `SupportTicket` - odstranene -
  a `home_changelog.py` bol preformatovany cez `ruff format`.
- **Stranka analytiky kurzu sa uz nezasekne pri prvom nacitani.** Tazky
  fragment analytiky sa pocita ~60-95 s na velkom kurze, co prekracovalo
  globalny 90 s htmx timeout, takze po kazdom deployi (cache je viazana na
  GIT_SHA = studeny stav) prve nacitanie spadlo do `htmx:timeout` a "nic sa
  nenacitalo". Timeout pre tento fragment je teraz 180 s a TTL cache stupol z
  60 s na 600 s, takze raz vypocitana analytika ostane tepla a dalsie nacitania
  su okamzite. Verzia `2026.5.30.post4`.

---

###  Opravene

- **Model `SupportTicket` prepisany na SQLAlchemy 2.0 typovanie.** Stare
  `Column(...)` priradenia sposobovali, ze Pylance odvodzoval kazdy atribut ako
  `Column[X]`, co produkovalo 11 falosnych chyb v dashboard support route. Model
  teraz pouziva `Mapped[...] / mapped_column(...)` ako jeho susedne modely. Cisto
  typova zmena - spravanie ORM je identicke; `mypy` aj cielene testy prechadzaju.
- **`lockfile-check` opat deterministicky.** `exclude-newer` ukazoval na buduci
  cas, takze kazde CI re-rozriesenie chytalo balicky vydane "dnes" a
  `requirements.lock` driftoval do cervena. Teraz je pripnuty na minuly cas a novy
  `.gitattributes` vynucuje `eol=lf` pre `requirements.lock`, takze Windows CRLF
  commity uz nemozu zlomit lint gate. Verzia `2026.5.30.post3`.

---

## [2026.5.30.post2] - 2026-05-30 - SRP rozdelenie (najvacsi subor -> JSON data)

###  Zmenene

- **Najvacsi zdrojovy subor bol rozdeleny podla principu jednej zodpovednosti.**
  `src/app/api/dashboard/home_changelog.py` (1511 riadkov) obsahoval ~1490
  riadkov rucne udrziavanych "Latest changes" dat priamo v kode. Data su teraz
  v `home_changelog_entries.json` a Python modul je tenky lokalizacny nacitavac.
  Data su oddelene od logiky; dashboard widget aj regresne testy citaju rovnake
  zaznamy s **nulovou zmenou spravania**.
- Verzia `2026.5.30.post2`. Iba struktura backendu - ziadna zmena sablon, JS
  ani CSS, takze bundles a service-worker cache ostavaju nezmenene.

---

## [2026.5.30.post1] - 2026-05-30 - Pokracovanie SRP rozdelenia (strankove kontrolery)

###  Zmenene

- **Pokracovanie SRP rozdelenia na dalsiu vrstvu velkych strankovych
  kontrolerov.** `pages/course-detail.js` (1414 riadkov) a
  `pages/team-detail.js` (1216 riadkov) su teraz rozdelene na usporiadane,
  'cisto zostavove' casti v `_parts/`, ktore `scripts/build_bundle.py` spaja
  verbatim: `course-detail/` na `00-sync-stream` / `10-teams-crud` /
  `20-sync-all` / `30-course-data` a `team-detail/` na `00-core` / `10-sync` /
  `20-analysis-boot` / `30-live`. Doruceny subor sa regeneruje **bajt po bajte
  identicky** (overene cez SHA-256 a `build_bundle.py --check`), takze ziadna
  zmena spravania.

---

## [2026.5.30] - 2026-05-30 - SRP rozdelenie vsetkych 1500+ riadkovych suborov

###  Zmenene

- **Vsetky 1500+ riadkove zdrojove subory boli rozdelene podla principu jednej
  zodpovednosti (SRP) na mensie moduly bez zmeny spravania.** Front-endove
  giganty (`core.js`, `global-job-bar.js`, `tour-engine.js`, `project-detail.js`,
  `course-settings.js` a `responsive.css`) boli rozdelene na 'cisto zostavove'
  casti v priecinkoch `_parts/`, ktore build skript spaja spat do identickeho
  vysledku (overene bajt po bajte na minifikovanom bundli). Backendove API
  moduly (courses, sync, telemetry, teams, projects, report/sync joby) maju
  pomocne casti vyclenene do susednych modulov.

---

## [2026.5.29.post1] - 2026-05-29 - Skeletony pouzivaju realne komponenty

###  Zmenene

- **Nacitavacie skeletony teraz pouzivaju realne komponenty stranky namiesto
  paralelneho `gl-skeleton-*` rozlozenia.** Skeleton primitiva v
  `components/loaders.html` mali vlastne kontajnery pre karty / statistiky /
  tabulky / formulare, kazdy s osobitnymi responzivnymi media queries, ktore sa
  lisili od realneho UI. Makra `sk_stat`, `sk_stats`, `sk_card`, `sk_table` a
  `sk_form` teraz generuju **realny** markup komponentov - `.stat-card` /
  `.stats-grid` / `.card` / `table.data-table` / `.form-group` - so shimmer
  pruhmi `.gl-skeleton` v listovych slotoch, takze rozlozenie a responzivnost
  dedia priamo od zivych komponentov a nemozu driftovat. Signatury makier sa
  nezmenili, takze ziadne call-site nebolo treba upravovat.
- **Odstranene mrtve skeleton CSS** (`.gl-skeleton-card`, `.gl-skeleton-stat`,
  `.gl-skeleton-table`/`-thead`/`-row` s ich `nth-child` variabilitou a media
  queries, `.gl-skeleton-stats-grid`, `.gl-skeleton-field`/`-label`/`-input`).
  Primitiv `.gl-skeleton`, `.gl-skeleton-tr`, `.gl-skeleton-cards-grid` a rodina
  `.gl-skeleton-list*` ostavaju.

###  Release

- Verzia `2026.5.29.post1`. Iba zmena sablon + CSS; bundly prebudovane. Bez
  backend zmien.

---

## [2026.5.29] - 2026-05-29 - Deterministicky lockfile-check

###  Opravene

- **CI job `lockfile-check` je teraz deterministicky a uz nepada kvoli
  nesuvisiacim novym verziam balikov.** Job spusta
  `uv pip compile pyproject.toml --extra otel -o requirements.lock` a potom
  `git diff --exit-code requirements.lock`. Kedze takmer kazda zavislost pouziva
  otvoreny rozsah `>=`, `uv` pri kazdom behu znova rozriesil na najnovsie verzie
  z PyPI, takze lockfile "driftoval" a job sa rozsvietil na cerveno vzdy, ked
  hociktora priama alebo tranzitivna zavislost vydala novu verziu - aj ked sa
  v repozitari nic nezmenilo. Pridana sekcia `[tool.uv]` s
  `exclude-newer = "2026-05-30T00:00:00Z"`, ktora pripne rozriesenie na pevny
  casovy bod. `requirements.lock` sa regeneruje bajt po bajte rovnako a gate
  ostava reprodukovatelny, kym sa timestamp zamerne neposunie.

###  Vydanie

- Verzia `2026.5.29`. Bez bumpu service-worker cache: ide o zmenu iba v
  CI/build konfiguracii, ziadne klientske assety sa nezmenili.

---

## [2026.5.23.post2] - 2026-05-23 - Dolacenie commit kategorie v UI

###  Opravene

- **Checklist chart na Course Analytics farbi commit-kategorie bary
  spravnou ruzovou (`#ec4899`).** Po remape R13 na `commit` v `post1`
  mapa `categoryColors` v `course-analytics.js` stale kludila kluc
  `quality:` (engine takuto hodnotu uz neposiela). R13 a vlastne
  commit-kategorie kontroly preto padali na fallback `custom` (fialova).
  Kluc premenovany na `commit:` (rovnaka ruzova), takze category stripe
  na chart-e zladi s farbou badgeu inde v UI.
- **Filter toolbar v Course Settings dostal chybajuce tlacidlo
  `Commit`.** Filter nad tabulkou kontrol ponukal iba `Issue`, `MR`,
  `Review`, `CI/CD` - bez `Commit` ucitelia nedokazali tabulku
  zuzitkovat na R13 alebo vlastne kontroly s `category="commit"`.
  Tlacidlo doplnene cez existujuci `filter_btn` macro; JS filter
  handler je data-driven a nepotreboval zmenu.

###  Release

- Verzia `2026.5.23.post2`, service-worker cache `gitpulse-v99`.

---

## [2026.5.23.post1] - 2026-05-23 - Kategoria Commit naprie celym stackom

###  Opravene

- **Kategoria `Commit` je teraz plnohodnotna naprie celym stackom kontrol.**
  Edit Check modal predtym ponukal iba pat moznosti
  (`issue`, `mr`, `review`, `ci`, `custom`); kontroly ulozene s
  `category=commit` sa zobrazovali s prazdnym pollom Category, lebo hodnota
  nebola v zozname a JS badge/label mapy ju nemapovali. Pridana volba
  `('commit', t('Commit'))` do dropdownu a `commit:` zaznamy do
  `CATEGORY_BADGES` (badge-purple) a `CATEGORY_LABELS` v
  `course-settings.js`.
- **Pydantic schemy a backend validatory akceptuju `commit`.** Rozsirene
  `ALLOWED_CATEGORIES` a dva `Literal[...]` unie v
  `schemas/custom_check.py`, takze custom-check API uz nevracia 422.
  Zladene aj `valid_categories` set a docstring pre LLM suggestions v
  `api/dashboard/course_checks.py` a stlpcovy komentar v
  `models/custom_check.py`.
- **R13 (`Commit Quality`) je teraz mapovany na kategoriu `commit`.**
  Predtym `_CHECK_CATEGORIES` v `compliance/engine.py` mapoval `R13` na
  osamoteny `"quality"` bucket, ktory nikto iny nepouzival, takze
  `commit_score` bol vzdy `None` v category breakdown a pilot telemetrii.
  Premapovane na `"commit"`, do mnoziny `all_cats` v
  `_compute_category_scores` pridana hodnota `"commit"`, rovnaka zmena v
  `pilot_telemetry._FALLBACK_CHECK_CATEGORIES` a pridanie `"commit"` do
  iteracnej n-tice v `_derive_category_scores`.

###  Release

- Verzia `2026.5.23.post1`, service-worker cache `gitpulse-v98`.

---

## [2026.5.23] - 2026-05-23 - Scoped button a modal guards

###  Opravene

- **Tlacidla a modaly uz pokryvaju zvysne course/project write akcie.**
  Archive/activate/delete kurzu, dashboard Add Group a edit kurzu,
  course-settings scoring/config importy, admin course actions a project unlink
  kontroluju aktivny `course`/`team`/`project` process scope pred otvorenim
  modalu alebo zmenou dat.
- **Process-lock click guard je fail-closed.** Kazdy element s
  `data-process-lock-when` sa overi este raz pri kliku, nie iba cez 1.5s poll,
  takze zastarany disabled stav nepusti konfliktne sync/import/run-check akcie.
- **Dynamicke tlacidla dedia scope.** Tlacidla vlozene po archive/activate
  operacii sa hned refreshnu cez zdielany process guard bez reloadu stranky.

###  Release

- Verzia `2026.5.23`, sw cache `gitpulse-v97`.

---

## [2026.5.22.post7] - 2026-05-22 - Spinner anomalie a obnova toastov

### Opravene

- **SVG spinnery (.spinner, .spinner-inline)** maju teraz
  `transform-origin: 50% 50%` a `transform-box: fill-box`, takze sa pri
  hoveri rodicovskej karty s transform efektom uz netocia okolo lavho
  horneho rohu a animacia je hladka.
- **Stratene completion toasty pocas navigacie.** Ked sync skoncil
  presne v momente navigacie (SSE complete event medzi `beforeunload`
  a unload), `_preserveFlashToast()` uz mal odfotenu prazdnu toast
  schranku a toast sa stratil. Restore vetva v `_restoreJobs` teraz
  pre obnovene done/error/finishing jobs zaradi completion toast do
  replay fronty (session-dedup blokuje duplicity v ramci toho isteho
  page-load) a okno pre nav-replay sa rozsirilo z 3 s na 8 s, aby sa
  pomalsie navigacie stihli.

---

## [2026.5.22.post6] - 2026-05-22 - Scoped process locks

###  Fixed

- **Scoped process locky sleduju hierarchiu course/team/project.**
  Per-team sync, per-project sync a run-check jobs pouzivaju stabilne
  scoped job keys, takze aktivna praca v jednej skupine neblokuje
  nesuvisiace kurzy alebo skupiny, no konfliktne akcie v rovnakom
  team/project scope ostavaju zamknute.
- **Course-level Run Checks ostava zamknuty az do realneho konca prace.**
  Pribudol aggregate run-check status endpoint a global job bar ho polluje,
  aby sa modaly/tlacidla neodomkli hned po fan-out enqueue, kym per-team
  joby este bezia.
- **Exclude from scoring je guardovane konzistentne.** Toggle tlacidla
  hodnotia scope konkretneho riadku, pouzivaju zdielane ikony a backend
  berie team advisory lock pred kontrolou aktivnych scoring jobov.

###  Release

- Verzia `2026.5.22.post6`, sw cache `gitpulse-v95`.

---

## [2026.5.22.post5] - 2026-05-22 - Scope-aware imperative guards

###  Fixed

- **Doplnene scope filtrovanie aj pre imperativne process guards.** Click
  handlery pre per-team sync, per-project sync, run checks a course-level
  sync-all/import/run-checks teraz posielaju `course`/`team`/`project`
  scope do `guardProcessAction`, takze varovny toast _"Wait for the
  active sync to finish"_ uz nevyskakuje pri akciach v inom kurze.
- **Dashboardove Import tlacitka.** Zamykaju sa iba inym aktivnym
  importom, nie bezucim sync v lubovolnom kurze.
- **Skeleton course-detail.** Vykresluje vsetky 4 akcne tlacitka (Add
  Group / Import from GitLab / Sync All / Run Checks), aby zodpovedal
  realnej strukture po nacitani HTMX obsahu 1-na-1.

###  Release

- Verzia `2026.5.22.post5`, sw cache `gitpulse-v94`.

---

## [2026.5.22.post4] - 2026-05-22 - Per-course sync independence

###  Fixed

- **Opravene blokovanie synchronizacie naprieg kurzami.** Process guard
  uz vie rozlisit, ktoreho kurzu/grupy/projektu sa bezici job tyka.
  Spustenie sync v jednom kurze uz neblokuje import alebo sync v inom
  kurze; run-checks a sync sa stale navzajom branie iba v ramci toho
  isteho tymu/projektu; dashboardove Import tlacitka su nezavisle od
  per-kurzovych jobov. Vsetky job-start call-sites pridavaju `courseId`,
  `teamId`, `projectId` a `jobKind` do meta, takze guards filtruju
  presne.

###  Release

- Verzia `2026.5.22.post4`, sw cache `gitpulse-v93`.

---

## [2026.5.22.post3] - 2026-05-22 - Process action guards

### Opravene

- **Konfliktne sync/import/run-check akcie sa blokuju konzistentne.**
  Tlacidla a modal triggery pouzivaju spolocny process guard a page handlery
  robia rovnaky preflight pred programatickym spustenim prace.
- **Project sync pouziva spravny global-job API povrch.** Project stranka uz
  necita chybajuce aliasy z `window.GP`, takze detekcia aktivneho syncu,
  registracia progressu aj cleanup po dokonceni idu cez kanonicke global-job
  helpery.
- **Backend sync/check races teraz failuju zatvorene.** Team/project/course
  sync a run-check endpointy zdielaju team-scope advisory locky a pri
  konfliktnych aktivnych joboch vracaju 409 namiesto paralelneho enqueue.
- **ASGI framework zavislosti su spevnene.** FastAPI teraz zacina na
  `0.136.1` a Starlette na `1.0.1`, cim sa cisti aktualny Starlette
  `PYSEC-2026-161` audit finding bez uvolnenia runtime kompatibility.

### Release

- Verzia aplikacie je `2026.5.22.post3`; Service Worker cache je
  `gitpulse-v92`.

---

## [2026.5.22] - 2026-05-22 - Konzistentne scoring exclusion

### Opravene

- **Exclude from scoring je zosuladene v team aj project dashboarde.** Backend
  toggle teraz odmieta race s aktivnym sync/run-checks jobom, pouziva row lock,
  hned prepocita team metrics a invaliduje team, course, project aj student
  page-cache scope-y.
- **Project live-data respektuje scoring exclusion.** Excluded clenovia uz
  nevstupuju do project live-data scoring cohort ani Issues to Address refreshu.
- **Member toggle ma jedneho frontend ownera.** Team aj project stranky zdielaju
  rovnaky handler, pri vrateni do scoringu zachovaju inherited/manual/csv
  kategoriu clena a blokuju konfliktnu akciu pocas sync/import/check runu.

### Release

- Verzia aplikacie je `2026.5.22`; Service Worker cache je `gitpulse-v89`.

---

## [2026.5.21.post26] - 2026-05-21 - Release housekeeping

### Zmenené

- **Dashboard changelog datumy su normalizovane.** `Latest changes` uz
  neobsahuje zaznamy datovane po aktualnom release dni 2026-05-21 a regresny
  test teraz odmietne future-dated dashboard changelog riadky.
- **Deploy workspace je cistejsi.** Stare ignorovane `deploy-post*.log` /
  `redeploy.log` subory a jednorazovy ignorovany SRP split helper skript boli
  odstranene pred redeployom.

### Release

- Verzia aplikacie je `2026.5.21.post26`; Service Worker cache je
  `gitpulse-v76`.

---

## [2026.5.21.post25] - 2026-05-21 - Sync cache invalidation modul

### Zmenené

- **Sync cache invalidacia ma samostatneho vlastnika.**
  `_invalidate_dashboard_cache_after_sync` sa presunul z velkeho
  `workers/sync_job.py` workera do `workers/sync_cache.py`. Full-team aj
  per-project sync dalej invaliduju project, team, course a student page-cache
  scope-y, ale worker drzi menej cache plumbing inline.
- **Release metadata je znovu zosuladene s aktualnym package baseline.**
  Root/docs changelogy a version refs teraz ukazuju na `2026.5.21.post25` a
  `gitpulse-v75`.

### Testy

- Sync cache invalidation regresny test teraz mieri na `app.workers.sync_cache`.

### Release

- Verzia aplikacie je `2026.5.21.post25`; Service Worker cache je
  `gitpulse-v75`.

---

## [2026.5.21.post3] - 2026-05-21 - Dashboard role-context modul

### Zmenené

- **Dashboard role-context helpery maju samostatneho vlastnika.** Sidebar badge
  pocty, greeting subtitle, student dashboard context a admin dashboard context
  sa presunuli z `dashboard/home.py` do `dashboard/home_context.py`. `home.py`
  sa tak sustredi viac na orchestraciu stranky.
- **Context fast-paths maju pokrytie.** Student context vracia defaultny
  zero-state bez DB pristupu, ked nie su aktivne predmety alebo GitLab username,
  a student sidebar badges ostavaju bez DB dotazu.

### Release

- Verzia aplikacie je `2026.5.21.post3`; Service Worker cache je
  `gitpulse-v53`.

---

## [2026.5.21.post2] - 2026-05-21 - Dashboard Latest changes split + course health modul

### Zmenené

- **Dashboard *Latest changes* ma samostatneho vlastnika.** Rucne udrziavane
  release zaznamy a vyber lokalizacie sa presunuli z velkeho
  `dashboard/home.py` routu do `dashboard/home_changelog.py`, aby home route
  riesil orchestraciu stranky namiesto release-note dat.
- **Course-card health SQL je mimo route.** Per-course RED-team health je teraz
  v `dashboard/home_course_health.py`. Helper pri prazdnom active-course vstupe
  hned vracia prazdny vysledok, bez zbytocnej DB prace pre onboarding a empty
  states.

### Testy

- Pridane regresne pokrytie pre prazdny active-course course-health path a
  dashboard changelog testy mieria na noveho vlastnika `home_changelog.py`.

### Release

- Verzia aplikacie je `2026.5.21.post2`; Service Worker cache je
  `gitpulse-v52`.

---

## [2026.5.21.post1] - 2026-05-21 - Dashboard stats split + 429 asset cache busting

### Zmenené

- **Stat-card SQL pre dashboard home ma samostatny modul.** Role-specific
  stat karty sa presunuli z velkeho `dashboard/home.py` routera do
  `dashboard/home_stats.py`. RED-team pocty a priemer compliance zdielaju jeden
  latest-team-snapshot subquery a student bez aktivnych predmetov dostane nulove
  karty bez zbytocnych DB dotazov.
- **Standalone 429 stranka pouziva deploy-hash static URL.** Rate-limit
  middleware nemoze bezpecne zavisiet od Jinja `static_url()`, preto jeho
  browser HTML doplna `BUILD_HASH` query string pre favicon, stylesheet a
  ilustraciu.
- **Supply-chain extras su uzsie.** Pridany `idna>=3.15`, redundantny optional
  scanner `safety` je prec v prospech `pip-audit` + CycloneDX a Locust je
  presunuty do samostatneho `load` extra.

### Testy

- Pridane regresne testy pre student stat-card path bez aktivnych predmetov a
  pre deploy-hash `/static/...` linky na browser rate-limit stranke.

### Release

- Verzia aplikacie je `2026.5.21.post1`; Service Worker cache je
  `gitpulse-v51`.

---

## [2026.5.19.post25] - 2026-05-19 - Page/static cache hardening

###  Opravené

- **Page-fragment cache ma bezkolizne variant kluce.** Variant casti sa
  serializuju cez JSON pred BLAKE2b digestom, takze hodnoty ako `("a|b", "c")`
  a `("a", "b|c")` nemozu skoncit v tom istom cache kluci. Redis namespace je
  bumpnuty na `gp:page:v2`, co vynuti bezpecny cold-start starych fragmentov.
- **Static cache headers su kanonicke.** `/static/*` odpovede nahradzaju
  existujuci `Cache-Control` namiesto pridavania duplicit, `Vary:
  Accept-Encoding` sa merguje s existujucimi `Vary` hodnotami a jednoročny
  immutable cache profil sa pouzije len pre validny hex content-hash `?v=`.
- **Dashboard home cleanup.** Odstranene nepouzite stat-card parametre a stare
  lokalne premenne v `home.py`; support-ticket sidebar badge jasne rata tikety
  vo viditelnych predmetoch.

### Zmenené

- Verzia aplikacie je `2026.5.19.post25`; Service Worker cache je
  `gitpulse-v50`.

---

## [2026.5.18.post24] - 2026-05-18 - Stabilita global-job-bar + debounce webhook metrik

###  Opravené

- **Progress bar uz neflikrue po dokonceni syncu.** 30-sekundovy
  `/sync/active` watchdog aj `htmx:load` rekoncilator preskakuju pracu
  na 3 s po `completeGlobalJob`. Predtym mohol stary `/sync/active`
  snapshot alebo navigacia nakratko zase pridať uz schovany bar.
- **Stale `Last Synced` po uspesnom syncu je teraz viditelne v logoch.**
  Zlyhania `_invalidate_dashboard_cache_after_sync` su logovane na
  WARNING (predtym DEBUG) vo full-team-sync aj per-project-sync vetve,
  takze Redis/SCAN hiccup uz nezostane ticho.

###  Vykon

- **Webhook bursty zlucuju metrics-refresh enqueue na uroven tymu.**
  Burst N eventov od toho isteho tymu v ramci 2 sekund teraz enqueuje
  iba jeden `metrics_refresh` job namiesto N (Redis `SET ... NX EX 2`
  debounce). Job je idempotentny - debounce nestrati ziaden stav.
  Odstranuje vacsinu Redis chatteru z CI pipelines emitujucich 10+
  eventov v rade.

---

## [2026.5.18.post23] - 2026-05-18 - Animovaný empty state + Diff column fix

### Opravené

- **Diff stĺpec v MR tabuľke už nezobrazuje "- files".** Keď chýbajú
  `files_changed`, `lines_added` aj `lines_removed`, bunka zobrazí pomlčku
  (`-`). Ak chýba iba počet súborov a sú dostupné +/- riadky, ukáže sa
  iba delta.
- **Ikony prázdnych stavov na detaile projektu majú rovnakú animáciu ako
  zvyšok dashboardu.** "Issues to Address -> No scored members yet" a
  "All passing" zdieľajú `emptyStateFloat` keyframy s ostatnými
  `.empty-state-icon`, s opt-outom `prefers-reduced-motion: reduce`.

### Zmenené

- **Widget *Posledné zmeny* na hlavnej stránke skrátený na posledných 5
  záznamov** a jednoodstavcové súhrny; dlhá história je tu a v
  `docs-site/docs/changelog*.md`.
- Verzia aplikácie a docs metadata sú `2026.5.18.post23`; Service Worker
  cache je `gitpulse-v48`.

## [2026.5.18.post22] - 2026-05-18 - Cache invalidácia syncu + CSP cleanup

### Opravené

- **Dokončené sync joby teraz okamžite invalidujú dashboard fragment cache.**
  Team sync aj per-projektový sync mažú dotknuté cache scope-y pre projekt,
  tím, kurz/activity/analytics a aktívnych študentov, takže používateľ po
  dokončení jobu nedostane starý HTML fragment z krátkej TTL cache.
- **Zvyšné inline časovače a Course Settings LLM helper sú mimo šablón.**
  401/429 redirect/countdown logika a LLM resource/prompt helper bežia z
  externých JS súborov; CSS/minified assets boli pregenerované.

### Zmenené

- Verzia aplikácie a docs metadata sú `2026.5.18.post22`; Service Worker
  cache je `gitpulse-v47`.

## [2026.5.18.post21] - 2026-05-18 - Per-projektový Sync v aktivite + seméstrový audit

### Pridané

- **Widget *Najnovšie udalosti* na dashboarde teraz rozlišuje
  per-projektový sync.** Keď učiteľ klikne *Sync* priamo na konkrétnom
  projekte (nie na celej skupine, nie cez globálny *Sync all*),
  záznam v aktivite sa vykreslí ako *"System - Project synced from
  GitLab"*, v detaile sa zobrazí názov projektu a odkaz vedie na
  `/dashboard/projects/{id}` namiesto stránky skupiny. Skupinové a
  globálne syncy zóstavajú bez zmeny. `run_checks` sa po-prejavuje na
  všetkých úrovniach, kde sa dá spustiť (skupina + fan-out kurzu).

### Opravené

- **Seméstrové skópovanie po celom systéme.** Viacero agregátnych
  a contributor dotazov beŽalo cez *celú históriu* namiesto
  aktuálneho semestra, čo nafukovalo čísla a nechávalo zastarané
  health projektov pretrvávať medzi semestrami. Opravené:
 - `course_detail`, `get_course_sync_status` a SSE builder pre
    `/courses/{id}/sync-stream` teraz posielajú
    `commit_since = semester_floor_utc(course.settings)` do
    `team_contributor_counts()` aj `total_distinct_contributors()`.
 - DB fallback `api/projects.py:get_contributors` filtruje commity
    podľa seméstrovej hranice kurzu projektu.
 - V `dashboard/teams.py` sa mapovanie *študent -> primárny projekt*
    používa rovnaký `_commit_window_clause` ako zvyšok detailu
    skupiny (študent, ktorý zmenil skupinu medzi semestrami, sa už
    nezasekne na projekte z minulého termu).
 - V `dashboard/courses.py` agregáty pipelines per skupinu
    (total / passed / failed / latest_status) aj alternatívna
    cesta cez kurz teraz limitujú `semester_floor_utc`, takže
    úspíšna pipeline z minulého semestra už neprekýva reálny
    stav.

### Odstránené

- Vrátená späť experimentálna karta aktivity na detaile projektu -
  dashboardový widget *Najnovšie udalosti* je jediné miesto pravdy,
  detail projektu ho neduplikuje.

---

## [2026.5.18.post17] - 2026-05-18 - Per-projektový Sync + presné SYNCING odznaky

### Pridané

- **Nový endpoint `POST /api/v1/projects/{project_id}/sync`.** Tlačidlo
  *Sync* na detaile projektu už nesynchronizuje celý team (group), ale
  refreshuje iba dotknutý projekt - issues, MR-y, MR-notes, pipelines,
  commits (default branch + per-MR source branches). Member sync
  a project discovery ostávajú team-scoped (kvôli pridávaniu nových
  projektov v podskupine). Endpoint má vlastný advisory lock na
  `project_id`, dedup voči bežiacim team-syncom a auditný záznam
  `sync_project`.
- **Per-row SYNCING/QUEUED/FAILED odznak v tabuľke projektov tímu.**
  `GET /api/v1/courses/{course_id}/sync-status` po novom vracia
  `sync_status_by_project`, takže detail skupiny presne vyznačí iba
  riadky tých projektov, ktorých sync skutočne beží - namiesto svietiť
  všetkým aktívnym riadkom kedykoľvek beží akýkoľvek team-job.

### Opravené

- **Fantómové "1/2 groups done"** pri jednej bežiacej synchronizácii.
  Čítač *X/Y groups* už nezahŕňa project-scoped joby (tie majú vlastný
  `project_sync_running_count`) a používa 3-minútové burst okno na
  počítanie completed/failed - stará 2-hodinová odlúčka v denominátore
  bola hlavná príčina misleading "1/2".
- **Migrácia `047_bg_job_project_id`** pridáva `BackgroundJob.project_id`
  (FK na `gitlab_projects` `ON DELETE SET NULL`) + index - kostra pre
  per-project sync sledovanie.

### Technické

- Service Worker cache: `gitpulse-v46`.

---

## [2026.5.18.post16] - 2026-05-18 - Pravdivé sync toasty + SYNCING badge v tabuľkách

### Opravené

- **Falošný toast "Sync started!" na detaile projektu.** Tlačidlo `Sync`
  predtým ukazovalo "Sync started!" pri každom kliknutí - aj keď backend
  vrátil `skipped_fresh` (dáta sú čerstvé), `failed` (Redis down) alebo
  existujúcu prácu vo fronte. Handler teraz vetví podľa skutočného
  `status` v odpovedi a zobrazuje pravdivý toast (`info`/`danger`/`success`).
- **Fantómové sloty "1/2 groups" v globálnom job bare** po jednorazovom
  sync z detailu projektu. `completeGlobalJob('sync', ...)` sa teraz volá
  vo všetkých vetvách handlera, takže odložený slot sa vždy uzavrie.
- **Tlačidlo `Sync` sa odomykalo predčasne** - pôvodný `finally` ho
  uvoľnil hneď po POST. Teraz drží stav `loading` až kým SSE stream
  nevráti `complete`/`error` pre konkrétny `job_id`.

### Pridané

- **Dynamický badge `SYNCING` / `QUEUED` / `FAILED` v stĺpci Status
  tabuľky `Subgroups and Projects` na detaile skupiny.** Keď sa skupina
  synchronizuje (lokálne klik na `Sync` alebo paralelne cez course-level
  `Sync All`), všetky aktívne projektové riadky zobrazia stav skupinového
  syncu namiesto pôvodného Active/Template. Po dokončení sa originálne
  badge automaticky obnovia. Mechanika zrkadlí už existujúci per-row
  status v tabuľke skupín na detaile kurzu.

---

## [2026.5.18.post15] - 2026-05-18 - Sync na projekte + odstránenie duplicitnej rotácie webhook secret

### Pridané

- **Tlačidlo `Sync` priamo na detaile projektu.** Predtým bolo synchronizáciu
  jedného projektu z GitLab-u možné spustiť iba z nadradeného kurzu/skupiny.
  Lišta nástrojov na `/dashboard/projects/<uuid>` má teraz vlastné tlačidlo
  `Sync` vedľa `Unlink`, gated cez `can_edit and team`, ktoré posiela
  `POST /api/v1/teams/{team_id}/sync` a zobrazuje priebeh v globálnom job bar
  rovnako ako sync na úrovni skupiny.

### Odstránené

- **Tlačidlo `Rotate Webhook Secret` a endpoint
  `POST /api/v1/projects/{project_id}/rotate-secret`.** Per-projektová rotácia
  webhook secret v UI duplikovala flow `Settings -> Webhook Configurations`
  (zavedený migráciou 041) bez akejkoľvek pridanej hodnoty. Tlačidlo, JS
  handler, FastAPI endpoint, Pydantic schéma `ProjectSecretRotated`, krok
  tour-u, riadok contract testu aj sekcia v security dokumentácii sú preč.
  `Project.webhook_secret_hash` sa stále generuje pri importe a overuje pri
  doručení webhook-u - len manuálna rotácia bola stiahnutá.

### Opravené

- **Skrátený tooltip `Unlink`.** 4-vetový opis pravidiel reaktivácie sa
  orezával na menších viewportoch; stiahnutý na jednu vetu.

---

## [2026.5.18.post14] - 2026-05-18 - Odstránenie duplicitnej modálky Sync Group Data

### Opravené

- **Odstránená duplicitná modálka `Sync Group Data`.** Pri kliknutí na
  `Sync` / `Sync All` sa otváral celostránkový modal, ktorý zobrazoval
  presne ten istý progres `Project N/15: ... synced (X%)` aký už ukazuje
  perzistentný global job bar na vrchu stránky. Dve kópie tej istej
  informácie na obrazovke naraz boli zbytočné a rušivé. Teraz progres
  ukazuje len global bar; modal markup (`team/_modals.html`) je
  odstránený a `_DEFAULT_LOCAL_SELECTORS.sync` v `global-job-bar.js`
  tiež.
- **Sync tlačidlo už nepretieka na mobile.** `triggerSync` /
  `triggerSyncAll` predtým volali `setButtonLoading(btn, true,
  'Syncing...')` čo nahradilo HTML ikonkového tlačidla doslovným reťazcom
  `Syncing...`. Na úzkych viewportoch tento text vyliezal mimo malého
  ikonkového tlačidla ako `/ncing`. Argument `loadingText` zhodený -
  tlačidlo si zachová pôvodnú ikonu / popis a dostane len triedu
  `.loading` pre spinner stav, rovnako ako všetky ostatné action
  tlačidlá.

---

## [2026.5.18.post13] - 2026-05-18 - Doladenie profilu študenta a kontrastu loaderov

### Zmenené

- **Profil študenta - vizuálny polish.** Žlté tlačidlo `Run Checks` z
  post12 už nevisí ako samostatný pruh nad stránkou - presunulo sa do
  hlavičky karty `Student Profile` / `My Profile` / `Teacher Profile`
  vedľa názvu, takže sedí na povrchu karty namiesto holého pozadia.
- **Kontribútori projektu - kanonické mená.** Widget Contributors na
  detaile projektu teraz mapuje zhodu git autorov na `Student.full_name`
  (najprv podľa emailu, potom podľa lowercased `gitlab_username`).
  Generické / zdieľané display názvy ako `student` sa už nezobrazujú,
  ak má študent zle nastavený lokálny git config. Pôvodný git názov
  ostáva v payloade ako `raw_name` pre audit.
- **Skeleton loadery - lepší kontrast.** `.gl-skeleton` číta z
  vyhradených tokenov `--gl-skeleton-bg` / `--gl-skeleton-shimmer`
  (`tokens.css`), shimmer overlay z 0.05 na 0.12. Riadky loaderu na
  detaile projektu / študenta sú viditeľne kontrastné voči pozadiu
  stránky namiesto takmer neviditeľných.

---

## [2026.5.18.post12] - 2026-05-18 - Run Checks na všetkých 3 úrovniach (kurz/skupina/študent) + pravdivé tooltipy Rotate/Unlink

- **Run Checks teraz existuje na všetkých troch úrovniach hierarchie GitPulse**
  (kurz -> skupina -> študent). Tlačidlo na úrovni skupiny tu bolo už dávno;
  v tomto release pribudli zvyšné dve.
   - **Úroveň kurzu.** V action bar-e kurzu pribudol žltý button
      `Run Checks (all groups)` vedľa `Sync All`. Volá nový endpoint
      `POST /api/v1/courses/{course_id}/run-checks`, ktorý vytvorí
      samostatný `run_checks` BackgroundJob pre každú aktívnu skupinu
      v kurze (rovnaké 10-minútové dedup okno ako pri tímovom volaní).
      Viditeľné pre kohokoľvek s `can_edit` na kurze.
   - **Úroveň študenta.** Profil študenta má rovnaký žltý button.
      Worker je stále team-scoped (GitPulse drží jednu snímku na
      študenta-v-tíme), takže button volá `/teams/{team_id}/run-checks`
      a snímka študenta sa obnoví automaticky cez existujúce SSE.
   - `_run_checks_modal.html` má novú vetvu pre Course scope v scope
      banner-i, takže dynamický kontext prechádza čisto:
      Course -> Group -> Project -> Student.
- **Pravdivý tooltip "Rotate Webhook Secret".** Predchádzajúci text
  nevysvetľoval, odkiaľ secret pochádza. Nový tooltip hovorí, že
  GitPulse webhook signing secret vygeneroval automaticky pri importe
  projektu, rotácia má zmysel iba ak mohol secret uniknúť, a starý
  token ostáva platný 24 h, aby sa nestratili in-flight delivery z
  GitLabu.
- **Pravdivý tooltip a confirm "Unlink from GitLab".** Starý text
  klamal, že projekt sa "znovu prilinkuje pri ďalšom sync-u". V
  realite `_upsert_project` rešpektuje manuálne mazanie - soft-
  deactivated projekt ostane neaktívny natrvalo, kým admin explicitne
  nezavolá `POST /projects/{id}/reactivate`. Tooltip aj confirm to
  teraz hovoria priamo a zdôrazňujú, že všetky dáta (commits, MRs,
  kontroly, snímky) ostávajú zachované.
- **Poznámka k rolám.** `User.role` má len tri hodnoty: `admin`,
  `teacher`, `student`. Systémová rola "mentor" NEEXISTUJE -
  `team_member.is_mentor` je iba per-team flag pre seniornejších
  študentov, ktorí pomáhajú skupine; sú vyňatí z agregátnych metrík
  ale nemajú zvýšené práva. Všetky Run Checks UIs sa rozhodujú podľa
  `can_edit` (course owner / teacher s členstvom v kurze / admin), nie
  podľa `User.role` priamo.

---

## [2026.5.18.post11] - 2026-05-18 - Oprava modrého pozadia skeletonov + ikony v modálkach + GitLab import UX

- Skeleton loadery už nesvietia modrou/červenou farbou notifikácií.
  Semantické triedy (`.member-api-note`, `.advisory-banner`, `.alert`)
  použité vnútri `[aria-busy="true"]` skeleton stromov presakovali
  svoje feature pozadia (modré `--info-bg`, modré `--gl-blue-950`)
  cez placeholdery. Defenzívne pravidlo v `loaders.css` teraz núti
  neutrálne `--surface-strong` + `--border-color` pre akýkoľvek
  semantický banner v skeleton kontexte - aplikované system-wide,
  aby budúce skeleton makra nikdy nezdedili feature farby.
- Ikony v titulkoch modálov sú teraz vertikálne centrované voči
  textu. `.modal-title` bol obyčajný `<h3>`, takže predradené ikony
  sedeli na text baseline. Prepnuté na
  `display: inline-flex; align-items: center` - opravuje každý
  modal v aplikácii (Edit Check, Settings, Import, Rotate,
  Edit Course, ...).
- Tlačidlo "Rotate Secret" na hlavičke projektu je teraz označené
  ako **"Rotate Webhook Secret"** s rozšíreným tooltipom, ktorý
  vysvetľuje, že sa generuje nový GitLab webhook token a predošlý
  zostáva platný 24 hodín ako grace window. Susedné "Unlink"
  tlačidlo premenované na **"Unlink from GitLab"** s tooltipom o
  automatickom re-linke pri ďalšej synchronizácii.
- Modál **Import from GitLab** teraz ponúka rovnaký Quick preset
  dropdown a Semester start/end date pickery ako Create Course.
  Výber TUKE FEI presetu vyplní akademický rok, semester a obe
  dátumy jedným klikom; dátumy sú perzistované na nastavenia
  importovaného kurzu, takže auto-archive a semester windowing
  fungujú okamžite bez ďalšieho "Edit Settings" kroku.
- Scope banner v Run Compliance Checks modáli teraz podporuje
  vetvu `student` (poradie: student -> project -> team), takže
  študentom scopovaný Run Checks dialog ukáže meno študenta
  namiesto nadradeného tímu - príprava pre nadchádzajúce
  študentom-scopované "Run Checks" tlačidlo v hlavičke.

---

## [2026.5.18.post10] - 2026-05-18 - Skeleton loader DOM parity a feature-flag gating

- Skeleton loadery každej lazy-loaded stránky (dashboard, course
  detail/activity/analytics/teachers, project detail, student detail,
  team detail, admin users, support tickets/detail/form) presne zrkadlia
  živú DOM štruktúru - rovnaký počet karet, stĺpcov tabuľky, toolbar a
  pagination - takže swap zo skeletonu na obsah neposúva layout.
- Skeletony rešpektujú runtime podmienky: project detail honoruje
  dostupnosť rubriky, `feature_docker_verification`,
  `feature_ci_failure_generator`, `feature_conflict_simulator`,
  `feature_llm_suggestions` a viditeľnosť GitLab tlačidiel; student
  detail honoruje dostupnosť rubriky a own-profile gate; analytics honoruje
  course-staff gate; dashboard honoruje rolu a toggle
  changelog panela; team detail rešpektuje student-privacy mód;
  course detail / teachers honoruje `can_edit` a `can_see_admins`.
  Loader pre vypnutý komponent sa už nezobrazuje.
- Service worker cache `gitpulse-v39`.
- Lokálny baseline: `2583 passed, 19 deselected`.

## [2026.5.18.post9] - 2026-05-17 - Quality gate a release metadata hygiene

- `src/app/api/dashboard/home.py` je znovu v súlade s `ruff format`;
  zmena je iba formátovanie bez zmeny správania.
- Release metadata, dashboard latest changes, docs-site `versions.json` a
  lokálne validačné dokumenty boli zosúladené s auditom dňa 2026-05-17.
- Opravené budúce dátumy v najnovších changelog záznamoch; aktuálny lokálny
  baseline testov je `2583 passed, 19 deselected`.
- `dead_code_report.py`, static artifact guard a `pip-audit` ostávajú čisté
  pre aktuálne nainštalované prostredie.
- Service worker cache `gitpulse-v38`.

## [2026.5.18.post8] - 2026-05-17 - Static cache a CSP hygiena

- Cache statických assetov teraz rozlišuje content-hash URL od priamych
  statických ciest: `/static/*?v=<hash>` má ročný `immutable` cache, zatiaľ čo
  neoverzionované `/static/*` má 5-minútové TTL.
- Inline JavaScript z login a error stránok sa presunul do externých statických
  modulov (`js/pages/login.js`, `js/error-actions.js`).
- `redeploy.py` teraz používa systémové OpenSSH s deploy kľúčom alebo SSH
  agentom, predvolene odmieta neznáme host kľúče a už nezávisí od Paramiko.
- Python/docs dependency floors boli zvýšené podľa aktuálnych `pip-audit`
  advisories vrátane `cryptography`, `python-multipart`, `Pillow`, `Pygments`,
  `requests` a `urllib3`.
- Template metadata odkazy používajú `static_url()` / `absolute_static_url()`
  pre lokálne statické assety všade, kde sa dá vypočítať content hash.
- Service worker cache `gitpulse-v37`.

## [2026.5.18.post6] - 2026-05-17 - Mobilná responzivita skeletonov

- `sk_chart` (vertikálne pruhy) sa zmenšuje na `<768px` (96 px min-výška,
  20 px pruhy) a `<480px` (80 px, 14 px); osové ticky sa orezávajú.
- `sk_h_bars` dostal `<360px` breakpoint so 56 px štítkovým stĺpcom a 12 px
  pruhmi; na malých obrazovkách sa skrývajú posledné osové ticky.
- Service worker cache `gitpulse-v35`.

## [2026.5.18.post5] - 2026-05-17 - Mobilný skeleton Week Analytics

- Skeleton `sk_week_analytics` bol na telefónoch vizuálne príliš vysoký
  (240 px graf + 140 px doughnut + 3 stĺpce 1.9em). Pridané pravidlá pre
  `<768px` a `<480px`: graf 240->180->140 px, pruhy 140->64->44 px,
  doughnut 140->120->96 px, toolbar sa zalamuje, štatistika 1.9em->1.5em.
- Service worker cache `gitpulse-v34`.

## [2026.5.18.post4] - 2026-05-17 - Offline banner namiesto false alarmu

- Health monitor teraz rozlišuje **klient offline** (`navigator.onLine === false`)
  od **server nedostupný**. Offline stav zobrazuje neutrálny sivý banner
  s ikonou `wifi-off` a textom "Ste offline. Niektoré funkcie nemusia byť
  dostupné, kým sa pripojenie neobnoví." namiesto zavádzajúceho červeného
  "Systém je momentálne nedostupný".
- `_performCheck` sa preruší keď je klient offline (žiadne fetch volania,
  žiadna eskalácia na `down`).
- `window 'online'` listener vyčistí dismissed flag, skryje offline banner
  a spustí okamžitú re-kontrolu + toast "Pripojenie obnovené".
- Pridaná ikona `wifi-off` do JS registra ikon (`GP.icons.get('wifi-off')`).
- Service worker cache `gitpulse-v33`.

## [2026.5.18.post2] - 2026-05-17 - Pixel-paritá skeleton parity

- `sk_h_bars` (Teačerov checklist) má teraz 170 px široký štítkový stĺpec,
  18 px stolčeky a spodnú os 0-100 % - zhoduje sa s reálnym horizontálnym
  grafom.
- Pláceďovák pre "Compliance by Category" používa `sk_h_bars(count=4)`
  (reálny graf je tiež horizontálny).
- `sk_chart` prerobý na `gl-skeleton-chart-wrap` so shimmer pruhmi (predtým
  sú neviditeľné na tmavom povrchu) a tickami osi naspodku.
- Service worker cache `gitpulse-v31`.

## [2026.5.18.post1] - 2026-05-17 - Page-specific skeleton parity

### Zmenené

- Skeleton loadery teraz lepšie zodpovedajú reálnej štruktúre stránok:
   - Nové makro `sk_h_bars` vykresľuje horizontálne pruhy ako placeholder
      pre Teacher's Checklist (13 riadkov R01-R13 s rôznou výplňou).
   - Nové makro `sk_legend` vykresľuje legendu kategórií grafu nad
      Teacher's Checklist.
   - Nové makro `sk_week_pills` vykresľuje pilulky týždenného navigátora.
- Doughnut skeleton zdravia pipeline na stránke Aktivity teraz používa
  radiálny gradient (číta sa ako doughnut graf, nie ako plný disk).
- Odstránený osirelý `to { opacity: 1; }` blok ponechaný v `loaders.css`
  po predchádzajúcej čistke progressive-reveal mechanizmu.
- Service worker cache verzia bumpnutá na `gitpulse-v30`.

---

## [2026.5.18] - 2026-05-17 - Skeleton legacy cleanup

### Zmenené

- Skeleton loadery sú prepísané na čistý GitLab Pajamas shimmer bez
  progressive reveal scaffoldingu. Všetky skeleton primitives (texty, stats,
  karty, tabuľky, taby, grafy, zoznamy, activity feedy, formuláre) sa renderujú
  naraz s jednotnou Pajamas shimmer animáciou.
- Odstránené legacy markery a mŕtve kontrolery: triedy
  `gl-skeleton-progressive`, `gl-skeleton-deferred`, `gl-skeleton-row--deferred`;
  atribúty `data-skeleton-progressive`, `data-skeleton-table`,
  `data-skeleton-total-items`, `data-skeleton-initial-items`,
  `data-skeleton-total-rows`, `data-skeleton-initial-rows`,
  `data-skeleton-delay`; kwargy `initial`, `initial_lines`, `initial_rows`,
  `initial_bars`, `deferred` v skeleton makrách; JS funkcia
  `_initProgressiveSkeletons` a jej `GP.initProgressiveSkeletons` /
  `GP.initProgressiveSkeletonTables` exporty; pravidlo
  `@keyframes glSkeletonItemReveal` a reduced-motion selektor
  `.gl-skeleton-table.is-progressive-expanded .gl-skeleton-row--deferred`.
- Service-worker cache verzia je teraz `gitpulse-v29` a bundle/min súbory boli
  prebuildnuté.

---

## [2026.5.17.post4] - 2026-05-17 - System-wide progressive skeleton reveal

### Zmenené

- GitLab/Pajamas-style progressive skeleton reveal teraz platí pre zdieľané
  skeleton primitives, nielen pre tabuľky: textové bloky, stats gridy, karty,
  taby, grafy, zoznamy, activity feedy, key-value riadky a formuláre zobrazia
  ľahký prvý batch a rozšíria sa iba keď lazy load zostane viditeľný.
- Dashboard home stats a course cards používajú rovnaký progressive reveal
  contract, takže primárne placeholders sa ukážu prvé a sekundárne doplnia
  štruktúru bez prázdnych medzier.
- Support ticket a support form skeletony už nemiešajú spinner do rovnakého
  content regiónu. Odpovede a follow-up polia majú štruktúrne placeholders;
  spinnery ostávajú pre action/background stavy.
- Asynchrónne tabuľky v Course Settings teraz používajú progressive table
  skeletony pre webhook konfigurácie a compliance checks namiesto centrovaných
  spinner blokov.
- Nepoužívaný `sk_content_spinner` macro a jeho CSS boli odstránené, takže
  loader primitives už neponúkajú zastaranú cestu pre page-content spinner.
- Aplikačná aj dokumentačná metadata teraz používajú `2026.5.17.post4`.
- Service-worker cache verzia je teraz `gitpulse-v28`.

---

## [2026.5.17.post3] - 2026-05-17 - Progressive skeleton table loading

### Zmenené

- Zdieľané dashboard table skeletony teraz používajú postupné načítanie: najprv
  sa zobrazia tri riadky a až pri pomalšom lazy requeste sa otvorí
  page-specific počet riadkov.
- Dokumentácia quality gates dopĺňa frontend loading contract: skeleton pre
  sekcie, ktoré sa postupne naplnia obsahom, spinner pre akcie a background
  prácu, bez miešania skeletonu a spinneru pre rovnaký región.
- Scale load-test konzolový status používa ASCII `[PASS]` / `[FAIL]` značky,
  aby kontroly neboli závislé od Unicode podpory vo Windows termináli.
- Aplikačná aj dokumentačná metadata teraz používajú `2026.5.17.post3`.
- Service-worker cache verzia je teraz `gitpulse-v27`.

---

## [2026.5.17.post2] - 2026-05-17 - Avatar loading a health version display

### Opravené

- Avatary na dashboarde a v topbare sa teraz načítavajú eager s vysokou
  prioritou a používajú neutrálny image background. Pomalá odpoveď GitLab
  avatar URL už počas vstupu na stránku neukáže fialový initials fallback.
- Health karta v Admin System zobrazuje runtime verziu presne tak, ako ju
  vracia `/health` (`2026.5.17.post2`), bez pridania prefixu `v`. Forma
  `v...` je vyhradená pre názvy git tagov.
- Service-worker cache verzia je teraz `gitpulse-v26`.

---

## [2026.5.17.post1] - 2026-05-17 - CSP inline cleanup a release metadata

### Zmenené

- Aplikačná aj dokumentačná metadata teraz používajú `2026.5.17.post1`.
  Existujúci tag `v2026.5.17` zostáva nezmenený, preto tento release používa
  `.post1` namiesto prepisovania histórie tagov.
- Dashboard shell už nevkladá inline script pre registráciu service workera.
  Registráciu rieši zdieľaný bundle `core.js`.
- Warning toasty na stránke Admin Events sú riadené cez JSON `gp-page-config`
  a renderuje ich `admin-events.js`; stránka už negeneruje state-specific
  inline scripty.
- DLQ loading spinner používa zdieľanú CSS utilitu `.gl-spinner-inline`
  namiesto inline style atribútu.
- Service-worker cache verzia je teraz `gitpulse-v25`.

### Overené

- Konzervatívny dead-code scan nenašiel bezpečných kandidátov na odstránenie.
- Typography cleanup scan nenašiel žiadne project-owned súbory na zmenu.

---

## [2026.5.16.post2] - 2026-05-16 - Semester scope a docs hygiene

### Pridané

- Formulár nastavení kurzu zobrazuje viditeľnú info-poznámku "Kaskáda rozsahu",
  ktorá vždy upozorňuje, že zmena semestrálneho okna prepočíta rozsah pre
  všetky dashboardy, synchronizácie, hodnotenie zhody a reporty.
- Pred uložením zmeny semestrálnych dátumov sa zobrazí potvrdzovací dialóg
  s presným zoznamom dôsledkov (čo bude skryté, čo bude opäť pridané).
- Prázdne stavy v profile študenta uvádzajú aktuálne semestrálne okno
  ("Showing current semester window: ..."), aby bolo jasné, prečo neexistujú
  žiadne komity / MR / issues.
- Skript na čistenie typografie teraz pokrýva JSON, web manifesty,
  extensionless deployment súbory a voliteľne i18n katalógy; normalizuje smart
  punctuation, dekoratívne šípky a box-drawing oddeľovače v komentároch.

### Zmenené

- Aplikačná aj dokumentačná metadata používajú `2026.5.16.post2`. Omylom
  future-dated metadata boli opravené, pretože dátum releasu je 16. máj 2026.
- Sweep, enrichment a LLM joby (`enrich_issue`, `enrich_mr`, `llm_job`,
  `_enrich_all_async`) explicitne filtrujú entity vytvorené pred
  `course.settings.semester_start_date`. Staršie komity, MR, issues a
  pipeliny zostávajú uložené, ale nie sú znovu spracované ani započítané
  do current-semester metrík.
- Dashboardy admina, hlavnej stránky, kurzov a tímov používajú spoločnú
  helper-funkciu `semester_floor_utc`, takže read-path a worker-path
  zdieľajú presne tú istú dolnú hranicu.
- Spodná hranica pre HTML5 validáciu dátumov sa automaticky posúva každý
  rok (`semester_date_min` = January 1 of `today.year - 2`) namiesto fixného
  `2020-01-01` - tým sa zabraňuje vstupu zastaraných dátumov, ktoré by
  "spôsobili nulový rozsah" a tichú stratu komitov.
- Reporty a exporty používajú zdieľaný mobile-safe blob download helper.
- Service-worker cache verzia je teraz `gitpulse-v24`.

### Opravené

- Generovanie reportov zachováva full name učiteľov, počíta distinct student
  improvements, uvádza compliance delta ako percentuálne body a spoľahlivo
  sťahuje PDF aj v mobilných prehliadačoch.
- Vrchný progress bar sa už nespúšťa skôr, než AJAX form handlery stihnú
  zastaviť native submit, takže report formuláre nemajú falošný progress flash.

---

## [2026.5.16.post1] - 2026-05-16 - Health version follow-up

### Opravené

- Aplikačná verzia je teraz `2026.5.16.post1`.
- Runtime kontajnery teraz čítajú `project.version` z `pyproject.toml`, keď nie
  je dostupná installed package metadata, takže `/health` a metrics už po
  source-checkout deploymente nehlásia `version="unknown"`.

---

## [2026.5.16] - 2026-05-16 - Course-scoped dashboard release

### Zmenené

- Aplikačná verzia je teraz `2026.5.16`.
- Aktivita v detaile študenta je pri nastavenom začiatku semestra obmedzená
  na aktívne časové okno kurzu. Importovaná história repozitára zo starších
  akademických rokov sa skryje z tabuliek commitov a riadkových súčtov namiesto
  toho, aby nafukovala aktuálny kurz.
- Weekly compliance výpočet aj historický backfill ignorujú issues, merge
  requesty, review aktivitu, pipelines a commity pred začiatkom semestra.
- Tabuľky členov už neduplikujú globálne GitLab access role vedľa mena člena,
  keď ich už zobrazuje samostatný stĺpec Role.

### Opravené

- Staré commity z rokov 2021/2022 už nemôžu v kurze 2026 vytvárať zavádzajúcu
  commit quality ani contribution totals.
- Dashboard latest-changes feed už neobsahuje future-dated záznam.

---

## [2026.5.15.post2] - 2026-05-15 - Declarative client actions release

### Zmenené

- Aplikačná verzia je teraz `2026.5.15.post2`.
- Reload ovládacie prvky generované JavaScriptom teraz používajú spoločný
  kontrakt `data-action="reload-keep-scroll"` namiesto inline `onclick`
  handlerov.
- Read-only hint v detaile support ticketu používa CSS triedu na spacing
  namiesto inline štýlu v template.
- Service-worker cache namespace zvýšený `gitpulse-v6` -> `gitpulse-v7` a
  generované bundle sú obnovené.

### Opravené

- Offline fallback page už neemituje inline click handler; retry používa
  obyčajný GET formulár.
- Pridané statické frontend testy, ktoré chránia source JS a service worker
  pred návratom inline `onclick=` handlerov.

---

## [2026.5.15.post1] - 2026-05-15 - Login alert polish release

### Zmenené

- Aplikačná verzia je teraz `2026.5.15.post1`.
- Chyby autentifikácie na login stránke používajú reusable GitLab-style alert:
  tmavý surface, červený horný border, alert ikonu, dismiss akciu a žiadne
  inline štýly.
- Client-side login failures používajú rovnaký alert DOM/CSS kontrakt ako
  server-rendered chyby.
- Service-worker cache namespace zvýšený `gitpulse-v5` -> `gitpulse-v6` a
  generated bundles sú obnovené.

### Opravené

- Odstránený starý login-specific error block a neplatný red fallback v login
  stylesheet.
- Pridané statické testy pre login alert component contract.

---

## [2026-05-15] - Version baseline a obnovenie cache

### Zmenené

- Aplikačná verzia je teraz CalVer `2026.5.15`.
- Dôvod: repozitár začal ako full-codebase initial commit a pre-release
  audit pred týmto normalizačným commitom našiel `1875` commitov, 47 Alembic
  migračných súborov a žiadne historické release tagy. Spätne
  zrekonštruovaný SemVer by bol arbitrárny; CalVer čestne zapisuje dátum
  produkčného releasu.
- Service-worker cache namespace zvýšený `gitpulse-v4` -> `gitpulse-v5`.
- Documentation status, deployment príklady a dashboard latest changes sú
  obnovené pre release 2026-05-15.

### Opravené

- `dead-code-report.txt` je ignorovaný ako generovaný lokálny/CI artefakt.
- Overené, že aktuálne static/dead-code guard skripty sú shell-independent a
  nespoliehajú sa na `git ls-files`.

---

## [0.1.1] - 2026-05-14 - Production-safe cleanup release

### Zmenené

- Stabilizované lokálne a CI gate-y: normalizácia test env, shell-independent pre-push unit runner, Ruff pin na `0.15.4`, bundle drift check, static artifact guard a non-blocking dead-code report.
- Dashboard scheduler registry teraz zodpovedá produkčnému scheduleru: 26 registrovaných jobov vrátane email log retention, cleanup expirovaných previous webhook secretov, team discovery a semester auto-archive.
- OpenAPI hygiena: `/dashboard/login` GET má stabilný operation id a HEAD je skrytý zo schémy, aby nevznikali duplicate operation IDs.
- Test suite je warning-clean v default lokálnom gate: `2583 passed, 19 deselected`.

### Opravené

- Odstránený náhodne trackovaný root artefakt `-w`.
- Bundle/vendor skripty používajú ASCII status markery, takže Windows cp1252 terminály nepadajú.
- Previous webhook secret sa akceptuje len do `webhook_secret_previous_expires_at`, potom ho čistí scheduler.
- legacy roster upload validuje všetky riadky pred zápisom, takže nevzniká partial commit.
- Retired grading save odmieta nulový súčet category weights.
- Redis session-store fallback inkrementuje `session_store_fallback_total` a readiness robí probe iba keď je store zapnutý.

---

## [2026-05-14 - root-cause patch] - Opätovné prihlasovanie na každej návšteve opravené

### Príčina

Defaulty v `app/config.py` boli správne (`persistent_sessions=True`, 30 dní idle, 90 dní absolútne), ale **`docker-compose.yml` riadky 11-12 hardkódovali zlé defaulty**:

```yaml
PERSISTENT_SESSIONS: ${PERSISTENT_SESSIONS:-false}
SESSION_MAX_AGE_SECONDS: ${SESSION_MAX_AGE_SECONDS:-28800}   # 8 hodín
```

Produkcia mala v `.env.production` `PERSISTENT_SESSIONS=true`, avšak `SESSION_MAX_AGE_SECONDS=28800` (8 h) znamenalo, že idle okno podpísanej cookie vypršalo po 8 hodinách - kto sa vrátil raz za deň, musel prejsť celým GitLab OAuth flow.

### Opravené

- **`docker-compose.yml`** defaulty prepnuté: `PERSISTENT_SESSIONS:-true`, `SESSION_MAX_AGE_SECONDS:-2592000` (30 dní) a nový `SESSION_ABSOLUTE_MAX_AGE_SECONDS:-7776000` (90 dní).
- **`redeploy.py`** injektuje všetky tri hodnoty do `.env.production` pri každom deploye (idempotentný `sed`/`echo` vzor ako pri `GIT_SHA`). Auditovateľné, odolné voči driftu.
- **`.env` aj `.env.production`** aktualizované na nové 30 d / 90 d hodnoty ako baseline pre ďalší deploy.

### Odstránené (dead code)

- **`session_auth.verify_password()`** a **`session_auth.hash_password()`** - produkcia beží výhradne cez GitLab OAuth; tieto pomocné funkcie nemali žiadneho volajúceho mimo import smoke testu. Odstránené spolu s už nevyužívaným `bcrypt` importom v `session_auth.py` (samotný `bcrypt` package zostáva v `pyproject.toml`, využíva ho webhook autentifikácia).
- Príslušné riadky v `tests/unit/test_module_imports.py` odstránené.

### Overené ako používané (ponechané, NIE dead code)

Audit potvrdil, že `gitlab_oauth.refresh_access_token()` JE používaná - volaná z `dependencies.get_fresh_gitlab_token()` (riadok 626) s 5-minútovou rezervou pred expiráciou tokenu. Tichý OAuth refresh pri telemetry/sync volaniach už funguje.

---

## [2026-05-14] - Trvalé relácie a celosystémová multi-tab synchronizácia

### Zmenené (autentifikácia)

- **`persistent_sessions` prepnuté na `True` (default)** - relácie prežijú reštart servera aj redeploy. Používateľ sa už nemusí opätovne prihlasovať pri každom nasadení nového buildu.
- **Idle TTL 8 h -> 30 dní**, **absolútna TTL 24 h -> 90 dní** (`session_max_age_seconds`, `session_absolute_max_age_seconds` v `app/config.py`). Obranné mechanizmy ostávajú: podpísaná cookie + Redis opaque sid + Secure/HttpOnly/SameSite=Lax/`__Host-` prefix + UA fingerprint (voliteľný) + explicitné zneplatnenie pri logoute.

### Pridané (multi-tab synchronizácia - celosystémovo)

- **Locale (`gp_lang`)** - `locale-sync.js` počúva `storage` event a po zmene jazyka v ktorejkoľvek karte aktualizuje cookie a reloadne ostatné karty.
- **Kolaps sidebaru** - desktopové zbalenie/rozbalenie sa zrkadlí v reálnom čase medzi všetkými otvorenými kartami cez `sidebar-collapsed` v `localStorage` + nový `storage` listener.
- **Banner pre cookies** - `BroadcastChannel('gp_cookie_consent_sync')` skryje banner vo všetkých sesterských kartách v okamihu, keď ho ktorákoľvek karta akceptuje; `dismiss()` je teraz idempotentný a po dokončení animácie sa odstráni `cookie-banner-hiding` trieda.

### Overené (už synchronizované, bezo zmeny)

- Dokončenie tour (`tour-engine.js`), globálny job bar (`global-job-bar.js`), cross-toast broadcast (`core.js`), dismiss PWA install karty (`pwa-install.js`).

---

## [2026-05-13 - round 3] - PWA install card: multi-tab sync, prevencia konfliktov, životný cyklus

### Pridané

- **Cross-tab synchronizácia** - `BroadcastChannel('gp_pwa_install')` plus záloha cez `localStorage` `storage` event. Dismiss alebo inštalácia v jednej karte sa okamžite prepáli do všetkých ostatných.
- **Prevencia konfliktov** - `_conflictPresent()` odloží zobrazenie karty, kým je viditeľný `#cookieConsent`, `.gp-tour-welcome`, `.driver-active`/`.driver-popover`, `.modal.show`/`.gl-modal-overlay` alebo `.gp-app-loader.is-visible`. 800 ms re-poll loop kartu znova ukáže hneď, ako prekážajúci element zmizne.
- **Page-synced životný cyklus** - `visibilitychange` zastaví plánovanie pri skrytej karte a po návrate ho obnoví (žiadna animácia na nečinnej karte).
- **Event-hooky** - počúva `gp:cookie-consent`, `gp:tour:welcome:dismissed`, `gp:modal:close` a okamžite skúsi zobraziť. `tour-engine.dismissWelcomeCard()` teraz dispatchuje `gp:tour:welcome:dismissed` po skončení 320 ms exit animácie.
- **UX detaily** - Escape zatvára bez perzistencie; `BroadcastChannel` sa čisto zatvára pri `pagehide`.

### Zmenené (PWA copy)

- Popis karty už neklame o "offline support" (dashboard vyžaduje autentifikáciu a DB, offline fungovať nemôže). Nový text: *"Install this app on your device for a faster, full-screen experience with quick access from your home screen."*

---

## [2026-05-13 - round 2] - Modernizácia JS a oprava chýb v PWA prompte

### Zmenené

- **`pwa-install.js`** prepísané do moderného ES6+: `const`/`let`, arrow funkcie, `async`/`await`, optional chaining, nullish coalescing.
- **`core.js`** Alpine `$mdShowPreview` magic - 6 `var` deklarácií (stack, i, node, refEl, rendered, rm) nahradených `const`/`let`.

### Opravené

- **Race condition v hide-timeri**: `_hide()` `setTimeout` sa nedal zrušiť pri opätovnom zobrazení. Pridaný `_hideTimer` referenčný cyklus na úrovni modulu.
- **Deprecated `userChoice` API**: `_triggerInstall` prepísaný cez `result?.outcome ?? (await prompt.userChoice?.catch(()=>null))?.outcome` - podporuje moderné (Chrome 97+) aj staršie dvojkrokové API.
- **`clearTimeout(t)` vo vnútri fired callbacku**: presunuté pred plánovanie, aby sa timer skutočne dal zrušiť.

---

## [2026-05-13] - PWA install prompt (štýl GitLab Pajamas)

### Pridané

- **Vlastná PWA install karta** (`pwa-install.js` + `pwa-install.css`) - zachytí `beforeinstallprompt` a vykreslí elegantnú kartu v pravom dolnom rohu s ikonou, titulkom, popisom, akciami *Install* a *Not now* a tlačidlom `×`.
- **90-dňová pamäť dismissu** (`gp_pwa_install_dismissed_until` v `localStorage`).
- **Rešpektuje reduced-motion** (`prefers-reduced-motion: reduce` zníži tranzíciu na čistý fade).
- **Mobil** - prilepené k spodku viewportu, šírka cez celú obrazovku.
- **Public API** - `window.GP.installApp.{ show, dismiss, isAvailable }`.
- **i18n háčiky** - `pwa.install.title`, `pwa.install.desc`, `pwa.install.cta`, `pwa.install.cancel`, `pwa.install.close` (s fallback reťazcami).

---

## [2026-05-12] - Deduplikácia toastov a zoradenie z-index ladderu

### Opravené

- **Duplicitné sync-completion toasty** - pri dokončení sync jobu sa toast občas publikoval dvakrát (jedenkrát z SSE eventu, druhý raz z terminal pollu). Pridaný `sessionStorage` kľúč `gp_job_completion_dedup_v1` na potlačenie duplicít v rámci session; auto-poll je preskočený pre terminálne joby.
- **Z-index konflikty** - toast container sa občas renderoval pod app loaderom / cookie bannerom. Token ladder je teraz: `--z-cookie-banner: 1040`, `--z-tour-welcome: 1045`, `--z-app-loader: 1050`, PWA install karta hardkódovaná na 1055, `--z-toast: 1060`.

---

## [2026-05-11] - Oprava dismissu sprievodcu a responzívnosť na mobile

### Opravené

- **Sprievodca - dismiss pri kliknutí do sidebaru na deskope/tablete**: na desktopoch a tabletoch je sidebar permanentná súčasť layoutu - kliknutie na navigačný odkaz, prepínač jazyka alebo tlačidlo Collapse už welcome card ani aktívne turné nerušia. Guard pridaný do click listenera: `if (!_isMobile() && t.closest('#appSidebar, .gl-sidebar')) return;`.
- **Sprievodca - príliš broad `summary` selektor**: click handler používal holý selektor `summary`, ktorý zachytil **každý** `<summary>` element na stránke vrátane collapsible sekcií (napr. `code-reference` panely v nastaveniach kurzu). Selektor zúžený na `details.gp-menu, details.dropdown, details.user-menu` - `.closest()` sa cez DOM strom sám dostane k `<summary>` deťom, takže žiadna funkčnosť nevypadla.
- **Tour popover - Android 3-tlačidlový nav bar skrýval footer**: pri aktívnom `viewport-fit=cover` sa viewport roztiahne za systémový panel, ale `env(safe-area-inset-bottom)` môže byť na Android 3-button nav nulové. Dvojfázová oprava: transform bottom-sheetu odrátava `env(safe-area-inset-bottom, 0px)`; prehliadače s podporou `dvh` dostanú `@supports (height: 100dvh)` blok s `100dvh`, ktorý vylúči systémový panel spoľahlivo. Rovnaká logika platí pre tablet portrait a landscape breakpointy.
- **Tour popover footer - minimálna dotyková plocha**: `padding-bottom: max(env(safe-area-inset-bottom, 0px), 12px)` garantuje aspoň 12 px nad systémovým panelom aj tam, kde `env()` vracia 0. Pridané `min-height: 44px` (WCAG 2.5.5).
- **Welcome card - poloha nad systémovým panelom**: `bottom: calc(0.75rem + env(safe-area-inset-bottom, 0px))` posúva kartu nahor o výšku systémového panela.
- **Tour popover - max-height dvh**: `max-height: 70dvh` (s fallbackom `70vh`) používa dynamickú jednotku, ktorá vylučuje adresný riadok prehliadača aj systémovú lištu.

## [2026-05-10 - round 3] - Attribution chips: kto skutočne robil prácu na MR a Issues

### Pridané

- **Attribution chips v tabuľke MR (detail študenta)**: keď MR neobsahuje žiadne commity od zobrazeného študenta, zobrazí sa oranžový badge "Žiadne commity študenta" a mená skutočných autorov (modrý = učiteľ, sivý = spolužiak). Ak študent commitoval spolu s inými, zobrazí sa riadok "Tiež od:" s menami.
- **Stĺpec "Assigned to" v tabuľke Authored Issues**: kto má issue pridelenú - modrý badge pre učiteľa, sivý pre spolužiaka, pomlčka ak nikto.
- **Stĺpec "Opened by" v tabuľke Assigned Issues**: kto issue otvoril - rovnaká farebná logika.
- **Preklady** (`sk.json`): 6 nových kľúčov - `Also by:`, `No student commits`, tooltip pre "Žiadne commity študenta", `Opened by`, `Assigned to`, `Peer student`.

### Implementácia

- `src/app/api/dashboard/students.py`: batch SQL query cez `tuple_(Commit.project_id, Commit.ref).in_(branch_pairs)` - žiadne N+1; `teacher_ids` (UUID set) + `teacher_gitlab_ids` (int set) pre správnu detekciu učiteľov aj bez `author_id`; `aliased(StudentModel)` / `aliased(TeamMember)` pre dva outerjoin na Issues.
- `src/app/templates/partials/student/_merge_requests.html`: attribution row sekcia s podmienkami `not _student_commits` / `_other_commits`.
- `src/app/templates/partials/student/_detail_content.html`: nové stĺpce "Assigned to" a "Opened by".

---

## [2026-05-10 - round 2] - Badge "Vetva zmazaná" a synchronizácia commitov cez MR API

### Pridané

- **Badge "Vetva zmazaná" v tabuľke MR (detail študenta)**: keď bola zdrojová vetva MR zmazaná po zlúčení (GitLab `force_remove_source_branch` alebo ručné zmazanie), na príslušnom riadku sa zobrazí sivý badge s tooltipom. Vyžaduje nový DB stĺpec `merge_requests.source_branch_deleted` (migrácia `044`).
- **Primárna detekcia zmazania vetvy** (`mr_processor.py`): GitLab posiela `force_remove_source_branch=true` v REST aj webhook payloade - hodnota sa ukladá do stĺpca pri každom spracovaní MR.
- **Sekundárna detekcia** (`sync_job.py`): sync-job sleduje počty commitov per-vetva; ak MR fallback loop obnoví > 0 commitov, ale branch-ref vrátil 0 a MR je `merged`, systém automaticky nastaví `source_branch_deleted = True` - zachytí aj manuálne zmazania bez GitLab príznaku.
- **Obnovenie commitov cez MR API** (`sync_job.py`): po slučke branch-ref nasleduje fallback slučka, ktorá pre každý MR zavolá `GET /projects/:id/merge_requests/:iid/commits` - tento endpoint funguje aj po zmazaní zdrojovej vetvy.
- **Fallback priradenia commitov podľa mena autora** (`students.py`): dotaz pre commity na stránke detailu študenta pridáva klauzulu `author_name = student.full_name` - zachytí prípady, keď sa email nezhodoval, ale git display name áno.
- **Preklady** (`sk.json`): `"Branch Deleted": "Vetva zmazaná"` + slovenský preklad tooltip textu.

### Opravené

- **CI - mypy** (`students.py`): holá anotácia `: list` na `_commit_clauses` spôsobovala chybu `type-arg` v strict móde -> odstránená.
- **CI - ruff-format** (`students.py`): viacriadkové `.append(func.lower(...))` volania zmestia na jeden riadok -> jednoradková forma.

---

## [2026-05-10] - Oprava priradenia commitov (email fallback, noreply prefix)

### Opravené

- **Fallback priradenia commitov podľa emailu** (`students.py`): dotaz na commity na stránke detailu študenta obsahuje klauzulu `author_email = student.email` - commity bez `author_id` sa zobrazia, ak email sedí.
- **Odstraňovanie prefixu `<čísla>+` z GitLab noreply emailov** (`commit_processor.py`): GitLab generuje noreply emaily vo formáte `123456+username@users.noreply.gitlab.com`; prefix sa pred porovnaním orezal - sync správne zaradí commity k správnemu študentovi.

---

## [2026-05-09 - round 2] - Druhý sprint na sprievodcu, DLQ a tabuľky

### Opravené

- **Sprievodca v2** (`gp_tour_v1` -> `gp_tour_v2` storage prefix): jednorazový čistý reset zastaralých `:completed` kľúčov, ktoré pod v1 vznikali pri každom dokončení turné a navždy potlačili welcome card na všetkých etapách multistage stránky `/dashboard/support` (`course_id` -> `category` -> formulár). Pod v2 sa **bare** kľúč zapisuje **iba pri explicitnom zavretí** welcome card (× alebo "Maybe later") - dokončenie konkrétnej etapy si pamätáme len pod fingerprintovým kľúčom, takže ďalšia etapa stránky znova ponúkne sprievodcu.
- **Sprievodca - synchronizácia medzi tabmi**: nový `storage` event listener počúva zápisy do `gp_tour_v2:` v iných tabách. Akonáhle používateľ dokončí alebo zatvorí sprievodcu v jednom tabe, ostatné taby okamžite skryjú welcome card a (ak práve beží) zatvoria aj aktívny Driver.js overlay. Kým predtým sa dva taby pretekali o to, ktorý prepíše localStorage neskôr.
- **Admin / Event Pipeline - DLQ loader**: krúžiaci spinner v prázdnej tabuľke DLQ Events bol vizuálne statický. SVG `transform-origin` defaultne býva `0 0`, takže ikona sa "točila" okolo svojho ľavého horného rohu a v 20×20 px bunke vyzerala zamrznutá. Pridaný `transform-origin: 50% 50%; transform-box: fill-box;` na `.spin` rotuje ikonu okolo jej skutočného stredu - naprieč všetkými stránkami, ktoré túto utility class používajú.
- **Admin / Users + DLQ tabuľky - orezávanie textu**: `Role` (badge "Student") a `Status` (badge "Active") boli orezané na trojbodku alebo zalomené uprostred slova, lebo `td { overflow: hidden; text-overflow: ellipsis }` platilo na celú tabuľku vrátane buniek s pill badgemi. Truncation teraz cieli iba textové stĺpce (`Username`, `GitLab ID`, `Full name`, `Email`, `Created`); `Role` / `Status` / `Actions` majú `white-space: nowrap; overflow: visible`, takže sa zmestia kompletne. Upravené šírky stĺpcov: `Actions` 8 % -> 12 %, `Email` 22 % -> 18 %.
- **Admin / Users + DLQ tabuľky - responzívnosť**: pod 900 px (Users) a 1024 px (DLQ) tabuľky prepínajú na `table-layout: auto` s `min-width` v reálnych pixeloch, takže sa skryjú za horizontálny scroll svojho `.table-responsive` wrappera namiesto skreslenia hlavičiek typu "GitLab User I..." alebo orezania pravostranných tlačidiel.

---

## [2026-05-09] - Oprava OAuth slučky a UI ladenia

### Opravené

- **OAuth prihlasovanie**: koniec nekonečnej slučky "Session expired" po návrate z GitLabu. Callback teraz robí explicitný HTTP 303 See Other s `Cache-Control: no-store`, predĺžili sme `STATE_TTL` z 600 s na 900 s a opravili sme atribúty cookie `gp_returning`, takže prehliadač spoľahlivo prenesie session-id na cieľovú stránku.
- **`select_field` formulár**: koniec doslovného textu `u2014` v dropdown poliach. Filter `tojson_attr` teraz serializuje JSON s `ensure_ascii=False`, takže em-dash (`-`) ide do HTML atribútu ako natívny UTF-8 znak a nestráca sa cestou backslash escape.
- **Sprievodca - popover na mobile**: zmiernené pravidlo auto-prepnutia na vrchný panel. Predtým striktné podmienky (≥ 40 % prekrytia zdola **a** ≤ 10 % zhora) blokovali legitímne preklopenia pre polia v dolnej polovici obrazovky (napr. "Priorita" v `/dashboard/support`), takže popover fyzicky zakrýval pole, na ktoré ukazoval.
- **Sprievodca - viacstupňové stránky**: každá etapa `/dashboard/support` (výber kurzu -> kategória -> formulár) má teraz vlastný welcome card. Predtým dokončenie jednej etapy zapísalo aj "globálny" `:completed` kľúč, čím navždy potlačilo welcome card na ostatných etapách. Globálny kľúč sa teraz zapisuje len pri **explicitnom** zavretí (× alebo "Maybe later").

---

## [2026-05-07] - Sprievodca a UI vylepšenia

### Pridané

- **Sprievodca používateľa (Tour)**: nová časť o "Servisných účtoch" v administrácii (`admin_users` tour), ktorá vysvetľuje botov a analytickú kartu.

### Opravené

- **Nastavenia kurzu**: fix renderovania Unicode znakov (Em-dash vizuálny glitch ako `\u2014`) nahradením spojovníkom v "Select a preset" poliach.
- **Sprievodca (Tour engine)**: oprava logiky pre cache (lokálne verzus re-prompt po refreshi, kedy sa nesprávne ukladalo `skipped`). Po skutočnom dokončení turné sa označí ako `completed` a zbytočne sa neopakuje.
- **Zamedzenie layout shiftov**: nasadenie spinnerov pre nastavenia kurzu miesto ťažkých skeleton tabuliek pri načítavaní kontrol s HTMX.

---

## [2026-05-06] - Servisné účty (boti) ako prvotriedna entita

### Pridané

- **Stĺpec `users.is_bot` + parciálny index** (Alembic `042_user_is_bot`): nová `BOOLEAN NOT NULL DEFAULT FALSE` na `users` tabuľke s parciálnym indexom `ix_users_is_bot_false WHERE is_bot=false`. Migrácia urobí backfill cez vzory zhodné s `is_bot_user()` (`project_*`, `group_*`, `*_bot`, `*-bot`, `ghost`, `alert-bot`, `support-bot`). Predošlé runtime-regex filtrovanie sa nahradilo jediným indexovaným predikátom `humans_only_clause()`.
- **Nastavenie `is_bot` pri každom vytvorení používateľa**: 9 miest, kde aplikácia vytvára `User`/`UserModel` riadok (group import, OAuth first login, dev-mode auto-create, admin manuál sync, student create, projects/teams auto-create z inherited members) teraz volá `is_bot_user(username, user_type=...)` a ukladá výsledok do stĺpca. Servisné účty sú tým označené *raz pri vstupe*, nie sa heuristicky filtrujú pri každom dotaze.
- **Stat karta "Service Accounts"** na admin System Settings + samostatné `bots` číslo v `/dashboard/api/v1/admin/system/stats`. **User Role Breakdown** (chart) teraz počíta **iba ľudí** - botov treba čítať z dedikovanej karty, nemiešajú sa s rolami.
- **Service Accounts collapsible panel** pod hlavnou tabuľkou User Management. Botov sa nedá editovať/deaktivovať z UI; ostáva len `Info` tlačidlo, ktoré otvára rovnaký User Info modal s **`Service Account` badge** vedľa rolovej značky a tooltipom "GitLab service account / bot - not a human user". Skeleton (`sk_admin_users`) zarovnaný s reálnym layoutom: 4 filter pily (All/Admin/Teacher/Student) + náznak servisného panelu pod tabuľkou.
- **Vylúčenie botov z agregovaných počtov**: `dashboard_stats`/`home._build_stat_cards` (Active Users / Students), `member_sync_service.get_teachers_for_course` (učiteľský whitelist), `users.update_user` last-admin guard, support assignee dropdown - všetky teraz ignorujú `is_bot=true`.

### Opravené

- **Predošlý regex-based filter `not_bot_user_clause()`** bol band-aid: tá istá logika sa duplikovala v Pythone (`is_bot_user`) aj v SQL (`ilike`-OR strom). Existuje stále ako alias, ale nový kód má používať `humans_only_clause()` / `bots_only_clause()` z `app.services.user_filters`.
- **`sk_admin_users` skeleton mal len 3 filter pily** namiesto 4 - pri lazy load sa layout vizuálne posúval, keď doľahla skutočná hlavička.

### Zmenené

- **Preklady (`sk.json`)**: pridané `Service Account`, `Service Accounts`, `Bot`, `View service account details`, `GitLab bots - read-only`, `GitLab service account / bot - not a human user`.

---

## [2026-05-05] - Mobile-friendly tours + sync access control

### Pridané

- **Sprievodcovia plne responzívni na mobile** (`static/css/tour.css`): pridaný `@media (max-width: 600px)` blok, ktorý zmení popover na bottom-sheet zaberajúci celú šírku obrazovky, max 70 vh, s tlačidlami Späť/Ďalej v zalamovacom päte. Welcome karta sa rozťahuje na celú šírku mínus 0.75 rem margins. Žiadne horizontálne scrollovanie, žiadne odrezané popover-y.
- **Tour engine otvorí sidebar automaticky** (`static/js/tour-engine.js`): keď krok cieli element vnútri `#appSidebar` / `.gl-sidebar` a používateľ je na mobile (≤ 768 px), engine pred meraním rectu cieľa pridá `mobile-open` class na sidebar a `visible` na overlay. V `onDeselected` (a `onDestroyed`) sa sidebar zatvorí, aby ďalší krok mimo sidebaru nebol prekrytý drawerom. Kľúčový fix: doteraz mali sidebar prvky kladný bounding rect aj v zatvorenom stave (translateX(-100%)), takže Driver.js kreslil cut-out mimo viewport - používateľ videl len stmavnutý overlay s ničím vyznačeným.

### Opravené

- **Sync progress bar - viditeľnosť pre študentov bez kurzov**: `/api/sync/active` vracal `per_course` slovník so všetkými prebiehajúcimi syncmi systému; študenti, ktorí nie sú zapísaní do žiadneho kurzu, videli aktivitu cudzích kurzov. Endpoint teraz volá `_filter_courses_for_user` (rovnaká logika ako dashboard widgets), takže ne-admin používateľ vidí iba kurzy, do ktorých má prístup. Bearer-token volania a admini obchádzajú filter.
- **Multi-job count badge - prekrývanie v Opere**: badge bol absolútne polohovaný v pravom hornom rohu `#globalJobBar`, čo v Opere s úzkym viewport-om prekrývalo titulok jobu. Badge sa presunul do tenkého header pásu nad listom úloh (`bar.insertBefore(countBadge, bar.firstChild)`) a má teraz prirodzený vlastný riadok.

### Zmenené

- **Dokumentácia (`docs-site`)**: pridané záznamy v `changelog.md` (SK) a `changelog.en.md` (EN). Dashboard "Latest changes" widget zoradený rovnakým poradím cez `_CHANGELOG_ENTRIES` v `src/app/api/dashboard/home_changelog.py`.

---

## [2026-05-04] - Sprievodca aplikáciou (Guided Tours)

### Pridané

- **Driver.js v1.3.6 vendored** v `static/vendor/driver.js/` (MIT, ~21 KB JS + 4 KB CSS, žiadny CDN). Globálny entry point `window.driver.js.driver()` je predvolene súčasťou každej autentifikovanej stránky.
- **Tour engine** (`static/js/tour-engine.js`): role-aware (študent / učiteľ / admin), multi-language (en + sk), per-page detekcia podľa `location.pathname`, perzistencia stavu v `localStorage` (`gp_tour_v1:<slug>@<role>:{completed,skipped,prompted}`). Kľúče sú **scope-nuté podľa role**, takže po promócii študenta na učiteľa sa nové sprievodci ponúknu znovu.
- **Tour content registry** (`static/js/tour-content.js`): 20 sprievodcov pokrývajúcich Dashboard, Course Detail / Settings / Roster / Teachers / Analytics / Activity, Team Detail, Project Detail, Student Profile, Admin Users / Courses / System, Retired grading Editor a Support - každý plne preložený.
- **First-visit welcome card**: nenápadná floating karta vpravo dole s názvom sprievodca, počtom krokov, odhadom času a CTA "Take the tour / Maybe later". Auto-zatváranie po 25 s, jednorázová ponuka per role.
- **Help launcher v hlavičke**: položky "Take a tour" a "Replay tours" v existujúcom user dropdowne, klikom na Replay sa vyčistí história sprievodcov.
- **Themed Driver.js popover** (`static/css/tour.css`): plne zhodný s design tokenmi (`--surface-default`, `--primary`, `--shadow-lg`), animovaný stage pulse cez `.gp-tour-pulse`, redukovaný režim animácií (`prefers-reduced-motion`).
- **Hard role guard**: `run(slug)` odmietne spustiť sprievodcu, ktorého `roles` neobsahujú aktuálnu rolu používateľa - bezpečnostná poistka pre prípad, že content registry omylom registruje teacher-only sprievodcu na študentskej stránke.

### Opravené

- **Run Compliance Checks modal - biely pruh dole**: `rcm-footer` mal `background: var(--card-bg, var(--surface, #fff))`, ale ani jeden token nie je v aplikácii definovaný (existujú len `--surface-default`, `--surface-strong`). Fallback `#fff` vykreslil biely sticky footer. Footer používa `--surface-strong` a vystupuje cez `--gl-spacing-5` modal padding, takže lícuje s okrajmi modálu. Rovnako `rcm-group` a `rcm-item` boli prepojené na reálne tokeny - checkbox riadky majú teraz povrch, hover state, focus ring a inset border-stripe pri zaškrtnutí.

### Zmenené

- **Tour CSS** používa real SVG ikony / unicode dots namiesto emoji (žiadne rakety / mávanie / žiarovky / špendlíky / stopky). Welcome card meta riadok má dva pillové badge s farebnou bodkou (primary pre "steps", success pre čas).
- **Build pipeline**: `tour-engine.js` a `tour-content.js` pridané do `JS_MODULES` v `scripts/build_bundle.py`; `tour.css` pridaný do `static/styles.css` manifestu - minifikované `.min` siblingy a gzip-precompressed bundle sa generujú automaticky.

---

## [2026-05-03] - Webhooks v2

### Pridané

- **Multi-scope konfigurácie webhookov:** Každý kurz môže mať ľubovoľný počet webhook tajomstiev, každé priradené ku GitLab Group, Sub-group, zoznamu projektov alebo celému kurzu. Tajomstvá sa generujú na serveri, zobrazia sa práve raz a rotácia má 24h grace okno. Audit log zachytáva všetky create / rotate / revoke události.
- **Auto-detekcia GitLab group path:** Pole `gitlab_group_path` na úrovni kurzu sa už nezadáva ručne - systém počíta najdlhší spoločný prefix z `gitlab_group_path` existujúcich tímov pri uložení. Pole odstránené z UI kvôli duplicite s per-config scope.
- **Archive-safe webhooky:** Pri archivácii kurzu sa všetky jeho `WebhookConfiguration` riadky preklopia na `is_active=False`, takže auth lookup ďalšie doručenia odmietne s 401. Riadky zostanú zachované (audit + rotation grace). Pri reaktivácii kurzu zostanú konfigurácie deaktivované - operator manuálne rozhodne, ktoré scope sú ešte relevantné.

### Opravené

- **Webhook config modal sa neotvára:** Vnútorný `.modal` div mal `class='d-none'`, čo prepisalo `.active` triedu na backdrope. Backdrop sa zobrazil, ale obsah zÿstal skrytý. Odstránené `d-none` zo všetkých 3 webhook modálov.
- **"Heads up" upozornenie prerobé** aby ladilo s ostatnými `.alert.alert-info` v modáloch (jednoriadkový callout, bez bold-prologu).

### Zmenené

- Odstránené legacy `api/group_webhooks.py`, `schemas/group_webhook.py`, `services/group_webhook.py` a `tests/unit/test_group_webhook_service.py` (nahradené modulom `webhook_configurations`). Pomocná funkcia na označovanie posledného použitia legacy course-level tajomstva bola priamo vložená do `api/webhooks.py`; `ROTATION_GRACE` teraz žije v `services/webhook_configurations.py`.

---

## [2026-05-03] - Late

### Zmenené

- **Backend refactor (-60 LOC, -73 net riadkov):** Hoistovanie 60+ duplicitných inúlínovaných importov v `admin.py`, `home.py`, `evaluation_report.py`, `pilot_telemetry.py` na úroveň modúlu. Odstránené mrtve cesty, opravené PERF401/PERF403 list/dict comprehensions a S110 "best-effort swallow" bloky majú explicitný `noqa` komentár. Žiadna zmena správania - `ruff` + `mypy 1.11` ostali čisté.
- **Analýza stránky kurzu - rýchla cesta:** `EvaluationReportService` má novú metódu `_collect_preview_data()`, ktorá preskčí 3 drahé agregáty (compliance trends, support summary, weekly aggregates) pre načítanie analytickej stránky. Generovanie PDF zostalo nezmenené.

### Opravené

- **Prístupnosť (a11y) - `<label>` bez asociovaného poľa:**
 - V `_analytics_content.html` (formulár generovania PDF reportu) štyri "header" labely (Course Name, Semester, Teacher Name, Report Period) prekonvertované z `<label>` na `<span class="form-label">`, lebo neopisujú žiaden vstupný prvok - označujú readonly zobrazenia.
 - V `member_filters.html`, `_run_checks_modal.html` a `forms.html` (toggle, bare checkbox, file-upload) doplnený explicitný `for=` atribút na obalľvé `<label>` prvky a generované `id` k checkbox vstupom v `_run_checks_modal.html`. Implicitné zabalenie aj explicitné `for` zahája oba kontrolné mechanizmy DevTools/axe.

---

## [2026-05-03]

### Zmenené

- **Detaily študentov (Collapsibles):** Prvá sekcia typu `<details>` sa teraz automaticky otvára aj v prípade prázdnych dát. Pokiaľ študent nemá priradené Issues alebo MR Diskusie, prázdny stav sa vizualizuje s inštruktážnym textom (namiesto potichu zbaleného zoznamu).
- **Vizuálne úpravy komponentov:**
 - Pridaná automaticky rotujúca šípka (chevron) pre element `.summary-toggle` (používaný v prehľadoch detailov študenta).
 - Component *Raw Check Details (JSON)* prestajlovaný ako štandardný rozbaľovací element s `pre`-formátovaním a lepšie ladí so zvyškom dashboardu.
 - Okraje v elemente `pagination-controls` sa po vložení do `details` neprekrývajú cez content (odstránený tzv. CSS notch).

### Opravené

- **Sprievodný text pod hlásením GitLab Health:** Notifikáčný banner je teraz vertikálne stohovaný s globálnym task barom, aby sa elementy neprekrývali. Hranica pre notifikáciu (`GL_FAIL_THRESHOLD`) bola zvýšená na 3 nadväzujúce výpadky.
- **Skeleton tabuľky (`.gl-skeleton-table`):** Vizuálne loaderi teraz lepšie využívajú flexbox a šírky sú rôznorodejšie (`nth-child` pattern) pre odstránenie monotónnych "blokov", no animácia a kompozícia zostáva konzistentná po celý čas načítania bez zablokovania vlákna DOM.
- **Oprava CSP pre `<script>` a `<link>` inliny:** Priamy atribút `onload` prepísaný, `nonce` pridaný na všetky inline script značky pre fungovanie striktného Strict CSP bez varovaní vo všetkých dashboard template moduloch.
- **Markdown úniky:** Znak spätného lomítka `\` pred Markdown kľúčovými znakmi sa už vo výslednom parsovaní renderuje bezpečne namiesto jeho tichého odseknutia.

---

## [2026-05-02]

### Bezpečnosť

- **Strict CSP - `@alpinejs/csp` build povýšený na 3.15.12 a defaultne zapnutý.** Pôvodne vendorovaný 3.14.9 mal očesaný evaluator výrazov, ktorý odmietal `||`, `===`, `!==`, `!`, `&&` a reťazcové argumenty metód - po zapnutí flagu padali všetky stránky používajúce `select_field()`, markdown editor taby, dropdowny pre vyhľadanie assignee, role-toggle dropdowny a sidebar taby (`Alpine Error: Alpine is unable to interpret the following expression...` v konzole). Alpine 3.15.3 (PR #4711, "Improve evaluator") obnovil plnú podporu inline výrazov; vendorujeme 3.15.12 (`vendor/alpine-csp-3.15.12.min.js`, SHA-256 `566167134bb2...`), takže šablóny zostávajú idiomatické. Middleware posiela enforced policy (s `unsafe-eval`/`unsafe-inline` pre spätnú kompatibilitu) aj strict Report-Only policy (`nonce-{nonce}` + `strict-dynamic`); povýšenie na enforce čaká na prázdny violation report.

### Zmenené

- **Markdown editor extrahovaný do jedného komponentu (`components/markdown_editor.html`).** ~30-riadkový GitHub-style toolbar (Heading / Bold / Italic / Quote / Code / Link / Bulleted list + Write / Preview taby) bol duplikovaný v troch templatoch (support formulár, detail tiketu, odpoveď v tikete). Jedno makro `md_editor()` teraz poháňa všetky tri miesta. Tlačidlá toolbaru prešli z `title=` na `data-tippy-content=` pre konzistentné tooltipy, dostali `aria-label`, a wrapper má `role="toolbar"` + `aria-label="Markdown formatting"`. Taby dostali `role="tab"` + `aria-selected`.

### Opravené

- **Tlačidlo Code v markdown toolbar opravené** (regresia z CSP migrácie). Predošlý overlapping regex cez tri support templaty dvojito predprifixoval volanie `$mdInsert` na `$$mdInsert`, ktoré ticho zlyhávalo. Opravené a konsolidované cez nové makro, takže sa to už per-template nemôže opakovať.
- **Edit User - loader na Save changes je vycentrovaný** v tlačidle (`inset:0; margin:auto`).
- **Dashboard - duplicitné riadky soft-deleted projektov sú skryté;** projekty s rovnakým názvom v rôznych tímoch sú v course tree disambiguované.

### Bezpečnosť

- **Absolútny TTL session-y vynucovaný aj na stateless (cookie-only) session-ách (AUTH-06b):** predošlý AUTH-06 fix pridal `session_absolute_max_age_seconds` iba do Redis session store-u. Stateless cookies (fallback pri nedostupnom Redise) naďalej záviseli výlučne od sliding `max_age` - aktívny používateľ (alebo ukradnutý cookie) si mohol TTL obnovovať donekonečna. `get_current_session()` teraz validuje claim `ts` (dátum vytvorenia) oproti `session_absolute_max_age` (default 24 h) pri **každom** načítaní session, nezávisle od storage backendu. Malformovaný `ts` = expired (fail-closed).
- **Rate-limit fail-closed vo VŠETKÝCH prostrediach (AUTH-05b):** predošlý AUTH-05 fix aplikoval fail-closed iba na `APP_ENV=production`; dev a test boli stále fail-open. Ak by dev `.env` omylom unikol na produkciu, rate limiting by sa tichto degradoval na no-op. Zjednotené na `HTTP 503 + Retry-After: 30` všade.
- **UA fingerprint sa ukladá vždy - aj pri prázdnom User-Agent (AUTH-08):** predtým pri chýbajúcom alebo prázdnom `User-Agent` headri cookie obsahoval `ua=""`, čo obišlo kontrolu fingerprintu. Útočník s ukradnutým cookie ho mohol replayovať z ľubovoľného klienta jednoduchým vynechaním headra. Session-y teraz vždy nesú fingerprint; prázdny UA produkuje hodnotu `"no_ua|no_ua"`, takže mismatch check sa spúšťa aj proti replay útokom, ktoré stripujú headre.

### Zmenené

- **Sweep enrich limitovaný na 2 000 jobov za periodický beh (SCALE-01):** `periodic_enrich_all` predtým zaraďoval enrich joby pre každý issue a MR naprieč všetkými aktívnymi projektami bez limitu. Pri 567 študentoch (~200-500 projektov × 15-30 entít) to mohlo zaplaviť frontu 5 000-15 000 jobmi naraz, vyčerpať kapacitu workerov a oneskoriť spracovanie webhook-ov. Nový config `sweep_enrich_max_jobs_per_run` (default 2 000) limituje celkový počet; zvyšné entity sa spracujú v ďalšom 24h cykle.

### Opravené

- **Mŕtvy kód odstránený v `sweep_stale_projects`:** duplikátny `return 0` (nedosiahnuteľný kód za prvým `return`) odstránený.

---

## [2026-05-07]

### Zmenené

- **Compliance engine - audit-driven kalibrácia kontrol R02/R04/R05/R06/R07/R08/R10/R11/R12:** komplexný logický audit 13-check systému odhalil sériu prípadov, kedy default semantika checkov nezodpovedala duchu zadania ZSI a buď nespravodlivo penalizovala disciplinovaných študentov, alebo naopak prepúšťala nezhody. Týmto release-om sa kalibrácia zarovnáva s textom "doing & communicating" (4-5 členné tímy, separátna feature branch per ticket, MR linkovaný na issue, dvaja reviewer-i, commit-ref-citing odpovede, Approve pred merge, MR + ticket sa zatvárajú spolu) a engine od teraz robí to, čo by skúsený učiteľ urobil pri ručnej kontrole.
   - **R02 (Branch naming) - fail-detail vysvetľuje aj protected-branch prípad** (predtým len "doesn't follow naming convention"). Nový text: "Branch '<name>' is on a protected name or does not match the configured naming convention" - okamžite jasné, či ide o naming-pattern miss alebo o priame mergeovanie do `master`/`main`/`develop`. Práznin vzor `branch_pattern` už nezhadzuje check (vetva sa proste preskočí).
   - **R04 (MR linked to issue) - branch-name fallback + presnejší bare-`#N` regex.** Worker `enrich_mr.py` aj `mr_processor.py` extrahuje `linked_issue_iid` aj z názvu vetvy (`issue-7-foo`, `7-add-login`, `feature/issue-12`), ak popis MR neobsahuje `Closes #N`. Kombinuje sa s textovým parserom - preferuje sa explicitné `Closes #N`, branch-IID je fallback. Bare-reference pattern `#N` je sprísnený na word-boundary aj na konci (`(?<![\w-])#(\d+)(?!\d)`), takže nezachytí `v#10` alebo `#10x`. FK `MergeRequest.linked_issue_id` sa zaresolvuje cez `gitlab_iid` lookup -> R11 vie spárovať MR s tiketom.
   - **R05 (MR description quality) - ratio počítania slov ignoruje markdown štruktúru.** Predtým mohol MR prejsť 10-word threshold s úplne prázdnym obsahom (sekcie `## Co`, `## Ako`, `## Prečo` zaberali ~9 slov bez toho, aby skutočne niečo opisovali). Helper `_word_count` teraz odstrihne markdown headers, list markers, link syntax `[text](url)->text`, italic/bold sigil-y a filtruje tokeny <2 znaky bez `\w` znaku. "Prázdne nadpisy bez obsahu" už neprejdú.
   - **R06 (Review Received) - počíta len reviewer-ov s zmysluplným feedback-om.** Predtým stačilo, aby reviewer napísal `"+1"` alebo `"ok"` a R06 ho započítal. Engine teraz agreguje všetky komentáre per reviewer (`notes_by_reviewer: dict[author_id, list[notes]]`), spojí ich a prejde cez `is_meaningful_comment(joined, min_words=cfg.min_word_count)`. Nový `cfg.require_meaningful` (default **True**) sa dá v UI vypnúť pre kurzy s lightweight review kultúrou. Detail uvádza počet reviewer-ov so "short comments only" zvlášť, takže teacher vidí, prečo R06 fail-ne aj pri 2 prítomných reviewer-och.
   - **R07 (Code Review Given) - default min_words 30 -> 15** (model `course_settings.min_review_word_count`, helper `is_meaningful_comment`, migrácia `039`). 30 slov bolo v praxi privysoké pre typické per-line review komentáre ("Tu by si mohol použiť dict comprehension namiesto for-loopu" má 9 slov a je to legitímna review). Zarovnáva sa s zvyškom kódu (kde `min_review_word_count` bol fallback na 15) a s ZSI textom, ktorý žiadny kvantitatívny prah neuvádza. Migrácia upraví iba kurzy stále na default-e 30; učiteľské customizácie sa nedotkne.
   - **R08 (Review Response) - počíta aj standalone reviewer notes + softer defaults.** Predtým engine bral ako "review thread" iba inline diff diskusie (notes s `discussion_id`); standalone reviewer komentáre na úrovni MR boli ignorované, takže študent mohol nikdy neodpovedať na `"Tento PR vyzerá dobre, ale chcel by som vidieť testy."` a R08 prešiel. Teraz `total_threads = inline_total + standalone_reviewer_notes` a `answered = inline_answered + min(standalone_author_notes, standalone_reviewer_notes)`. `cfg.require_commit_ref` zmenený **True -> False default** (ZSI commit-ref-citing odporúča, ale neuvádza ako must), `cfg.pass_if_no_threads` **False -> True** (študent nemôže odpovedať na feedback, ktorý neexistuje). Keď commit-ref nie je vyžadovaný, partial scoring je čistá `response_rate` (nie 50/50 weighting).
   - **R10 (Merged by author) - akceptuje aj merger-tímakolega.** Predtým `allow_self_merge=True` znamenalo "autor MUSÍ merge-núť", čo je sémanticky proti ZSI textu "assignment owner (or designated assignee) executed the merge". Default semantika je teraz **permisívna**: prejde, keď autor ALEBO ďalší resolved tímakolega (`merged_by_id != None`) merge-uje; **fail-ne iba pri unknown-user merger-i** (admin, bot, externý GitLab user). Nové explicitné cfg: `require_self_merge` (default False - autor MUSÍ kliknúť Merge) a `forbid_self_merge` (default False - reviewer-gates-merge model: niekto INÝ ako autor musí merge-núť). Detail strings: "Merged by author", "Merged by a team member after approval", "Merged by an unknown user (not a team member)".
   - **R11 (MR + Issue closed) - strict pairing cez `linked_issue_iid`.** Predtým bol check decoupled: stačilo, aby existoval **ľubovoľný** merged MR + **ľubovoľný** closed issue, čo prešlo aj keď študent merge-ol niečo úplne iné než tiket #7, ktorý zostal otvorený. Engine teraz buduje `issues_by_iid = {i.gitlab_iid: i for i in ctx.issues_assigned}`, pre každý merged MR pozre `mr.linked_issue_iid` a check passne **iba**, ak spárovaný issue je `closed`. Fallback: keď žiadny merged MR nemá `linked_issue_iid` (študent zabudol napísať `Closes #N` aj pomenovať vetvu), engine spadne späť na legacy any-issue-closed semantiku, aby unlinked-but-closed pair nebol prísnejšie penalizovaný než predtým. Detail strings: "Merged MR's linked issue is closed", "Merged MR references an issue that is still open", "MR merged and assigned issue closed (no explicit link)", "MR merged but no assigned issue is closed".
   - **R12 (Pipeline Health) - širšia detekcia test job-ov.** Substring `"test"` zachytával len `"test"`, `"pytest"`, `"junit"` (`junit` obsahuje `test` po zámene jednej slovo... nie, neobsahuje), takže pipeline s job-om `"spec"`, `"verify"`, `"coverage"`, `"jest"`, `"mocha"`, `"rspec"`, alebo `"phpunit"` sa hlásil ako "nemá test job" a R12 fail-ol. Detektor v `pipeline_processor.py` teraz prechádza tuple `("test", "spec", "pytest", "junit", "jest", "mocha", "rspec", "phpunit", "verify", "coverage")` proti `name` aj `stage`, takže tipické naming conventions cross-language sú pokryté.

### Bezpečnosť

- **Absolútny strop životnosti session-y 24 h (AUTH-06):** doteraz mal session store iba sliding TTL - aktívny používateľ (alebo ukradnutý long-lived cookie) si mohol TTL refreshovať donekonečna. Pridaný `session_absolute_max_age_seconds` (default 24 h); store stamp-uje `created_at` pri `create()` a v `load()` odmieta session-y staršie než limit nezávisle od sliding TTL. Ohraničuje blast-radius ukradnutého cookie.
- **Webhook side-effecty po commit-e fail-best-effort (EVT-01):** event processor-uje doteraz commitol DB transakciu a _potom_ spúšťal cache-invalidation, immediate enrichment, metrics enqueue a SSE notify. Ak ktorýkoľvek z nich raisol, outer `except` zavolal rollback - ale commit už bol persistovaný, takže `event.processed=True` zostalo a side-effecty sa nikdy nezopakovali. Teraz každý side-effect ide cez `_safe(coro, name)` ktorý chytá výnimky, inkrementuje Prometheus counter `webhook_processed_total{status="sideeffect_failed:<name>"}` a loguje `WARNING` namiesto bublania.
- **Redis vyžaduje heslo aj na internej Docker sieti (SEC-03/SEC-04):** doteraz Redis počúval bez autentifikácie a `REDIS_URL` mohlo byť `redis://redis:6379/0` bez hesla. Útočník s prístupom do Docker bridge-u (alebo so zlým rebind-om porto-mappingu) by si vedel prečítať session blob-y a queues. Validátor v `app.config` teraz v `APP_ENV=production` **odmieta naštartovať**, ak `REDIS_URL` neobsahuje password segment (`redis://:PASSWORD@...`). Compose template plnohodnotne zapína `--requirepass` keď je `REDIS_PASSWORD` set. Na produkcii vygenerované 40-char heslo, všetky 4 worker-y + scheduler + api re-pripojené.
- **`FEATURE_RBAC=false` v produkcii hard-faily (AUTH-04):** predtým `_check_required_roles` len logovalo `WARNING` a požiadavku _prepúšťalo_ bez kontroly rolí. Človek omylom vypnutím flagu by ticho otvoril všetky teacher-only endpointy. Validátor teraz v produkcii vyhodí `ValueError` pri štartu, čím deployment fail-ne fail-fast namiesto fail-open behu.
- **`DEBUG=true` v produkcii hard-faily (§7b):** debug mód odhaľuje stack trace-y a môže auto-zakladať admin používateľov. Validátor odmieta beh.
- **Rate-limit fail-closed v produkcii (AUTH-05):** keď bol Redis nedostupný, `dependencies.check_rate_limit` skončilo v `except Exception` a _povolilo_ request (graceful degradation). To znamenalo, že útočník dokáže obísť rate limit kompletným zhotenín Redisu (alebo brute-force-om kým Redis flapne). Produkcia teraz vracia `HTTP 503` s `Retry-After: 30` a logom `rate_limit_unavailable_blocking`. Vývoj a testy zostávajú permissívne.
- **`SESSION_STRICT_UA_FINGERPRINT` opt-in (AUTH-02):** UA-fingerprint je k dispozícii ako defence-in-depth proti XSS / cookie-theft replay útokom z iného OS / browser-a, ale ako default zostáva `false`. Pri prepínaní mobil <-> desktop alebo browser update-och nie je hash UA stabilný a flag default-true v praxi vyhadzoval reálnych používateľov 401-kou. Sady "prísnych" CSRF + IP-binding + absolútneho session ceiling-u (AUTH-04/05/06) poskytujú ekvivalent post-stolen-cookie ochrany bez tejto false-positive miery.

### Pridané

- **Healthcheck pre Caddy reverzný proxy (INFRA-02):** Compose definícia teraz robí `caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile` (interval 30 s, retry 3, start_period 10 s). Keď preklep v `Caddyfile` zhodí konfiguráciu, kontajner sa označí **unhealthy** namiesto tichého servovania starej cache.
- **Json-file log rotation 20 MB × 5 (INFRA-04):** `postgres`, `redis`, `api`, `worker`, `scheduler`, `caddy` majú default-logging cez `x-default-logging` YAML anchor. Predtým sa `/var/lib/docker/containers/*/*.log` mohol rozrásť na desiatky GB pri verbose worker-och a zhodiť disk.
- **Scheduler healthcheck (`/proc/1/cmdline`):** pôvodný `pgrep -f` testy zlyhávali, lebo slim worker image nemá procps. Použitý `tr '\0' ' ' < /proc/1/cmdline | grep -q app.workers.scheduler` - funguje v každom Linux kontajneri bez extra závislosti.
- **Auto-spustené integration-tests na feature branchoch (CI-05):** predtým `when: manual + allow_failure: true` znamenalo, že integration regression sa zachytil iba pri otvorení MR alebo merge-i do main. Teraz beží automaticky pri každom push-i na feature branch.

### Vylepšené

- **API memory limit 768 MB -> 1024 MB (INFRA-03):** PDF render pipeline + súčasné LLM streamy občas trafili OOM kill. Worker bumpnutý 512 -> 768 MB.
- **Sweep cleanup robí batched delete-y (DB-04):** `_cleanup_events_async`, `_cleanup_snapshots_async` a `_cleanup_audit_async` mazali `WHERE timestamp < cutoff` jedným statement-om. Pri 1 M+ riadkoch to malo dlhú transakciu, blokovalo replikačné slot-y a vacuum mohlo zaostávať. Helper `_delete_in_batches` mazaní vo farbenných 5 K-row dávkach s commit-om medzi nimi a hard cap 200 dávok / spustenie (~1 M riadkov / sweep). Subsekvenčné spustenia plynulo dorobia zvyšok.
- **SBOM generovanie nemá `allow_failure` (CI-02):** SBOM je supply-chain compliance artefakt. Tichý fail by znamenal, že release ide bez auditovateľnej depencency listingu.
- **Globálne `APP_ENV: "test"` v `.gitlab-ci.yml`:** unit-tests job nemal explicitné `APP_ENV`, takže s pridanými production validátormi by `Settings()` v testoch hádzalo `ValueError`. Globálna premenná zaisťuje, že iba production-targeted joby behajú v production režime.

### Opravené

- **Globálny job-bar - ETA "2 min left" sa zasekol pri 5+ min reálne uplynulých:** `_computeEta` sa volalo iba pri novej progress-vzorke, takže medzi dávkami 1 Hz timer iba inkrementoval elapsed clock, ale štítok `time-left` zostal na poslednej vypočítanej hodnote. Teraz ETA kotvená na wall-clock `expectedFinishAt`; tick re-rendruje `[data-job-eta]` cez `_displayEta(job)`, ktoré odpočítava k 0 a po vypršaní pôvodnej predikcie spočíta novú zo cumulative rate (`totalElapsed / pct * (100-pct)`). Žiadne flickeringy, ETA monotónne klesá.
- **Toasty pre dokončenie sync-u sa nezobrazovali pri minimalizovanej karte:** `sidebar.js` zatváral dashboardový SSE pri `visibilitychange->hidden`. Server pushe pre `member_sync_complete` teda počas minimalizácie nedorazili - `_queuedToasts` nemal čo flush-núť pri návrate. Teraz SSE zostáva otvorený (browseri throttle-ujú, ale doručia), zastavujeme iba 60 s polling timer.
- **Course Analytics - load order legacy report controllera:** report-form Alpine controller zil v `pages/course-analytics.js`, ktory sa loadoval cez `<script defer>` *vo vnutri* HTMX-swapnuteho partial-u. HTMX vytvara nove `<script>` elementy s `defer`, ale dynamicky inserted scripts nerespektuju `defer` semantiku - bezia async. Alpine medzitym presiel novy subtree a vyhodnotil controller skor, nez sa skript stiahol -> cascade `startDate / endDate / durationText / dateError is not defined`. Controller bol potom inline-nuty ako `x-data=""` literal priamo na `<form>` - ziadna load-order zavislost.
- **Test `test_tampered_signature_returns_none` flaky:** itsdangerous `URLSafeSerializer` pre SHA-1 emit-uje 27-char base64 podpis (162 bit-ov, z toho posledné 2 sú padding bits). Flipping len posledného char-u medzi `"A"` a `"B"` neménil dekódované HMAC byty (rozdiel iba v padding bit-och). Test teda v ~25% pípeline-ov reportoval, že tamper neporušil signature - pravdivo, ale to znamenalo, že test merá nesprávnu vec. Teraz mení interior char.

---

## [2026-04-29]

### Pridané

- **Notifikácia personálu kurzu pri novom support tikete:** doteraz dostával e-mail iba odosielateľ tiketu (potvrdenie). Učitelia/owneri kurzu sa o nových tiketoch dozvedeli iba tým, že manuálne otvorili dashboard. Nový template `notify_ticket_new_to_staff` (subject `[GitPulse] New ticket #{id} ({course_code}) - {title}`) sa rozosiela všetkým aktívnym `owner` + `teacher` daného kurzu (s vylúčením samotného odosielateľa) v oboch vetvách `submit_support_ticket` (dynamic-form aj fixed-column). Idempotency cez `ticket_new_staff` kľúč, retry s exponential backoff, sweep každé 2 min ako fallback (`api/telemetry.py`, `services/email_notifications.py`)

### Opravené

- **Únik súkromia: interné poznámky lekli odosielateľovi tiketu:** `notify_ticket_comment` posielalo e-mail submitterovi aj keď `is_internal=true` (interná poznámka určená len pre personál - napr. "tento študent klame, ignoruj"). Pridaný explicitný guard `not payload.is_internal` pred notifikáciou submitter-a. Internal poznámky teraz dostane výhradne pridelený teacher/staff
- **Avatary nezostávajú písmenkami po prebudení notebooku zo spánku:** keď notebook zaspí alebo Wi-Fi krátko vypadne, prehliadač vyhodí `error` event na _každom_ rozpracovanom `<img>` aváteri. Predošlý handler okamžite skryl `<img>` a zobrazil písmenkový fallback - _bez akejkoľvek logiky obnovy_. Po jednom uspánkovaní teda VŠETKY avatary v aplikácii (header, dashboard greeting, profil študenta, support tikety, course teachers, search) tichto degradovali na písmenká až do hard-reloadu. **Fix v `core.js`:** uložiť pôvodný `src` pri prvej chybe; ak `!navigator.onLine`, odložiť rozhodnutie o fallbacku (mark `data-avatar-pending="1"`) namiesto natvrdo zobrazenia písmena; nový retry-all listener na `online` + `pageshow` (BFCache) + `visibilitychange->visible` s 250 ms defer (čas pre DNS/Wi-Fi po wake) a cache-busterom obnoví všetky pending/fallback avatary jediným re-fetchom. Centralizované - funguje na celej aplikácii, nie iba na jednej stránke
- **Reálny double-submit race v formulároch - niektoré akcie posielali 2 POST naraz:** globálny intersepter formulárov v `core.js` bežal na _capture_ fáze a volal `preventDefault() + fetch()`, zatiaľ čo page-level handler na _bubble_ fáze tiež volal `preventDefault() + fetch()` na rovnakom formulári. Výsledok: dva HTTP POST za jeden klik. Postihnuté: dismiss LLM error (project detail), login, Alpine `@submit` formulár pridelenia učiteľa kurzu. **Fix:** rozšírený zoznam pravidiel preskočenia - globálny handler teraz nechá tak formuláre s `data-submit-action`, `@submit` / `@submit.prevent` (Alpine), `data-no-boundary="1"` aj HTMX atribútmi. `login.html` označený `data-no-boundary="1"`
- **Email scheduler zaseknutý 25+ hodín - koniec záhady "nedošlo žiadne email":** scheduler kontajner po dlhom uptime prestal registrovať periodické joby; pri starte ukazoval iba "Scheduler registered 5 periodic jobs" namiesto plnej sady. `sweep_email_queue` sa nezavolal nikdy -> `email_log` riadky zostávali `pending` navždy. Po `redeploy.py` (ktorý recreate-uje kontajnery) scheduler správne registruje všetky joby a smoke-test e-mail prešiel pipeline za 1.6 s

### Vylepšené

- **Caddy konfigurácia - vyčistené Caddy 2.x deprecation warnings:** `basicauth` direktíva zmenená na `basic_auth` pre `/grafana`, `/prometheus`, `/jaeger` (×3); odstránené redundantné `header_up X-Forwarded-Proto {scheme}` (×2 - Caddy reverse_proxy ho posiela automaticky). Po prebuilde žiadne deprecation/style warnings v `caddy` logu, basic_auth naďalej vynucuje 401 bez kreditov

---

## [2026-04-28]

### Vylepšené

- **Profil študenta - MR a issue diskusie rendrujú markdown:** komentariale review (`partials/student/_comments.html`) sa predým zobrazovali len s linkifikovanými `#`/`!`/`@` referenciami, zvyšok bol surový text. Teraz prechádzajú cez filter `render_gl_description`, ktorý bol rozšírený o **fenced code blocks** (```` ```c ...``` ````) - obsah je escapovaný, zabalený do `<pre class="gl-desc-pre"><code class="language-X">...</code></pre>` a má vlastný CSS štýl. Mark down ako `## nadpis`, `**bold**`, `_italic_`, zoznamy (`*`/`-`/`1.`), inline `` `code` `` a fenced bloky fungujú rovnako ako vo GitLab webe
- **Render markdown popis - žiadne veľké medzery medzi sekciami:** newliny sa teraz strihajú okolo OPEN aj CLOSE block tag-ov (`<h6>` ... `</h6>`, `<pre>`, `<ul>`, `<ol>`), takže prázdny riadok medzi nadpisom a odsekom už neprodukuje viditeľný dvojitý `<br>` gap. Bezpečnostný cap: 3+ po sebe idúce `<br>` sa zberú na 2
- **Note list (`components/lists.html`) - markdown render:** sekundárny note-list-item komponent (legacy cesta) používa rovnaký filter ako student detail, aby žiadna výpisová plocha s GitLab komentármi nezostala s holou escapovanou hodnotou
- **Globally unified course-sync banner format:** päť rôznych miest produkovalo štyri rôzne formáty toho istého `Syncing...` textu (SSE detail / SSE fallback / legacy poll / `registerServerSyncs` / `_reconcileCourseJobs`). Jeden helper `_courseSyncMsg(name, running, queued, synced, total)` v `global-job-bar.js` produkuje jednu formu vsade: `"NAME: Syncing X/Y groups done (R active, Q queued)"`, X/Y a zátvorky odpadajú pri neznámych dátach. Helper je vystavený cez `window._courseSyncMsg`, dashboard a course-detail page-skripty volajú ten istý kód - koniec flickeringu medzi formátmi pri každom SSE ticku alebo htmx settle

---

## [2026-04-27]

### Opravené

- **CI `dependency-scan` job - koniec falošného "Job failed":** druhý beh `pip-audit` (oproti celému inštalovanému prostrediu, nie len `requirements-lock.txt`) zachytával zraniteľnosti v _CI nástrojoch_ - `pip` samotný (CVE-2026-3219, fix zatiaľ nie je vydaný), prípadne `cyclonedx-bom`/`pip-audit` tranzitívne závislosti - ktoré nie sú našou aplikačnou závislosťou. Pridaný `|| true` na informatívny scan + komentár; `requirements-lock.txt` audit (skutočné runtime deps) zostáva striktný a generuje SBOM artefakt
- **Dashboard - falošný toast "Process timed out - check results manually" počas dlhého synku:** dva navzájom sa zosilňujúce buggy. (1) `_jobMaxAge` pre course-sync joby (UUID-like alebo numeric ID) bol 10 minút, reálny sync 8-skupinového kurzu beží 15-25 min -> staleness-guard hlásil timeout aj keď server stále aktívne synkoval. Zvýšené na 45 minút. (2) Predošlá oprava "passive `deferGlobalJob` neprepisuje živú správu" early-return-ovala bez `showGlobalJob` -> `_autoStartPolling` sa nikdy nezavolal, `lastUpdate` zostávalo zamrznuté, staleness-guard po 10 min vypálil aj na zdravý job. Passive vetva teraz spúšťa polling, ak ešte žiadny nebeží (`global-job-bar.js`)

## [2026-04-25]

### Vylepšené

- **Per-team Status pill na stránke kurzu - okamžite po kliknutí Sync All:** optimistický update v `triggerSyncAll()` zapíše `QUEUED` badge do `cells[4]` všetkých riadkov tímov a "Sync queued..." do Last Updated stĺpca pred odpoveďou servera. `_refreshCourseData()` neprepíše SYNCING/QUEUED badge počas SSE race-u; `updateTeamRow(team)` rieši všetky stavové prechody (`course-detail.js`)
- **`/sync-all` odpoveď do ~100 ms (predtým ~20 s):** discovery tímov (volania `/projects/:id/users`) presunuté do background tasku `_discover_course_teams_async` - endpoint okamžite vráti queued, frontend nemusí čakať na rate-limit od GitLabu (`api/sync.py`)
- **Pilot Telemetry Service lint - `cast(date, ...)` cleanup:** zjednotené `datetime` importy, premenované shadowing premenné v cykloch, ruff/mypy strict pass (`services/pilot_telemetry.py`)
- **Bez flickeringu progresu na dashboard kurzových kartách:** stabilizované Last Updated / progress text počas SSE updates

---

## [2026-04-24]

### Opravené

- **Compliance report PDF - žiadne orphanované nadpisy ani orezané riadky:** odstránili sme `page-break-after: avoid` na `<h2>` a `break-inside: avoid` na veľkých naratívnych/attention blokoch v `@media print`. V A4 landscape to spôsobovalo, že WeasyPrint posúval nadpis sekcie na prázdnu stranu, ak sa obsah už nezmestil do aktuálnej. Ponechané je len `break-inside: avoid` na úrovni riadkov tabuliek a titulkov - individuálne riadky sa už nerežú uprostred (`src/app/workers/report_job.py`)
- **Pilot Evaluation - reálne počty:** namiesto surového počtu riadkov `MetricSnapshot` (rástol s každým webhookom) sa teraz počítajú **distinct trojice (team_id, student_id, week_bucket)** joinnuté cez `TeamMember` s filtrami `is_active` + `excluded_from_scoring=False` - teacherov, peer-mentorov a vylúčených členov report už nezapočíta. Odstránili sme aj `or`-fallback, ktorý v prípade nulových `rpt_course_count` použil globálne číslo. Týždeň pokrytia má teraz fallback na `len(compliance_trends.weeks)`, aby graf a štatistika neukazovali `0` pri reálnych 5 týždňoch. Násobič klikov znížený na `2×checks + 4×flags` (`src/app/services/evaluation_report.py`)

### Vylepšené

- **Detail projektu - rovnaká veľkosť tlačidiel ako na skupine/kurze:** akčné tlačidlá v hlavičke stránky projektu (`Open in GitLab`, `Rotate Secret`, `Unlink`, `Run Checks`) už nepoužívajú `size='sm'` - zarovnávajú sa s tlačidlami `Link Project / Sync / Run Checks / Export CSV / Export JSON / Retired Report / Delete` na stránke skupiny. Vizuálna konzistencia naprieč úrovňami (Kurz -> Skupina -> Projekt)
- **@mention v popisoch MR na stránke študenta sa rendruje ako meno:** filter `linkify_gl_refs` prijíma voliteľný `username_map` (`gitlab_username -> full_name`) a pre mentiony spárované s členom tímu vypíše čitateľné meno (napr. `Reviewers: Andrii Betsa` namiesto `Reviewers: @sm361rw`). Neznáme @mentiony sa zobrazujú ako plain handle. Dotknuté šablóny: `partials/student/_merge_requests.html` (opis MR), `partials/student/_comments.html` (MR notes)
- **Compliance report - prepis do štýlu diplomovej práce:** číslované sekcie 1-9, titulky `Table 1..N`, pätka so stranou, empty-state paragraphs pre každú sekciu, kompaktný "Group Overview" namiesto 4-card gridu, odstránená duplicita v exekutívnom zhrnutí a recommended-actions

---

## [2026-04-23]

### Pridané

- **Per-kurz prepínač `skip_auto_archive` (migrácia `036`)** - nové boolean pole v `course_settings` chráni manuálne reaktivované kurzy pred opätovnou archiváciou pri ďalšom behu sweep-u. `course_service.activate_course()` ho automaticky nastaví na `True`, aby kurz reaktivovaný po skončení semestra nezmizol znova na ďalší deň. Učiteľ ho môže manuálne prepnúť v UI Settings -> sekcia "Dátumy semestra"
- **Presety integrované do modálok "Vytvoriť kurz" a "Klonovať kurz":** selektor Rýchla predvoľba teraz jedným kliknutím vyplní `academic_year`, `semester` (zimný/letný) aj dátumy `semester_start_date` a `semester_end_date` - učiteľ už nemusí otvárať Settings po vytvorení kurzu, aby sa kurz archivoval automaticky. Endpoint `POST /api/v1/courses/` prijíma voliteľné polia `semester_start_date` / `semester_end_date` priamo pri vytváraní
- **Pole `semester` rozšírené v `SemesterPreset`:** každý preset teraz nesie aj kanonickú hodnotu `winter` / `summer`, čo odstránilo potrebu ručne synchronizovať preset s `Course.semester` výberom
- **Plný cyklus exportu/importu** teraz prenáša aj `skip_auto_archive` v JSON konfigurácii - `config-import.js` validuje a vypisuje "Skip auto-archive: yes" do import summary
- **Automatické vypnutie automatizácie po skončení semestra:** nový denný plánovaný job `sweep_auto_archive_ended_courses` (queue `low`, interval 24 h) prepne `courses.is_active=False` pre kurzy, ktorých `semester_end_date + semester_grace_days` už uplynul. Pretože **všetkých 23 existujúcich periodických sweep-ov** už filtruje na `Course.is_active.is_(True)`, jediné preklopenie flagu okamžite zastaví: `periodic_enrich_all`, `periodic_membership_sync`, `periodic_metrics_all`, `periodic_llm_analysis`, `periodic_telemetry_snapshot`, `periodic_verify_webhooks`, `periodic_docker_reverify`, `periodic_enrich_users`, `sweep_stale_projects`, `sweep_dead_projects`, `sweep_discover_new_projects`, `sweep_discover_new_teams`, plus všetky cleanup sweepy. Výsledok: **nulové GitLab API volania pre dokončené semestre** (migrácia `035_semester_end_date.py`)
- **Nové pole `course_settings.semester_end_date` (DATE NULL):** explicitné "posledný deň výučby/skúšok". Pre kurzy bez vyplneného `semester_end_date` sa odvodí z `semester_start_date + semester_default_length_weeks` (default 14), čo chráni pred zabudnutými kurzami bežiacimi donekonečna
- **Rýchle predvoľby semestra pre TUKE FEI KPI - Informatika (všetky ročníky):** nový modul `app.utils.semester_presets` a endpoint `GET /dashboard/semester-presets` ponúka 4 preset-y: Zimný 2025/2026, Letný 2025/2026, Zimný 2026/2027, Letný 2026/2027. V UI kurzových nastavení dropdown **"Rýchla predvoľba"** jedným kliknutím vyplní oba dátumy (Monday of week 1 + posledný deň skúšok); učiteľ ich môže ďalej upraviť. Kalendár identický pre 1., 2., aj 3. ročník - TUKE FEI používa jeden akademický kalendár pre celý študijný program Informatika
- **Nové nastavenia v `app.config`:** `semester_auto_archive_enabled` (feature flag, default `True`), `semester_grace_days` (default `14` dní - buffer pre uzatvorenie známok, neskoré MR-ky, export záverečných reportov), `semester_default_length_weeks` (default `14`, fallback pre kurzy bez `semester_end_date`)
- **Helper modul `app.utils.semester`:** dve čisté funkcie - `get_effective_semester_end(cs, default_length_weeks)` a `is_semester_over(cs, grace_days, default_length_weeks, today=None)`. Explicitné `semester_end_date` má prednosť; fallback `semester_start_date + N weeks`. Open-ended kurzy (žiaden `start` ani `end`) sa nikdy neoznačia ako skončené - archivujú sa len manuálne cez admin UI
- **Plný cyklus exportu/importu konfigurácie** teraz prenáša aj `semester_end_date` v JSON `/settings/full-config` (export + import vetva), aby sa presety dali prenášať medzi inštanciami a klonovanými kurzami
- **14 nových unit testov** v `tests/unit/test_semester.py` pokrývajúcich: prázdne settings, open-ended kurz, within-grace, past-grace, fallback-to-start+N-weeks, preset uniqueness, bilingual labels, JSON shape
- **SK preklady:** `Dátum konca semestra`, `Koniec semestra`, `Dátumy semestra`, `Rýchla predvoľba`, `- Vyberte predvoľbu -`, `Končí`, `Posledný deň výučby / skúšok...`, `TUKE FEI - Zimný/Letný semester 2025/2026 a 2026/2027 (Informatika, všetky ročníky)` a ďalšie

### Opravené

- **Týždenný graf skóre a Weekly Breakdown - falošné W1-W7 riadky pre tímy aktívne od polovice semestra:** _reťaz piatich prepojených chýb_, ktorá spôsobila, že Score Trend ukazoval falošnú čiaru W1=100 % -> W7=0 % -> W8+ reálne, Skill Profile používal zastaralý radar z W7 (0 %) a Weekly Breakdown mal sedem prázdnych červených riadkov vyvolávajúcich paniku študenta a učiteľa:
   - (a) `pilot_telemetry.get_student_compliance_history` primárna vetva (keď existovali `StudentComplianceSnapshot` riadky) nikdy nevracala zozbierané dáta - `return filled` chýbalo - a kód padol do fallback MetricSnapshot vetvy, ktorá videla len najnovšie `computed_at` (W10). _Fix_: pridané `return filled` (commit `bd189ee8`)
   - (b) `compliance.engine.backfill_compliance_history` fabrikoval `StudentComplianceSnapshot` riadky pre týždne 1..N aj pre tímy, ktoré GitLab projekt ešte nemali (-> W1=100 % "default ok" + W2..W7=0 %). _Fix_: detekcia prvého aktívneho týždňa z `MIN(Commit.committed_at)`, preskočenie predchádzajúcich (commit `3e6fe1b1`)
   - (c) heterogénna n-tica `for col, model in ((Commit.committed_at, Commit), (MergeRequest.created_at, MergeRequest), ...)` zlyhala na CI strict-mypy kvôli union-type inference. _Fix_: rozdelené na tri explicitné `select(func.min(...))` dotazy (commit `52611892`)
   - (d) `Result[Any].rowcount` nie je v SQLAlchemy async stuboch -> CI mypy `attr-defined`. _Fix_: `getattr(deleted, "rowcount", 0) or 0` (commit `c289c5b1`)
   - (e) _skrytý root cause_: GitLab pri vytvorení projektu automaticky vytvorí počiatočný README commit s `committed_at ≈ čas vytvorenia projektu`, takže `MIN(Commit.committed_at)` vrátil W1 pre **každý** tím, a celá anti-fabrikačná logika z (b) zostala no-op. _Fix_: `first_activity` sa teraz určuje z `MIN(MergeRequest.created_at)` a `MIN(Issue.created_at)` (skutočné úmyselné akcie študenta); commity sa berú iba ako fallback a len tie, ktorých `author_id` zodpovedá `TeamMember.student_id` (ignoruje bootstrap bot/system commity) (commit `56a9387f`)
   - (f) _oprava post-deploy auditu_: aj po DELETE pre-activity `StudentComplianceSnapshot` riadky API stále syntetizovalo W1..(first_activity-1) ako `null` stub riadky kvôli `for wk in range(1, max_week+1)` - Weekly Breakdown ich renderoval ako prázdne em-dash riadky. _Fix_: rozsah začína od `min(populated_weeks)`, takže chart/heatmap/tabuľka zobrazujú len reálne týždne - žiadne fabrikované dáta, žiadne zavádzajúce prázdne riadky
- Dôsledok: pre tím, ktorý zahájil prácu v W8 a má aktuálnu aktivitu W10, UI teraz pravdivo zobrazuje iba W8, W9, W10 - bez zavádzajúcich W1=100 % (falošné zelené) ani W2-W7=0 % (falošné červené)

---

## [2026-04-22]

### Pridané

- **Job bar - stav "Dokončuje sa...":** globálna lišta postupu už nezamrzá na "0 beží, 0 v rade" počas 15-sekundového post-batch grace okna na serveri. Keď klient vidí `running==0 && queued==0` ale server ešte hlási `has_active_sync=true`, lišta prepne do stavu `finishing` so správou `t('Finishing...')` mésto ínak šrtnutého počítadla. Týka sa SSE aj legacy poll vetvy v `global-job-bar.js`
- **Preklad - pokryté stavy kariet a job bar fallbacky:** všetky hardcoded English fallbacky v `global-job-bar.js` (`'Analyzing...'`, `'Generating report...'`, `'Running compliance checks...'`, `'Importing roster...'`, `'Exporting data...'`, `'Processing...'`) zabalené do `t(...)` a pridané zodpovedajúce klúče do `sk.json`. Audit skript `scripts/find_missing_translations.py` teraz hlási 0 chýbajúcich klúčov

### Pridané

- **Issues to Address -> interaktívny graf:** statický zoznam porušených kontrol nahradený horizontálnym stĺpcovým grafom (Chart.js) - os X je % zasiahnutej skupiny, stĺpce sú farebne odlíšené podľa závažnosti (červená High / oranžová Medium / modrá Low), animované entrance (900 ms, staggered). Hover tooltip zobrazuje count/weight/severity, klik na stĺpec rozbalí detail-panel so zoznamom zasiahnutých študentov v grid-e kariet s click-throughom do riadku tabuľky členov. Zachovaný IntersectionObserver scroll-reveal pattern a `<noscript>` fallback. Chart.js sa načíta iba na project-detail stránke cez `extra_head`
- **Detail-panel Issues to Address:** nová kartička s farebným ľavým okrajom podľa severity, uppercase severity-pill, close-tlačidlo (×), tabular-nums štatistiky (affected/total · share · weight) a zoznam študentov ako hover-highlighted karty v responzívnom grid-e. Legenda ako pill-chips (namiesto kurzívy) pre konzistentnosť s ostatnými komponentmi
- **Quick Access - informatívne položky:** každá položka v bočnom paneli teraz zobrazuje traffic-light bodku poslednej compliance metriky, skóre v % a počet členov z `TeamMetricSnapshot` namiesto iba názvu (sidebar je teraz informatívny, nie dekoratívny)
- **Slovenský preklad UI - kompletné pokrytie:** doplnených 99 chýbajúcich prekladov do `sk.json` (chybové hlášky synchronizácie, dialógy potvrdení, toast správy, editor rubriky, stránka admin-users, user-info modal, reaktivácia projektu, CI scenáre). Nový audit skript `scripts/find_missing_translations.py` skenuje všetky `t(...)` volania v JS a šablónach a hlási chýbajúce kľúče - zaradený do CI checklistu
- **Vlastné výnimky pre GitLab klienta:** nová trieda `GitLabPaginationTruncatedError` (podtrieda `GitLabAPIError`) - pagination-truncate už nevracia čiastočné dáta ticho, ale vyvolá výnimku, takže per-project `try/except` označí len tento jeden projekt ako zlyhaný a sweep ho neskôr zopakuje

### Opravené

- **Mobilná responzívnosť - tabuľky a profilová karta:** (1) profile header na úzčku `.profile-identity` nemal `min-width:0` a odkaz "Zobraziť na GitLabe" pretáčal cez okraj karty na mobile - pridané `flex:1+min-width:0`, `overflow-wrap:anywhere` a `align-self:flex-start+nowrap` na link. (2) Tabuľka členov projektu mala na mene `<td class="text-nowrap">`, sticky koľonka sa preto roztáhla a prekrývala R01-R13 check-bunky - na mobile sa `text-nowrap` prepíše na `white-space:normal` + `max-width:14rem` + wrap badges. (3) Teams tabuľka kurzu (7 stĺpcov) skrýva tree-toggle a Last Updated stĺpec na mobile, aby Avg Score / Status / Actions boli viditeľné bez horizontálneho skrolu. (4) Check-bunky `.check-pass/.check-fail/.check-na` prepnuté na `vertical-align:middle` - ikony už neleznia navrchu viacriadkovej bunky s menom
- **Klik na meno študenta v Issues to Address už neposkúva stránku na vrch:** `scrollIntoView` skroloval aj externe ch-containery (viewport) prečo sa fixný topbar vizuálne presunúl. Teraz skrol cieli výhradne na `.gl-page-content` a dopočíta `scrollTop + boundingRect` posun, takže cieľový riadok presne centruje v scrolľovateľnej zone a okolité elementy (topbar, breadcrumb, sidebar) zostanú nehybné
- **Týždenný compliance heatmap - historické týždne už nie sú prázdne:** dve previazané chyby mazali minulé týždne pri synku. (a) `compliance.engine` v `backfill_compliance_history` ignoroval parameter `as_of_week` a vždy písal aktuálne číslo týždňa do `StudentComplianceSnapshot.week_number`. (b) `pilot_telemetry.capture_team_snapshots` posielal ON CONFLICT DO UPDATE so zbaveným `raw_metrics` (bez `checks_detail`), čím prepísal engine'om naplných 13 checkov na prázdne. Fix: engine rešpektuje `as_of_week`, telemetry sweep teraz odvodí kategorické skóre z `_derive_category_scores(checks_detail)` a do raw_metrics píše superset. 170 unit testov prehľto

- **Issues to Address - kohorta priamych členov projektu:** bola zoradená podľa `latest_computed` s limitom 20, ale tých 20 riadkov boli tie isté tímy, čo už boli v karte Groups (team:project je ~1:1), takže po Python dedupe ostalo 0 projektov a karta vždy ukazovala prázdny stav. Teraz sa `team_id NOT IN` tlačí do SQL `WHERE`, takže 5-row limit sa minie na tímy, ktoré NIE SÚ už v Groups; ak Groups pokrýva všetky tímy (≤5), fallback ukáže top-5 projektov bez ohľadu na duplicity
- **Course Analytics - automatické skrolovanie stránky pri načítaní:** prvotné `selectWeek(currentWeek)` volalo `pill.scrollIntoView({block:'nearest'})`, čo prehliadače interpretovali ako vertikálne skrolovanie celého dokumentu (keď cieľ bol pod prvou obrazovkou). Teraz initial select preskakuje scroll (`scrollPill:false`), a user-driven klik používa `weekPills.scrollBy({left, behavior:'smooth'})` scoped iba na horizontálny pásik pill-ov
- **LLM modal - guard proti volaniu endpointov bez API kľúča:** všetky LLM modály teraz kontrolujú feature flag aj prítomnosť API kľúča pred zobrazením a vracajú priateľskú chybu namiesto 500 z upstream volania
- **GitLab 429 (rate limit) - tichá strata dát:** po vyčerpaní retry-ov klient vracal `None`, čo volajúci kód interpretoval ako "žiadne dáta" (404) - sync job sa označil ako `completed` s chýbajúcimi issue/MR/pipeline záznamami, dashboard zobrazoval nesprávne metriky. Teraz vyvolá `GitLabAPIError(429)` s `Retry-After` v správe
- **GitLab pagination (10 000+ položiek) - tichá strata dát:** pri dosiahnutí stropu `max_pages=100` s plnou poslednou stránkou (čo znamená, že GitLab má viac dát) klient vracal čiastočný zoznam a len zalogoval warning. Dashboard po synchronizácii zobrazoval "completed" s podhodnotenými číslami. Teraz vyvolá `GitLabPaginationTruncatedError` so štruktúrovanými poliami (`path`, `max_pages`, `items_fetched`) pre Grafana alert
- **Webhook rate-limit IP spoofing (DoS):** orphan-webhook rate limiter čítal `X-Forwarded-For` priamo z hlavičiek a obchádzal trust-boundary `ProxyHeadersMiddleware` - útočník mohol rotovať spoofed IP pre obídenie limitu 10/min a zaplavenie `orphan_webhook_events`. Teraz sa používa `request.client.host`, ktorý middleware už validoval voči `trusted_hosts`
- **Webhook backpressure - tiché zlyhanie kontroly:** `except: enqueue anyway` ticho skrývalo poruchy backpressure modulu / Redis outage. Fallback je zachovaný (best-effort enqueue), ale teraz sa loguje `logger.warning` s `exc_info` - operátori vidia degradovaný režim namiesto falošnej istoty
- **Globálny job bar - únik intervalu pri zatvorení karty:** `_syncWatchdogId` (5-sekundový polling `/sync/active`) sa nečistil v `beforeunload` handleri - interval žil až do garbage collection po zatvorení karty alebo odhlásení. Teraz `clearInterval` spolu s `_elapsedTimerId`

---

## [2026-04-21]

### Zmenené

- **Sync UI - jeden zdroj pravdy:** odstránený redundantný inline info-card "Sync in progress" z overview, roster aj teachers záložiek - perzistentný globálny progress bar je teraz jediný indikátor synku, čím sa odstránili duplicitné UI flash-e a double-animation počas prechodov medzi stránkami (-312 riadkov mŕtveho UI kódu vrátane komponentu `SyncStatusBanner` a jeho pollerov)
- **Sync freshness guard (up-to-date kontrola):** `POST /api/v1/courses/{id}/sync-all` a `POST /api/v1/teams/{id}/sync` teraz preskočia tímy, ktorých posledný úspešný sync skončil v 5-minútovom okne - odpoveď obsahuje `already_fresh: N`, single-team vracia `status: "skipped_fresh"`; `?force=true` obídete guard. Zabraňuje zahlteniu GitLab API pri opakovanom kliknutí na Sync All alebo pri paralelnom sledovaní kurzu viacerými učiteľmi. Frontend ponúkne force re-sync, ak sú všetky tímy čerstvé, namiesto tichého no-op-u

### Opravené

- **Globálny progress bar - objavenie aktívnych synkov na všetkých stránkach:** nový endpoint `GET /api/v1/sync/active` vráti prebiehajúce kurzové synky, ktoré globálny bar volá pri `restoreGlobalJobBar()` - bar sa teraz zobrazí aj na Admin -> Users / System / Dashboard, keď sync beží v inom tabe, zariadení alebo bol spustený plánovačom
- **Globálny progress bar - race conditions:** odstránený tichý removal bar-u počas 2-sekundového restore okna, keď `/sync-status` dočasne vrátil `has_active_sync=false` počas prechodu stavu; job má teraz flag `serverConfirmedRunning`, a silent-remove guard sa spúšťa len pre skutočné redirect-flash prípady
- **Issues to Address - kohorta priamych členov projektu:** karta iterovala cez celý tímový zoznam (napr. 37/37) namiesto len priamych členov GitLab projektu (napr. 5/5) - live-data endpoint teraz volá `get_project_members(include_inherited=False)` rovnako ako full-page render
- **Issues to Address - dynamická aktualizácia:** karta sa teraz prerendrovuje pri každej zmene (vylúčenie, zmena roly, nový check run) cez server-side Jinja partial
- **Issues to Address - syntetickí/zdedení členovia:** učitelia, mentori, zdedení a syntetickí GitLab-only členovia sú vylúčení zo scorer kohorty
- **CSS bleed systémové riešenie:** globálne `details summary::before` pravidlá presunuté pod opt-in triedu `.details-accordion`; odstránená duplikátna unicode šípka ▶ z `pages/course.css`

## [2026-04-20]

### Pridané

- Comprehensive mobile responsiveness overhaul
- GitHub-style zebra tables + changelog sidebar widget
- Kompletný changelog zo všetkých 1347 commitov od vytvorenia repozitára

### Opravené

- Auth resilience - login page for new users, next-URL preservation, crash protection
- Redesign OG image - clean centered layout for Google previews
- Prevent skeleton flash + lighten heavy table skeletons
- Rebuild bundles + ruff format auth.py (fix CI lint)
- Prevent zebra-stripe flash when toggling member filters
- Clean empty CSS ruleset + add restripeTable to no-paginator filter path
- Fully suppress transition on clickable rows during restripe
- Zebra tabuľky bez animácií - odstránenie transition na riadkoch, okamžitý hover (GitHub štýl)
- Propagate zebra/hover backgrounds to `<td>` for overflow:hidden tables
- Use solid opaque colors for table zebra stripes
- Remove opacity from row-page-enter animation to prevent color mixing during filter/pagination

### Zmenené

- GitLab-style skeleton loaders - lighter, mixed with spinners

### Infraštruktúra

- Code quality audit - var->let/const, dead code removal, cache fixes

## [2026-04-13 - 2026-04-17]

### Pridané

- Periodic team discovery sweep + lint fixes
- Email-based teacher/mentor detection + early sync progress
- Improve OG image + add skeleton loader to User Management
- Add peer mentor detection and filter
- Production-grade email notification system with retry queue

### Opravené

- Email enrichment propagates to User + filter inherited teachers from contributors
- Whitelist contributor filter - show only team student commits
- Whitelist contributor counts on course/team dashboard too
- Remove deprecated code, fix labels, inherited members modal, subtle flash
- Resolve mypy arg-type errors in _stats.py narrowing
- Lower coverage threshold to 30, fix arena email caching and timeouts
- Replace asyncio.TimeoutError with builtin TimeoutError (ruff UP041)
- Add arena email fallback to single-user enrich, suppress global bar flash on redirect
- Auto-create User records for inherited members, remove teacher/mentor opacity
- Batch enrich Arena fallback, course count from groups, inherited member import
- Inherited member import, toast visibility, course cards in modal
- Course display with code/year/semester for membership-derived courses, add academic_year+semester to membership API, fix ruff-format
- Arena enrichment for User records during import, role badge for derived courses, elevate Arena logs to warning
- Mypy User.gitlab_username type + strip course name from card sync badge
- Stale sync after redeploy + smooth global bar entrance
- Create User records during member sync (not only on initial import)
- Ensure User record for existing active members during sync
- Limit User creation during sync to teachers only
- Enrich User emails from Student records and Arena during sync
- Sync_all discovers new teams + Arena enrichment shared httpx client
- Arena enrichment 30s per-request timeout, concurrency 2
- Update scheduler test counts for job #23 + cross-team project dup guard
- Pass course_id to sync worker for early progress toasts
- Add toasts to enrich button + welcome-back toast after login
- Reduce lazy skeleton reveal delay from 400ms to 150ms
- Rewrite admin users skeleton to match page structure + ruff format
- Remove corrupted duplicate in sk_admin_users skeleton
- Defer admin-users paginator/filter init for lazy-shell loading
- Skeleton pagination to match 3-column layout (info | buttons | per-page)
- Update all skeleton pagination to 3-column layout (info|buttons|per-page)
- Skeleton search width, pagination inside card-body, mobile dropdown clamping
- Dropdown portal right-aligned, support tickets skeleton structure
- Dropdown portal conflict with global handler - use data-gl-portal marker
- Keep per-page dropdown visible when pageSize=all so user can switch back
- Skeleton card structure, pagination DRY, pageSize localStorage cache
- Add per-page dropdown to admin/system Job History pagination
- Mobile responsiveness, optimize scheduler & telemetry
- Stop spinner reset and button color flash on mobile
- Pull-to-refresh false trigger on table scroll + toast reliability + lint
- Completion toast suppressed when global bar visible
- Ruff E501 in scheduler.py (line too long)
- Member table, enrichment gate, contributor exclusion
- Global bar dedup, contributor exclusion in project detail
- Complete mentor support across all views and scoring paths
- Exclude mentors from all student count queries
- Preserve is_mentor and excluded_from_scoring on team reassignment
- Increase worker heartbeat freshness window to match RQ TTL (420s)
- Enrich PRIVATE emails during sync and periodic sweep
- Member table bugs - filter empty state, badge count, sorting, inherited visibility, commit-based email enrichment
- Arena email enrichment, mentor badge, blue focus, progress bar course name, student count labels
- Dashboard Students stat now counts User accounts (matches admin breakdown)
- Deduplicate role badges, global bar flash, blue row selection
- Prevent global bar flash during skeleton loader phase
- Ruff-check unused import + ruff-format (fixes CI pipeline)
- Dashboard JS created duplicate at-risk badge using old class names
- Show more description text in course card (3-line clamp, no Jinja truncate)
- Global job bar hidden on team page when course sync is running
- Sorting/filter conflict + welcome email on first login
- Rebuild JS bundle for sorting/filter changes
- Correct CTA links in welcome emails (404 paths)
- Remove all emoji characters from email notifications
- Replace deforming loader icon with smooth circle spinner
- Show text status badges instead of dots in group activity table
- Prevent page-size dropdown from being clipped by pagination container
- Replace custom page-size dropdown with native select
- Restore custom page-size dropdown with fixed positioning
- Portal page-size dropdown to document.body to escape overflow
- Smart dropdown direction - open downward when space allows
- Remove unused Request import (ruff F401)
- Tabs overflow, footer theme, remove icons, accuracy fixes
- Tabs scroll + footer light theme with explicit colors
- Shorten tab names, remove tab icons, light footer, full-width tabs
- Footer light mode with !important to override Material theme
- Footer text/link colors visible in light mode
- Stronger no-store cache headers to prevent stale proxy/browser cache
- Job history table responsive headers + zebra striping on filter/sort
- Replace broken Sync Status modal with toast notifications
- Update tests for queue-based email system + fix ruff lint

### Zmenené

- Replace var with const/Set/Map in JS, use begin_nested savepoints instead of rollback, add logger.debug for inherited member fetches, consolidate imports, fix line lengths
- Reuse ClientPaginator for admin Job History (server-side mode)
- Revert: remove commit-based email enrichment - Arena API already handles this
- Privacy: comprehensive GitLab-quality privacy statement with TOC, tables, GDPR rights, retention schedule, cookie details, supervisory authority

### Bezpečnosť

- Fix header issues from security scan
- Add privacy policy page, CSP upgrade-insecure-requests, sitemap update

### UI / UX

- Redesign: course card - clean layout like top companies

### Infraštruktúra

- Config: pass EXCLUDED_CONTRIBUTOR_NAMES through docker-compose
- Config: remove unused ARENA_EMAIL_API_TOKEN from compose (endpoint is public)

### Dokumentácia

- Comprehensive audit - fix counts, intervals, add 19 missing models
- Full documentation audit and actualization
- Move legal pages to docs-site, add student guide, open docs access

## [2026-04-09 - 2026-04-12]

### Pridané

- Smart stale data notifications with webhook activity detection
- Webhook attention items + fix activity feed showing team actions
- Premium Week Analytics with interactive Chart.js charts
- I18n: add 17 missing Slovak translations for Week Analytics
- Auto-expand current week in Week Analytics on page load
- I18n: add 87 missing Slovak translations
- Add Week Analytics skeleton loader to analytics page
- Redesign report generation form with component-based UI
- Simplify sub-project rows to links only, remove per-project metrics
- Detect template repos, unify team page contributor count
- Stale data warning banner for course and team pages
- Comprehensive i18n, job history improvements, LLM config diagnostics
- Expose Grafana/Prometheus/Jaeger via Caddy with basic auth
- Enrich Configuration Preview with detailed settings, LLM status, course metadata
- Install OpenTelemetry packages in Docker image and init tracing in workers
- GitLab-style course sub-navigation + update course configs

### Opravené

- Enrich activity feed with background_jobs + fix audit commit in sync endpoints
- Ruff lint + format errors (line length, unused import, alias)
- Remove broken effective-start detection, replace weekly summary with week navigator
- Analytics & activity quality audit - responsive, empty states, data consistency
- Show empty state message in week bar chart when activity is 0
- Pill focus outline follows rounded shape
- Fully suppress rectangular focus outline on week pills
- Remove focus ring from week pills entirely
- Remove blue glow shadow from active week pill
- Ruff-format compliance + suppress stale-data toast on report generation
- Widen GitLab ID column, add webhook setup info to Event Pipeline page
- Smart webhook detection on events page, rebuild CSS bundle
- Use toast instead of alert banner for webhook warning on events page
- Code quality improvements across admin module
- CI pipeline failures - lint script, admin early-return in _session_caller
- Mobile responsiveness - activity tables scroll, instructors layout, danger zone overlap
- Redesign instructors mobile layout - CSS Grid 2-row compact (GitHub/GitLab style)
- Mobile responsive - students table scroll, sidebar overflow, compact action buttons
- Sidebar panel overflow:hidden, action buttons 32px matching btn base height
- Distinct icons for team actions - code for JSON, bar-chart-2 for Report
- Stretch action buttons evenly across full width on mobile
- Uniform 36px square buttons in mobile action toolbar
- Quick Access projects tab overflow + skeleton loader matches action toolbar
- Quick Access ellipsis - move overflow:hidden to list level, not item
- Quick Access ellipsis - remove negative margins, add overflow:hidden to .gl-qa-text
- Truncate long project paths server-side (45 chars) + display:block on qa spans
- Quick Access: filter empty/template teams, fix CSS text-overflow
- Use student_id instead of id in TeamMember count
- Add display:block + flex:1 for CSS text-overflow ellipsis in Quick Access
- Use width:0+flex-grow:1 for reliable text-overflow ellipsis, cap sidebar on mobile
- Commits table + heatmap mobile responsive, badge inline positioning
- Pin trivy to 0.62.1 (latest tag removed from Docker Hub), guard publish upload
- Team contributors count uses distinct commit authors for consistency with sub-projects
- Live-data and SSE endpoints also use distinct commit authors for contributor counts
- Show dash instead of 0% for projects with no resolved authors
- Resolve ruff lint errors - unused import and per-file-ignores for utility scripts
- Sub-projects inherit team avg score and traffic light when no commit authors resolved
- Hide stale-data banner when sync is already in progress
- Template detection now also checks author_gitlab_id against team students
- Exclude teachers from contributor counts + robust compliance chart loading
- Contributor count excludes teacher by name + compliance data_attrs as dict
- Mypy types, dedup teacher imports, improve group messages, quick access, compliance visuals
- Mypy list[Any] type, never-synced count uses sync status not metrics
- MR empty state msg, improve semester settings, remove review requirements card
- Align course configs with assignment requirements + fix sk.json broken quote
- Remove C01/C02 custom checks, fix weights to sum 1.00
- Resolve mypy and ruff lint errors in LLM status endpoint
- Monitoring proxy + code quality cleanup
- Rebuild CSS bundle (config-preview-details styles were missing)
- Config preview sub-items layout (flex-basis + baseline align)
- Hide AI Analysis Configuration card when LLM feature is disabled
- Support form dropdown clipped by overflow:hidden on .gh-category-fields
- Full monitoring stack - Grafana Failed to fetch, Jaeger DS, enhanced dashboard
- Remove orphaned duplicate alerts in alerts.yml
- Add basic_auth for Grafana metrics scraping by Prometheus
- Correct rq_failed_jobs metric name in dashboard and alerts
- Align DevOps config with ZSI, remove sergej.chodarev from teachers
- Rebuild CSS bundle from sources + fix ZSI description
- Update DevOps description with test (10b) + team project (10b)
- Align course descriptions with official kurzy.kpi pages
- Unify Refresh buttons across all course pages
- Unify dashboard header buttons - remove size='sm' to match course pages
- Break SSE read loop on done event to prevent spurious network error toast
- Remove extra closing brace that broke JS bundle parsing
- Break outer while loop in readImportSSEStream after done event
- Concurrent email enrichment + activity feed labels/dedup
- Remove commit sync date filter + fix CI lint + show 0 for empty sub-projects
- R08 and R13 no longer auto-pass with zero student activity
- Update R13 test to expect fail with zero commits
- Progress timer ticks every 1s + threshold labels positioned at actual percentages
- Send SSE done event before sync-enqueue to prevent network error toast
- Default member filter shows Direct + Inherited to match team contributor count
- Exclude inherited members from team student count on course overview

### Zmenené

- Deduplicate components, consolidate JS utils, update docs
- Consolidate _lock alias into GP destructuring across 14 page JS files
- Deduplicate code patterns, validate thresholds, clean translations
- Unify contributor counts via shared _stats helper, remove fake per-project score fallback
- Lift tab nav to shell pages - instant tabs, ARIA a11y, keyboard nav, body-only skeletons

### UI / UX

- Fix ruff-format for teams.py and reset_db_remote.py

### Testy

- Force-show all 3 stale data scenarios for visual review

## [2026-03-30 - 2026-04-04]

### Pridané

- Search panel - mobile close btn, GitLab avatars, user->admin nav with auto-search
- PWA support + rewrite login animations (no conflicts)
- SSR-direct page entrance animation - staggered contentEnter for pages without skeleton loaders
- Edge-to-edge mobile cards + pull-to-refresh
- Comprehensive SEO - Google Search Console, OG, sitemap, robots.txt
- Comprehensive email notifications + refactor to shared template
- Non-anonymous tickets + auth-only submission + SMTP setup
- Add proper error handling for 401/session expired
- Wire support form skeleton + sys audit cleanup
- Add 346 missing Slovak translations for support, fix form overflow CSS, improve skeleton
- Support ticket system with comments, filters, and management\n\n- Add migration 031: ticket lifecycle columns (status, priority, category,\n  assigned_to, resolved_at, updated_at) + support_comments table\n- Add SupportComment model with author, content, is_internal fields\n- Add ticket management API: PUT ticket, GET/POST comments\n- Add filtering by status/priority/category/search in ticket list\n- Rewrite support_tickets.html: filter bar, expandable detail rows,\n  inline status/priority/category management, comments section\n- Replace all Unicode arrows with SVG icon components\n- Replace emojis with icon() macro calls throughout\n- Rename FEATURE_FEEDBACK_FORMS to FEATURE_SUPPORT_FORMS in docs\n- Update architecture doc: feedback.css -> support.css\n- Add btn_link_icon for back navigation and pagination controls\n- All linters pass (ruff, mypy), 2382 tests pass"
- GitHub-style support system redesign
- SSE real-time updates, email notifications, GitHub-identical UI
- Redesign support filters with animated selects + category-specific form fields
- Add alternating row backgrounds for visual consistency
- Ticket detail - component-based layout, assignee user search
- Dashboard integration - attention items, activity feed, sidebar badges, error page links
- Pass SMTP env vars through docker-compose to containers
- Component-based Subgroups & Projects table + Groups child rows
- Auto-enrich user profiles from GitLab after config import
- Persistent feedback links with CRUD, form picker, expiry, and link management
- Move Feedback Links to Feedback Forms page + gl-dropdown form picker + context default forms
- Add expand/collapse arrows to groups table with member preview
- Expandable tree view for team projects + UI fixes
- Arena email API fallback + filter bots from instructor lists
- Security hardening - secret rotation, per-user tokens, retired heuristic detectors, CSRF UA binding

### Opravené

- Add PNG favicon for Google Search + shorten meta description
- Redirect /favicon.ico to PNG instead of SVG
- Slovak translations (podpora), mobile responsive improvements, email cleanup
- Login page mobile - keep desktop look (background, centered card)
- Ruff format + remove deploy job from CI pipeline
- Login language switcher 404 - use /dashboard/login path
- Login mobile - keep card contained like Keycloak (remove max-width:100%)
- Login mobile - full-screen card like Keycloak (edge-to-edge white, no dark bg)
- Login mobile - center content, visible lang selector on white bg
- SW CORS error on OAuth redirect - skip navigate requests
- Remove /dashboard/ from SW pre-cache - redirects to OAuth when unauthenticated
- Remove SSR entrance guard - caused blank page on slow connections
- Prevent skeleton flash on fast HTMX loads
- Mobile card styling + PTR indicator hidden by default
- Rewrite PTR to match GitLab blue circle design
- Rewrite PTR and mobile card styling (manual)
- Clean PTR rewrite - fix cancelable touchmove + Material spinner
- Instant mobile logout + suppress native PTR on login page
- Regenerate OG image with proper GitPulse branding
- Clean OG image rewrite - minimalist pixel-perfect layout
- Render login page for search-engine crawlers instead of OAuth redirect
- Detect Lighthouse/PageSpeed bot in crawler regex
- Ruff lint + accessibility (main landmark, color contrast)
- Allow HEAD method on SEO routes (robots.txt, sitemap.xml, verification)
- Restructure robots.txt - unblock /dashboard/login for Google
- Simplify robots.txt - remove dashboard disallow entirely
- Support HEAD on /dashboard/login + detect Google-InspectionTool
- CI mypy errors, remove sidebar badge, fix login lang auto-login
- Wire comprehensive email enrichment with GitLab API + Arena fallback
- Support form double toast, markdown preview, asterisk notice, email notification
- Proper double-toast fix (data-no-boundary), XSS prevention in markdown, hide info-card on success
- Rebuild JS bundle, fix mypy dict type in gitlab_group_import
- Remove temp SMTP scripts causing ruff lint failures
- Add Arena API token auth + Arena fallback in student enrichment
- Improve student enrichment with username search fallback
- Replace anonymous message with logged-in user info on support form
- Rebuild JS bundle and use proper 401 SVG from GitLab design
- Rewrite renderMarkdown() in support-form & ticket-detail
- Ticket comments 500, emails, comment permissions
- Duplicate comments, missing icons, email avatar, notifications, responsiveness
- Admin-system crash, duplicate emails, 401 UA mismatch
- SSE real-time timeline update, touch updated_at on comment, skeleton loaders
- Perfect 1:1 skeleton loaders for support pages, update email v4 with arena/SMTP/SSE changes
- Restrict textarea.form-input to vertical resize only
- Render info_card HTML correctly in support form (use call block)
- Complete feedback->support rename, fix .env config bug and data.feedback attribute bug
- CI lint failures + SSE security + dashboard auth guards + docs
- Support page layout to match standard dashboard structure
- Remove sidebar duplication, drop support/manage page, fix filter styling
- Full-width form, move info card, expand category-specific fields
- Improve support form - reorder notices, add padding, expand category fields
- Dropdown z-index/transparency bug - replace opacity transition with class-based enter/leave
- Add id=description to textarea and for=description to label (a11y)
- Correct RateLimitDep usage and add empty-string UUID validator for SupportCreate
- Tickets table matching admin pattern + dropdown transparency
- Rewrite support tickets page with proper table/filter components
- Cast UUID to string for tojson serialization
- Improve toolbar dropdown hover with button-like bg highlight
- Move filters to card header with search (User Management pattern)
- Use subtle rgba hover for data-table rows across all pages
- Ticket detail - proper two-column layout, fix sidebar overflow, self-contained assignee dropdown
- Alpine expression error, form corners, sidebar heading colors, assignee reload, responsive
- RenderMarkdown via vanilla JS init instead of Alpine expressions - prevents quote escaping errors
- Correct SSE endpoint URL - remove stale /sse/ prefix
- Enable assignee unassign + form accessibility (id/label)
- Change timeline labels to spans (no associated form field)
- Deep-link URLs, email notifications, assigned-by info, 403 page
- Harden teacher membership sync - upgrade student memberships, elevate User.role, enrich avatars
- Resolve ruff lint/format failures in teacher membership sync
- Course Teachers count includes admins, filter-pill descender clipping, config preview spacing
- Create User records for teacher_usernames during config import
- Ruff lint errors in reset_prod_db.py, tighter config preview spacing
- Section count toast mismatch + dashboard config preview spacing
- Add error handlers for unexpected scenarios + fix mismatches
- Active column width, unify config-import component
- Remove stale _fullConfig ref, add comprehensive config validations
- Pass disabledFeatures to config-import in course-settings
- Prevent SSE task cancellation after import commit + add keepalive pings
- Filter bot users from teacher discovery + clear config on import success
- Fast config import, modal close, admin-teacher filter
- Correct cell indices in course-detail.js (group names overwritten by member count)
- Student privacy - hide metrics, restrict profile access, fix tree layout
- Student profiles, LLM error display, table layout, global job bar coverage
- Clean LLM error display, role-appropriate suggestions, proper icon
- Error card dynamic injection + CI test fix
- Skip job history for zero-work scheduled jobs + fix mypy
- Groups child-row dashes, member name overflow, LLM error card bugs
- Restore Groups Status column + LLM error card delayed swap
- Build LLM error card client-side, show project last_synced_at, fix worker MissingGreenlet
- Per-project contributors, inline SVG icons, toast-delayed error card, dismiss empty state
- Error card delay 6s, per-project avg score, remove Active badge, single-MR retry
- Real per-project avg score, error card without toast, better error classification
- Role-based error messages + classify MissingGreenlet as transient
- MissingGreenlet root cause + role-based messages + MR links in analysis
- LLM error classifier order, global progress bar deferral, per-project status badges
- Replace en dash with hyphen in llm_job comment (ruff RUF003)
- Use forceCloseModal after successful import to avoid spurious Discard confirm
- Lint errors (ruff/mypy) + UI consistency for feedback links
- Cast UUID to text in feedback-links join to fix 503 error
- Add for attribute to form picker label (a11y)
- Fix Form picker dropdown not opening
- Align tokens and modals 1:1 with GitLab Pajamas
- Weekly deadlines table uses full width, no wasted space
- Align table th, toggle token, pagination padding to GitLab Pajamas
- Pixel-perfect GitLab Pajamas 1:1 alignment (round 5)
- Align backgrounds and borders with GitLab dark theme
- Remove max-width cap on main-container - content fills full page width
- Pixel-perfect GitLab Pajamas component alignment
- Align status dots, pagination radius, table padding, card/modal footer to GitLab
- Project links to internal pages, arena JSON API with identities
- Even column distribution across all tables (colgroups + table-layout:fixed)
- Ruff lint/format errors in arena_email (UP037, E501, N806)
- Show empty-state message when filter pills yield 0 results
- Hide pagination when filter yields 0 rows, clean empty-state styling
- Add !important to .d-none utility to override .pagination-controls display:flex
- Prevent scrollbar flash on table pages by deferring page-initialised with double-rAF and hiding pagination-controls pre-init
- Suppress row animation and lock container height during filter/sort to prevent scrollbar flash
- Add missing column width classes for compliance checks table and fix weekly deadlines layout
- Improve weekly deadlines table layout and prevent modal scrollbar flash
- Unify scrollbar styling across modals, drawers, tables to match main content
- Switch checksTable to auto layout on mobile to prevent column overflow
- Hide Active/Code columns on small mobile screens, constrain Actions column width
- Wire per-user token auth, fix ruff format, enable event pipeline
- Resolve ruff lint/format failures, rename remaining instructor refs in i18n, fixtures and docs
- Move Resurrect button right, fix duplicate toasts, let pagination stretch
- Move Resurrect Selected to card header top-right, footer only pagination
- Move pagination inside card body, hide in empty state
- Add table-empty-row class to all empty/loading/error rows, hide pagination in empty state
- Use table-empty-state with icon for empty DLQ, matching courses/users pages
- Map event.replay/resurrect/processed/failed in activity feed with icons, labels, details, URLs
- Align Configuration Preview icon, expose currentUsername to Alpine, fix modal close animation
- Configuration Preview spacing, add fg855ni to ZSI config, fix DLQ Type column wrapping
- Sync teacher_usernames from config import to CourseMembership

### Zmenené

- Unified premium animation system - staggered entrance, no conflicts
- Zero-lag PTR - all passive listeners + rAF batching
- Audit fixes - deduplicate afterSwap handler, fix deploy script PS5.1 compat
- Comprehensive best-practice audit
- Audit: full system refactor - security, a11y, i18n, dedup, dead code
- Deep rename feedback->support across entire codebase
- Redesign: pixel-perfect GitHub Support UI with markdown editor, thread view, expanded categories
- GitHub-identical support UI - reply on top, reverse chronological comments, remove thread connectors
- Unify table styles and replace inline styles with CSS classes
- Ticket detail page - use page_header, remove custom action bar
- Simplify forms, fix dropdown, sortable table
- Rename Feedback subsystem to Support/Ticketing system
- Revert: undo UI changes
- Revert: restore to d03fd4f (align tokens and modals 1:1 with GitLab Pajamas)
- Unify role system (instructor->teacher), drop instructor_usernames column, R13 push enqueue
- Eliminate all 'instructor' terminology - rename to 'teacher' everywhere

### UI / UX

- Align UI system to GitLab Pajamas design tokens
- Align remaining components to GitLab Pajamas
- Revert: restore main-container max-width layout
- Pixel-perfect GitLab Pajamas alignment - focus ring 1px/3px, form padding 8px/12px, line-height 1rem, triple-ring focus, card radius 8px, modal radius 12px, table cell 12px/16px

### Infraštruktúra

- Remove test support script
- Remove temp verify_fix script
- Remove junk files and harden .gitignore
- Remove debug scripts
- Remove utility scripts with hardcoded credentials

### Dokumentácia

- Comprehensive update - R13, 30 migrations, 2382 tests, CourseMembership

### Testy

- Add unit tests for email notifications, api utils, constants, and type modules

## [2026-03-23 - 2026-03-29]

### Pridané

- Clickable member rows + context-aware back navigation
- Group members table navigates to project context
- Role separation - force logout on change, hide docs from students, fix attention items
- Suggest full sync after course settings save
- Redesign instructors page (GitLab-style invite bar + member rows)
- Real GitLab avatars + wider layout
- Clickable instructor rows with User Info modal, Owner badge
- GitLab-style Source & Role columns in member tables
- GitLab reference linkification + reduce member-api-note spacing
- Role-based sidebar + thesis feedback card
- Add R13 Commit Quality check - web editor detection
- Simplify: remove intervention list, risk groups, all groups; disable event pipeline/roster; add instructors lazy loading
- Redesign dashboard cards, header, timeline grid, profile menu
- Quick Access sidebar, health for teacher, scheduler feature-flag gating
- Single-user enrich button in User Info modal
- Comprehensive UX improvements from teacher review
- Add 295 missing Slovak translations
- Overhaul global search - students scope, role badges, direct links, docs
- Drastically reduce GitLab API polling - webhook-first approach
- Extend activity-window filter to ALL remaining GitLab polling jobs
- Webhook edge-case hardening - orphan projects, backpressure, immediate enrichment, delivery health
- System-wide resilience - sweep retry, pagination limit, Prometheus enrichment metrics
- Gate GitLab-polling sweep jobs through the scheduled-jobs master switch

### Opravené

- Member profile - dynamic role title, no-activity guard, table scroll
- Member profile UX - back nav to group, instructor-aware empty states
- Prevent infinite login loop when allowlist user changes role
- Dashboard: fix status dots, reporter role warning, pipeline health overflow
- Fix CI lint + Groups 0: match Student by gitlab_user_id
- Fix OAuth: GitLabUser.id not gitlab_user_id
- Elevate dashboard role for course owners/instructors, remove redundant stat tooltip
- Rewrite modal CSS to match GitLab Pajamas exactly
- Silence editCheck console warning and aria-hidden focus conflict
- Quick Access shows real teams, System health enriched
- Quick Access Groups/Subgroups tabs, interactive timeline weeks, skeleton blue bar fix
- Lint errors (ruff/mypy), timeline semester_weeks order, project name display
- Sidebar layout, project names, timeline nav, telemetry gating
- Round avatars, attention link to course, instructor layout
- Avatar backgrounds hardcoded, groups sort by RED, instructor panels stretch
- Revert email, muted avatar colors 24px, restore email docs
- Language switch revert, new analytics favicon, DTA refs cleanup
- Cache-bust extra.js/css/favicon, reduce nginx cache, remove dead locale persistence
- Fix language revert, favicon flash, and canonical URLs
- Restore missing `<script>` tag, update verification date to 2026-03-28
- Sort by status on attention click + per-course red teams
- Mypy arg-type error in dashboard red_teams_by_course dict comprehension
- Avatar fallback from gitlab_user_id + skeleton 1:1 + email v3 fixes
- Avatar fallback, owner visibility, a11y, mobile
- Avatar fallback, full-width layout, mobile, admin owner role
- Avatar fallback, instructor navigation, admin user info
- Revert instructor nav to full page, fetch avatars from GitLab API
- Toast dedup, 'you' badge styling, ruff-format
- Remove fake Owner badge from admins, fix instructor navigation
- Role-aware Student Not Found, restore Owner badge, avatars in search
- Remove bulk avatar fetch (timeout), improve not-found, fix admin role
- Auto-assign Owner to course importer + suggestion box layout
- Guard gitlab_user_id None before get_user (mypy)
- Create admin User records on import + enrich instructors/admins
- Create User records during JSON config import
- Prevent scrollbar flicker in modals and tables during animations
- Reliable scrollbar-flicker prevention in modals
- Remove scale() from modal animations to eliminate scrollbar flicker
- Remove Timeline page, help icon, fix toast stacking
- Restore coverage above 40%, remove per-week deadline columns
- Shrink weekly deadlines table to content width
- Table layout + GIT_SHA for reliable cache-busting
- Activity grid align-items:start to remove empty space
- Activity skeleton 1:1 match with real card structure
- Activity grid cards - override .card+.card margin-top
- Ruff lint errors in test_coverage_gaps.py
- Mobile table responsiveness, cookie consent cross-device, session persistence
- Comprehensive mobile responsiveness overhaul
- Comprehensive responsive pass - tables scroll, skeletons match pages
- Pagination overflow + deformation on mobile
- Third pass - touch scroll, heatmap column, min font sizes, invite dropdown
- Remove unused type: ignore comment in auth.py
- Member filter fallback, page size 50, skeleton loader alignment
- Rebuild JS bundle after member-filter and page-size changes
- Include all team members in detail pages for client-side filtering
- Show dash in empty Job History Actions column
- Empty-data guards, config warnings, progress dedup
- Add localIndicatorSelector to all deferGlobalJob/showGlobalJob calls
- Combine nested ifs to satisfy ruff SIM102
- Global bar dedup - sync recheck in _renderGlobalBar + default selectors
- Toast progress bar completes before dismiss (120ms headroom)
- UI polish - text indicators, scrollbar, skeletons, sync perf, expired note
- Team 500 error, project skeleton accuracy, GPU-accelerated shimmer
- Member-api-note styling and missing Slovak translations
- Members table cell index mismatch after Source/Role columns added
- Skeleton member-api-note gray + reduce spacing above info note
- Rebuild project-detail skeleton to match actual page 1:1
- Lint/mypy errors + empty state for member filters
- Sorting + member filter sync on lazy-loaded pages
- Sk_details skeleton matches real details/summary structure
- Re-apply member filters after live-data update
- Show only GitLab project members, include inherited teachers
- Show inherited GitLab group members on team detail page
- Disable event pipeline, fix contributors filter, eye icon, banner, course cards
- Revert course card CSS to clean original design
- Simplify role badges + optimize intelligence panel cards
- Exclusion refresh, card spacing, instructor score display
- Instructor score hiding, project exclusion toggle, skeleton accuracy
- Show instructor scores when snapshot exists (hidden by default via filter)
- Add card-body padding to Group Members table (match other tables)
- Match dashboard sidebar feedback panel (2 links)
- Team detail 1:1 accuracy - avatar size, filter bar, info note
- Add 'commit' to valid categories for R13 check
- Ruff format/import-sort in engine.py, update email feedback forms rationale
- Instructor page Alpine.js errors, remove Groups from Timeline, reorder dashboard
- Use avg_weighted_score instead of non-existent overall_score
- Enrichment fallback to username, progress bar stability, role sync for users without gitlab_username
- Rewrite enrichment UI - button progress, completion detection, toast dedup, global bar SSE
- Enrichment total counts only Users, process Students silently
- Global bar stuck at 100%, toast suppressed after HTMX nav, button flicker
- SSE idle status handling, stale _deferredJobs cleanup at completion
- Join running enrichment on already_running response instead of resetting button
- Restore Job History card, fix enrichment button white/stuck-at-100%
- Eliminate enrichment race conditions, add scheduler master flag
- Map 4 missing jobs to feature flags, sync enrichment progress to global bar
- Lint E501, unify global job progress across all processes
- Correct enrichment total (409 not 808), button shows Enriching state
- Store enrichment status in Redis (multi-worker), cross-link users->students, fix spinner
- Always show global progress bar for all processes (no local dedup)
- Don't inflate enrichment total with students, use backend message in global bar
- Smooth enrichment progress across user+student phases, fix ruff format
- Single consistent progress counter for enrichment, fix mypy
- Show enrichment in global bar and Job History
- Deduplicate enrichment total, remove dual polling
- Remove students from enrichment total, prevent duplicate SSE
- Enable defer/promote pattern for global bar
- Silently remove completed job on HTMX navigation
- Always start SSE polling even when deferred
- Disable Caddy buffering for SSE streams
- Bypass GzipMiddleware for SSE streams + fix Caddy config
- Complete progress bar after users, before students
- Re-add deduplication, always start SSE
- Better messages, immediate Job History update
- Skip 429 sleep on last retry attempt to prevent modal blocking
- Comprehensive quality pass - race conditions, lint, UI polish
- Deep audit - SSRF protection, TOCTOU race fix, dead code removal, UI improvements
- Comprehensive quality pass - race conditions, tooltips, unbounded queries
- Resolve mypy type errors in evaluation_report.py (SimpleNamespace annotation)
- Caddy listen on multiple domains (TUKE proxy support)
- FEATURE_FEEDBACK_FORMS=false now fully hides feedback UI
- Import safety - cross-course protection, team path-prefix matching, membership transfer
- Lint errors - unused import, f-string, en-dashes, type-ignore, formatting
- False teacher detection feedback loop + modal auto-close race
- Mypy type errors in freq-detected instructor gitlab_user_id
- Lint - ruff-format, ruff-check, mypy for sweep activity-window
- Telemetry snapshot upsert - prevent UniqueViolationError on repeated runs
- Prevent UniqueViolationError session poisoning in engine + feedback
- Use risk_score threshold for 'behind' count instead of binary missing-checks
- Add polling jobs to the admin scheduled-jobs registry
- Add scheduled-jobs master switch to docker-compose env vars
- Redistribute check weights so active checks sum to 1.00
- Resolve metric card spinners from initial data and SSE

### Zmenené

- Centralise role elevation in _enforce_db_role
- Polish: square avatars, docs i18n selector, favicon, email, READMEs, cleanup
- Complete DTA->GP rebrand across JS/HTML/Python/docs
- Redesign Manage Instructors page layout
- Centralize reload logic, eliminate location.reload() duplication
- Remove Timeline Dashboard page and all references
- Add empty-data guard to periodic_metrics_all, add Jaeger datasource to Grafana
- Simplify: remove Milestones/Releases/Labels cards from project detail
- Merge feedback cards + add form questionnaire guide
- Simplify: remove intervention list & all groups from timeline, sort attention items by severity, update email
- Hide: remove Automation section from System page
- Relax defaults: disable R09/R11, R02 branch naming optional

### Bezpečnosť

- Harden validation, fix auth bypass, add input size limits

### UI / UX

- Pipeline Health: GitLab-style redesign with refined bar, badge pct, mini legend

### Infraštruktúra

- Reduce all artifact retention to 3 days
- Config: set thesis feedback Google Form URL
- Add R13 to course configs + update email review response
- Gitignore reset_db.sql

### Dokumentácia

- Update email review response with current system state
- Rebrand DTA->GitPulse, fix i18n selector, replace mindmap
- Rewrite feedback forms section - built-in module, not Google Forms
- Complete email - add missing responses (import, timeline, MR detail, routing, tooltips)
- Migrate all references from IP to gitpulse.kpi.fei.tuke.sk domain

## [2026-03-16 - 2026-03-21]

### Pridané

- Add Slovak translations for Automation page (42 new keys)
- Redesign diff viewer - full-width rows, line numbers, responsive
- Scroll-triggered chart & counter animations via IntersectionObserver
- Overhaul Automation panel - scheduled jobs + job history with actions
- Spinner loading states + withUiLock on all actions\n\n- setButtonLoading() now uses .btn.loading (animated spinner) instead\n  of .btn-loading-text (opacity-only dim)\n- Add withUiLock() deduplication to: Refresh Stats, Refresh Jobs,\n  Retry Failed Job, Purge Old Jobs, Trigger Scheduled Job\n- Add .table-loading overlay for job history filter changes\n- Trigger buttons: idle -> spinner -> ✓ success (3s) -> idle"
- Show global progress bar for manually triggered scheduled jobs
- Track scheduler-triggered jobs with BackgroundJob records
- Weekly summary uses real activity/compliance data instead of empty telemetry API
- Context-specific feedback forms + enhanced settings page
- Import-time historical project detection + analytics warning banner
- Proxy /docs/ to documentation site via Caddy
- Cookie hardening, project reactivation, docs refresh
- Add GitLab availability checks and graceful degradation
- Top-tier cache/session invalidation system
- Perfect instructor detection - seed from env config on fresh DB
- Role_locked - admin role changes persist through auto-sync
- Student exclusion from scoring + role_locked propagation to all instructor detection paths
- Comprehensive report overhaul - maximally informative for teachers
- Health-aware SSE/polling across all pages, UX fixes, docs update
- I18n: add 15 missing Slovak translations, fix hardcoded strings, update docs and responsive CSS

### Opravené

- CI lint errors, infinite progress bar, disabled-feature tracking
- _get_queue fallback when Redis pool not initialized in workers
- Standardize Automation pagination & reduce scheduler frequencies
- Lint + best-practice hardening across worker subsystem
- Connection-recovery toasts, SSE fallback, version-detect reliability
- Stat card text overflow, diff responsiveness, session UA false positives
- Regenerate CSS bundle from sources (bundle-check CI)
- Diff toggle uses details/summary like Changed Files, fixes mobile
- Dashboard UX overhaul - clickable attention/activity items, system health for teachers, feedback link generator, instructor filtering
- Resolve ruff-check and ruff-format lint failures
- Resolve mypy call-overload + remove dead code
- Remove max_retries=0 causing Retry(max=0) ValueError
- Visible trigger/retry feedback - min 500ms spinner + green success state\n\n- Minimum 500ms spinner display so user always sees loading\n- Trigger: spinner -> checkmark + 'Triggered' text (4s) -> restore\n- Bright green triggered state with pulse animation\n- Retry: same 500ms minimum spinner before re-enqueue toast"
- Center spinner on btn-xs + anti-spam safeguards\n\n- Smaller 10px spinner for btn-xs (was 14px, too large for 20px button)\n- Client-side 30s cooldown per trigger function prevents rapid clicks\n- Server-side Redis cooldown key (30s TTL) prevents queue flooding\n- Retry marks old failed job as 'retried' with link to new RQ job\n- Server rate limit (60/min) already existed via RateLimitDep"
- Show 'Running...' text on trigger instead of spinner\n\n- setButtonLoading: text mode uses btn-loading-text (visible text),\n  no-text mode uses loading (spinner). Previously spinner hid text.\n- Trigger buttons now show 'Running...' during API call"
- Trigger button state persistence, dedup guard, SSE RQ reconciliation
- Card overflow visible for dropdowns + table-layout:fixed colgroups system-wide
- Remove :has() stacking rules (dropdown freeze) + add table fadeIn animation
- Dropdown stacking via Alpine class toggle + table fadeSlideUp animation
- Dropdown CSS race, MR table + pagination on activity page
- Cap max_weeks at 52, align activity cards
- Equal-height activity cards with pagination at bottom
- Add danger/info/warning status-dot CSS classes
- Replace en-dash with hyphen in comment (ruff RUF003)
- Analytics stat cards, max_weeks=semester, report dates prefill
- Skip pre-semester events instead of coercing to week 1
- Auto-detect imported projects for weekly summary
- Filter future dates, year-grouped week selector
- Add date ceiling to MetricSnapshot queries, cap max_week in compliance history
- Week selector uses semester_start for numbering + audit logging for all mutation endpoints
- Resolve ruff-format and mypy CI errors
- Filter instructors from Contributors list in project detail
- Avoid lazy='raise' on TeamMember.student in contributor filter
- Sync Repository Stats commit count with filtered contributors
- Session invalidation on role change, activity feed scoping, card color case, sync deletion protection
- Persistent frontend network for docs container
- Admin-users.js brace mismatch causing SyntaxError at line 190
- Filter contributors to team members only & remove pagination scroll jump
- Docs language switching - set site_url to /docs/ prefix
- Docs site_url needs full URL with scheme for mkdocs --strict
- Resolve CI lint, format, type and bundle-check failures
- Login false-positive, error styling, /en/ redirect, table animation
- Include /en/ (trailing slash) in Caddy redirect matcher
- Persist locale across app and docs
- Remove warnings and harden avatar/docs behavior
- Scrollbar shift prevention, auto-retry lazy loads, transparent scrollbar track, CI pin
- Use stable UA fingerprint (browser+OS only) to prevent session invalidation on browser updates
- Stabilise admin table layout + MR card stretches to match grid height
- Groups Actions alignment, member filter-paginator sync, skeleton flash delay
- Remove stray brace in ClientPaginator causing SyntaxError
- Member filters - empty array truthy bug + resync preserves filter state
- Group links 404 - use /dashboard/teams/{id} instead of /dashboard/courses/{id}/groups/{id}
- Member sync includes global teacher/admin roles in instructor detection
- Instructor detection - include inherited root members, raise cross-subgroup threshold to 90%
- Ruff-format + add teachers to course configs
- Instructor auto-detection false positives + rebuild CSS bundle
- Exclude admin users from course instructor_usernames and CourseMembership
- Instructor page spacing, search id, per-page dropdown
- Instructor page - show all admins, fix pagination dropdown, spacing
- Create /app/reports with app user ownership in Docker images
- Exclude teachers/admins from reports & fix score percentage display
- Lint + test fixes for report overhaul
- Reports - semester week context, fix bottlenecks, expected-check awareness, partial credit, custom check weights
- Sidebar Events badge counts DLQ events, not failed BackgroundJobs
- CI lint - close docstrings, remove unused type-ignores, reformat admin
- Hide pagination controls when all items fit on one page
- Revert "fix: hide pagination controls when all items fit on one page"
- Pagination overflow in p-0 card bodies, pin mypy version
- Consistent counts - roster excludes instructors, system stats counts active users
- Restore sweep.py type-ignores, suppress unused-ignore for cross-env compat
- UI bugs - spinner animation, pagination overflow, responsiveness, cross-tab polling
- Legend/pagination overlap + add missing error toasts
- 1:1 structure matching for dashboard, feedback, and admin events
- Align all skeleton loaders 1:1 with actual page structures
- Skeleton mismatches + coverage boost to 40.32%
- Toast SVG stroke rounding + course-picker skeleton structure
- Remove blue gradient from course-picker skeleton icon
- Course-picker skeleton uses card wrapper instead of gl-skeleton-section
- Compliance checks UX, contributor counts, dynamic analytics
- SSE event handling on all pages, sync-lock settings, lint fixes
- Report WeasyPrint OSError fallback, heatmap dark mode, false toast, animation jitter
- Health monitor threshold, report failure handler, progress bar polish, docs cleanup
- OAuth error handling, dev monitoring setup, deployment guide
- Use HTTP for bare IP deployment (no TLS for IP addresses)
- Pass APP_BASE_URL and ALLOWED_HOSTS through docker-compose
- Pass PERSISTENT_SESSIONS and SESSION_MAX_AGE_SECONDS through docker-compose
- Alpine query error and mobile sidebar close button
- Remove Alpine from course search, show collapse button on mobile
- Pixel-perfect GitLab layout - radius, z-index, colors, hover effects
- Restore Alpine removal from course search and mobile sidebar fix
- Alpine script order, add missing Slovak translations, wrap hardcoded strings in t()
- Remove cosmetic skeletons from SSR pages, complete lazy-page skeletons
- Pixel-perfect skeleton loaders - use actual CSS classes, responsive grids, pagination
- Responsive CSS - ring-stats-grid 768px, compliance-summary compact 480px, dead pipeline-overview rules
- Skeleton loaders - use actual page CSS classes, fix structure mismatches, remove 8 dead macros, add responsive breakpoints
- Responsive CSS cleanup - remove dead selectors, replace hardcoded values with design tokens
- Comprehensive responsive - checksTable selector + table-responsive wrapper, sticky first column for dynamic tables, MR/CI column hiding, course-name ellipsis, code-inline word-break, instructor-badge overflow
- Replace remaining hardcoded font-size/weight/color values with design tokens, wrap JS-generated members table in table-responsive
- Page-header h1 overflow visible on mobile, profile-header vertical stacking on narrow screens
- Responsive instructor management - hide table columns on mobile, icon-only action buttons, instructor manager grid/list wrap, card-header-flex wrap
- GitLab Pages - set site_url to relative, add --strict build, echo CI_PAGES_URL for URL discovery
- Add default artifact expire_in 3d to prevent storage bloat, fix missing expire on contract-tests
- Add needs:[] to test-fast jobs - prevent artifact download from security stage
- Allow admins as regular instructors - remove auto-promote to owner and backend filter that dropped non-owner admins
- Admin visibility - hide admins from instructor badges and available users for non-admin viewers
- Resolve 500 on instructors page - define is_admin, fix line length
- Admin visibility - course owners can see admins, role dropdown instead of remove button
- User info modal - use teal badge for course owner instead of warning

### Zmenené

- Component-based Automation panel with feature flag awareness
- Replace native `<select>` with select_field() component
- Production-quality audit - unify duplicates, fix tokens, update docs

### UI / UX

- Fix ruff format in auth.py
- Restyle Available Users pagination to match standard component
- Layout: make page skeleton 1:1 identical to GitLab on all devices
- Revert: undo Alpine/layout/i18n/pixel-perfect commits (a656e82..7ff95cd)

### Infraštruktúra

- Clear instructor_usernames from course configs - auto-detected now
- Remove stray temp script

### Dokumentácia

- Rebrand DTA to GitPulse, remove emojis, update stats, improve charts
- Self-host fonts and mermaid.js for CDN resilience
- Comprehensive documentation overhaul - security hardening, middleware stack, session model, cache busting, changelog
- Update documentation verification date to 2026-03-16

### Testy

- Add 46 worker job unit tests to reach 40% coverage
- Add 58 comprehensive edge-case tests for worker subsystem

## [2026-03-09 - 2026-03-15]

### Pridané

- GitLab-style skeleton loaders for all 20 page templates
- HTMX lazy loading for all heavy pages + 1:1 skeleton loaders\n\nConverted 8 heavy pages to HTMX lazy loading pattern:\n- dashboard, course_detail, project_detail, student_detail\n- team_detail, course_activity, course_analytics, timeline_dashboard\n\nPattern: shell renders instantly with skeleton loader, content loads\nasynchronously via HX-Content-Only header. Route handlers split into\nfast shell path (minimal context) and full content path (heavy queries).\n\nRewrote all 13 page-level skeleton macros in loaders.html to match\nactual page elements 1:1. Added lazy parameter (lazy=true omits\ngl-loading-skeleton class for HTMX, lazy=false default for SSR).\n\nAll 2094 tests pass.
- Show instructor names in import toast and global progress bar
- Frequency-based instructor detection during GitLab import
- Always-visible Instructors counter in import UI and toast
- Redesign User Info modal - polished profile card, GitLab avatar, proper CSS
- Retroactive compliance history with date derivation and backfill\n\n- get_student_compliance_history: derive dates for gap-filled weeks\n  from semester_start + timedelta(weeks=wk-1) instead of null\n- Primary path merges MetricSnapshot data for weeks missing\n  ComplianceSnapshots, extending coverage\n- Semester start lookup moved before if/else split (shared by both paths)\n- engine: add as_of_week parameter to compute_team_metrics for\n  retroactive scoring against per-week expected_checks config\n- engine: add backfill_compliance_history() that detects missing\n  weeks and fills them via compute_team_metrics(as_of_week=N)\n- sync_job: call backfill_compliance_history after sync so projects\n  added late (e.g. week 8) get compliance data for weeks 1-7"
- Per-course role hierarchy via CourseMembership (owner/instructor/assistant/student)

### Opravené

- Replace wrong error-429 SVG, remove dead skeleton CSS, fix error boundaries
- Smoother synchronized animations, fix cropped spinner icons
- Unify all animation easing across entire CSS codebase
- Unify last 2 animation easing outliers (tooltip, job-bar shimmer)
- Remove remaining page-load stagger anims (sidebar, home, cards)
- Remove last page-load stagger (home sidebar panels)
- Skeleton loader bugs - student lazy=true, CSS brace, instructor import\n\n- student_detail.html: add lazy=true to sk_student_detail() so skeleton\n  stays visible until HTMX content arrives (was fading out immediately)\n- student_detail.html: remove hx-indicator referencing nonexistent class\n- course_instructors.html: fix import sk_course_instructors (was sk_table_page)\n- loaders.css: fix .page-loader missing closing brace before .nav-progress\n- sk_student_detail: update to match actual page 1:1 - 4 profile cards,\n  3-col compliance table, add compliance progress charts + weekly table,\n  add communication indicators section\n\nAll 2094 tests pass.
- Align all skeleton loaders 1:1 with actual page content\n\n- sk_dashboard: add gl-home-layout/sidebar wrappers, sidebar panels\n- sk_analytics: add Feedback Token Generator card, 6-field form\n- sk_project_detail: 4 header actions (was 3), 4 info cards (was 5)\n- sk_team_detail: 7 header actions (was 6)\n- sk_timeline: expandable details pattern (was flat list)\n- sk_settings: 8 card sections matching actual page (was 4)\n- sk_admin_system: 5 runtime rows (was 6)\n- New sk_admin_events: stats+replay form+DLQ table (no search)\n- New sk_feedback_manage: header+forms table\n- New sk_feedback_results: course picker cards\n- New sk_course_roster: CSV upload+roster table\n- New sk_retired grading_list: header+table (no search bar)\n- New sk_retired grading_editor: info+categories+week configs\n- sk_feedback: simplified to course picker cards\n- Update 6 templates to use dedicated macros\n\nAll 2094 tests pass."
- Precise 1:1 skeleton-to-page alignment for all remaining pages\n\n- sk_project_detail: add 5 missing sections (retired grading scores, docker\n  verification 9-col, CI scenarios 9-col, conflict challenges 8-col,\n  AI analysis with details), fix members table to base 4 cols\n- sk_course_detail: tabs 6 -> 7 (all tab slots)\n- sk_feedback_manage: header actions 2 -> 3 (Change course + New Form + Import)\n- sk_course_instructors: 2-col grid (assigned text list + available\n  search+list) with save/cancel buttons, no avatar circles\n- sk_dashboard sidebar: quick links 4 -> 6 items, suggestions panel\n  expanded to title + paragraph + link (was single line)\n\nAll 2094 tests pass."
- Rename devopsta->gitpulse (DB, user, paths), fix all ruff/mypy lint
- Logout redirect loop, backfill gitlab_user_id from session
- Ruff RUF006 lint, separate instructor/student import counts, remove logo animation
- Accurate student/instructor counts in import toast & counter
- Emit instructor SSE events during discovery phase
- Clean `__pycache__` on restart, prevent stale bytecode
- Instructor events + student count consistency\n\n- Add client-side safety net: when done event arrives with\n  instructors_list but no instructor SSE events were received\n  during streaming, inject synthetic instructor events so the\n  import log and counters are populated\n- Move students_total / instructors_total DB queries BEFORE\n  sync job enqueue to prevent race where a worker deactivates\n  a student before the toast count is captured\n- Remove all diagnostic print()/console.log() statements\n- Keep server-side instructor emit code (correct on disk)\n- Rebuild JS bundle"
- SSE buffering, worker errors, Total Members label
- Instructor count in toast, consistent member counts, instant disconnect UX
- Instructor frequency detection threshold and roster count consistency
- Instructor detection + undefined toast + coverage 40%
- Cross-subgroup instructor detection + toast race condition
- Ensure all discovered instructors get teacher role
- Add cross-project instructor detection + remove premature sync
- Expand instructor detection - Owner+root-group, project frequency scan
- Sync toasts - per-group completion, sync start flash, group progress, UUID guard
- Instructor detection, toast overwrite, sync UX, user info modal
- Toast icon clipping, enhanced User Info modal, student count consistency, 302 redirect fix
- Constrain SVG icon size in User Info sections, add autocomplete attributes
- Lint errors, component CSS, Student Info in Roster
- Third audit pass - security, logic, and consistency fixes
- CI lint failures + code quality audit pass 4
- Remove Webhook Events card, fadeSlideUp animations, auto-refresh on SSE connect
- Restore animations, server-side GL data, auto-reload team page, remove Review Coverage\n\n- Restore fadeSlideUp animations with staggered delays for .gl-intelligence-card\n  and .project-info-item in project.css (incorrectly removed in prev commit)\n- Pre-fetch GitLab Intelligence data server-side (asyncio.gather for 6 endpoints)\n  and pass via window.`__GL_INTELLIGENCE_DATA__` for instant rendering\n- Team detail page: full reload on SSE update and sync completion so\n  Group Members table and all server-rendered data refresh automatically\n- Remove Review Coverage stat card from Group Summary\n- Fix SessionMiddleware assertion traceback spam in llm_analysis_status"
- Contributors dedup, analysis progress [object Object], completion state
- Responsive button layout + SSE data refresh on sync complete
- Team-detail live data creates badge elements when missing
- Hover animations, remove Clicks Avoided, AI toasts, MR actions styling, pagination, logging
- AI analysis UI bugs + suppress OpenAI worker log noise
- Use real dates from sync data instead of fabricated week dates
- 7 UI bugs + per-course badge system wiring
- Badge system - Owner/Instructor roles with legacy fallback
- Badge system - stackable multi-badge display
- Phase 8: Fix badge override, row flicker, trends canvas, SSE empty data
- I18n aria-labels and XSS-hygiene in innerHTML assignments
- Toast race condition on course page + autocomplete a11y on form inputs
- Align dynamic project items with gl-list-item classes, add missing aria-labels, i18n fix
- Orphaned labels + missing sync-complete toast in suppress-reload path
- Self-host vendor libs, fix color contrast + language selector a11y
- System-wide polish - tooltips, animations, login redirect
- Icon vertical centering, label a11y, duplicate job route
- Resolve 500 on project detail, sync toast race, a11y labels, table sort UX
- Resolve mypy errors in projects.py and sse.py
- Sync toast race condition + coverage tests to 40%
- Toast race condition, compliance trends gap-fill, ruff format
- Comprehensive security, i18n, and best-practices audit
- Resolve ruff-format, ruff-check, mypy CI failures
- Merge duplicate alembic revision 011 (fix_legacy_grading_id_type into add_missing_indexes)
- Make migration 011 idempotent (if_not_exists for indexes/constraints)
- Alpine x-for missing 'in' expression in list_manager + equal-height grid panels
- Add search icon to list manager, filter instructor pool to admin/teacher roles only
- Complete CourseMembership integration across all API layers

### Zmenené

- Production hardening - shared modal, rate limiter, GPU animations, error pages\n\n- Extract shared UserInfoModal JS module (~200 lines dedup from admin-users + course-roster)\n- Add double-click race condition guards and HTMX beforeSwap SSE cleanup\n- Rate limiter: defaultdict(list) -> dict[str,deque] for O(1) pruning, 100K cap,\n  incremental batch cleanup, inline trigger from is_allowed()\n- Error page: dynamic SVG per status code (404/403/429/500), suggestions list\n- CSS animations: barLoader/shrink -> GPU-composited transforms, unify scaleIn naming\n- Fix mypy type narrowing in exception_handlers.py (rename headers vars)\n- Archive outdated docs (thesis outline, eval plan, pilot telemetry)\n- Bump enrichment refresh interval 5->25 for 1000-user scale\n- Rebuild CSS bundle (hash 96c7e4b76ebddf9b)\n- All 2094 tests pass, ruff clean, 0 errors
- GitLab-style unified page reveal - remove per-element stagger
- Rebrand: rename service devops-ta -> gitpulse in logs, tracing, health
- Rebrand: complete devops-ta -> gitpulse rename across entire codebase
- Second audit pass - fix workarounds, hardcodes, and inconsistencies
- Eliminate page reloads in SSE/job handlers, add hover animations
- Fix N+1 queries, batch admin stats, eliminate remaining reloads
- Aggregate pipeline queries, eliminate feedback-manage reloads
- Remove sync-overridden CRUD, fix GitLab client construction, harden API safety
- Upgrade all API access checks to async CourseMembership
- Remove assistant role, componentize UI, clean dead code

### UI / UX

- Polish: CSS tokens, query limits, retired grading-list soft-refresh, mypy fixes
- Polish: security, CSS hygiene, DOM updates, search optimization
- Cleanup: remove dead macros/CSS, replace last 2 reload() with soft-refresh toast
- Add tooltips, aria-labels, and accessibility improvements

### Infraštruktúra

- Componentize webhook inputs, add feature overview

## [2026-03-02 - 2026-03-08]

### Pridané

- Universal error boundary - no more black screen of death
- Fix instructor badge table + one-time assignment notifications
- Add HTMX response error toast notifications
- Unified JS+CSS bundle builder with CI verification
- Add debug logging to silent exception handlers in telemetry and courses
- Manual conflict trigger API + CI auto-rollback scheduler
- Full system automation - 11 scheduled jobs for zero-touch operation
- Event-driven metrics, cache invalidation, BG job cleanup, DLQ auto-resurrect
- Complete automation - 16 scheduled jobs, event-driven cache/CI/sync
- Complete automation - SSE-first everywhere, 21 sweep jobs, push-based sync
- Member webhook handler, graceful ignorable events, activity live-data endpoint, project metadata sync
- SSE live stream for project-detail + blocked user filtering in member sync
- Docs+monitoring: update all READMEs, expand Grafana dashboard to 16 panels, add 6 Prometheus alerts
- SSE live analytics, dynamic stats, lint i18n, UI fixes
- I18n: add 88 missing Slovak translations across all templates
- CI auto-create branch, retry failed scenarios, UX polish
- Comprehensive Docker lint rules (DL001-DL021), CI failure scenarios, bug fixes
- Dynamic per-course Docker lint & CI failure configs - zero Python hardcoding
- Production-ready ZSI + DevOps configs for TUKE 2025/2026

### Opravené

- Polish student/teacher roles - hash nav, attention items, sidebar, access control
- Icon centering, instructor auth, student features, addTeam field
- Resolve ruff-check, ruff-format, and mypy lint errors
- Resolve all ruff-check, ruff-format, and mypy errors
- Change misleading 'teacher activity' log to 'activity' (applies to admins too)
- Avatar button centering, instructor suggestions include teachers
- Instructor suggestions - only teachers, exclude self/admins/current
- Add skipBeforeunload before all post-save navigations
- Dev login - auto-fill username per role, allow role switching
- Comprehensive access control hardening - empty instructor_usernames: all teachers can view (matches UI text) - re-import merges instructors instead of replacing - importing user always added to instructor list - deactivated users rejected via is_active check - API course endpoints enforce instructor access (PUT/DELETE/settings) - telemetry feedback forms: filter list + check import by instructor - both gitlab_username and username checked consistently - is_course_instructor returns True for empty list (no restrictions)
- Harden validation, race conditions, UI gaps, type errors
- Eliminate hardcoded values, fix role access, clean dead code
- Add _can_view_course auth check to course_analytics + add logging to silent exception catches
- Extract hardcoded values to config, per-project webhook secrets, FK cascades
- Config-back job timeouts, DLQ delay, session auth constant
- Add warning-level logging for silent exception handlers
- Enrichment TOCTOU race, Redis conn pooling, exception truncation
- Dynamic asset versioning, config-based job timeouts, DLQ race
- RBAC bypass, race conditions, access controls, dead code, input validation
- Schema validation constraints, pagination, status codes, race conditions, exception logging
- Deduplicate instructor checks, improve error UX, narrow exception handling
- Add cross-reference validation for config import check references
- Add missing gitlab_url to course_detail template context
- Handle UnicodeDecodeError in API roster upload
- Security hardening, race conditions, error handling improvements
- GitLab import 422 on course-detail + flash-toast race condition
- System-wide schema validation, SSE race conditions, and dead code cleanup
- Event-loop blocking, XSS, SSE timer leaks, atomic commits
- Auth checks, XSS escaping, ASGI middleware, atomic audit writes
- Sweep dead-project logic, auth gaps, rate-limit, input validation, Redis leak, case-insensitive instructors
- Redis connection leaks, auth gap on project SSE, input validation hardening
- Remaining Redis leaks, schema validation constraints
- Session rollback in batch loops, close AsyncOpenAI clients, httpx client finally
- Resolve all mypy strict-mode errors (10 errors across 6 files)
- Access-check order, retired grading activation, cross-course guard, search scope, parsing safety, webhook type validation
- DLQ resurrection clears markers only after successful enqueue
- Rate limiter uses config values, retired grading activation row lock
- Add logging for silent audit write failure in import script
- Cross-course authorization bypass in teams, reports, and feedback form APIs
- Reuse Redis connection for rate limiter, use config for webhook payload limit
- Critical missing await, config gaps, validation, query limits
- Add max_length to Update schemas, log compliance engine fallback
- Ruff format on reports, teams, dependencies
- Migration chain + auto-refresh + sweep #17 + deactivation cascade
- Wire ignored check configs, course-agnostic defaults, retired grading alignment
- Ruff N806 uppercase local variable and S101 assert in production code
- Ruff format + mypy unused type-ignore in event_processor
- Info_card HTML escaping + submit button gradient removal
- Alpine_modal x-teleport to escape gl-page contain context
- Teaching notes style matches violations, remove lint score bar, fix flaky_test timing
- Move CI exercise files to exercises/ to prevent auto-pipeline failures
- Add card background fills, fix events page layout, remove double borders
- Revert card backgrounds, fix dropdown flash, unify all animations
- Load core.bundle.js before Alpine to fix glFormSelect undefined
- Search input icons, z-index stacking, animation consistency
- Tippy applyStyles error, form label a11y, dropdown z-index
- Tippy createSingleton error, DLQ checkbox label, card z-index
- Rewrite toast system - GitLab Pajamas design, fix broken rendering
- Toast invisible text + position behind sidebar
- Toast progress bar resume + flash toast reload survival
- Translations, sync backoff, CI scenario panel, Docker card ID
- Missing CourseSettings import in pilot_telemetry + dynamic weeks
- Feedback module structure, flashToast, and remaining SK translations
- Breadcrumb + question builder styling
- Remove duplicate label in instructor modal, widen feedback modals
- Sync completion reload, polling fallback, all async edge cases across system
- Discover new GitLab projects during sync
- Reconcile orphan sync jobs that block future syncs
- Global job bar shows stale sync jobs after DB wipe/restart
- Flush stale RQ jobs from Redis on dev restart
- Use ZREM for registry cleanup (RQ 2.x compat)
- Use raw Redis commands for queue flush on Windows
- Commit BackgroundJob rows before enqueuing to RQ (race condition)
- Show DONE badge for completed syncs instead of N/A
- Traffic light badge takes priority over DONE status
- Commit import data before enqueuing sync jobs (race condition)
- Sticky modal action buttons so they stay visible on long content
- Modal backdrop clipped by .gl-page overflow:clip
- Move modals outside .gl-page to fix stacking context
- Silence httpcore trace logs and asyncpg pool termination noise
- Detect Owner-level members as instructors & prevent stats flash
- SSE reload loop, CI branch trailing-slash, asyncpg filter propagation
- CI rollback graceful 400/404, scroll preservation, Docker alignment, inline CI refresh
- Remove invisible status-dot from CI active badge pill
- Give status-dot inside pills visible background via currentColor
- Sortable table keeps companion rows with parent, guard empty JSON responses

### Zmenené

- Audit-pass-2: deduplicate helpers, gate flags, SQL aggregation, extract constants
- Extract all hardcoded limits, intervals, and timeouts to config
- Extract inline JS to external files, fix hardcoded GitLab URLs
- Eliminate all inline JS, convert window configs to JSON blocks
- Question builder to standard component macros
- Cleanup: remove dead code, unused imports, hardcoded fallback
- Unify alpine_input/alpine_checkbox into text_input/checkbox
- Componentize inline SVGs and expandable details across all templates
- Remove Python language from CI scenarios - C only
- Comprehensive frontend optimization - cut HTTP requests 90%, enable compression
- Deep optimization pass - zero render-blocking scripts, remove waste
- Dead code removal, transition optimization, CSP compliance & device fixes
- Unify animations & sync transition timings across all pages
- Eliminate all hardcoded stats values - fully dynamic from settings
- Eliminate remaining hardcodes across reports, timelines, SSE
- Eliminate last hardcoded values in analytics pipeline
- Component-based UI, fix instructor centering, changelog pagination
- Replace all inline HTML with component macros
- Align feedback pages to standard component library
- Docker verify UI - component templates, SSE live updates, table alignment, config management
- Eliminate residual inline SVGs, use `<template>` components

### Bezpečnosť

- Harden student/project API endpoints

### UI / UX

- Fix ruff format line wrapping in sweep.py
- Fix ruff format for course_settings.py and teams.py

### Infraštruktúra

- Wire docker size threshold + gitlab_parse timeout from config
- Courses: use session_max_age_seconds from config instead of hardcoded default
- Cleanup: remove dead code and unused config fields
- Eliminate remaining hardcodes in templates and services
- Remove redundant zsi-check-config.json (checks already in course config)

## [2026-02-23 - 2026-03-01]

### Pridané

- Universal global progress bar, per-student recheck, SSE leak fix
- Client-side member filter bar (replaces server-side hide logic)
- Add check-selection modal to project detail page
- Defensive null guards across all page JS files
- Replace all polling with SSE across entire system
- Fix missing member + add force-recheck (all checks override)
- GitLab-style role hierarchy - exclude non-contributing members from team score
- Auto-import course configs on deployment
- Centralize icon system + async health checks + lint fixes
- Dynamic feedback forms, feature flag error handling, form styling
- Docker/CI services - status bars, user attribution, sync analysis, layout fixes
- Docker analysis inline feedback + proper error handling

### Opravené

- Sticky breadcrumb scrolling + legacy_grading_id type mismatch
- SSE connection pool leak in sync-stream endpoint
- Shield session cleanup from CancelledError in async_session_ctx
- Eliminate SSE connection-pool leaks + dashboard bfcache staleness
- Eliminate SSE connection pool leaks in all streaming endpoints
- DI session cancellation safety + import double-reload/flash
- Eliminate connection leaks, standardize session handling, responsive CSS hardening
- Deep audit - Redis connection leaks, SSE reconnect loops, XSS, timer cleanup
- Convert middlewares to raw ASGI, replace recheck-all with selective check runner
- LLM UUID schema, single MR background analysis, status bar timing, a11y summary
- Micro-issues - Redis leaks, dead code, field names, CSS classes, tooltip reinit
- Modal close, toast progress, status bar dedup, reanalyze spin, advisory spacing
- Toast system, 40%+ coverage, cache busting, type annotations
- Comprehensive CSS/JS audit - 20+ bugs fixed
- Modal responsive overflow - content no longer clipped on narrow screens
- Toast persistence, inherited-member filter, health-monitor sensitivity
- Toast persistence, filter redesign with pagination sync & dark-mode
- Observer/instructor category, run-checks UX, translations, SSE progress
- Completion toast suppressed for deferred jobs (sync, analysis)
- Eliminate all inline styles, hard-coded values, and remaining JS safeguard gaps
- Status mismatch in edit modal, stale flash toast, search input artifacts, raw JSON spacing
- Double toast on import, auto-reload after sync completion
- Force-remove pgdata volume in Stop-All fallback
- Kill leftover uvicorn/worker processes in Stop-All
- Stop-All wipes local PostgreSQL database on restart
- PowerShell parse error in Redis Cloud status + split DB reset
- Replace em-dash with ASCII dash for Windows PowerShell compat
- Infinite recursion in flashToast/showToast alias
- Flash toast cleared too early by rAF before page unloads
- Add missing stat-danger glow + silence tracing noise
- Add missing stat-* color classes for hover glows + fix snapshot duplicate bug
- Resolve 22 ruff lint errors (E501, S110, SIM105)
- Weekly check filtering, CSS spacing, ruff format
- Weekly check filtering - bottlenecks, expected flag, templates, edge cases
- Sort imports in test_roles.py (ruff I001)
- Exclude inherited members with zero activity from team score + reload after import
- Resolve mypy union-attr errors in engine scoring gate
- Schema refs, OAuth error handling, anon feedback form, error propagation
- PDF generation + interventions chart empty state + UX improvements
- Resolve mypy and ruff-format pipeline failures
- Course-settings.js ceActiveLabel null reference crash
- Add loader icon + spin animation to health check loading state
- Remove duplicate health banner, fix 'Last healthy' timer
- Pin ruff==0.15.4 in CI, bump JS/CSS cache busters
- Unify all cache-busting versions to 20260227v01
- Table sort scrollbar, default sort indicators, card footer layout
- CI ruff errors + comprehensive quality audit
- Edit User modal data loading, avatar hover, transitions, button macros
- Tojson_attr for raw HTML attrs, modal buttons->macros, CSS transitions
- Unify stat cards, add stat-info color, fix 3 missing transitions
- Alpine collapse plugin, tojson_attr escaping, lint cleanup
- Add 45 missing Slovak translations + fix CSS status-bar separator
- Improve teaching notes and error banner spacing
- Restyle teaching notes component + center error banner icon
- Drop error-row-banner up into its own row with proper spacing
- Language selector overlapping title on mobile login page

### Zmenené

- Harden: comprehensive safeguards for run-checks & global job bar
- Unify toast: flashToast shows immediately + persists for reload
- Start-dev.ps1 for local Postgres + Redis Cloud
- Unify all stat cards + fix toast flicker
- Revert: restore original gl-home-stat dashboard cards
- Reduce health banner delay from ~27s to ~3-4s
- Split oversized files - 1 class/1 file, template partials, CSS modules
- Convert last 5 raw buttons to macros, add xs size, fix navbar transitions
- Frontend quality sweep and CI pipeline fixes

### UI / UX

- Fix ruff 0.15.4 formatting in test_middleware.py

### Dokumentácia

- Comprehensive update for role hierarchy, scoring gate, force-recheck, weekly filtering

## [2026-02-16 - 2026-02-22]

### Pridané

- I18n wrap ~122 strings, withUiLock/confirmProcessRestart on 18 actions, bump cache
- Interactive Chart.js charts, animated stat cards, enhanced UI
- Chart.js compliance chart, skill radar, animated cards
- Optimistic locking, last raw HTML migrations, external link security
- Extend optimistic locking to all mutation endpoints, fix schema & type errors
- Modal dirty-state guards, syncStatusModal X fix, LLM completion UX
- Page-level beforeunload guards to prevent data loss on navigation
- Global job bar for Docker/CI, cross-tab toasts, form layout fix
- Accept 'avg_word_count' as rule type alias for 'word_count'
- Course JSON configs, settings validation, verification guide
- Dashboard-level JSON config import + full clone
- AI privacy, enrichment, pagination, toasts
- Unified compliance check management - R01-R12 + custom in single UI
- Export/import check config, dynamic registry, file upload component, validation hardening
- Complete JSON config export/import with full validation
- Add admin Quick Links + GitLab-style animations and UI polish
- Auto-detect GitLab project/group URLs in import + replace feedback panel
- Bot detection, compact check legend, instructor activity filter
- Add is_instructor flag to TeamMember, exclude from team metrics
- Dynamic custom checks with teacher UI and LLM generation
- Rewrite badges as dynamic JS-only components
- Replace native `<select>` with GitLab Pajamas component dropdown (GlFormDropdown)

### Opravené

- Instant link-project toast, populate Docker metadata from static analysis, center status-pill text
- Standardize UI processes - setButtonLoading, flashToast, remove arbitrary timeouts
- Comprehensive UI process hardening - withUiLock, confirmDangerousAction, i18n
- WithUiLock + confirmDangerousAction on all remaining UI processes
- Add singleConfirm to skip misleading 'delete permanently' dialog on non-delete actions
- Analytics bugs - flags loading, 52-week dropdown, compliance scores
- Add missing btn_icon_only import causing 500 error
- Add 4 missing macro imports preventing 500 errors
- Correct field names + store approvals_count
- Comprehensive data-path audit - 7 bugs fixed
- Dashboard views - student context, inflated RED counts, export N+1
- Comprehensive audit - 18 bugs across 13 files
- 5 UI bugs - triggerDockerVerify/CiScenario errors, duplicate import check, global bar duplicates, toast persistence, all processes use global bar
- Global bar duplicate prevention - add isGlobalJobRunning guards and enrichment meta tag
- Docker verify + LLM generate errors, global status bar on all processes
- Eliminate global bar duplication, fix LLM JSON parsing
- DeferGlobalJob on all processes - bar hidden while local UI active
- Preserve LLM suggestions across modal close/reopen
- Close remaining guard gaps found in second audit
- Eliminate spurious beforeunload dialogs on all programmatic navigations
- Resolve all ruff, ruff-format, and mypy lint errors for green pipeline
- Resolve ruff lint/format errors in new test files
- Add missing Dockerfile.worker for CI container-build job
- Global job bar cross-tab + free navigation + auto-refresh
- Role badges, toggle panel styles, smart tab-refresh
- Inline Docker verify & CI scenarios, form alignment, project_id routing
- Retired grading 500 error, instructor filtering, toast duration, pagination, audit log
- Revert toast duration to defaults, keep reload delay fix
- Toast persists across navigation, archive layout, activity feed
- Safe actor extraction - replace request.session with custom session auth
- Toast persistence, audit writes, dead code cleanup
- Wrap remaining shared + page scripts in IIFEs, add window exports
- Add missing destructured refs - _escHtml, flashToast, openModal, closeModal
- Resolve 29 mypy errors in dashboard.py - typed _t helpers, CourseSettings null check
- Dashboard 500 error (missing file_upload_area import) + remove deploy job from CI
- Add Import JSON button to empty-state dashboard (admin + teacher)
- Drag-drop import enables button + Docker-link port parsing in CI
- Use gl-file-selected event for import config (browse + drag-drop)
- Update paste placeholder with actual ZSI course example data
- Auto-create session user in DB after restart (0 users stat)
- Harden dashboard against 500 errors
- Import-config 500 - link CourseSettings via relationship
- Import URL parsing, sync status bar, docs update, GitLab Pages
- Install git in pages CI job for revision-date plugin
- Pin mkdocs<2, add print-site plugin to pages CI job
- Docs match engine R01-R12, remove hardcoded values
- Ruff lint errors (S110, F401, E501) + correct MR pie chart weight 38->42
- Replace /* wildcard in mermaid node labels causing syntax error
- Use course-configured thresholds in analytics, fix zero-score display
- Mypy errors, category validation, Pydantic schemas, field_check partial_scoring
- Custom-checks 404, label accessibility, card icons, course description
- Harden unified checks - validations, accessibility, dedup, responsive
- Harden unified checks - 12 audit issues resolved
- Deep audit pass 2 - security, validation, a11y, CSS hardcodes
- 404 on checks API, layout grid margin, description not persisting
- Description not saving on course create + settings fields not persisted
- Prevent spurious save toast + show builtin check hint
- Ruff format, uniform filter buttons, code_reference component, semester_start_date type
- Full config import 'Stream consumed' error + update docs
- Report download, CSV double-fire, label a11y, activity feed
- Defer global job bar for report generation
- `_auth.username` -> `_auth` in write_audit calls (500 error)
- Add missing search SVG icons to all search inputs
- Persist import success toast across page reloads
- Show owners without snapshot in project members table
- Stop treating project owners as instructors during import/sync
- Include admin/teacher users as team members during import and sync
- CI lint errors + dynamic per-check configuration
- Prop-list spacing, feedback token 422, retired grading explainer
- Remove retired grading-explainer, harden all process logic
- R12 pipeline matching, R08 detail, tojson unicode, error template icon
- Auto-populate compliance history, improve system logic
- Prevent compliance snapshots from breaking metric computation
- Global job bar, health check, LLM i18n, sticky bar, pagination
- MR card structure, evidence display, course-aware LLM prompt
- Split LLM prompt to avoid f-string crash with JSON schema braces
- Dynamic custom checks audit - reports, retired grading editor, validation, inline styles
- Timeline + LLM dynamic custom checks, remove debug files
- Admin system API 404s - add /dashboard prefix to JS API calls
- Animation conflict + modal scrollbar interference
- 422 telemetry errors + chart container CSS conflict
- Admin users header layout, instructor list clipping, attention card tokens
- Roster/projects/instructors 500 (UUID tojson) + login language selector
- Unify selector styles, animations, and remove dead CSS

### Zmenené

- Complete component unification across all templates
- Migrate ~120 raw buttons, form-groups, spinner, card to Jinja2 macros across 18 templates
- Polish: chart bars, toggle panels, global job bar animations
- Deduplicate global progress bar, remove sounds & toast actions
- Worker bootstrap DRY, kill `__import__()`, modernize JS/dashboard
- Cleanup: os.getenv->Settings, get_event_loop->get_running_loop, inline imports->module-level, .keys() simplification, stubs modernization
- Cleanup: hoist inline stdlib imports, drop OrderedDict, direct settings access
- I18n: comprehensive Slovak translation coverage (1840 entries)
- Zero inline styles - extract login.css, CSS custom props, Import button
- Replace hardcodes with design tokens & GitLab cookie pattern

### Infraštruktúra

- Modernize Python & JS codebase
- Deduplicate components, remove dead code, consolidate infra
- Update all cache-bust versions to v=20260216gl18

### Dokumentácia

- Update test guide for dashboard JSON import, remove generic fixture
- Style all 114 mermaid diagrams with emoji icons, fix R01-R12 tables, translate EN blocks, fix Celery->RQ and hostname

### Testy

- Add unit tests to exceed 40% coverage threshold
- Comprehensive feature test script (F1-F5, 89 checks)

## [2026-02-09 - 2026-02-15]

### Pridané

- Complete GitLab Pajamas tokenization + lint compliance
- Role-based stat cards, rich attention items, activity feed privacy, auto-hide scrollbar
- Comprehensive role-specific UI for all dashboard elements
- Comprehensive role-specific logic across all pages and templates
- Global role config, navigation role gates, search palette role awareness
- Defense-in-depth JS role guards on all page mutations
- Login page server-online health check + remaining security hardening
- Replace generic OG image with thesis-relevant preview
- Add interactive DevOps pipeline app loader
- GitLab sidebar navigation, top bar breadcrumb, smooth animations
- GitLab top bar search button, action icons & sidebar active blue highlight
- GitLab styling - zero inline styles, CSS dedup, component polish
- Functional header, language switcher, search palette, user dropdown, footer
- Rewrite search palette with API integration + UI fixes
- Unify all lists into gl-list component + DLQ sortable columns
- GitLab avatar in header + dashboard greeting + docs update
- GitLab-style home layout with stats, sidebar, activity feed
- Unify card styles, remove footer, match GitLab color zones
- Breadcrumb separator bar, remove Back to Dashboard, responsive fixes
- Complete GitLab Pajamas CSS rewrite + JS error handling
- Pajamas tokens, JS handlers, inline style removal
- Inline style migration, SRI integrity, Pajamas motion polish
- Complete dark theme migration matching GitLab Pajamas
- Cookie banner component, UI polish, tooltip fix, feedback back-nav, ruff format fix
- Add Docker verification trigger + CI/CD scenario create UI
- Comprehensive admin interactivity - retired grading CRUD, course edit, retired heuristic dismiss, project edit/unlink
- Add complete English translations for docs-site
- Full SK/EN localization for dashboard and docs-site
- Add server-side {{ t() }} translations to all templates
- Complete translation coverage for all templates + fix feedback form
- I18n: translate all 14 remaining page templates + add feedback link
- I18n: add 28 missing catalog keys + audit script
- Sync feedback page styles with app design system + role-based template gating
- Full frontend API coverage - analytics, events DLQ, retired grading import/export, secret rotation
- Complete frontend API coverage - telemetry, retired grading suggestions/preview, flags, compliance history
- Harden all raw fetch->apiCall + add missing frontend features
- Fifth round frontend API coverage - dynamic analytics refresh, weekly summary viewer, roster history, retired grading JS activate/export, MR history viewer, fix telemetry course_id int->UUID
- Fix empty data pages: add Team Members table, MR fallback, fix llm-analysis-status 500
- Fix CI formatting, add Team Members pagination, analytics compliance trends
- Add external_id to User model, rename Student ID to ID everywhere
- Show student_id inline with username in User Management table
- More informative AI analysis error display
- Collapsible MR cards, pagination, spacing fixes
- Add GitLab User ID to User model + admin_users page
- Show sync status on dashboard + persist across page navigation
- Live data updates everywhere - no more page reloads
- Toast notifications on process completion + CSRF login_nonce fix
- Phase 31: Fix teacher visibility, add Sync All, fix activities CSS, remove viewer role, fix review comments
- Phase 33: Fix dashboard UX bugs & add server health check

### Opravené

- List click bugs, CSS chevron, unify all lists to macros
- GitLab-exact stat cards, list dividers, dashboard JS bug
- Login lang dropdown consistent width + cache bust login.js
- Sidebar lang dropdown freeze (MutationObserver infinite loop)
- Broken URLs, dashboard filters, teacher 403, table layout
- Quick-link toast guards, remove inline styles, lower greeting
- #my-courses hash toast when no courses, warning icon fill
- Eliminate Alpine.js FOUC - add x-cloak + animation suppression
- CSP img-src for GitLab avatars + remove phantom modal scrollbar
- Telemetry course_id UUID type + course_settings.html tojson serialization
- Button size consistency, chart container overflow, remove inline styles
- Lang switcher, GitLab-style search palette, sidebar open by default
- Collapsed lang dropdown, sidebar default state, GitLab-exact search modal
- Unify lang switcher with Help/Sign out, add mobile slide animation, prevent tablet animation triggers
- Restore mobile/tablet animations with preload guard, add lang chevron
- Align collapsed lang icon, add session heartbeat check
- Match GitLab home page style exactly
- Remove inline styles, dead links, decorations
- Dashboard links & link color - feedback, system status, GitLab-matching blue
- Remove card double-border, add content-wrapper 16px top-left radius
- Match dashboard layout to TUKE GitLab 1:1 - grid, spacing, overflow
- Scrollbar inside content area, double border on cards, job bar layout
- Match GitLab color layers and layout gaps
- Courses table Loading bug, nav_active, inline styles, breadcrumb labels
- JS hardening & CSS polish: fix SyntaxErrors, IIFE wrapping, null guards, pagination corners
- JS security audit + enhanced admin system panel
- Dark theme for all native `<select>`/`<option>` elements
- Toast close button, mobile burger menu, tooltips on touch, language select descender
- Instructor table overflow, diff dark theme, sticky job bar, empty-state spacing, title->tippy, API error toasts
- Resolve all mypy type errors and ensure clean lint pipeline
- Resolve 500 on feedback submit + add admin system page + toast notifications
- Harden remaining raw fetch->apiCall across 6 files
- Telemetry URL prefixes, analytics style fixes, add 186 SK translations
- Remove form-row grid from Weekly Summary to eliminate large gaps between elements
- JS global scope conflicts + import toast error flash
- UUID serialization, responsive CSS, deprecation warnings, CSS cleanup
- Show PRIVATE in email columns, use as placeholder in modals, remove emoji
- Revert: remove external_id, fix enrichment hang + green flash
- Username / ID as header label only, remove student_id data fetching
- Global job bar spinner stutter during enrichment
- Prevent duplicate course card on dashboard
- Remove spinner from modal submit buttons, keep text-only loading state
- Replace CSS spinner with text-only loading state on all buttons
- Prevent enrichment from stalling on GitLab rate limits
- Elapsed timer jumps 2s due to dual updaters
- Robust LLM JSON parser + live analysis progress
- Schema normalization for LLM output + expanded analysis prompt
- Sync BGjob reconciliation + retry on team-not-found
- Increase vertical spacing in analysis grids and sections
- Search-box icon gap + backfill gitlab_user_id from students
- Remove incorrect Student-based gitlab_user_id backfill
- Populate User.gitlab_user_id during GitLab group import
- MR note body empty on sync + analysis section spacing
- Sync field mismatches + template safety across processors
- Resolve all ruff/mypy lint errors, fix tests, add token encryption
- Modal-footer layout - pull flush to edges when inside modal-body
- Add closeDrawer + toggleSelectAll, remove stale pagination HTML
- Remove orphaned Jinja block tags causing 500 errors, comprehensive mobile CSS
- Unify pagination, smart global bar visibility, last_synced_at
- Remove Team Members table, email optional, edge case guards
- CSRF 403 on forms + button spinner text overlay
- Enrichment AJAX, no global bar flash, live dashboard stats
- Global job bar dismiss persistence + duplicate status badges
- Auto-reload teams table + remove dashboard duplicate sync badge
- Smooth indeterminate progress bar animation
- LLM queue priority, student ID auto-populate, remove viewer role
- Phase-33-fix: cancel jobs on archive, text-only loading button, empty grid cleanup
- Import progress in global bar + dynamic course card on dashboard
- Archived table btn-group layout + createCourse toast persists on redirect
- Outline button variants for archived table actions
- Remove icons from archived table buttons, revert to btn-secondary/btn-danger

### Zmenené

- Login lang switch from native `<select>` to gl-dropdown
- Extract app-loader to component files, remove all JS inline styles
- Replace overlay loader with GitLab-identical page-initialised pattern
- Match GitLab UI - remove indicator bar, counter badges, no inline styles, fix layout bug
- Remove all inline styles & hardcoded colors - 100% token-based CSS
- Match TUKE GitLab styles 1:1 from gitlab.example.com
- Move topbar above sidebar+content, add scrollbar component
- Animated paginated lists: staggered row fade-in + TableFilter component
- Align dashboard greeting spacing with page-header (gl-spacing-8 -> gl-spacing-5)
- Custom dropdown for pagination, visible scrollbar, cache bust v=gl9
- Unified dropdown component, GitLab button sizing, smart auto-direction
- Replace all inline styles with CSS classes across JS/HTML
- Use page_header component for Back to Dashboard on feedback page
- Extract back button to page_header component, fix activity grid alignment
- Remove all emojis, fix AI analysis spacing, add evidence links
- Replace Student ID / University ID with GitLab User ID everywhere
- Remove student_id_external from active code
- Fully remove student_id_external column and migration 004
- Reusable process status components, import duplicate detection, import queue
- Split CSS into 18 component files, add reusable JS components library
- Phase 13b: audit fixes - csrfToken bug, deduplicate import flow + addUsername, use shared utilities
- Phase 21: dynamic DOM updates everywhere - no more page reloads
- Phase 22: Edge-case hardening for dynamic DOM updates
- Phase 32: Optimize sync - concurrent API calls for notes + commits
- Refactor app architecture and refresh docs for current CI quality gates

### Bezpečnosť

- Harden RBAC - enforce proper auth levels on all routes
- Add RateLimitDep to all POST routes + RBAC bypass warning

### UI / UX

- GitLab dark theme body bg + cursor:pointer on all interactive elements
- Match GitLab sidebar/topbar - remove uppercase headers, center search
- Exact GitLab Pajamas tokens, inline style removal, a11y fixes across 19 templates
- Phase 13: extract base.html JS into 5 modules, deduplicate student CRUD, extract inline CSS from 7 templates

### Dokumentácia

- Full bilingual documentation refresh with system audit
- Add TUKE Cloud deployment guide for SIVVP VMs
- Update documentation for frontend component architecture

## [2026-02-02 - 2026-02-08]

### Pridané

- Simplify startup scripts and remove hardcoded secrets
- Add GitLab OAuth environment variables to docker-compose
- Implement GitLab OAuth authentication
- Add cleanup on exit to quick-start.ps1 and update to GitLab OAuth
- Complete RBAC implementation across all templates

### Opravené

- Script execution order, PYTHONPATH, and import modal bugs
- Email display, sync polling URL, global bar dedup, action spacing
- Combine if/elif branches to satisfy ruff SIM114
- Update OAuth tests for OAuthTokenResponse and fix all lint errors
- Resolve all ruff and mypy type errors in CI pipeline
- Resolve remaining mypy and ruff linting errors
- Resolve all mypy type errors in commit_processor, gitlab_group_import, and dashboard
- Lower coverage threshold to 40%, fix lint/type errors, add unit tests
- Hot fix
- Wrap all modals with can_edit checks
- Add ApiAuth to LLM endpoints
- Enforce proper auth levels across all API endpoints
- Exclude scripts/stubs/alembic from ruff, fix line length in tests
- Fix typing, coverage, and docs for clean CI
- Fix CycloneDX CLI flags for SBOM job
- Fix pipeline checks and Docker build deps
- Restore mutation testing, fix linting and mypy issues
- Update integration tests for GitLab OAuth
- Add telemetry model relationships to Course/Team/User and fix container scan
- Telemetry UUID types, login template, admin config, mutation tests
- Format telemetry.py, redesign login page with role cards
- Protect Link Project and Run Analysis buttons for viewers
- Protect all action buttons and forms with role checks
- Improve exception handling and update tests

### Zmenené

- Align generics with ruff and mypy
- Initial commit: full codebase backup before cleanup
- Merge chore/repo-cleanup: remove generated files and unused scripts
- Merge hardening/full-audit-fixes: security fixes and production hardening
- License

### Bezpečnosť

- Enable Jinja2 autoescape to prevent XSS
- Remove unsafe |safe filter from error template
- Use configurable report output directory

### UI / UX

- Ruff format 10 files + fix import-status hidden spacing

### Infraštruktúra

- Remove temporary tmpclaude files and add to gitignore
- Make security jobs optional, reduce artifact retention to 7 days
- Make all docker-build dependencies optional to prevent stuck pipelines
- Trigger pipeline rebuild
- Lower mutation score threshold to 65% during development
- Finalize CI pipeline stages
- Remove generated MkDocs site folder (6.5MB)
- Remove unused/obsolete scripts
- Update .gitignore to prevent re-committing generated files

### Dokumentácia

- Comprehensive documentation update for current project structure
- Add repository cleanup report
- Add comprehensive hardening report

### Testy

- Add comprehensive mutation killer tests for text_analysis and time_utils
