# AI Virtual Keyboard

A touchless, hand-gesture-controlled virtual keyboard built with Python, OpenCV, and MediaPipe. Type, control your mouse, and autocomplete words — all without touching your keyboard.

---

## Demo

> Point your index finger to hover over keys. **Pinch** (bring thumb and index finger together) to press a key.

---

## Features

| Feature | Description |
|---|---|
| ✋ **Hand Tracking** | Real-time finger detection via webcam using cvzone + MediaPipe |
| ⌨️ **Virtual Typing** | Types into any active window on your system |
| 🔠 **Caps Lock / Shift** | Toggle Caps for permanent uppercase; Shift for one-shot uppercase |
| 🖱️ **Mouse Mode** | Control your system cursor with your finger; pinch to left-click |
| 💡 **Autocomplete** | Hover + pinch word suggestions shown below the keyboard |
| 💾 **Auto-Save** | Every keystroke saves to `typed_output.txt` automatically |
| 🎨 **Modern UI** | Dark theme with hover highlights, active state indicators, semi-transparent keys |

---

## Requirements

- Python 3.8+
- Webcam

### Install dependencies

```bash
pip install opencv-python cvzone mediapipe pynput numpy
```

> **Note:** `cvzone` installs MediaPipe automatically. On some systems you may need:
> ```bash
> pip install opencv-contrib-python
> ```

---

## Usage

```bash
python keyboard.py
```

- A window opens showing your webcam feed with the keyboard overlay
- Hold your hand up in front of the camera
- **Hover** your index finger over a key to highlight it
- **Pinch** (index + thumb together) to press the highlighted key
- Press **`Q`** on your physical keyboard to quit

---

## Controls

| Key | Action |
|---|---|
| `CAPS` | Toggle Caps Lock (glows purple when on) |
| `SHIFT` | One-shot uppercase for next character |
| `SPACE` | Type a space |
| `BACK` | Backspace |
| `ENTER` | New line + saves file |
| `MOUSE` | Toggle gesture mouse mode (teal when active) |

### Mouse Mode
When `MOUSE` is active:
- Your **index fingertip** moves the system cursor
- **Pinch** performs a left click
- Press `MOUSE` again to return to keyboard mode

### Autocomplete
- A suggestion bar appears below the keyboard as you type
- Hover + pinch any suggestion to complete the current word

---

## Output

Typed text is auto-saved to `typed_output.txt` in the project folder on every keystroke. The file path is printed to the terminal when you quit.

---

## Project Structure

```
ai-virtual-keyboard/
├── keyboard.py          # Main application
├── typed_output.txt     # Auto-generated: your typed text
├── requirements.txt     # Python dependencies
└── README.md
```

---

## How It Works

1. **OpenCV** captures webcam frames at 960×540
2. **cvzone HandDetector** (wrapping MediaPipe) detects 21 hand landmarks per frame
3. Landmark `[8]` (index fingertip) position is mapped onto the keyboard layout
4. The distance between landmarks `[4]` (thumb tip) and `[8]` (index tip) determines a pinch — threshold is `< 30px`
5. A debounce delay of `0.35s` prevents accidental double-presses
6. **pynput** fires real keyboard/mouse events so typing works in any application

---

## Troubleshooting

**Camera not opening**
```bash
# Try a different camera index
cap = cv2.VideoCapture(1)  # change 0 → 1 or 2
```

**Hand not detected**
- Ensure good lighting facing your hand
- Keep your hand within ~60cm of the camera
- Only one hand is tracked at a time

**Mouse mode not available**
- Ensure `pynput` is installed: `pip install pynput`
- On Linux you may need to run with elevated permissions or configure `uinput`

**Pinch too sensitive / not sensitive enough**
- Adjust the threshold in `keyboard.py`:
  ```python
  pinching = length < 30  # lower = harder to trigger, higher = easier
  ```

---

## Platform Notes

| Platform | Status |
|---|---|
| Windows | ✅ Fully supported |
| macOS | ✅ Supported (grant camera + accessibility permissions) |
| Linux | ⚠️ Supported — may need `python3-xlib` for pynput mouse |

---

## License

MIT License — free to use, modify, and distribute.

---

## Acknowledgements

- [cvzone](https://github.com/cvzone/cvzone) by Murtaza Hassan
- [MediaPipe](https://mediapipe.dev/) by Google
- [pynput](https://github.com/moses-palmer/pynput) for system input control
