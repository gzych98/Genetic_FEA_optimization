import unittest

def modify_material_properties(line, params):
    '''
    Funkcja modyfikująca wybrane właściwości materiałowe.
    :param line: oryginalna linia tekstu do modyfikacji
    :param params: słownik z parametrami do zmiany, gdzie klucz to nazwa parametru

    
    MATVB - zgodnie z MSC Nastran Quick Reference Guide 2023.1 - strona 2003 PDF
    (moje odkrycie - każde pole ma 8 znaków)
    MAT1 - MID - E - G - NU - RHO - A - TREF - GE
    MAT1 - defines the material properties for linear isotropic materials
    MID - material identification number (int > 0)
    E - Young' modulus (Real >= 0.0 or blank)
    G - Shear modulus (Real >= 0.0 or blank)
    NU - Poisson's ratio (-1.0 < Real <= 0.5 or blank)
    A - Thermal expansion coefficient (Real)
    TREF - Reference temperature for the calculation of thermal loads, 
    or a temperature dependent thermal expansion coefficient
    GE - Structural element damping coefficient

    '''    
    mat = line[0:8]
    mid = line[8:16]
    e = line[16:24]
    g = line[24:32]
    nu = line[32:40]
    rho = line[40:48]
    a = line[48:56]
    tref = line[56:64]
    ge = line[64:72]

    if 'E' in params:
        e = f"{params['E']}"  
    if 'NU' in params:
        nu = f"{params['NU']:.6f}" 

    new_line = f"{mat:<8}{mid:<8}{e:<6}{g:<8}{nu:<8}{rho:<8}{a:<8}{tref:<8}{ge:<8}"

    return new_line


def edit_file(file_path, params):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if line.startswith('MAT'):
            new_props = modify_material_properties(line,params)
            lines[i] = new_props + '\n'
            break
    new_file = f'{file_path.rstrip('.bdf')}_{params['E']}_{params['NU']}.bdf'
    with open(new_file, 'w') as file:
        file.writelines(lines)

    return new_file
        
        
    

class TestExtractMaterialProperties(unittest.TestCase):
    def test_modify_material_properties(self):
        line = "MAT1    1       2.000+11        0.3000007850.0001.200-0522.00000"
        params = {'E': '2.100+11', 'NU' : 0.25}
        expected_result = "MAT1    1       2.100+11        0.2500007850.0001.200-0522.00000        "
        result = modify_material_properties(line,params)
        self.assertEqual(result,expected_result,"Wynik nie zgadza się z oczekiwanym")


if __name__ == '__main__':
    #unittest.main()
    path = r"C:\Users\Grzesiek\Desktop\Doktorat\00_PROJEKT_BADAWCZY\01_MECHANIKA\02_NASTRAN\02_MODAL_TEST\do_skryptu.bdf"
    params = {'E': '2.100+11', 'NU' : 0.25}
    new = edit_file(path,params)
    print(new)