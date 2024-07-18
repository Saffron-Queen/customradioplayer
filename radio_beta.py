import os
import random
import json
import tkinter as tk
from tkinter import ttk, filedialog
from pygame import mixer
import sys

SETTINGS_FILE = "settings.json"

class AudioPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Radio Player v0.1 by Cheryl Green")
        self.root.geometry("600x400")
        self.root.configure(bg="black")

        # Initialize station details with default values
        self.stations = [{"name": f"Custom Station {i+1}", "songs_folder": "", "voice_lines_folder": ""} for i in range(4)]
        self.current_station = 0  # Index of the currently selected station (0 for "Off")
        self.playlists = [[] for _ in range(4)]  # List of playlists for each station
        self.current_indices = [0] * 4  # List of current indices for each station
        self.positions = [0] * 4  # List of current positions for each station
        self.is_playing = [False] * 4  # Play/pause state for each station
        self.volume = 0.5  # Default volume level

        # Set up pygame mixer
        mixer.init()
        self.channels = [mixer.Channel(i) for i in range(4)]  # Channels for each station

        # Default key bindings
        self.key_bindings = {
            "prev_station": "Left",
            "next_station": "Right",
            "volume_up": "Up",
            "volume_down": "Down",
            "off": "o"
        }

        # Load settings from file
        self.load_settings()

        # Ensure 'off' key binding is present
        if 'off' not in self.key_bindings:
            self.key_bindings['off'] = 'o'

        # Set up the GUI elements
        self.create_widgets()

        # Bind keys for switching stations and controlling volume
        self.bind_keys()

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

        # Create tabs for stations and settings using ttk.Notebook
        self.tab_control = ttk.Notebook(self.main_frame, style="TNotebook")
        self.tab_control.pack(expand=1, fill="both")

        self.station_tabs = []
        self.current_song_labels = []

        # Add "Off" tab
        off_tab = ttk.Frame(self.tab_control, style="TFrame")
        self.tab_control.add(off_tab, text="Off")
        self.station_tabs.append(off_tab)

        for i in range(4):
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

    def create_settings_widgets(self):
        self.settings_frame = tk.Frame(self.settings_tab, bg="black")
        self.settings_frame.pack(pady=10)

        self.path_entries = []  # List to store folder path entries
        self.browse_buttons = []  # List to store browse buttons

        for i in range(4):
            frame = tk.Frame(self.settings_frame, bg="black")
            frame.pack(pady=10)

            # Create entry and browse button for songs folder
            label = tk.Label(frame, text=f"{self.stations[i]['name']} - Songs Folder:", fg="white", bg="black", font=("Helvetica", 10))
            label.grid(row=0, column=0, padx=5)
            entry = tk.Entry(frame, width=50)
            entry.grid(row=0, column=1, padx=5)
            button = tk.Button(frame, text="Browse", command=lambda idx=i: self.browse_folder(idx, 'songs'), bg="grey", fg="white")
            button.grid(row=0, column=2, padx=5)
            self.path_entries.append(entry)
            self.browse_buttons.append(button)

            # Create entry and browse button for voice lines folder
            label = tk.Label(frame, text=f"{self.stations[i]['name']} - Voice Lines Folder:", fg="white", bg="black", font=("Helvetica", 10))
            label.grid(row=1, column=0, padx=5)
            entry = tk.Entry(frame, width=50)
            entry.grid(row=1, column=1, padx=5)
            button = tk.Button(frame, text="Browse", command=lambda idx=i: self.browse_folder(idx, 'voice_lines'), bg="grey", fg="white")
            button.grid(row=1, column=2, padx=5)
            self.path_entries.append(entry)
            self.browse_buttons.append(button)

        self.rename_station_buttons = []
        for i in range(4):
            frame = tk.Frame(self.settings_frame, bg="black")
            frame.pack(pady=10)
            label = tk.Label(frame, text=f"Rename {self.stations[i]['name']}:", fg="white", bg="black", font=("Helvetica", 10))
            label.grid(row=0, column=0, padx=5)
            entry = tk.Entry(frame, width=30)
            entry.grid(row=0, column=1, padx=5)
            button = tk.Button(frame, text="Rename", command=lambda idx=i, ent=entry: self.rename_station(idx, ent.get()), bg="grey", fg="white")
            button.grid(row=0, column=2, padx=5)
            self.rename_station_buttons.append(button)

        # Key bindings for switching stations and controlling volume
        self.create_key_binding_widgets()

        # Add Save Settings button
        save_button = tk.Button(self.settings_frame, text="Save Settings", command=self.save_settings, bg="grey", fg="white")
        save_button.pack(pady=20)

        # Add Restart Application button
        restart_button = tk.Button(self.settings_frame, text="Restart Application", command=self.restart_app, bg="grey", fg="white")
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
        tk.Button(key_bindings_frame, text="Save Key Bindings", command=self.save_key_bindings, bg="grey", fg="white").grid(row=5, columnspan=2, pady=10)

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
        for i in range(4):
            self.path_entries[i*2].delete(0, tk.END)
            self.path_entries[i*2].insert(0, self.stations[i]['songs_folder'])
            self.path_entries[i*2+1].delete(0, tk.END)
            self.path_entries[i*2+1].insert(0, self.stations[i]['voice_lines_folder'])

    def rename_station(self, station_index, new_name):
        # Rename the station tab and update the station name
        self.stations[station_index]['name'] = new_name
        self.tab_control.tab(station_index + 1, text=new_name)  # +1 to account for "Off" tab

    def shuffle_and_create_playlist(self, station_index):
        # Create and shuffle the playlist for the specified station
        station = self.stations[station_index]
        songs_files = self.get_mp3_files(station['songs_folder'])
        voice_lines_files = self.get_mp3_files(station['voice_lines_folder'])

        random.shuffle(songs_files)
        random.shuffle(voice_lines_files)

        playlist = songs_files.copy()

        for i in range(9, len(playlist), 10):
            if voice_lines_files:
                playlist.insert(i, voice_lines_files.pop(0))

        if voice_lines_files:
            playlist.extend(voice_lines_files)

        self.playlists[station_index] = playlist
        self.current_indices[station_index] = 0

    def get_mp3_files(self, folder):
        # Return a list of MP3 files in the specified folder
        if not folder or not os.path.isdir(folder):
            return []
        return [os.path.join(folder, file) for file in os.listdir(folder) if file.endswith(".mp3")]

    def play_audio(self, station_index):
        # Play the audio for the given station
        if self.current_indices[station_index] < len(self.playlists[station_index]):
            current_track = self.playlists[station_index][self.current_indices[station_index]]
            sound = mixer.Sound(current_track)
            self.channels[station_index].play(sound)
            self.is_playing[station_index] = True
            self.update_current_song_label(station_index)
            self.root.after(100, self.check_music_end)
            print(f"Playing: {current_track} from {self.positions[station_index]} seconds")

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
        for station_index in range(4):
            if not self.channels[station_index].get_busy() and self.is_playing[station_index]:
                self.next_track(station_index)
        # Schedule the next check
        self.root.after(100, self.check_music_end)

    def next_track(self, station_index):
        # Move to the next track in the playlist for the given station
        self.current_indices[station_index] += 1
        if self.current_indices[station_index] >= len(self.playlists[station_index]):
            self.shuffle_and_create_playlist(station_index)
        self.play_audio(station_index)

    def prev_station(self, event=None):
        # Switch to the previous station, skipping the "Off" tab
        self.current_station = (self.current_station - 1) % 5  # Include "Off" tab
        if self.current_station == 0:  # Skip "Off" tab
            self.current_station = 4
        self.tab_control.select(self.current_station)  # Update the GUI tab
        self.update_station_playback()

    def next_station(self, event=None):
        # Switch to the next station, skipping the "Off" tab
        self.current_station = (self.current_station + 1) % 5  # Include "Off" tab
        if self.current_station == 0:  # Skip "Off" tab
            self.current_station = 1
        self.tab_control.select(self.current_station)  # Update the GUI tab
        self.update_station_playback()

    def off_station(self, event=None):
        # Switch to the "Off" station
        self.current_station = 0
        self.tab_control.select(self.current_station)  # Update the GUI tab
        self.update_station_playback()

    def on_tab_change(self, event):
        # Handle tab change events to switch stations
        self.current_station = self.tab_control.index(self.tab_control.select())
        self.update_station_playback()

    def update_station_playback(self):
        # Adjust the volume for the current station and mute others
        if self.current_station == 0:
            # Mute all channels for the "Off" tab
            for i in range(4):
                self.channels[i].set_volume(0)
        else:
            for i in range(4):
                if i == self.current_station - 1:
                    self.channels[i].set_volume(self.volume)
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

    def increase_volume(self, event=None):
        # Increase the volume
        self.volume = min(self.volume + 0.1, 1.0)
        self.update_station_playback()

    def decrease_volume(self, event=None):
        # Decrease the volume
        self.volume = max(self.volume - 0.1, 0.0)
        self.update_station_playback()

    def set_volume(self, val):
        # Set the volume for the audio playback
        self.volume = float(val)
        self.update_station_playback()

    def save_key_bindings(self):
        # Save the key bindings
        self.key_bindings["prev_station"] = self.prev_station_entry.get()
        self.key_bindings["next_station"] = self.next_station_entry.get()
        self.key_bindings["volume_up"] = self.volume_up_entry.get()
        self.key_bindings["volume_down"] = self.volume_down_entry.get()
        self.key_bindings["off"] = self.off_entry.get()
        self.bind_keys()
        self.save_settings()

    def load_settings(self):
        # Load settings from a JSON file
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                self.stations = settings.get("stations", self.stations)
                self.volume = settings.get("volume", self.volume)
                self.key_bindings = settings.get("key_bindings", self.key_bindings)
        
        # Ensure 'off' key binding is present
        if 'off' not in self.key_bindings:
            self.key_bindings['off'] = 'o'

    def save_settings(self):
        # Save settings to a JSON file
        settings = {
            "stations": self.stations,
            "volume": self.volume,
            "key_bindings": self.key_bindings
        }
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f)

    def on_closing(self):
        # Save settings before closing the application
        self.save_settings()
        self.root.destroy()

    def restart_app(self):
        self.save_settings()
        self.root.destroy()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def play_all_stations(self):
        for station_index in range(4):
            if self.stations[station_index]['songs_folder'] and os.path.isdir(self.stations[station_index]['songs_folder']):
                self.shuffle_and_create_playlist(station_index)
                self.play_audio(station_index)

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioPlayer(root)
    root.mainloop()
