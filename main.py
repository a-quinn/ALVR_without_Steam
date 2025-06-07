# Author: Alastair Quinn 2025

from pathlib import Path
from sys import exit
from subprocess import Popen, CREATE_NO_WINDOW, DETACHED_PROCESS, CREATE_NEW_PROCESS_GROUP
import sys
from time import sleep
import traceback
from os import _exit

# This program allows running SteamVR from calls to the Steam protocol without needing Steam installed.
# This will replace the steam://rungameid/250820 command with a call to the SteamVR executable.
# Any other command will be passed to the Steam executable as normal.
# If steam is not installed, the program will exit with an error message.
# This prgoram replaced the call to the Steam executable in the HKEY_CLASSES_ROOT\steam\Shell\Open\Command
# registry key with a call to this program.

# If this program is run with no arguments it will check if it set in the registry and if so,
# it will replace the call to this executable with the Steam executable. If it is not set,
# it will replace the call to the Steam executable with this program. Toggling the registry key.

# If the registry key does not exist, it will create it and set the value to this program.

import winreg

def get_steam_path():
    # get from registry key HKEY_CURRENT_USER\Software\Valve\Steam\SteamPath
    # if it does not exist, return None

    try:
        # Open the registry key
        registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", 0, winreg.KEY_READ)
        # Read the value of the SteamPath key
        steam_path, _ = winreg.QueryValueEx(registry_key, "SteamPath")
        # Close the registry key
        winreg.CloseKey(registry_key)
        
        steam_path = steam_path.replace("/", "\\")
        steam_path += "\\steam.exe"
        return steam_path
    except FileNotFoundError:
        # If the key does not exist, return None
        return None

def get_registry_key():
    # Get the registry key what is called HKEY_CLASSES_ROOT\steam\Shell\Open\Command\(Default)
    # if it does not exist, return None
    try:
        # Open the registry key
        registry_key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"steam\Shell\Open\Command", 0, winreg.KEY_READ)
        # Read the value of the (Default) key
        default_value, _ = winreg.QueryValueEx(registry_key, "")
        # Close the registry key
        winreg.CloseKey(registry_key)
        return default_value
    except FileNotFoundError:
        # If the key does not exist, return None
        return None

def set_registry_key(value):
    # Set the registry key what is called HKEY_CLASSES_ROOT\steam\Shell\Open\Command\(Default)
    # if it does not exist, create it
    try:
        # Open the registry key
        registry_key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"steam\Shell\Open\Command", 0, winreg.KEY_SET_VALUE)
        # Set the value of the (Default) key
        winreg.SetValueEx(registry_key, "", 0, winreg.REG_SZ, value)
        # Close the registry key
        winreg.CloseKey(registry_key)
    except FileNotFoundError:
        # If the key does not exist, create it
        registry_key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"steam\Shell\Open\Command")
        # Set the value of the (Default) key
        winreg.SetValueEx(registry_key, "", 0, winreg.REG_SZ, value)
        # Close the registry key
        winreg.CloseKey(registry_key)
    except Exception as e:
        print(f"Error setting registry key: {e}")
        return False

def extract_path_from_command(command):
    # Extract the path from the command
    # The command is in the format "C:\path\to\steam.exe" -- "%1"
    # We want to extract the path to steam.exe
    # This will be used to set the registry key to the steam executable
    # if it is not already set
    parts = command.split('"')
    if len(parts) > 1:
        return parts[1]
    else:
        return None

def create_base_registry_key():
    # Create the base registry key what is called HKEY_CLASSES_ROOT\steam
    # HKEY_CLASSES_ROOT
    # └── steam
    #     ├── (Default) = "URL:Steam Protocol"
    #     ├── URL Protocol = ""
    #     └── shell
    #         └── open
    #             └── command
    #                 └── (Default) = "C:\local\projects\steam_run_shortcut\dist\steam_run_shortcut.exe" "%1"
    # if it does not exist, create it
    try:
        # Open the registry key
        registry_key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"steam", 0, winreg.KEY_SET_VALUE)
        # Set the value of the (Default) key
        winreg.SetValueEx(registry_key, "", 0, winreg.REG_SZ, "URL:Steam Protocol")
        # Set the value of the URL Protocol key
        winreg.SetValueEx(registry_key, "URL Protocol", 0, winreg.REG_SZ, "")
        # Close the registry key
        winreg.CloseKey(registry_key)
    except FileNotFoundError:
        # If the key does not exist, create it
        registry_key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"steam")
        # Set the value of the (Default) key
        winreg.SetValueEx(registry_key, "", 0, winreg.REG_SZ, "URL:Steam Protocol")
        # Set the value of the URL Protocol key
        winreg.SetValueEx(registry_key, "URL Protocol", 0, winreg.REG_SZ, "")
        # Close the registry key
        winreg.CloseKey(registry_key)
    # Create the shell key
    try:
        registry_key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"steam\Shell")
        # Create the open key
        registry_key = winreg.CreateKey(registry_key, r"Open")
        # Create the command key
        registry_key = winreg.CreateKey(registry_key, r"Command")
        # Close the registry key
        winreg.CloseKey(registry_key)
    except FileNotFoundError:
        # If the key does not exist, create it
        registry_key = winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, r"steam\Shell\Open\Command")
        # Close the registry key
        winreg.CloseKey(registry_key)
    except Exception as e:
        print(f"Error creating registry key: {e}")
        return False

def update_active_protocol():
    # get name of this executable
    self_name = Path(sys.argv[0])
    this_exe_path = self_name.resolve()

    protocol_path = get_registry_key()

    print(f"Registry key: {protocol_path}")

    if protocol_path is None:
        print("Registry key does not exist. Creating it.")
        # set registry key to steam executable
        create_base_registry_key()
        set_registry_key(f'conhost.exe "{this_exe_path}" -- "%1"') # use conhost to avoid any custom terminal windows
        return
    
    # Toggle the registry key

    steam_path = get_steam_path()
    if steam_path is None:
        print("Steam is not installed.")
        return
    
    print(f"Steam path: {steam_path}")

    protocol_exe = extract_path_from_command(protocol_path)
    print(f"Steam protocol exe: {protocol_exe}")

    if this_exe_path.name in protocol_path:
        print("Registry key was set to this executable changing to Steam executable.")
        # set registry key to steam executable
        set_registry_key(f'"{steam_path}" -- "%1"')
    elif str(protocol_exe).lower() == str(steam_path).lower():
        print("Registry key was set to steam executable changing to this executable.")
        # set registry key to this executable
        # get the path to this executable
        set_registry_key(f'conhost.exe "{this_exe_path}" -- "%1"') # use conhost to avoid any custom terminal windows
    else:
        print(f"Registry key was set to something else ({protocol_exe}). Doing nothing.")
        return

    print(f"New registry key: {get_registry_key()}")


# this executable will be stored in the SteamVR folder
# we want to run the 'SteamVR\bin\win64\vrstartup.exe' executable
# if the command is 'rungameid' and the parameters are '250820'
def run_steamvr():
    # get path to this executable
    this_exe_path = Path(sys.argv[0])
    # get path to steamvr executable
    steamvr_path = this_exe_path.parent / "bin" / "win64" / "vrstartup.exe"
    # check if the path exists
    if not steamvr_path.exists():
        print(f"SteamVR executable not found: {steamvr_path}")
        sleep(2)
        return
    
    #cmd = ['cmd.exe', '/c', str(steamvr_path)] # working
    cmd = ['cmd.exe', '/c', 'start', '', str(steamvr_path)] # working
    #cmd = [str(steamvr_path)] # working
    #print(f"Running SteamVR by: {cmd}")
    
    # spawn the process without waiting for it to finish
    flags = 0
    #flags |= CREATE_NEW_CONSOLE
    flags |= DETACHED_PROCESS
    flags |= CREATE_NEW_PROCESS_GROUP
    flags |= CREATE_NO_WINDOW
    Popen(cmd, shell=True, creationflags=flags, close_fds=True)
    _exit(0) # ignore cleanup, just exit immediately


def main():

    if len(sys.argv) < 3:
        print("No arguments provided. Updating active registry key.")
        update_active_protocol()
        sleep(2)
        exit(0)

    # add help message
    if sys.argv[1] == "--help" or sys.argv[1] == "-h":
        print("Version 1.0.1")
        print("If this program is run with no arguments, it will update the active registry key for the Steam browser protocol.")
        print("Updating the active registry key will toggle the registry key between this executable and the Steam executable.")
        print("This program will run the SteamVR executable directly if the protocol is 'steam://rungameid/250820'.")
        print("Otherwise, it will run the command with Steam if Steam is installed.")
        exit(0)
    
    print(sys.argv)
    # "C:\local\projects\steam_run_shortcut\dist\steam_run_shortcut\steam_run_shortcut.exe" -- "%1"

    if sys.argv[1] != "--":
        print("Invalid arguments. Expected '--' as the first argument.")
        sleep(1)
        exit(0)

    protocol = sys.argv[2]
    if protocol.startswith("steam://"):
        parts = protocol.split("/")
        command = parts[2] if len(parts) > 2 else None
        parameters = parts[3:] if len(parts) > 3 else []

        print(f"Command: {command}")
        print(f"Parameters: {parameters}")

        if command == "rungameid":
            if len(parameters) > 0:
                game_id = parameters[0]
                print(f"Game ID: {game_id}")
                if game_id == "250820":
                    print("Running SteamVR")
                    run_steamvr()
                    exit(0)
        
        # if steam is installed, run the command with Steam
        steam_path = get_steam_path()
        if steam_path is None:
            print("Steam is not installed. Unable to run command.")
            #sleep(2)
            exit(0)

        # spawn the process without waiting for it to finish
        cmd = ['cmd.exe', '/c', 'start', '', str(steam_path), protocol] # working
        
        flags = 0
        flags |= DETACHED_PROCESS
        flags |= CREATE_NEW_PROCESS_GROUP
        flags |= CREATE_NO_WINDOW
        Popen(cmd, shell=True, creationflags=flags, close_fds=True)
        _exit(0) # ignore cleanup, just exit immediately

    else:
        print("Invalid protocol format.")

    sleep(2)
    exit(0)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        sleep(2)
        exit(1)