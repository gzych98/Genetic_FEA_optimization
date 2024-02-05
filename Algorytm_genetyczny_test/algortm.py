import numpy as np
import scipy.stats
import random
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation 

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

    def __init__(self, young, poisson):
        self.young = young
        self.poisson = poisson
        self.dopasowanie = None
        self.dopasowanie_Y = None
        self.dopasowanie_v = None

    def __str__(self):
        return f"Osobnik - Dopasowanie: {self.dopasowanie}, Moduł Younga: {self.young}, Liczba Poissona: {self.poisson}, Dopsaowanie Y: {self.dopasowanie_Y} - v: {self.dopasowanie_v}"

    def oblicz_dopasowanie(self, result_solver, result_measurement):
        self.dopasowanie = scipy.stats.pearsonr(result_solver, result_measurement)[0]
    
    def oblicz_dopasowanie_TEST(self,idealny_Y,idealny_v):
        self.dopasowanie_Y = abs(idealny_Y-self.young)/idealny_Y
        self.dopasowanie_v = abs(idealny_v-self.poisson)/idealny_v
        self.dopasowanie = 1-((self.dopasowanie_v+self.dopasowanie_Y)/2)
        


    
# Funkcja generująca losowe wartości
def init_random():
    """
    Generuje losowe wartości modułu Younga i liczby Poissona dla nowego osobnika.

    Zwraca:
        Tuple[float, float]: Para wartości (moduł Younga, liczba Poissona).
    """
    young_max = 300e6
    poisson_max = 0.5
    initial_v = (np.random.rand() - 0.5) * 2 * poisson_max
    initial_Y = np.random.rand() * young_max
    # Użycie .item() nie jest tutaj konieczne, ponieważ nie tworzymy macierzy o wymiarach (1,1)
    return (initial_Y, initial_v)


def selekcja(populacja, procent_najlepszych=50):
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

def krzyzowanie(populacja, liczba_potomkow):
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
        nowa_populacja.append(Osobnik(new_Y,new_v))
    return nowa_populacja

def mutacja(populacja, coeff=0.1):
    """
    Aplikuje mutacje do osobników w populacji z określonym współczynnikiem mutacji.

    Parametry:
        populacja (list[Osobnik]): Lista osobników do mutacji.
        coeff (float): Współczynnik mutacji określający intensywność zmian.

    Zwraca:
        list[Osobnik]: Populacja po mutacji.
    """
    young_max = 300e6
    poisson_max = 0.5
    for osobnik in populacja:
        if random.random() < coeff:
            osobnik.young += (random.random() - 0.5) * 2 * young_max * coeff
            osobnik.poisson += (random.random() -0.5) * 2 * poisson_max * coeff

            osobnik.young = (min(max(osobnik.young, 0), young_max))
            osobnik.poisson = min(max(osobnik.poisson, -poisson_max), poisson_max)
    return populacja


if __name__ == "__main__":
    # Tworzenie początkowej populacji
    initial_size = 10
    populacja = [Osobnik(*init_random()) for _ in range(initial_size)]


    # DEFINIOWANIE IDEALNEGO WYNIKU
    idealny_Y = 250e6
    idealny_v = 0.3
    liczba_generacji = 0  # Licznik generacji
    max_generacji = 200  # Maksymalna liczba generacji jako warunek bezpieczeństwa
    idealne_dopasowanie = 0.95  # Pożądany poziom dopasowania


    while liczba_generacji < max_generacji:
        # NARYSUJ
        x = []
        y = []
                
        # Obliczanie dopasowania dla każdego osobnika
        for osobnik in populacja:
            x.append(osobnik.young)
            y.append(osobnik.poisson)
            osobnik.oblicz_dopasowanie_TEST(idealny_Y, idealny_v)

        fig, ax = plt.subplots()
        ax.set_xlim(0, 300e6)  # Zakres dla Young
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
        populacja = krzyzowanie(selekcjonowane, initial_size)

        # Mutacja
        populacja = mutacja(populacja)

        liczba_generacji += 1

        

        print(f"Generacja {liczba_generacji} zakończona. Najlepszy osobnik {selekcjonowane[0].dopasowanie}")

    

    # Upewnij się, że wszystkie osobniki mają obliczone dopasowanie
    for osobnik in populacja:
        osobnik.oblicz_dopasowanie_TEST(idealny_Y, idealny_v)

    # Wyszukaj najlepszego osobnika
    najlepszy_osobnik = max(populacja, key=lambda osobnik: osobnik.dopasowanie if osobnik.dopasowanie is not None else 0)

    print(f"Najlepszy: {najlepszy_osobnik}")
