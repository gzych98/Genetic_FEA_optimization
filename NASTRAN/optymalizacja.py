import optuna
from genetic_nastran import algorytm

def objective(trial):
    coeff = trial.suggest_uniform('coeff', 0.1, 1.0)  # Przykład hiperparametru
    # Tutaj uruchom swój algorytm genetyczny z danym coeff i zwróć wynik jako wartość do optymalizacji
    wynik = algorytm(coeff)
    return wynik

study = optuna.create_study(direction='minimize')
study.optimize(objective, n_trials=100)

print(study.best_params)