"""
OPS LOG — System Admin Work Order Tracker
Kivy rebuild (native Android app via Buildozer).
"""

import json
import os
import uuid
from datetime import datetime, timedelta

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget

# ---------------------------------------------------------------- palette --
BG = (0.0784, 0.0902, 0.1098, 1)
PANEL = (0.1059, 0.1216, 0.1529, 1)
PANEL2 = (0.1255, 0.1412, 0.1765, 1)
BORDER = (0.1686, 0.1882, 0.2196, 1)
TEXT = (0.9137, 0.9059, 0.8784, 1)
MUTED = (0.5451, 0.5765, 0.6314, 1)
MUTED2 = (0.3608, 0.3843, 0.4392, 1)
AMBER = (0.851, 0.5765, 0.1804, 1)

CATEGORIES = [
    {"id": "call", "label": "Call", "color": (0.3569, 0.5608, 0.851, 1)},
    {"id": "repair", "label": "Repair", "color": (0.851, 0.3843, 0.1804, 1)},
    {"id": "draft", "label": "Drafting", "color": (0.3098, 0.6588, 0.5412, 1)},
    {"id": "maint", "label": "Maintenance", "color": (0.7098, 0.5333, 0.2471, 1)},
    {"id": "meet", "label": "Meeting", "color": (0.6078, 0.4196, 0.851, 1)},
    {"id": "deploy", "label": "Deployment", "color": (0.3569, 0.749, 0.4196, 1)},
    {"id": "monitor", "label": "Monitoring", "color": (0.3098, 0.7216, 0.7686, 1)},
    {"id": "other", "label": "Other", "color": (0.4902, 0.5176, 0.5725, 1)},
]
CAT_MAP = {c["id"]: c for c in CATEGORIES}

Window.clearcolor = BG


def today_str(d=None):
    d = d or datetime.now()
    return d.strftime("%Y-%m-%d")


# ------------------------------------------------------------- widgets ----
class Panel(BoxLayout):
    """A BoxLayout with a rounded panel background."""

    def __init__(self, bg=PANEL, border=BORDER, radius=8, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*bg)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
            Color(*border)
            self._line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, radius), width=1)
        self.bind(pos=self._update, size=self._update)

    def _update(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size
        self._line.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(8))


class CategoryChip(ToggleButton):
    def __init__(self, cat, **kwargs):
        super().__init__(**kwargs)
        self.cat = cat
        self.text = cat["label"]
        self.font_size = dp(11)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = PANEL2
        self.color = MUTED
        self.group = "category"

    def on_state(self, widget, value):
        if value == "down":
            self.background_color = (self.cat["color"][0], self.cat["color"][1], self.cat["color"][2], 0.18)
            self.color = self.cat["color"]
        else:
            self.background_color = PANEL2
            self.color = MUTED


class BreakdownRow(BoxLayout):
    def __init__(self, cat, minutes, max_minutes, **kwargs):
        super().__init__(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(20), **kwargs)
        self.add_widget(Label(text=cat["label"], color=TEXT, font_size=dp(12), size_hint_x=None, width=dp(92),
                               halign="left", valign="middle"))
        track = Widget(size_hint_x=1)
        with track.canvas:
            Color(*BORDER)
            self._track_rect = RoundedRectangle(pos=track.pos, size=(track.width, dp(8)), radius=[dp(4)])
            pct = (minutes / max_minutes) if max_minutes else 0
            Color(*cat["color"])
            self._fill_rect = RoundedRectangle(pos=track.pos, size=(track.width * pct, dp(8)), radius=[dp(4)])
        def _upd(_, __, pct=pct):
            self._track_rect.pos = (track.x, track.y + track.height / 2 - dp(4))
            self._track_rect.size = (track.width, dp(8))
            self._fill_rect.pos = (track.x, track.y + track.height / 2 - dp(4))
            self._fill_rect.size = (track.width * pct, dp(8))
        track.bind(pos=_upd, size=_upd)
        self.add_widget(track)
        self.add_widget(Label(text=f"{minutes/60:.1f}h", color=MUTED, font_size=dp(12),
                               size_hint_x=None, width=dp(48)))


class LogEntryRow(BoxLayout):
    def __init__(self, entry, on_delete, **kwargs):
        super().__init__(orientation="horizontal", spacing=dp(10), size_hint_y=None, height=dp(70),
                          padding=(dp(12), dp(8)), **kwargs)
        cat = CAT_MAP[entry["category"]]
        with self.canvas.before:
            Color(*PANEL)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])
            Color(*cat["color"])
            self._bar = RoundedRectangle(pos=self.pos, size=(dp(3), self.height), radius=[dp(2)])
        self.bind(pos=self._update, size=self._update)

        self.add_widget(Label(text=entry["wo"], color=MUTED2, font_size=dp(10), size_hint_x=None,
                               width=dp(58), valign="top", halign="left"))

        body = BoxLayout(orientation="vertical", spacing=dp(2))
        top_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(20), spacing=dp(8))
        top_row.add_widget(Label(text=f"[b]{cat['label']}[/b]", markup=True, color=cat["color"],
                                  font_size=dp(10.5), size_hint_x=None, width=dp(80)))
        top_row.add_widget(Label(text=entry["time"], color=MUTED, font_size=dp(11), size_hint_x=None, width=dp(50)))
        top_row.add_widget(Label(text=f"{entry['duration']}m", color=AMBER, font_size=dp(11)))
        body.add_widget(top_row)
        body.add_widget(Label(text=entry["description"], color=TEXT, font_size=dp(12.5),
                               halign="left", valign="top", text_size=(Window.width - dp(160), None)))
        self.add_widget(body)

        del_btn = Button(text="X", size_hint_x=None, width=dp(28), background_normal="",
                          background_color=(0, 0, 0, 0), color=MUTED2, font_size=dp(12))
        del_btn.bind(on_release=lambda *_: on_delete(entry["id"]))
        self.add_widget(del_btn)

    def _update(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size
        self._bar.pos = self.pos
        self._bar.size = (dp(3), self.height)


# ------------------------------------------------------------- root app ---
class OpsLogRoot(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(14), spacing=dp(10), **kwargs)
        self.entries = []
        self.selected_category = "call"
        self.current_view = "today"
        self.mode = "manual"
        self.timer_running = False
        self.timer_start = None
        self.timer_desc = ""

        self.data_file = os.path.join(App.get_running_app().user_data_dir, "entries.json")
        self.next_wo_num = 1

        self._build_header()
        self._build_stats()
        self._build_view_tabs()
        self._build_breakdown()
        self._build_form()
        self._build_log_list()
        self._build_footer()

        self.load_entries()
        Clock.schedule_interval(self._tick_clock, 30)
        self._tick_clock()

    # ---- header ----
    def _build_header(self):
        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(54))
        title_block = BoxLayout(orientation="vertical")
        eyebrow = Label(text="// SYSTEM ADMINISTRATION", color=AMBER, font_size=dp(10),
                         halign="left", size_hint_y=None, height=dp(16))
        eyebrow.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        title = Label(text="[b]OPS LOG[/b]", markup=True, color=TEXT, font_size=dp(22),
                      halign="left", size_hint_y=None, height=dp(30))
        title.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        title_block.add_widget(eyebrow)
        title_block.add_widget(title)
        header.add_widget(title_block)

        self.clock_label = Label(text="—", color=MUTED, font_size=dp(12), halign="right",
                                  size_hint_x=None, width=dp(140))
        self.clock_label.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        header.add_widget(self.clock_label)
        self.add_widget(header)

    def _tick_clock(self, *args):
        now = datetime.now()
        self.clock_label.text = now.strftime("%a %b %d\n%I:%M %p")

    # ---- stats ----
    def _build_stats(self):
        self.stats_grid = GridLayout(cols=3, size_hint_y=None, height=dp(64), spacing=dp(8))
        self.stat_hours = self._make_stat_box("0.0h", "Logged")
        self.stat_count = self._make_stat_box("0", "Entries")
        self.stat_top = self._make_stat_box("—", "Top Category")
        for box in (self.stat_hours, self.stat_count, self.stat_top):
            self.stats_grid.add_widget(box)
        self.add_widget(self.stats_grid)

    def _make_stat_box(self, num, label):
        box = Panel(orientation="vertical", padding=dp(10))
        num_lbl = Label(text=num, color=TEXT, font_size=dp(20), bold=True, size_hint_y=0.65)
        lbl = Label(text=label.upper(), color=MUTED, font_size=dp(10), size_hint_y=0.35)
        box.add_widget(num_lbl)
        box.add_widget(lbl)
        box.num_lbl = num_lbl
        return box

    # ---- view tabs ----
    def _build_view_tabs(self):
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(38), spacing=dp(4))
        self.tab_buttons = {}
        for key, label in (("today", "Today"), ("week", "This Week"), ("all", "All Time")):
            btn = ToggleButton(text=label, group="view", state="down" if key == "today" else "normal",
                                background_normal="", background_down="",
                                background_color=PANEL2, color=AMBER if key == "today" else MUTED,
                                font_size=dp(11.5))
            btn.bind(on_release=lambda b, k=key: self._set_view(k))
            self.tab_buttons[key] = btn
            row.add_widget(btn)
        self.add_widget(row)

    def _set_view(self, key):
        self.current_view = key
        for k, b in self.tab_buttons.items():
            b.color = AMBER if k == key else MUTED
        self.render()

    # ---- breakdown ----
    def _build_breakdown(self):
        self.breakdown_panel = Panel(orientation="vertical", padding=dp(12), spacing=dp(6),
                                      size_hint_y=None, height=dp(90))
        title = Label(text="BREAKDOWN", color=MUTED, font_size=dp(10.5), size_hint_y=None, height=dp(16),
                      halign="left")
        title.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
        self.breakdown_panel.add_widget(title)
        self.breakdown_body = BoxLayout(orientation="vertical", spacing=dp(5))
        self.breakdown_panel.add_widget(self.breakdown_body)
        self.add_widget(self.breakdown_panel)

    # ---- form ----
    def _build_form(self):
        self.form_panel = Panel(orientation="vertical", padding=dp(14), spacing=dp(8),
                                 size_hint_y=None, height=dp(330))

        mode_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(38), spacing=dp(6))
        self.mode_manual_btn = ToggleButton(text="Manual Entry", group="mode", state="down",
                                             background_normal="", background_color=PANEL2,
                                             color=AMBER, font_size=dp(11.5))
        self.mode_timer_btn = ToggleButton(text="Live Timer", group="mode",
                                            background_normal="", background_color=PANEL2,
                                            color=MUTED, font_size=dp(11.5))
        self.mode_manual_btn.bind(on_release=lambda *_: self._set_mode("manual"))
        self.mode_timer_btn.bind(on_release=lambda *_: self._set_mode("timer"))
        mode_row.add_widget(self.mode_manual_btn)
        mode_row.add_widget(self.mode_timer_btn)
        self.form_panel.add_widget(mode_row)

        cat_grid = GridLayout(cols=4, size_hint_y=None, height=dp(70), spacing=dp(5))
        self.cat_chips = []
        for cat in CATEGORIES:
            chip = CategoryChip(cat, state="down" if cat["id"] == "call" else "normal")
            chip.bind(on_release=lambda c, cat=cat: self._select_category(cat["id"]))
            cat_grid.add_widget(chip)
            self.cat_chips.append(chip)
        self.form_panel.add_widget(cat_grid)

        # dynamic body: manual block or timer block
        self.form_body = BoxLayout(orientation="vertical", spacing=dp(6))
        self.form_panel.add_widget(self.form_body)
        self._build_manual_block()
        self._build_timer_block()
        self._set_mode("manual")

        self.add_widget(self.form_panel)

    def _select_category(self, cat_id):
        self.selected_category = cat_id

    def _set_mode(self, mode):
        self.mode = mode
        self.mode_manual_btn.color = AMBER if mode == "manual" else MUTED
        self.mode_timer_btn.color = AMBER if mode == "timer" else MUTED
        self.form_body.clear_widgets()
        self.form_body.add_widget(self.manual_block if mode == "manual" else self.timer_block)

    def _build_manual_block(self):
        self.manual_block = BoxLayout(orientation="vertical", spacing=dp(6))
        self.desc_input = TextInput(hint_text="What did you do? e.g. Restarted mail relay service",
                                     multiline=True, size_hint_y=None, height=dp(56),
                                     background_color=PANEL2, foreground_color=TEXT,
                                     hint_text_color=MUTED2, padding=(dp(10), dp(10)))
        self.manual_block.add_widget(self.desc_input)

        row2 = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(44))
        self.dur_input = TextInput(hint_text="Duration (min)", input_filter="int", multiline=False,
                                    background_color=PANEL2, foreground_color=TEXT, hint_text_color=MUTED2,
                                    padding=(dp(10), dp(10)))
        self.time_input = TextInput(hint_text="Time (HH:MM)", multiline=False,
                                     background_color=PANEL2, foreground_color=TEXT, hint_text_color=MUTED2,
                                     padding=(dp(10), dp(10)))
        row2.add_widget(self.dur_input)
        row2.add_widget(self.time_input)
        self.manual_block.add_widget(row2)

        log_btn = Button(text="LOG WORK ORDER", bold=True, background_normal="",
                          background_color=AMBER, color=(0.1, 0.08, 0.03, 1), size_hint_y=None, height=dp(46))
        log_btn.bind(on_release=lambda *_: self._log_manual())
        self.manual_block.add_widget(log_btn)

    def _build_timer_block(self):
        self.timer_block = BoxLayout(orientation="vertical", spacing=dp(6))
        self.timer_desc_input = TextInput(hint_text="What are you working on?",
                                           multiline=True, size_hint_y=None, height=dp(56),
                                           background_color=PANEL2, foreground_color=TEXT,
                                           hint_text_color=MUTED2, padding=(dp(10), dp(10)))
        self.timer_block.add_widget(self.timer_desc_input)

        self.timer_display = Label(text="00:00:00", color=AMBER, font_size=dp(34), bold=True,
                                    size_hint_y=None, height=dp(50))
        self.timer_block.add_widget(self.timer_display)
        self.timer_status = Label(text="NOT RUNNING", color=MUTED, font_size=dp(10.5),
                                   size_hint_y=None, height=dp(18))
        self.timer_block.add_widget(self.timer_status)

        self.timer_btn = Button(text="START TIMER", bold=True, background_normal="",
                                 background_color=(0.3569, 0.749, 0.4196, 1), color=(0.04, 0.1, 0.05, 1),
                                 size_hint_y=None, height=dp(46))
        self.timer_btn.bind(on_release=lambda *_: self._toggle_timer())
        self.timer_block.add_widget(self.timer_btn)

    def _toggle_timer(self):
        if not self.timer_running:
            desc = self.timer_desc_input.text.strip()
            if not desc:
                self._alert("Describe what you're working on before starting the timer.")
                return
            self.timer_running = True
            self.timer_start = datetime.now()
            self.timer_desc = desc
            self.timer_btn.text = "STOP TIMER"
            self.timer_btn.background_color = (0.851, 0.3843, 0.1804, 1)
            self.timer_status.text = "RUNNING"
            Clock.schedule_interval(self._update_timer_display, 1)
        else:
            self.timer_running = False
            Clock.unschedule(self._update_timer_display)
            elapsed_min = max(1, round((datetime.now() - self.timer_start).total_seconds() / 60))
            self._add_entry(self.selected_category, self.timer_desc, elapsed_min,
                             today_str(), self.timer_start.strftime("%H:%M"))
            self.timer_desc_input.text = ""
            self.timer_display.text = "00:00:00"
            self.timer_status.text = "NOT RUNNING"
            self.timer_btn.text = "START TIMER"
            self.timer_btn.background_color = (0.3569, 0.749, 0.4196, 1)

    def _update_timer_display(self, dt):
        elapsed = int((datetime.now() - self.timer_start).total_seconds())
        h, rem = divmod(elapsed, 3600)
        m, s = divmod(rem, 60)
        self.timer_display.text = f"{h:02d}:{m:02d}:{s:02d}"

    def _log_manual(self):
        desc = self.desc_input.text.strip()
        dur_text = self.dur_input.text.strip()
        time_text = self.time_input.text.strip()
        if not desc:
            self._alert("Describe the work.")
            return
        if not dur_text or int(dur_text) <= 0:
            self._alert("Enter a duration in minutes.")
            return
        time_val = time_text if time_text else datetime.now().strftime("%H:%M")
        self._add_entry(self.selected_category, desc, int(dur_text), today_str(), time_val)
        self.desc_input.text = ""
        self.dur_input.text = ""
        self.time_input.text = ""

    def _alert(self, msg):
        popup = Popup(title="", content=Label(text=msg, color=TEXT), size_hint=(0.8, 0.25))
        popup.open()

    # ---- log list ----
    def _build_log_list(self):
        scroll = ScrollView(size_hint=(1, 1))
        self.log_list_body = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None, padding=(0, dp(4)))
        self.log_list_body.bind(minimum_height=self.log_list_body.setter("height"))
        scroll.add_widget(self.log_list_body)
        self.add_widget(scroll)

    # ---- footer ----
    def _build_footer(self):
        footer = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40))
        clear_btn = Button(text="Clear all entries", background_normal="", background_color=(0, 0, 0, 0),
                            color=MUTED, font_size=dp(11))
        clear_btn.bind(on_release=lambda *_: self._confirm_clear())
        footer.add_widget(clear_btn)
        self.add_widget(footer)

    def _confirm_clear(self):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))
        content.add_widget(Label(text="Delete all logged work orders?\nThis cannot be undone.", color=TEXT))
        btn_row = BoxLayout(orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(44))
        popup = Popup(title="Confirm", content=content, size_hint=(0.85, 0.35))
        yes_btn = Button(text="Delete", background_color=(0.851, 0.3843, 0.1804, 1))
        no_btn = Button(text="Cancel")

        def do_clear(*_):
            self.entries = []
            self.save_entries()
            self.render()
            popup.dismiss()

        yes_btn.bind(on_release=do_clear)
        no_btn.bind(on_release=lambda *_: popup.dismiss())
        btn_row.add_widget(yes_btn)
        btn_row.add_widget(no_btn)
        content.add_widget(btn_row)
        popup.open()

    # ---- data ----
    def load_entries(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r") as f:
                    self.entries = json.load(f)
        except Exception:
            self.entries = []
        self.next_wo_num = len(self.entries) + 1
        self.render()

    def save_entries(self):
        try:
            with open(self.data_file, "w") as f:
                json.dump(self.entries, f)
        except Exception:
            pass

    def _add_entry(self, category, description, duration, date, time_val):
        wo = f"WO-{self.next_wo_num:04d}"
        self.next_wo_num += 1
        self.entries.append({
            "id": uuid.uuid4().hex[:10],
            "wo": wo,
            "category": category,
            "description": description,
            "duration": duration,
            "date": date,
            "time": time_val,
        })
        self.save_entries()
        self.render()

    def _delete_entry(self, entry_id):
        self.entries = [e for e in self.entries if e["id"] != entry_id]
        self.save_entries()
        self.render()

    def _filtered_entries(self):
        if self.current_view == "today":
            t = today_str()
            return [e for e in self.entries if e["date"] == t]
        if self.current_view == "week":
            week_ago = datetime.now() - timedelta(days=7)
            return [e for e in self.entries if datetime.strptime(e["date"], "%Y-%m-%d") >= week_ago]
        return list(self.entries)

    # ---- render ----
    def render(self):
        entries = self._filtered_entries()

        total_min = sum(e["duration"] for e in entries)
        self.stat_hours.num_lbl.text = f"{total_min/60:.1f}h"
        self.stat_count.num_lbl.text = str(len(entries))

        by_cat = {}
        for e in entries:
            by_cat[e["category"]] = by_cat.get(e["category"], 0) + e["duration"]
        if by_cat:
            top_id = max(by_cat, key=by_cat.get)
            self.stat_top.num_lbl.text = CAT_MAP[top_id]["label"]
        else:
            self.stat_top.num_lbl.text = "—"

        self.breakdown_body.clear_widgets()
        if not by_cat:
            self.breakdown_body.add_widget(Label(text="No entries logged yet.", color=MUTED2,
                                                  font_size=dp(12), size_hint_y=None, height=dp(20)))
        else:
            max_val = max(by_cat.values())
            for cat_id, mins in sorted(by_cat.items(), key=lambda kv: -kv[1]):
                self.breakdown_body.add_widget(BreakdownRow(CAT_MAP[cat_id], mins, max_val))

        self.log_list_body.clear_widgets()
        if not entries:
            self.log_list_body.add_widget(
                Label(text="Log book empty.\nLog your first work order above.", color=MUTED2,
                      font_size=dp(12), size_hint_y=None, height=dp(60))
            )
            return

        groups = {}
        for e in sorted(entries, key=lambda e: (e["date"], e["time"]), reverse=True):
            groups.setdefault(e["date"], []).append(e)

        today_s = today_str()
        yest_s = today_str(datetime.now() - timedelta(days=1))

        for date in sorted(groups.keys(), reverse=True):
            label_text = date
            if date == today_s:
                label_text = f"TODAY — {date}"
            elif date == yest_s:
                label_text = f"YESTERDAY — {date}"
            header = Label(text=label_text.upper(), color=MUTED, font_size=dp(11),
                            size_hint_y=None, height=dp(24), halign="left")
            header.bind(size=lambda w, *_: setattr(w, "text_size", w.size))
            self.log_list_body.add_widget(header)
            for entry in groups[date]:
                self.log_list_body.add_widget(LogEntryRow(entry, self._delete_entry))


class OpsLogApp(App):
    def build(self):
        self.title = "Ops Log"
        return OpsLogRoot()


if __name__ == "__main__":
    OpsLogApp().run()
