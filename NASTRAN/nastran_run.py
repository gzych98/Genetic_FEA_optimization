#run Nastran input
#D:\NASTRAN\Nastran\bin\nastran.exe "C:\Users\Grzesiek\Desktop\Doktorat\00_PROJEKT_BADAWCZY\01_MECHANIKA\02_NASTRAN\01_TESTY\A5_Static Structural.bdf" out="C:\Users\Grzesiek\Desktop\Doktorat\00_PROJEKT_BADAWCZY\01_MECHANIKA\02_NASTRAN\01_TESTY\result_test"
from edit_material_prop import edit_file
import os

def run_nastran_solver(input_file, outupt_path, params, solver_path = r'D:\NASTRAN\Nastran\bin\nastran.exe'):
    ...


import re
import subprocess

def run_solver_and_extract_frequencies(solver_path, input_file,eigenmodes = 6):
    # Uruchomienie solvera i oczekiwanie na zakończenie procesu
    out_path = os.path.dirname(input_file)
    # out = 'out= C:\\Users\\Grzesiek\\Desktop\\Doktorat\\00_PROJEKT_BADAWCZY\\01_MECHANIKA\\02_NASTRAN\\02_MODAL_TEST\\do_skryptu'
    out = f'out= {out_path}'
    old = 'old=No'
    subprocess.run([solver_path, input_file, out, old ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    frequencies = []
    new_path = input_file.replace('.bdf', '.f06')    
    line_counter=0
    found_table = False

    with open(new_path, 'r') as file:
        for line in file:
            if "MODAL EFFECTIVE MASS FRACTION" in line:
                found_table = True  # Znaleziono sekcję z częstotliwościami
            elif found_table:
                if line_counter < 5:
                    # Jeszcze nie doszliśmy do danych, inkrementuj licznik linii
                    line_counter += 1
                else:
                    # Jesteśmy w sekcji danych, ekstrahujemy częstotliwości
                    if line.strip() == "":  # Sprawdzenie, czy linia nie jest pusta
                        break
                    columns = line.split()[1]
                    frequencies.append(columns)                   

    return frequencies



if __name__ == '__main__':
    # Przykład użycia funkcji
    solver_path = r'D:\NASTRAN\Nastran\bin\nastran.exe'  # Ścieżka do pliku wykonywalnego solvera
    input_file = r"C:\Users\Grzesiek\Desktop\Doktorat\00_PROJEKT_BADAWCZY\01_MECHANIKA\02_NASTRAN\02_MODAL_TEST\do_skryptu.bdf"  # Ścieżka do pliku wejściowego

    frequencies = run_solver_and_extract_frequencies(solver_path, input_file)
    print(frequencies)