---
title: "Vyhodnotenie vo výučbe"
description: "Ako sa GitPulse overí s cvičiacimi a študentmi a čo pri tom robí cvičiaci"
---
{{< details >}}
- Pre: Učiteľ
- Vyžaduje: Účet v GitPulse s rolou učiteľa
{{< /details >}}
Stránka opisuje, ako sa GitPulse vyhodnotí vo výučbe. Postup vychádza z kapitoly
[7. Metódy vyhodnotenia](../../diplomovka/vyhodnotenie/) diplomovej práce. Výsledky
zatiaľ neexistujú, merania ešte len prebehnú.

## Čo sa overuje

1. Kontroly počítajú správne a opakované alebo chýbajúce doručenie udalosti
   nespôsobí stratu ani zdvojenie údajov.
2. Výsledok kontroly sa zhoduje s tým, ako tú istú otázku posúdi cvičiaci priamo
   v GitLabe.
3. Cvičiaci s GitPulse odpovie na bežné otázky rýchlejšie a s menej prechodmi medzi
   stránkami a systém považuje za použiteľný.
4. Študent, ktorý vidí vlastný prehľad, vie povedať, ktorý krok mu chýba.

## Harmonogram

| Obdobie | Čo prebehne |
|:--------|:------------|
| Zimný semester 2026/2027 | Meranie zhody na dokončených projektoch z letného semestra 2025/2026 a úlohová skúška s cvičiacimi. Vyhodnotenie do marca 2027. |
| Letný semester 2026/2027 | Živé nasadenie na predmete, prevádzkové metriky, dotazník pre študentov po odovzdaní tímového projektu a jedno cvičenie s asistentom. |

Obidva súbory údajov sú v tej istej inštancii a oddeľuje ich akademické obdobie
kurzu.

## Čo robí cvičiaci

### Pred živým nasadením

- [ ] Importujte kurz po zostavení tímov ([Začíname](../zaciname/)).
- [ ] Nastavte webhooky skôr, než sa začne práca na tímovom projekte, aby sa
      udalosti zbierali od začiatku ([Webhooky](../../gitlab/webhooky/)).
- [ ] Skontrolujte zapnuté kontroly, váhy a prahy v nastaveniach kurzu.
- [ ] Na cvičení informujte študentov, že majú vlastný prehľad a že jeho používanie
      je dobrovoľné.

### Počas semestra

- Prehľad používajte podľa vlastného uváženia. Nástroj nie je podmienkou hodnotenia
  a známky sa udeľujú ako doteraz.
- Nízke skóre berte ako podnet na rozhovor so študentom, nie ako verdikt. Môže
  znamenať neúplnú synchronizáciu, inak organizovaný projekt alebo chýbajúci krok
  ([Interpretácia výsledkov](../interpretacia/)).
- Asistenta cvičení používajte iba v projektoch určených na precvičenie, aby
  neovplyvnil kontroly tímového projektu ([Asistent cvičení](../asistent/)).

### Pri meraní zhody a úlohovej skúške

- Pri meraní zhody posudzujú dvaja cvičiaci vzorku študentov nezávisle a priamo
  v GitLabe, bez otvorenia GitPulse.
- V úlohovej skúške rieši cvičiaci štyri úlohy raz len s GitLabom a raz s GitPulse
  na dvoch porovnateľných skupinách, piata úloha overí odpoveď systému v GitLabe.
  Po skúške nasleduje dotazník System Usability Scale a krátky rozhovor.

## Dotazníky

Každá rola má vlastný anonymný dotazník v Google Forms. Aplikácia ukáže každému
používateľovi jeho dotazník v paneli Podpora a návrhy na prehľade.

| Dotazník | Kto ho vypĺňa |
|:---------|:--------------|
| [Dotazník pre študentov](https://forms.gle/mNvu5Yv4bLmm4D6L6) | študenti po odovzdaní tímového projektu |
| [Dotazník pre vyučujúcich](https://forms.gle/TaHFrQaFM1a33hG27) | cvičiaci a garanti, po úlohovej skúške alebo počas semestra (obsahuje System Usability Scale) |
| [Posúdenie komentára asistenta](https://forms.gle/6AbyWK3HGoYpjkfm7) | cvičiaci, jedna odpoveď za každý posúdený komentár asistenta |
| [Dotazník pre správcov](https://forms.gle/AYkbAJEft1bmHpTq5) | správcovia inštancie GitPulse |

## Údaje a súkromie

Údaje GitPulse zostávajú v infraštruktúre univerzity a výsledky sa uvádzajú súhrnne
a bez mien. Záznamy obrazovky z úlohovej skúšky sa po prepise časov zmažú.
Odpovede z dotazníkov ukladá Google Forms a nezbiera sa pri nich meno, e-mail ani
prihlasovacie údaje. GitPulse nesleduje, ako sa používa prehliadač, a neodhaduje
ušetrené kliknutia.
Podrobnosti sú v [ochrane osobných údajov](../../pravne/ochrana-udajov/).
