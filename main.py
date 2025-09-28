from datetime import datetime, timedelta
import json
import math
import os
import struct
import tempfile
import wave
import traceback

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.utils import platform, get_color_from_hex
from kivy.properties import BooleanProperty, StringProperty, ListProperty, ObjectProperty, NumericProperty
from kivy.config import Config

# Configure Kivy for better Android compatibility
Config.set('kivy', 'exit_on_escape', '0')

from kivymd.app import MDApp
from kivymd.theming import ThemableBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView
from kivy.uix.switch import Switch
from kivymd.uix.textfield import MDTextField
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.image import Image
from kivy.uix.slider import Slider
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.textinput import TextInput

NOTEBOOK_FILE = "notebook.json"

# --- Updated Notebook KV ---
NOTEBOOK_KV = """
<NotebookRoot>:
    orientation: 'vertical'
    spacing: dp(6)
    padding: dp(6)
    md_bg_color: 0.95, 0.95, 0.95, 1

    BoxLayout:
        size_hint_y: None
        height: dp(48)
        spacing: dp(6)
        MDIconButton:
            icon: "pencil"
            on_release: root.set_pen_color(0,0,0)
        MDIconButton:
            icon: "palette"
            on_release: root.set_pen_color(0,0,1)
            theme_text_color: "Custom"
            text_color: 0,0,1,1
        MDIconButton:
            icon: "palette"
            on_release: root.set_pen_color(1,0,0)
            theme_text_color: "Custom"
            text_color: 1,0,0,1
        MDIconButton:
            icon: "palette"
            on_release: root.set_pen_color(0,1,0)
            theme_text_color: "Custom"
            text_color: 0,1,0,1
        MDIconButton:
            icon: "image-plus"
            on_release: root.open_image_chooser()
        MDIconButton:
            icon: "content-save"
            on_release: root.save_notebook()
        MDIconButton:
            icon: "book-open"
            on_release: root.open_notes_viewer()

    BoxLayout:
        size_hint_y: None
        height: dp(40)
        spacing: dp(6)
        MDIconButton:
            icon: "minus"
            on_release: root.set_pen_size(1)
        MDIconButton:
            icon: "minus-thick"
            on_release: root.set_pen_size(5)
        MDIconButton:
            icon: "eraser"
            on_release: root.set_pen_color(1,1,1)

    DrawingPanel:
        id: drawpanel

<NotebookTextInput>:
    background_color: 0,0,0,0
    foreground_color: root.text_color
    font_size: '14sp'
    padding: [dp(10), dp(10), dp(10), dp(10)]
    multiline: True
    size_hint_y: None
    height: max(self.minimum_height, dp(200))
"""

# Fixed KV String for UI
KV = '''
#:import dp kivy.metrics.dp

MDBoxLayout:
    orientation: "vertical"
    spacing: dp(10)
    padding: dp(10)

    MDBoxLayout:
        orientation: "horizontal"
        size_hint_y: None
        height: dp(56)
        padding: dp(10)
        spacing: dp(10)

        MDLabel:
            text: "TiM@$k"
            theme_text_color: "Primary"
            halign: "left"
            font_style: "H6"
            size_hint_x: 0.6
            height: dp(56)

        MDIconButton:
            id: add_task_btn
            icon: "plus"
            on_release: app.open_task_dialog()
        MDIconButton:
            icon: "bell"
            on_release: app.test_alert()
        MDIconButton:
            icon: "notebook"
            on_release: app.open_notebook()
        MDIconButton:
            id: theme_toggle
            icon: "weather-night"
            on_release: app.toggle_theme()

    MDBoxLayout:
        orientation: "horizontal"
        size_hint_y: None
        height: dp(60)
        padding: dp(10)
        spacing: dp(10)

        MDLabel:
            text: app.current_date
            theme_text_color: "Secondary"
            size_hint_x: 0.6
            height: dp(60)

        MDLabel:
            text: app.current_time
            theme_text_color: "Primary"
            size_hint_x: 0.4
            halign: "right"
            font_style: "Subtitle1"
            height: dp(60)

    MDBoxLayout:
        orientation: "horizontal"
        size_hint_y: None
        height: dp(50)
        padding: dp(10)

        MDLabel:
            text: "Status:"
            theme_text_color: "Secondary"
            size_hint_x: 0.3
            height: dp(50)

        MDLabel:
            text: app.status_text
            theme_text_color: "Primary"
            size_hint_x: 0.7
            id: status_label
            height: dp(50)

    MDBoxLayout:
        orientation: "horizontal"
        size_hint_y: None
        height: dp(50)
        padding: dp(10)

        MDLabel:
            text: "Do Not Disturb:"
            theme_text_color: "Secondary"
            size_hint_x: 0.5
            height: dp(50)

        Switch:
            id: dnd_switch
            size_hint_x: 0.5
            active: False

    ScrollView:
        id: scroll_view

        MDGridLayout:
            id: tasks_container
            cols: 1
            spacing: dp(10)
            size_hint_y: None
            height: self.minimum_height
            padding: dp(10)
'''

# Appearance & Constants
Window.clearcolor = (0.95, 0.95, 0.95, 1)  # Light background

TASKS_FILE = "tasks.json"

DEFAULT_SLOTS = [
    ("08:00", "12:00", "💼 Work", "Focus on important tasks", True, "work"),
    ("15:00", "19:00", "💼 Work", "Project work and meetings", True, "work"),
    ("20:00", "22:00", "💻 Coding", "Personal projects", True, "coding"),
    ("22:00", "00:00", "🎯 Hacking", "Cybersecurity practice", True, "hacking"),
    ("00:00", "08:00", "📈 Trading", "Markets & analysis", True, "trading"),
]

CATEGORY_COLORS = {
    "work": "#4CAF50",      # Green
    "coding": "#2196F3",    # Blue
    "trading": "#FF9800",   # Orange
    "hacking": "#9C27B0",   # Purple
    "default": "#9E9E9E",   # Grey
}

CATEGORY_ICONS = {
    "work": "briefcase",
    "coding": "code-tags",
    "trading": "trending-up",
    "hacking": "security",
    "default": "clock",
}

IS_ANDROID = platform == "android"
if IS_ANDROID:
    try:
        from plyer import notification, tts, vibrator
        from android.permissions import request_permissions, Permission
        from jnius import autoclass
        from android import mActivity
        
        # For keeping the app running in background
        PythonService = autoclass('org.kivy.android.PythonService')
        Service = autoclass('android.app.Service')
        Intent = autoclass('android.content.Intent')
        Context = autoclass('android.content.Context')
        PendingIntent = autoclass('android.app.PendingIntent')
    except Exception as e:
        print(f"Android imports failed: {e}")
        notification, tts, vibrator = None, None, None
else:
    notification, tts, vibrator = None, None, None

# --- Updated Notebook Classes ---
class NotebookTextInput(TextInput):
    text_color = ListProperty([0, 0, 0, 1])

class DrawingPanel(Widget):
    images = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.strokes = []
        self.current_line = None
        self.line_objects = []
        self.color = (0, 0, 0)
        self.line_width = 2
        self.images = []
        self.text_input = NotebookTextInput()
        self.add_widget(self.text_input)
        self.bind(size=self._update_layout, pos=self._update_layout)
        self._update_layout()

    def _update_layout(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(1,1,1,1)
            Rectangle(pos=self.pos, size=self.size)
            # Make lines more visible: darker and dashed
            Color(0.4,0.4,0.4,0.7)
            spacing = 32
            y = self.y
            while y < self.top:
                Line(points=[self.x, y, self.right, y], width=1)
                y += spacing
        
        # Update text input size and position
        self.text_input.size = self.size
        self.text_input.pos = self.pos

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        
        # Check if touch is on text input
        if self.text_input.collide_point(*touch.pos):
            self.text_input.focus = True
            return super().on_touch_down(touch)
        
        # Otherwise, draw
        with self.canvas:
            Color(*self.color)
            self.current_line = Line(points=(touch.x, touch.y), width=self.line_width)
            self.line_objects.append(self.current_line)
        self.strokes.append([(touch.x, touch.y, self.color, self.line_width)])
        return True

    def on_touch_move(self, touch):
        if self.current_line and self.collide_point(*touch.pos):
            self.current_line.points += [touch.x, touch.y]
            self.strokes[-1].append((touch.x, touch.y, self.color, self.line_width))
            return True
        return False

    def on_touch_up(self, touch):
        self.current_line = None
        return True

    def add_image(self, path):
        # Add image with a close button overlay
        img = Image(source=path, size=(200,200), pos=(self.center_x-100, self.center_y-100))
        self.images.append(img)
        self.add_widget(img)
        # Add close button
        btn = MDIconButton(icon="close", pos=(img.x+180, img.y+180), size_hint=(None, None), size=(32,32))
        btn.bind(on_release=lambda x: self.remove_image(img, btn))
        self.add_widget(btn)

    def remove_image(self, img, btn):
        if img in self.images:
            self.images.remove(img)
        self.remove_widget(img)
        self.remove_widget(btn)

    def get_note_data(self):
        # Save strokes, images, and text
        return {
            "strokes": self.strokes,
            "images": [img.source for img in self.images],
            "text": self.text_input.text,
            "text_color": self.text_input.text_color
        }

    def load_note_data(self, data):
        # Clear existing content
        self.strokes = []
        for line in self.line_objects:
            self.canvas.remove(line)
        self.line_objects = []
        
        # Load text and color
        if "text" in data:
            self.text_input.text = data["text"]
        if "text_color" in data:
            self.text_input.text_color = data["text_color"]
        
        # Load strokes
        if "strokes" in data:
            for stroke in data["strokes"]:
                points = []
                for point in stroke:
                    x, y, color, width = point
                    points.extend([x, y])
                
                with self.canvas:
                    Color(*color)
                    line = Line(points=points, width=width)
                    self.line_objects.append(line)
                self.strokes.append(stroke)
        
        # Load images
        if "images" in data:
            for img_path in data["images"]:
                if os.path.exists(img_path):
                    self.add_image(img_path)

class NotebookRoot(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_note_date = datetime.now().strftime("%Y-%m-%d")
        self.notes_history = self.load_notes_history()

    def set_pen_color(self, r, g, b):
        if hasattr(self, 'ids') and 'drawpanel' in self.ids:
            self.ids.drawpanel.color = (r, g, b)
            # Also set text color
            self.ids.drawpanel.text_input.text_color = [r, g, b, 1]

    def set_pen_size(self, value):
        if hasattr(self, 'ids') and 'drawpanel' in self.ids:
            self.ids.drawpanel.line_width = value

    def open_image_chooser(self):
        chooser = FileChooserIconView(path=os.getcwd())
        popup = Popup(title="Choose an image", content=chooser, size_hint=(0.9, 0.9))

        def on_select(instance, selection, touch):
            if selection:
                if hasattr(self, 'ids') and 'drawpanel' in self.ids:
                    self.ids.drawpanel.add_image(selection[0])
            popup.dismiss()

        chooser.bind(on_submit=on_select)
        popup.open()

    def load_notes_history(self):
        """Load all saved notes from the notebook file"""
        notes = {}
        if os.path.exists(NOTEBOOK_FILE):
            try:
                with open(NOTEBOOK_FILE, "r") as f:
                    notes = json.load(f)
            except:
                notes = {}
        return notes

    def save_notebook(self, *args):
        # Save strokes, images, and text to notebook.json
        drawing = {}
        if hasattr(self, 'ids') and 'drawpanel' in self.ids:
            drawing = self.ids.drawpanel.get_note_data()

        data = {
            "drawing": drawing,
            "timestamp": datetime.now().isoformat()
        }
        
        # Load existing notes
        all_notes = self.load_notes_history()
        
        # Add current note with date as key
        all_notes[self.current_note_date] = data
        
        # Save all notes
        with open(NOTEBOOK_FILE, "w") as f:
            json.dump(all_notes, f, indent=4)
        
        popup = Popup(title="Saved!", content=MDLabel(text="Notebook saved.", height=dp(40)), size_hint=(0.4, 0.2))
        popup.open()

    def load_note(self, date_str):
        """Load a specific note by date"""
        self.notes_history = self.load_notes_history()
        if date_str in self.notes_history:
            data = self.notes_history[date_str]
            if hasattr(self, 'ids') and 'drawpanel' in self.ids:
                self.ids.drawpanel.load_note_data(data.get("drawing", {}))
            self.current_note_date = date_str

    def open_notes_viewer(self):
        """Open the notes viewer popup"""
        viewer = NotebookViewer()
        popup = Popup(title="Your Notes", content=viewer, size_hint=(0.9, 0.9))
        popup.open()

class NotebookViewer(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(10)
        self.padding = dp(10)
        self.load_notes()

    def load_notes(self):
        """Load all notes and display them in a scrollable list"""
        notes = {}
        if os.path.exists(NOTEBOOK_FILE):
            try:
                with open(NOTEBOOK_FILE, "r") as f:
                    notes = json.load(f)
            except Exception as e:
                print(f"Error loading notes: {e}")
                notes = {}
        
        # Clear existing widgets
        self.clear_widgets()
        
        # Add title
        title = MDLabel(
            text="Your Notes",
            halign="center",
            theme_text_color="Primary",
            size_hint_y=None,
            height=dp(40),
            font_style="H6"
        )
        self.add_widget(title)
        
        # Create scroll view for notes
        scroll = ScrollView()
        notes_layout = GridLayout(cols=1, spacing=dp(10), size_hint_y=None)
        notes_layout.bind(minimum_height=notes_layout.setter('height'))
        
        # Sort notes by date (newest first)
        sorted_dates = sorted(notes.keys(), reverse=True)
        
        if not sorted_dates:
            no_notes = MDLabel(
                text="No notes yet. Create your first note!",
                halign="center",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(100)
            )
            notes_layout.add_widget(no_notes)
        else:
            for date_str in sorted_dates:
                note_data = notes[date_str]
                # Create a card for each note
                note_card = MDCard(
                    size_hint_y=None,
                    height=dp(180),  # Increased height for buttons
                    elevation=2
                )

                # A layout inside the card to hold content
                card_box = MDBoxLayout(
                    orientation="vertical",
                    spacing=dp(5),
                    padding=dp(15)
                )

                # Add date header
                date_header = MDLabel(
                    text=date_str,
                    theme_text_color="Primary",
                    size_hint_y=None,
                    height=dp(30),
                    font_style="Subtitle1"
                )
                card_box.add_widget(date_header)
                
                # Add text preview (first 100 characters)
                drawing_data = note_data.get("drawing", {})
                note_text = drawing_data.get("text", "") if drawing_data else ""
                if note_text:
                    text_preview = MDLabel(
                        text=note_text[:100] + "..." if len(note_text) > 100 else note_text,
                        theme_text_color="Secondary",
                        size_hint_y=None,
                        height=dp(40)
                    )
                    card_box.add_widget(text_preview)
                else:
                    # Add placeholder if no text
                    text_preview = MDLabel(
                        text="[No text content]",
                        theme_text_color="Hint",
                        size_hint_y=None,
                        height=dp(40)
                    )
                    card_box.add_widget(text_preview)
                
                # Add drawing indicator
                if drawing_data and drawing_data.get("strokes"):
                    drawing_indicator = MDLabel(
                        text="✓ Contains drawing",
                        theme_text_color="Hint",
                        size_hint_y=None,
                        height=dp(20)
                    )
                    card_box.add_widget(drawing_indicator)
                
                # Add image indicator
                if drawing_data and drawing_data.get("images"):
                    image_count = len(drawing_data["images"])
                    image_indicator = MDLabel(
                        text=f"📷 {image_count} image(s)",
                        theme_text_color="Hint",
                        size_hint_y=None,
                        height=dp(20)
                    )
                    card_box.add_widget(image_indicator)
                
                # Add buttons layout
                buttons_layout = MDBoxLayout(
                    orientation="horizontal",
                    size_hint_y=None,
                    height=dp(40),
                    spacing=dp(10)
                )
                
                # Add view button
                view_btn = MDFlatButton(
                    text="View",
                    size_hint_x=0.5,
                    on_release=lambda x, ds=date_str, nd=note_data: self.view_note(ds, nd)
                )
                buttons_layout.add_widget(view_btn)
                
                # Add delete button
                delete_btn = MDFlatButton(
                    text="Delete",
                    size_hint_x=0.5,
                    on_release=lambda x, ds=date_str: self.delete_note(ds)
                )
                buttons_layout.add_widget(delete_btn)
                
                card_box.add_widget(buttons_layout)
                note_card.add_widget(card_box)
                notes_layout.add_widget(note_card)
        
        scroll.add_widget(notes_layout)
        self.add_widget(scroll)

    def delete_note(self, date_str):
        """Delete a specific note"""
        # Load current notes
        notes = {}
        if os.path.exists(NOTEBOOK_FILE):
            try:
                with open(NOTEBOOK_FILE, "r") as f:
                    notes = json.load(f)
            except:
                notes = {}
        
        # Remove the note
        if date_str in notes:
            del notes[date_str]
            
            # Save updated notes
            with open(NOTEBOOK_FILE, "w") as f:
                json.dump(notes, f, indent=4)
            
            # Reload the notes view
            self.load_notes()
            
            # Show confirmation
            popup = Popup(
                title="Deleted", 
                content=MDLabel(text=f"Note from {date_str} deleted.", height=dp(40)), 
                size_hint=(0.4, 0.2)
            )
            popup.open()

    def view_note(self, date_str, note_data):
        """Show a popup with the full note content"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(15))
        
        scroll = ScrollView()
        inner_content = BoxLayout(orientation='vertical', size_hint_y=None)
        inner_content.bind(minimum_height=inner_content.setter('height'))
        
        # Add title
        title = MDLabel(
            text=f"Note from {date_str}",
            halign="center",
            theme_text_color="Primary",
            size_hint_y=None,
            height=dp(40),
            font_style="H6"
        )
        inner_content.add_widget(title)
        
        # Add text content
        drawing_data = note_data.get("drawing", {})
        note_text = drawing_data.get("text", "") if drawing_data else ""
        
        if note_text:
            text_content = MDLabel(
                text=note_text,
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(200) if len(note_text) > 500 else dp(100),
                text_size=(None, None)
            )
            text_content.bind(texture_size=text_content.setter('size'))
            inner_content.add_widget(text_content)
        else:
            no_text = MDLabel(
                text="[No text content]",
                theme_text_color="Hint",
                size_hint_y=None,
                height=dp(40)
            )
            inner_content.add_widget(no_text)
        
        # Add drawing indicator
        if drawing_data and drawing_data.get("strokes"):
            drawing_info = MDLabel(
                text="✓ This note contains drawings",
                theme_text_color="Hint",
                size_hint_y=None,
                height=dp(30)
            )
            inner_content.add_widget(drawing_info)
        
        # Add image indicator
        if drawing_data and drawing_data.get("images"):
            image_count = len(drawing_data["images"])
            image_info = MDLabel(
                text=f"📷 Contains {image_count} image(s)",
                theme_text_color="Hint",
                size_hint_y=None,
                height=dp(30)
            )
            inner_content.add_widget(image_info)
        
        # Add timestamp
        timestamp = note_data.get("timestamp", "")
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                time_label = MDLabel(
                    text=f"Created: {dt.strftime('%Y-%m-%d %H:%M')}",
                    theme_text_color="Hint",
                    size_hint_y=None,
                    height=dp(30)
                )
                inner_content.add_widget(time_label)
            except:
                pass
        
        scroll.add_widget(inner_content)
        content.add_widget(scroll)
        
        # Add close button
        close_btn = MDFlatButton(
            text="Close",
            size_hint_y=None,
            height=dp(40)
        )
        content.add_widget(close_btn)
        
        popup = Popup(
            title="View Note",
            content=content,
            size_hint=(0.8, 0.8)
        )
        
        close_btn.bind(on_release=popup.dismiss)
        popup.open()

# Custom Widgets
class ElevatedCard(MDCard):
    pass

class TimeSlotCard(ElevatedCard):
    start_time = StringProperty()
    end_time = StringProperty()
    title = StringProperty()
    description = StringProperty()
    is_active = BooleanProperty()
    category = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(120)
        self.padding = dp(16)
        self.elevation = 2

    def on_category(self, instance, value):
        color = get_color_from_hex(CATEGORY_COLORS.get(value, CATEGORY_COLORS["default"]))
        self.md_bg_color = color
        try:
            self.line_color = color
        except Exception:
            pass

# Main App with Alarm Fixes
class TimmytimetableApp(MDApp):
    dialog = None
    current_time = StringProperty("00:00:00")
    current_date = StringProperty("Loading...")
    status_text = StringProperty("No active tasks")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tasks = []
        self.fired_today = set()
        self.sound_cache = {}
        self.reminder_intervals = {}
        self.background_service_started = False
        self.theme_mode = "Light"
        self.alarm_manager = None

    def build(self):
        print("Building main UI...")
        Builder.load_string(NOTEBOOK_KV)
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        return Builder.load_string(KV)

    def toggle_theme(self):
        if self.theme_cls.theme_style == "Light":
            self.theme_cls.theme_style = "Dark"
            try:
                self.root.ids.theme_toggle.icon = "white-balance-sunny"
            except Exception:
                pass
        else:
            self.theme_cls.theme_style = "Light"
            try:
                self.root.ids.theme_toggle.icon = "weather-night"
            except Exception:
                pass

    def on_start(self):
        self.tasks = self.load_tasks()
        self.refresh_task_cards()
        self.update_clock(0)
        Clock.schedule_interval(self.update_clock, 1)
        Clock.schedule_interval(self.check_alarms, 30)
        
        # Initialize Android alarm system
        if IS_ANDROID:
            self.setup_android_alarms()
            if not self.background_service_started:
                self.start_background_service()
                self.background_service_started = True

    def setup_android_alarms(self):
        """Setup Android alarm manager for background alarms"""
        try:
            from jnius import autoclass, cast
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Context = autoclass('android.content.Context')
            AlarmManager = autoclass('android.app.AlarmManager')
            
            context = cast('android.content.Context', PythonActivity.mActivity)
            self.alarm_manager = cast('android.app.AlarmManager', 
                                    context.getSystemService(Context.ALARM_SERVICE))
            print("Android alarm manager initialized")
        except Exception as e:
            print(f"Android alarm setup failed: {e}")

    def set_android_alarm(self, trigger_time):
        """Set an exact alarm on Android"""
        if not IS_ANDROID or not self.alarm_manager:
            return
            
        try:
            from jnius import autoclass, cast
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            PendingIntent = autoclass('android.app.PendingIntent')
            
            context = cast('android.content.Context', PythonActivity.mActivity)
            intent = Intent(context, autoclass('com.timmy.alarm.AlarmReceiver'))
            pending_intent = PendingIntent.getBroadcast(context, 0, intent, 
                                                      PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE)
            
            # Set exact alarm
            self.alarm_manager.setExact(self.alarm_manager.RTC_WAKEUP, trigger_time, pending_intent)
            print(f"Alarm set for {trigger_time}")
        except Exception as e:
            print(f"Failed to set Android alarm: {e}")

    def schedule_all_alarms(self):
        """Schedule all active tasks as Android alarms"""
        if not IS_ANDROID:
            return
            
        now = datetime.now()
        for task in self.tasks:
            if task[4]:  # if active
                start_time_str = task[0]
                try:
                    # Convert to datetime for today
                    start_time = datetime.strptime(start_time_str, "%H:%M")
                    trigger_time = now.replace(hour=start_time.hour, 
                                             minute=start_time.minute, 
                                             second=0, 
                                             microsecond=0)
                    
                    # If time already passed today, schedule for tomorrow
                    if trigger_time < now:
                        trigger_time += timedelta(days=1)
                    
                    # Convert to milliseconds
                    trigger_millis = int(trigger_time.timestamp() * 1000)
                    self.set_android_alarm(trigger_millis)
                    
                except Exception as e:
                    print(f"Error scheduling alarm: {e}")

    def start_background_service(self):
        """Start a foreground service to keep the app running in background"""
        try:
            service_intent = Intent(mActivity, PythonService)
            service_intent.putExtra("background", "true")
            mActivity.startService(service_intent)
            print("Background service started")
            
            # Schedule all alarms when service starts
            self.schedule_all_alarms()
        except Exception as e:
            print(f"Failed to start background service: {e}")

    def request_android_permissions(self):
        if IS_ANDROID:
            try:
                permissions = [Permission.VIBRATE, Permission.WAKE_LOCK]
                if hasattr(Permission, 'POST_NOTIFICATIONS'):
                    permissions.append(Permission.POST_NOTIFICATIONS)
                if hasattr(Permission, 'FOREGROUND_SERVICE'):
                    permissions.append(Permission.FOREGROUND_SERVICE)
                request_permissions(permissions)
            except Exception as e:
                print(f"Permission request failed: {e}")

    def get_data_dir(self):
        if IS_ANDROID:
            from android.storage import app_storage_path
            return app_storage_path()
        else:
            return os.getcwd()

    def load_tasks(self):
        tasks = []
        try:
            data_dir = self.get_data_dir()
            tasks_file_path = os.path.join(data_dir, TASKS_FILE)
            if os.path.exists(tasks_file_path):
                with open(tasks_file_path, "r") as f:
                    data = json.load(f)
                    for item in data:
                        if len(item) >= 6:
                            tasks.append(tuple(item[:6]))
            else:
                tasks = DEFAULT_SLOTS.copy()
                # Save default tasks to file
                with open(tasks_file_path, "w") as f:
                    json.dump(tasks, f)
        except Exception as e:
            print(f"Error loading tasks: {e}")
            tasks = DEFAULT_SLOTS.copy()
        return tasks

    def save_tasks(self):
        try:
            data_dir = self.get_data_dir()
            tasks_file_path = os.path.join(data_dir, TASKS_FILE)
            with open(tasks_file_path, "w") as f:
                json.dump(self.tasks, f)
        except Exception as e:
            print(f"Error saving tasks: {e}")

    def refresh_task_cards(self):
        if not hasattr(self, 'root') or self.root is None:
            return
        if not hasattr(self.root, 'ids') or 'tasks_container' not in self.root.ids:
            return
        container = self.root.ids.tasks_container
        container.clear_widgets()
        if not self.tasks:
            empty_label = MDLabel(
                text="No tasks scheduled\nTap '+' to add your first task",
                halign="center",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=dp(100)
            )
            container.add_widget(empty_label)
            return
        for task in self.tasks:
            card = self._create_task_card(task)
            container.add_widget(card)

    def _create_task_card(self, task):
        start, end, title, desc, active, category = task
        card = TimeSlotCard(
            start_time=start,
            end_time=end,
            title=title,
            description=desc,
            is_active=active,
            category=category
        )
        content_layout = MDBoxLayout(orientation="horizontal", spacing=dp(10))
        content_layout.add_widget(self._create_task_icon(task))
        content_layout.add_widget(self._create_task_text_layout(task))
        content_layout.add_widget(self._create_task_controls(task))
        card.add_widget(content_layout)
        return card

    def _create_task_icon(self, task):
        start, end, title, desc, active, category = task
        icon_widget = MDIconButton(
            icon=CATEGORY_ICONS.get(category, "clock"),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1) if active else (0.7, 0.7, 0.7, 1),
            disabled=not active
        )
        return icon_widget

    def _create_task_text_layout(self, task):
        start, end, title, desc, active, category = task
        text_layout = MDBoxLayout(orientation="vertical", size_hint_x=0.7)
        time_title_layout = MDBoxLayout(orientation="horizontal")
        time_title_layout.add_widget(MDLabel(
            text=f"{start} - {end}",
            size_hint_x=0.4,
            theme_text_color="Custom" if active else "Secondary",
            text_color="white" if active else (0.5, 0.5, 0.5, 1),
            height=dp(30)
        ))
        time_title_layout.add_widget(MDLabel(
            text=title,
            size_hint_x=0.6,
            theme_text_color="Custom" if active else "Secondary",
            text_color="white" if active else (0.5, 0.5, 0.5, 1),
            height=dp(30)
        ))
        text_layout.add_widget(time_title_layout)
        text_layout.add_widget(MDLabel(
            text=desc,
            theme_text_color="Custom" if active else "Secondary",
            text_color="white" if active else (0.5, 0.5, 0.5, 1),
            size_hint_y=None,
            height=dp(40)
        ))
        return text_layout

    def _create_task_controls(self, task):
        start, end, title, desc, active, category = task
        controls_layout = MDBoxLayout(
            orientation="vertical",
            size_hint_x=0.2,
            spacing=dp(10)
        )
        switch = Switch(active=active)
        switch.bind(active=lambda instance, value: self.toggle_task(task, value))
        controls_layout.add_widget(switch)
        edit_btn = MDIconButton(
            icon="pencil",
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            theme_text_color="Custom",
            text_color="white" if active else (0.7, 0.7, 0.7, 1)
        )
        edit_btn.bind(on_release=lambda x: self.open_edit_popup(task))
        controls_layout.add_widget(edit_btn)
        return controls_layout

    def open_task_dialog(self, task=None):
        """Open add-new-task popup (task None) OR edit (task provided)."""
        is_edit = task is not None
        title_text = "Edit Task" if is_edit else "Add New Task"
        button_text = "Save" if is_edit else "Add"

        # Create a more visible background
        background = BoxLayout(orientation='vertical')
        with background.canvas.before:
            Color(0.9, 0.9, 0.95, 1)  # Light blue-gray background
            Rectangle(pos=background.pos, size=background.size)
        
        # content layout
        content = MDBoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10), size_hint_y=None)
        content.height = dp(450)
        
        # Emoji helper label
        emoji_label = MDLabel(
            theme_text_color="Hint",
            size_hint_y=None,
            height=dp(25)
        )
        content.add_widget(emoji_label)
        
        # Create more visible input fields
        start_input = MDTextField(
            hint_text="Start Time", 
            size_hint_y=None, 
            height=dp(50),
            mode="fill"
        )
        end_input = MDTextField(
            hint_text="End Time", 
            size_hint_y=None, 
            height=dp(50),
            mode="fill"
        )
        title_input = MDTextField(
            hint_text="Title", 
            size_hint_y=None, 
            height=dp(50),
            mode="fill"
        )
        desc_input = MDTextField(
            hint_text="Description", 
            size_hint_y=None, 
            height=dp(50),
            mode="fill"
        )
        category_input = MDTextField(
            hint_text="Category", 
            size_hint_y=None, 
            height=dp(50),
            mode="fill"
        )

        content.add_widget(start_input)
        content.add_widget(end_input)
        content.add_widget(title_input)
        content.add_widget(desc_input)
        content.add_widget(category_input)

        # bottom buttons
        buttons = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(60), spacing=dp(10))
        cancel_btn = MDFlatButton(
            text="CANCEL",
            theme_text_color="Custom",
            text_color=(0.8, 0.2, 0.2, 1)
        )
        action_btn = MDFlatButton(
            text=button_text,
            theme_text_color="Custom", 
            text_color=(0.2, 0.6, 0.2, 1)
        )
        buttons.add_widget(cancel_btn)
        buttons.add_widget(action_btn)
        content.add_widget(buttons)

        background.add_widget(content)
        
        popup = Popup(
            title=title_text, 
            content=background, 
            size_hint=(0.9, None), 
            height=dp(550),
            background_color=(0.95, 0.95, 1, 1)  # Light blue background for popup
        )

        # populate if editing
        if is_edit:
            s, e, t, d, a, c = task
            start_input.text = s
            end_input.text = e
            title_input.text = t
            desc_input.text = d
            category_input.text = c

        def do_cancel(instance):
            popup.dismiss()

        def do_action(instance):
            s = start_input.text.strip()
            e = end_input.text.strip()
            t = title_input.text.strip()
            d = desc_input.text.strip()
            c = category_input.text.strip().lower()
            if not s or not e or not t:
                return
            new_task = (s, e, t, d, True, c)
            if is_edit:
                try:
                    idx = self.tasks.index(task)
                    # preserve previous active state if desired
                    prev_active = self.tasks[idx][4]
                    new_task_list = list(new_task)
                    new_task_list[4] = prev_active
                    self.tasks[idx] = tuple(new_task_list)
                except ValueError:
                    pass
            else:
                self.tasks.append(new_task)
            self.save_tasks()
            self.refresh_task_cards()
            popup.dismiss()

        cancel_btn.bind(on_release=do_cancel)
        action_btn.bind(on_release=do_action)
        popup.open()

    def open_edit_popup(self, task):
        self.open_task_dialog(task=task)

    def save_task_from_dialog(self, original_task=None):
        return

    def toggle_task(self, task, active):
        if not self.tasks:
            return
        try:
            index = self.tasks.index(task)
            task_list = list(self.tasks[index])
            task_list[4] = active
            self.tasks[index] = tuple(task_list)
            self.save_tasks()
            self.refresh_task_cards()
        except ValueError:
            pass

    def update_clock(self, dt):
        now = datetime.now()
        self.current_time = now.strftime("%H:%M:%S")
        self.current_date = now.strftime("%A, %B %d, %Y")

    def check_alarms(self, dt):
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        current_date_str = now.strftime("%Y-%m-%d")
        
        # Reset fired_today at midnight
        if now.hour == 0 and now.minute == 0:
            self.fired_today.clear()
            self.reminder_intervals.clear()
            
        for task in self.tasks:
            start_time_str, end_time_str, title, description, is_active, category = task
            if is_active:
                try:
                    start_time_obj = datetime.strptime(start_time_str, "%H:%M").time()
                    end_time_obj = datetime.strptime(end_time_str, "%H:%M").time()
                    current_time_obj = now.time()
                    
                    # Check if task is currently active
                    if end_time_obj <= start_time_obj:  # Overnight task
                        if current_time_obj >= start_time_obj or current_time_obj <= end_time_obj:
                            task_key = f"{current_date_str}-{start_time_str}"
                            if task_key not in self.fired_today:
                                self.trigger_alert(title, description)
                                self.fired_today.add(task_key)
                                self.status_text = f"Active: {title}"
                                self.schedule_reminders(task_key, title, description)
                    else:  # Normal task
                        if start_time_obj <= current_time_obj <= end_time_obj:
                            task_key = f"{current_date_str}-{start_time_str}"
                            if task_key not in self.fired_today:
                                self.trigger_alert(title, description)
                                self.fired_today.add(task_key)
                                self.status_text = f"Active: {title}"
                                self.schedule_reminders(task_key, title, description)
                except Exception as e:
                    print(f"Error checking alarm: {e}")

    def schedule_reminders(self, task_key, title, description):
        # Cancel any existing reminders for this task
        if task_key in self.reminder_intervals:
            Clock.unschedule(self.reminder_intervals[task_key])
        
        # Create a new reminder function
        def reminder_callback(dt):
            dnd_active = False
            if hasattr(self, 'root') and self.root is not None and hasattr(self.root, 'ids') and 'dnd_switch' in self.root.ids:
                dnd_active = self.root.ids.dnd_switch.active
            if not dnd_active:
                self.trigger_alert(f"Reminder: {title}", description)
        
        # Schedule reminders every 5 minutes
        self.reminder_intervals[task_key] = Clock.schedule_interval(reminder_callback, 300)  # 300 seconds = 5 minutes

    def trigger_alert(self, title, description):
        dnd_active = False
        if hasattr(self, 'root') and self.root is not None and hasattr(self.root, 'ids') and 'dnd_switch' in self.root.ids:
            dnd_active = self.root.ids.dnd_switch.active
        if not dnd_active:
            alert_text = f"{title}: {description}"
            if notification:
                try:
                    notification.notify(
                        title=title,
                        message=description,
                        ticker=alert_text,
                        toast=True
                    )
                except Exception as e:
                    print(f"Notification error: {e}")
            if vibrator:
                try:
                    vibrator.vibrate(2)
                except Exception as e:
                    print(f"Vibration error: {e}")
            if tts:
                try:
                    tts.speak(alert_text)
                except Exception as e:
                    print(f"TTS error: {e}")
                    
    def test_alert(self):
        self.trigger_alert("Test Alarm", "This is a test notification and voice alert.")

    def open_menu(self):
        pass

    def on_pause(self):
        """Android-specific: called when app is paused"""
        return True

    def on_resume(self):
        """Android-specific: called when app resumes from background"""
        pass

    def open_notebook(self, *args):
        # Build a tabbed notebook UI using TabbedPanel and Popup
        notebook_tabs = TabbedPanel(do_default_tab=False)

        new_note_tab = TabbedPanelItem(text="New Note")
        new_note_content = NotebookRoot()
        new_note_tab.add_widget(new_note_content)
        notebook_tabs.add_widget(new_note_tab)

        view_notes_tab = TabbedPanelItem(text="View Notes")
        viewer = NotebookViewer()
        view_notes_tab.add_widget(viewer)
        notebook_tabs.add_widget(view_notes_tab)

        popup = Popup(
            title="Notebook", 
            content=notebook_tabs, 
            size_hint=(0.95, 0.95)
        )
        popup.open()

if __name__ == '__main__':
    TimmytimetableApp().run()