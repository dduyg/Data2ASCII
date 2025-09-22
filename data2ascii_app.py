import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="ASCII Graph Plotter with Themes", layout="wide")
st.title("🎨 ASCII Graph Plotter with Themes & Sample Data")
st.write("Upload your dataset or choose a sample dataset to visualize with ASCII charts!")

# ---------------------------
# Step 1: Sample Datasets
# ---------------------------
sample_datasets = {
    "Planetary Data": StringIO("""Planet,Diameter_km,Distance_from_Sun_million_km,Moons
Mercury,4879,57.9,0
Venus,12104,108.2,0
Earth,12742,149.6,1
Mars,6779,227.9,2
Jupiter,139820,778.5,79
Saturn,116460,1434,83
Uranus,50724,2871,27
Neptune,49244,4495,14"""),
    
    "RPG Character Stats": StringIO("""Character,Level,HP,Mana,Strength,Agility
Elf,5,120,200,15,25
Warrior,8,250,50,30,10
Mage,7,100,300,10,15
Rogue,6,150,80,20,30
Dragon,10,500,150,50,20"""),
    
    "Ice Cream Survey": StringIO("""Flavor,Votes,Calories,Popularity
Chocolate,120,210,95
Vanilla,80,200,85
Strawberry,50,190,75
Mint,40,180,65
Cookie Dough,70,220,90""")
}

use_sample = st.selectbox("Or select a sample dataset", ["None"] + list(sample_datasets.keys()))
uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx"])

# ---------------------------
# Step 2: Load Dataset
# ---------------------------
df = None
if use_sample != "None":
    df = pd.read_csv(sample_datasets[use_sample])
elif uploaded_file is not None:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

if df is not None:
    st.success("Dataset loaded successfully!")
    st.dataframe(df.head())

    # ---------------------------
    # Step 3: Select Chart Type
    # ---------------------------
    chart_type = st.selectbox("Select chart type", ["Bar Chart", "Line Chart", "Scatter Plot"])

    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    
    if chart_type in ["Bar Chart", "Line Chart"]:
        if len(numeric_cols) == 0:
            st.warning("No numeric columns found!")
        else:
            y_col = st.selectbox("Select numeric column to plot", numeric_cols)
            x_col = None
            if chart_type == "Line Chart":
                x_col = st.selectbox("Select x-axis (optional)", [None] + df.columns.tolist())
    else:  # Scatter
        if len(numeric_cols) < 2:
            st.warning("Need at least two numeric columns for scatter plot!")
        else:
            x_col = st.selectbox("Select X column", numeric_cols)
            y_col = st.selectbox("Select Y column", numeric_cols)

    # ---------------------------
    # Step 4: Chart Size & Theme
    # ---------------------------
    width = st.slider("Chart width", 20, 80, 40)
    height = st.slider("Chart height", 5, 20, 10)
    theme = st.selectbox("Select theme", ["Classic", "Fancy", "Retro"])

    # ---------------------------
    # Step 5: ASCII Chart Functions
    # ---------------------------
    def bar_chart(data, labels, max_width=40, theme="Fancy"):
        if theme == "Classic":
            return "\n".join(f"{label:10} | {'#'*int((v/max(data))*max_width)} {v}" for label, v in zip(labels, data))
        elif theme == "Retro":
            return "\n".join(f"{label:10} | {'='*int((v/max(data))*max_width)} {v}" for label, v in zip(labels, data))
        else:
            gradient = ["░","▒","▓","█"]
            result = []
            max_val = max(data)
            for label, value in zip(labels, data):
                bar_len = int((value / max_val) * max_width)
                full_blocks = bar_len // 4
                remainder = bar_len % 4
                bar = "█"*full_blocks + (gradient[remainder] if remainder else "")
                result.append(f"{label:10} | {bar} {value}")
            return "\n".join(result)

    def line_chart(y_data, x_data=None, height=10, theme="Fancy"):
        max_val, min_val = max(y_data), min(y_data)
        scale = (max_val - min_val)/height or 1
        if x_data is None:
            x_data = list(range(len(y_data)))
        markers = {"Classic":"*","Retro":"o","Fancy":"•"}
        mark = markers.get(theme,"•")
        lines = []
        for level in range(height, -1, -1):
            line_val = min_val + level*scale
            line = f"{line_val:>6.2f} ┤ "
            for y in y_data:
                line += mark+" " if abs(y - line_val)<scale/2 else "  "
            lines.append(line)
        return "\n".join(lines)

    def scatter_plot(x, y, width=40, height=10, theme="Fancy"):
        markers_dict = {"Classic":["*"],"Retro":["o","+"] ,"Fancy":["•","×","+"]}
        markers = markers_dict.get(theme, ["•"])
        min_x, max_x = min(x), max(x)
        min_y, max_y = min(y), max(y)
        grid = [[" " for _ in range(width)] for _ in range(height)]
        for i, (xi, yi) in enumerate(zip(x, y)):
            col = int((xi-min_x)/(max_x-min_x)*(width-1))
            row = height-1 - int((yi-min_y)/(max_y-min_y)*(height-1))
            grid[row][col] = markers[i % len(markers)]
        return "\n".join("".join(row) for row in grid)

    # ---------------------------
    # Step 6: Generate Chart
    # ---------------------------
    chart_text = ""
    if chart_type=="Bar Chart" and y_col:
        chart_text = bar_chart(df[y_col], df.index.astype(str), max_width=width, theme=theme)
    elif chart_type=="Line Chart" and y_col:
        chart_text = line_chart(df[y_col], df[x_col] if x_col else None, height=height, theme=theme)
    elif chart_type=="Scatter Plot" and x_col and y_col:
        chart_text = scatter_plot(df[x_col], df[y_col], width=width, height=height, theme=theme)

    if chart_text:
        st.subheader("ASCII Chart")
        st.text(chart_text)
        st.download_button("Download ASCII Chart", chart_text, file_name="ascii_chart.txt")
