import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO
import base64
from typing import List, Tuple, Optional
import math

# Configure Streamlit page
st.set_page_config(
    page_title="ASCII Data Visualizer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class ASCIIPlotter:
    """Main class for generating ASCII plots"""
    
    def __init__(self, width: int = 80, height: int = 20, charset: str = ".:-=+*#%@"):
        self.width = width
        self.height = height
        self.charset = charset
        self.colored = False
        
    def set_dimensions(self, width: int, height: int):
        self.width = width
        self.height = height
        
    def set_charset(self, charset: str):
        self.charset = charset
        
    def set_colored(self, colored: bool):
        self.colored = colored
        
    def normalize_data(self, data: np.ndarray) -> np.ndarray:
        """Normalize data to 0-1 range"""
        if len(data) == 0:
            return data
        data_min, data_max = np.min(data), np.max(data)
        if data_max == data_min:
            return np.zeros_like(data)
        return (data - data_min) / (data_max - data_min)
    
    def value_to_char(self, value: float) -> str:
        """Convert normalized value to ASCII character"""
        if np.isnan(value):
            return ' '
        char_idx = int(value * (len(self.charset) - 1))
        char_idx = max(0, min(len(self.charset) - 1, char_idx))
        return self.charset[char_idx]
    
    def add_color(self, char: str, intensity: float) -> str:
        """Add ANSI color codes based on intensity"""
        if not self.colored or char == ' ':
            return char
        
        # Color gradient from blue (low) to red (high)
        if intensity < 0.2:
            color_code = '\033[34m'  # Blue
        elif intensity < 0.4:
            color_code = '\033[36m'  # Cyan
        elif intensity < 0.6:
            color_code = '\033[32m'  # Green
        elif intensity < 0.8:
            color_code = '\033[33m'  # Yellow
        else:
            color_code = '\033[31m'  # Red
        
        return f"{color_code}{char}\033[0m"
    
    def plot_line_chart(self, x_data: np.ndarray, y_data: np.ndarray, 
                       title: str = "Line Chart") -> str:
        """Generate ASCII line chart"""
        if len(x_data) == 0 or len(y_data) == 0:
            return "No data to plot"
        
        # Normalize data
        y_norm = self.normalize_data(y_data)
        
        # Create plot grid
        plot_grid = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
        # Plot points and lines
        for i in range(len(y_norm)):
            x_pos = int((i / (len(y_norm) - 1)) * (self.width - 1)) if len(y_norm) > 1 else self.width // 2
            y_pos = int((1 - y_norm[i]) * (self.height - 1))
            
            x_pos = max(0, min(self.width - 1, x_pos))
            y_pos = max(0, min(self.height - 1, y_pos))
            
            # Use different character for data points
            char = '*' if '*' in self.charset else self.charset[-1]
            if self.colored:
                plot_grid[y_pos][x_pos] = self.add_color(char, y_norm[i])
            else:
                plot_grid[y_pos][x_pos] = char
        
        # Convert to string
        result = [f"📈 {title}"]
        result.append("┌" + "─" * self.width + "┐")
        for row in plot_grid:
            result.append("│" + "".join(row) + "│")
        result.append("└" + "─" * self.width + "┘")
        
        # Add axis labels
        y_min, y_max = np.min(y_data), np.max(y_data)
        result.append(f"Y-axis: {y_min:.2f} to {y_max:.2f}")
        
        return "\n".join(result)
    
    def plot_histogram(self, data: np.ndarray, bins: int = 20, 
                      title: str = "Histogram") -> str:
        """Generate ASCII histogram"""
        if len(data) == 0:
            return "No data to plot"
        
        # Calculate histogram
        hist, bin_edges = np.histogram(data, bins=bins)
        hist_norm = hist / np.max(hist) if np.max(hist) > 0 else hist
        
        # Create plot
        result = [f"📊 {title}"]
        result.append("┌" + "─" * self.width + "┐")
        
        for i in range(self.height):
            row = "│"
            for j in range(len(hist_norm)):
                if j < self.width:
                    bar_height = hist_norm[j] * self.height
                    if (self.height - i - 1) < bar_height:
                        char = self.charset[-1]  # Use darkest character for bars
                        if self.colored:
                            row += self.add_color(char, hist_norm[j])
                        else:
                            row += char
                    else:
                        row += " "
            # Fill remaining width
            while len(row) < self.width + 1:
                row += " "
            row += "│"
            result.append(row)
        
        result.append("└" + "─" * self.width + "┘")
        
        # Add statistics
        result.append(f"Range: {np.min(data):.2f} to {np.max(data):.2f}")
        result.append(f"Mean: {np.mean(data):.2f}, Std: {np.std(data):.2f}")
        
        return "\n".join(result)
    
    def plot_scatter(self, x_data: np.ndarray, y_data: np.ndarray, 
                    title: str = "Scatter Plot") -> str:
        """Generate ASCII scatter plot"""
        if len(x_data) == 0 or len(y_data) == 0:
            return "No data to plot"
        
        # Normalize data
        x_norm = self.normalize_data(x_data)
        y_norm = self.normalize_data(y_data)
        
        # Create plot grid
        plot_grid = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
        # Plot points
        for i in range(len(x_norm)):
            x_pos = int(x_norm[i] * (self.width - 1))
            y_pos = int((1 - y_norm[i]) * (self.height - 1))
            
            x_pos = max(0, min(self.width - 1, x_pos))
            y_pos = max(0, min(self.height - 1, y_pos))
            
            char = 'o' if 'o' in self.charset else self.charset[len(self.charset)//2]
            if self.colored:
                intensity = (x_norm[i] + y_norm[i]) / 2
                plot_grid[y_pos][x_pos] = self.add_color(char, intensity)
            else:
                plot_grid[y_pos][x_pos] = char
        
        # Convert to string
        result = [f"🔸 {title}"]
        result.append("┌" + "─" * self.width + "┐")
        for row in plot_grid:
            result.append("│" + "".join(row) + "│")
        result.append("└" + "─" * self.width + "┘")
        
        return "\n".join(result)
    
    def plot_heatmap(self, data: np.ndarray, title: str = "Heatmap") -> str:
        """Generate ASCII heatmap"""
        if data.size == 0:
            return "No data to plot"
        
        # Ensure 2D array
        if data.ndim == 1:
            # Reshape 1D data into 2D
            side_length = int(np.sqrt(len(data)))
            if side_length * side_length == len(data):
                data = data.reshape(side_length, side_length)
            else:
                # Pad or trim to make square
                target_size = side_length * side_length
                if len(data) > target_size:
                    data = data[:target_size].reshape(side_length, side_length)
                else:
                    padded = np.zeros(target_size)
                    padded[:len(data)] = data
                    data = padded.reshape(side_length, side_length)
        
        # Resize to fit display
        if data.shape[0] > self.height or data.shape[1] > self.width:
            # Downsample
            row_step = max(1, data.shape[0] // self.height)
            col_step = max(1, data.shape[1] // self.width)
            data = data[::row_step, ::col_step]
        
        # Normalize
        data_norm = self.normalize_data(data.flatten()).reshape(data.shape)
        
        # Convert to ASCII
        result = [f"🔥 {title}"]
        result.append("┌" + "─" * data.shape[1] + "┐")
        
        for i in range(data.shape[0]):
            row = "│"
            for j in range(data.shape[1]):
                char = self.value_to_char(data_norm[i, j])
                if self.colored:
                    row += self.add_color(char, data_norm[i, j])
                else:
                    row += char
            row += "│"
            result.append(row)
        
        result.append("└" + "─" * data.shape[1] + "┘")
        
        return "\n".join(result)
    
    def plot_bar_chart(self, categories: List[str], values: np.ndarray, 
                      title: str = "Bar Chart") -> str:
        """Generate ASCII bar chart"""
        if len(values) == 0:
            return "No data to plot"
        
        # Normalize values
        values_norm = self.normalize_data(values)
        
        result = [f"📊 {title}"]
        result.append("┌" + "─" * self.width + "┐")
        
        # Calculate bar width
        bar_width = max(1, self.width // len(values))
        
        for i in range(self.height):
            row = "│"
            for j, val in enumerate(values_norm):
                start_pos = j * bar_width
                bar_height = val * self.height
                
                for k in range(bar_width):
                    if start_pos + k < self.width:
                        if (self.height - i - 1) < bar_height:
                            char = self.charset[-1]
                            if self.colored:
                                row += self.add_color(char, val)
                            else:
                                row += char
                        else:
                            row += " "
            
            # Fill remaining width
            while len(row) < self.width + 1:
                row += " "
            row += "│"
            result.append(row)
        
        result.append("└" + "─" * self.width + "┘")
        
        # Add category labels (truncated)
        if categories:
            label_row = "│"
            for i, cat in enumerate(categories):
                start_pos = i * bar_width
                cat_short = cat[:bar_width] if len(cat) > bar_width else cat
                label_row += cat_short.ljust(bar_width)[:self.width - len(label_row) + 1]
            result.append(label_row + "│")
        
        return "\n".join(result)

def load_sample_data():
    """Generate sample datasets"""
    np.random.seed(42)
    
    datasets = {
        "Sample Sine Wave": pd.DataFrame({
            'x': np.linspace(0, 4*np.pi, 100),
            'y': np.sin(np.linspace(0, 4*np.pi, 100)) + np.random.normal(0, 0.1, 100)
        }),
        "Random Data": pd.DataFrame({
            'values': np.random.normal(100, 15, 200),
            'categories': np.random.choice(['A', 'B', 'C', 'D'], 200),
            'x': np.random.uniform(0, 10, 200),
            'y': np.random.uniform(0, 10, 200)
        }),
        "Sales Data": pd.DataFrame({
            'month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'sales': [100, 120, 140, 110, 160, 180],
            'profit': [20, 25, 35, 22, 40, 45]
        }),
        "Correlation Example": pd.DataFrame({
            'x': np.linspace(0, 10, 50),
            'y_pos': np.linspace(0, 10, 50) + np.random.normal(0, 1, 50),
            'y_neg': 10 - np.linspace(0, 10, 50) + np.random.normal(0, 1, 50)
        })
    }
    
    return datasets

def create_download_link(text_content: str, filename: str) -> str:
    """Create download link for ASCII art"""
    b64 = base64.b64encode(text_content.encode()).decode()
    return f'<a href="data:text/plain;base64,{b64}" download="{filename}">📥 Download as TXT</a>'

def main():
    st.title("📊 ASCII Data Visualizer")
    st.markdown("Transform your data into beautiful ASCII art plots!")
    
    # Sidebar controls
    st.sidebar.header("🎛️ Controls")
    
    # Dataset selection/upload
    st.sidebar.subheader("📂 Data Source")
    data_source = st.sidebar.radio(
        "Choose data source:",
        ["Upload File", "Use Sample Data"]
    )
    
    df = None
    
    if data_source == "Upload File":
        uploaded_file = st.sidebar.file_uploader(
            "Upload CSV file",
            type=['csv'],
            help="Upload a CSV file to visualize"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.sidebar.success(f"✅ Loaded {len(df)} rows, {len(df.columns)} columns")
            except Exception as e:
                st.sidebar.error(f"❌ Error loading file: {e}")
    
    else:  # Sample data
        sample_datasets = load_sample_data()
        selected_sample = st.sidebar.selectbox(
            "Choose sample dataset:",
            list(sample_datasets.keys())
        )
        df = sample_datasets[selected_sample]
        st.sidebar.info(f"📊 {selected_sample} loaded")
    
    if df is not None:
        # Display dataset info
        with st.expander("📋 Dataset Preview"):
            st.dataframe(df.head())
            st.write(f"**Shape:** {df.shape[0]} rows × {df.shape[1]} columns")
            st.write("**Columns:**", list(df.columns))
        
        # Plot configuration
        st.sidebar.subheader("📈 Plot Configuration")
        
        plot_type = st.sidebar.selectbox(
            "Plot Type:",
            ["Line Chart", "Histogram", "Scatter Plot", "Bar Chart", "Heatmap"]
        )
        
        # Column selection based on plot type
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
        all_columns = df.columns.tolist()
        
        if plot_type == "Line Chart":
            if len(numeric_columns) >= 2:
                x_col = st.sidebar.selectbox("X-axis column:", numeric_columns)
                y_col = st.sidebar.selectbox("Y-axis column:", 
                                           [col for col in numeric_columns if col != x_col])
            else:
                st.sidebar.error("Need at least 2 numeric columns for line chart")
                return
        
        elif plot_type == "Histogram":
            if numeric_columns:
                data_col = st.sidebar.selectbox("Data column:", numeric_columns)
                bins = st.sidebar.slider("Number of bins:", 5, 50, 20)
            else:
                st.sidebar.error("Need at least 1 numeric column for histogram")
                return
        
        elif plot_type == "Scatter Plot":
            if len(numeric_columns) >= 2:
                x_col = st.sidebar.selectbox("X-axis column:", numeric_columns)
                y_col = st.sidebar.selectbox("Y-axis column:", 
                                           [col for col in numeric_columns if col != x_col])
            else:
                st.sidebar.error("Need at least 2 numeric columns for scatter plot")
                return
        
        elif plot_type == "Bar Chart":
            if categorical_columns and numeric_columns:
                cat_col = st.sidebar.selectbox("Category column:", categorical_columns)
                val_col = st.sidebar.selectbox("Value column:", numeric_columns)
            else:
                st.sidebar.error("Need 1 categorical and 1 numeric column for bar chart")
                return
        
        elif plot_type == "Heatmap":
            if numeric_columns:
                data_cols = st.sidebar.multiselect(
                    "Select columns for heatmap:",
                    numeric_columns,
                    default=numeric_columns[:min(5, len(numeric_columns))]
                )
                if not data_cols:
                    st.sidebar.error("Select at least 1 column for heatmap")
                    return
            else:
                st.sidebar.error("Need numeric columns for heatmap")
                return
        
        # ASCII configuration
        st.sidebar.subheader("🎨 ASCII Settings")
        
        charset_options = {
            "Light to Dark": ".:-=+*#%@",
            "Simple": ".#",
            "Blocks": "░▒▓█",
            "Dots": ".·•●",
            "Classic": " .*#",
            "Extended": " .·∶:∴∵∷≡≈≋≣≡◈◉●"
        }
        
        charset_name = st.sidebar.selectbox("Character Set:", list(charset_options.keys()))
        charset = charset_options[charset_name]
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            plot_width = st.slider("Width:", 20, 120, 80)
        with col2:
            plot_height = st.slider("Height:", 10, 40, 20)
        
        colored_ascii = st.sidebar.checkbox("🌈 Colored ASCII", value=False)
        
        # Create plotter
        plotter = ASCIIPlotter(plot_width, plot_height, charset)
        plotter.set_colored(colored_ascii)
        
        # Generate plot
        try:
            ascii_art = ""
            
            if plot_type == "Line Chart":
                x_data = df[x_col].values
                y_data = df[y_col].values
                ascii_art = plotter.plot_line_chart(x_data, y_data, f"{y_col} vs {x_col}")
            
            elif plot_type == "Histogram":
                data = df[data_col].dropna().values
                ascii_art = plotter.plot_histogram(data, bins, f"Histogram of {data_col}")
            
            elif plot_type == "Scatter Plot":
                x_data = df[x_col].values
                y_data = df[y_col].values
                ascii_art = plotter.plot_scatter(x_data, y_data, f"{y_col} vs {x_col}")
            
            elif plot_type == "Bar Chart":
                # Aggregate data by category
                grouped = df.groupby(cat_col)[val_col].mean()
                categories = grouped.index.tolist()
                values = grouped.values
                ascii_art = plotter.plot_bar_chart(categories, values, f"{val_col} by {cat_col}")
            
            elif plot_type == "Heatmap":
                heatmap_data = df[data_cols].corr().values
                ascii_art = plotter.plot_heatmap(heatmap_data, f"Correlation Matrix")
            
            # Display results
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader(f"🎨 ASCII {plot_type}")
                
                if colored_ascii:
                    # For colored ASCII, use HTML with monospace font
                    ascii_html = ascii_art.replace('\n', '<br>')
                    st.markdown(f"<pre style='font-family: monospace; font-size: 12px;'>{ascii_html}</pre>", 
                               unsafe_allow_html=True)
                else:
                    st.code(ascii_art, language=None)
                
                # Copy to clipboard button (JavaScript)
                if st.button("📋 Copy to Clipboard"):
                    st.code(ascii_art, language=None)
                    st.success("📋 ASCII art displayed above - select and copy manually")
                
                # Download link
                filename = f"ascii_{plot_type.lower().replace(' ', '_')}.txt"
                st.markdown(create_download_link(ascii_art, filename), unsafe_allow_html=True)
            
            with col2:
                st.subheader("📊 Reference Plot")
                
                # Create matplotlib comparison plot
                fig, ax = plt.subplots(figsize=(6, 4))
                
                if plot_type == "Line Chart":
                    ax.plot(df[x_col], df[y_col], 'b-o', markersize=3)
                    ax.set_xlabel(x_col)
                    ax.set_ylabel(y_col)
                
                elif plot_type == "Histogram":
                    ax.hist(df[data_col].dropna(), bins=bins, alpha=0.7)
                    ax.set_xlabel(data_col)
                    ax.set_ylabel('Frequency')
                
                elif plot_type == "Scatter Plot":
                    ax.scatter(df[x_col], df[y_col], alpha=0.6, s=20)
                    ax.set_xlabel(x_col)
                    ax.set_ylabel(y_col)
                
                elif plot_type == "Bar Chart":
                    grouped = df.groupby(cat_col)[val_col].mean()
                    ax.bar(grouped.index, grouped.values)
                    ax.set_xlabel(cat_col)
                    ax.set_ylabel(f"Mean {val_col}")
                    plt.xticks(rotation=45, ha='right')
                
                elif plot_type == "Heatmap":
                    corr_matrix = df[data_cols].corr()
                    im = ax.imshow(corr_matrix.values, cmap='viridis', aspect='auto')
                    ax.set_xticks(range(len(data_cols)))
                    ax.set_yticks(range(len(data_cols)))
                    ax.set_xticklabels(data_cols, rotation=45, ha='right')
                    ax.set_yticklabels(data_cols)
                    plt.colorbar(im, ax=ax)
                
                ax.set_title(f"{plot_type} - Reference")
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()
        
        except Exception as e:
            st.error(f"❌ Error generating plot: {e}")
            st.error("Please check your data and column selections.")
    
    else:
        st.info("👆 Please upload a dataset or select sample data from the sidebar to get started!")
        
        # Show feature overview
        st.markdown("""
        ## 🌟 Features
        
        - **📂 Multiple Data Sources**: Upload CSV files or use built-in sample datasets
        - **📈 Various Plot Types**: Line charts, histograms, scatter plots, bar charts, and heatmaps  
        - **🎨 Customizable ASCII Art**: Choose from multiple character sets and styles
        - **🎛️ Adjustable Resolution**: Control width and height of your ASCII plots
        - **🌈 Color Support**: Toggle between plain and colored ASCII output
        - **📋 Easy Export**: Copy to clipboard or download as TXT files
        - **📊 Reference Plots**: Compare with traditional matplotlib visualizations
        
        ## 🚀 How to Use
        
        1. **Upload your data** or select a sample dataset
        2. **Choose a plot type** that suits your data
        3. **Select columns** for visualization  
        4. **Customize ASCII settings** (characters, size, colors)
        5. **View and export** your ASCII masterpiece!
        """)

if __name__ == "__main__":
    main()
