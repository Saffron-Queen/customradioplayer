# customradioplayer
Custom Radio Player for Racing games
The Custom Radio Player is a Python-based application designed to mimic the functionality and aesthetics of a real-life car radio. It allows users to play audio from multiple folders, seamlessly switching between different "stations" which are represented by separate tabs in the application. Users can configure the folders for each station, shuffle songs, and intermix voice lines. The application includes a feature to mute all stations and a user-friendly interface for managing settings and controls.
Technical Explanation

The Custom Radio Player is built using Python and the following libraries:

    tkinter: For creating the gui.
    pygame: For handling audio playback.

Key Features

  Multi-station Support: Users can configure up to four stations, each with its own folder for songs and voice lines.
  Station Switching: Switch between stations using hotkeys or by clicking on the tabs. The "Off" tab can only be selected using a designated hotkey.
  Audio Playback: Songs are shuffled, and voice lines are inserted every tenth song. Playback continues in the background for all stations, ensuring smooth transitions.
  Volume Control: Users can adjust the volume using hotkeys or the volume control in the settings tab.
  Settings Management: Paths for songs and voice lines can be configured, key bindings can be customized, and stations can be renamed through the settings tab.
  Persistent Settings: User settings are saved and loaded from a JSON file, ensuring preferences are preserved across sessions.

Install Guide
Prerequisites

  Python 3.6 or higher: Ensure Python is installed on your system. You can download it from python.org.

Dependencies

  tkinter: Typically included with Python.
  pygame: Needs to be installed separately.

Installation Steps
For Linux

  Install Python and tkinter

Install pygame



Run the application:


    python3 radio_beta.py

For Windows

  Install Python and tkinter:
        Download and install Python from python.org.
        Ensure you check the box to add Python to your PATH during installation.

  Install pygame:
  Open Command Prompt and run:


    pip install pygame


Run the application:

  Open Command Prompt, navigate to the directory containing custom_radio_player.py, and run:

    

        python radio_beta.py

Usage Guide

  Configuring Stations:
        Open the application and navigate to the Settings tab.
        Use the browse buttons to select folders for songs and voice lines for each station.
        Rename stations as desired and save your changes.

  Switching Stations:
        Use the left and right arrow keys to switch between stations.
        Press o to mute all stations by selecting the "Off" tab.
        You can also click on the station tabs at the bottom of the window to switch stations.

   Adjusting Volume:
        Use the up and down arrow keys to increase or decrease the volume.
        Volume can also be adjusted in the settings tab.

  Enjoy Your Music:
        The current song playing will be displayed on the main screen, and the application will continuously play music based on your settings.
