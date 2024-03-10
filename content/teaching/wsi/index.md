---
title: Introduction to Artificial Intelligence [PL, WSI-24L-G103, WSI-24L-G104]
subtitle: Wprowadzenie do Sztucznej Inteligencji
date: "2024-02-23T00:00:00Z"
lastmod: "2024-03-12:12:00:00Z"

draft: false
featured: false
toc: true
toc_depth: 4

---

{{<toc>}}
## Zasady laboratorium
Celem laboratorium jest zapoznanie się z podstawowymi algorytmami sztucznej
inteligencji, ich zastosowaniem oraz analizą. Zaliczenie laboratorium odbywa się
poprzez oddanie siedmiu ćwiczeń. Pełen kalendarz ćwiczeń znajduje się poniżej.
Wszystkie ćwiczenia są realizowane indywidualne poza ćwiczeniem związanego z
implementacją sieci neuronowych, gdzie zadanie będzie realizowane w parach. Na każde zadanie przypada 2 tygodnie. Nie ma
obowiązku bycia na zajęciach po odebranie tematu ćwiczenia.

### Miejsce i czas zajęć

- Grupa 103: Sala 011, budynek WEiTI, każdy wtorek, 12:15-14:00
- Grupa 104: Sala 09, budynek WEiTI, każda środa, 16:15-18:00


### Wymagania 
Zaliczenie pojedynczego zajęcia odbywa się poprzez oddanie:
- sprawozdania, na które składają się części opisane niżej,
- kodu źródłowego.

Na sprawozdanie składa się:
- krótki opis działania algorytmu,
- opis eksperymentów,
- wyniki jakościowe i ilościowe,
- wnioski, obserwacje.

Całe sprawozdanie powinno zamykać się maksymalnie w 5 stronach A4, w formacie jednokolumnowym.

### Ocena i oddawanie zadań
Z każdego zadania można uzyskać 0-7 pkt., natomiast w przypadku tematu z
sieciami neuronowymi: 0-8pkt. 

Na liczbę przyznanych punktów składają się:
- poprawność implementacji algorytmu: 30%,
- poprawność przeprowadzonych eksperymentów: 30%,
- analiza i dyskusja wyników 35%,
- poprawność sprawozdania: 5%.

Oddawanie zadania na zajęciach wygląda następująco:
- student pokazuje działanie algorytmu,
- odpowiada na kilka pytań dotyczących wyników z raportu i działania algorytmu.

Oddane zadanie, czyli raport + kod źródłowy, należy spakować do pliku
`wsi-{numer-indeksu}-{numer ćwiczenia}.zip`  i przesłać na
kacper.kania.dokt@pw.edu.pl. 

Możliwe jest oddanie zadania przed terminem.


### Zalecenia
Zachęcam do implementacji algorytmów przy wykorzystaniu Pythona. W ten sposób
zwiększycie Państwo swoje szanse na skuteczność mojej pomocy przy ewentualnym
debugowaniu. Inne języki programowania (Rust, C++, C#, Java) też są
dopuszczalne. 

Przy wykorzystaniu Pythona, zachęcam do automatycznego formatowania kodu za
pomocą [blacka](https://github.com/psf/black) i komendą:
```bash
black --line-length 79 ./**/*.py
```

W przypadku korzystania z [VSCode'a](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter) lub [PyCharma](https://black.readthedocs.io/en/stable/integrations/editors.html) możliwe jest podpięcie
automatycznego formatowania kodu.

Użytkowników Windowsa zachęcam do korzystania z [Windows Subsystem for Linux
(WSL)](https://learn.microsoft.com/en-us/windows/wsl/install).

### Opóźnienie oddawania
Każdy dzień opóźnienia skutkuje obniżeniem punktów końcowych za zadanie według
wzoru:
$$
O_k = \max \\{O_p(1- 10\\%n), 0\\},
$$
gdzie $n$ to liczba dni opóźnienia (dzień po oddaniu $n=1$), $O_p$ to
proponowana liczba punktów, a $O_k$ to końcowa liczba punktów. Dla przykładu,
za tydzień opóźnienia zadania za 7 pkt. otrzymują Państwo 2,1 pkt.


### Konsultacje
Jestem dostępny w piątki o 13 w sali 413 budynku WEiTI. Proszę powiadomić mnie
wcześniej drogą mailową lub na Teamsie w przypadku chęci odbycia takich konsultacji.


### Wykorzystanie modeli językowych
Dopuszczam wykorzystywanie modeli językowych, takich jak ChatGPT, w
następujących celach:
- edycja tekstu **już gotowego** sprawozdania (np. w celu usunięcia błędów
  językowych)
- copilot (lub inne dowolne narzędzie tego typu) w celu predykcji kodu (jako
  następnego tokenu, nie jako całości algorytmu)

## Terminarz dla grupy 103

| Lp. | Temat | Start | Oddanie | Punktacja |
|---|---|---|----|----|
| 1 | Przeszukiwanie przestrzeni | 27.02.2024 | 12.03.2024 | 0-7 |
| 2| Algorytmy ewolucyjne i genetyczne | 12.03.2024 | 26.03.2024 | 0-7 |
| 3| Dwuosobowe gry deterministyczne | 26.03.2024 | 16.04.2024 | 0-7 |
| 4| Regresja i klasyfikacja | 16.04.2024 | 07.05.2024 | 0-7 |
| 5| Sztuczne sieci neuronowe | 07.05.2024 | 21.05.2024 | 0-8 |
| 6| Uczenie ze wzmocnieniem | 21.05.2024 | 04.06.2024 | 0-7 |
| 7| Modele bayesowskie | 04.06.2024 | 11.06.2024 | 0-7 |

## Terminarz dla grupy 104

|Lp. | Temat | Start | Oddanie | Punktacja |
|--|---|---|----|----|
|1| Przeszukiwanie przestrzeni | 28.02.2024 | 13.03.2024 | 0-7 |
|2| Algorytmy ewolucyjne i genetyczne | 13.03.2024 | 27.03.2024 | 0-7 |
|3| Dwuosobowe gry deterministyczne | 27.03.2024 | 10.04.2024 | 0-7 |
|4| Regresja i klasyfikacja | 10.04.2024 | 24.04.2024 | 0-7 |
|5| Sztuczne sieci neuronowe | 24.04.2024 | 15.05.2024 | 0-8 |
|6| Uczenie ze wzmocnieniem | 15.05.2024 | 29.05.2024 | 0-7 |
|7| Modele bayesowskie | 29.05.2024 | 12.06.2024 | 0-7 |

## Zadania

### Zadanie 1.
Zaimplementuj metodę gradientu prostego oraz przeprowadź analizę zaimplementowanej metody dla dwóch funkcji:
- Funkcji Rastrigina dla zakresu $\mathbf{x} \in [-5,12; 5,12], \mathbf{x}\in\mathbb{R}^2$:
$$
f(\mathbf{x}) = 10d + \sum^d_{i=1}\left[x^2_i - 10\cos(2\pi x_i)\right],
$$
- Funkcji Griewanka dla zakresu $\mathbf{x} \in [-5, 5], \mathbf{x}\in\mathbb{R}^2$
$$
f(\mathbf{x}) = \sum^d_{i=1} \frac{x_i^2}{4000} -
\prod^d_{i=1}\cos\left(\frac{x_i}{\sqrt{i}} \right) +1,
$$
gdzie $d$ to liczba wymiarów oraz $d{=}2$.

Eksperymenty powinny zawierać między innymi: testy różnych wartości parametrów
uczenia ($\beta$, patrz slajdy z wykładu), oraz różne punkty inicjalizacji (blisko optimum, daleko od optimum). W czasie zajęć proszę pokazać zbieżność dla
funkcji:
$$
f(\mathbf{x}) = \sum_{i=1}^d x_i^2.
$$

Więcej informacji, w tym wizualizacje, na temat testowanych funkcji możecie
znaleźć [tutaj](https://www.sfu.ca/~ssurjano/optimization.html).


### Zadanie 2.
Treść zadania można pobrać tutaj: [zadanie-2-algorytmy-ewolucyjne.pdf](/media/wsi2024L/zadanie-2-algorytmy-ewolucyjne.pdf). W
razie pytań, zapraszam do kontaktu na MS Teams oraz na konsultacje. 

### Zadanie 3.
### Zadanie 4.
### Zadanie 5.
### Zadanie 6.
### Zadanie 7.
