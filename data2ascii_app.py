import streamlit as st
import pandas as pd
import numpy as np
import html
import re
from textwrap import dedent

st.set_page_config(page_title="ASCII Plotter", layout="wide")

# -------------------------
# Helper functions
# -------------------------

DEFAULT_CHARSETS = {
    "Shades (.:-=+*#%@)": ".:-=+*#%@",
    "Blocks ( ▁▂▃▄▅▆▇█ )": "▁▂▃▄▅▆▇█",
    "Simple (#)": "#",
    "Simple (*)": "*",
    "Dots ( . o O )": ".oO",
}

def normalize(arr, new_min=0.0, new_max=1.0):
    a = np.array(arr, dtype=float)
    if a.size == 0:
        return a
    mn, mx = np.nanmin(a), np.nanmax(a)
    if mx == mn:
        return np.full_like(a, (new_min + new_max) / 2.0)
    return (a - mn) / (mx - mn) * (new_max - new_min) + new_min

def generate_empty_grid(width, height, fill=" "):
    return [[fill for _ in range(width)] for _ in range(height)]

def grid_to_text_lines(grid):
    return ["".join(row) for row in grid]

def grid_to_colored_html(grid, charset, matrix_values=None, cmap="viridis"):
    import matplotlib
    cm = matplotlib.cm.get_cmap(cmap)
    rows_html = []
    for i in range(len(grid)):
        row_chars = []
        for j in range(len(grid[0])):
            ch = grid[i][j]
            if matrix_values is not None:
                val = matrix_values[i, j]
            else:
                val = charset.find(ch) / max(1, len(charset) - 1) if ch in charset else 0.0
            rgba = cm(val)
            r, g, b, _ = rgba
            hexcol = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
            esc = html.escape(ch)
            if esc == " ":
                esc = "&nbsp;"
            row_chars.append(f"<span style='color:{hexcol};'>{esc}</span>")
        rows_html.append("".join(row_chars))
    return "<pre style='font-family: monospace; line-height: 90%; font-size: 12px; white-space: pre;'>\n" + "\n".join(rows_html) + "\n</pre>"

# -------------------------
# Plot functions
# -------------------------

def ascii_line_plot(x, y, width, height, charset, show_axes=True):
    x, y = np.asarray(x, float), np.asarray(y, float)
    mask = ~np.isnan(x) & ~np.isnan(y)
    if not mask.any():
        return ["(no valid data)"]
    xn, yn = normalize(x[mask], 0, width-1), normalize(y[mask], 0, height-1)
    yn = (height-1) - yn
    grid = generate_empty_grid(width, height)
    for xi, yi in zip(xn, yn):
        grid[int(round(yi))][int(round(xi))] = charset[-1]
    if show_axes:
        for r in range(height):
            grid[r][0] = "|"
        for c in range(width):
            grid[height-1][c] = "-"
        grid[height-1][0] = "+"
    return grid_to_text_lines(grid)

def ascii_scatter_plot(x, y, width, height, marker="o", show_axes=True):
    x, y = np.asarray(x, float), np.asarray(y, float)
    mask = ~np.isnan(x) & ~np.isnan(y)
    if not mask.any():
        return ["(no valid data)"]
    xn, yn = normalize(x[mask], 0, width-1), normalize(y[mask], 0, height-1)
    yn = (height-1) - yn
    grid = generate_empty_grid(width, height)
    for xi, yi in zip(xn, yn):
        grid[int(round(yi))][int(round(xi))] = marker
    if show_axes:
        for r in range(height):
            grid[r][0] = "|"
        for c in range(width):
            grid[height-1][c] = "-"
        grid[height-1][0] = "+"
    return grid_to_text_lines(grid)

def ascii_bar_plot(x, y, width, height, charset):
    y = np.asarray(y, float)
    if y.size == 0:
        return ["(no data)"]
    vals = normalize(y, 0, height-2)
    grid = generate_empty_grid(width, height)
    for i, v in enumerate(vals[:width-2]):
        h = int(round(v*(height-2)))
        for r in range(height-2, height-2-h, -1):
            grid[r][i+1] = charset[-1]
    for c in range(width):
        grid[height-1][c] = "-"
    return grid_to_text_lines(grid)

def ascii_histogram(values, width, height, charset, bins=20):
    vals = np.asarray(values, float)
    vals = vals[~np.isnan(vals)]
    if vals.size == 0:
        return ["(no data)"]
    hist, _ = np.histogram(vals, bins=bins)
    return ascii_bar_plot(range(len(hist)), hist, width, height, charset)

def ascii_heatmap(matrix, width, height, charset):
    a = np.asarray(matrix, float)
    if a.ndim == 1:
        a = a[np.newaxis, :]
    tgt = np.zeros((height, width))
    for i in range(height):
        for j in range(width):
            y0, y1 = int(i*a.shape[0]/height), int((i+1)*a.shape[0]/height)
            x0, x1 = int(j*a.shape[1]/width), int((j+1)*a.shape[1]/width)
            block = a[y0:max(y1,y0+1), x0:max(x1,x0+1)]
            tgt[i, j] = np.nanmean(block)
    normed = normalize(tgt, 0, 1)
    grid = generate_empty_grid(width, height)
    for i in range(height):
        for j in range(width):
            grid[i][j] = charset[int(normed[i,j]*(len(charset)-1))]
    return grid, normed

def ascii_sparkline(values, charset, length=40):
    vals = np.asarray(values, float)
    vals = vals[~np.isnan(vals)]
    if vals.size == 0:
        return "(no data)"
    idx = np.linspace(0, len(vals)-1, length).astype(int)
    normed = normalize(vals[idx], 0, len(charset)-1).astype(int)
    return "".join(charset[i] for i in normed)

# -------------------------
# UI
# -------------------------

st.title("ASCII Plotter — Streamlit (No Matplotlib)")

with st.sidebar:
    st.header("Controls")
    uploaded = st.file_uploader("Upload CSV/JSON", type=["csv","json"])
    sample = st.selectbox("Sample dataset", ["-- none --","Sine wave","Random scatter","Heatmap"])
    plot_type = st.selectbox("Plot type", ["Line","Scatter","Bar","Histogram","Heatmap","Sparkline"])
    charset_choice = st.selectbox("Character set", list(DEFAULT_CHARSETS.keys()))
    custom_charset = st.text_input("Custom charset", value=DEFAULT_CHARSETS[charset_choice])
    width = st.slider("Width (chars)", 40, 150, 80)
    height = st.slider("Height (chars)", 10, 50, 20)
    colored = st.checkbox("Colored ASCII", value=False)

charset = custom_charset or DEFAULT_CHARSETS["Shades (.:-=+*#%@)"]

df, matrix = None, None
if uploaded:
    if uploaded.name.endswith(".json"):
        df = pd.read_json(uploaded)
    else:
        df = pd.read_csv(uploaded)
elif sample == "Sine wave":
    x = np.linspace(0, 4*np.pi, 300)
    df = pd.DataFrame({"x":x,"y":np.sin(x)})
elif sample == "Random scatter":
    df = pd.DataFrame({"x":np.random.randn(200),"y":np.random.randn(200)})
elif sample == "Heatmap":
    xx,yy = np.meshgrid(np.linspace(-2,2,80),np.linspace(-1.5,1.5,40))
    matrix = np.exp(-(xx**2+yy**2))

ascii_text, ascii_html = None, None
if plot_type=="Heatmap" and matrix is not None:
    grid, norm = ascii_heatmap(matrix,width,height,charset)
    if colored:
        ascii_html = grid_to_colored_html(grid,charset,norm)
    else:
        ascii_text = "\n".join(grid_to_text_lines(grid))
elif df is not None:
    numcols = df.select_dtypes(include=[np.number]).columns.tolist()
    if plot_type=="Line" and len(numcols)>=2:
        out = ascii_line_plot(df[numcols[0]],df[numcols[1]],width,height,charset)
        ascii_text = "\n".join(out)
    elif plot_type=="Scatter" and len(numcols)>=2:
        out = ascii_scatter_plot(df[numcols[0]],df[numcols[1]],width,height)
        ascii_text = "\n".join(out)
    elif plot_type=="Bar" and len(numcols)>=1:
        out = ascii_bar_plot(df.index,df[numcols[0]],width,height,charset)
        ascii_text = "\n".join(out)
    elif plot_type=="Histogram" and len(numcols)>=1:
        out = ascii_histogram(df[numcols[0]],width,height,charset)
        ascii_text = "\n".join(out)
    elif plot_type=="Sparkline" and len(numcols)>=1:
        ascii_text = ascii_sparkline(df[numcols[0]],charset,width)

# -------------------------
# Display
# -------------------------

st.subheader("ASCII Output")
if ascii_html:
    st.markdown(ascii_html, unsafe_allow_html=True)
elif ascii_text:
    st.code(ascii_text, language=None)
else:
    st.info("Upload a dataset or choose a sample to begin.")

if ascii_text:
    st.download_button("Download .txt", ascii_text.encode("utf-8"), file_name="ascii_plot.txt", mime="text/plain")
