import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from database import get_db_connection

COLORS = ['#2C7BB6', '#F4A261', '#57CC99', '#E76F51', '#A8DADC', '#264653', '#E9C46A', '#F4A261']
ACCENT = '#2C7BB6'

def fetch_summary_metrics():
    conn = get_db_connection()
    if not conn:
        return {"total_employees": 0, "avg_hours": 0.0, "total_tasks": 0, "avg_performance": 0.0}
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM employees) as total_employees,
                ROUND(AVG(hours_worked), 2) as avg_hours,
                SUM(tasks_completed) as total_tasks,
                ROUND(AVG(performance_rating), 2) as avg_performance
            FROM attendance_logs;
        """)
        metrics = cursor.fetchone()
    except Exception:
        metrics = {"total_employees": 0, "avg_hours": 0.0, "total_tasks": 0, "avg_performance": 0.0}
    finally:
        cursor.close()
        conn.close()
    return metrics

def generate_selected_chart(chart_type):
    conn = get_db_connection()
    if not conn: return None
    
    query = """
        SELECT e.employee_id, e.employee_name, e.department, e.position, e.monthly_salary,
               a.date, a.attendance_status, a.hours_worked, a.tasks_completed, a.performance_rating
        FROM attendance_logs a 
        JOIN employees e ON a.employee_id = e.employee_id;
    """
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
    except Exception as e:
        print(f"Error querying dashboard data: {e}")
        rows = []
    finally:
        cursor.close()
        conn.close()
        
    if not rows: return None
    
    df = pd.DataFrame(rows)

    # Convert MySQL Decimal objects into standard Pandas floats
    numeric_columns = ['hours_worked', 'tasks_completed', 'performance_rating', 'monthly_salary']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    # Structural transformations for plotting strings
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date') # Crucial for clean trend lines!
    df['month'] = df['date'].dt.to_period('M')
    df['month_str'] = df['month'].astype(str)

    # --- DEBUGGING CHECKPOINT 2: POST-FETCH ---
    print("\n" + "="*40)
    print("CHECKPOINT 2: DATA ENTERING DASHBOARD")
    print("="*40)
    print(f"Total Rows Fetched from SQL: {len(df)}")
    print(f"Are there duplicates? {df.duplicated(subset=['employee_id', 'date']).sum()} found.")
    print("\nSample of data fed to Matplotlib (first 5 rows):")
    print(df[['employee_id', 'date', 'hours_worked', 'performance_rating']].head(5))
    print("="*40 + "\n")
    

    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=100)
    ax.set_facecolor('#F9F9F9')
    fig.patch.set_facecolor('white')

    if chart_type == "1. Avg Performance by Dept":
        dept_perf = df[df['department'] != 'Unknown'].groupby('department')['performance_rating'].mean().sort_values(ascending=False)
        bars = ax.bar(dept_perf.index, dept_perf.values, color=COLORS[:len(dept_perf)], edgecolor='white', linewidth=0.8)
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.03, f'{h:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold', color='#333333')
        ax.set_title('Average Performance Rating by Department', fontsize=12, fontweight='bold', pad=15, color='black')
        ax.axhline(dept_perf.mean(), color='#E76F51', linestyle='--', linewidth=1.5, label=f'Overall Avg: {dept_perf.mean():.2f}')
        ax.set_ylim(0, 5.5)
        ax.set_ylabel('Average Performance Rating', color='black')
        ax.tick_params(axis='x', rotation=15, colors='black')
        ax.tick_params(axis='y', colors='black')
        ax.legend(fontsize=8)
        ax.spines[['top', 'right']].set_visible(False)

    elif chart_type == "2. Monthly Work Hours Trend":
        monthly_hours = df.groupby('month_str')['hours_worked'].mean().reset_index()
        ax.plot(monthly_hours['month_str'], monthly_hours['hours_worked'], marker='o', color=ACCENT, linewidth=2.2, markersize=6, markerfacecolor='white', markeredgecolor=ACCENT, markeredgewidth=2)
        ax.fill_between(monthly_hours['month_str'], monthly_hours['hours_worked'], alpha=0.12, color=ACCENT)
        ax.set_title('Average Hours Worked per Month', fontsize=12, fontweight='bold', pad=15, color='black')
        ax.axhline(monthly_hours['hours_worked'].mean(), color='#E76F51', linestyle='--', linewidth=1.5, label=f'Overall Avg: {monthly_hours["hours_worked"].mean():.2f} hrs')
        ax.tick_params(axis='x', rotation=45, colors='black')
        ax.tick_params(axis='y', colors='black')
        ax.set_ylabel('Average Hours Worked', color='black')
        ax.legend(fontsize=8)
        ax.spines[['top', 'right']].set_visible(False)

    elif chart_type == "3. Attendance Status Distribution":
        fig.patch.set_facecolor('white')
        attendance_counts = df['attendance_status'].value_counts()
        wedges, texts, autotexts = ax.pie(attendance_counts.values, labels=attendance_counts.index, autopct='%1.1f%%', colors=COLORS[:len(attendance_counts)], startangle=140, pctdistance=0.82, wedgeprops=dict(edgecolor='white', linewidth=2))
        for text in texts: text.set_color('black')
        for autotext in autotexts: autotext.set_fontweight('bold'); autotext.set_color('white')
        ax.set_title('Distribution of Attendance Status', fontsize=12, fontweight='bold', pad=15, color='black')

    elif chart_type == "4. Hours Worked vs Performance scatter":
        positions = df['position'].unique()
        pos_colors = {pos: COLORS[i % len(COLORS)] for i, pos in enumerate(positions)}
        for pos in positions:
            subset = df[df['position'] == pos]
            ax.scatter(subset['hours_worked'], subset['performance_rating'], label=pos, color=pos_colors[pos], alpha=0.6, s=40, edgecolors='white', linewidth=0.5)
        
        if len(df) > 1 and df['hours_worked'].nunique() > 1:
            slope, intercept, r, p, _ = stats.linregress(df['hours_worked'], df['performance_rating'])
            x_line = np.linspace(df['hours_worked'].min(), df['hours_worked'].max(), 100)
            ax.plot(x_line, slope * x_line + intercept, color='#333333', linewidth=1.8, linestyle='--', label=f'Trend (r = {r:.3f})')
        
        ax.set_title('Hours Worked vs. Performance Rating by Position', fontsize=12, fontweight='bold', pad=15, color='black')
        ax.legend(fontsize=8, loc='upper left')
        ax.tick_params(colors='black')
        ax.spines[['top', 'right']].set_visible(False)

    elif chart_type == "5. Distribution Histogram of Hours":
        n, bins, patches = ax.hist(df['hours_worked'], bins=20, color=ACCENT, edgecolor='white', linewidth=0.8, alpha=0.85)
        norm_vals = n / n.max() if n.max() > 0 else n
        for patch, val in zip(patches, norm_vals):
            patch.set_facecolor(plt.cm.Blues(0.3 + val * 0.6))
        ax.axvline(df['hours_worked'].mean(), color='#E76F51', linestyle='--', linewidth=1.8, label=f'Mean: {df["hours_worked"].mean():.2f} hrs')
        ax.axvline(df['hours_worked'].median(), color='#57CC99', linestyle='--', linewidth=1.8, label=f'Median: {df["hours_worked"].median():.2f} hrs')
        ax.set_title('Distribution of Hours Worked', fontsize=12, fontweight='bold', pad=15, color='black')
        ax.legend(fontsize=8)
        ax.tick_params(colors='black')
        ax.spines[['top', 'right']].set_visible(False)

    elif chart_type == "6. Performance by Position":
        pos_perf = df.groupby('position')['performance_rating'].mean().sort_values(ascending=False)
        pos_colors = {pos: COLORS[i % len(COLORS)] for i, pos in enumerate(pos_perf.index)}
        bars6 = ax.bar(pos_perf.index, pos_perf.values, color=[pos_colors[p] for p in pos_perf.index], edgecolor='white', linewidth=0.8)
        for bar in bars6:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, h + 0.03, f'{h:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold', color='black')
        ax.set_title('Average Performance Rating by Position', fontsize=12, fontweight='bold', pad=15, color='black')
        ax.axhline(pos_perf.mean(), color='#E76F51', linestyle='--', linewidth=1.5, label=f'Overall Avg: {pos_perf.mean():.2f}')
        ax.set_ylim(0, 5.5)
        ax.legend(fontsize=8)
        ax.tick_params(colors='black')
        ax.spines[['top', 'right']].set_visible(False)

    plt.tight_layout()
    return fig