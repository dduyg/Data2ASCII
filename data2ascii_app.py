import streamlit as st
import pandas as pd
import numpy as np
from io import StringIO

st.set_page_config(page_title="Data2ASCII ＜（＾－＾）＞", page_icon="🌸", layout="wide")

# Vaporwave CSS styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Sans:wght@300;400;700&display=swap');
    
    /* Main app styling */
    .stApp {
        background: linear-gradient(135deg, #392c39 0%, #2d1f3d 50%, #392c39 100%);
        color: #cfd4c5;
        font-family: 'Fira Sans', sans-serif;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #4a3a52 0%, #392c39 100%);
        border-right: 2px solid #ff71ce;
    }
    
    [data-testid="stSidebar"] * {
        color: #cfd4c5 !important;
    }
    
    /* Headers with vaporwave glow */
    h1, h2, h3 {
        color: #ff71ce;
        text-shadow: 0 0 10px #ff71ce, 0 0 20px #ff71ce, 0 0 30px #01cdfe;
        font-weight: 700;
        letter-spacing: 2px;
    }
    
    h1 {
        font-size: 3rem !important;
        text-align: center;
        margin-bottom: 0 !important;
    }
    
    /* Glowing dividers */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, #ff71ce, #01cdfe, #b967ff, #ff71ce);
        box-shadow: 0 0 10px #01cdfe;
        margin: 2rem 0;
    }
    
    /* Buttons with vaporwave style */
    .stButton > button {
        background: linear-gradient(135deg, #ff71ce 0%, #b967ff 100%);
        color: #0f0326;
        border: 2px solid #01cdfe;
        border-radius: 20px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 0.75rem 2rem;
        box-shadow: 0 0 20px rgba(1, 205, 254, 0.5);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #01cdfe 0%, #b967ff 100%);
        box-shadow: 0 0 30px rgba(255, 113, 206, 0.8);
        transform: scale(1.05);
    }
    
    /* Download buttons */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #01cdfe 0%, #05ffa1 100%);
        color: #0f0326;
        border: 2px solid #ff71ce;
        border-radius: 15px;
        font-weight: 700;
        padding: 0.6rem 1.5rem;
        box-shadow: 0 0 15px rgba(5, 255, 161, 0.5);
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #05ffa1 0%, #01cdfe 100%);
        box-shadow: 0 0 25px rgba(1, 205, 254, 0.8);
    }
    
    /* Input elements */
    .stSelectbox, .stSlider, .stRadio {
        color: #cfd4c5;
    }
    
    .stSelectbox > div > div {
        background-color: #2d1f3d;
        border: 2px solid #b967ff;
        border-radius: 10px;
        color: #cfd4c5;
    }
    
    /* Code blocks (ASCII output) */
    .stCodeBlock {
        background: #1a0f1f !important;
        border: 2px solid #ff71ce;
        border-radius: 15px;
        box-shadow: 0 0 30px rgba(255, 113, 206, 0.3), inset 0 0 20px rgba(1, 205, 254, 0.1);
    }
    
    code {
        color: #05ffa1 !important;
        font-family: 'Courier New', monospace;
    }
    
    /* Info boxes */
    .stAlert {
        background: rgba(1, 205, 254, 0.1);
        border: 2px solid #01cdfe;
        border-radius: 10px;
        color: #cfd4c5;
    }
    
    /* Success messages */
    .stSuccess {
        background: rgba(5, 255, 161, 0.1);
        border: 2px solid #05ffa1;
        color: #05ffa1;
    }
    
    /* Dataframe styling */
    .stDataFrame {
        border: 2px solid #b967ff;
        border-radius: 10px;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(185, 103, 255, 0.2);
        border-radius: 10px;
        color: #ff71ce !important;
        font-weight: 700;
    }
    
    /* Radio buttons */
    .stRadio > label {
        color: #ff71ce !important;
        font-weight: 700;
    }
    
    /* Slider */
    .stSlider > div > div > div {
        background: linear-gradient(90deg, #ff71ce, #01cdfe);
    }
    
    /* Text styling */
    p, li, label {
        color: #cfd4c5;
        font-size: 1rem;
    }
    
    /* Markdown styling */
    .stMarkdown {
        color: #cfd4c5;
    }
    
    /* Grid effect overlay */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            linear-gradient(rgba(1, 205, 254, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(1, 205, 254, 0.03) 1px, transparent 1px);
        background-size: 50px 50px;
        pointer-events: none;
        z-index: 0;
    }
    
    /* Neon border effect */
    .main > div {
        border: 1px solid rgba(255, 113, 206, 0.3);
        border-radius: 20px;
        padding: 2rem;
        backdrop-filter: blur(10px);
    }
    
    /* Custom container styling */
    .element-container {
        z-index: 1;
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        border: 2px dashed #ff71ce;
        border-radius: 15px;
        padding: 1rem;
        background: rgba(255, 113, 206, 0.05);
        position: relative;
        z-index: 100;
    }
    
    [data-testid="stFileUploader"] section {
        pointer-events: auto;
    }
    
    [data-testid="stFileUploader"] button {
        pointer-events: auto;
        cursor: pointer;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #ff71ce !important;
        border-right-color: #01cdfe !important;
        border-bottom-color: #b967ff !important;
        border-left-color: #05ffa1 !important;
    }
    </style>
""", unsafe_allow_html=True)

def create_scatter_ascii(x_data, y_data, width=100, height=30):
    """Create ASCII scatter plot"""
    return create_simple_ascii_chart(x_data, y_data, width, height, 'scatter')

def create_line_ascii(x_data, y_data, width=100, height=30):
    """Create ASCII line plot"""
    return create_simple_ascii_chart(x_data, y_data, width, height, 'line')

def create_bar_ascii(x_data, y_data, width=100, height=30):
    """Create ASCII bar chart"""
    return create_simple_ascii_chart(x_data, y_data, width, height, 'bar')

def create_histogram_ascii(data, bins=20, width=100, height=30):
    """Create ASCII histogram"""
    hist, bin_edges = np.histogram(data, bins=bins)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    return create_simple_ascii_chart(bin_centers, hist, width, height, 'bar')

def create_simple_ascii_chart(x_data, y_data, width=80, height=20, chart_type='line'):
    """Create simple ASCII chart using basic characters"""
    x_norm = np.array(x_data)
    y_norm = np.array(y_data)
    
    y_min, y_max = y_norm.min(), y_norm.max()
    if y_max == y_min:
        y_max = y_min + 1
    
    y_scaled = ((y_norm - y_min) / (y_max - y_min) * (height - 1)).astype(int)
    
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    step = max(1, len(x_data) // width)
    for i in range(0, len(x_data), step):
        x_pos = min(int((i / len(x_data)) * (width - 1)), width - 1)
        y_pos = height - 1 - y_scaled[i]
        
        if chart_type == 'scatter':
            grid[y_pos][x_pos] = '●'
        elif chart_type == 'line':
            grid[y_pos][x_pos] = '█'
            # Connect points for line chart
            if i > 0:
                prev_i = max(0, i - step)
                prev_x = min(int((prev_i / len(x_data)) * (width - 1)), width - 1)
                prev_y = height - 1 - y_scaled[prev_i]
                # Draw line between points
                if prev_x != x_pos:
                    for x in range(min(prev_x, x_pos), max(prev_x, x_pos) + 1):
                        if prev_y != y_pos:
                            y = prev_y + int((y_pos - prev_y) * (x - prev_x) / (x_pos - prev_x))
                        else:
                            y = prev_y
                        if 0 <= y < height and 0 <= x < width:
                            grid[y][x] = '█'
        elif chart_type == 'bar':
            for j in range(y_pos, height):
                grid[j][x_pos] = '█'
    
    result = []
    result.append('┌' + '─' * width + '┐')
    for row in grid:
        result.append('│' + ''.join(row) + '│')
    result.append('└' + '─' * width + '┘')
    
    # Add axis labels
    result.append(f"\nMin: {y_min:.2f}  Max: {y_max:.2f}")
    
    return '\n'.join(result)

# Title with vaporwave aesthetic
st.markdown("""
    <h1 style='text-align: center; margin-bottom: 0;'>
        ✧･ﾟ: *✧･ﾟ:* DATA2ASCII *:･ﾟ✧*:･ﾟ✧
    </h1>
    <p style='text-align: center; color: #01cdfe; font-size: 1.2rem; margin-top: 0; letter-spacing: 3px;'>
        ～ A E S T H E T I C  D A T A  V I S U A L I Z A T I O N ～
    </p>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main content area - File upload
st.markdown("### 📁 U P L O A D  D A T A S E T")
st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    uploaded_file = st.file_uploader(
        "Drop your file here or click to browse", 
        type=['csv', 'xlsx', 'txt'],
        help="Upload a CSV, Excel, or TXT file",
        label_visibility="collapsed"
    )

st.markdown("<br>", unsafe_allow_html=True)

# Sidebar with settings only
with st.sidebar:
    st.markdown("### ⚙️ C O N F I G")
    st.markdown("---")
    
    st.markdown("### 🎨 D I S P L A Y")
    plot_width = st.slider("Width", 60, 150, 100)
    plot_height = st.slider("Height", 15, 50, 25)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
        <div style='text-align: center; padding: 1rem; background: rgba(255, 113, 206, 0.1); border-radius: 10px; border: 1px solid #ff71ce;'>
            <p style='margin: 0; font-size: 0.9rem; color: #01cdfe;'>✧ V A P O R W A V E ✧</p>
            <p style='margin: 0; font-size: 0.8rem;'>A S C I I  A R T</p>
        </div>
    """, unsafe_allow_html=True)

# Main content
if uploaded_file is not None:
    try:
        # Load data
        if uploaded_file.name.endswith('.csv') or uploaded_file.name.endswith('.txt'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"✨ L O A D E D  {len(df)} rows × {len(df.columns)} columns ✨")
        
        # Data preview
        with st.expander("📋 D A T A  P R E V I E W", expanded=False):
            st.dataframe(df.head(20), use_container_width=True)
        
        st.markdown("---")
        
        # Variable selection
        st.markdown("### 🎯 S E L E C T  V A R I A B L E S")
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        all_cols = df.columns.tolist()
        
        with col1:
            x_var = st.selectbox(
                "X-axis Variable ➤",
                options=all_cols,
                help="Select the variable for X-axis"
            )
        
        with col2:
            y_var = st.selectbox(
                "Y-axis Variable ➤",
                options=numeric_cols,
                help="Select the numeric variable for Y-axis"
            )
        
        st.markdown("---")
        
        # Chart type selection
        st.markdown("### 📈 V I S U A L I Z A T I O N  T Y P E")
        st.markdown("<br>", unsafe_allow_html=True)
        
        chart_type = st.radio(
            "Choose your aesthetic:",
            ["✧ Line Chart", "✧ Scatter Plot", "✧ Bar Chart", "✧ Histogram (Y-axis only)"],
            horizontal=True
        )
        
        st.markdown("---")
        
        # Generate button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            generate_btn = st.button("✧ G E N E R A T E  A S C I I ✧", type="primary", use_container_width=True)
        
        if generate_btn:
            with st.spinner("✨ Creating vaporwave ASCII art... ✨"):
                try:
                    ascii_output = ""
                    chart_name = chart_type.replace("✧ ", "")
                    
                    if "Histogram" in chart_name:
                        ascii_output = create_histogram_ascii(
                            df[y_var].dropna(),
                            bins=20,
                            width=plot_width,
                            height=plot_height
                        )
                    elif "Bar Chart" in chart_name:
                        if len(df) > 50:
                            st.warning("⚠ Dataset too large for bar chart. Using first 50 rows.")
                            data_subset = df.head(50)
                        else:
                            data_subset = df
                        
                        x_data = pd.to_numeric(range(len(data_subset)), errors='coerce')
                        y_data = data_subset[y_var].values
                        ascii_output = create_bar_ascii(
                            x_data,
                            y_data,
                            width=plot_width,
                            height=plot_height
                        )
                    else:
                        x_data = pd.to_numeric(df[x_var], errors='coerce').dropna()
                        y_data = df[y_var].loc[x_data.index]
                        
                        if "Line Chart" in chart_name:
                            ascii_output = create_line_ascii(
                                x_data.values,
                                y_data.values,
                                width=plot_width,
                                height=plot_height
                            )
                        else:  # Scatter Plot
                            ascii_output = create_scatter_ascii(
                                x_data.values,
                                y_data.values,
                                width=plot_width,
                                height=plot_height
                            )
                    
                    st.session_state.ascii_plot = ascii_output
                    st.session_state.chart_info = f"{chart_name}: {x_var} vs {y_var}"
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    try:
                        st.info("✧ Trying alternative ASCII rendering... ✧")
                        x_data = pd.to_numeric(df[x_var], errors='coerce').dropna()
                        y_data = df[y_var].loc[x_data.index]
                        chart_map = {
                            "✧ Line Chart": "line",
                            "✧ Scatter Plot": "scatter",
                            "✧ Bar Chart": "bar"
                        }
                        ascii_output = create_simple_ascii_chart(
                            x_data.values,
                            y_data.values,
                            width=plot_width,
                            height=plot_height,
                            chart_type=chart_map.get(chart_type, 'line')
                        )
                        st.session_state.ascii_plot = ascii_output
                        st.session_state.chart_info = f"{chart_type.replace('✧ ', '')}: {x_var} vs {y_var}"
                    except Exception as e2:
                        st.error(f"❌ Could not generate chart: {str(e2)}")
        
        # Display ASCII plot
        if 'ascii_plot' in st.session_state:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### ✨ A S C I I  V I S U A L I Z A T I O N ✨")
            st.markdown(f"<p style='text-align: center; color: #01cdfe; font-size: 1.1rem;'>{st.session_state.chart_info}</p>", unsafe_allow_html=True)
            
            st.code(st.session_state.ascii_plot, language=None)
            
            st.markdown("---")
            st.markdown("### 💾 E X P O R T  O P T I O N S")
            st.markdown("<br>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="📋 Download as TXT",
                    data=st.session_state.ascii_plot,
                    file_name=f"ascii_vaporwave_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col2:
                metadata = f"# {st.session_state.chart_info}\n# Generated: {pd.Timestamp.now()}\n# Dimensions: {plot_width}x{plot_height}\n# ✧･ﾟ: *✧･ﾟ:* VAPORWAVE ASCII *:･ﾟ✧*:･ﾟ✧\n\n"
                full_output = metadata + st.session_state.ascii_plot
                
                st.download_button(
                    label="📄 Download with Metadata",
                    data=full_output,
                    file_name=f"ascii_vaporwave_full_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
    
    except Exception as e:
        st.error(f"❌ Error loading file: {str(e)}")
        st.info("Please make sure your file is properly formatted (CSV or Excel)")

else:
    # Welcome screen with vaporwave aesthetic
    st.markdown("""
        <div style='text-align: center; padding: 3rem 2rem; background: rgba(1, 205, 254, 0.05); border-radius: 20px; border: 2px solid #ff71ce; margin: 2rem 0;'>
            <h2 style='margin: 0;'>✧ W E L C O M E ✧</h2>
            <p style='font-size: 1.2rem; color: #01cdfe; margin-top: 1rem;'>Upload a dataset to begin your journey</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🎯 H O W  T O  U S E
        
        **1.** Upload your dataset (CSV/Excel)
        
        **2.** Select variables to visualize
        
        **3.** Choose visualization type
        
        **4.** Customize dimensions
        
        **5.** Generate ASCII art
        
        **6.** Download your creation
        """)
    
    with col2:
        st.markdown("""
        ### 📊 C H A R T  T Y P E S
        
        ✧ **Line Charts** - Flowing connections
        
        ✧ **Scatter Plots** - Point distributions
        
        ✧ **Bar Charts** - Categorical data
        
        ✧ **Histograms** - Data distributions
        """)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
        <div style='text-align: center; padding: 2rem; background: rgba(185, 103, 255, 0.1); border-radius: 15px; border: 1px solid #b967ff;'>
            <p style='font-size: 1.1rem; color: #ff71ce; margin: 0;'>✧･ﾟ: *✧･ﾟ:* Perfect for README files, documentation, and retro aesthetics *:･ﾟ✧*:･ﾟ✧</p>
        </div>
    """, unsafe_allow_html=True)

# Footer with vaporwave style
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("""
    <div style='text-align: center; padding: 1rem;'>
        <p style='color: #ff71ce; font-size: 0.9rem; margin: 0;'>✧ Made with 💜 using Streamlit ✧</p>
        <p style='color: #01cdfe; font-size: 0.8rem; margin: 0;'>DATA2ASCII v1.0 - Vaporwave Edition</p>
    </div>
""", unsafe_allow_html=True)
