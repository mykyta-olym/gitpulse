---
title: "Ciele diplomovej práce"
description: "Čiastkové úlohy diplomovej práce, ich kapitoly a stav"
---
{{< details >}}
- Pre: Všetci
- Vyžaduje: Nič
{{< /details >}}
Stránka zhŕňa čiastkové úlohy diplomovej práce *Nástroje pre podporu výučby
základov DevOps* tak, ako sú uvedené vo formulácii úlohy (sekcia 1.2 textu práce),
a odkazuje na kapitoly, ktoré ich riešia.

{{< alert type="note" >}}
**Zdroj.** Autoritatívnym zdrojom je text práce v repozitári [`dp.mykyta.olym/thesis`](https://gitlab.example.com/kpi-zp/2027/dp.mykyta.olym/thesis). Stručný prehľad kapitol je v sekcii [Diplomovka](../../diplomovka/).
{{< /alert >}}
## Čiastkové úlohy

| # | Úloha | Kapitola | Stav |
|---|------|----------|------|
| 1 | Analyzovať požiadavky tímových zadaní a oddeliť strojovo overiteľné podmienky od podmienok, ktoré posudzuje cvičiaci. | [2. Analýza tímových zadaní](../../diplomovka/analyza/) | Hotové |
| 2 | Preskúmať existujúce nástroje na automatizované hodnotenie, analytiku repozitárov a kontrolu zmien. | [3. Existujúce nástroje](../../diplomovka/nastroje/) | Hotové |
| 3 | Overiť, ktoré údaje posiela GitLab cez webhooky a ktoré treba doplniť cez REST, a určiť hranice ich interpretácie. | [4. Získavanie údajov z GitLabu](../../diplomovka/preskumanie/) | Hotové |
| 4 | Navrhnúť architektúru, dátový tok a bezpečnostné hranice platformy bez zásahu do študentských repozitárov. | [5. Návrh platformy GitPulse](../../diplomovka/navrh/) | Hotové |
| 5 | Realizovať prototyp s importom kurzu, synchronizáciou, nastaviteľnými kontrolami a prehľadmi. | [6. Realizácia riešenia](../../diplomovka/realizacia/) | Hotové, beží na verejnej inštancii |
| 6 | Navrhnúť vyhodnotenie, ktoré oddelí technickú správnosť od pedagogického účinku, a pripraviť overenie s cieľovou skupinou. | [7. Metódy vyhodnotenia](../../diplomovka/vyhodnotenie/) | Postup pripravený, meranie v zimnom semestri 2026/2027 a od februára 2027 |

## Úlohy a táto dokumentácia

| Úloha | Sekcia dokumentácie |
|-------|---------------------|
| 1 a 2 | [Prehľad projektu](../prehlad/), [Diplomovka](../../diplomovka/) |
| 3 | [GitLab integrácia](../../gitlab/) |
| 4 a 5 | [Architektúra](../architektura/), [Vývojári](../../vyvojari/), [API](../../api/), [Asistent cvičení](../../ucitelia/asistent/) |
| 6 | [Vyhodnotenie vo výučbe](../../ucitelia/pilot/), [Operátori](../../operatori/) |

## Princípy riešenia

1. **Riadenie udalosťami.** GitPulse prijíma webhooky GitLabu a podrobnosti dopĺňa
   cez REST. Na strane GitLabu netreba nič meniť a študentské repozitáre sa iba
   čítajú, zapisuje do nich len voliteľný asistent cvičení pod vlastným účtom kurzu.
2. **Hodnotenie študenta za semester.** Kontroly R01 až R13 sledujú prácu študenta
   naprieč jeho žiadosťami o zlúčenie, nie jednu zmenu.
3. **Rozhoduje cvičiaci.** Výsledok kontroly má zdôvodnenie a odkaz do GitLabu
   a nie je známkou.
