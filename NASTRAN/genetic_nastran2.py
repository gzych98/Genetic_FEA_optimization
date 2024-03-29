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
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        return f"Osobnik - Dopasowanie: {self.dopasowanie:8.1f}, Moduł Younga: {self.young/1e9:7.3f} GPa, Liczba Poissona: {self.poisson:.3f}"
    

    def oblicz_dopasowanie(self, result_measurement):
        """Oblicz dopasowanie jako odwrotność znormalizowanego RMSE, skalowanego do zakresu [0, 1].

        Args:
            result_measurement (list): idealne wyniki częstotliwości drgań
        """
        # Konwersja częstotliwości obliczonych na float
        freq_float = [float(i) for i in self.freq]

        # Obliczanie RMSE
        rmse = np.sqrt(sum((fm - rm) ** 2 for fm, rm in zip(freq_float, result_measurement)) / len(result_measurement))
        
    
        # Skalowanie dopasowania do zakresu [0, 1], gdzie 1 to idealne dopasowanie, a 0 brak dopasowania
        self.dopasowanie = rmse

        return self.dopasowanie




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
    initial_v = np.round((np.random.rand())/2,2) 
    if initial_v == 0.5:
        initial_v = 0.49
    initial_Y = 1e9 + np.random.rand() * (young_max-1e9)
    params = {'E': convert_number_to_nastran(initial_Y), 'NU': initial_v}
    file_path = edit_file(template, params)
    return (initial_Y, initial_v, file_path)


def selekcja2(populacja, procent_najlepszych=40):
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

def mutacja2(populacja, template, coeff=0.6 ):
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

            osobnik.young = (min(max(osobnik.young, 1e9), young_max))
            osobnik.poisson = min(max(osobnik.poisson, 0), poisson_max)
            params = {'E': convert_number_to_nastran(osobnik.young), 'NU': osobnik.poisson}
            osobnik.file_path = edit_file(template, params)
    return populacja
###################################################
# Differential Evolution
###################################################
def mutacja(populacja, template, F):
    """
    W ER mutacja polega na wybraniu trzech różnych wektorów a, b, c z populacji dla każdego targetowego wektora
    x, a następnie utworzeniu wektora mutantu v za pomocą formuły: v = a + F * (b - c), gdzie F jest współczynnikiem mutacji,
    zazwyczaj w przedziale [0.5, 2.0].
    """
    N = len(populacja)
    nowa_populacja = []
    for i in range(N):
        idxs = [idx for idx in range(N) if idx != i]
        a, b, c = np.random.choice(idxs, 3, replace=False)
        mutant_young = populacja[a].young + F * (populacja[b].young - populacja[c].young)
        mutant_poisson = populacja[a].poisson + F * (populacja[b].poisson - populacja[c].poisson)
        
        # Zapewnienie, że wartości są w akceptowalnych zakresach
        mutant_young = np.clip(mutant_young, 1e9, 300e9)
        mutant_poisson = np.clip(mutant_poisson, 0, 0.5-1/1000)
        
        # Utworzenie nowego osobnika z mutowanymi wartościami
        params = {'E': convert_number_to_nastran(mutant_young), 'NU': mutant_poisson}
        file_path = edit_file(template, params)
        nowa_populacja.append(Osobnik(mutant_young, mutant_poisson, file_path))
        
    return nowa_populacja

def rekombinacja(target, mutant, CR, template):
    """
    W każdej iteracji dla każdego osobnika w populacji wykonujemy rekombinację, aby utworzyć nowego osobnika
    testowego, mieszając atrybuty osobnika mutantu z oryginalnym osobnikiem. Stosuje się losowy lub stały
    współczynnik krzyżowania CR [0, 1] do decydowania, które atrybuty są dziedziczone od mutantu.
    """
    # Tworzenie nowego osobnika z atrybutami pochodzącymi z mutanta lub targetu
    new_young = mutant.young if random.random() < CR else target.young
    new_poisson = mutant.poisson if random.random() < CR else target.poisson
    
    # Utworzenie nowego osobnika z połączonych cech
    params = {'E': convert_number_to_nastran(new_young), 'NU': new_poisson}
    file_path = edit_file(template, params)
    new_osobnik = Osobnik(new_young, new_poisson, file_path)
    
    return new_osobnik

def selekcja(populacja, nowa_populacja):
    """
    Porównujemy nowego osobnika z oryginalnym osobnikiem w populacji. Jeśli nowy osobnik ma lepsze 
    dopasowanie, zastępuje oryginalnego osobnika w populacji.
    """
    for i in range(len(populacja)):
        # Zakładam, że funkcja oblicz_dopasowanie jest już zaimplementowana w klasie Osobnik
        # i zwraca wartość dopasowania bezpośrednio z atrybutu osobnika
        if nowa_populacja[i].dopasowanie < populacja[i].dopasowanie:
            populacja[i] = nowa_populacja[i]
    return populacja


def przetwarzaj_osobnika(osobnik, idealny_FREQ, solver_path):
    osobnik.solve_file(solver_path)
    osobnik.oblicz_dopasowanie(idealny_FREQ)
    return osobnik
    
def algorytm(F, CR, solver_path, template, initial_size):
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

    # USTAWIENIA POCZĄTKOWE
    F_increment = 0.2  # Wartość o którą zwiększamy F
    CR_increment = 0.2  # Wartość o którą zwiększamy CR
    threshold = 100  # Próg dla różnicy w dopasowaniu, poniżej którego uznajemy, że algorytm wpadł w minimum lokalne
    # Ustawienia dla dekrementacji
    F_decrement = 0.1  # Wartość o którą zmniejszamy F
    CR_decrement = 0.1  # Wartość o którą zmniejszamy CR
    large_difference_threshold = 1000  # Próg dla "dużej" różnicy w dopasowaniu
    najlepsze_dopasowanie_w_poprzedniej_generacji = None

    # Tworzenie początkowej populacji    
    populacja = [Osobnik(*init_random(template)) for _ in range(initial_size)]   

    
    # DEFINIOWANIE IDEALNEGO WYNIKU
    idealny_Y = 2.000e+11
    idealny_v = 0.3
    idealny_FREQ = [1.617939E-02,
                    1.075608E+04,
                    1.075608E+04,
                    2.255294E+04,
                    2.255294E+04,
                    2.265445E+04,
                    1.382356E+05,
                    1.382356E+05,
                    1.757281E+05,
                    1.766887E+05,
                    1.766887E+05,
                    1.925443E+05,
                    1.925443E+05,
                    1.925518E+05,
                    1.939036E+05,
                    2.081178E+05,
                    2.125266E+05,
                    2.125266E+05,
                    2.164848E+05,
                    2.164848E+05]
    liczba_generacji = 0  # Licznik generacji
    max_generacji = 100  # Maksymalna liczba generacji jako warunek bezpieczeństwa
    idealne_dopasowanie = 500  # Pożądany poziom dopasowania

    # Ścieżka do folderu, w którym będą zapisywane obrazy
    folder_obrazy = r"C:\Users\Grzesiek\Desktop\Doktorat\00_PROJEKT_BADAWCZY\02_SOFTWARE\NASTRAN_INPUT\IMG"

    # Sprawdzenie, czy folder istnieje, a jeśli nie – jego utworzenie
    if not os.path.exists(folder_obrazy):
        os.makedirs(folder_obrazy)

        
    while liczba_generacji < max_generacji:
        x = []
        y = []
                
        # Obliczanie dopasowania dla każdego osobnika

        # Ustawienie liczby wątków na 2, ale można dostosować do możliwości sprzętowych
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Użycie mapowania executora do przetwarzania listy osobników równolegle
            future_to_osobnik = {executor.submit(przetwarzaj_osobnika, osobnik, idealny_FREQ, solver_path): osobnik for osobnik in populacja}
            
            for future in as_completed(future_to_osobnik):
                osobnik = future_to_osobnik[future]
                try:
                    data = future.result()
                except Exception as exc:
                    print(f'{osobnik} wygenerował wyjątek: {exc}')
                else:
                    print(f'{liczba_generacji:4} - DOPASOWANIE:\t{data}')
        
        # for index, osobnik in enumerate(populacja):
        #     osobnik.solve_file(solver_path)
        #     osobnik.oblicz_dopasowanie(idealny_FREQ)
        #     print(f'{liczba_generacji:4} - {index:3} DOPASOWANIE:\t{osobnik}')
        #     # Sprawdzenie, czy któryś z osobników osiągnął pożądane dopasowanie
            

        if any((osobnik.dopasowanie <= idealne_dopasowanie and osobnik.dopasowanie != 0.0) for osobnik in populacja):
            print("Osiągnięto pożądane dopasowanie!")
            break 

        populacja_mod = selekcja2(populacja, procent_najlepszych=30)
        populacja_mod = krzyzowanie_z_naciskiem(populacja, initial_size, template)
        
        # Mutacja i rekombinacja
        mutowana_populacja = mutacja(populacja_mod, template, F)
        rekombinowana_populacja = [rekombinacja(populacja_mod[i], mutowana_populacja[i], CR, template) for i in range(len(populacja_mod))]

        # Ustawienie liczby wątków na 2, ale można dostosować do możliwości sprzętowych
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Użycie mapowania executora do przetwarzania listy osobników równolegle
            future_to_osobnik = {executor.submit(przetwarzaj_osobnika, osobnik, idealny_FREQ, solver_path): osobnik for osobnik in rekombinowana_populacja}
            
            for future in as_completed(future_to_osobnik):
                osobnik = future_to_osobnik[future]
                try:
                    data = future.result()
                except Exception as exc:
                    print(f'{osobnik} wygenerował wyjątek: {exc}')
                else:
                    print(f'{liczba_generacji:4} - DOPASOWANIE:\t{data}')
        
        # Ponowne obliczenie dopasowania dla rekombinowanych osobników
        # for osobnik in rekombinowana_populacja:
        #     osobnik.solve_file(solver_path)
        #     osobnik.oblicz_dopasowanie(idealny_FREQ)
        #     print(f'{liczba_generacji:4} -  DOPASOWANIE:\t{osobnik}')
        #     index -=1

        if any((osobnik.dopasowanie <= idealne_dopasowanie and osobnik.dopasowanie != 0.0) for osobnik in populacja):
            print("Osiągnięto pożądane dopasowanie!")
            break 
        # Selekcja
        populacja = selekcja(populacja, rekombinowana_populacja)

        for osobnik in populacja:            
            x.append(osobnik.young)
            y.append(osobnik.poisson)
        

        # Oblicz najlepsze dopasowanie w obecnej generacji
        obecne_najlepsze_dopasowanie = min(osobnik.dopasowanie for osobnik in populacja)
        print(f'NAJLEPSZE: {obecne_najlepsze_dopasowanie}')
        
        # # Sprawdź, czy różnica w dopasowaniu jest duża
        # if najlepsze_dopasowanie_w_poprzedniej_generacji is not None:
        #     roznica_dopasowania = -(obecne_najlepsze_dopasowanie) + najlepsze_dopasowanie_w_poprzedniej_generacji
        #     print(f'Różnica dopasowania: {roznica_dopasowania}')
        #     if roznica_dopasowania < threshold:
        #         # Zwiększ F i CR, jeśli algorytm wpadł w minimum lokalne
        #         F += F_increment
        #         CR += CR_increment
        #         print(f"Zwiększono F do {F} i CR do {CR} aby wyjść z minimum lokalnego.")
        #     elif roznica_dopasowania >= large_difference_threshold:
        #         # Zmniejsz F i CR, jeśli algorytm jest blisko optymalnego rozwiązania
        #         F = max(F - F_decrement, 0.1)  # Ustaw dolny limit, aby nie zmniejszyć zbyt mocno
        #         CR = max(CR - CR_decrement, 0.1)
        #         print(f"Zmniejszono F do {F} i CR do {CR} aby skupić się na eksploatacji.")
        
        # najlepsze_dopasowanie_w_poprzedniej_generacji = obecne_najlepsze_dopasowanie


        # Sprawdzenie, czy któryś z osobników osiągnął pożądane dopasowanie
        if any(osobnik.dopasowanie <= idealne_dopasowanie for osobnik in populacja):
            print("Osiągnięto pożądane dopasowanie!")
            break        

        # Zapis do pliku        
        fig, ax = plt.subplots()
        ax.set_xlim(0, 300e9)  # Zakres dla Young
        ax.set_ylim(-0.5, 0.5)  # Zakres dla Poisson
        scatter = ax.scatter(x, y, s=50, c='b', marker='o')
        scatter = ax.scatter(idealny_Y, idealny_v, s=50, c='r', marker='o')
        plt.draw()
        nazwa_pliku = f"obraz_{liczba_generacji}.png"  # Unikalna nazwa pliku dla każdej generacji
        sciezka_zapisu = os.path.join(folder_obrazy, nazwa_pliku)
        plt.savefig(sciezka_zapisu)  # Zapisz obraz do pliku
        plt.close()  # Zamknij figurę po zapisaniu, aby uniknąć wyświetlania

        liczba_generacji += 1        

        print(f"Generacja {liczba_generacji} zakończona.")
        
    

    # Upewnij się, że wszystkie osobniki mają obliczone dopasowanie
    for osobnik in populacja:
        osobnik.oblicz_dopasowanie(idealny_FREQ)

    # Wyszukaj najlepszego osobnika
    najlepszy_osobnik = min(populacja, key=lambda osobnik: osobnik.dopasowanie if osobnik.dopasowanie is not None else 0)

    print(f"Najlepszy: {najlepszy_osobnik}")

    time_end = datetime.datetime.now()

    diff = (time_end-time_start)
    # Przeliczanie na godziny, minuty, sekundy
    godziny = diff.seconds // 3600
    minuty = (diff.seconds % 3600) // 60
    sekundy = diff.seconds % 60

    print(f'CZAS ANALIZY:\t{godziny}h {minuty}m {sekundy}s')

    return(diff)


if __name__ == "__main__":
    F = 0.1 # współczynnik mutacji
    CR = 0.5 # współczynnik rekombinacji
    initial_size=50
    solver_path = r'D:\NASTRAN\Nastran\bin\nastran.exe'
    template = r"C:\Users\Grzesiek\Desktop\Doktorat\00_PROJEKT_BADAWCZY\02_SOFTWARE\NASTRAN_INPUT\nastran_modal.bdf"
    najlepsze_dopasowanie = algorytm(F, CR, solver_path, template, initial_size)
    print(f'Wynik analizy: {najlepsze_dopasowanie}')
    
