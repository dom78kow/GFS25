# GFS25 — Farming Simulator 3D

Prototyp gry rolniczej 3D z widokiem trzecioosobowym, zbudowany w Pythonie i Panda3D. Gracz prowadzi ciągnik po proceduralnie wyświetlanym terenie, może orać pole oraz korzystać z kamery orbitalnej i podstawowego HUD-u.

## Wymagania

- Python 3.10 lub nowszy
- `pip`
- System Windows, macOS albo Linux z obsługą Panda3D

## Instalacja

Polecenia wykonuj w głównym katalogu projektu.

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

W systemie macOS/Linux aktywuj środowisko poleceniem:

```bash
source .venv/bin/activate
```

## Uruchomienie

```powershell
python GFS25_3D_V2.py
```

Projekt należy uruchamiać z głównego katalogu repozytorium — aplikacja korzysta ze ścieżek względnych do katalogów `models/`, `textures/` i `maps/`.

## Sterowanie

| Klawisz / akcja | Działanie |
| --- | --- |
| `W` / `S` | Jazda do przodu / cofanie |
| `A` / `D` | Skręt w lewo / prawo podczas jazdy |
| `F` | Włącza lub wyłącza reflektory |
| Prawy przycisk myszy + ruch | Obraca kamerę wokół ciągnika |
| Kółko myszy | Przybliża lub oddala kamerę |
| Środkowy przycisk myszy | Przywraca domyślne ustawienie kamery |
| `Esc` | Zamyka grę |

## Mapa

Układ terenu jest określony w pliku [maps/map1.txt](maps/map1.txt). Każdy znak odpowiada jednemu segmentowi mapy:

| Znak | Typ terenu |
| --- | --- |
| `.` | Trawa |
| `W` | Pszenica |
| `C` | Rzepak |
| `#` | Zaorane pole |

Podczas jazdy po zaoranym polu ciągnik pracuje z mniejszą prędkością i zużywa paliwo. Przejechane sektory są wizualnie oznaczane jako zaorane.

## Struktura projektu

```text
GFS25_3D_V2.py      # kod aplikacji
requirements.txt    # zależności Pythona
maps/map1.txt       # układ mapy
models/tractor.obj  # model ciągnika
textures/            # tekstury terenu
```
