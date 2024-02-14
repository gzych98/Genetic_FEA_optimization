import datetime
import numpy as np
import scipy.stats
import random
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation 
from nastran_run import run_solver_and_extract_frequencies
from edit_material_prop import edit_file
from nastran_run import run_solver_and_extract_frequencies
import os
import shutil

# Definicja klasy Osobnik
class Osobnik:
    """
    Reprezentacja osobnika w algorytmie genetycznym.

    Atrybuty:
        young (float): Moduł Younga materiału.
        poisson (float): Liczba Poissona materiału.
        dopasowanie (float): Wartość dopasowania osobnika, obliczana na podstawie korelacji Pearsona.
        dopasowanie_Y (float): Dopasowanie modułu Younga.
        dopasowanie_v (float): Dopasowanie liczby Poissona.

    Metody:
        __init__(self, young, poisson): Inicjalizacja nowego osobnika z określonymi parametrami.
        __str__(self): Reprezentacja tekstowa osobnika.
        oblicz_dopasowanie(self, result_solver, result_measurement): Oblicza dopasowanie osobnika na podstawie wyników solvera i pomiarów.
        oblicz_dopasowanie_TEST(self, idealny_Y, idealny_v): Oblicza dopasowanie osobnika do idealnych wartości modułu Younga i liczby Poissona.
    """

    def __init__(self, young, poisson, file_path):
        self.young = young
        self.poisson = poisson
        self.dopasowanie = None
        self.file_path = file_path
        self.freq = None

    def __str__(self):
        return f"Osobnik - Dopasowanie: {self.dopasowanie:.7f}, Moduł Younga: {self.young/1e9:7.3f} GPa, Liczba Poissona: {self.poisson:.3f}"
    

    def oblicz_dopasowanie(self, result_measurement):
        """Oblicz dopasowanie jako znormalizowany błąd średniokwadratowy (MSE) do zakresu [0, 1].

        Args:
            result_measurement (list): idealne wyniki częstotliwości drgań
        """
        # Konwersja częstotliwości obliczonych na float
        freq_float = [float(i) for i in self.freq]

        # Obliczanie MSE
        mse = sum((fm - rm) ** 2 for fm, rm in zip(freq_float, result_measurement)) / len(result_measurement)
        
        # Normalizacja MSE do zakresu [0, 1] przy użyciu funkcji eksponencjalnej
        # Założenie: mniejsze MSE jest lepsze, więc większe dopasowanie oznacza wartość bliższą 1
        self.dopasowanie = 1 / (1 + mse)  # im mniejsze MSE, tym większa wartość dopasowania




    def oblicz_dopasowanie_korelacja(self, result_measurement):
        """Oblicz dopasowanie

        Args:
            result_measurement (list): wyniki z pomiarów (idealne)
        """
        freq_float = [float(i) for i in self.freq]  # Konwersja na listę floatów
        self.dopasowanie = scipy.stats.pearsonr(freq_float, result_measurement)[0]
        
        
    def oblicz_dopasowanie_TEST(self,idealny_Y,idealny_v):
        self.dopasowanie_Y = abs(idealny_Y-self.young)/idealny_Y
        self.dopasowanie_v = abs(idealny_v-self.poisson)/idealny_v
        self.dopasowanie = 1-((self.dopasowanie_v+self.dopasowanie_Y)/2)

    def create_nastran_input_file(self, basemodel):
        params = {'E': self.young, 'NU': self.poisson}
        self.file_path = edit_file(basemodel, params)
    
    def solve_file(self, solver_path):
        self.freq = run_solver_and_extract_frequencies(solver_path, self.file_path)
        



        
def convert_number_to_nastran(value):
    value_str = str(int(value))  # Konwersja value na int, a następnie na string
    if len(value_str) >= 11:
        out = f"{value_str[0]}.{value_str[1:3]}e+{len(value_str)-1}"
    else:
        out = f"{value_str[0]}.{value_str[1:4]}e+{len(value_str)-1}"
    return out

    
# Funkcja generująca losowe wartości
def init_random(template):
    """
    Generuje losowe wartości modułu Younga i liczby Poissona dla nowego osobnika.

    Zwraca:
        Tuple[float, float]: Para wartości (moduł Younga, liczba Poissona).
    """
    young_max = 300e9
    poisson_max = 0.5
    initial_v = (np.random.rand())/2 
    initial_Y = 1e7 + np.random.rand() * (young_max-1e7)
    params = {'E': convert_number_to_nastran(initial_Y), 'NU': initial_v}
    file_path = edit_file(template, params)
    return (initial_Y, initial_v, file_path)


def selekcja(populacja, procent_najlepszych=40):
    """
    Wybiera najlepsze osobniki z populacji na podstawie ich dopasowania.

    Parametry:
        populacja (list[Osobnik]): Lista osobników do selekcji.
        procent_najlepszych (int): Procent najlepszych osobników do wybrania.

    Zwraca:
        list[Osobnik]: Lista najlepszych osobników z populacji.
    """
    # Sortowanie populacji według dopasowania od najlepszego do najgorszego
    posortowana_populacja = sorted(populacja, key=lambda osobnik: osobnik.dopasowanie, reverse=True)
    
    # Obliczanie, ile osobników należy wybrać
    liczba_do_wyboru = len(populacja) * procent_najlepszych // 100
    
    # Zwracanie najlepszych osobników
    return posortowana_populacja[:liczba_do_wyboru]

def krzyzowanie(populacja, liczba_potomkow,template):
    """
    Tworzy nową populację poprzez krzyżowanie osobników z danej populacji.

    Parametry:
        populacja (list[Osobnik]): Lista osobników do krzyżowania.
        liczba_potomkow (int): Liczba potomków do wygenerowania.

    Zwraca:
        list[Osobnik]: Nowa populacja potomków.
    """
    nowa_populacja=[]
    while len(nowa_populacja) < liczba_potomkow:
        parent1,parent2 = random.sample(populacja,2) # losowo wybieracm dwóch rodziców
        new_Y = (parent1.young + parent2.young) /2
        new_v = (parent1.poisson + parent2.poisson) /2
        params = {'E': convert_number_to_nastran(new_Y), 'NU': new_v}
        file_path = edit_file(template, params)
        nowa_populacja.append(Osobnik(new_Y,new_v,file_path))
    return nowa_populacja

def krzyzowanie_z_naciskiem(populacja, liczba_potomkow,template):
    nowa_populacja = []
    while len(nowa_populacja) < liczba_potomkow:
        # Losowo wybieramy dwóch rodziców
        parent1, parent2 = random.sample(populacja, 2)

        # Obliczamy wagi na podstawie dopasowania rodziców
        suma_dopasowan = parent1.dopasowanie + parent2.dopasowanie
        waga1 = parent1.dopasowanie / suma_dopasowan
        waga2 = parent2.dopasowanie / suma_dopasowan

        # Używamy ważonej średniej dla cech
        new_Y = waga1 * parent1.young + waga2 * parent2.young
        new_v = waga1 * parent1.poisson + waga2 * parent2.poisson

        # Tworzymy nowego osobnika z połączonych cech
        params = {'E': convert_number_to_nastran(new_Y), 'NU': new_v}
        file_path = edit_file(template, params)
        nowa_populacja.append(Osobnik(new_Y, new_v, file_path))
        
    return nowa_populacja

def mutacja(populacja, template, coeff=0.6 ):
    """
    Aplikuje mutacje do osobników w populacji z określonym współczynnikiem mutacji.

    Parametry:
        populacja (list[Osobnik]): Lista osobników do mutacji.
        coeff (float): Współczynnik mutacji określający intensywność zmian.

    Zwraca:
        list[Osobnik]: Populacja po mutacji.
    """
    young_max = 300e9
    poisson_max = 0.5-1/1000
    for osobnik in populacja:
        if random.random() < coeff:
            osobnik.young += (random.random() - 0.5) * 2 * young_max * coeff
            osobnik.poisson += (random.random() -0.5) * 2 * poisson_max * coeff/10

            osobnik.young = (min(max(osobnik.young, 1e7), young_max))
            osobnik.poisson = min(max(osobnik.poisson, 0), poisson_max)
            params = {'E': convert_number_to_nastran(osobnik.young), 'NU': osobnik.poisson}
            osobnik.file_path = edit_file(template, params)
    return populacja

def algorytm(coeff):
    # Ścieżka do folderu, który chcesz wyczyścić
    folder_do_wyczyszczenia = r"C:\Users\Grzesiek\Desktop\Doktorat\00_PROJEKT_BADAWCZY\02_SOFTWARE\NASTRAN_INPUT\genetic"

    # Sprawdzenie, czy folder istnieje
    if os.path.exists(folder_do_wyczyszczenia):
        # Iteracja przez wszystkie pliki i foldery wewnątrz folderu
        for nazwa_pliku in os.listdir(folder_do_wyczyszczenia):
            sciezka_pliku = os.path.join(folder_do_wyczyszczenia, nazwa_pliku)
            try:
                # Jeśli to folder, usuń go wraz z zawartością
                if os.path.isdir(sciezka_pliku):
                    shutil.rmtree(sciezka_pliku)
                # Jeśli to plik, usuń plik
                else:
                    os.remove(sciezka_pliku)
            except Exception as e:
                print(f"Błąd podczas usuwania {sciezka_pliku}. Powód: {e}")
    else:
        print("Podany folder nie istnieje.")

    time_start = datetime.datetime.now()
    # Formatowanie i wyświetlanie czasu startu
    formatted_time_start = time_start.strftime("%Y-%m-%d %H:%M:%S")
    print(f'CZAS STARTU:\t{formatted_time_start}')

    # Zmienne systemowe
    solver_path = r'D:\NASTRAN\Nastran\bin\nastran.exe'  # Ścieżka do pliku wykonywalnego solvera
    template = r"C:\Users\Grzesiek\Desktop\Doktorat\00_PROJEKT_BADAWCZY\02_SOFTWARE\NASTRAN_INPUT\nastran_modal.bdf"  # Ścieżka do pliku wejściowego

    # Tworzenie początkowej populacji
    initial_size = 20
    populacja = [Osobnik(*init_random(template)) for _ in range(initial_size)]
    # NOWE - wygeneruj initial_size par liczby NU i E

    
    # DEFINIOWANIE IDEALNEGO WYNIKU
    idealny_Y = 2.000e+11
    idealny_v = 0.3
    idealny_FREQ = [0.0,
                    6695.6,
                    6695.6,
                    14102,
                    14297,
                    14297,
                    1.4341e+005,
                    1.4341e+005,
                    1.9162e+005,
                    1.9196e+005,
                    1.9196e+005,
                    1.9512e+005,
                    1.9512e+005,
                    1.9647e+005,
                    2.2134e+005,
                    2.2135e+005,
                    2.2135e+005,
                    2.2789e+005,
                    2.2919e+005,
                    2.2919e+005]
    liczba_generacji = 0  # Licznik generacji
    max_generacji = 100  # Maksymalna liczba generacji jako warunek bezpieczeństwa
    idealne_dopasowanie = 0.85  # Pożądany poziom dopasowania

    # Ścieżka do folderu, w którym będą zapisywane obrazy
    folder_obrazy = r"C:\Users\Grzesiek\Desktop\Doktorat\00_PROJEKT_BADAWCZY\02_SOFTWARE\NASTRAN_INPUT\IMG"

    # Sprawdzenie, czy folder istnieje, a jeśli nie – jego utworzenie
    if not os.path.exists(folder_obrazy):
        os.makedirs(folder_obrazy)


    while liczba_generacji < max_generacji:
        # NARYSUJ
        x = []
        y = []
                
        # Obliczanie dopasowania dla każdego osobnika
        
        for osobnik in populacja:
            x.append(osobnik.young)
            y.append(osobnik.poisson)
            osobnik.solve_file(solver_path)
            osobnik.oblicz_dopasowanie(idealny_FREQ)
            print(f'DOPASOWANIE:\t{osobnik}')
        

        fig, ax = plt.subplots()
        ax.set_xlim(0, 300e9)  # Zakres dla Young
        ax.set_ylim(-0.5, 0.5)  # Zakres dla Poisson

        scatter = ax.scatter(x, y, s=50, c='b', marker='o')
        scatter = ax.scatter(idealny_Y, idealny_v, s=50, c='r', marker='o')
        plt.draw()

        plt.pause(1)
        xdata, ydata = [], []  # Przenieś deklaracje poza funkcję init 

        # Sprawdzenie, czy któryś z osobników osiągnął pożądane dopasowanie
        if any(osobnik.dopasowanie >= idealne_dopasowanie for osobnik in populacja):
            print("Osiągnięto pożądane dopasowanie!")
            break

        # Selekcja najlepszych osobników
        selekcjonowane = selekcja(populacja)

        # Krzyżowanie wybranych osobników, aby stworzyć nową populację
        populacja = krzyzowanie_z_naciskiem(selekcjonowane, initial_size, template)

        # Mutacja
        populacja = mutacja(populacja, template, coeff)

        # Tutaj dodajemy zapis do pliku
        nazwa_pliku = f"obraz_{liczba_generacji}.png"  # Unikalna nazwa pliku dla każdej generacji
        sciezka_zapisu = os.path.join(folder_obrazy, nazwa_pliku)
        plt.savefig(sciezka_zapisu)  # Zapisz obraz do pliku
        plt.close()  # Zamknij figurę po zapisaniu, aby uniknąć wyświetlania

        liczba_generacji += 1

        

        print(f"Generacja {liczba_generacji} zakończona. Najlepszy osobnik {selekcjonowane[0].dopasowanie} ({selekcjonowane[0].young/1e9:7.3f} GPa, {selekcjonowane[0].poisson:.3f})")
        
    

    # Upewnij się, że wszystkie osobniki mają obliczone dopasowanie
    for osobnik in populacja:
        osobnik.oblicz_dopasowanie_TEST(idealny_Y, idealny_v)

    # Wyszukaj najlepszego osobnika
    najlepszy_osobnik = max(populacja, key=lambda osobnik: osobnik.dopasowanie if osobnik.dopasowanie is not None else 0)

    print(f"Najlepszy: {najlepszy_osobnik}")

    time_end = datetime.datetime.now()
    diff = (time_end-time_start)
    # Przeliczanie na godziny, minuty, sekundy
    godziny = diff.seconds // 3600
    minuty = (diff.seconds % 3600) // 60
    sekundy = diff.seconds % 60

    print(f'CZAS ANALIZY:\t{godziny}h {minuty}m {sekundy}s')

    return(najlepszy_osobnik.dopasowanie)


if __name__ == "__main__":
    algorytm(0.1)
    