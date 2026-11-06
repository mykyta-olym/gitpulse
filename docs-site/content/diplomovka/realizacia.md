---
title: "6. Realizácia riešenia"
weight: 6
description: "Technológie, import a synchronizácia, spracovanie udalostí, priebeh kontroly a kvalita"
---
{{< details >}}
- Pre: Čitateľ práce
- Vyžaduje: Nič
{{< /details >}}
GitPulse beží od júla 2026 na verejnej inštancii
[gitpulse.kpi.fei.tuke.sk](https://gitpulse.kpi.fei.tuke.sk). Aplikácia je
napísaná v jazyku Python 3.12 na rámci FastAPI, údaje ukladá PostgreSQL 16,
Redis 7 slúži ako vyrovnávacia pamäť, front úloh pre RQ a kanál živých zmien.
Stránky sa vykresľujú na serveri cez Jinja2 a v prehliadači ich dopĺňajú htmx,
Alpine.js a Chart.js. Výpočet kontrol je v balíku `compliance`, ktorý nevie nič
o webe ani o frontoch. Štruktúru kódu opisuje [sekcia pre vývojárov](../../vyvojari/struktura/).

## 6.1 Priebeh kontroly v prototype

Hlavný postup cvičiaceho má štyri kroky. Snímky sú z demonštračného kurzu
s vymyslenými údajmi, výsledky však vypočítal ten istý kontrolný mechanizmus,
ktorý beží nad reálnymi projektmi.

![Prehľadový panel cvičiaceho](/docs/assets/thesis/gitpulse-01-prehlad.png)

*Prehľadový panel so súhrnom obdobia a položkami, ktoré potrebujú pozornosť.*

![Skupiny kurzu so semaforom](/docs/assets/thesis/gitpulse-02-kurz.png)

*Skupiny kurzu s priemerným skóre a semaforom.*

![Členovia skupiny](/docs/assets/thesis/gitpulse-03-skupina.png)

*Členovia skupiny so skóre a počtom splnených zapnutých kontrol.*

![Detail študenta](/docs/assets/thesis/gitpulse-04-student.png)

*Detail študenta s postupom žiadosti o zlúčenie a odkazom do GitLabu.*

## 6.2 Kvalita a prevádzka

K 2. 11. 2026 má sada 4 656 jednotkových testov vrátane 26 kontraktových a ďalších
173 integračných testov beží v integračnom procese nad PostgreSQL a Redisom.
Asistent bol overený skriptom proti lokálnemu GitLabu CE 19.4.2. Prvý beh odhalil
tri chyby v prijímaní webhookov, ktoré ručne písané vzory nezachytili, a trinásť
zachytených doručení sa stalo novými kontraktovými vzormi. Pri príprave snímok sa
našli ďalšie tri chyby (vypnutá kontrola zobrazená ako nesplnená, skóre bez
normalizácie, pokrok študenta počítaný za celú skupinu), opravené vo verzii
2026.11.2.post4.

Integračný proces kontroluje štýl, typy, statické súbory a závislosti, preveruje
zraniteľnosti, spúšťa testy, zostavuje obraz pre Docker a zverejňuje dokumentáciu.
Metriky pre Prometheus sa zobrazujú v Grafane a osemnásť pravidiel výstrah
posiela e-maily správcovi. Prevádzku opisuje [sekcia pre operátorov](../../operatori/).
