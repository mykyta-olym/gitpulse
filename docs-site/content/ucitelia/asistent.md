---
title: "Asistent cvičení"
description: "Bot, ktorý na cvičeniach pracuje ako kolega na projekte - kontrola pushu, konflikt pri zlučovaní, tikety a merge requesty"
---
{{< details >}}
- Pre: Učiteľ
- Vyžaduje: V kurze rolu vlastníka alebo vyučujúceho (prípadne administrátora), bot token v GitLabe, na serveri zapnuté `FEATURE_CLASSROOM_ASSISTANT=true`
{{< /details >}}
Asistent cvičení je bot, ktorý sa na cvičeniach správa ako kolega na projekte. Študenti preň nemajú žiadne nové rozhranie - stretnú ho v GitLabe: komentár k commitu, review merge requestu, tiket, ktorý im pridelí, commit od „kolegu“. Učiteľ ho nastavuje a sleduje na karte **Asistent** kurzu.

Kartu vidí vlastník kurzu, jeho vyučujúci a administrátor. Učiteľ, ktorý kurz vidí len preto, že mentoruje niektorý tím, ju nemá a v prehľade nevidí ani upozornenia a udalosti asistenta. Bot zapisuje do GitLabu za celý kurz, preto ho riadia len tí, ktorí kurz vedú.

Všetky pravidlá sú deterministické - asistent nepoužíva LLM. Každý krok má jasnú udalosť z GitLabu, ktorá ho spustí, a jasnú podmienku, kedy je splnený.

## Sledovanie a zasahovanie sú oddelené

GitPulse číta GitLab tokenom iba na čítanie a analytika (kontroly R01 až R13) do GitLabu nikdy nezapisuje. Asistent je jediná časť, ktorá v GitLabe koná - komentuje, commituje, otvára tikety, schvaľuje a zlučuje. Robí to **pod vlastným bot účtom a vlastným tokenom**, ktorý je pri kurze uložený zašifrovaný:

- token na čítanie, ktorým GitPulse synchronizuje, asistent odmietne,
- keď bot token vyprší alebo ho GitLab odmietne, synchronizácia kurzu beží ďalej,
- odpojením tokenu sa všetky nástroje okamžite zastavia; čo už asistent v GitLabe urobil, zostane.

## Pripojenie bota

1. V GitLabe otvorte skupinu kurzu, potom **Settings > Access tokens**.
2. Pridajte token s rolou **Maintainer** a rozsahom **`api`**; expiráciu nastavte napríklad na koniec semestra. GitLab k tokenu vytvorí bot používateľa (napr. `group_123_bot_…`), ktorý je členom skupiny a jej projektov.
3. V GitPulse otvorte kurz, kartu **Asistent**, kliknite na **Pripojiť bota** a vložte token. GitPulse sa GitLabu spýta, komu token patrí a či má rozsah `api` - až potom ho uloží.

Rola Maintainer je potrebná, pretože asistent commituje do predvolenej (chránenej) vetvy a zlučuje merge requesty. Na samotnú kontrolu pushu stačí Developer.

Asistent reaguje na udalosti **Push**, **Merge request** a **Comments**, ktoré GitPulse už prijíma. Webhook nastavte podľa stránky [Webhooky](../../gitlab/webhooky/) - nič ďalšie netreba.

Karta zobrazuje, pod akým účtom bot koná a kedy vyprší jeho token; dva týždne pred expiráciou ju označí. Keď token vyprší alebo ho GitLab odmietne (napr. bol odvolaný), asistent sa zastaví a karta to povie hneď navrchu - stačí tlačidlom **Vymeniť token** pripojiť nový. Navrchu stránka upozorní aj vtedy, keď sú nástroje zapnuté, ale bot pripojený nie je. Keď kurz nemá nastavený webhook alebo jeho webhook 48 hodín nedostal z GitLabu žiadnu udalosť, stránka to pri otvorení povie upozornením v rohu obrazovky, rovnako ako stránka Udalosti.

## Nástroje

Každý nástroj sa zapína zvlášť a uloží sa tlačidlom **Uložiť zmeny**. Karta **Komentáre** určuje jazyk, ktorým asistent v GitLabe píše (slovenčina alebo angličtina) - komentáre, tikety aj riadok od kolegu.

Asistent sa riadi aj pravidlami, ktoré kurz hodnotí: ak má kurz zapnutú kontrolu **R02**, nová vetva a vetva merge requestu sa kontrolujú podľa pravidla kurzu pre názvy vetiev; ak má zapnutú **R05**, review vyžaduje sekcie popisu merge requestu. Karty nástrojov tieto pravidlá vypíšu. Kontrolu, ktorú kurz vypol, asistent nežiada.

### Kontrola pushu

Po pushi študenta asistent okomentuje pushnutý commit, keď niečo nesedí:

- push išiel **priamo do predvolenej vetvy** namiesto vlastnej vetvy a merge requestu,
- správu commitu **napísal webový editor GitLabu** („Update README.md“) - to isté pravidlo ako kontrola R13,
- prvý riadok správy je **kratší** ako nastavená dĺžka (predvolene 10 znakov),
- názov novej vetvy **nezodpovedá pravidlu kurzu** (iba keď kurz hodnotí R02).

Nová vetva dostane so svojimi prvými commitmi slovo povzbudenia; čistý push do existujúcej vetvy zostane bez komentára - kolega nekomentuje každý push. Vetva založená v GitLabe tlačidlom **New branch** ešte nemá vlastný commit, preto sa ozve až pri prvom pushi do nej; vtedy sa posúdi aj jej názov. Zlúčenie merge requestu GitLab zapíše do predvolenej vetvy v mene študenta, ktorý klikol na **Merge** - to nie je push priamo do `main` a komentár nedostane, commity sa posudzovali už vo vetve. Merge commity sa nehodnotia, ich správu píše git. Každý push sa komentuje najviac raz, aj keď GitLab webhook doručí opakovane.

Komentár, ktorý študent dostane:

```text
Push do vetvy `main`:

- Tento push išiel priamo do `main`, predvolenej vetvy. Pracuj vo vlastnej vetve a zmenu do nej dostaň cez merge request.
- Commit 1a2b3c4d má správu „Update README.md“, ktorú napísal webový editor GitLabu. Napíš, čo sa zmenilo a prečo.

Maj to na pamäti pri ďalších commitoch.
```

### Konflikt pri zlučovaní

Zadanie cvičenia určí súbor (predvolene `README.md`), ktorý študenti upravia vo vlastnej vetve.

1. Keď vetva študenta **prvýkrát zmení súbor**, asistent ako „kolega“ commitne do predvolenej vetvy úpravu **presne tých riadkov**, ktoré študent zmenil - riadok s kontrolným kódom (`GP-1A2B3C`). Zlúčenie vetvy potom vždy skončí konfliktom, aj keď sa predvolená vetva medzitým posunula.
2. Kým si študent predvolenú vetvu nezlúči do svojej (merge alebo rebase), asistent mlčí - konflikt čaká, kým sa študent pôjde zlučovať.
3. Potom pri každom pushi skontroluje súbor: **nezostali značky konfliktu**, zachoval sa **riadok od kolegu** aj **vlastná zmena študenta**. Výsledok napíše do merge requestu vetvy, ak je otvorený, inak ku commitu. Keď je všetko v poriadku, pochváli a úloha je hotová.

Kým vetva súbor nezmenila, alebo súbor v repozitári nie je, úloha čaká a tabuľka Aktivita povie, na čo. Každý študent má v projekte jedno cvičenie: prvú vetvu, ktorá súbor zmení. Do zadania napíšte, ktorý súbor majú upraviť a že pri riešení konfliktu treba zachovať obe zmeny.

### Tikety a merge requesty

**Príprava.** Tlačidlo **Pripraviť cvičenie** (potrebuje pripojeného bota a zapnutý a uložený nástroj) v každom vybranom projekte:

- vytvorí jedným commitom súbor pre každého študenta tímu podľa šablóny (predvolene `ulohy/{username}.txt`) s miestami `???` na doplnenie,
- každému študentovi otvorí tiket, ktorý mu pridelí, s postupom: vlastná vetva, doplniť súbor, commit, merge request s `Closes #N`. Tiket vopred povie aj to, čo bude review žiadať navyše: sekcie popisu, ak kurz hodnotí R05, a pravidlo pre názov vetvy, ak je kurz prísnejší ako predvolené pravidlo „čokoľvek okrem `main` a podobných“. Posledný krok hovorí, kto merge request zlúči.

Opätovné spustenie pridá iba študentov, ktorí tiket ešte nemajú - takto dostane úlohu aj neskôr pridaný študent. Existujúce súbory sa neprepisujú. Príprava beží na pozadí ako synchronizácia: jej priebeh ukazuje horná lišta, po skončení sa zobrazí oznámenie a stránka sa sama obnoví s výsledkom po projektoch. Ak máte vo formulári neuložené zmeny, stránka sa neobnoví, aby ste o ne neprišli, obnoví sa iba karta s aktivitou. Kým príprava beží, karta ukazuje „Pripravuje sa“ a tlačidlo ďalšie spustenie nedovolí. Keď sa príprava ani nezačne, napríklad lebo GitLab medzitým odmietol token, karta to hneď povie aj s dôvodom. Každé spustenie je v Administrácia, Systém, v histórii úloh aj s trvaním. Študenta, ktorého GitPulse ešte nepozná ako používateľa GitLabu (napr. po importe súpisky pred synchronizáciou), tiket priradiť nemožno - výsledok ho započíta zvlášť.

**Priebeh** je konečný automat nad udalosťami, ktoré GitPulse dostáva:

| Udalosť | Čo asistent urobí |
|:--|:--|
| Študent otvorí alebo zmení merge request | Review: vlastná vetva, cieľ je predvolená vetva, popis odkazuje na tiket, zmena je iba v pridelenom súbore, nezostalo `???`, nie je to draft, nemá konflikty, vlákna sú vyriešené. Ak niečo chýba, jeden komentár presne s tým. |
| Študent v merge requeste napíše komentár | Prejde ho znova a odpovie, aj keď sa nič nezmenilo. Ak už po komentári prišlo novšie review (napríklad po úprave merge requestu), neopakuje sa. |
| Nič nechýba | Schváli ho a študenta požiada, aby merge request zlúčil. Keď je zapnuté **Zlúčiť schválený merge request**, zlúči ho sám; ak beží pipeline, zlúčenie počká na ňu. Kým GitLab po pushi ešte zisťuje, či sa dá merge request zlúčiť, review niekoľko sekúnd počká, aby neschválilo konflikt. |
| GitLab merge request zlúčil | Uzavrie tiket a študenta pochváli. |
| Merge request zlúčil niekto pred schválením | Napíše to do merge requestu; úloha je „Zlúčené bez review“. |
| Merge request zatvoria bez zlúčenia | Úloha sa ho pustí; ďalší merge request k tiketu prejde review od začiatku. |

Predvolene zlučuje študent: kontrola R10 hodnotí, či merge request po schválení zlúčil autor alebo člen tímu, a zlúčenie botom za študentovo nepovažuje. Ak chcete celý kolobeh automaticky, zapnite zlučovanie asistentom - R10 vtedy pri týchto merge requestoch neprejde. Schválenie asistentom R09 započíta ako schválenie od učiteľa; komentáre bota sa medzi recenzie R06 nepočítajú, lebo bot nie je člen tímu. Kontrola R08 ich nepočíta ani medzi vlákna, na ktoré má autor odpovedať, takže študent nemusí reagovať napríklad na „schválené, zlúč“.

{{< alert type="warning" >}}
**Cvičenie sa počíta do hodnotenia.** Tiket, vetva, merge request aj uzavretý tiket z cvičenia sú bežná práca v GitLabe a kontroly R01, R02, R04, R05 a R11 ich započítajú ako každú inú. Cvičenie preto pripravte v projektoch určených na precvičenie (napríklad v samostatnom kurze) alebo skôr, než sa začne tímové zadanie. Karta to pripomína pri tlačidle **Pripraviť cvičenie**.
{{< /alert >}}

Review hlási aj zlyhanú pipeline merge requestu a pri kurze s R02 a R05 aj názov vetvy a chýbajúce sekcie popisu.

Review sa píše iba vtedy, keď je čo nové povedať (iný commit alebo iné nálezy), takže napríklad zmena štítku ho neopakuje. Merge request, ktorý odkazuje na cudzí tiket, dostane raz upozornenie, komu je tiket pridelený.

## Aktivita asistenta

Karta **Aktivita asistenta** ukazuje, čo asistent urobil - od najnovšieho, s odkazom na miesto v GitLabe. Filtrovať sa dá podľa nástroja, hľadať podľa študenta, skupiny alebo projektu a triediť aj podľa skupiny. Karta sa obnoví sama, keď asistent v GitLabe niečo urobí, a dá sa obnoviť aj tlačidlom **Obnoviť**.

| Stav | Význam |
|:--|:--|
| Čaká | Asistent sleduje, zatiaľ nemá čo urobiť (vetva ešte nezmenila súbor). |
| Konflikt pripravený | Commit od kolegu je v predvolenej vetve. |
| Tiket pridelený | Tiket je otvorený, merge request ešte nie. |
| Vyžiadané úpravy | Posledné review alebo kontrola si vyžiadali zmenu. |
| Schválené | Schválené, zlučuje sa alebo čaká na pipeline. |
| Hotovo | Úloha je splnená správne. |
| Zlúčené bez review | Merge request bol zlúčený skôr, ako ho asistent schválil. |
| GitLab odmietol | GitLab akciu odmietol (napr. 403, keď bot nemá oprávnenie); dôvod je v stĺpci Posledná akcia. Ďalšia udalosť to skúsi znova. |

## Na nástenke a v konfigurácii kurzu

- **Položky, ktoré si vyžadujú vašu pozornosť** na nástenke uvedú to isté, čo stránka Asistent hovorí navrchu: token, ktorý GitLab odmieta alebo ktorému vypršala platnosť, nástroje zapnuté bez bota, token, ktorý čoskoro vyprší, a prípravu cvičenia, ktorá sa nedokončila. Navyše tam bude počet krokov, ktoré GitLab asistentovi za posledných 7 dní odmietol. Každá položka vedie na stránku Asistent. Chýbajúci webhook tam už je ako samostatná položka kurzu, preto sa pri asistentovi neopakuje.
- **Sledujte najnovšie aktualizácie** ukazuje pripojenie a odpojenie bota, úpravu nástrojov, pripravené cvičenie a token, ktorý GitLab odmietol, s odkazom na stránku Asistent. Študenti tieto riadky nevidia.
- **Export a import konfigurácie kurzu** prenáša aj nastavenia nástrojov asistenta (sekcia `assistant`), nikdy bota ani jeho token. Import ich overí rovnako ako formulár na stránke; keď je asistent na serveri vypnutý, sekciu preskočí.

## Hranice

- Asistent ignoruje udalosti, ktoré sám spôsobil (svoje komentáre, commit, schválenie) - okrem udalosti zlúčenia, z ktorej sa dozvie, že zlúčenie prebehlo.
- Koná iba za študentov tímu - push učiteľa alebo mentora nekomentuje. Člena, ktorého ste vylúčili z hodnotenia, nepovažuje za študenta ani asistent: nedostane tiket ani komentáre.
- Archivovaný kurz je iba na čítanie: GitPulse jeho webhooky zahadzuje, takže asistent stojí, a karta Asistent nedovolí nič zmeniť.
- Pri prenose kurzu do nového semestra prejdú nastavenia nástrojov (zapnuté nástroje, súbory, jazyk, kto zlučuje), bot token nie - nový semester pripojí vlastný.
- Celú funkciu zapína a vypína správca servera premennou `FEATURE_CLASSROOM_ASSISTANT`.
