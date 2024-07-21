import os
import random
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pygame import mixer
import sys
from pynput import keyboard
import time

SETTINGS_FILE = "settings.json"

class AudioPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Radio Player v0.2 by Cheryl Green")
        self.root.geometry("800x300")  # Adjusted resolution
        self.root.configure(bg="black")

        # Initialize attributes before loading settings
        self.num_stations = 4  # Default number of stations
        self.volumes = [0.5] * self.num_stations  # Default volume level for each station
        self.key_bindings = {
            "prev_station": "Left",
            "next_station": "Right",
            "volume_up": "Up",
            "volume_down": "Down",
            "off": "o"
        }
        self.stations = []  # Initialize empty stations list

        self.load_settings()  # Load settings which might set the stations list

        # Initialize station details with default values if not set by settings
        if not self.stations:
            self.stations = [{"name": f"Custom Station {i+1}", "songs_folder": "", "voice_lines_folder": ""} for i in range(self.num_stations)]
        
        self.current_station = 0  # Index of the currently selected station (0 for "Off")
        self.playlists = [[] for _ in range(self.num_stations)]  # List of playlists for each station
        self.current_indices = [0] * self.num_stations  # List of current indices for each station
        self.positions = [0] * self.num_stations  # List of current positions for each station
        self.is_playing = [False] * self.num_stations  # Play/pause state for each station

        # Set up pygame mixer
        try:
            mixer.init()
            self.channels = [mixer.Channel(i) for i in range(self.num_stations)]  # Channels for each station
        except Exception as e:
            messagebox.showerror("Error", f"Error initializing mixer: {e}")

        # Ensure 'off' key binding is present
        if 'off' not in self.key_bindings:
            self.key_bindings['off'] = 'o'

        # Set up the GUI elements
        self.create_widgets()

        # Bind keys for switching stations and controlling volume
        self.bind_keys()

        # Register global hotkeys
        self.register_global_hotkeys()

        # Play all stations simultaneously
        self.play_all_stations()

        # Mute all stations except the first one
        self.update_station_playback()

        # Save settings on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # Create main frame with rounded corners
        self.main_frame = tk.Frame(self.root, bg="black", bd=2, relief="solid")
        self.main_frame.pack(expand=1, fill="both", padx=10, pady=10)

        # Display Clock
        self.clock_label = tk.Label(self.main_frame, text="", fg="white", bg="black", font=("Courier New", 24))
        self.clock_label.pack(pady=5)
        self.update_clock()

        # Display Current Station
        self.current_station_label = tk.Label(self.main_frame, text="Current Station: 89.7 MHz", fg="white", bg="black", font=("Courier New", 14))
        self.current_station_label.pack(pady=5)

        # Create station preset buttons
        self.preset_frame = tk.Frame(self.main_frame, bg="black")
        self.preset_frame.pack(pady=5)
        
        self.preset_buttons = []
        for i in range(self.num_stations):
            preset_button = tk.Button(self.preset_frame, text=f"{self.stations[i]['name']}\nEmpty", fg="white", bg="dark grey", width=20, height=3, command=lambda idx=i: self.set_preset_station(idx))
            preset_button.grid(row=0, column=i, padx=10)
            self.preset_buttons.append(preset_button)

        # Create tabs for stations and settings using ttk.Notebook
        self.tab_control = ttk.Notebook(self.main_frame, style="TNotebook")
        self.tab_control.pack(expand=1, fill="both")

        self.station_tabs = []
        self.current_song_labels = []

        # Add "Off" tab
        off_tab = ttk.Frame(self.tab_control, style="TFrame")
        self.tab_control.add(off_tab, text="Off")
        self.station_tabs.append(off_tab)

        for i in range(self.num_stations):
            tab = ttk.Frame(self.tab_control, style="TFrame")
            self.tab_control.add(tab, text=self.stations[i]["name"])
            self.station_tabs.append(tab)
            label_frame = tk.Frame(tab, bg="black")
            label_frame.pack(pady=10)
            self.current_song_labels.append(tk.Label(label_frame, text="Current Song: ", fg="white", bg="black", font=("Courier New", 14)))
            self.current_song_labels[-1].pack()

        # Add a settings tab
        self.settings_tab = ttk.Frame(self.tab_control, style="TFrame")
        self.tab_control.add(self.settings_tab, text="Settings")

        # Bind the tab change event to switch stations
        self.tab_control.bind("<<NotebookTabChanged>>", self.on_tab_change)

        # Create widgets for the settings tab
        self.create_settings_widgets()

        # Style for the notebook tabs
        style = ttk.Style()
        style.configure("TNotebook", background="black", foreground="white", padding=5, borderwidth=0)
        style.configure("TNotebook.Tab", background="grey", foreground="white", padding=10, borderwidth=1)
        style.map("TNotebook.Tab", background=[("selected", "dark grey")], foreground=[("selected", "white")])

    def update_clock(self):
        current_time = time.strftime("%H:%M:%S")
        self.clock_label.config(text=current_time)
        self.root.after(1000, self.update_clock)

    def set_preset_station(self, idx):
        # Switch to the selected preset station
        self.current_station = idx + 1  # +1 to account for "Off" tab
        self.update_station_playback()
        self.current_station_label.config(text=f"Current Station: {self.stations[idx]['name']}")

    def no_action(self):
        # Placeholder for buttons with no action assigned
        pass

    def create_settings_widgets(self):
        self.settings_frame = tk.Frame(self.settings_tab, bg="black")
        self.settings_frame.pack(pady=10)

        self.path_entries = []  # List to store folder path entries
        self.browse_buttons = []  # List to store browse buttons

        for i in range(self.num_stations):
            frame = tk.Frame(self.settings_frame, bg="black")
            frame.pack(pady=10)

            # Create entry and browse button for songs folder
            label = tk.Label(frame, text=f"{self.stations[i]['name']} - Songs Folder:", fg="white", bg="black", font=("Helvetica", 10))
            label.grid(row=0, column=0, padx=5)
            entry = tk.Entry(frame, width=50)
            entry.grid(row=0, column=1, padx=5)
            button = tk.Button(frame, text="Browse", command=lambda idx=i: self.browse_folder(idx, 'songs'), bg="dark grey", fg="white")
            button.grid(row=0, column=2, padx=5)
            self.path_entries.append(entry)
            self.browse_buttons.append(button)

            # Create entry and browse button for voice lines folder
            label = tk.Label(frame, text=f"{self.stations[i]['name']} - Voice Lines Folder:", fg="white", bg="black", font=("Helvetica", 10))
            label.grid(row=1, column=0, padx=5)
            entry = tk.Entry(frame, width=50)
            entry.grid(row=1, column=1, padx=5)
            button = tk.Button(frame, text="Browse", command=lambda idx=i: self.browse_folder(idx, 'voice_lines'), bg="dark grey", fg="white")
            button.grid(row=1, column=2, padx=5)
            self.path_entries.append(entry)
            self.browse_buttons.append(button)

        self.rename_station_buttons = []
        for i in range(self.num_stations):
            frame = tk.Frame(self.settings_frame, bg="black")
            frame.pack(pady=10)
            label = tk.Label(frame, text=f"Rename {self.stations[i]['name']}:", fg="white", bg="black", font=("Helvetica", 10))
            label.grid(row=0, column=0, padx=5)
            entry = tk.Entry(frame, width=30)
            entry.grid(row=0, column=1, padx=5)
            button = tk.Button(frame, text="Rename", command=lambda idx=i, ent=entry: self.rename_station(idx, ent.get()), bg="dark grey", fg="white")
            button.grid(row=0, column=2, padx=5)
            self.rename_station_buttons.append(button)

        # Key bindings for switching stations and controlling volume
        self.create_key_binding_widgets()

        # Add Save Settings button
        save_button = tk.Button(self.settings_frame, text="Save Settings", command=self.save_settings, bg="dark grey", fg="white")
        save_button.pack(pady=20)

        # Add Restart Application button
        restart_button = tk.Button(self.settings_frame, text="Restart Application", command=self.restart_app, bg="dark grey", fg="white")
        restart_button.pack(pady=20)

        self.update_entries()

    def create_key_binding_widgets(self):
        key_bindings_frame = tk.Frame(self.settings_frame, bg="black")
        key_bindings_frame.pack(pady=10)

        # Previous station key
        tk.Label(key_bindings_frame, text="Previous Station Key:", fg="white", bg="black", font=("Helvetica", 10)).grid(row=0, column=0, padx=5, pady=5)
        self.prev_station_entry = tk.Entry(key_bindings_frame, width=10)
        self.prev_station_entry.grid(row=0, column=1, padx=5, pady=5)
        self.prev_station_entry.insert(0, self.key_bindings["prev_station"])

        # Next station key
        tk.Label(key_bindings_frame, text="Next Station Key:", fg="white", bg="black", font=("Helvetica", 10)).grid(row=1, column=0, padx=5, pady=5)
        self.next_station_entry = tk.Entry(key_bindings_frame, width=10)
        self.next_station_entry.grid(row=1, column=1, padx=5, pady=5)
        self.next_station_entry.insert(0, self.key_bindings["next_station"])

        # Volume up key
        tk.Label(key_bindings_frame, text="Volume Up Key:", fg="white", bg="black", font=("Helvetica", 10)).grid(row=2, column=0, padx=5, pady=5)
        self.volume_up_entry = tk.Entry(key_bindings_frame, width=10)
        self.volume_up_entry.grid(row=2, column=1, padx=5, pady=5)
        self.volume_up_entry.insert(0, self.key_bindings["volume_up"])

        # Volume down key
        tk.Label(key_bindings_frame, text="Volume Down Key:", fg="white", bg="black", font=("Helvetica", 10)).grid(row=3, column=0, padx=5, pady=5)
        self.volume_down_entry = tk.Entry(key_bindings_frame, width=10)
        self.volume_down_entry.grid(row=3, column=1, padx=5, pady=5)
        self.volume_down_entry.insert(0, self.key_bindings["volume_down"])

        # Off key
        tk.Label(key_bindings_frame, text="Off Key:", fg="white", bg="black", font=("Helvetica", 10)).grid(row=4, column=0, padx=5, pady=5)
        self.off_entry = tk.Entry(key_bindings_frame, width=10)
        self.off_entry.grid(row=4, column=1, padx=5, pady=5)
        self.off_entry.insert(0, self.key_bindings.get("off", "o"))  # Use default 'o' if not in settings

        # Button to save key bindings
        tk.Button(key_bindings_frame, text="Save Key Bindings", command=self.save_key_bindings, bg="dark grey", fg="white").grid(row=5, columnspan=2, pady=10)

    def browse_folder(self, station_index, folder_type):
        # Open a file dialog to select a folder and update the corresponding entry
        folder = filedialog.askdirectory()
        if folder:
            if folder_type == 'songs':
                self.stations[station_index]['songs_folder'] = folder
            elif folder_type == 'voice_lines':
                self.stations[station_index]['voice_lines_folder'] = folder
            self.update_entries()
    
    def update_entries(self):
        # Update the folder path entries with the selected paths
        for i in range(self.num_stations):
            self.path_entries[i*2].delete(0, tk.END)
            self.path_entries[i*2].insert(0, self.stations[i]['songs_folder'])
            self.path_entries[i*2+1].delete(0, tk.END)
            self.path_entries[i*2+1].insert(0, self.stations[i]['voice_lines_folder'])
            self.preset_buttons[i].config(text=self.stations[i]['name'])

    def rename_station(self, station_index, new_name):
        # Rename the station tab and update the station name
        self.stations[station_index]['name'] = new_name
        self.preset_buttons[station_index].config(text=new_name)
        self.tab_control.tab(station_index + 1, text=new_name)  # +1 to account for "Off" tab

    def calculate_voice_line_probability(self, song_index):
        # Calculate the probability of inserting a voice line based on the song index
        return min(0.1 * (song_index + 1), 1.0)

    def shuffle_and_create_playlist(self, station_index):
        # Create and shuffle the playlist for the specified station
        station = self.stations[station_index]
        songs_files = self.get_mp3_files(station['songs_folder'])
        voice_lines_files = self.get_mp3_files(station['voice_lines_folder'])

        random.shuffle(songs_files)
        random.shuffle(voice_lines_files)

        playlist = []
        voice_lines_used = 0

        for i, song in enumerate(songs_files):
            playlist.append(song)
            if voice_lines_files and random.random() < self.calculate_voice_line_probability(i - voice_lines_used):
                playlist.append(voice_lines_files.pop(0))
                voice_lines_used += 1

        if voice_lines_files:
            playlist.extend(voice_lines_files)

        self.playlists[station_index] = playlist
        self.current_indices[station_index] = 0

    def get_mp3_files(self, folder):
        # Return a list of MP3 files in the specified folder
        try:
            if not folder or not os.path.isdir(folder):
                return []
            return [os.path.join(folder, file) for file in os.listdir(folder) if file.endswith(".mp3")]
        except Exception as e:
            messagebox.showerror("Error", f"Error reading folder '{folder}': {e}")
            return []

    def play_audio(self, station_index):
        # Play the audio for the given station
        try:
            if self.current_indices[station_index] < len(self.playlists[station_index]):
                current_track = self.playlists[station_index][self.current_indices[station_index]]
                sound = mixer.Sound(current_track)
                self.channels[station_index].play(sound)
                self.is_playing[station_index] = True
                self.update_current_song_label(station_index)
                self.root.after(100, self.check_music_end)
                print(f"Playing: {current_track} from {self.positions[station_index]} seconds")
        except Exception as e:
            messagebox.showerror("Error", f"Error playing audio: {e}")

    def update_current_song_label(self, station_index):
        # Update the label to display the current song
        current_station = self.stations[station_index]
        current_track = self.playlists[station_index][self.current_indices[station_index]]
        
        if current_station['voice_lines_folder'] in current_track:
            self.current_song_labels[station_index].config(text="Current Song: [Intermission]")
        else:
            self.current_song_labels[station_index].config(text=f"Current Song: {os.path.basename(current_track)}")
        print(f"Current: {self.current_song_labels[station_index].cget('text')}")

    def check_music_end(self):
        # Check if the music has ended and move to the next track if necessary
        try:
            for station_index in range(self.num_stations):
                if not self.channels[station_index].get_busy() and self.is_playing[station_index]:
                    self.next_track(station_index)
            # Schedule the next check
            self.root.after(100, self.check_music_end)
        except Exception as e:
            messagebox.showerror("Error", f"Error checking music end: {e}")

    def next_track(self, station_index):
        # Move to the next track in the playlist for the given station
        try:
            self.current_indices[station_index] += 1
            if self.current_indices[station_index] >= len(self.playlists[station_index]):
                self.shuffle_and_create_playlist(station_index)
            self.play_audio(station_index)
        except Exception as e:
            messagebox.showerror("Error", f"Error switching to next track: {e}")

    def prev_station(self, event=None):
        # Switch to the previous station, skipping the "Off" tab
        self.current_station = (self.current_station - 1) % (self.num_stations + 1)  # Include "Off" tab
        if self.current_station == 0:  # Skip "Off" tab
            self.current_station = self.num_stations
        self.tab_control.select(self.current_station)  # Update the GUI tab
        self.update_station_playback()
        if self.current_station == 0:
            self.current_station_label.config(text="Current Station: Off")
        else:
            self.current_station_label.config(text=f"Current Station: {self.stations[self.current_station-1]['name']}")

    def next_station(self, event=None):
        # Switch to the next station, skipping the "Off" tab
        self.current_station = (self.current_station + 1) % (self.num_stations + 1)  # Include "Off" tab
        if self.current_station == 0:  # Skip "Off" tab
            self.current_station = 1
        self.tab_control.select(self.current_station)  # Update the GUI tab
        self.update_station_playback()
        self.current_station_label.config(text=f"Current Station: {self.stations[self.current_station-1]['name']}")

    def off_station(self, event=None):
        # Switch to the "Off" station
        self.current_station = 0
        self.tab_control.select(self.current_station)  # Update the GUI tab
        self.update_station_playback()
        self.current_station_label.config(text="Current Station: Off")

    def on_tab_change(self, event):
        # Handle tab change events to switch stations
        self.current_station = self.tab_control.index(self.tab_control.select())
        self.update_station_playback()

    def update_station_playback(self):
        # Adjust the volume for the current station and mute others
        if self.current_station == 0:
            # Mute all channels for the "Off" tab
            for i in range(self.num_stations):
                self.channels[i].set_volume(0)
        else:
            for i in range(self.num_stations):
                if i == self.current_station - 1:
                    self.channels[i].set_volume(self.volumes[i])
                    self.update_current_song_label(i)
                else:
                    self.channels[i].set_volume(0)

    def bind_keys(self):
        # Bind keys for switching stations and controlling volume
        self.root.bind(f"<{self.key_bindings['prev_station']}>", self.prev_station)
        self.root.bind(f"<{self.key_bindings['next_station']}>", self.next_station)
        self.root.bind(f"<{self.key_bindings['volume_up']}>", self.increase_volume)
        self.root.bind(f"<{self.key_bindings['volume_down']}>", self.decrease_volume)
        self.root.bind(f"<{self.key_bindings['off']}>", self.off_station)

    def register_global_hotkeys(self):
        # Register global hotkeys for switching stations and controlling volume
        def on_press(key):
            try:
                if key == keyboard.Key[self.key_bindings["prev_station"].lower()]:
                    self.prev_station()
                elif key == keyboard.Key[self.key_bindings["next_station"].lower()]:
                    self.next_station()
                elif key == keyboard.Key[self.key_bindings["volume_up"].lower()]:
                    self.increase_volume()
                elif key == keyboard.Key[self.key_bindings["volume_down"].lower()]:
                    self.decrease_volume()
                elif key.char == self.key_bindings["off"]:
                    self.off_station()
            except AttributeError:
                pass

        listener = keyboard.Listener(on_press=on_press)
        listener.start()

    def increase_volume(self, event=None):
        # Increase the volume
        if self.current_station > 0:
            self.volumes[self.current_station - 1] = min(self.volumes[self.current_station - 1] + 0.1, 1.0)
        self.update_station_playback()

    def decrease_volume(self, event=None):
        # Decrease the volume
        if self.current_station > 0:
            self.volumes[self.current_station - 1] = max(self.volumes[self.current_station - 1] - 0.1, 0.0)
        self.update_station_playback()

    def set_volume(self, val, station_index=None):
        # Set the volume for the audio playback
        if station_index is not None:
            self.volumes[station_index] = float(val)
        self.update_station_playback()

    def save_key_bindings(self):
        # Save the key bindings
        self.key_bindings["prev_station"] = self.prev_station_entry.get()
        self.key_bindings["next_station"] = self.next_station_entry.get()
        self.key_bindings["volume_up"] = self.volume_up_entry.get()
        self.key_bindings["volume_down"] = self.volume_down_entry.get()
        self.key_bindings["off"] = self.off_entry.get()
        self.bind_keys()
        self.register_global_hotkeys()
        self.save_settings()

    def load_settings(self):
        # Load settings from a JSON file
        print("Loading settings...")
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    self.num_stations = settings.get("num_stations", self.num_stations)
                    self.stations = settings.get("stations", self.stations)  # Only overwrite if settings provide stations
                    self.volumes = settings.get("volumes", [0.5] * self.num_stations)
                    self.key_bindings = settings.get("key_bindings", self.key_bindings)
                    self.current_station = settings.get("current_station", 0)
                    selected_tab = settings.get("selected_tab", 0)
                    self.root.after(100, lambda: self.tab_control.select(selected_tab))
                print(f"Settings loaded: {settings}")
            except json.JSONDecodeError as e:
                messagebox.showerror("Error", f"Error loading settings: Invalid JSON format. {e}")
            except Exception as e:
                messagebox.showerror("Error", f"Error loading settings: {e}")
        else:
            print("Settings file not found. Using default settings.")
        
        if 'off' not in self.key_bindings:
            self.key_bindings['off'] = 'o'

    def save_settings(self):
        # Save settings to a JSON file
        settings = {
            "num_stations": self.num_stations,
            "stations": self.stations,
            "volumes": self.volumes,
            "key_bindings": self.key_bindings,
            "current_station": self.current_station,
            "selected_tab": self.tab_control.index(self.tab_control.select())
        }
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f)
            print(f"Settings saved: {settings}")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving settings: {e}")

    def on_closing(self):
        # Save settings before closing the application
        self.save_settings()
        self.root.destroy()

    def restart_app(self):
        self.save_settings()
        self.root.destroy()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def play_all_stations(self):
        for station_index in range(self.num_stations):
            if self.stations[station_index]['songs_folder'] and os.path.isdir(self.stations[station_index]['songs_folder']):
                self.shuffle_and_create_playlist(station_index)
                self.play_audio(station_index)

if __name__ == "__main__":
    print("Launching application")
    root = tk.Tk()
    app = AudioPlayer(root)
    print("Running mainloop")
    root.mainloop()
    print("Application closed")
