---
title: "2. Analýza tímových zadaní"
weight: 2
description: "Požiadavky predmetov, pozorovateľné postupy a kontroly R01 až R13"
---
{{< details >}}
- Pre: Čitateľ práce
- Vyžaduje: Nič
{{< /details >}}
Kapitola určuje, čo sa má sledovať. Zo znenia zadania vyplývajú tri povinnosti:
vlastný príspevok aj s testami, recenzia kódu ostatných členov tímu a zlúčenie
zmeny do hlavnej vetvy. Obidva predmety majú rovnaké znenie projektu, líšia sa
prípravou, preto tá istá sada kontrol slúži obom a prahy si nastaví každý kurz.

## 2.1 Čo zanecháva stopu v repozitári

Pozorovať sa dá práca s vetvami a žiadosťami o zlúčenie, väzba zmeny na tiket,
automatizované testovanie v procese CI/CD, recenzia kódu a spôsob práce s Gitom.
Úspešný proces bez testovacej úlohy však testovanie nedokazuje a schválenie
jedným kliknutím nie je rovnocenné vecnej pripomienke. Nástroj preto rozlišuje
recenzentov, komentáre, diskusné vlákna, odpovede autora a schválenia.

## 2.2 Kontroly R01 až R13

| ID | Otázka |
|---|---|
| R01 | Má študent priradený aspoň jeden tiket? |
| R02 | Vznikla jeho zmena vo vlastnej vetve a má žiadosť o zlúčenie? |
| R03 | Pridal alebo upravil v niektorej svojej žiadosti súbor s testami? |
| R04 | Odkazuje žiadosť na tiket, ktorý rieši? |
| R05 | Má opis žiadosti minimálny obsah, prípadne časti šablóny? |
| R06 | Okomentoval jeho žiadosť požadovaný počet spolužiakov? |
| R07 | Recenzoval on sám požadovaný počet cudzích žiadostí? |
| R08 | Odpovedal na recenzné vlákna vo vlastnej žiadosti? |
| R09 | Získala jeho žiadosť schválenie? |
| R10 | Zlúčil zmenu člen tímu, ktorého určuje pravidlo kurzu? |
| R11 | Sú žiadosť aj súvisiaci tiket uzavreté? |
| R12 | Existuje úspešný proces CI/CD s testovacou úlohou? |
| R13 | Nepresahuje podiel commitov z webového editora nastavený prah? |

R03 overuje iba zmenu testovacieho súboru, nie kvalitu testov. R06 a R07 spájajú
komentáre jedného recenzenta k jednej žiadosti a vyžadujú predvolene pätnásť slov,
systémové poznámky GitLabu sa nepočítajú. R13 porovnáva názvy commitov so vzormi
webového editora a je predvolene vypnutá s nulovou váhou.

## 2.3 Hranice rozkladu

Stav tiketu alebo procesu je uložený priamo, kým R06, R07 a R13 pracujú so
zástupnými ukazovateľmi. Ich výsledok je podnetom na overenie. Výskum nad
študentskými projektmi ukazuje, že súhrnné čísla silno závisia od zvolenej
metriky, a preto slúžia ako podklad pre rozhovor s tímom.
