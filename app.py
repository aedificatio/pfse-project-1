import streamlit as st
import crane_runway as cr

import matplotlib.pyplot as plt
import numpy as np
import pycba as cba
from typing import Union, Dict
import math

st.header("Designcalculation of a Crane runway.")
st.write("NOT for use in real-life. \
         No safety factors or instability effects are taken into account.")

# Geometry Parameters
st.sidebar.header("Geometry Parameters")
no_spans = st.sidebar.slider(
    "Number of spans: ", 
    min_value=1, 
    max_value=5, 
    value=3
)
st.sidebar.write("")
spans = {}
for idx, span in enumerate([0] * no_spans,start = 1):
    spans[idx] = st.sidebar.slider(
        f"Span {idx} - Length in (mm):",
        min_value=250, 
        max_value=9000, 
        value=5000,
        step = 250
    )
support_locations = [0]
for idx, _ in enumerate(spans):
    support_to_add = sum(list(spans.values())[0:idx+1])
    support_locations.append(support_to_add)


# Bridge Crane Parameters
st.sidebar.write("")
st.sidebar.header("Bridge Crane Parameters")

crane = cr.Crane()
crane.crane_load = st.sidebar.number_input("Max Crane Load (kN)", value=350, step=10)
st.sidebar.write("(This includes self-weight of the bridge crane)")
crane.no_cranewheels = st.sidebar.slider(
    "Number of crane wheels: ", 
    min_value=1, 
    max_value=4, 
    value=2
)
crane.dist_between_cranewheels = st.sidebar.slider(
    "Distance between crane wheels - Length in (mm):",
    min_value=250, 
    max_value=1500, 
    value=1000,
    step = 250
)


# Steel Properties
steel_properties = st.expander(label="Steel Properties")
with steel_properties:
    st.header("Steel Properties")
    fy = st.number_input("Yield strength (MPa)", value=235)
    E_mod = st.number_input("Elastic modulus (MPa)", value=200e3)
    rho = st.number_input("Density ($kg/m^3$)", value = 7850)


# Section Properties
section_properties = st.expander(label="Section Properties")
with section_properties:
    st.header("Section Properties")
    top_flange_width = st.number_input("Width top flange (mm)", value = 300)
    top_flange_height = st.number_input("Height top flange (mm)", value = 15)
    web_width = st.number_input("Width of the web (mm)", value = 12)
    web_height = st.number_input("Height of the web (mm)", value = 500)
    bot_flange_width = st.number_input("Width bottom flange (mm)", value = 300)
    bot_flange_height = st.number_input("Height bottom flange (mm)", value = 15)

    section = cr.calc_sectionproperties(
        fy=fy, 
        E_mod=E_mod, 
        rho=rho,
        top_flange_width=top_flange_width, 
        top_flange_height=top_flange_height,
        web_width= web_width,
        web_height=web_height,
        bot_flange_width=bot_flange_width,
        bot_flange_height=bot_flange_height
    )

    area = section.get_area() # mm2
    mass = section.get_mass() * 1000 # kg/m1
    ixx, iyy, ixy = section.get_ic()
    height = top_flange_height + web_height + bot_flange_height

    st.write(f"The current section has the following properties:")
    st.write(f"- Mass of {mass:.3f} ($kg/m^1$)")
    st.write(f"- A =  {area:.0f} ($mm^2$)")
    st.write(f"- $I_y$ = {ixx/10000:.0f} ($10^4 mm^4$)")
    st.write(f"- $I_z$ = {iyy/10000:.0f} ($10^4 mm^4$)")

    st.header("Plot Section")
    plot_centroids = section.plot_centroids()
    fig_plot_centroids = plot_centroids.figure
    st.pyplot(fig=fig_plot_centroids)


# Calculate Runway
calculate_runway = st.expander(label="Calculate Crane Runway")
with calculate_runway:

    stepsize: float = 0.05

    results_envelope, results_critical_values, bridge_model = cr.calculate_envelopes(
        E_mod, 
        ixx, 
        spans, 
        mass, 
        crane, 
        stepsize
    )

    pos_x_all = results_envelope.x # Numpy array with x values

    # RESULT AT SELECTED POS
    pos_x_selected = st.slider(
        "Select position of beam crane", 
        min_value = float(min(pos_x_all)),
        max_value = float(max(pos_x_all)),
        value=float(math.floor(pos_x_all.mean())),
        step=stepsize
    )
    result_at_pos = bridge_model.static_vehicle(pos=pos_x_selected)

    fig_M, ax_M, fig_V, ax_V = cr.plot_MV_results(results_envelope, result_at_pos, support_locations)
    st.pyplot(fig=fig_M)
    st.pyplot(fig=fig_V)



# Show Hand Calculation for runway stresses
show_handcalcs = st.expander(label="Show Hand Calculation for runway stresses")
with show_handcalcs:
    st.header("Show Hand Calculation for runway stresses")



# st.write(results_critical_values) # dict met Min max values

# N=1e3
# Vy=3e3
# Mxx=1e6

# stress_post = section.calculate_stress(N=N, Vy=Vy, Mxx=Mxx)
# plot_stress_vm = stress_post.plot_stress_vm()
# fig, ax = plt.subplots()
# ax = plot_centroids

fig = plot_centroids.figure
# axes = fig.add_axes(plot_centroids)
# s = fig.add_axes()





# example_latex_a, factored_load_a = sam.calc_pr_at_given_height(
#     area_a, 
#     i_x_a*1e6, 
#     i_y_a*1e6, 
#     1.0, 
#     1.0, 
#     height_input,
#     E_a, 
#     fy_a, 
#     1.34
#     )





# calc_expander_a = st.expander(label="Sample Calculation, Column A")
# with calc_expander_a:
#     for calc in example_latex_a:
#         st.latex(
#             calc
#         )
