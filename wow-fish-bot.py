# -*- coding: utf-8 -*-
import os
import random
import sys
import time
import webbrowser

import cv2
import numpy as np
import pyautogui
from infi.systray import SysTrayIcon
from PIL import ImageGrab
from win10toast import ToastNotifier

from pynput.keyboard import Key, KeyCode, Listener
from win32gui import GetForegroundWindow, GetWindowRect, GetWindowText

is_stop = False


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def app_pause(systray):
    global is_stop
    is_stop = False if is_stop is True else True
    print("Is Pause: " + str(is_stop))
    if is_stop is True:
        systray.update(hover_text=app + " - On Pause")
    else:
        systray.update(hover_text=app)


def app_destroy(systray):
    print("Exit app")
    sys.exit()


def app_about(systray):
    webbrowser.open("https://github.com/YECHEZ/wow-fish-bot")


# config
KEY_FISHING = "f10"
KEY_BAIT = "f11"
KEY_FISHING_ROD = "f9"

recast_time = 40  # s
bait_time = 10 * 60 + 10  # s

app = "WoW Fish BOT by YECHEZ"
link = "github.com/YECHEZ/wow-fish-bot"
app_ico = resource_path("wow-fish-bot.ico")
menu_options = (("Start/Stop", None, app_pause), (link, None, app_about))


def put_bait(bait_since):
    if bait_since is None or (
        bait_since is not None and time.time() - bait_since > bait_time
    ):
        bait_since = time.time()
        print("Bait on !")
        pyautogui.press(KEY_BAIT)
        pyautogui.press(KEY_FISHING_ROD)
        time.sleep(3.5)
    return bait_since


if __name__ == "__main__":
    flag_exit = False

    # for reduced spam in log
    has_shown_waiting = False
    has_shown_pause = False
    has_shown_frame = False
    has_shown_fish_frame = False

    # detection
    lastx = 0
    lasty = 0

    is_block = False
    bait_since = None
    new_cast_time = 0

    # systray
    systray = SysTrayIcon(app_ico, app, menu_options, on_quit=app_destroy)
    systray.start()

    # windows popup
    toaster = ToastNotifier()
    toaster.show_toast(app, link, icon_path=app_ico, duration=5)

    # main loop
    while flag_exit is False:
        if not is_stop:
            has_shown_pause = False
            if GetWindowText(GetForegroundWindow()) != "World of Warcraft":
                if not has_shown_waiting:
                    toaster.show_toast(
                        app,
                        "Waiting for World of Warcraft" + " as active window",
                        icon_path="wow-fish-bot.ico",
                        duration=5,
                    )
                    has_shown_waiting = True
                    print("Waiting for World of Warcraft as active window")
                    systray.update(
                        hover_text=app
                        + " - Waiting for World of Warcraft as active window"
                    )
                time.sleep(0.1)
            else:
                has_shown_waiting = False
                systray.update(hover_text=app)

                # detection
                rect = GetWindowRect(GetForegroundWindow())

                # top-left corner is x,y = 0,0
                window_width = rect[2] / 3
                x_min = rect[2] / 3  # offset
                x_max = x_min + window_width

                window_height = rect[3] * 0.3
                y_min = rect[3] / 2  # offset
                y_max = y_min + window_height

                fish_area = x_min, y_min, x_max, y_max

                # show the frame once
                if not has_shown_fish_frame:
                    has_shown_fish_frame = True
                    pyautogui.moveTo(fish_area[0], fish_area[1], 0.5)
                    time.sleep(0.125)
                    pyautogui.moveTo(fish_area[2], fish_area[1], 0.5)
                    time.sleep(0.125)
                    pyautogui.moveTo(fish_area[2], fish_area[3], 0.5)
                    time.sleep(0.125)
                    pyautogui.moveTo(fish_area[0], fish_area[3], 0.5)
                    time.sleep(0.125)
                    pyautogui.moveTo(fish_area[0], fish_area[1], 0.5)
                    time.sleep(0.125)

                if not is_block:
                    bait_since = put_bait(bait_since)

                    lastx = 0
                    lasty = 0
                    time.sleep(random.randint(500, 3000) / 1000)
                    pyautogui.press(KEY_FISHING)
                    print("Fish on !")
                    new_cast_time = time.time()
                    is_block = True
                    time.sleep(random.randint(500, 1500) / 1000)
                else:
                    img = ImageGrab.grab(fish_area)
                    img_np = np.array(img)

                    frame = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
                    frame_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

                    h_min = np.array((0, 0, 253), np.uint8)
                    h_max = np.array((255, 0, 255), np.uint8)

                    mask = cv2.inRange(frame_hsv, h_min, h_max)

                    moments = cv2.moments(mask, 1)
                    dM01 = moments["m01"]
                    dM10 = moments["m10"]
                    dArea = moments["m00"]

                    b_x = 0
                    b_y = 0

                    if dArea > 0:
                        b_x = int(dM10 / dArea)
                        b_y = int(dM01 / dArea)

                    if lastx > 0 and lasty > 0:
                        if lastx != b_x and lasty != b_y:
                            is_block = False
                            if b_x < 1:
                                b_x = lastx
                            if b_y < 1:
                                b_y = lasty
                            print(f"Detected at x:{b_x}, y:{b_y}")
                            pyautogui.click(
                                x=b_x + fish_area[0],
                                y=b_y + fish_area[1],
                                duration=random.randint(100, 1250) / 1000,
                                button="right",
                            )
                            print("Catch !")
                            time.sleep(random.randint(500, 3000) / 1000)
                    lastx = b_x
                    lasty = b_y

                    if time.time() - new_cast_time > recast_time:
                        print("New cast if something wrong")
                        is_block = False
            if cv2.waitKey(1) == 27:
                break
        else:
            if not has_shown_pause:
                has_shown_pause = True
                print("Pause")
                systray.update(hover_text=app + " - On Pause")
            time.sleep(0.1)


def function_startstop():
    is_stop = not is_stop


# Create a mapping of keys to function (use frozenset as sets are not hashable - so they can't be used as keys)
combination_to_function = {
    frozenset(
        [Key.shift, KeyCode(char="s")]
    ): function_startstop,  # No `()` after function_1 because we want to pass the function, not the value of the function
    frozenset([Key.shift, KeyCode(char="S")]): function_startstop,
}

current_keys = set()


def on_press(key):
    current_keys.add(key)
    if frozenset(current_keys) in combination_to_function:
        combination_to_function[frozenset(current_keys)]()


def on_release(key):
    current_keys.remove(key)


with Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
