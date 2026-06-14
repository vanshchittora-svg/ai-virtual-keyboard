import cv2
from cvzone.HandTrackingModule import HandDetector
from pynput.keyboard import Controller, Key
import time
import numpy as np
import os
import ctypes

# ─────────────────────────────────────────
#  Autocomplete word list
# ─────────────────────────────────────────
WORD_LIST = [
    "the","be","to","of","and","a","in","that","have","it",
    "for","not","on","with","he","as","you","do","at","this",
    "but","his","by","from","they","we","say","her","she","or",
    "an","will","my","one","all","would","there","their","what",
    "so","up","out","if","about","who","get","which","go","me",
    "when","make","can","like","time","no","just","him","know",
    "take","people","into","year","your","good","some","could",
    "them","see","other","than","then","now","look","only","come",
    "its","over","think","also","back","after","use","two","how",
    "our","work","first","well","way","even","new","want","because",
    "any","these","give","day","most","us","hello","world","python",
    "virtual","keyboard","press","type","enter","space","delete",
    "computer","screen","camera","hand","finger","gesture","pinch",
    "click","mouse","mode","shift","caps","lock","autocomplete",
    "suggest","word","text","file","save",
]

# ─────────────────────────────────────────
#  Save text to file
# ─────────────────────────────────────────
SAVE_FILE = "typed_output.txt"

def save_text(text):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        f.write(text)

# ─────────────────────────────────────────
#  Keyboard Controller
# ─────────────────────────────────────────
keyboard_controller = Controller()

# ─────────────────────────────────────────
#  Camera Setup
# ─────────────────────────────────────────
cap = cv2.VideoCapture(0)
cap.set(3, 960)
cap.set(4, 540)

# ─────────────────────────────────────────
#  Hand Detector
# ─────────────────────────────────────────
detector = HandDetector(detectionCon=0.8, maxHands=1)

# ─────────────────────────────────────────
#  State Variables
# ─────────────────────────────────────────
finalText    = ""
lastClickTime = 0
clickDelay   = 0.35

caps_lock    = False
shift_active = False
mouse_mode   = False

suggestions          = []
suggestion_hover_idx = -1

# ─────────────────────────────────────────
#  Mouse mode helpers
# ─────────────────────────────────────────
try:
    from pynput.mouse import Controller as MouseController, Button
    mouse_ctrl     = MouseController()
    MOUSE_AVAILABLE = True
except Exception:
    MOUSE_AVAILABLE = False

prev_mouse_x = None
prev_mouse_y = None
MOUSE_SMOOTH = 0.5

try:
    user32   = ctypes.windll.user32
    SCREEN_W = user32.GetSystemMetrics(0)
    SCREEN_H = user32.GetSystemMetrics(1)
except Exception:
    SCREEN_W, SCREEN_H = 1920, 1080

# ─────────────────────────────────────────
#  Keyboard Layouts
# ─────────────────────────────────────────
lower_layout = [
    ["1","2","3","4","5","6","7","8","9","0"],
    ["q","w","e","r","t","y","u","i","o","p"],
    ["a","s","d","f","g","h","j","k","l"],
    ["z","x","c","v","b","n","m","."],
    ["CAPS","SHIFT","SPACE","BACK","ENTER","MOUSE"],
]

upper_layout = [
    ["1","2","3","4","5","6","7","8","9","0"],
    ["Q","W","E","R","T","Y","U","I","O","P"],
    ["A","S","D","F","G","H","J","K","L"],
    ["Z","X","C","V","B","N","M","."],
    ["CAPS","SHIFT","SPACE","BACK","ENTER","MOUSE"],
]

row_y      = [90, 175, 260, 345, 440]
row_starts = [50, 50, 100, 150, 20]
key_height = 65

SPECIAL_WIDTHS = {
    "SPACE": 200, "BACK": 120, "ENTER": 140,
    "CAPS": 100,  "SHIFT": 100, "MOUSE": 110,
}
DEFAULT_KEY_W = 60

# ─────────────────────────────────────────
#  Colour palette
# ─────────────────────────────────────────
COL_BG_KEY   = (40,  40,  40)
COL_HOVER    = (60, 140, 255)
COL_SPECIAL  = (70,  40, 100)
COL_ACTIVE   = (180, 60, 220)
COL_MOUSE_ON = (0,  180, 180)
COL_OUTLINE  = (120, 120, 120)
COL_TEXT     = (240, 240, 240)
COL_FINGER   = (0,  255,   0)
COL_PINCH    = (0,  200, 255)

# ─────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────
def get_layout():
    return upper_layout if (caps_lock ^ shift_active) else lower_layout

def key_width(key):
    return SPECIAL_WIDTHS.get(key, DEFAULT_KEY_W)

def get_suggestions(text, n=4):
    words = text.split()
    if not words:
        return []
    partial = words[-1].lower()
    if not partial:
        return []
    return [w for w in WORD_LIST if w.startswith(partial) and w != partial][:n]

# ─────────────────────────────────────────
#  Draw a key
# ─────────────────────────────────────────
def draw_key(img, key, x, y, w, h, hovered):
    is_special = key in SPECIAL_WIDTHS

    if key == "MOUSE" and mouse_mode:
        fill = COL_MOUSE_ON
    elif (key == "CAPS" and caps_lock) or (key == "SHIFT" and shift_active):
        fill = COL_ACTIVE
    elif hovered:
        fill = COL_HOVER
    elif is_special:
        fill = COL_SPECIAL
    else:
        fill = COL_BG_KEY

    overlay = img.copy()
    cv2.rectangle(overlay, (x, y), (x+w, y+h), fill, cv2.FILLED)
    cv2.addWeighted(overlay, 0.85, img, 0.15, 0, img)

    border_col = (200, 200, 200) if hovered else COL_OUTLINE
    cv2.rectangle(img, (x, y), (x+w, y+h), border_col, 1)

    font_scale = 0.55 if len(key) > 3 else (0.65 if len(key) > 1 else 0.75)
    (tw, th), _ = cv2.getTextSize(key, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)
    tx = x + (w - tw) // 2
    ty = y + (h + th) // 2
    cv2.putText(img, key, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, COL_TEXT, 2)

# ─────────────────────────────────────────
#  Draw suggestion bar
# ─────────────────────────────────────────
SUGG_Y   = 510
SUGG_H   = 40
SUGG_PAD = 12

def draw_suggestions(img, suggestions, finger_x, finger_y):
    global suggestion_hover_idx
    suggestion_hover_idx = -1
    x = 20
    for i, word in enumerate(suggestions):
        (tw, _), _ = cv2.getTextSize(word, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
        w = tw + SUGG_PAD * 2
        hovered = (finger_x is not None and
                   x < finger_x < x + w and
                   SUGG_Y < finger_y < SUGG_Y + SUGG_H)
        fill = (80, 160, 255) if hovered else (50, 50, 80)
        cv2.rectangle(img, (x, SUGG_Y), (x+w, SUGG_Y+SUGG_H), fill, cv2.FILLED)
        cv2.rectangle(img, (x, SUGG_Y), (x+w, SUGG_Y+SUGG_H), COL_OUTLINE, 1)
        cv2.putText(img, word, (x+SUGG_PAD, SUGG_Y+27),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, COL_TEXT, 2)
        if hovered:
            suggestion_hover_idx = i
        x += w + 10

# ─────────────────────────────────────────
#  Main Loop
# ─────────────────────────────────────────
while True:
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)
    now = time.time()

    # ── Detect Hands ───────────────────────
    hands, img = detector.findHands(img, flipType=False)

    finger_x = finger_y = None
    length   = 999
    pinching = False

    if hands:
        lmList   = hands[0]["lmList"]
        finger_x = lmList[8][0]
        finger_y = lmList[8][1]

        length, info, img = detector.findDistance(
            lmList[4][:2], lmList[8][:2], img
        )
        pinching = length < 30

        dot_col = COL_PINCH if pinching else COL_FINGER
        cv2.circle(img, (finger_x, finger_y), 12, dot_col, cv2.FILLED)
        cv2.circle(img, (finger_x, finger_y), 12, (255, 255, 255), 1)

    # ── Mouse Mode ─────────────────────────
    if mouse_mode and MOUSE_AVAILABLE and finger_x is not None:
        target_x = int(np.interp(finger_x, [0, 960], [0, SCREEN_W]))
        target_y = int(np.interp(finger_y, [0, 540], [0, SCREEN_H]))

        if prev_mouse_x is None:
            prev_mouse_x, prev_mouse_y = target_x, target_y

        smooth_x = int(prev_mouse_x + (target_x - prev_mouse_x) * MOUSE_SMOOTH)
        smooth_y = int(prev_mouse_y + (target_y - prev_mouse_y) * MOUSE_SMOOTH)

        mouse_ctrl.position = (smooth_x, smooth_y)
        prev_mouse_x, prev_mouse_y = smooth_x, smooth_y

        if pinching and now - lastClickTime > clickDelay:
            mouse_ctrl.click(Button.left, 1)
            lastClickTime = now

        cv2.putText(img, "MOUSE MODE  (pinch=click)", (20, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, COL_MOUSE_ON, 2)

    # ── Update suggestions ──────────────────
    if not mouse_mode:
        suggestions = get_suggestions(finalText)

    # ── Draw Keyboard ──────────────────────
    layout = get_layout()

    for row_index, row in enumerate(layout):
        cx = row_starts[row_index]
        y  = row_y[row_index]

        for key in row:
            w = key_width(key)
            hovered = (
                not mouse_mode and
                finger_x is not None and
                cx < finger_x < cx + w and
                y < finger_y < y + key_height
            )

            draw_key(img, key, cx, y, w, key_height, hovered)

            # ── Pinch → type ──────────────
            if hovered and pinching and now - lastClickTime > clickDelay and not mouse_mode:
                lastClickTime = now

                if key == "SPACE":
                    finalText += " "
                    keyboard_controller.press(Key.space)
                    keyboard_controller.release(Key.space)

                elif key == "BACK":
                    if finalText:
                        finalText = finalText[:-1]
                    keyboard_controller.press(Key.backspace)
                    keyboard_controller.release(Key.backspace)

                elif key == "ENTER":
                    finalText += "\n"
                    keyboard_controller.press(Key.enter)
                    keyboard_controller.release(Key.enter)
                    save_text(finalText)

                elif key == "CAPS":
                    caps_lock = not caps_lock

                elif key == "SHIFT":
                    shift_active = not shift_active

                elif key == "MOUSE":
                    mouse_mode   = not mouse_mode
                    prev_mouse_x = prev_mouse_y = None

                else:
                    finalText += key
                    keyboard_controller.type(key)
                    if shift_active:
                        shift_active = False

                save_text(finalText)

            cx += w + 10

    # ── Suggestion bar ─────────────────────
    if suggestions and not mouse_mode:
        draw_suggestions(img, suggestions, finger_x, finger_y)

        if pinching and suggestion_hover_idx >= 0 and now - lastClickTime > clickDelay:
            chosen   = suggestions[suggestion_hover_idx]
            parts    = finalText.split(" ")
            parts[-1] = chosen + " "
            finalText = " ".join(parts)
            keyboard_controller.type(chosen + " ")
            lastClickTime = now
            save_text(finalText)

    # ── Text display bar ───────────────────
    cv2.rectangle(img, (0, 0), (960, 75), (20, 20, 20), cv2.FILLED)
    cv2.line(img, (0, 75), (960, 75), (70, 70, 70), 1)

    display_text = finalText.replace("\n", "↵")[-50:]
    cv2.putText(img, display_text, (14, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.85, (240, 240, 240), 2)

    # ── CAPS / SHIFT indicators ─────────────
    if caps_lock:
        cv2.putText(img, "CAPS", (14, 68),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, COL_ACTIVE, 2)
    if shift_active:
        cv2.putText(img, "SHIFT", (70, 68),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 2)

    cv2.imshow("AI Virtual Keyboard", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ── Cleanup ────────────────────────────────
save_text(finalText)
print(f"\n[Saved] → {os.path.abspath(SAVE_FILE)}")
cap.release()
cv2.destroyAllWindows()