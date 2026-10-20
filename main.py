# vestavene knihovny
import csv
import json
import sys
from datetime import datetime

# externi knihovny
from rich.console import Console
from rich.table import Table

# vytvoreni konzole
console = Console()


def nacti_dochazku(nazev_souboru):
    """nacte zaznamy o dochazce z csv"""
    zaznamy = []
    try:
        # osetreni BOM pomoci utf-8-sig
        with open(nazev_souboru, "r", encoding="utf-8-sig", newline="") as soubor:
            reader = csv.DictReader(soubor, delimiter=";")

            # oriznuti mezer v hlavicce
            if reader.fieldnames:
                reader.fieldnames = [name.strip() for name in reader.fieldnames]

            for row in reader:
                # prevod na datetime
                row["příchod_dt"] = datetime.strptime(row["příchod"].strip(), "%Y-%m-%d %H:%M")
                row["odchod_dt"] = datetime.strptime(row["odchod"].strip(), "%Y-%m-%d %H:%M")

                # vypocet delky smeny
                rozdil = row["odchod_dt"] - row["příchod_dt"]
                row["odpracováno_hodin"] = round(rozdil.total_seconds() / 3600, 2)

                zaznamy.append(row)
    except FileNotFoundError:
        console.print(f"[bold red]Chyba: Soubor '{nazev_souboru}' nebyl nalezen.[/bold red]")
        sys.exit(1)
    except Exception as error:
        console.print(f"[bold red]Nastala chyba při čtení souboru: {error}[/bold red]")
        sys.exit(1)

    return zaznamy


def vypis_dochazky(zaznamy):
    """vypis vsech zaznamu"""
    table = Table(title="Kompletní přehled docházky")
    table.add_column("Číslo čipu", justify="right")
    table.add_column("Zaměstnanec", justify="left")
    table.add_column("Příchod", justify="center")
    table.add_column("Odchod", justify="center")
    table.add_column("Odpracováno (h)", justify="right", style="green")

    for z in zaznamy:
        table.add_row(
            z["číslo čipu"],
            z["zaměstnanec"],
            z["příchod"],
            z["odchod"],
            str(z["odpracováno_hodin"])
        )

    console.print(table)


def analyza_zamestnancu(zaznamy):
    """agregace dat a statistiky"""
    statistiky = {}

    for z in zaznamy:
        jmeno = z["zaměstnanec"]
        cip = z["číslo čipu"]
        hodiny = z["odpracováno_hodin"]

        if jmeno not in statistiky:
            statistiky[jmeno] = {
                "číslo čipu": cip,
                "zaměstnanec": jmeno,
                "počet_dní": 0,
                "celkem_hodin": 0.0
            }

        statistiky[jmeno]["počet_dní"] += 1
        statistiky[jmeno]["celkem_hodin"] += hodiny

    # vypocet prumerne smeny
    vystup = []
    table = Table(title="Statistika zaměstnanců")
    table.add_column("Zaměstnanec", justify="left")
    table.add_column("Počet směn", justify="right")
    table.add_column("Celkem hodin", justify="right", style="cyan")
    table.add_column("Průměrná směna (h)", justify="right", style="yellow")

    for s in statistiky.values():
        s["celkem_hodin"] = round(s["celkem_hodin"], 2)
        s["průměrná_směna"] = round(s["celkem_hodin"] / s["počet_dní"], 2)
        vystup.append(s)

        table.add_row(
            s["zaměstnanec"],
            str(s["počet_dní"]),
            str(s["celkem_hodin"]),
            str(s["průměrná_směna"])
        )

    console.print(table)
    return vystup


def vyhledat_zamestnance(zaznamy):
    """vyhledani podle jmena"""
    hledane = input("Zadejte jméno (nebo jeho část) zaměstnance: ").strip().lower()

    nalezene_zaznamy = [z for z in zaznamy if hledane in z["zaměstnanec"].lower()]

    if not nalezene_zaznamy:
        console.print(f"[bold yellow]Nikdo s výrazem '{hledane}' nebyl nalezen.[/bold yellow]")
        return

    table = Table(title=f"Výsledky hledání: {hledane}")
    table.add_column("Číslo čipu", justify="right")
    table.add_column("Zaměstnanec", justify="left")
    table.add_column("Příchod", justify="center")
    table.add_column("Odchod", justify="center")
    table.add_column("Odpracováno (h)", justify="right", style="green")

    for z in nalezene_zaznamy:
        table.add_row(
            z["číslo čipu"],
            z["zaměstnanec"],
            z["příchod"],
            z["odchod"],
            str(z["odpracováno_hodin"])
        )

    console.print(table)


def pozdni_prichody(zaznamy):
    """vyhledani pozdnich prichodu"""
    cas_str = input("Zadejte čas limitu pro pozdní příchod (formát HH:MM, např. 08:00): ").strip()
    try:
        limit_cas = datetime.strptime(cas_str, "%H:%M").time()
    except ValueError:
        console.print("[bold red]Neplatný formát času. Použijte HH:MM.[/bold red]")
        return

    nalezene = [z for z in zaznamy if z["příchod_dt"].time() > limit_cas]

    if not nalezene:
        console.print(f"[bold yellow]Žádné pozdní příchody po {cas_str}[/bold yellow]")
        return

    table = Table(title=f"Pozdní příchody (po {cas_str})")
    table.add_column("Číslo čipu", justify="right")
    table.add_column("Zaměstnanec", justify="left")
    table.add_column("Příchod", justify="center", style="red")
    table.add_column("Odchod", justify="center")
    table.add_column("Odpracováno (h)", justify="right", style="green")

    for z in nalezene:
        table.add_row(
            z["číslo čipu"],
            z["zaměstnanec"],
            z["příchod"],
            z["odchod"],
            str(z["odpracováno_hodin"])
        )

    console.print(table)


def uloz_json(data, nazev_souboru):
    """ulozeni dat do jsonu"""
    try:
        # prevod datetime objektu na retezce
        json_data = []
        for item in data:
            temp_item = item.copy()
            temp_item.pop("příchod_dt", None)
            temp_item.pop("odchod_dt", None)
            json_data.append(temp_item)

        with open(nazev_souboru, "w", encoding="utf-8") as soubor:
            json.dump(json_data, soubor, indent=4, ensure_ascii=False)

        console.print(f"[bold green]Data byla úspěšně uložena do {nazev_souboru}[/bold green]")
    except OSError as error:
        console.print(f"[bold red]Chyba při ukládání: {error}[/bold red]")


def menu():
    console.print()
    console.rule("[bold blue]ANALÝZA DOCHÁZKY[/bold blue]")
    console.print()
    console.print("1 - Zobrazit všechny záznamy docházky")
    console.print("2 - Zobrazit statistiky zaměstnanců (odpracované hodiny)")
    console.print("3 - Vyhledat zaměstnance")
    console.print("4 - Uložit statistiky do JSON")
    console.print("5 - Zobrazit pozdní příchody")
    console.print("0 - Konec")


def main():
    if len(sys.argv) < 2:
        console.print("[bold red]Použití: python dochazka.py <cesta_k_csv>[/bold red]")
        sys.exit(1)

    cesta_k_souboru = sys.argv[1]
    zaznamy = nacti_dochazku(cesta_k_souboru)

    while True:
        menu()
        volba = input("\nVolba: ").strip()

        if volba == "1":
            vypis_dochazky(zaznamy)
        elif volba == "2":
            _ = analyza_zamestnancu(zaznamy)
        elif volba == "3":
            vyhledat_zamestnance(zaznamy)
        elif volba == "4":
            statistika_data = analyza_zamestnancu(zaznamy)
            uloz_json(statistika_data, "vysledek.json")
        elif volba == "5":
            pozdni_prichody(zaznamy)
        elif volba == "0":
            console.print("[bold cyan]Program ukončen.[/bold cyan]")
            break
        else:
            console.print("[bold red]Neplatná volba, zadejte číslo 0–5.[/bold red]")


if __name__ == "__main__":
    main()