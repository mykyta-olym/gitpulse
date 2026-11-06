---
title: "4. Získavanie údajov z GitLabu"
weight: 4
description: "Webhooky, REST API a priradenie kontrol R01 až R13 k zdrojom údajov"
---
{{< details >}}
- Pre: Čitateľ práce
- Vyžaduje: Nič
{{< /details >}}
GitLab ponúka dve cesty k údajom. **Webhook** oznámi zmenu v priebehu sekúnd, ale
doručenie nie je zaručené práve raz, poradie nie je zaručené a po opakovaných
zlyhaniach ho GitLab vypne. **Rozhranie REST** vráti úplný aktuálny stav objektu,
o zmene sa však program sám nedozvie. Platforma preto berie udalosť ako signál
a REST ako zdroj podrobností.

## 4.1 Čo je v tele udalosti

Udalosť žiadosti o zlúčenie neobsahuje zmenené súbory (R03), udalosť Note nemá
celé diskusné vlákno (R08) a Push obsahuje najviac dvadsať commitov. Udalosť
procesu CI/CD naopak obsahuje zoznam úloh, takže R12 sa dá vyhodnotiť priamo.
Po prijatí sa telo uloží, odpoveď sa vráti hneď a doplnenie prebehne na pozadí.
Ručná synchronizácia doplní, čo sa stalo pred nastavením webhooku alebo čo sa
nedoručilo. Periodické prehľadávanie projektov GitPulse nemá.

## 4.2 Priradenie kontrol k zdrojom

| Kontrola | Spúšťač | Doplnenie | Hranica interpretácie |
|---|---|---|---|
| R01 | Issue | stav a priradenie | Priradenie nepreukazuje vykonanú prácu. |
| R02 | Merge Request | netreba | Konvencia názvu je voliteľná podľa kurzu. |
| R03 | Merge Request | zmenené súbory | Z názvu súboru nevyplýva kvalita testu. |
| R04 | Merge Request | netreba | Odkaz nepreukazuje vecnú zhodu zmeny s tiketom. |
| R05 | Merge Request | netreba | Dĺžka a sekcie sú iba formálne minimum. |
| R06 | Note | poznámky žiadosti | Počet slov je zástupný ukazovateľ kvality. |
| R07 | Note | poznámky viacerých žiadostí | Počet žiadostí nevyjadruje náročnosť recenzie. |
| R08 | Note | diskusné vlákna | Komentáre mimo vlákna sa párujú iba približne. |
| R09 | Merge Request | schválenia | Schválenie bez komentára nedokazuje kontrolu. |
| R10 | Merge Request | netreba | Kto smie zlúčiť, určuje pravidlo kurzu. |
| R11 | Issue, Merge Request | stav oboch objektov | Bez výslovnej väzby je výsledok menej istý. |
| R12 | Pipeline | netreba | Úspech dokazuje len to, čo proces naozaj spúšťa. |
| R13 | Push, synchronizácia | história commitov | Vzor názvu nedokazuje použitého klienta. |

## 4.3 Zistenia pre návrh

Všetkých trinásť kontrol má dostupný vstup. Pri dvoch však potrebný údaj
v GitLabe nie je: väzba odpovede na pripomienku mimo vlákna (R08) a klient, ktorým
commit vznikol (R13). Takéto kontroly rozhranie odlišuje a výsledky ukladajú aj
identifikátory objektov a textové zdôvodnenie. Samostatné odhaľovanie neúprimného
plnenia zadania bolo z návrhu vypustené, pretože by skladalo neisté signály
do tvrdenia o správaní študenta.

## Zdroje rozhraní

- [GitLab webhooks](https://docs.gitlab.com/user/project/integrations/webhooks/)
- [GitLab REST API](https://docs.gitlab.com/api/rest/)
