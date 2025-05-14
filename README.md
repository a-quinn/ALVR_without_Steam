# ALVR_without_Steam

### This is for Windows OS only.

I had a problem, [others](https://github.com/alvr-org/ALVR/issues/2412) also had it. There may be a better solution but this works for me right now.

For reference, calls to [this](https://developer.valvesoftware.com/wiki/Steam_browser_protocol) is what we are redirecting. Specifically for SteamVR

## Building

### Setup environment
```PowerShell
py -3.10 -m venv .redirect
.\.redirect\Scripts\activate
pip install -r requirements.txt
```

### To build executable
```Powershell
.\.redirect\Scripts\activate

pyinstaller --name ALVR_without_Steam --onefile --noconfirm main.py
```
The built executable will be in a newly created `./dist` folder.

## Usage

Put the compiled `ALVR_without_Steam.exe` in the root dir of SteamVR (i.e., next to `bin`, `content`, `drivers`...)
If Steam is not installed, run executable with Admin and this will create the appropriate registry keys to redirect ALVR launch requests to the `vrstartup.exe`.
If Steam is installed but you want to redirect it. Run executable (may need Admin) and this will redirect requests to `steam://` to this executable and then call `vrstartup.exe`.
For now only SteamVR is handled correctly.

If calls are already being redirected to the `ALVR_without_Steam.exe` then running this executable alone will reset the protocol back to Steam (if you have it installed).

## TODO:
- Launching executables is quite slow.
- Create a Github workflow to auto upload releases. etc.