import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from textwrap import dedent
import html

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
    mn = np.nanmin(a)
    mx = np.nanmax(a)
    if mx == mn:
        return np.full_like(a, (new_min + new_max) / 2.0)
    return (a - mn) / (mx - mn) * (new_max - new_min) + new_min

def render_ascii_grid(grid_lines, monospace=True, colored_html=None):
    """
    grid_lines: list[str] lines (already escaped)
    colored_html: optional string containing HTML preformatted content (if present, used instead)
    """
    if colored_html is not None:
        # show HTML with monospace
        st.markdown(colored_html, unsafe_allow_html=True)
        return
    content = "\n".join(grid_lines)
    st.code(content, language=None)  # uses monospace; good for copying

def map_value_to_char(val_norm, charset):
    """
    val_norm : 0..1
    charset : string of characters from low-intensity to high-intensity
    """
    idx = int(round(val_norm * (len(charset) - 1)))
    idx = max(0, min(idx, len(charset) - 1))
    return charset[idx]

def generate_empty_grid(width, height, fill=" "):
    return [[fill for _ in range(width)] for _ in range(height)]

def grid_to_text_lines(grid):
    return ["".join(row) for row in grid]

def ascii_line_plot(x, y, width, height, charset, colored=False, cmap=None, show_axes=True):
    """
    Basic line plot mapping points onto a discrete character grid.
    - x, y: 1D arrays (same length)
    - width, height: characters
    - charset: characters ordered from low to high intensity
    - colored: if True, returns an HTML string with colored spans
    - cmap: matplotlib colormap name for coloring intensity
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.size == 0 or y.size == 0:
        return ["(no data)"]
    # remove NaNs
    mask = ~np.isnan(x) & ~np.isnan(y)
    if not mask.any():
        return ["(no valid numeric data)"]
    x = x[mask]
    y = y[mask]

    # Normalize x and y to grid coords
    xn = normalize(x, 0, width - 1)
    yn = normalize(y, 0, height - 1)
    # In grid, row 0 is top, so invert y
    yn = (height - 1) - yn

    grid = generate_empty_grid(width, height, fill=" ")
    # draw points as highest-intensity char of charset
    for xi, yi, val in zip(xn, yn, y):
        cx = int(round(xi))
        cy = int(round(yi))
        # mark with high-intensity char (last char)
        ch = charset[-1]
        grid[cy][cx] = ch

    # Optionally add a simple line connection by interpolating between consecutive points
    for i in range(1, len(xn)):
        x0, y0 = int(round(xn[i-1])), int(round(yn[i-1]))
        x1, y1 = int(round(xn[i])), int(round(yn[i]))
        # Bresenham-like interpolation
        dx = x1 - x0
        dy = y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        for s in range(steps + 1):
            tx = int(round(x0 + dx * (s / steps)))
            ty = int(round(y0 + dy * (s / steps)))
            # use a char scaled by the y-value at this interpolation (approx)
            grid[ty][tx] = charset[-1]

    # axes (simple)
    if show_axes:
        yaxis_col = 0
        xaxis_row = height - 1
        for r in range(height):
            if grid[r][yaxis_col] == " ":
                grid[r][yaxis_col] = "|"
        for c in range(width):
            if grid[xaxis_row][c] == " ":
                grid[xaxis_row][c] = "-"

        grid[xaxis_row][yaxis_col] = "+"

    # If colored requested, build HTML with colored spans based on y intensity
    if colored:
        return grid_to_colored_html(grid, charset, cmap=cmap)
    else:
        return grid_to_text_lines(grid)

def ascii_scatter_plot(x, y, width, height, charset, colored=False, cmap=None, show_axes=True, marker="o"):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.size == 0 or y.size == 0:
        return ["(no data)"]
    mask = ~np.isnan(x) & ~np.isnan(y)
    if not mask.any():
        return ["(no valid numeric data)"]
    x = x[mask]
    y = y[mask]

    xn = normalize(x, 0, width - 1)
    yn = normalize(y, 0, height - 1)
    yn = (height - 1) - yn

    grid = generate_empty_grid(width, height, fill=" ")

    for xi, yi, val in zip(xn, yn, y):
        cx = int(round(xi))
        cy = int(round(yi))
        grid[cy][cx] = marker

    if show_axes:
        yaxis_col = 0
        xaxis_row = height - 1
        for r in range(height):
            if grid[r][yaxis_col] == " ":
                grid[r][yaxis_col] = "|"
        for c in range(width):
            if grid[xaxis_row][c] == " ":
                grid[xaxis_row][c] = "-"

        grid[xaxis_row][yaxis_col] = "+"

    if colored:
        return grid_to_colored_html(grid, charset, cmap=cmap)
    else:
        return grid_to_text_lines(grid)

def ascii_bar_plot(x, y, width, height, charset, horizontal=False, colored=False, cmap=None):
    """
    For bar plot: x labels on axis, y numeric heights
    If horizontal True: bars extend to the right
    """
    x = np.asarray(x)
    y = np.asarray(y, dtype=float)
    if y.size == 0:
        return ["(no data)"]
    # For vertical bar chart mapping to a grid:
    grid = generate_empty_grid(width, height, fill=" ")
    # decide number of bars: limit to width if vertical bars (one char per bar)
    if horizontal:
        # create rows = len(y) clipped by height
        n = min(len(y), height - 2)  # keep room for axes
        vals = y[:n]
        maxv = np.nanmax(vals) if not np.all(np.isnan(vals)) else 1.0
        for i, v in enumerate(vals):
            normalized = 0 if maxv == 0 else v / maxv
            length = int(round(normalized * (width - 10)))
            length = max(0, min(length, width-1))
            row = i
            # draw bar from col 0 to length
            for c in range(length):
                grid[row][c] = charset[-1]
            # label at far right if space
            lbl = str(x[i])
            for j,ch in enumerate(lbl):
                if j < width:
                    grid[row][min(width-1, j+length)] = ch
    else:
        # vertical bars: each bar occupies a column; place them across width, skipping spacing
        n = min(len(y), width - 6)  # leave room for axis
        vals = y[:n]
        vals_norm = normalize(vals, 0, height - 2)  # exclude bottom row for axis
        for i, vn in enumerate(vals_norm):
            col = i + 3  # leave left margin
            bar_height = int(round(vn * (height - 3)))
            for r in range(height - 2, height - 2 - bar_height, -1):
                if 0 <= r < height:
                    grid[r][col] = charset[-1]
        # draw x-axis
        for c in range(width):
            grid[height - 1][c] = "-"
        # left y-axis
        for r in range(height):
            grid[r][2] = "|"
        grid[height - 1][2] = "+"
    if colored:
        return grid_to_colored_html(grid, charset, cmap=cmap)
    else:
        return grid_to_text_lines(grid)

def ascii_histogram(values, width, height, charset, bins=20, colored=False, cmap=None):
    vals = np.asarray(values, dtype=float)
    vals = vals[~np.isnan(vals)]
    if vals.size == 0:
        return ["(no numeric data)"]
    hist, edges = np.histogram(vals, bins=bins)
    # reuse vertical bar plot logic
    return ascii_bar_plot(np.arange(len(hist)), hist, width=width, height=height, charset=charset, horizontal=False, colored=colored, cmap=cmap)

def ascii_heatmap(matrix, width, height, charset, colored=False, cmap=None):
    """
    matrix: 2D array-like
    Map matrix to the provided width/height by resampling
    """
    a = np.asarray(matrix, dtype=float)
    if a.size == 0:
        return ["(no data)"]
    # handle if 1D: treat as single row
    if a.ndim == 1:
        a = a[np.newaxis, :]
    # resize: use simple block-averaging
    src_h, src_w = a.shape
    if src_h == 0 or src_w == 0:
        return ["(no data)"]
    # create target resampled array
    target = np.zeros((height, width))
    # calculate source coordinates for each target cell
    for i in range(height):
        for j in range(width):
            # mapping
            src_y0 = int(i * src_h / height)
            src_y1 = int((i + 1) * src_h / height)
            src_x0 = int(j * src_w / width)
            src_x1 = int((j + 1) * src_w / width)
            src_y1 = max(src_y1, src_y0 + 1)
            src_x1 = max(src_x1, src_x0 + 1)
            block = a[src_y0:src_y1, src_x0:src_x1]
            # average ignoring NaNs
            if np.isnan(block).all():
                target[i, j] = 0.0
            else:
                target[i, j] = np.nanmean(block)
    # normalize target
    tnorm = normalize(target, 0, 1)
    grid = generate_empty_grid(width, height, fill=" ")
    for i in range(height):
        for j in range(width):
            grid[i][j] = map_value_to_char(tnorm[i, j], charset)
    if colored:
        return grid_to_colored_html(grid, charset, cmap=cmap, matrix_values=tnorm)
    else:
        return grid_to_text_lines(grid)

def ascii_sparkline(values, charset, length=30):
    vals = np.asarray(values, dtype=float)
    vals = vals[~np.isnan(vals)]
    if vals.size == 0:
        return "(no data)"
    n = min(length, len(vals))
    # resample to n points
    idx = np.linspace(0, len(vals)-1, n).astype(int)
    sampled = vals[idx]
    normed = normalize(sampled, 0, len(charset)-1).astype(int)
    return "".join(charset[i] for i in normed)

# Coloring helper: produce HTML with inline color for each char based on intensity (0..1)
def grid_to_colored_html(grid, charset, cmap=None, matrix_values=None):
    """
    grid: 2D list of characters
    matrix_values: optional 2D numpy array of same shape with normalized 0..1 intensity
    cmap: matplotlib colormap name
    """
    height = len(grid)
    width = len(grid[0]) if height>0 else 0
    # Use matplotlib colormap to map values to colors
    import matplotlib
    if cmap is None:
        cmap = "viridis"
    cm = matplotlib.cm.get_cmap(cmap)
    # Build HTML with <pre> and <span style="color: #RRGGBB">char</span>
    rows_html = []
    for i in range(height):
        row_chars = []
        for j in range(width):
            ch = grid[i][j]
            # determine intensity: if matrix_values provided, use it, else derive from charset position
            if matrix_values is not None:
                val = float(matrix_values[i, j])
            else:
                # map based on position in charset
                if ch in charset:
                    val = charset.find(ch) / max(1, len(charset)-1)
                else:
                    # fallback for axes etc.
                    val = 0.0
            rgba = cm(val)
            # convert to hex
            r,g,b,a = rgba
            hexcol = '#%02x%02x%02x' % (int(r*255), int(g*255), int(b*255))
            esc = html.escape(ch)
            # preserve spaces visually with &nbsp;
            if esc == " ":
                esc = "&nbsp;"
            span = f'<span style="color:{hexcol};">{esc}</span>'
            row_chars.append(span)
        rows_html.append("".join(row_chars))
    pre = "<pre style='font-family: monospace; line-height: 90%; font-size: 12px; white-space: pre;'>\n" + "\n".join(rows_html) + "\n</pre>"
    return pre

# -------------------------
# UI
# -------------------------

st.title("ASCII Plotter — Streamlit")
st.write("Create ASCII/Unicode art plots from CSV/JSON or sample data. Copy or download the ASCII output.")

# Sidebar controls
with st.sidebar:
    st.header("Controls")
    uploaded = st.file_uploader("Upload dataset (CSV or JSON)", type=["csv","json"], accept_multiple_files=False)
    sample_data = st.selectbox("Or choose sample dataset", ["-- none --", "Sine wave", "Iris (sepal_length vs petal_length)", "Random scatter", "2D heatmap sample"])
    plot_type = st.selectbox("Plot type", ["Line", "Scatter", "Bar", "Histogram", "Heatmap", "Sparkline"])
    st.markdown("---")
    charset_choice = st.selectbox("Character set", list(DEFAULT_CHARSETS.keys()))
    custom_charset = st.text_input("Or custom characters (from low -> high intensity)", value=DEFAULT_CHARSETS[charset_choice])
    st.markdown("**Appearance**")
    width = st.slider("Width (characters)", min_value=40, max_value=200, value=100)
    height = st.slider("Height (characters)", min_value=8, max_value=60, value=20)
    colored = st.checkbox("Colored ASCII (HTML)", value=False)
    cmap = st.selectbox("Color map (if colored)", ["viridis","plasma","inferno","magma","cividis"], index=0)
    show_axes = st.checkbox("Show axes (line/scatter/bar)", value=True)
    marker_char = st.text_input("Scatter marker (single char)", value="o", max_chars=1)
    st.markdown("---")
    show_real = st.checkbox("Show real chart (Matplotlib) alongside", value=True)
    st.markdown("## Export")
    download_filename = st.text_input("Download filename", value="ascii_plot.txt")
    st.markdown("")

# compile charset to use
if custom_charset.strip() == "":
    charset = DEFAULT_CHARSETS["Shades (.:-=+*#%@)"]
else:
    charset = custom_charset

# Load data
df = None
matrix_for_heatmap = None

if uploaded is not None:
    try:
        if uploaded.type == "application/json" or uploaded.name.lower().endswith(".json"):
            df = pd.read_json(uploaded)
        else:
            df = pd.read_csv(uploaded)
    except Exception as e:
        st.sidebar.error(f"Failed to read file: {e}")
else:
    # handle sample data
    if sample_data == "Sine wave":
        x = np.linspace(0, 4*np.pi, 300)
        y = np.sin(x)
        df = pd.DataFrame({"x": x, "y": y})
    elif sample_data == "Iris (sepal_length vs petal_length)":
        from sklearn import datasets
        iris = datasets.load_iris()
        df = pd.DataFrame(iris.data, columns=iris.feature_names)
        # pick two columns
        df = df.rename(columns={df.columns[0]: "sepal_length", df.columns[2]: "petal_length"})
    elif sample_data == "Random scatter":
        n = 500
        x = np.random.randn(n).cumsum()
        y = np.random.randn(n).cumsum()
        df = pd.DataFrame({"x": x, "y": y})
    elif sample_data == "2D heatmap sample":
        # create a 2D gaussian-ish sample
        xx, yy = np.meshgrid(np.linspace(-2,2,120), np.linspace(-1.5,1.5,60))
        z = np.exp(-(xx**2 + (yy*2)**2))
        matrix_for_heatmap = z
        df = None
    else:
        df = None

# Show dataset preview and column selectors
st.sidebar.markdown("### Data preview")
if df is not None:
    st.sidebar.dataframe(df.head(10), height=200)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    all_cols = df.columns.tolist()
    if plot_type in ("Line","Scatter"):
        xcol = st.sidebar.selectbox("X column", options=all_cols, index=0 if len(all_cols)>0 else None)
        ycol = st.sidebar.selectbox("Y column", options=numeric_cols, index=1 if len(numeric_cols)>1 else 0)
    elif plot_type in ("Bar",):
        xcol = st.sidebar.selectbox("Category column (x)", options=all_cols)
        ycol = st.sidebar.selectbox("Value column (y)", options=numeric_cols)
    elif plot_type in ("Histogram", "Sparkline"):
        valcol = st.sidebar.selectbox("Value column", options=numeric_cols)
    elif plot_type == "Heatmap":
        # For heatmap, user can either upload an image or provide matrix in CSV form
        st.sidebar.markdown("For heatmap: upload a CSV where each row is a row in the matrix, or choose sample.")
        heat_uploaded = st.sidebar.file_uploader("Upload matrix CSV for heatmap (optional)", type=["csv"], key="heatup")
        if heat_uploaded is not None:
            try:
                mdf = pd.read_csv(heat_uploaded, header=None)
                matrix_for_heatmap = mdf.values
            except Exception as e:
                st.sidebar.error(f"Failed to read heatmap matrix: {e}")
else:
    st.sidebar.write("No tabular dataset selected. Choose a sample dataset or upload a file.")

# -------------------------
# Build ASCII output
# -------------------------
ascii_output_lines = ["(no output)"]
ascii_output_html = None
show_error = None

def generate_ascii_for_selected():
    global ascii_output_lines, ascii_output_html, show_error
    ascii_output_lines = ["(no output)"]
    ascii_output_html = None
    show_error = None

    cs = charset
    try:
        if plot_type == "Heatmap":
            if matrix_for_heatmap is None:
                show_error = "No matrix provided for heatmap. Upload matrix CSV or choose sample."
                return
            mat = matrix_for_heatmap
            if colored:
                ascii_output_html = ascii_heatmap(mat, width, height, cs, colored=True, cmap=cmap)
            else:
                ascii_output_lines[:] = ascii_heatmap(mat, width, height, cs, colored=False)
            return

        if df is None:
            show_error = "No dataframe to plot. Upload a CSV/JSON or choose a sample dataset."
            return

        if plot_type == "Line":
            x = df[xcol].values
            y = df[ycol].values
            out = ascii_line_plot(x, y, width, height, cs, colored=colored, cmap=cmap, show_axes=show_axes)
            if colored and isinstance(out, str):
                ascii_output_html = out
            else:
                ascii_output_lines[:] = out

        elif plot_type == "Scatter":
            x = df[xcol].values
            y = df[ycol].values
            out = ascii_scatter_plot(x, y, width, height, cs, colored=colored, cmap=cmap, show_axes=show_axes, marker=marker_char or "o")
            if colored and isinstance(out, str):
                ascii_output_html = out
            else:
                ascii_output_lines[:] = out

        elif plot_type == "Bar":
            x = df[xcol].astype(str).values
            y = pd.to_numeric(df[ycol], errors="coerce").fillna(0).values
            out = ascii_bar_plot(x, y, width, height, cs, horizontal=False, colored=colored, cmap=cmap)
            if colored and isinstance(out, str):
                ascii_output_html = out
            else:
                ascii_output_lines[:] = out

        elif plot_type == "Histogram":
            vals = pd.to_numeric(df[valcol], errors="coerce").values
            out = ascii_histogram(vals, width, height, cs, bins= min(60, max(5, width//2)), colored=colored, cmap=cmap)
            if colored and isinstance(out, str):
                ascii_output_html = out
            else:
                ascii_output_lines[:] = out

        elif plot_type == "Sparkline":
            vals = pd.to_numeric(df[valcol], errors="coerce").values
            spark = ascii_sparkline(vals, cs, length=width)
            ascii_output_lines[:] = [spark]

        else:
            show_error = f"Plot type {plot_type} not implemented."
    except Exception as e:
        show_error = f"Error generating ASCII: {e}"

generate_ascii_for_selected()

# -------------------------
# Main layout: two columns: left ascii, right optional real chart + controls
# -------------------------
left_col, right_col = st.columns([1.0, 1.0] if show_real else [1.0, 0.0])

with left_col:
    st.subheader("ASCII Output")
    if show_error:
        st.error(show_error)
    else:
        if ascii_output_html is not None:
            # render the HTML pre block (already contains <pre>)
            st.markdown(ascii_output_html, unsafe_allow_html=True)
            ascii_text = strip_html_to_text(ascii_output_html := ascii_output_html) if False else None
        else:
            # present as code block, make sure monospace and allow easy copy
            # We provide both a copy button and a download button below
            rendered = "\n".join(ascii_output_lines)
            st.code(rendered, language=None)

    # Export buttons
    if ascii_output_html is not None:
        # convert HTML-based colored ascii back into plain text for download (strip tags)
        # Simple approach: remove tags and replace &nbsp; with spaces
        import re
        plain = re.sub(r'<.*?>', '', ascii_output_html)
        plain = plain.replace("&nbsp;", " ")
        ascii_text_for_download = plain
    else:
        ascii_text_for_download = "\n".join(ascii_output_lines)

    # Download
    st.download_button(label="Download ASCII as .txt", data=ascii_text_for_download.encode("utf-8"),
                       file_name=download_filename or "ascii_plot.txt", mime="text/plain")

    # Copy to clipboard via tiny JS injected in components
    copy_button_html = dedent(f"""
    <button onclick="copyToClipboard()" style="padding:6px 10px; font-size:14px">Copy ASCII to clipboard</button>
    <script>
    function copyToClipboard(){{
        const text = {json_safe(ascii_text_for_download)};
        navigator.clipboard.writeText(text).then(function() {{
            document.querySelector('button').innerText = 'Copied!';
            setTimeout(()=>{{document.querySelector('button').innerText = 'Copy ASCII to clipboard'}}, 1200);
        }}, function(err) {{
            alert('Could not copy: ' + err);
        }});
    }}
    </script>
    """)
    # We will display the copy button
    st.components.v1.html(copy_button_html, height=40)

with right_col:
    if show_real:
        st.subheader("Real Chart (preview)")
        try:
            fig, ax = plt.subplots(figsize=(6, 3))
            if plot_type == "Line":
                ax.plot(df[xcol], df[ycol], linewidth=1)
                ax.set_xlabel(xcol)
                ax.set_ylabel(ycol)
            elif plot_type == "Scatter":
                ax.scatter(df[xcol], df[ycol], s=6)
                ax.set_xlabel(xcol)
                ax.set_ylabel(ycol)
            elif plot_type == "Bar":
                ax.bar(df[xcol].astype(str), pd.to_numeric(df[ycol], errors="coerce").fillna(0).values)
                ax.set_xlabel(xcol)
                ax.set_ylabel(ycol)
                plt.xticks(rotation=45, ha='right', fontsize=8)
            elif plot_type == "Histogram":
                ax.hist(pd.to_numeric(df[valcol], errors="coerce").dropna(), bins=30)
            elif plot_type == "Heatmap" and matrix_for_heatmap is not None:
                ax.imshow(matrix_for_heatmap, aspect='auto', origin='lower')
            elif plot_type == "Sparkline":
                ax.plot(pd.to_numeric(df[valcol], errors="coerce").fillna(0).values, linewidth=1)
            else:
                ax.text(0.5, 0.5, "No preview available", ha='center', va='center')
            st.pyplot(fig)
        except Exception as e:
            st.write(f"Could not render real chart preview: {e}")

# -------------------------
# Utility helpers defined after use (to keep flow readable)
# -------------------------
def json_safe(s: str):
    """
    Return a JS string literal representation safe for embedding.
    """
    if s is None:
        return "''"
    # Escape backslashes and single quotes & newlines
    esc = s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "")
    return f"'{esc}'"

def strip_html_to_text(html_str):
    # primitive HTML stripper for our generated HTML
    import re
    text = re.sub(r'<[^>]+>', '', html_str)
    text = text.replace("&nbsp;", " ")
    return text

# Add a final help / tips panel
st.markdown("---")
st.markdown("""
**Tips**
- Use a monospace font view to preserve alignment. The app renders ASCII in a `<pre>` block for exact spacing.
- For colored output, `Colored ASCII` uses inline HTML coloring (works in the browser) — when you download as `.txt` you'll get plain text without colors.
- To embed ASCII in READMEs, copy the text into a markdown code block using triple backticks (```) — monospace is preserved.
- Adjust width/height to get the best balance between resolution and readability.
""")
