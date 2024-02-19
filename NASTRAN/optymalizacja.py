import optuna
from genetic_nastran import algorytm

def objective(trial):
    # Zdefiniuj zakres poszukiwań dla F i CR
    F = trial.suggest_uniform('F', 0.5, 1.5)
    CR = trial.suggest_uniform('CR', 0.1, 1.0)
    initial_size=50
    solver_path = r'D:\NASTRAN\Nastran\bin\nastran.exe'
    template = r"C:\Users\Grzesiek\Desktop\Doktorat\00_PROJEKT_BADAWCZY\02_SOFTWARE\NASTRAN_INPUT\nastran_modal.bdf"
    

    # Tutaj uruchamiamy algorytm ewolucji różnicowej z wybranymi wartościami F i CR
    # Zakładamy, że funkcja `algorytm` zwraca jakąś miarę jakości rozwiązania, np. odwrotność błędu
    # Możesz dostosować tę funkcję do swoich potrzeb
    wynik = algorytm(F, CR, solver_path, template, initial_size)

    return wynik



# Utworzenie obiektu study Optuna i przeprowadzenie optymalizacji
study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=100)

print(f"Najlepsze parametry: {study.best_params}")
print(f"Najlepsze dopasowanie: {1 / study.best_value}")
