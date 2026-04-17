import streamlit as st
import pandas as pd
from graphviz import Digraph
import itertools

st.set_page_config(layout="wide")

st.title("🌋 Geothermal Conceptual Model Decision Tool")

# -----------------------------
# SESSION STATE INIT
# -----------------------------
if "models" not in st.session_state:
    st.session_state.models = []

if "wells" not in st.session_state:
    st.session_state.wells = []

# -----------------------------
# LEFT PANEL: INPUTS
# -----------------------------
st.sidebar.header("⚙️ Inputs")

# --- Conceptual Models ---
st.sidebar.subheader("Conceptual Models")

model_name = st.sidebar.text_input("Model Name")
model_prob = st.sidebar.number_input("Model Probability", 0.0, 1.0, 0.5)

if st.sidebar.button("Add Model"):
    st.session_state.models.append({
        "name": model_name,
        "prob": model_prob,
        "outcomes": {}
    })

# --- Wells ---
st.sidebar.subheader("Wells")

well_name = st.sidebar.text_input("Well Name")
well_cost = st.sidebar.number_input("Well Cost (M USD)", 0.0, 100.0, 5.0)

if st.sidebar.button("Add Well"):
    st.session_state.wells.append({
        "name": well_name,
        "cost": well_cost
    })

# -----------------------------
# DISPLAY MODELS & WELLS
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("📌 Conceptual Models")
    for m in st.session_state.models:
        st.write(f"{m['name']} (P={m['prob']})")

with col2:
    st.subheader("🛢 Wells")
    for w in st.session_state.wells:
        st.write(f"{w['name']} (${w['cost']}M)")

# -----------------------------
# DEFINE OUTCOMES
# -----------------------------
st.subheader("🎯 Define Outcomes per Model & Well")

for m in st.session_state.models:
    st.markdown(f"### {m['name']}")

    for w in st.session_state.wells:
        st.write(f"**{w['name']}**")

        col_s, col_c, col_f = st.columns(3)

        s = col_s.number_input(f"{m['name']}-{w['name']}-Success", 0.0, 1.0, 0.33, key=f"s_{m['name']}_{w['name']}")
        c = col_c.number_input(f"{m['name']}-{w['name']}-Conditional", 0.0, 1.0, 0.33, key=f"c_{m['name']}_{w['name']}")
        f = col_f.number_input(f"{m['name']}-{w['name']}-Failure", 0.0, 1.0, 0.34, key=f"f_{m['name']}_{w['name']}")

        m["outcomes"][w["name"]] = {
            "Success": s,
            "Conditional": c,
            "Failure": f
        }

# -----------------------------
# SCENARIO GENERATION
# -----------------------------
st.subheader("🌳 Scenario Results")

def generate_scenarios(model, wells):
    scenarios = []

    def recurse(step, prob, cost, path):
        if step == len(wells):
            scenarios.append({
                "Model": model["name"],
                "Path": " → ".join(path),
                "Probability": prob,
                "Cost": cost
            })
            return

        well = wells[step]
        outcomes = model["outcomes"][well["name"]]

        for outcome, p in outcomes.items():
            recurse(
                step + 1,
                prob * p,
                cost + well["cost"],
                path + [f"{well['name']}:{outcome}"]
            )

    recurse(0, model["prob"], 0, [])
    return scenarios

all_scenarios = []

for m in st.session_state.models:
    if len(m["outcomes"]) == len(st.session_state.wells):
        all_scenarios.extend(generate_scenarios(m, st.session_state.wells))

if all_scenarios:
    df = pd.DataFrame(all_scenarios)
    st.dataframe(df)

# -----------------------------
# DECISION TREE VISUALIZATION
# -----------------------------
st.subheader("🌲 Decision Tree")

def build_tree(model, wells):
    dot = Digraph()

    def recurse(parent, step):
        if step >= len(wells):
            return

        well = wells[step]
        outcomes = model["outcomes"][well["name"]]

        for outcome in outcomes:
            node_id = f"{parent}_{well['name']}_{outcome}_{step}"
            label = f"{well['name']} - {outcome}"

            dot.node(node_id, label)
            dot.edge(parent, node_id)

            recurse(node_id, step + 1)

    root = model["name"]
    dot.node(root)

    recurse(root, 0)
    return dot

for m in st.session_state.models:
    if len(m["outcomes"]) == len(st.session_state.wells):
        st.markdown(f"### {m['name']}")
        st.graphviz_chart(build_tree(m, st.session_state.wells))