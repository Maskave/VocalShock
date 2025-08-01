# -------------------------- --------------------------
#                        IMPORTS 
# -------------------------- --------------------------
import os, re, json, threading, asyncio, random, time, sys
import tkinter as tk
import sounddevice as sd
import speech_recognition as sr
import aiohttp

import customtkinter as ctk
from tkinter import messagebox


# -------------------------- --------------------------
#                        APP SETUP
# -------------------------- --------------------------
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
app = ctk.CTk()
app.title("VocalShock V1.3")
app.geometry("700x550")
# settings area
settings_frame = ctk.CTkFrame(app, fg_color="#2E2E2E", border_color="gray", border_width=2)
settings_frame.place_forget()

# scrollable settings page
canvas = tk.Canvas(settings_frame, highlightthickness=0, bg=settings_frame._fg_color)
v_scroll = ctk.CTkScrollbar(settings_frame, orientation="vertical", command=canvas.yview)
inner = ctk.CTkFrame(canvas, fg_color=settings_frame._fg_color)
for col, w in ((0,0),(1,1),(2,0),(3,1)):
    inner.columnconfigure(col, weight=w)

canvas.configure(yscrollcommand=v_scroll.set)
canvas.create_window((0,0), window=inner, anchor="nw")
inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

for w in (canvas, v_scroll):
    w.place(relx=0 if w is canvas else 0.95, rely=0, relwidth=0.95 if w is canvas else 0.05, relheight=1.0)

inner.columnconfigure(0, weight=0)
inner.columnconfigure(1, weight=0)
inner.columnconfigure(2, weight=0)
inner.columnconfigure(3, weight=0)
inner.columnconfigure(4, weight=0)

def on_resize(event):
    home_frame.update_idletasks()
    home_frame.rowconfigure(0, weight=1)
    home_frame.columnconfigure(0, weight=1)
    home_text_frame.grid(row=0, column=0, sticky="nsew")

app.bind("<Configure>", on_resize)

# -------------------------- --------------------------
#                       HOME PAGE
# -------------------------- --------------------------
home_frame = ctk.CTkFrame(app, fg_color="#000000")
home_frame.place_forget()
home_frame.rowconfigure(0, weight=1)
home_frame.columnconfigure(0, weight=1)

# Text widget inside scrollable canvas
home_text_frame = tk.Frame(home_frame, background="#000000", bd=2, relief="solid")
home_text_frame.grid(row=0, column=0, sticky="nsew")
home_text_frame.rowconfigure(0, weight=1)
home_text_frame.columnconfigure(0, weight=1)

# Scroll bar
scrollbar = tk.Scrollbar(home_text_frame); scrollbar.grid(row=0, column=1, sticky="ns")

text_widget = tk.Text(home_text_frame, wrap="word", state="normal",
    bg="#000000", fg="#FFFFFF", yscrollcommand=scrollbar.set, bd=0,
    font=("Segoe UI Emoji", 14), insertbackground="white"
)
text_widget.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
scrollbar.config(command=text_widget.yview)

# -------------------------- --------------------------
#                  BUTTONS AND FUNCTIONS
# -------------------------- --------------------------

current_page = None  # global
app.grid_rowconfigure((0, 1), weight=1)
app.grid_columnconfigure((0, 1), weight=1)
def on_settings_button_click():
    global current_page
    if current_page == "settings": return
    current_page = "settings"
    home_frame.place_forget()
    settings_frame.place(relx=0.5, y=60, anchor="n", relwidth=0.95, relheight=0.75)
    settings_button.configure(fg_color="#9932CC")
    settings_button.lift()
    home_button.configure(fg_color="#800080")

def on_home_button_click():
    global current_page
    if current_page == "home": return
    current_page = "home"
    settings_frame.place_forget()
    home_frame.place(relx=0.5, y=60, anchor="n", relwidth=0.95, relheight=0.75)
    home_button.configure(fg_color="#9932CC")
    home_frame.lift()
    settings_button.configure(fg_color="#800080")

is_paused = False
def toggle_pause():
    global is_paused
    is_paused = not is_paused

    if is_paused:
        # when paused: turn green and change text
        pause_button.configure(
            text="▶️ Resume",
            fg_color="#006400",       # dark green
            hover_color="#008000"     # slightly brighter green on hover
        )
        home_box_add("⏸️ Paused: No shocks will be sent.")
    else:
        # when resumed: turn red and change text
        pause_button.configure(
            text="⏸️ PAUSE",
            fg_color="#B31D02",       # original red
            hover_color="red"
        )
        home_box_add("✅ Resumed: Listening for trigger words.")

home_button = ctk.CTkButton(
    app,
    text="🏠 Home",
    width=40, height=40,
    corner_radius=20,
    fg_color="#800080",
    hover_color="#9932CC",
    command=on_home_button_click
)
home_button.grid(row=0, column=0, sticky="nw", padx=15, pady=15)
# ── SETTINGS BUTTON ────────────────────────────────────────────────────────
settings_button = ctk.CTkButton(
    app,
    text="⚙️ Settings",
    width=40, height=40,
    corner_radius=20,
    fg_color="#800080",
    hover_color="#9932CC",
    command=on_settings_button_click
)
settings_button.grid(row=0, column=1, sticky="ne", padx=15, pady=15)

pause_button = ctk.CTkButton(
    app,
    text="⏸️ Pause",  
    fg_color="#B31D02",
    hover_color="red",
    command=toggle_pause,
    corner_radius=10,
    width=120,
    height=40
)
pause_button.grid(row=1, column=1, sticky="se", padx=15, pady=15)

# Tag styles
for tag, cfg in {
    "speech":{"foreground":"#00BFFF"},
    "match": {"foreground":"#00FF00"},
    "shock": {"foreground":"#FFD700"},
    "detected":{"foreground":"#FF4500"},
    "listening":{"foreground":"#e1b2a7"},
}.items():
    text_widget.tag_config(tag, **cfg)


# -------------------------- --------------------------
#               TEXT BOXES FORMATTING
# -------------------------- --------------------------

def home_box_add(text):
    text_widget.configure(state="normal")
    if "🗣 You said:" in text:
        text_widget.insert("end", text + "\n", "speech")
    elif "MATCH!" in text:
        text_widget.insert("end", text + "\n", "match")
    elif "⚡ Shock" in text:
        text_widget.insert("end", text + "\n", "shock")
    elif "🚨 Trigger word Detected:" in text:
        text_widget.insert("end", text + "\n", "detected")
    elif "⏳ Waiting for speech…" in text or "⌛ Waiting for speech…" in text:
        text_widget.insert("end", text + "\n", "listening")
    else:
        text_widget.insert("end", text + "\n")
    text_widget.see("end")
    text_widget.configure(state="disabled")


# -------------------------- --------------------------
#                 VALIDATION FUNCTIONS
# -------------------------- --------------------------
# first one is a little special 'lil fucker
def validate_api(v):
    if v == "":
        return True
    if v == "X00X00X0-X00X-X00X-X00X-X00X00X00X00":
        return True
    match = re.fullmatch(r"[A-Za-z0-9\-]*", v)
    return len(v) <= 36 and match is not None

def validate_username(v): return v == "" or  (len(v) <= 99 and v.isalnum())
def validate_code    (v): return v == "" or  (len(v) <= 11 and v.isalnum())
def validate_strength(v): return v == "" or v == "1-100" or (v.isdigit() and 0 <= int(v) <= 100)
def validate_duration(v): return v == "" or v == "1-15" or (v.isdigit() and 0 <= int(v) <= 15)

# Register them with Tk
vcmd_username   = app.register(validate_username)
vcmd_api        = app.register(validate_api)
vcmd_code       = app.register(validate_code)
vcmd_strength   = app.register(validate_strength)
vcmd_duration   = app.register(validate_duration)


# -------------------------- --------------------------
#               TEXT BOXES AND THEIR INPUTS
# -------------------------- --------------------------

def add_row(row, column, label_text, entry_kwargs):
    ctk.CTkLabel(inner, text=label_text).grid(
        row=row, column=column,
        sticky="w", padx=10, pady=5
    )
    entry = ctk.CTkEntry(inner, **entry_kwargs)
    entry.grid(row=row, column=1,
            sticky="w", padx=10, pady=5)
    return entry

username_entry = add_row(0, 0, "Username:", {"placeholder_text":
"Username", "width":300, "height":40})
username_entry.configure(
validate="key",validatecommand=(vcmd_username, "%P"))


api_entry = add_row(1, 0, "API Key:",{"placeholder_text": 
"X00X00X0-X00X-X00X-X00X-X00X00X00X00", "width":300, "height":40})
api_entry.configure(validate="key", validatecommand=(vcmd_api, "%P"))

code_entry = add_row(2, 0, "Device Code:",{"placeholder_text": 
"00X00XX0X0X", "width":300, "height":40})
code_entry.configure(
validate="key",validatecommand=(vcmd_code, "%P"))
min_strength_entry = add_row(3, 0, "Min Shock Strength (1–100):",
{"placeholder_text": "1-100", "width":75, "height":40})
min_strength_entry.configure(
validate="key",validatecommand=(vcmd_strength, "%P"))

max_strength_label = ctk.CTkLabel(inner, text="Max Shock Strength (1–100):")
max_strength_entry = ctk.CTkEntry(inner, placeholder_text="1", width=75, 
height=40, validate="key", validatecommand=(vcmd_strength, "%P"))

max_strength_label.grid(row=3, column=1, sticky="w", padx=100, pady=5)
max_strength_entry.grid(row=3, column=1, sticky="w", padx=275, pady=5)

min_duration_entry = add_row(4, 0, "Min Shock Duration (1–15):",
{"placeholder_text": "1-15", "width":75, "height":40})
min_duration_entry.configure(
validate="key",validatecommand=(vcmd_duration, "%P"))

max_duration_label = ctk.CTkLabel(inner, text="Max Shock Duration (1–15):")
max_duration_entry = ctk.CTkEntry(inner, placeholder_text="1", width=75,
height=40, validate="key", validatecommand=(vcmd_duration, "%P"))

max_duration_label.grid(row=4, column=1, sticky="w", padx=100, pady=5)
max_duration_entry.grid(row=4, column=1, sticky="w", padx=275, pady=5)



for w in (max_strength_label, max_strength_entry, 
        max_duration_label, max_duration_entry): w.grid_remove()

def on_random_toggle():
    if random_switch.get():
        # show both max boxes, resize max boxes to half width
        max_strength_label.grid()
        max_strength_entry.grid()
        max_duration_label.grid()
        max_duration_entry.grid()


    else:
        # hide the max boxes, restore max boxes full‑width
        for w in (max_strength_label, max_strength_entry, max_duration_label, max_duration_entry):
            w.grid_remove()



random_switch = ctk.CTkSwitch(inner, text="Random Mode", command=on_random_toggle)
random_switch.grid(row=5, column=0, columnspan=2, pady=(5,15), sticky="w")

# -------------------------- --------------------------
#                        DROPDOWNS
# -------------------------- -------------------------- 

# MICRPHONE DROPDOWN ---------------------------
def list_active_mics():
    active = []
    seen_names = set()

    for idx, dev in enumerate(sd.query_devices()):
        name = dev['name']
        # 1) must have at least one input channel
        if dev['max_input_channels'] < 1:
            continue
        # 2) skip duplicates
        if name in seen_names:
            continue

        # 3) try opening a tiny, immediate-close stream to test “liveness”
        try:
            with sd.InputStream(device=idx, channels=1, samplerate=int(dev['default_samplerate'])):
                pass
        except Exception:
            # device can't actually open now (e.g. unplugged, exclusive-mode)
            continue

        # if we get here, it's a good one
        seen_names.add(name)
        active.append(name)

    return active

ctk.CTkLabel(inner, text="Detected Microphones:")\
    .grid(row=6, column=0, sticky="w", padx=10, pady=5)
    
mic_list = list_active_mics()

mic_dropdown = ctk.CTkComboBox(
    inner,
    values=mic_list,
    width=200,
    state="readonly",
    command=lambda _: threading.Thread(target=restart_listener, daemon=True).start()
)

mic_dropdown.grid(row=6, column=1, sticky="w", padx=10, pady=5)

# TRIGGER TXT FILES DROPDOWN ---------------------------

def load_trigger_words():
    path = os.path.join(wordlist_dropdown, trigger_dropdown.get())
    words = set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip().lower()
                if w:
                    words.add(w)
    except Exception as e:
        print(f"⚠️ Error loading {path}: {e}")
    print("✅ Loaded triggers:", words)
    return words

def load_and_assign_triggers():
    global trigger_words
    trigger_words = load_trigger_words()

def select_trigger_file(filename):
    # set the dropdown *and* reload the words
    trigger_dropdown.set(filename)
    load_and_assign_triggers()

# Trigger Dropdown ---------------------------
def on_trigger_change(selection):
    """Called whenever the user picks a new file in the dropdown."""
    global trigger_words
    trigger_words = load_trigger_words()
    home_box_add(f"✅ Triggers reloaded from {selection}")
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(__file__)

wordlist_dropdown = os.path.join(base_dir, "WordList")
trigger_files = []
try:
    trigger_files = [f for f in os.listdir(wordlist_dropdown) if f.lower().endswith(".txt")]
except FileNotFoundError:
    pass
    
ctk.CTkLabel(inner, text="Trigger‑word File:")\
    .grid(row=7, column=0, sticky="w", padx=10, pady=5)

if not trigger_files:
    trigger_dropdown = ctk.CTkComboBox(inner,
        values=["No .txt found"],
        state="disabled",
        width=200
    )
else:
    trigger_dropdown = ctk.CTkComboBox(inner,
        values=trigger_files,
        state="readonly",
        width=200,
        command=on_trigger_change
    )
    trigger_dropdown.set(trigger_files[0])
trigger_dropdown.grid(row=7, column=1, sticky="w", padx=10, pady=5)


load_and_assign_triggers()

trigger_words = load_trigger_words()

# -------------------------- --------------------------
#                   # SAVE AND LOAD
# -------------------------- --------------------------

# Save button
save_button = ctk.CTkButton(inner, text="Save Settings", fg_color="#006400", command=lambda: save_settings())
save_button.grid(row=8, column=0, columnspan=1, pady=(10,20), padx=10, sticky="ew")

# Save settings
def save_settings():
    # 0) Build your recognizer
    r = sr.Recognizer()
    r.dynamic_energy_threshold = False

    # 1) Figure out which mic is selected
    mic_name = mic_dropdown.get()
    devs     = sd.query_devices()
    idx      = next((i for i,d in enumerate(devs) if d["name"] == mic_name), None)
    mic_idx  = idx if idx is not None else sd.default.device[0]

    # 2) Calibrate ambient noise *right now*
    try:
        with sr.Microphone(device_index=mic_idx) as source:
            r.adjust_for_ambient_noise(source, duration=1.5)
        level = r.energy_threshold
        print(f"[MIC] Calibrated ambient noise level: {level:.2f}")
        
        # 3) If it’s too high, show a warning
        if level > 350:
            home_box_add(f"⚠️ Detected ambient noise level {int(level)}\n"
                "This may cause missed speech or false triggers."
            )
    except Exception as e:
        print(f"[MIC] Could not calibrate mic: {e}")
        home_box_add(f"Mic Calibration Failed. Could not test your mic:\n{e}")
    threading.Thread(target=restart_listener, daemon=True).start()
    data = {
        "username":         username_entry.get(),
        "api_key":          api_entry.get(),
        "share_code":       code_entry.get(),
        "min_strength":     min_strength_entry.get(),
        "max_strength":     max_strength_entry.get(),
        "min_duration":     min_duration_entry.get(),
        "max_duration":     max_duration_entry.get(),
        "random_mode":      random_switch.get(),
        "dropdown_choice":  mic_dropdown.get(),
        "trigger_file":     trigger_dropdown.get()
    }
    print("🔍 saving settings:", data)    # ← add this line
    try:
        with open("settings.json", "w") as f: json.dump(data, f, indent=2)
        home_box_add("✅ Settings successfully saved.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save settings:\n{e}")
# Load Settings

def load_settings():
    try:
        data = json.load(open("settings.json","r"))
        for ent, key in [
            (username_entry,"username"),
            (code_entry,    "share_code"),
            (api_entry,     "api_key"),
            (min_strength_entry,"min_strength"),
            (max_strength_entry,"max_strength"),
            (min_duration_entry,"min_duration"),
            (max_duration_entry,"max_duration")
            ]:
            val = data.get(key,"")
            print(f"Loading {key!r} → {val!r} into {ent!r}")
            ent.delete(0,"end")
            if val:
                print(f"Inserting {val!r} into {key}")
                ent.insert(0, val)
        if data.get("random_mode"): random_switch.select()
        else:   random_switch.deselect()
        on_random_toggle()
        print(f"Skipping insert for {key} because value is empty")
        mic_dropdown.set(data.get("dropdown_choice",""))
        select_trigger_file(data.get("trigger_file",""))
    except FileNotFoundError: pass


# -------------------------- --------------------------
#                      SHOCK PROCESS
# -------------------------- --------------------------

async def _async_send_shock(trigger_word: str):
    min_int = int(min_strength_entry.get() or "1")
    min_dur = int(min_duration_entry.get()  or "1")

    if random_switch.get():
        # use max…max ranges
        max_int = int(max_strength_entry.get() or "100")
        max_dur = int(max_duration_entry.get()  or "15")
        intensity = random.randint(min_int, max_int)
        duration  = random.randint(min_dur, max_dur)
    else:
        intensity, duration = max_int, max_dur

    username    = username_entry.get().strip()
    api_key     = api_entry.get().strip()
    device_code = code_entry.get().strip()
    max_int     = int(max_strength_entry.get() or "100")
    max_dur     = int(max_duration_entry.get()  or "15")
    if random_switch.get():
        intensity = random.randint(min_int, max_int)
        duration  = random.randint(min_dur, max_dur)
    else:
        intensity, duration = max_int, max_dur

        print(f"⚡ Shock sent! Watch your language! ⚡ Intensity: {intensity}, Duration: {duration}")
    app.after(0, lambda i=intensity, d=duration: home_box_add(
        f"⚡ Shock sent! Watch your language! ⚡\nIntensity: {i}, Duration: {d}"
    ))
    payload = {"Username":  username,"Apikey":api_key,"Op":"0",
    "Intensity": intensity,"Duration": duration,"Code": device_code}

    try:
        async with aiohttp.ClientSession() as session:
            resp = await session.post("https://do.pishock.com/api/apioperate", json=payload)
            if resp.status != 200:
                detail = await resp.text()
                home_box_add(f"❌ Shock failed ({resp.status}): {detail}, error")
    except Exception as e:
        home_box_add(f"❌ Error sending shock: {e}, error")

def send_shock(word:str):
    global is_paused
    if is_paused:
        home_box_add("⚠️ Shock blocked: System is paused")
        return
    
    threading.Thread(target=lambda: asyncio.run(_async_send_shock(word)
),daemon=True).start()
    
# -------------------------- --------------------------
#        LISTENING, PRINTING, MIC ADJUSTMENT
# -------------------------- --------------------------
stop_listening = None
def schedule_listening_indicator():
    # push into the GUI thread
    app.after(0, lambda: home_box_add("⏳ Waiting for speech…"))
    # schedule again in 3 s
    app.after(8000, schedule_listening_indicator)

def recognition_callback(recognizer, audio):
    try:
        text = recognizer.recognize_google(audio).lower()
    except sr.UnknownValueError:
        return
    except sr.RequestError as e:
        print("⚠️ API error in background listener:", e)
        return

    app.after(0, lambda t=text: home_box_add(f"🗣 You said: {t}"))
    for w in trigger_words:
        if re.search(rf"\b{re.escape(w)}\b", text):
            app.after(0, lambda w=w: home_box_add(f"🚨 Trigger word Detected: {w} !"))
            send_shock(w)
            break

def restart_listener():
    global stop_listening, trigger_words
    if stop_listening:
        try:
            stop_listening(wait_for_stop=False)
        except Exception:
            pass
    stop_listening = None

    # 1) Recognizer setup
    r = sr.Recognizer()
    r.dynamic_energy_threshold = False
    r.pause_threshold          = 0.8 # ammount of silence before done talking
    r.phrase_threshold         = 0.2 # how long speech is to count
    r.energy_threshold         = 500

    # 2) Pick your mic index
    mic_name = mic_dropdown.get()
    devs     = sd.query_devices()
    idx      = next((i for i,d in enumerate(devs) if d["name"] == mic_name), None)
    mic_idx  = idx if idx is not None else sd.default.device[0]

    # 4) Instantiate the Mic *once*
    mic = sr.Microphone(device_index=mic_idx)
    with mic as source:
        r.adjust_for_ambient_noise(source, duration=1.0)
        ret = r.energy_threshold
        print(f"[MIC] Calibrated ambient noise level: {ret:.2f}")
        app.after(0, lambda: home_box_add(f"[MIC] Calibrated ambient noise level: {ret:.2f}"))

        if ret > 350:
            home_box_add(
                f"⚠️ Detected ambient noise level {int(ret)}\n"
                "This may cause missed speech or false triggers."
            )

    trigger_words = load_trigger_words()

    # 6) Start the background listener on the mic object
    stop_listening = r.listen_in_background(
        mic,
        recognition_callback,
        phrase_time_limit=3
    )

schedule_listening_indicator()


# ──  START GUI LOOP ────────────────────────────────────────────────────────

load_settings()
on_home_button_click()
save_settings()
app.mainloop()