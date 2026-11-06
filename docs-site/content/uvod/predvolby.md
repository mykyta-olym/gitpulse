---
title: "Osobné predvoľby"
description: "Nastavenia vzhľadu, správania, jazyka a času, ktoré patria vášmu účtu"
---
{{< details >}}
- Pre: Všetkých
- Vyžaduje: Prihlásenie
{{< /details >}}
## Kde ich nájdete

Kliknite na svoj avatar vpravo hore a vyberte **Predvoľby**, alebo prejdite
priamo na `/dashboard/preferences`.

Stránku má **každá rola** - študent, učiteľ aj admin. Sú to vaše vlastné
nastavenia: nemenia nič pre ostatných a nikto iný ich nevidí.

## Patria účtu, nie prehliadaču

Všetky predvoľby sa ukladajú k vášmu účtu, nie do prehliadača. Keď sa
prihlásite na inom počítači alebo v inom prehliadači, idú s vami. To je aj
dôvod, prečo sa ukladajú na serveri a nie do `localStorage`.

## Farebný režim

Svetlý, tmavý, alebo podľa systému.

Toto je **jediná** výnimka na stránke: použije sa okamžite a uloží sa sama -
tlačidlo *Uložiť zmeny* na ňu nepotrebujete. Je to ten istý ovládač, aký máte
v menu pod avatarom, takže existuje len jeden spôsob, ako režim zmeniť.

## Motív

Akcentová farba rozhrania. Náhľad ukazuje, čo sa presne zmení: zafarbí sa
podsvietenie vybranej položky v ľavej navigácii. **Predvolená** ponechá
štandardnú modrú.

## Rozdiely

Farby odstránených a pridaných riadkov v zobrazení rozdielov - používa ich
profil študenta pri zobrazení kontextu kódu, ako aj počítadlá `+`/`−`
v hlavičke profilu a v tabuľke commitov.

Zadajte ľubovoľnú hex farbu vo formáte `#RRGGBB` alebo kliknite na jednu
z navrhovaných. **Náhľad nad poliami je skutočný komponent rozdielov**, nie
obrázok - takže vidíte presne to, čo dostanete. Prázdne pole vráti farbu na
štandardnú zelenú/červenú.

## Správanie

| Nastavenie | Čo robí |
|---|---|
| Klávesové skratky | Zapína vyhľadávaciu paletu (`/`, `Ctrl+K`) a ostatné globálne skratky. Vypnutie neovplyvní `Esc` - dialógy sa stále dajú zavrieť. |
| Šírka rozloženia | **Pevná** obmedzí obsah na 1280 pixelov, **Plynulá** ho roztiahne na celú šírku. |
| Domovská stránka | Kam vás pustí `/dashboard/` po prihlásení. Ponúkajú sa **len stránky, ktoré vaša rola dokáže otvoriť**. |
| Riadkov na stranu | Koľko riadkov ukazuje tabuľka. Je to **predvoľba** - voľba v konkrétnej tabuľke má naďalej prednosť. |
| Bočný panel | Či sa načíta zbalený. Použije sa len na zariadení, kde ste ho ešte nezbalili ručne. |

## Notifikácie

Ktoré e-maily vám GitPulse posiela: **tikety podpory**, **predmety** (priradenie,
archivácia, opätovná aktivácia) a **účet** (zmeny roly, obnovenie účtu).

Vypnutie zastaví e-mail **na serveri** - nie je len skrytý pred vami. Uvítacia
správa prepínač nemá zámerne: posiela sa skôr, než túto stránku vôbec uvidíte.

## Lokalizácia

**Jazyk** sa uplatní od ďalšieho načítania stránky. *Predvolené systémom* vráti
voľbu vášmu prehliadaču.

**Prvý deň týždňa** zmení každý výber dátumu v aplikácii.

## Nastavenia času

**Relatívne časy** sa čítajú ako „pred 30 minútami". Ak ich vypnete, všade
uvidíte presné časové značky. Tak či tak po prejdení myšou nad časom stále
uvidíte kanonickú UTC hodnotu.

**Formát času** prepína medzi 24-hodinovým (`14:34`) a 12-hodinovým
(`2:34 PM`) zobrazením.

## Ukladanie

Všetko okrem farebného režimu sa ukladá naraz tlačidlom **Uložiť zmeny**.

**Obnoviť predvolené** iba vyplní formulár späť na východiskové hodnoty -
nič sa nezapíše, kým neuložíte, takže si to ešte môžete rozmyslieť.

{{< alert type="note" >}}
Ak si nie ste istí, čo ktoré nastavenie robí, spustite si sprievodcu:
avatar → **Prevziať prehliadku**. Prevedie vás všetkými sekciami tejto stránky.
{{< /alert >}}
