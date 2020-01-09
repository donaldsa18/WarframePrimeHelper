import cv2
import numpy as np

from time import time
from datetime import datetime

import win32gui
import win32ui
import win32con
import time
import os

from prettytable import PrettyTable
import csv
import string
import re
import difflib

if os.path.isdir('tesseract4win64-4.0-beta\\tessdata'):
    os.environ['TESSDATA_PREFIX'] = os.path.abspath('tesseract4win64-4.0-beta\\tessdata')

from concurrent.futures import ThreadPoolExecutor
from optparse import OptionParser
from tesserocr import PyTessBaseAPI
from PIL import Image
import queue


class OCR:
    def __init__(self, debug=None, gui=None):
        self.window_name = "Warframe"
        self.screenshot_name = 'resources\\screenshot.bmp'

        self.title = "Warframe Prime Helper"

        self.w = w = 908
        self.h = h = 70
        self.x_offset = 521
        self.y_offset = 400

        self.warframe_w = 0
        self.warframe_h = 0

        box_w = 223
        half_box_w = int(box_w / 2)
        self.crop_list = [(0, 27, w, h),  # the entire bottom
                          (half_box_w, 0, half_box_w * 3, h),  # assumes 3 relics
                          (half_box_w * 3, 0, half_box_w * 5, h),
                          (half_box_w * 5, 0, half_box_w * 7, h),
                          (0, 0, box_w, h),  # assumes 2 or 4 relics
                          (box_w, 0, box_w * 2, h),
                          (box_w * 2, 0, box_w * 3, h),
                          (box_w * 3, 0, w, h)]

        self.interval = 1

        self.skip_screenshot = debug

        self.price_csv = 'resources\\allprice.csv'
        self.ducats_csv = 'resources\\ducats.csv'
        self.primes_txt = 'resources\\primes.txt'

        # HSV bounds for getting rid of background
        self.lower = np.array([0, 0, 197])
        self.upper = np.array([180, 255, 255])

        self.prices = {}
        self.prime_dict = None
        self.ducats = {}
        self.primes = None

        self.log = None
        self.tesseract_log = None

        self.printable = set(string.printable)

        self.regex_alphabet = re.compile('[^a-zA-Z\s]')

        self.datetime_format = "%Y-%m-%d %I.%M.%S%p"
        if os.path.isdir('tesseract4win64-4.0-beta\\tessdata'):
            os.environ['TESSDATA_PREFIX'] = os.path.abspath('tesseract4win64-4.0-beta\\tessdata')

        self.gui = gui
        self.exit_now = False
        self.move_to_top = True

        self.diff_threshold = 1

        self.api = queue.Queue()
        self.ex = None

    def safe_cast(self, val, to_type, default=None):
        try:
            return to_type(val)
        except (ValueError, TypeError):
            return default

    def init(self):
        # make a dictionary of prices
        with open(self.price_csv, mode='r') as csv_file:
            reader = csv.reader(csv_file)
            next(reader)
            self.prices = {rows[0]: self.safe_cast(rows[1], int, 0) for rows in reader}
        self.prices["Forma Blueprint"] = 0

        with open(self.ducats_csv, mode='r') as csv_file:
            reader = csv.reader(csv_file)
            next(reader)
            self.ducats = {rows[0]: self.safe_cast(rows[1], int, 0) for rows in reader}
        self.ducats['Forma Blueprint'] = 0

        # make a dictionary of prime words
        with open(self.primes_txt, 'r') as f:
            self.prime_dict = [line.strip() for line in f]

        self.primes = [key for key, value in self.prices.items() if "Prime" in key and "Set" not in key]
        self.primes.append("Forma Blueprint")

        self.log = open('logs\\log.txt', 'a+')

        self.tesseract_log = open('logs\\tesseract.log', 'a+')
        if self.gui is None:
            os.system('cls')
            os.system('TITLE {}'.format(self.title))

        if self.skip_screenshot is None:
            parser = OptionParser()
            parser.add_option("-d", "--debug", action="store_true", dest="debug", default=False,
                              help="uses the current screenshot for debug purposes")
            (options, args) = parser.parse_args()
            self.skip_screenshot = options.debug
        #for i in range(len(self.crop_list)):
        #    self.api.put(PyTessBaseAPI())
        self.ex = ThreadPoolExecutor(max_workers=(len(self.crop_list)+3))

    def window_enumeration_handler(self, hwnd, top_windows):
        top_windows.append((hwnd, win32gui.GetWindowText(hwnd)))

    def bring_to_front(self):
        if self.move_to_top:
            if self.gui is None:
                top_windows = []
                win32gui.EnumWindows(self.window_enumeration_handler, top_windows)
                for i in top_windows:
                    if self.title in i[1]:
                        win32gui.ShowWindow(i[0], 5)
                        win32gui.SetForegroundWindow(i[0])
            else:
                hwnd = win32gui.FindWindow(None, self.title)
                win32gui.ShowWindow(hwnd, 5)
                win32gui.SetForegroundWindow(hwnd)

    def dict_match(self, text):
        words = text.split(" ")
        dict_words = []
        for word in words:
            close_words = difflib.get_close_matches(word, self.prime_dict, n=1)
            if len(close_words) != 0:
                dict_words.append(close_words[0])
            # else:
            #    dict_words.append('|')
        corrected = " ".join(dict_words)
        return corrected

    def set_x_offset(self, val):
        self.x_offset = val

    def set_y_offset(self, val):
        self.y_offset = val

    def set_w(self, val):
        self.w = val

    def set_h(self, val):
        self.h = val

    def set_v1(self, val):
        self.lower[2] = val

    def set_v2(self, val):
        self.upper[0] = val

    def set_interval(self, val):
        self.interval = val

    def set_move_to_top(self, val):
        self.move_to_top = val

    def set_diff_threshold(self, val):
        self.diff_threshold = val

    def screenshot(self):
        if self.skip_screenshot:
            return cv2.imread(self.screenshot_name)
        hwnd = None
        while not hwnd:
            hwnd = win32gui.FindWindow(None, self.window_name)
            if not hwnd:
                return cv2.imread(self.screenshot_name)
        rect = win32gui.GetWindowRect(hwnd)
        x = rect[0]
        y = rect[1]
        warframe_w = rect[2]-x
        warframe_h = rect[3]-y
        if self.gui is not None and (warframe_w != self.warframe_w or warframe_h != self.warframe_h):
            self.gui.set_sliders_range(warframe_w, warframe_h)
            self.warframe_h = warframe_h
            self.warframe_w = warframe_w

        top = self.y_offset + y
        left = self.x_offset + x
        wDC = win32gui.GetWindowDC(hwnd)
        dcObj = win32ui.CreateDCFromHandle(wDC)
        cDC = dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj, self.w, self.h)

        # make sure values don't change while taking screenshot
        w = self.w
        h = self.h
        cDC.SelectObject(dataBitMap)
        cDC.BitBlt((0, 0), (w, h), dcObj, (left, top), win32con.SRCCOPY)

        # make numpy img
        bmpRGB = dataBitMap.GetBitmapBits(True)
        img = np.frombuffer(bmpRGB, dtype='uint8')
        img.shape = (h, w, 4)

        # Free Resources
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())

        return cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)

    def save_screenshot(self):
        screenshot = self.screenshot()
        cv2.imwrite(self.screenshot_name, screenshot)

    def filter_img(self, img):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower, self.upper)

        return mask

    def title_case(self, input_str):
        return string.capwords(input_str.lower())

    def sanitize(self, input_str):
        return self.regex_alphabet.sub('', input_str)

    def read_box(self, crop, filtered, read_primes, text, table, old_read_primes, num):
        cur_time = datetime.now().strftime(self.datetime_format)
        #print("reading box")
        api = None
        try:
            api = self.api.get(block=False)
            #print("reading box")
        except queue.Empty:
            api = PyTessBaseAPI()

        api.SetImage(Image.fromarray(filtered[crop[1]:crop[3], crop[0]:crop[2]]))
        ocr_output = api.GetUTF8Text()
        self.api.put(api)
        #self.log.write("{}: Succeeded reading image x={} num_api={}\n".format(cur_time, crop[0], self.api.qsize()))
        #self.log.flush()

        sanitized = self.sanitize(ocr_output)
        ocr_text = self.title_case(sanitized)
        #self.log.write("{}: ocr text={}\n".format(cur_time, ocr_text))
        text[crop[0] + crop[1]] = ocr_text
        dict_text = self.dict_match(ocr_text)
        self.update_table(dict_text, table, read_primes, old_read_primes)

    def update_table(self, ocr_text, table, read_primes, old_read_primes):
        for p in self.primes:
            if p in ocr_text:
                if p not in read_primes:
                    read_primes.append(p)
                    if len(old_read_primes) == 0:
                        row = [p, self.prices[p], self.ducats.get(p, 0)]
                        self.bring_to_front()
                        if self.gui is not None:
                            self.gui.insert_table_row(row)
                            #self.gui.select_max()
                        else:
                            table.add_row(row)
                            os.system('cls')
                            print(table)

    def image_identical(self, img1, img2):
        try:
            diff = cv2.subtract(img1, img2)
            return diff.mean() < self.diff_threshold
        except:
            return False

    def read_screen(self, old_read_primes, old_filtered):
        screenshot_img = self.screenshot()
        filtered = self.filter_img(screenshot_img)

        if self.gui is not None:
            self.ex.submit(self.gui.update_screenshot, screenshot_img)
            self.ex.submit(self.gui.update_filtered, filtered)
        if self.image_identical(filtered, old_filtered):
            return old_read_primes.copy(), filtered

        start = datetime.now()
        cur_time = start.strftime(self.datetime_format)

        # make formatted table
        table = PrettyTable()
        table.field_names = ['Prime', 'Plat', 'Ducats']
        table.sortby = 'Plat'

        read_primes = []
        text = {}

        # surround in try catch since threads don't receive keyboard interrupts
        i = 0
        for crop in self.crop_list:
            #self.ex.submit(self.read_box, crop, filtered, read_primes, text, table, old_read_primes, i)
            self.read_box(crop, filtered, read_primes, text, table, old_read_primes, i)
            i += 1

        # use this to find slient crashes
        # i = 0
        #for crop in self.crop_list:
        #    self.read_box(crop, filtered, read_primes, text, table, old_read_primes, i)
        #    i += 1
        # read_primes.sort()

        if len(read_primes) == 0 and len(old_read_primes) != 0:
            if self.gui is not None:
                self.gui.clear_table()
            else:
                os.system('cls')
        if read_primes != old_read_primes:
            if len(read_primes) != 0:
                if not self.skip_screenshot:
                    cv2.imwrite('screenshots/{}.bmp'.format(cur_time), screenshot_img)
                end = datetime.now()
                duration = (end - start).total_seconds()
                self.log.write("{}: OCR='{}' Primes={} duration={}s\n".format(cur_time, text, read_primes, duration))
                self.log.flush()
        return read_primes, filtered

    def main(self):
        self.init()
        old_read_primes = []
        old_filtered = 0
        while not self.exit_now:
            start = datetime.now()
            old_read_primes, old_filtered = self.read_screen(old_read_primes, old_filtered)
            end = datetime.now()
            duration = (end - start).total_seconds()
            if duration < self.interval:
                time.sleep(self.interval - duration)


if __name__ == '__main__':
    ocr = OCR()
    ocr.main()
