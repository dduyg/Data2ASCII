import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from textwrap import dedent


st.set_page_config(page_title="Ascii Plotter", layout="wide")


-------------------- Utilities --------------------


def to_text_download(content: str, filename: str = "ascii_plot.txt"):
return content


def numeric_df(df: pd.DataFrame):
return df.select_dtypes(include=[np.number])


def scale_to_range(arr, new_min, new_max):
a = np.array(arr, dtype=float)
if np.all(np.isnan(a)):
return np.full_like(a, (new_min + new_max) / 2)
a_min = np.nanmin(a)
a_max = np.nanmax(a)
if a_max - a_min == 0:
return np.full_like(a, (new_min + new_max) / 2)
return new_min + (a - a_min) * (new_max - new_min) / (a_max - a_min)


def color_for_value(v, vmin, vmax):
# returns hex color mapping value to a red->yellow->green scale
if np.isnan(v):
return "#888888"
ratio = 0 if vmax==vmin else (v - vmin) / (vmax - vmin)
# green to red
r = int(255 * ratio)
g = int(255 * (1 - ratio))
b = 0
return f"#{r:02x}{g:02x}{b:02x}"


-------------------- ASCII rendering --------------------


def render_ascii_line(x, y, width, height, char="*", fill=False, bg_char=" "):
canvas = [[bg_char for _ in range(width)] for _ in range(height)]
# scale x to 0..width-1
xs = scale_to_range(x, 0, width - 1).astype(int)
ys = scale_to_range(y, 0, height - 1).astype(int)
# flip y: 0 at top -> we want 0 at bottom
ys = (height - 1) - ys


# draw points
for xi, yi in zip(xs, ys):
    if 0 <= yi < height and 0 <= xi < width:
        canvas[yi][xi] = char

# optionally connect with lines (Bresenham-like)
for i in range(1, len(xs)):
    x0, y0 = xs[i-1], ys[i-1]
    x1, y1 = xs[i], ys[i]
    dx = x1 - x0
    dy = y1 - y0
    steps = max(abs(dx), abs(dy))
    if steps == 0:
        continue
    for s in range(1, steps+1):
        xp = int(round(x0 + dx * s / steps))
        yp = int(round(y0 + dy * s / steps))
        if 0 <= yp < height and 0 <= xp < width:
            canvas[yp][xp] = char

# optionally fill under curve
if fill:
    for col in range(width):
        # find first non-bg from top
        row_idx = None
        for row in range(height):
            if canvas[row][col] != bg_char:
                row_idx = row
                break
        if row_idx is not None:
            for r in range(row_idx+1, height):
                canvas[r][col] = char

lines = ["".join(row) for row in canvas]
return "\n".join(lines)



def render_ascii_scatter(x, y, width, height, char="o", bg_char=" "):
canvas = [[bg_char for _ in range(width)] for _ in range(height)]
xs = scale_to_range(x, 0, width - 1).astype(int)
ys = scale_to_range(y, 0, height - 1).astype(int)
ys = (height - 1) - ys
for xi, yi in zip(xs, ys):
canvas[yi][xi] = char
return "\n".join("".join(r) for r in canvas)


def render_ascii_bars(categories, values, width, height, char="#", horizontal=False):
if horizontal:
# each row corresponds to a category
lines = []
vals = scale_to_range(values, 0, width)
for cat, v in zip(categories, vals):
bar = char * int(round(v))
label = f"{cat}: "
lines.append(label + bar)
return "\n".join(lines)
else:
# vertical bars across width
canvas = [[" " for _ in range(width)] for _ in range(height)]
n = min(len(values), width)
vals = scale_to_range(values[:n], 0, height-1).astype(int)
for i, val in enumerate(vals):
for h in range(val+1):
canvas[height - 1 - h][i] = char
return "\n".join("".join(r) for r in canvas)


def render_ascii_histogram(values, width, height, bins=20, char="#"):
counts, edges = np.histogram(values[~np.isnan(values)], bins=bins)
# render vertical bars scaled to height
vals = scale_to_range(counts, 0, height-1).astype(int)
# ensure width matches bins
w = min(width, bins)
# compress counts into w columns
if bins > w:
factor = bins // w
vals = np.array([np.sum(vals[i*factor:(i+1)*factor]) for i in range(w)])
vals = scale_to_range(vals, 0, height-1).astype(int)
canvas = [[" " for _ in range(w)] for _ in range(height)]
for i, v in enumerate(vals):
for h in range(v+1):
canvas[height - 1 - h][i] = char
return "\n".join("".join(r) for r in canvas)


def render_ascii_heatmap(matrix, width, height, shading=".:-=+*#%@"):
# matrix: 2D numpy array
mat = np.array(matrix, dtype=float)
h0, w0 = mat.shape
# resample to (height, width)
ys = np.linspace(0, h0 - 1, height)
xs = np.linspace(0, w0 - 1, width)
new = np.zeros((height, width))
for i, y in enumerate(ys):
for j, x in enumerate(xs):
new[i,j] = mat[int(round(y)), int(round(x))]
vmin = np.nanmin(new)
vmax = np.nanmax(new)
levels = len(shading) - 1
out_lines = []
for i in range(height):
row_chars = []
for j in range(width):
val = new[i,j]
if np.isnan(val):
ch = " "
else:
idx = int(round((val - vmin) / (vmax - vmin + 1e-12) * levels))
ch = shading[idx]
row_chars.append(ch)
out_lines.append("".join(row_chars))
return "\n".join(out_lines), vmin, vmax


def colorize_ascii(ascii_art: str, vmin=None, vmax=None, matrix_vals=None, shading=None):
# matrix_vals is optional flattened list matching chars if needed for heatmap
# For simplicity, if matrix_vals provided, color by value, otherwise gray
lines = ascii_art.splitlines()
html_lines = []
if matrix_vals is not None and vmin is not None and vmax is not None:
mat = np.array(matrix_vals).reshape(len(lines), -1)
for i, row in enumerate(lines):
html_row = ""
for j, ch in enumerate(row):
val = mat[i, j]
color = color_for_value(val, vmin, vmax)
safe_ch = ch if ch != ' ' else ' '
html_row += f"{safe_ch}"
html_lines.append(html_row)
else:
for row in lines:
html_lines.append(''.join([f"{(ch if ch!=' ' else ' ')}" for ch in row]))
return "
{}
".format("\n".join(html_lines))



-------------------- Demo datasets --------------------


def demo_dataset(name):
if name == 'Sine Wave':
x = np.linspace(0, 4*np.pi, 200)
y = np.sin(x) + np.random.normal(scale=0.05, size=x.shape)
return pd.DataFrame({'x': x, 'y': y})
if name == 'Random Walk':
n = 200
r = np.cumsum(np.random.randn(n))
return pd.DataFrame({'t': np.arange(n), 'value': r})
if name == 'Heatmap Demo':
x = np.linspace(-3, 3, 80)
y = np.linspace(-3, 3, 60)
X, Y = np.meshgrid(x, y)
Z = np.exp(-(X2 + Y2))
df = pd.DataFrame(Z)
return df
if name == 'Iris (numeric)':
# simple synthetic-ish iris numeric columns
np.random.seed(0)
return pd.DataFrame({
'sepal_length': np.random.normal(5.8, 0.35, 150),
'sepal_width': np.random.normal(3.0, 0.38, 150),
'petal_length': np.random.normal(3.7, 1.5, 150),
'petal_width': np.random.normal(1.15, 0.6, 150),
})
# fallback
return pd.DataFrame({
'a': np.random.randn(100),
'b': np.random.randn(100)
})


-------------------- Streamlit UI --------------------


st.title("Ascii Plotter — Streamlit")
st.markdown("Create beautiful ASCII plots and export them as text — monospace-ready for README or terminals.")


Sidebar controls


st.sidebar.header("Data & Plot Settings")
upload = st.sidebar.file_uploader("Upload CSV or Excel", type=['csv', 'xlsx', 'xls'], accept_multiple_files=False)
use_demo = st.sidebar.selectbox("Or use a demo dataset:", ['None', 'Sine Wave', 'Random Walk', 'Heatmap Demo', 'Iris (numeric)'])


if upload is not None:
try:
if upload.name.endswith(('xls', 'xlsx')):
df = pd.read_excel(upload)
else:
df = pd.read_csv(upload)
except Exception as e:
st.error(f"Failed to read file: {e}")
st.stop()
elif use_demo != 'None':
df = demo_dataset(use_demo)
else:
st.info('Upload a CSV/Excel or select a demo dataset to begin.')
st.stop()


st.sidebar.markdown(f"Dataset shape: {df.shape}")


numeric = numeric_df(df)


col1, col2 = st.sidebar.columns(2)
plot_type = st.sidebar.selectbox("Plot type", ['Line', 'Scatter', 'Bar', 'Histogram', 'Heatmap', 'Sparkline'])


if plot_type in ['Line', 'Scatter']:
x_col = st.sidebar.selectbox("X column", options=numeric.columns.tolist(), index=0 if len(numeric.columns)>0 else None)
y_col = st.sidebar.selectbox("Y column", options=numeric.columns.tolist(), index=1 if len(numeric.columns)>1 else 0)
elif plot_type == 'Bar':
# for bar, allow category + value
all_cols = df.columns.tolist()
cat_col = st.sidebar.selectbox("Category column (optional)", options=[None] + all_cols, index=0)
if cat_col:
val_col = st.sidebar.selectbox("Value column", options=numeric.columns.tolist())
else:
val_col = st.sidebar.selectbox("Value column", options=numeric.columns.tolist())
elif plot_type == 'Histogram':
hist_col = st.sidebar.selectbox("Column", options=numeric.columns.tolist())
elif plot_type == 'Heatmap':
# heatmap uses full numeric DF or selected columns
heat_cols = st.sidebar.multiselect("Columns to include (rows remain)", options=numeric.columns.tolist(), default=numeric.columns.tolist()[:min(6, len(numeric.columns))])
if len(heat_cols) < 1:
st.sidebar.warning('Please select at least one numeric column for heatmap.')
elif plot_type == 'Sparkline':
spark_col = st.sidebar.selectbox("Column", options=numeric.columns.tolist())


char_preset = st.sidebar.selectbox("Character set", ['#', '', '.:-=+#@%', '▁▂▃▄▅▆▇█', '@%#*+=-:.'])
width = st.sidebar.slider("Width (characters)", min_value=20, max_value=200, value=80)
height = st.sidebar.slider("Height (characters)", min_value=5, max_value=80, value=24)
colored = st.sidebar.checkbox("Colored ASCII (HTML)", value=False)
show_mpl = st.sidebar.checkbox("Show Matplotlib/Plotly comparison", value=True)
fill_under = st.sidebar.checkbox("Fill under curve (line plot)", value=False)


st.sidebar.markdown("---")
if st.sidebar.button('Download current ASCII as txt'):
st.experimental_set_query_params(_download='1')


-------------------- Build ASCII --------------------


ascii_art = ""
color_html = None


try:
if plot_type == 'Line':
x = numeric[x_col].values
y = numeric[y_col].values
ascii_art = render_ascii_line(x, y, width=width, height=height, char=char_preset[0], fill=fill_under)
if colored:
# color by y values (heatmap along vertical)
# build matrix vals matching lines
# For line, build matrix of NaNs and set points to y scaled
canvas_vals = np.full((height, width), np.nan)
xs = scale_to_range(x, 0, width - 1).astype(int)
ys = scale_to_range(y, 0, height - 1).astype(float)
ys = (height - 1) - ys
for xi, yi, val in zip(xs, ys, y):
if 0 <= int(yi) < height:
canvas_vals[int(yi), int(xi)] = val
vmin, vmax = np.nanmin(y), np.nanmax(y)
color_html = colorize_ascii(ascii_art, vmin=vmin, vmax=vmax, matrix_vals=canvas_vals.flatten())


elif plot_type == 'Scatter':
    x = numeric[x_col].values
    y = numeric[y_col].values
    ascii_art = render_ascii_scatter(x, y, width=width, height=height, char=char_preset[0])
    if colored:
        canvas_vals = np.full((height, width), np.nan)
        xs = scale_to_range(x, 0, width - 1).astype(int)
        ys = scale_to_range(y, 0, height - 1).astype(float)
        ys = (height - 1) - ys
        for xi, yi, val in zip(xs, ys, y):
            if 0 <= int(yi) < height:
                canvas_vals[int(yi), int(xi)] = val
        color_html = colorize_ascii(ascii_art, vmin=np.nanmin(y), vmax=np.nanmax(y), matrix_vals=canvas_vals.flatten())

elif plot_type == 'Bar':
    if cat_col:
        cats = df[cat_col].astype(str).values
        vals = numeric[val_col].values
        ascii_art = render_ascii_bars(cats, vals, width=width, height=height, char=char_preset[0], horizontal=True)
    else:
        vals = numeric[val_col].values
        ascii_art = render_ascii_bars(list(range(len(vals))), vals, width=width, height=height, char=char_preset[0], horizontal=False)

elif plot_type == 'Histogram':
    vals = numeric[hist_col].values
    ascii_art = render_ascii_histogram(vals, width=width, height=height, bins=width, char=char_preset[0])

elif plot_type == 'Heatmap':
    # build numeric matrix from selected columns; if user selected multiple cols, use DataFrame values
    mat = numeric[heat_cols].values if heat_cols and len(heat_cols)>0 else numeric.values
    # If mat is 1D (single column), reshape using row count x 1
    if mat.ndim == 1:
        mat = mat.reshape(-1, 1)
    hm_text, vmin, vmax = render_ascii_heatmap(mat, width=width, height=height, shading=char_preset if len(char_preset)>1 else '.:-=+*#%@')
    ascii_art = hm_text
    if colored:
        # color by matrix
        # resample mat to height x width like renderer did
        # reuse renderer's interpolation to build new matrix used for coloring
        h0, w0 = mat.shape
        ys = np.linspace(0, h0 - 1, height)
        xs = np.linspace(0, w0 - 1, width)
        new = np.zeros((height, width))
        for i, y in enumerate(ys):
            for j, x in enumerate(xs):
                new[i,j] = mat[int(round(y)), int(round(x))]
        color_html = colorize_ascii(ascii_art, vmin=vmin, vmax=vmax, matrix_vals=new.flatten())

elif plot_type == 'Sparkline':
    vals = numeric[spark_col].values
    # map values to block chars
    blocks = '▁▂▃▄▅▆▇█'
    scaled = scale_to_range(vals, 0, len(blocks)-1).astype(int)
    ascii_art = ''.join(blocks[i] for i in scaled)



except Exception as e:
st.error(f"Failed to render ASCII: {e}")
st.stop()


-------------------- Display --------------------


left, right = st.columns([2,1])
with left:
st.subheader("ASCII Output")
if colored and color_html is not None:
st.markdown(color_html, unsafe_allow_html=True)
else:
# show in code block with monospace so copy preserves spacing
st.code(ascii_art, language='text')


st.download_button("Download ASCII as .txt", data=ascii_art, file_name="ascii_plot.txt", mime="text/plain")
st.markdown("**Copy / Edit**")
st.text_area("ASCII (editable):", value=ascii_art, height=300)



with right:
st.subheader("Controls Summary")
st.markdown(f"Type: {plot_type}")
st.markdown(f"Width x Height: {width} x {height}")
st.markdown(f"Charset: {char_preset}")
st.markdown(f"Colored: {colored}")


optional Matplotlib for comparison


if show_mpl:
st.subheader("Visual comparison (Matplotlib)")
fig, ax = plt.subplots(figsize=(6,3))
try:
if plot_type == 'Line':
ax.plot(numeric[x_col], numeric[y_col], marker='o' if len(numeric)>50 else '')
elif plot_type == 'Scatter':
ax.scatter(numeric[x_col], numeric[y_col])
elif plot_type == 'Bar':
if cat_col:
grouped = df.groupby(cat_col)[val_col].sum()
grouped.plot(kind='bar', ax=ax)
else:
ax.bar(range(len(numeric[val_col])), numeric[val_col])
elif plot_type == 'Histogram':
ax.hist(numeric[hist_col].dropna(), bins=30)
elif plot_type == 'Heatmap':
import seaborn as sns
mat = numeric[heat_cols].values if heat_cols else numeric.values
if mat.ndim == 1:
mat = mat.reshape(-1,1)
sns.heatmap(mat, ax=ax)
elif plot_type == 'Sparkline':
ax.plot(numeric[spark_col])
st.pyplot(fig)
except Exception as e:
st.write('Could not create Matplotlib preview:', e)


st.caption('Tip: use a monospace font when pasting the ASCII into other apps. For colored output, the app renders HTML spans.\nEnjoy!')


