import pandas as pd
import mysql.connector
from mysql.connector import Error
import numpy as np

def get_db_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",              
            password="Sky-digong12",   # Your database server password
            database="employee"        
        )
    except Error as e:
        print(f"Error: {e}")
        return None

def clean_and_migrate_pipeline(file_path="employee_attendance_productivity.csv"):
    """
    Reads the raw uncleaned CSV file, cleans the anomalies inline,
    normalizes the structures, and loads them straight into the database.
    """
    conn = get_db_connection()
    if not conn:
        print("Database connection failed.")
        return
    cursor = conn.cursor()
    
    print(f"Loading raw file: {file_path}")
    try:
        df_raw = pd.read_csv(file_path)
    except FileNotFoundError:
        print("Raw data file not found! Please check your file paths.")
        return

    # --- 1. CLEANING STEP ---
    print("Executing data cleaning routines...")
    
    # Trim accidental white spaces from text variables
    string_cols = ['employee_id', 'employee_name', 'department', 'position', 'attendance_status']
    for col in string_cols:
        if col in df_raw.columns:
            df_raw[col] = df_raw[col].fillna("Unknown").astype(str).str.strip()
            
    # Fix typos and standardize names to match your cleaning rules
    df_raw['department'] = df_raw['department'].astype(str).str.strip().str.title()
    dept_mapping = {'Marketting': 'Marketing', 'Operatons': 'Operations', 'It Support': 'IT Support', 'Hr': 'HR', 'Nan': 'Unknown', 'None': 'Unknown'}
    df_raw['department'] = df_raw['department'].replace(dept_mapping)

    df_raw['attendance_status'] = df_raw['attendance_status'].astype(str).str.strip().str.title()
    df_raw['attendance_status'] = df_raw['attendance_status'].replace({'Wfh': 'Work From Home', 'Nan': 'Present', 'None': 'Present'})

    # Handle Logical Outliers matching your rules exactly (out-of-bounds to NaN)
    df_raw['hours_worked'] = pd.to_numeric(df_raw['hours_worked'], errors='coerce')
    df_raw['performance_rating'] = pd.to_numeric(df_raw['performance_rating'], errors='coerce')
    df_raw['tasks_completed'] = pd.to_numeric(df_raw['tasks_completed'], errors='coerce')
    df_raw['monthly_salary'] = pd.to_numeric(df_raw['monthly_salary'], errors='coerce')

    df_raw.loc[(df_raw['hours_worked'] < 0) | (df_raw['hours_worked'] > 24), 'hours_worked'] = np.nan
    df_raw.loc[(df_raw['performance_rating'] < 0) | (df_raw['performance_rating'] > 5), 'performance_rating'] = np.nan

    # Impute Missing Values with Medians instead of 0.0 to protect chart shapes
    for col in ['hours_worked', 'tasks_completed', 'performance_rating', 'monthly_salary']:
        median_val = df_raw[col].median()
        if pd.isna(median_val): median_val = 0.0
        df_raw[col] = df_raw[col].fillna(median_val)

    # Resolve timeline dates safely
    df_raw['date'] = pd.to_datetime(df_raw['date'], errors='coerce')
    df_raw = df_raw.sort_values(by=['employee_id'])
    synthetic_dates = pd.Timestamp('2025-01-01') + pd.to_timedelta(df_raw.groupby('employee_id').cumcount() * 3, unit='D')
    df_raw['date'] = df_raw['date'].fillna(synthetic_dates)
    df_raw['date'] = df_raw['date'].dt.strftime('%Y-%m-%d')

    df_raw = df_raw[df_raw['employee_id'] != 'Unknown']

    # --- 2. NORMALIZATION STEP ---
    print("Separating data collections...")
    
    # Extract unique employee table records
    df_sorted = df_raw.sort_values(by=['employee_id', 'date'])
    df_employees = df_sorted.groupby('employee_id').last().reset_index()
    df_employees = df_employees[['employee_id', 'employee_name', 'department', 'position', 'monthly_salary']]
    
    # Extract daily transaction log table records
    df_logs = df_raw[['employee_id', 'date', 'attendance_status', 'hours_worked', 'tasks_completed', 'performance_rating']]

    # --- 3. DATABASE INGESTION STEP ---
    print("Flushing old data and uploading clean master data to SQL server...")
    
    # Clean tables completely to prevent merging old messy runs with new uploads
    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("TRUNCATE TABLE attendance_logs;")
        cursor.execute("TRUNCATE TABLE employees;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conn.commit()
    except Error as db_err:
        print(f"Warning clearing tables: {db_err}")
    
    # --- DEBUGGING CHECKPOINT 1: PRE-UPLOAD ---
    print("\n" + "="*40)
    print("CHECKPOINT 1: DATA LEAVING CLEANER")
    print("="*40)
    print(f"Total Logs to Upload: {len(df_logs)}")
    print(f"Date range: {df_logs['date'].min()} to {df_logs['date'].max()}")
    print("\nMissing Values in Logs:")
    print(df_logs.isnull().sum())
    print("\nSample of clean logs (first 5 rows):")
    print(df_logs[['employee_id', 'date', 'hours_worked', 'performance_rating']].head(5))
    print("="*40 + "\n")

    def clean_tuple(record):
        cleaned = []
        for val in record:
            if pd.isna(val) or val == 'nan' or val == 'None' or val == 'NaN':
                cleaned.append(None)
            else:
                cleaned.append(val)
        return tuple(cleaned)
    
    # Load unique employees
    insert_emp_query = """
        INSERT INTO employees (employee_id, employee_name, department, position, monthly_salary)
        VALUES (%s, %s, %s, %s, %s)
    """
    emp_records = [clean_tuple(x) for x in df_employees.to_numpy()]
    cursor.executemany(insert_emp_query, emp_records)
    
    # Load transactional logs
    insert_log_query = """
        INSERT INTO attendance_logs (employee_id, date, attendance_status, hours_worked, tasks_completed, performance_rating)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    log_records = [clean_tuple(x) for x in df_logs.to_numpy()]
    cursor.executemany(insert_log_query, log_records)
    
    conn.commit()
    print(f"Success! Migrated {len(emp_records)} clean employee records and {len(log_records)} logs.")
    
    cursor.close()
    conn.close()

def fetch_all_employees():
    """Fetches all employee records from the SQL server for the GUI grid."""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT employee_id, employee_name, department, position, monthly_salary FROM employees ORDER BY employee_id;")
        records = cursor.fetchall()
    except Exception as e:
        print(f"Error fetching directory: {e}")
        records = []
    finally:
        cursor.close()
        conn.close()
        
    return records

if __name__ == "__main__":
    clean_and_migrate_pipeline()