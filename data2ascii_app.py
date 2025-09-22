import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="ASCII Graph Plotter", layout="wide")
st.title("ASCII Graph Plotter 🏹")
st.write("Upload your dataset or select a sample dataset to visualize with ASCII charts!")

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
    chart_type = st.selectbox("Select chart type", ["Vertical Bar Chart", "Horizontal Bar Chart", "Line Chart", "Scatter Plot"])

    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    
    if chart_type in ["Vertical Bar Chart", "Horizontal Bar Chart", "Line Chart"]:
        if len(numeric_cols) == 0:
            st.warning("No numeric columns found!")
        else:
            y_col = st.selectbox("Select numeric column to plot", numeric_cols)
            x_col = None
            if chart_type == "Line Chart":
                x_col = st.selectbox("Select x-axis (optional)", [None] + df.columns.tolist())
    elif chart_type == "Scatter Plot":
        if len(numeric_cols) < 2:
            st.warning("Need at least two numeric columns for scatter plot!")
        else:
            x_col = st.selectbox("Select X column", numeric_cols)
            y_col = st.selectbox("Select Y column", numeric_cols)

    # ---------------------------
    # Step 4: Chart Size
    # ---------------------------
    width = st.slider("Chart width", 10, 80, 40)
    height = st.slider("Chart height", 5, 20, 10)

    # ---------------------------
    # Step 5: ASCII Chart Functions
    # ---------------------------

    # Vertical Bar Chart
    def vertical_bar_chart(values, labels, height=10):
        max_val = max(values)
        scale = max_val / height
        chart_lines = []
        for i in range(height, 0, -1):
            line = f"{int(i*scale):>3} ┤ "
            for val in values:
                line += "█   " if val >= i*scale else "    "
            chart_lines.append(line)
        chart_lines.append("  0 ┼" + "────"*len(values))
        label_line = "     "
        for label in labels:
            label_line += f"{label:<4}"
        chart_lines.append(label_line)
        return "\n".join(chart_lines)

    # Horizontal Bar Chart
    def horizontal_bar_chart(values, labels, max_width=20):
        gradient = ["░", "▒", "▓", "█"]
        max_val = max(values)
        chart_lines = []
        for label, val in zip(labels, values):
            bar_len = int((val / max_val) * max_width)
            full_blocks = bar_len // 4
            remainder = bar_len % 4
            bar = "█"*full_blocks + (gradient[remainder] if remainder else "")
            chart_lines.append(f"{label:<10} | {bar:<{max_width}} {val}")
        return "\n".join(chart_lines)

    # Line Chart
    def line_chart(y_data, height=10):
        max_val = max(y_data)
        min_val = min(y_data)
        scale = (max_val - min_val)/height or 1
        chart_lines = []
        for level in range(height, 0, -1):
            line_val = min_val + level*scale
            line = f"{int(line_val):>3} ┤ "
            for y in y_data:
                line += "╭─╮" if abs(y - line_val) < scale/2 else "   "
            chart_lines.append(line)
        chart_lines.append(f"{int(min(y_data))} ┼" + "───"*len(y_data))
        x_labels = "     "
        for i in range(len(y_data)):
            x_labels += f"{i:<3}"
        chart_lines.append(x_labels)
        return "\n".join(chart_lines)

    # Scatter Plot
    def scatter_plot(x, y, width=40, height=10):
        min_x, max_x = min(x), max(x)
        min_y, max_y = min(y), max(y)
        grid = [[" " for _ in range(width)] for _ in range(height)]
        for xi, yi in zip(x, y):
            col = int((xi - min_x)/(max_x - min_x)*(width-1))
            row = height - 1 - int((yi - min_y)/(max_y - min_y)*(height-1))
            grid[row][col] = "•"
        chart_lines = []
        for i, row in enumerate(grid):
            chart_lines.append(f"{int(max_y - i*(max_y-min_y)/height):>3} | " + "".join(row))
        chart_lines.append("    " + "-"*width)
        x_labels = "     "
        for xi in range(width):
            x_val = int(min_x + xi*(max_x-min_x)/(width-1))
            x_labels += f"{x_val%10}"
        chart_lines.append(x_labels)
        return "\n".join(chart_lines)

    # ---------------------------
    # Step 6: Generate Chart
    # ---------------------------
    chart_text = ""
    if chart_type == "Vertical Bar Chart" and y_col:
        chart_text = vertical_bar_chart(df[y_col], df.index.astype(str), height=height)
    elif chart_type == "Horizontal Bar Chart" and y_col:
        chart_text = horizontal_bar_chart(df[y_col], df.index.astype(str), max_width=width)
    elif chart_type == "Line Chart" and y_col:
        chart_text = line_chart(df[y_col], height=height)
    elif chart_type == "Scatter Plot" and x_col and y_col:
        chart_text = scatter_plot(df[x_col], df[y_col], width=width, height=height)

    if chart_text:
        st.subheader("ASCII Chart")
        st.text(chart_text)
        st.download_button("Download ASCII Chart", chart_text, file_name="ascii_chart.txt")
