import streamlit as st
import crane_runway as cr

import matplotlib.pyplot as plt
import numpy as np
import pycba as cba

st.header("Designcalculation of a Crane runway.")

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


# Bridge Crane Parameters
st.sidebar.write("")
st.sidebar.header("Bridge Crane Parameters")
crane_load = st.sidebar.number_input("Max Crane Load (kN)", value=350, step=10)
st.sidebar.write("(This includes self-weight of the bridge crane)")
no_cranewheels = st.sidebar.slider(
    "Number of crane wheels: ", 
    min_value=1, 
    max_value=4, 
    value=2
)
dist_between_cranewheels = st.sidebar.slider(
    f"Distance between crane wheels - Length in (mm):",
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

    st.write(f"The current section has the following properties:")
    st.write(f"- Mass of {mass:.3f} ($kg/m^1$)")
    st.write(f"- A =  {area:.0f} ($mm^2$)")
    st.write(f"- $I_y$ = {ixx/10000:.0f} ($10^4 mm^4$)")
    st.write(f"- $I_z$ = {iyy/10000:.0f} ($10^4 mm^4$)")


# Plot Section
plot_current_section = st.expander(label="Plot Section")
with plot_current_section:
    st.header("Plot Section")
    plot_centroids = section.plot_centroids()
    fig_plot_centroids = plot_centroids.figure
    st.pyplot(fig=fig_plot_centroids)




# PyCBA
stepsize = 0.0325
EI_spans =  [E_mod * ixx / 1000] * len(spans) # kN/m2
supports = [-1, 0] * (len(spans) + 1) # rigid vertical support, no rotation capacity
UDL = mass / 100 # kN/m1

loads = []
element_types = []
for idx, span in enumerate(spans, start = 1):
    loads.append([idx, 1, UDL, 0, 0]) # beamnr, loadtype, force, start, stop
    element_types.append(1)

spans_in_m = [span / 1000 for span in list(spans.values())]

beam_model = cba.BeamAnalysis(spans_in_m, EI_spans, supports, loads, element_types)
beam_model.analyze()

beam_model.plot_results()
axle_spacings = [4.3, 6.5]
axle_loads = [35, 145, 145]
aashto_truck = cba.Vehicle(axle_spacings=axle_spacings,  axle_weights=axle_loads)
bridge_model = cba.BridgeAnalysis(beam_model, aashto_truck)
bridge_model.static_vehicle(pos=13, plotflag=True)
results = bridge_model.run_vehicle(step=stepsize)
results_envelope = bridge_model.critical_values(results)
st.write(results_envelope)



results_envelope = bridge_model.run_vehicle(step=stepsize, plot_env=True)
pos_x = results_envelope.x
Mmax = -results_envelope.Mmax
Mmin = -results_envelope.Mmin
Vmax = results_envelope.Vmax
Vmin = results_envelope.Vmin

fig1, ax1 = plt.subplots()
ax1.set_ylabel("kNm")
ax1.set_ylabel("kNm")
ax1.set_xlabel("m")
ax1.plot(pos_x, Mmax, "green")
ax1.plot(pos_x, Mmin, "blue")
ax1.fill_between(pos_x, Mmax, color="green", alpha=0.3)
ax1.fill_between(pos_x, Mmin, color="blue", alpha=0.3)

fig1.set_size_inches(7,5)
st.pyplot(fig=fig1)

fig2, ax2 = plt.subplots()
ax2.set_ylabel("kNm")
ax2.set_ylabel("kNm")
ax2.set_xlabel("m")
ax2.plot(pos_x, Vmax, "red")
ax2.plot(pos_x, Vmin, "orange")
ax2.fill_between(pos_x, Vmax, color="red", alpha=0.3)
ax2.fill_between(pos_x, Vmin, color="orange", alpha=0.3)

fig2.set_size_inches(7,5)
st.pyplot(fig=fig2)

N=1e3
Vy=3e3
Mxx=1e6

stress_post = section.calculate_stress(N=N, Vy=Vy, Mxx=Mxx)
plot_stress_vm = stress_post.plot_stress_vm()
fig, ax = plt.subplots()
# ax = plot_centroids

fig = plot_centroids.figure
# axes = fig.add_axes(plot_centroids)
# s = fig.add_axes()










# # Calculation of "resistance lines"
# results = sam.compare_two_columns(
#     min_height,
#     max_height,
#     interval,
#     area_a,
#     i_x_a * 1e6,
#     i_y_a * 1e6,
#     E_a,
#     fy_a,
#     area_b,
#     i_x_b * 1e6,
#     i_y_b * 1e6,
#     E_b,
#     fy_b,
# )

# height_input = st.number_input(label="Height", min_value=min_height, max_value=max_height)
# # Calculation of individual point for plot marker and example calculations
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

# example_latex_b, factored_load_b = sam.calc_pr_at_given_height(
#     area_b, 
#     i_x_b*1e6, 
#     i_y_b*1e6, 
#     1.0, 
#     1.0, 
#     height_input,
#     E_b, 
#     fy_b, 
#     1.34
#     )

# fig = go.Figure()

# # Plot lines
# fig.add_trace(
#     go.Scatter(
#     x=results["a"][1], 
#     y=results["a"][0],
#     line={"color": "red"},
#     name="Column A"
#     )
# )
# fig.add_trace(
#     go.Scatter(
#     x=results["b"][1], 
#     y=results["b"][0],
#     line={"color": "teal"},
#     name="Column B"
#     )
# )

# fig.add_trace(
#     go.Scatter(
#         y=[height_input],
#         x=[factored_load_a],
#         name="Example Calculation: Column A"
#     )
# )

# fig.add_trace(
#     go.Scatter(
#         y=[height_input],
#         x=[factored_load_b],
#         name="Example Calculation: Column B"
#     )
# )

# fig.layout.title.text = "Factored axial resistance of Column A and Column B"
# fig.layout.xaxis.title = "Factored axial resistance, N"
# fig.layout.yaxis.title = "Height of column, mm"


# st.plotly_chart(fig)

# calc_expander_a = st.expander(label="Sample Calculation, Column A")
# with calc_expander_a:
#     for calc in example_latex_a:
#         st.latex(
#             calc
#         )

# calc_expander_b = st.expander(label="Sample Calculation, Column B")
# with calc_expander_b:
#     for calc in example_latex_b:
#         st.latex(
#             calc
#         )