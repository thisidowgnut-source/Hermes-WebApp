import pygetwindow as gw
import pyautogui
import time
import pyperclip
import sys

# Find Chrome window
chrome_windows = gw.getWindowsWithTitle('Chrome')
if not chrome_windows:
    chrome_windows = [w for w in gw.getAllWindows() if 'Google Chrome' in w.title or 'Chrome' in w.title]

if not chrome_windows:
    print("Could not find Chrome window.")
    sys.exit(1)

# Pick the first one and activate
win = chrome_windows[0]
try:
    win.activate()
except Exception as e:
    print(f"Failed to activate window: {e}")
    # Try restoring if minimized
    if win.isMinimized:
        win.restore()

time.sleep(1)

# Open a new tab
pyautogui.hotkey('ctrl', 't')
time.sleep(1)

# Go to the user's profile
pyautogui.typewrite('https://www.facebook.com/profile.php?id=1668818405')
pyautogui.press('enter')
time.sleep(8)  # Wait for Facebook to load

# Open DevTools
pyautogui.hotkey('ctrl', 'shift', 'j')
time.sleep(3)  # Wait for DevTools

js_code = """
(async () => {
    // Basic script to extract first post date from timeline.
    // Instead of doing complex DOM manipulation, let's just copy the page HTML to clipboard
    // so the Python script can analyze it, or we can fetch the GraphQL / Activity Log.
    const res = await fetch('https://www.facebook.com/1668818405/allactivity');
    const text = await res.text();
    copy(text); // DevTools function to copy to clipboard
})();
"""

pyperclip.copy(js_code)
pyautogui.hotkey('ctrl', 'v')
time.sleep(0.5)
pyautogui.press('enter')

print("Script executed. Waiting for clipboard to update...")
time.sleep(5)

clipboard_content = pyperclip.paste()
with open("fb_activity.html", "w", encoding="utf-8") as f:
    f.write(clipboard_content)

print(f"Saved {len(clipboard_content)} characters from clipboard.")
