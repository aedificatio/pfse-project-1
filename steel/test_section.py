import section
from math import isclose

# testdata
M = 100e+6
b = 200
h = 400
Wy = 1/6*b*h**2
Iy= 1/12*b*h**3
e = h/2
stress = 18.75

def test_bending_stress_ixx():
    assert isclose(section.bending_stress_ixx(M, Iy, e), stress)
    
def test_bending_stress_wxx():
    assert isclose(section.bending_stress_wxx(M, Wy), stress)


