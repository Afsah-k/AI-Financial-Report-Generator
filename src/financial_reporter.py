import pandas as pd
from openai import OpenAI
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch
import matplotlib.colors as mcolors

class AIFinancialReporter:
    def __init__(self, model_type="local"):
        # Setup for Local Llama or OpenAI
        if model_type == "local":
            self.client = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
            self.model = "llama3"
        else:
            self.client = OpenAI(api_key="OPENAI_KEY")
            self.model = "gpt-4o"

    def process_data(self, file_path):
        df = pd.read_csv(file_path).sort_values('Year')
        
        # For automatic comparison of the last two year
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        return {
            "year": int(latest['Year']),
            "rev_growth": round(((latest['Revenue ($B)'] - prev['Revenue ($B)']) / prev['Revenue ($B)']) * 100, 2),
            "margin": latest['Operating Margin (%)'],
            "debt_ratio": round(latest['Total debt ($B)'] / latest['Total assets ($B)'], 2),
            "eps": latest['EPS ($)'],
            "risk_flag": "High" if latest['Total debt ($B)'] > latest['Total assets ($B)'] else "Moderate"
        }

    def generate_report(self, metrics):
        # Prompt template for document generation
        prompt = f"""
        Generate a professional financial audit report for the fiscal year {metrics['year']}.
        Metrics:
        - Revenue Growth: {metrics['rev_growth']}%
        - Operating Margin: {metrics['margin']}%
        - Debt-to-Asset Ratio: {metrics['debt_ratio']}
        - Risk Level: {metrics['risk_flag']}
        
        Format:
        ## Executive Summary
        ## Financial Health Analysis
        ## Risk & Recommendations
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    def save_report(self, content, filename="outputs/Financial_Report.md"):
        with open(filename, "w") as f:
            f.write(content)
        print(f"Report successfully generated and saved to {filename}")


def generate_visual_dashboard(file_path):
    
    # Load data
    df = pd.read_csv(file_path).sort_values('Year')

    # Extract latest and previous year for KPIs
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    revenue_growth = ((latest['Revenue ($B)'] - prev['Revenue ($B)']) / prev['Revenue ($B)']) * 100
    debt_ratio = latest['Total debt ($B)'] / latest['Total assets ($B)']

    # setting updates figure
    fig = plt.figure(figsize=(18, 13), facecolor="#f7f9fc")
    gs = GridSpec(3, 4, figure=fig, height_ratios=[1, 2, 2], hspace=0.45, wspace=0.05)

    # Main title
    fig.suptitle("Financial Performance Dashboard", fontsize=22, fontweight='bold', y=0.98)
    fig.text(0.5, 0.93, f"Company Financial Overview ({int(df['Year'].min())} - {int(df['Year'].max())})",
             ha='center', fontsize=12, color='dimgray')

   # ---------------- KPI CARDS ----------------
    kpi_titles = ["Latest Revenue ($B)", "Revenue Growth (%)", "Operating Margin (%)", "Debt/Asset Ratio"]
    kpi_values = [
        f"{latest['Revenue ($B)']:.2f}",
        f"{revenue_growth:.2f}%",
        f"{latest['Operating Margin (%)']:.2f}%",
        f"{debt_ratio:.2f}"
    ]
    
    # colours for cards
    card_colors = ["#24F27E", "#F2248E", "#F28E24", "#24EBF2"]

    for i in range(4):
        ax = fig.add_subplot(gs[0, i])
    
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
    
        # Rounded card
        rect = FancyBboxPatch(
            (0, 0), 1, 1,
            boxstyle="round,pad=0.05,rounding_size=0.1",
            transform=ax.transAxes,
            facecolor=card_colors[i],
            edgecolor="none"
        )
    
        ax.add_patch(rect)
    
        # KPI Value
        ax.text(0.5, 0.65, kpi_values[i], ha='center', va='center',fontsize=20, fontweight='bold', color="white")
    
        # KPI Title
        ax.text(0.5, 0.28, kpi_titles[i],ha='center', va='center',fontsize=11, color='white')

# ---------------- CHART 1: Revenue Trend ----------------
    ax1 = fig.add_subplot(gs[1, 0:2])
    ax1.set_facecolor("white")
    
    # Line
    ax1.plot(df['Year'], df['Revenue ($B)'], color='#B2F20C', linewidth=2.5)
    
    ax1.scatter(
        df['Year'],
        df['Revenue ($B)'],
        c='#E52512',
        s=80,
        edgecolors='#E5BE12',
        zorder=3
    )
    
    ax1.set_title("Revenue Trend", fontsize=14, fontweight='bold')
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Revenue ($B)")
    ax1.grid(True, alpha=0.3)
    
    # Label every 3rd point in graph
    for i, (x, y) in enumerate(zip(df['Year'], df['Revenue ($B)'])):
        if i % 3 == 0 or i == len(df) - 1:
            ax1.text(x, y + 0.3, f"{y:.1f}", fontsize=9, ha='center', va='bottom')

# ---------------- CHART 2: Operating Margin ----------------
    ax2 = fig.add_subplot(gs[1, 2:4])
    ax2.set_facecolor("white")


    #Create gradient
    custom_cmap = mcolors.LinearSegmentedColormap.from_list("custom_purple", ["#e6b9d8", "#7c4d79"])
    norm = mcolors.Normalize(vmin=df['Operating Margin (%)'].min(), vmax=df['Operating Margin (%)'].max())
    colors = [custom_cmap(norm(value)) for value in df['Operating Margin (%)']]

    #Plot bars
    bars = ax2.bar(df['Year'].astype(str), df['Operating Margin (%)'], 
                   color=colors, edgecolor='#5a3558', linewidth=0.4, width=0.8)

    ax2.set_title("Operating Margin by Year", fontsize=14, fontweight='bold')
    ax2.set_xlabel("Year")
    ax2.set_ylabel("Margin (%)")
    ax2.grid(axis='y', alpha=0.3, linestyle='--')

    # Add labels in black and only for every 3rd bar
    for i, bar in enumerate(bars):
        if i % 3 == 0 or i == len(bars) - 1:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2, height + 0.5, f"{height:.1f}%",
                     ha='center', va='bottom', fontsize=9, 
                     color='black', fontweight='bold')
    
    # X-axis
    plt.setp(ax2.get_xticklabels()[1::2], visible=False)
 
# ---------------- CHART 3: Debt vs Assets ----------------
    
    ax3 = fig.add_subplot(gs[2, 0:2])
    ax3.set_facecolor("white")

    # colors defination
    color_debt = '#89CEE8'   
    color_assets = '#AAFA91' 

    # Plot the lines
    ax3.plot(df['Year'], df['Total debt ($B)'], color=color_debt, linewidth=2, label='Total Debt', marker='o', markersize=4)
    ax3.plot(df['Year'], df['Total assets ($B)'], color=color_assets, linewidth=2, label='Total Assets', marker='s', markersize=4)

    ax3.fill_between(df['Year'], df['Total debt ($B)'], color=color_debt, alpha=0.6)
    ax3.fill_between(df['Year'], df['Total assets ($B)'], color=color_assets, alpha=0.4)

    ax3.set_title("Debt vs Assets", fontsize=14, fontweight='bold')
    ax3.set_xlabel("Year")
    ax3.set_ylabel("Value ($B)")
    ax3.grid(True, alpha=0.2, linestyle='--')
    ax3.legend(frameon=False, loc='upper left')

    ax3.xaxis.set_major_locator(plt.MaxNLocator(integer=True))

   # ---------------- CHART 4: EPS and P/E ----------------
    ax4 = fig.add_subplot(gs[2, 2:4])
    ax4.set_facecolor("white")
    
    # color of EPS
    ax4.plot(df['Year'], df['EPS ($)'], marker='o', linewidth=2.5, 
             color='#7951FC', label='EPS ($)') 
    
    ax4.set_title("EPS and P/E Ratio Trend", fontsize=14, fontweight='bold')
    ax4.set_xlabel("Year")
    ax4.set_ylabel("EPS ($)", color='black')
    ax4.grid(True, alpha=0.3)

    ax4b = ax4.twinx()
    
    # color to P/E Ratio
    ax4b.plot(df['Year'], df['P/E ratio'], marker='s', linestyle='--', linewidth=2, color='#FC9551', label='P/E Ratio') 
    ax4b.set_ylabel("P/E Ratio", color='black') 

    # Combined legend
    lines1, labels1 = ax4.get_legend_handles_labels()
    lines2, labels2 = ax4b.get_legend_handles_labels()
    ax4.legend(lines1 + lines2, labels1 + labels2, loc='upper left', frameon=False)

    # Clean up spines
    for ax in [ax1, ax2, ax3, ax4]:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

    ax4b.spines['top'].set_visible(False)

    fig.subplots_adjust(top=0.86, hspace=0.5, wspace=0.3)
    os.makedirs("outputs", exist_ok=True)

    plt.savefig("outputs/financial_dashboard.png", dpi=300, bbox_inches="tight")
    plt.show()

if __name__ == "__main__":

    path = r'data/McDonalds.csv'

    # Charts
    generate_visual_dashboard(path)

    # Metrics
    reporter = AIFinancialReporter(model_type="local")
    metrics = reporter.process_data(path)

    # LLM Report
    report_text = reporter.generate_report(metrics)

    # Save Report
    reporter.save_report(report_text, "outputs/MCD_Audit_2022.md")




