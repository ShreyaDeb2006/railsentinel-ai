import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import csv
from datetime import datetime


# ============================================================
# RAILSENTINEL-AI
# Handheld Security Detection Simulator
# ============================================================


class RailSentinelApp:

    def __init__(self, root):

        self.root = root

        # -----------------------------
        # Window
        # -----------------------------

        self.root.title("RailSentinel-AI | Handheld Security Simulator")
        self.root.geometry("1100x700")
        self.root.minsize(1000, 650)

        self.root.configure(bg="#0f172a")

        # -----------------------------
        # Variables
        # -----------------------------

        self.location = tk.StringVar(value="Platform 1")
        self.device_status = tk.StringVar(value="READY")
        self.camera_status = tk.StringVar(value="READY")
        self.sensor_status = tk.StringVar(value="READY")

        self.result = tk.StringVar(
            value="SYSTEM READY — START A SCAN"
        )

        self.confidence = tk.StringVar(value="--")

        self.scan_count = 0
        self.is_scanning = False

        # -----------------------------
        # Colors
        # -----------------------------

        self.bg = "#0f172a"
        self.panel = "#1e293b"
        self.panel2 = "#334155"
        self.text = "#f8fafc"
        self.muted = "#94a3b8"
        self.green = "#22c55e"
        self.red = "#ef4444"
        self.yellow = "#f59e0b"
        self.blue = "#38bdf8"

        # -----------------------------
        # Style
        # -----------------------------

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "TCombobox",
            fieldbackground="#334155",
            background="#334155",
            foreground="white"
        )

        # -----------------------------
        # Build UI
        # -----------------------------

        self.create_header()
        self.create_status_bar()
        self.create_main_area()
        self.create_history_area()
        self.create_footer()

    # ========================================================
    # HEADER
    # ========================================================

    def create_header(self):

        header = tk.Frame(
            self.root,
            bg="#111827",
            height=90
        )

        header.pack(fill="x")
        header.pack_propagate(False)

        title = tk.Label(
            header,
            text="RAILSENTINEL-AI",
            font=("Segoe UI", 25, "bold"),
            fg=self.text,
            bg="#111827"
        )

        title.pack(side="left", padx=30, pady=18)

        subtitle = tk.Label(
            header,
            text="HANDHELD SECURITY DETECTION SIMULATOR",
            font=("Segoe UI", 11),
            fg=self.blue,
            bg="#111827"
        )

        subtitle.pack(side="left", pady=20)

        self.clock_label = tk.Label(
            header,
            text="",
            font=("Segoe UI", 11),
            fg=self.muted,
            bg="#111827"
        )

        self.clock_label.pack(side="right", padx=30)

        self.update_clock()

    # ========================================================
    # CLOCK
    # ========================================================

    def update_clock(self):

        current_time = datetime.now().strftime(
            "%d-%m-%Y   %H:%M:%S"
        )

        self.clock_label.config(text=current_time)

        self.root.after(1000, self.update_clock)

    # ========================================================
    # STATUS BAR
    # ========================================================

    def create_status_bar(self):

        status = tk.Frame(
            self.root,
            bg=self.bg,
            height=60
        )

        status.pack(fill="x", padx=25, pady=10)

        self.make_status_box(
            status,
            "DEVICE",
            self.device_status,
            self.green
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=5
        )

        self.make_status_box(
            status,
            "CAMERA",
            self.camera_status,
            self.green
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=5
        )

        self.make_status_box(
            status,
            "SENSORS",
            self.sensor_status,
            self.green
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=5
        )

    # ========================================================
    # STATUS BOX
    # ========================================================

    def make_status_box(
        self,
        parent,
        title,
        variable,
        color
    ):

        frame = tk.Frame(
            parent,
            bg=self.panel,
            height=55
        )

        label1 = tk.Label(
            frame,
            text=title,
            font=("Segoe UI", 9, "bold"),
            fg=self.muted,
            bg=self.panel
        )

        label1.pack(pady=(7, 0))

        label2 = tk.Label(
            frame,
            textvariable=variable,
            font=("Segoe UI", 11, "bold"),
            fg=color,
            bg=self.panel
        )

        label2.pack()

        return frame

    # ========================================================
    # MAIN AREA
    # ========================================================

    def create_main_area(self):

        main = tk.Frame(
            self.root,
            bg=self.bg
        )

        main.pack(
            fill="both",
            expand=True,
            padx=25
        )

        # -----------------------------
        # LEFT PANEL
        # -----------------------------

        left = tk.Frame(
            main,
            bg=self.panel
        )

        left.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 10)
        )

        tk.Label(
            left,
            text="SCAN CONTROL",
            font=("Segoe UI", 15, "bold"),
            fg=self.text,
            bg=self.panel
        ).pack(
            anchor="w",
            padx=25,
            pady=(20, 15)
        )

        tk.Label(
            left,
            text="Scanning location",
            font=("Segoe UI", 10),
            fg=self.muted,
            bg=self.panel
        ).pack(
            anchor="w",
            padx=25
        )

        self.location_box = ttk.Combobox(
            left,
            textvariable=self.location,
            values=[
                "Platform 1",
                "Platform 2",
                "Platform 3",
                "Platform 4",
                "Coach A1",
                "Coach B2",
                "Luggage Area",
                "Entry Gate"
            ],
            state="readonly",
            font=("Segoe UI", 11)
        )

        self.location_box.pack(
            fill="x",
            padx=25,
            pady=(5, 25)
        )

        self.scan_button = tk.Button(
            left,
            text="START SCAN",
            font=("Segoe UI", 16, "bold"),
            fg="white",
            bg="#2563eb",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            height=2,
            command=self.start_scan
        )

        self.scan_button.pack(
            fill="x",
            padx=25,
            pady=10
        )

        self.reset_button = tk.Button(
            left,
            text="RESET DEVICE",
            font=("Segoe UI", 11, "bold"),
            fg=self.text,
            bg=self.panel2,
            activebackground="#475569",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            command=self.reset_device
        )

        self.reset_button.pack(
            fill="x",
            padx=25,
            pady=5
        )

        # -----------------------------
        # SENSOR READINGS
        # -----------------------------

        tk.Label(
            left,
            text="SIMULATED SENSOR DATA",
            font=("Segoe UI", 12, "bold"),
            fg=self.text,
            bg=self.panel
        ).pack(
            anchor="w",
            padx=25,
            pady=(25, 10)
        )

        self.camera_value = self.create_sensor_row(
            left,
            "Camera Analysis"
        )

        self.chemical_value = self.create_sensor_row(
            left,
            "Chemical Signature"
        )

        self.environment_value = self.create_sensor_row(
            left,
            "Environmental Sensor"
        )

        # -----------------------------
        # RIGHT PANEL
        # -----------------------------

        right = tk.Frame(
            main,
            bg=self.panel
        )

        right.pack(
            side="right",
            fill="both",
            expand=True,
            padx=(10, 0)
        )

        tk.Label(
            right,
            text="DETECTION RESULT",
            font=("Segoe UI", 15, "bold"),
            fg=self.text,
            bg=self.panel
        ).pack(
            pady=(20, 15)
        )

        self.result_label = tk.Label(
            right,
            textvariable=self.result,
            font=("Segoe UI", 22, "bold"),
            fg=self.text,
            bg=self.panel,
            wraplength=420
        )

        self.result_label.pack(
            pady=25
        )

        # -----------------------------
        # Confidence
        # -----------------------------

        confidence_title = tk.Label(
            right,
            text="SIMULATED CONFIDENCE",
            font=("Segoe UI", 10, "bold"),
            fg=self.muted,
            bg=self.panel
        )

        confidence_title.pack()

        self.confidence_label = tk.Label(
            right,
            textvariable=self.confidence,
            font=("Segoe UI", 30, "bold"),
            fg=self.blue,
            bg=self.panel
        )

        self.confidence_label.pack(
            pady=5
        )

        # -----------------------------
        # Location
        # -----------------------------

        self.current_location_label = tk.Label(
            right,
            text="LOCATION: Platform 1",
            font=("Segoe UI", 11),
            fg=self.muted,
            bg=self.panel
        )

        self.current_location_label.pack(
            pady=10
        )

        # -----------------------------
        # Alert box
        # -----------------------------

        self.alert_box = tk.Label(
            right,
            text=(
                "No active alert\n"
                "System monitoring normally"
            ),
            font=("Segoe UI", 11),
            fg=self.green,
            bg="#14532d",
            padx=25,
            pady=20,
            width=38
        )

        self.alert_box.pack(
            pady=20
        )

    # ========================================================
    # SENSOR ROW
    # ========================================================

    def create_sensor_row(self, parent, title):

        frame = tk.Frame(
            parent,
            bg=self.panel2
        )

        frame.pack(
            fill="x",
            padx=25,
            pady=4
        )

        tk.Label(
            frame,
            text=title,
            font=("Segoe UI", 10),
            fg=self.text,
            bg=self.panel2
        ).pack(
            side="left",
            padx=10,
            pady=7
        )

        value = tk.Label(
            frame,
            text="--",
            font=("Segoe UI", 10, "bold"),
            fg=self.blue,
            bg=self.panel2
        )

        value.pack(
            side="right",
            padx=10
        )

        return value

    # ========================================================
    # HISTORY
    # ========================================================

    def create_history_area(self):

        frame = tk.Frame(
            self.root,
            bg=self.panel,
            height=130
        )

        frame.pack(
            fill="x",
            padx=25,
            pady=(10, 5)
        )

        frame.pack_propagate(False)

        tk.Label(
            frame,
            text="SCAN HISTORY",
            font=("Segoe UI", 12, "bold"),
            fg=self.text,
            bg=self.panel
        ).pack(
            anchor="w",
            padx=15,
            pady=(8, 3)
        )

        list_frame = tk.Frame(
            frame,
            bg=self.panel
        )

        list_frame.pack(
            fill="both",
            expand=True,
            padx=15
        )

        self.history = tk.Listbox(
            list_frame,
            font=("Consolas", 9),
            bg="#0f172a",
            fg=self.text,
            selectbackground="#334155",
            relief="flat",
            height=3
        )

        self.history.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar = tk.Scrollbar(
            list_frame,
            command=self.history.yview
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.history.config(
            yscrollcommand=scrollbar.set
        )

    # ========================================================
    # FOOTER
    # ========================================================

    def create_footer(self):

        footer = tk.Frame(
            self.root,
            bg=self.bg,
            height=50
        )

        footer.pack(
            fill="x",
            padx=25,
            pady=5
        )

        export_button = tk.Button(
            footer,
            text="EXPORT HISTORY",
            font=("Segoe UI", 10, "bold"),
            fg=self.text,
            bg=self.panel2,
            relief="flat",
            command=self.export_history
        )

        export_button.pack(
            side="left"
        )

        tk.Label(
            footer,
            text="SIMULATION MODE • Sensor readings are simulated",
            font=("Segoe UI", 9),
            fg=self.muted,
            bg=self.bg
        ).pack(
            side="right"
        )

    # ========================================================
    # START SCAN
    # ========================================================

    def start_scan(self):

        if self.is_scanning:
            return

        self.is_scanning = True

        self.scan_button.config(
            text="SCANNING...",
            state="disabled",
            bg="#475569"
        )

        self.device_status.set("SCANNING")
        self.camera_status.set("ACTIVE")
        self.sensor_status.set("ANALYZING")

        self.result.set(
            "ANALYZING SIGNALS..."
        )

        self.result_label.config(
            fg=self.yellow
        )

        self.confidence.set("--")

        self.alert_box.config(
            text="Scanning environment...\nPlease wait.",
            fg=self.yellow,
            bg="#78350f"
        )

        self.current_location_label.config(
            text=f"LOCATION: {self.location.get()}"
        )

        self.animate_scan(0)

    # ========================================================
    # SCAN ANIMATION
    # ========================================================

    def animate_scan(self, step):

        if step >= 6:
            self.complete_scan()
            return

        camera_value = random.randint(45, 95)
        chemical_value = random.randint(20, 90)
        environment_value = random.randint(30, 85)

        self.camera_value.config(
            text=f"{camera_value}%"
        )

        self.chemical_value.config(
            text=f"{chemical_value}%"
        )

        self.environment_value.config(
            text=f"{environment_value}%"
        )

        self.root.after(
            400,
            lambda: self.animate_scan(step + 1)
        )

    # ========================================================
    # COMPLETE SCAN
    # ========================================================

    def complete_scan(self):

        self.is_scanning = False

        self.scan_button.config(
            text="START SCAN",
            state="normal",
            bg="#2563eb"
        )

        self.device_status.set("READY")
        self.camera_status.set("READY")
        self.sensor_status.set("READY")

        # ----------------------------------------------------
        # SIMULATED RESULT
        # ----------------------------------------------------

        result = random.choices(
            ["CLEAR", "SUSPICIOUS"],
            weights=[80, 20]
        )[0]

        confidence = random.randint(82, 98)

        self.confidence.set(
            f"{confidence}%"
        )

        time_now = datetime.now().strftime(
            "%H:%M:%S"
        )

        location = self.location.get()

        self.scan_count += 1

        # ----------------------------------------------------
        # CLEAR
        # ----------------------------------------------------

        if result == "CLEAR":

            self.result.set(
                "✓ CLEAR"
            )

            self.result_label.config(
                fg=self.green
            )

            self.alert_box.config(
                text=(
                    "NO SUSPICIOUS SIGNATURE DETECTED\n"
                    "Continue normal monitoring."
                ),
                fg=self.green,
                bg="#14532d"
            )

        # ----------------------------------------------------
        # SUSPICIOUS
        # ----------------------------------------------------

        else:

            self.result.set(
                "⚠ SUSPICIOUS"
            )

            self.result_label.config(
                fg=self.red
            )

            self.alert_box.config(
                text=(
                    "SECURITY ALERT\n"
                    "Notify authorized security personnel."
                ),
                fg=self.red,
                bg="#7f1d1d"
            )

            messagebox.showwarning(
                "RailSentinel-AI Security Alert",
                "A simulated suspicious signature was detected.\n\n"
                "This is a software demonstration only.\n"
                "Follow authorized security procedures."
            )

        # ----------------------------------------------------
        # Add history
        # ----------------------------------------------------

        entry = (
            f"{time_now}  |  "
            f"{location:<15} |  "
            f"{result:<11} |  "
            f"{confidence}%"
        )

        self.history.insert(
            0,
            entry
        )

    # ========================================================
    # RESET
    # ========================================================

    def reset_device(self):

        if self.is_scanning:
            return

        self.device_status.set("READY")
        self.camera_status.set("READY")
        self.sensor_status.set("READY")

        self.result.set(
            "SYSTEM READY — START A SCAN"
        )

        self.result_label.config(
            fg=self.text
        )

        self.confidence.set("--")

        self.camera_value.config(
            text="--"
        )

        self.chemical_value.config(
            text="--"
        )

        self.environment_value.config(
            text="--"
        )

        self.alert_box.config(
            text=(
                "No active alert\n"
                "System monitoring normally"
            ),
            fg=self.green,
            bg="#14532d"
        )

    # ========================================================
    # EXPORT HISTORY
    # ========================================================

    def export_history(self):

        if self.history.size() == 0:

            messagebox.showinfo(
                "Export",
                "There are no scans to export yet."
            )

            return

        file_path = filedialog.asksaveasfilename(
            title="Save Scan History",
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ],
            initialfile="rail_sentinel_scan_history.csv"
        )

        if not file_path:
            return

        with open(
            file_path,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "Time",
                "Location",
                "Result",
                "Confidence"
            ])

            for item in self.history.get(0, tk.END):

                parts = item.split("|")

                if len(parts) == 4:

                    writer.writerow([
                        parts[0].strip(),
                        parts[1].strip(),
                        parts[2].strip(),
                        parts[3].strip()
                    ])

        messagebox.showinfo(
            "Export Successful",
            "Scan history exported successfully."
        )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = RailSentinelApp(root)

    root.mainloop()
    