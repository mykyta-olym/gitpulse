---
title: "Začíname"
description: "Úvodná príručka pre študentov - prvé kroky s GitPulse"
---
{{< details >}}
- Pre: Študent
- Vyžaduje: Školský GitLab účet
{{< /details >}}
## Prihlásenie

1. Otvorte [GitPulse](https://gitpulse.kpi.fei.tuke.sk/) vo webovom prehliadači
2. Kliknite na **Prihlásiť sa cez GitLab**
3. Autorizujte prístup pomocou vášho účtu na [gitlab.example.com](https://gitlab.example.com)
4. Po úspešnom prihlásení budete presmerovaní na dashboard

{{< alert type="note" >}}
**Prvé prihlásenie.** Pri prvom prihlásení systém automaticky vytvorí váš profil a synchronizuje základné údaje z GitLabu (meno, email, avatar). Váš učiteľ vás musí najprv pridať do kurzu, aby ste videli svoje projekty.
{{< /alert >}}
## Navigácia v dashboarde

Po prihlásení uvidíte hlavné časti:

### Výber kurzu

V hornej časti stránky si vyberte kurz, do ktorého ste zapísaní. Každý kurz obsahuje zoznam projektov, ku ktorým máte prístup.

### Prehľad projektu

Pre každý projekt vidíte:

| Sekcia | Popis |
|---|---|
| **Compliance skóre** | Celkové hodnotenie projektu podľa pravidiel R01-R13 |
| **Timeline aktivity** | Graf commitov, issues a merge requestov v čase |
| **Členovia tímu** | Prehľad príspevkov jednotlivých členov |
| **Posledné udalosti** | Zoznam posledných akcií v projekte |

### Detaily pravidiel

Kliknutím na compliance skóre zobrazíte detail jednotlivých pravidiel:

- **Splnené** - pravidlo je splnené
- **Nesplnené** - pravidlo nie je splnené  
- **Čiastočné** - pravidlo je čiastočne splnené

## Čo môžete robiť

Ako študent máte v GitPulse tieto možnosti:

- **Prezerať** compliance skóre svojho tímu
- **Sledovať** timeline aktivity projektu
- **Vidieť** príspevky jednotlivých členov tímu
- **Exportovať** prehľady aktivity (ak je povolené učiteľom)
- **Prijímať** emailové notifikácie o stave projektu

## Čo nemôžete robiť

- Meniť konfiguráciu pravidiel alebo kurzu
- Pristupovať k projektom iných tímov
- Upravovať hodnotenia učiteľa
- Meniť váhy pravidiel

---

## Tipy pre efektívnu prácu

{{< alert type="note" >}}
**Plánovanie cez Issues (R01, R04, R11).** Každú zmenu najprv naplánujte v podobe Issue v GitLab projekte a priraďte ju členovi tímu, ktorý za ňu zodpovedá. Pri otváraní Merge Requestu nezabudnite na prepojenie pomocou kľúčových slov (napr. `Closes #XYZ` v popise MR), ktoré po zlúčení issue automaticky uzavrú.
{{< /alert >}}
{{< alert type="note" >}}
**Vetvenie a Merge Requesty (R02, R05, R10).** Nikdy nepushujte kód priamo do hlavnej vetvy (`main`/`master`). Vytvorte si feature vetvu (napr. `issue-42-login`) a z nej otvorte Merge Request s jasným a podrobným popisom zmien. Po schválení MR ho ako autor sami zmergujte.
{{< /alert >}}
{{< alert type="note" >}}
**Zmysluplné Code Review (R06, R07, R08, R09).** Code review nie je len formálne kliknutie na "Approve". Poskytujte zmysluplné a konštruktívne pripomienky (aspoň 15 slov) k MR svojim kolegom a naopak, reagujte na všetky diskusné vlákna vo svojich Merge Requestoch.
{{< /alert >}}
{{< alert type="note" >}}
**Testovanie a CI/CD (R03, R12).** Každý Merge Request by mal obsahovať aj zmeny v testoch. Uistite sa, že vaše zmeny prejdú automatickým testovaním a pipeline v GitLab CI je úspešná (zelená).
{{< /alert >}}
{{< alert type="note" >}}
**Lokálna práca a Git CLI (R13).** Klonujte si repozitár lokálne a pracujte vo vašom obľúbenom IDE (napr. VS Code). Vyhnite sa priamej úprave súborov cez webové rozhranie GitLabu, pretože to porušuje pravidlo o kvalite commitov.
{{< /alert >}}
## Potrebujete pomoc?

Ak máte problémy s prístupom alebo otázky k hodnoteniu:

1. Obráťte sa na svojho **učiteľa** alebo **cvičiaceho**
2. Pozrite si sekciu [FAQ](faq.md)
3. V prípade technických problémov kontaktujte [mykyta.olym.work@gmail.com](mailto:mykyta.olym.work@gmail.com)
