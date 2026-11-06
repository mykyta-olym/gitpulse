---
title: "1. Úvod"
weight: 1
description: "Problém, motivácia a formulácia úlohy"
---
{{< details >}}
- Pre: Čitateľ práce
- Vyžaduje: Nič
{{< /details >}}
Tímové zadanie predmetu Základy softvérového inžinierstva vyžaduje, aby študent
vyriešil pridelenú úlohu aj s jednotkovými testami, recenzoval kód ostatných
členov tímu a zlúčil ich riešenia do hlavnej vetvy. Takmer rovnaké zadanie má
predmet Základy DevOps. Hodnotí sa teda aj spôsob práce, ktorý z hotového programu
nevidno.

Dôkaz o splnení jednej úlohy je v GitLabe na viacerých miestach: zadanie v tikete,
realizácia vo vetve a v žiadosti o zlúčenie, kontrola v diskusii a schválení,
overenie vo výsledku procesu CI/CD a stopa v histórii commitov. V letnom semestri
2025/2026 bolo na prvý predmet zapísaných 189 študentov v deviatich skupinách a na
druhý 393 študentov v ôsmich skupinách. Pri takom počte sa priebežná ručná kontrola
v praxi takmer nerobí, hoci najväčší zmysel má práve počas semestra.

## 1.1 Motivácia

Na mnohé kontrolné otázky sa dá odpovedať priamo zo stavu v GitLabe, napríklad či
má študent priradený tiket alebo či proces CI/CD skončil úspešne. Ak sa takéto
ukazovatele prepočítajú krátko po zmene a pri každom výsledku je dôvod a odkaz na
pôvodný objekt, cvičiaci aj študent vidia chýbajúci krok včas. Rovnaký výpočet pre
celý kurz robí výsledky skupín porovnateľnými. Kvalitu kódu a porozumenie študenta
naďalej posudzuje cvičiaci a nástroj neprevádza percentá na známku.

## 1.2 Formulácia úlohy

Cieľom práce je navrhnúť, realizovať a overiť nástroje, ktoré podporia výučbu
základov DevOps nad tímovými projektmi v GitLabe. Čiastkové úlohy:

1. analyzovať požiadavky tímových zadaní a oddeliť strojovo overiteľné podmienky
   od podmienok, ktoré musí posúdiť cvičiaci,
2. preskúmať existujúce nástroje na automatizované hodnotenie, analytiku
   repozitárov a kontrolu zmien,
3. overiť, ktoré údaje posiela GitLab cez webhooky a ktoré treba doplniť cez
   rozhranie REST, a určiť hranice ich interpretácie,
4. navrhnúť architektúru, dátový tok a bezpečnostné hranice platformy bez zásahu
   do študentských repozitárov,
5. realizovať prototyp s importom kurzu, synchronizáciou, nastaviteľnými
   kontrolami a prehľadom na úrovni kurzu, skupiny, projektu a študenta,
6. navrhnúť vyhodnotenie, ktoré oddelí technickú správnosť od pedagogického
   účinku, a pripraviť podklady na overenie s cieľovou skupinou.
