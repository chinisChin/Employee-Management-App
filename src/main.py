import customtkinter as ctk
import pandas as pd
from tkinter import ttk, filedialog, messagebox
from database import clean_and_migrate_pipeline, fetch_all_employees, get_db_connection
from dashboard import fetch_summary_metrics, generate_selected_chart
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

ctk.set_appearance_mode("Dark")

class EmployeeManagementApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Employee Management System")
        self.geometry("1200x750")
        self.configure(fg_color="#121212")
        self.raw_file_path = None

        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)
        self.show_welcome_screen()

    def show_welcome_screen(self):
        self.clear_main_container()
        frame = ctk.CTkFrame(self.main_container, fg_color="#1a1a1a", corner_radius=15)
        frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.6, relheight=0.4)

        title = ctk.CTkLabel(frame, text="Employee Management System", font=("Arial", 28, "bold"), text_color="#ff4a75")
        title.pack(pady=(60, 10))
        sub = ctk.CTkLabel(frame, text="A Database and Data Analytics System", font=("Arial", 13), text_color="#b0b0b0")
        sub.pack(pady=5)

        open_btn = ctk.CTkButton(frame, text="Open System", font=("Arial", 14, "bold"), fg_color="#ff4a75", hover_color="#e03e63", height=40, command=self.show_file_selection_screen)
        open_btn.pack(pady=40)

    def show_file_selection_screen(self):
        self.clear_main_container()
        top_bar = ctk.CTkFrame(self.main_container, fg_color="#1a1a1a", height=70)
        top_bar.pack(side="top", fill="x")

        ctk.CTkButton(top_bar, text="← Back", width=70, fg_color="#2b2b2b", command=self.show_welcome_screen).pack(side="left", padx=15, pady=15)
        ctk.CTkLabel(top_bar, text="Data Ingestion Preview", font=("Arial", 16, "bold")).pack(side="left", padx=10)
        
        # Ingestion Button Triggers
        self.action_btn_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        self.action_btn_frame.pack(side="right", padx=15, pady=15)
        
        ctk.CTkButton(self.action_btn_frame, text="Select Uncleaned CSV", fg_color="#ff4a75", hover_color="#e03e63", command=self.browse_uncleaned_file).pack(side="left", padx=5)

        self.preview_container = ctk.CTkFrame(self.main_container, fg_color="#1e1e1e", corner_radius=10)
        self.preview_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.msg = ctk.CTkLabel(self.preview_container, text="Awaiting CSV ingestion layout data map...", text_color="#b0b0b0")
        self.msg.pack(expand=True)

    def browse_uncleaned_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            self.raw_file_path = file_path
            for w in self.preview_container.winfo_children(): w.destroy()
            for w in self.action_btn_frame.winfo_children(): w.destroy()
            
            # Put the buttons back but append the specific clean operation selector option
            ctk.CTkButton(self.action_btn_frame, text="Re-select File", fg_color="#2b2b2b", command=self.browse_uncleaned_file).pack(side="left", padx=5)
            ctk.CTkButton(self.action_btn_frame, text="Clean & Ingest Dataset 🚀", fg_color="#57CC99", hover_color="#3ca877", command=self.prompt_cleaning_routine).pack(side="left", padx=5)

            df = pd.read_csv(file_path, nrows=10)
            
            # Style Preview treeview to be charcoal/pink matching theme parameters
            style = ttk.Style()
            style.configure("Preview.Treeview", background="#1e1e1e", foreground="white", fieldbackground="#1e1e1e", rowheight=24)
            style.configure("Preview.Treeview.Heading", background="#1a1a1a", foreground="#ff4a75", font=("Arial", 9, "bold"))

            tree = ttk.Treeview(self.preview_container, columns=list(df.columns), show="headings", style="Preview.Treeview")
            for c in df.columns:
                tree.heading(c, text=c)
                tree.column(c, width=100, anchor="center")
            for _, r in df.iterrows():
                tree.insert("", "end", values=[str(v) for v in r])
            tree.pack(fill="both", expand=True, padx=15, pady=15)

    def prompt_cleaning_routine(self):
        if messagebox.askyesno("Clean Routine", "Do you want to clean this file and migrate parameters to local SQL?"):
            clean_and_migrate_pipeline(self.raw_file_path)
            self.show_main_dashboard_view()

    def show_main_dashboard_view(self):
        self.clear_main_container()
        
        top_nav = ctk.CTkFrame(self.main_container, fg_color="#1a1a1a", height=50)
        top_nav.pack(side="top", fill="x")
        ctk.CTkButton(top_nav, text="↺ Disconnect & Reset to Welcome", fg_color="#cf2a4b", hover_color="#a81d37", command=self.show_welcome_screen).pack(side="right", padx=15, pady=10)
        ctk.CTkLabel(top_nav, text="System Management Panel Instance Active", font=("Arial", 14, "bold"), text_color="#ff4a75").pack(side="left", padx=15)

        self.tab_view = ctk.CTkTabview(self.main_container, fg_color="#121212")
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_directory = self.tab_view.add("Interactive CRUD Directory")
        self.tab_analytics = self.tab_view.add("Selectable Charts Dashboard")

        self.setup_crud_directory_tab()
        self.setup_selectable_analytics_tab()

    def setup_crud_directory_tab(self):
        left_crud = ctk.CTkFrame(self.tab_directory, fg_color="#1e1e1e", width=280)
        left_crud.pack(side="left", fill="y", padx=10, pady=10)
        left_crud.pack_propagate(False)

        ctk.CTkLabel(left_crud, text="Manage Records Form", font=("Arial", 14, "bold"), text_color="#ff4a75").pack(pady=10)
        
        self.ent_id = ctk.CTkEntry(left_crud, placeholder_text="Emp ID (Primary Key)")
        self.ent_id.pack(pady=5, padx=15, fill="x")
        self.ent_name = ctk.CTkEntry(left_crud, placeholder_text="Full Name")
        self.ent_name.pack(pady=5, padx=15, fill="x")
        self.ent_dept = ctk.CTkEntry(left_crud, placeholder_text="Department")
        self.ent_dept.pack(pady=5, padx=15, fill="x")
        self.ent_pos = ctk.CTkEntry(left_crud, placeholder_text="Position")
        self.ent_pos.pack(pady=5, padx=15, fill="x")
        self.ent_sal = ctk.CTkEntry(left_crud, placeholder_text="Monthly Salary")
        self.ent_sal.pack(pady=5, padx=15, fill="x")

        ctk.CTkButton(left_crud, text="Save / Update Record", fg_color="#57CC99", hover_color="#3ca877", command=self.crud_save).pack(pady=10, padx=15, fill="x")
        ctk.CTkButton(left_crud, text="Delete Selection", fg_color="#cf2a4b", hover_color="#a81d37", command=self.crud_delete).pack(pady=5, padx=15, fill="x")

        right_grid = ctk.CTkFrame(self.tab_directory, fg_color="#1e1e1e")
        right_grid.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Resetting main view grid colors to elegant dark charcoal & pop pink highlight styles
        style = ttk.Style()
        style.configure("Grid.Treeview", background="#1e1e1e", foreground="white", rowheight=28, fieldbackground="#1e1e1e", borderwidth=0)
        style.map('Grid.Treeview', background=[('selected', '#ff4a75')], foreground=[('selected', 'white')])
        style.configure("Grid.Treeview.Heading", background="#1a1a1a", foreground="#ff4a75", font=("Arial", 10, "bold"))

        self.tree = ttk.Treeview(right_grid, columns=("id", "name", "dept", "pos", "salary"), show="headings", style="Grid.Treeview")
        for col, h in zip(("id", "name", "dept", "pos", "salary"), ("Employee ID", "Name", "Department", "Position", "Salary")):
            self.tree.heading(col, text=h)
            self.tree.column(col, width=110, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=15, pady=15)
        self.tree.bind("<<TreeviewSelect>>", self.on_grid_select_row)
        self.reload_grid()

    def reload_grid(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for emp in fetch_all_employees():
            self.tree.insert("", "end", values=(emp["employee_id"], emp["employee_name"], emp["department"], emp["position"], f"₱{emp['monthly_salary']:,.2f}"))

    def on_grid_select_row(self, event):
        sel = self.tree.selection()
        if sel:
            item = self.tree.item(sel[0])['values']
            self.ent_id.delete(0, 'end'); self.ent_id.insert(0, item[0])
            self.ent_name.delete(0, 'end'); self.ent_name.insert(0, item[1])
            self.ent_dept.delete(0, 'end'); self.ent_dept.insert(0, item[2])
            self.ent_pos.delete(0, 'end'); self.ent_pos.insert(0, item[3])
            clean_sal = item[4].replace('₱', '').replace(',', '')
            self.ent_sal.delete(0, 'end'); self.ent_sal.insert(0, clean_sal)

    def crud_save(self):
        # Fix: Safely fetching previous values for fields left empty during a manual form update
        emp_id = self.ent_id.get()
        if not emp_id:
            messagebox.showwarning("Warning", "Employee ID is required to map parameters.")
            return

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM employees WHERE employee_id = %s", (emp_id,))
        existing = cursor.fetchone()

        # Fallback to existing attributes if a text box is left blank
        name = self.ent_name.get() if self.ent_name.get() else (existing['employee_name'] if existing else "")
        dept = self.ent_dept.get() if self.ent_dept.get() else (existing['department'] if existing else "Unknown")
        pos = self.ent_pos.get() if self.ent_pos.get() else (existing['position'] if existing else "Staff")
        sal = float(self.ent_sal.get()) if self.ent_sal.get() else (existing['monthly_salary'] if existing else 0.0)

        query = """
            INSERT INTO employees (employee_id, employee_name, department, position, monthly_salary)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE employee_name=%s, department=%s, position=%s, monthly_salary=%s
        """
        cursor.execute(query, (emp_id, name, dept, pos, sal, name, dept, pos, sal))
        conn.commit(); conn.close()
        self.reload_grid(); messagebox.showinfo("CRUD", "Database Record Saved Successfully.")

    def crud_delete(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM employees WHERE employee_id = %s", (self.ent_id.get(),))
        conn.commit(); conn.close()
        self.reload_grid(); messagebox.showinfo("CRUD", "Record Erased from Server.")

    def setup_selectable_analytics_tab(self):
        ctrl_panel = ctk.CTkFrame(self.tab_analytics, fg_color="#1e1e1e", height=60)
        ctrl_panel.pack(side="top", fill="x", padx=10, pady=5)

        ctk.CTkLabel(ctrl_panel, text="Select Computation Graph:", font=("Arial", 12, "bold")).pack(side="left", padx=15, pady=15)
        
        chart_options = [
            "1. Avg Performance by Dept",
            "2. Monthly Work Hours Trend",
            "3. Attendance Status Distribution",
            "4. Hours Worked vs Performance scatter",
            "5. Distribution Histogram of Hours",
            "6. Performance by Position"
        ]
        
        self.chart_selector = ctk.CTkComboBox(ctrl_panel, values=chart_options, width=300, command=self.update_analytics_canvas)
        self.chart_selector.pack(side="left", padx=10, pady=15)
        self.chart_selector.set(chart_options[0])

        self.canvas_frame = ctk.CTkFrame(self.tab_analytics, fg_color="#1e1e1e", corner_radius=10)
        self.canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.update_analytics_canvas(chart_options[0])

    def update_analytics_canvas(self, chosen_chart):
        for w in self.canvas_frame.winfo_children(): w.destroy()
        fig = generate_selected_chart(chosen_chart)
        if fig:
            canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
            canvas.draw()

    def clear_main_container(self):
        for w in self.main_container.winfo_children(): w.destroy()

if __name__ == "__main__":
    app = EmployeeManagementApp()
    app.mainloop()