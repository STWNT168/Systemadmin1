import time
import json
import os
from datetime import datetime, timedelta

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

DATA_FILE = "work_logger_data.json"
CATEGORIES = ["Call", "Repair", "Drafting", "Maintenance", "Meeting", "Deployment", "Monitoring", "Other"]

# -------------------------------------------------------------------
# MODULAR PLUGIN ARCHITECTURE
# Add new features here without breaking core tracking logic.
# -------------------------------------------------------------------
class BaseAppModule:
    """Base class for future pluggable modules (e.g., Export to CSV, Sync to Server)."""
    def __init__(self, app_instance):
        self.app = app_instance

    def on_entry_created(self, entry):
        pass

# Example plugin placeholder
class AnalyticsPlugin(BaseAppModule):
    def on_entry_created(self, entry):
        print(f"[Plugin] New WO recorded: {entry['wo_number']}")


# -------------------------------------------------------------------
# CORE APPLICATION UI
# -------------------------------------------------------------------
class WorkLoggerUI(BoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(orientation="vertical", spacing=10, padding=10, **kwargs)
        self.app = app
        
        # Live Timer State
        self.timer_running = False
        self.timer_start_time = 0
        self.timer_event = None

        self._build_top_dashboard()
        self._build_timer_section()
        self._build_manual_entry_section()
        self._build_category_breakdown()
        self._build_recent_entries_list()
        
        self.refresh_ui()

    def _build_top_dashboard(self):
        dashboard = GridLayout(cols=3, size_hint_y=None, height=70, spacing=5)
        
        # Today
        box_today = BoxLayout(orientation="vertical")
        box_today.add_widget(Label(text="[b]TODAY[/b]", markup=True, font_size="12sp"))
        self.lbl_today = Label(text="0h | 0 WOs", font_size="14sp")
        box_today.add_widget(self.lbl_today)
        
        # Week
        box_week = BoxLayout(orientation="vertical")
        box_week.add_widget(Label(text="[b]THIS WEEK[/b]", markup=True, font_size="12sp"))
        self.lbl_week = Label(text="0h | 0 WOs", font_size="14sp")
        box_week.add_widget(self.lbl_week)

        # All-Time & Top
        box_all = BoxLayout(orientation="vertical")
        box_all.add_widget(Label(text="[b]ALL-TIME / TOP[/b]", markup=True, font_size="12sp"))
        self.lbl_all = Label(text="0h | None", font_size="14sp")
        box_all.add_widget(self.lbl_all)

        dashboard.add_widget(box_today)
        dashboard.add_widget(box_week)
        dashboard.add_widget(box_all)
        self.add_widget(dashboard)

    def _build_timer_section(self):
        timer_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=50, spacing=10)
        self.lbl_timer = Label(text="00:00:00", font_size="20sp", size_hint_x=0.4)
        self.btn_timer = Button(text="Start Timer", background_color=(0.2, 0.7, 0.3, 1), size_hint_x=0.6)
        self.btn_timer.bind(on_press=self.toggle_timer)
        
        timer_box.add_widget(self.lbl_timer)
        timer_box.add_widget(self.btn_timer)
        self.add_widget(timer_box)

    def _build_manual_entry_section(self):
        form = GridLayout(cols=2, size_hint_y=None, height=130, spacing=5)
        
        form.add_widget(Label(text="Category:", size_hint_x=0.3))
        self.spinner_cat = Spinner(text=CATEGORIES[0], values=CATEGORIES)
        form.add_widget(self.spinner_cat)

        form.add_widget(Label(text="Description:", size_hint_x=0.3))
        self.txt_desc = TextInput(hint_text="e.g. Server reboot", multiline=False)
        form.add_widget(self.txt_desc)

        form.add_widget(Label(text="Duration (mins):", size_hint_x=0.3))
        self.txt_duration = TextInput(hint_text="60", input_filter="int", multiline=False)
        form.add_widget(self.txt_duration)

        self.btn_add = Button(text="Log Manual Entry", size_hint_y=None, height=40, background_color=(0.2, 0.5, 0.8, 1))
        self.btn_add.bind(on_press=self.log_manual_entry)
        
        self.add_widget(form)
        self.add_widget(self.btn_add)

    def _build_category_breakdown(self):
        self.add_widget(Label(text="[b]Category Split (% of time)[/b]", markup=True, size_hint_y=None, height=25))
        self.breakdown_container = BoxLayout(orientation="vertical", size_hint_y=None, height=100, spacing=2)
        self.add_widget(self.breakdown_container)

    def _build_recent_entries_list(self):
        self.add_widget(Label(text="[b]Recent Work Orders[/b]", markup=True, size_hint_y=None, height=25))
        scroll = ScrollView()
        self.entries_container = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.entries_container.bind(minimum_height=self.entries_container.setter('height'))
        scroll.add_widget(self.entries_container)
        self.add_widget(scroll)

    # --- TIMER LOGIC ---
    def toggle_timer(self, instance):
        if not self.timer_running:
            self.timer_running = True
            self.timer_start_time = time.time()
            self.btn_timer.text = "Stop & Auto-Log"
            self.btn_timer.background_color = (0.8, 0.2, 0.2, 1)
            self.timer_event = Clock.schedule_interval(self.update_timer_label, 1)
        else:
            self.timer_running = False
            Clock.unschedule(self.timer_event)
            elapsed_seconds = int(time.time() - self.timer_start_time)
            mins = max(1, round(elapsed_seconds / 60))
            
            desc = self.txt_desc.text.strip() or "Live tracked task"
            self.app.add_entry(self.spinner_cat.text, desc, mins)
            
            # Reset
            self.lbl_timer.text = "00:00:00"
            self.btn_timer.text = "Start Timer"
            self.btn_timer.background_color = (0.2, 0.7, 0.3, 1)
            self.txt_desc.text = ""
            self.refresh_ui()

    def update_timer_label(self, dt):
        elapsed = int(time.time() - self.timer_start_time)
        hrs, remainder = divmod(elapsed, 3600)
        mins, secs = divmod(remainder, 60)
        self.lbl_timer.text = f"{hrs:02d}:{mins:02d}:{secs:02d}"

    # --- MANUAL LOGIC ---
    def log_manual_entry(self, instance):
        try:
            mins = int(self.txt_duration.text)
        except ValueError:
            return  # Duration invalid
        
        desc = self.txt_desc.text.strip() or "Manual entry"
        self.app.add_entry(self.spinner_cat.text, desc, mins)
        self.txt_duration.text = ""
        self.txt_desc.text = ""
        self.refresh_ui()

    # --- UI UPDATES ---
    def refresh_ui(self):
        entries = self.app.data["entries"]
        
        # Calculate stats
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        start_of_week = now - timedelta(days=now.weekday())

        today_mins, today_count = 0, 0
        week_mins, week_count = 0, 0
        all_mins = 0
        cat_totals = {c: 0 for c in CATEGORIES}

        for e in entries:
            dt = datetime.fromisoformat(e["timestamp"])
            dur = e["duration_mins"]
            all_mins += dur
            cat_totals[e["category"]] += dur

            if dt.strftime("%Y-%m-%d") == today_str:
                today_mins += dur
                today_count += 1

            if dt >= start_of_week:
                week_mins += dur
                week_count += 1

        top_cat = max(cat_totals, key=cat_totals.get) if all_mins > 0 else "None"

        # Update Top Stats
        self.lbl_today.text = f"{today_mins/60:.1f}h | {today_count} WOs"
        self.lbl_week.text = f"{week_mins/60:.1f}h | {week_count} WOs"
        self.lbl_all.text = f"{all_mins/60:.1f}h | Top: {top_cat}"

        # Update Breakdown
        self.breakdown_container.clear_widgets()
        for cat in CATEGORIES:
            pct = (cat_totals[cat] / all_mins * 100) if all_mins > 0 else 0
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=20)
            row.add_widget(Label(text=f"{cat[:8]}:", size_hint_x=0.3, font_size="10sp"))
            pb = ProgressBar(max=100, value=pct, size_hint_x=0.7)
            row.add_widget(pb)
            self.breakdown_container.add_widget(row)

        # Update Recent List
        self.entries_container.clear_widgets()
        for e in reversed(entries[-20:]):  # Last 20 entries
            lbl = Label(
                text=f"[b]{e['wo_number']}[/b] | {e['category']} | {e['duration_mins']}m\n{e['description']}",
                markup=True,
                size_hint_y=None,
                height=40,
                font_size="11sp"
            )
            self.entries_container.add_widget(lbl)


# -------------------------------------------------------------------
# MAIN APP CLASS
# -------------------------------------------------------------------
class WorkLoggerApp(App):
    def build(self):
        self.title = "Work Tracker"
        self.load_data()
        self.modules = [AnalyticsPlugin(self)]  # Extensible plugin array
        self.ui = WorkLoggerUI(self)
        return self.ui

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {"next_wo": 1, "entries": []}
        else:
            self.data = {"next_wo": 1, "entries": []}

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.data, f, indent=2)

    def add_entry(self, category, description, duration_mins):
        wo_num = f"WO-{self.data['next_wo']:04d}"
        self.data["next_wo"] += 1
        
        entry = {
            "wo_number": wo_num,
            "category": category,
            "description": description,
            "duration_mins": duration_mins,
            "timestamp": datetime.now().isoformat()
        }
        
        self.data["entries"].append(entry)
        self.save_data()

        # Notify modules/plugins
        for module in self.modules:
            module.on_entry_created(entry)

if __name__ == "__main__":
    WorkLoggerApp().run()

