from ansys.mapdl.core import launch_mapdl


# LAUNCH ANSYS
mapdl = launch_mapdl()
print(mapdl)

# CREATE GEOMETRY
box1 = [0,6,-1,1]
box2 = [4,6,-1,-3]
mapdl.prep7()
mapdl.rectng(box1[0],box1[1],box1[2],box1[3])
mapdl.rectng(*box2)
bracket = mapdl.aadd('all')

# DEFINE MATERIAL
ex = 30e6 # Young's Modulos
prxy = 0.27 # Poisson's ratio
mapdl.mp('EX',1,ex)
mapdl.mp('PRXY',1,prxy)

# Define a local element type from the element library
mapdl.et(1, "PLANE183", kop3=3)

# SET ELEMENT THICKNESS
thick = 0.5
mapdl.r(1,thick)

# MESH
element_size = 0.5
mapdl.esize(element_size)
mapdl.amesh(bracket)

# PLOT AREA
#mapdl.aplot(cpos='xy', show_lines=True)

# PLOT ELEMENT
# mapdl.eplot(
#     vtk=True,
#     cpos='xy',
#     show_edges=True,
#     show_axes=False,
#     line_width=2,
#     background='w',
#) 

# BOUNDARY CONDITIONS

mapdl.allsel()
mapdl.solution()

mapdl.antype('STATIC')

bc1 = mapdl.lsel("S","LOC", "X", box1)
print(f'Number of lines selected: {len(bc1)}')

fixNodes = mapdl.nsll(type_="S")
# SET THE BOUNDARY CONDITIONS
mapdl.d("ALL", "ALL",0)
# Select everything again
mapdl.allsel()

p1 = 50

mapdl.lsel("S", "LOC", "Y", box2)
#mapdl.lplot(vtk=True, cpos='xy')

mapdl.sf("ALL", "PRESS",p1)
mapdl.allsel()

# SOLVE MODEL

output=mapdl.solve()

print(output)

mapdl.post1()

result = mapdl.result
result_set = 0 #plotting the first results
disp_fact = 1e10
result.plot_nodal_displacement(result_set,
                               cpos='xy',
                               displacement_factor=5,
                               show_displacement=True,
                               show_edges=True)

result.plot_principal_nodal_stress(
    0,
    "SEQV",
    cpos='xy',
    background ='w',
    text_color='k',
    add_text=True,
    show_edges=True,
)
