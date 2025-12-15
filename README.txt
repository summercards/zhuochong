Knight Pet Desktop Application
=============================

This folder contains the source code and resources for a simple desktop pet
application built with Python and Tkinter. A cute cat knight character will
appear on your desktop, gently breathing when idle and performing a quick
attack animation whenever you press a key or click the mouse. A counter below
the character keeps track of how many interactions have occurred.

Files:

* `knight_pet.py` – the main Python script containing the Tkinter
  implementation. Run this script to launch the pet.
* `images/knight.png` – the cat knight image used by the application.

Running the application on Windows:
-----------------------------------

1. Install Python 3.x for Windows if you don't already have it. Make sure the
   optional *tcl/tk* component is selected during installation (it's enabled by
   default).
2. Install the Pillow library (required to load the PNG image) by opening a
   command prompt and running:

       pip install pillow

3. Open a command prompt, navigate to this folder, and run:

       python knight_pet.py

   The knight pet will appear near the bottom-right corner of your primary
   monitor. Press any key or click the mouse to see it attack. The counter
   will increment each time.

### Global key capture

This program can optionally capture keyboard events even when the pet window
doesn't have focus. To enable this, install the `keyboard` library:

    pip install keyboard

If the library isn't installed, the pet will still work, but it will only
respond when it has focus.

Converting to a standalone .exe:
--------------------------------

To create a Windows executable, you need to run a *freezing* tool on a
Windows machine. PyInstaller is a popular choice. Unfortunately PyInstaller
cannot cross-compile from Linux to Windows【706207000818629†L60-L62】, so you
must perform this step on a Windows PC. Here is a brief guide:

1. Ensure Python and Pip are installed on your Windows machine.
2. Install PyInstaller:

       pip install pyinstaller

3. From a command prompt in this directory, run PyInstaller with the
   following flags to produce a single-file executable without a console
   window:

       pyinstaller --noconsole --onefile knight_pet.py

4. After the build completes, look in the `dist` folder for
   `knight_pet.exe`. You can copy this .exe and distribute it as your
   desktop pet. When double-clicked, it will launch without requiring
   Python to be installed on the target system.

Note: because Tkinter cannot capture global keyboard events outside its
window, the pet will only respond when it has focus. Implementing a
system-wide hook requires additional libraries (e.g., `keyboard` or
`pynput`) which are not included here. You may add such functionality
before freezing if desired.