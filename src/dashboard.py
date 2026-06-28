import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from database import get_db_connection

COLORS = ['#ff4a75', '#F4A261', '#57CC99', '#E76F51', '#A8DADC', '#264653', '#E9C46A']

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
    df = pd.read_sql(query, conn)
    conn.close()
    if df.empty: return None

    df['date'] = pd.to_datetime(df['date'])
    df['month_str'] = df['date'].dt.strftime('%Y-%m')

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(6, 3.8), dpi=100)
    fig.patch.set_facecolor('#1e1e1e')
    ax.set_facecolor('#1e1e1e')

    if chart_type == "1. Avg Performance by Dept":
        dept_perf = df[df['department'] != 'Unknown'].groupby('department')['performance_rating'].mean().sort_values(ascending=False)
        bars = ax.bar(dept_perf.index, dept_perf.values, color=COLORS[:len(dept_perf)])
        ax.set_title("Average Performance by Department", color="white", fontweight="bold")
        ax.set_xticklabels(dept_perf.index, rotation=15)

    elif chart_type == "2. Monthly Work Hours Trend":
        monthly_hours = df.groupby('month_str')['hours_worked'].mean().reset_index()
        ax.plot(monthly_hours['month_str'], monthly_hours['hours_worked'], marker='o', color='#ff4a75', linewidth=2)
        ax.fill_between(monthly_hours['month_str'], monthly_hours['hours_worked'], alpha=0.15, color='#ff4a75')
        ax.set_title("Average Work Hours per Month", color="white", fontweight="bold")
        ax.set_xticklabels(monthly_hours['month_str'], rotation=30)

    elif chart_type == "3. Attendance Status Distribution":
        counts = df['attendance_status'].value_counts()
        ax.pie(counts.values, labels=counts.index, autopct='%1.1f%%', colors=COLORS[:len(counts)], startangle=140)
        ax.set_title("Distribution of Attendance Status", color="white", fontweight="bold")

    elif chart_type == "4. Hours Worked vs Performance scatter":
        positions = df['position'].unique()
        for i, pos in enumerate(positions):
            sub = df[df['position'] == pos]
            ax.scatter(sub['hours_worked'], sub['performance_rating'], label=pos, color=COLORS[i % len(COLORS)], alpha=0.6, edgecolors='white', s=30)
        slope, intercept, r_val, _, _ = stats.linregress(df['hours_worked'], df['performance_rating'])
        x_ln = np.linspace(df['hours_worked'].min(), df['hours_worked'].max(), 100)
        ax.plot(x_ln, slope * x_ln + intercept, color='white', linestyle='--', label=f'Trend (r = {r_val:.2f})')
        ax.legend(fontsize=8, loc="upper left")
        ax.set_title("Hours Worked vs. Performance", color="white", fontweight="bold")

    elif chart_type == "5. Distribution Histogram of Hours":
        n, bins, patches = ax.hist(df['hours_worked'], bins=15, color='#ff4a75', edgecolor='white', alpha=0.8)
        ax.set_title("Distribution of Hours Worked", color="white", fontweight="bold")

    elif chart_type == "6. Performance by Position":
        pos_perf = df.groupby('position')['performance_rating'].mean().sort_values(ascending=False)
        ax.bar(pos_perf.index, pos_perf.values, color=COLORS[:len(pos_perf)])
        ax.set_title("Average Performance by Position", color="white", fontweight="bold")

    plt.tight_layout()
    return fig