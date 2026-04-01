#!/usr/bin/python3
import sys
import argparse
import random
import usb
from .elc import *
from .elc_constants import *


DURATION_MAX = 0xffff
DURATION_BATTERY_LOW = 0xff
DURATION_MIN = 0x00
TEMPO_MAX = 0xff
TEMPO_MIN = 0x01
ZONES = [0, 1, 2, 3]
ZONES_KB = [0, 1, 2]
ZONES_NP = [3]

def init_device():
    supportedProducts = [0x0550, 0x0551]
    vid = 0x187C

    # Find supported device
    device = None
    for pid in supportedProducts:
        device = usb.core.find(idVendor=vid, idProduct=pid)
        if device:
            break

    if not device:
        raise Exception('No supported device was found. Do you have an RGB keyboard 187c:0550 or 187c:0551?')

    ep = device[0].interfaces()[0].endpoints()[0]
    i = device[0].interfaces()[0].bInterfaceNumber
    device.reset()
    if device.is_kernel_driver_active(i):
        device.detach_kernel_driver(i)

    # Create the elc object
    elc = Elc(vid, device.idProduct, debug=0)
    return (elc, device)

def apply_action(elc, red, green, blue, duration, tempo, animation=AC_CHARGING, effect=COLOR, zones=ZONES):
    if (effect == COLOR):
        elc.remove_animation(animation)
        elc.start_new_animation(animation)
        elc.start_series(zones)
        # Static color, 2 second duration, tempo tempo (who cares?)
        elc.add_action((Action(effect, duration, tempo, red, green, blue),))
        elc.finish_save_animation(animation)
        elc.set_default_animation(animation)
    else:  # Then, effect is morph.
        elc.remove_animation(animation)
        elc.start_new_animation(animation)
        elc.start_series(zones)
        elc.add_action((Action(MORPH, duration, tempo, red, green, blue), Action(MORPH, duration, tempo, green,
                       blue, red), Action(MORPH, duration, tempo, blue, red, green)))  # Morph based on given values.
        elc.finish_save_animation(animation)
        elc.set_default_animation(animation)

def apply_action_color_and_morph(elc, red, green, blue, red_morph, green_morph, blue_morph, duration, tempo, animation=AC_CHARGING):
    elc.remove_animation(animation)
    elc.start_new_animation(animation)
    elc.start_series(ZONES_NP)
    elc.add_action((Action(MORPH, duration, tempo, red_morph, green_morph, blue_morph),Action(MORPH, duration, tempo, green_morph, blue_morph, red_morph),Action(MORPH, duration, tempo, blue_morph, red_morph, green_morph)))
    # elc.finish_save_animation(animation)
    
    # elc.start_new_animation(animation)
    elc.start_series(ZONES_KB)
    elc.add_action((Action(COLOR, duration, tempo, red, green, blue),))
    elc.finish_save_animation(animation)

    elc.set_default_animation(animation)


def battery_flashing(elc):
    # Red flashing on battery low.
    elc.remove_animation(DC_LOW)
    elc.start_new_animation(DC_LOW)
    elc.start_series(ZONES)
    # Static color, 2 second duration, tempo tempo (who cares?)
    elc.add_action(
        (Action(COLOR, DURATION_BATTERY_LOW, TEMPO_MIN, 255, 0, 0),))
    # Static color, 2 second duration, tempo tempo (who cares?)
    elc.add_action((Action(COLOR, DURATION_BATTERY_LOW, TEMPO_MIN, 0, 0, 0),))
    elc.finish_save_animation(DC_LOW)
    elc.set_default_animation(DC_LOW)

def set_static(red, green, blue):
    set_dim(0)
    elc, device = init_device()
    apply_action(elc, 0, 0, 0, DURATION_MAX, TEMPO_MIN,
                 AC_SLEEP, COLOR)       # Off on AC Sleep
    apply_action(elc, red, green, blue, DURATION_MAX, TEMPO_MIN,
                 AC_CHARGED, COLOR)     # Full brightness on AC, charged
    apply_action(elc, red, green, blue, DURATION_MAX, TEMPO_MIN,
                 AC_CHARGING, COLOR)    # Full brightness on AC, charging
    apply_action(elc, 0, 0, 0, DURATION_MAX, TEMPO_MIN,
                 DC_SLEEP, COLOR)       # Off on DC Sleep
    apply_action(elc, int(red/2), int(green/2), int(blue/2), DURATION_MAX, TEMPO_MIN,
                 DC_ON, COLOR)          # Half brightness on Battery
    battery_flashing(elc)  # Red flashing on battery low.
    # apply_action(elc, 0, 0, 0, 0, 0,
    #              DEFAULT_POST_BOOT, COLOR)       # Off on post-boot
    # apply_action(elc, 0, 0, 0, 0, 0,
    #              RUNNING_START, COLOR)           # Off on start
    # apply_action(elc, 0, 0, 0, 0, 0,
    #              RUNNING_FINISH, COLOR)          # Off on finish
    device.reset()

def set_morph(red, green, blue, duration):
    set_dim(0)
    elc, device = init_device()
    apply_action(elc, 0, 0, 0, DURATION_MAX, TEMPO_MIN,
                 AC_SLEEP, COLOR)       # Off on AC Sleep
    apply_action(elc, red, green, blue, duration, TEMPO_MIN,
                 AC_CHARGED, MORPH)     # Full brightness on AC, charged
    apply_action(elc, red, green, blue, duration, TEMPO_MIN,
                 AC_CHARGING, MORPH)    # Full brightness on AC, charging
    apply_action(elc, 0, 0, 0, DURATION_MAX, TEMPO_MIN,
                 DC_SLEEP, COLOR)       # Off on DC Sleep
    apply_action(elc, int(red/2), int(green/2), int(blue/2), duration, TEMPO_MIN,
                 DC_ON, MORPH)          # Half brightness on Battery
    battery_flashing(elc)  # Red flashing on battery low.
    # apply_action(elc, 0, 0, 0, 0, 0,
    #              DEFAULT_POST_BOOT, COLOR)       # Off on post-boot
    # apply_action(elc, 0, 0, 0, 0, 0,
    #              RUNNING_START, COLOR)           # Off on start
    # apply_action(elc, 0, 0, 0, 0, 0,
    #              RUNNING_FINISH, COLOR)          # Off on finish
    device.reset()

def set_color_and_morph(red, green, blue,red_morph, green_morph, blue_morph, duration):
    set_dim(0)
    elc, device = init_device()
    #Set static color on keyboard, and morph on numpad
    apply_action_color_and_morph(elc, 0, 0, 0, 0, 0, 0, DURATION_MAX, TEMPO_MIN,
                 AC_SLEEP)       # Off on AC Sleep
    apply_action_color_and_morph(elc, red, green, blue, red_morph, green_morph, blue_morph, duration, TEMPO_MIN,
                 AC_CHARGED)     # Full brightness on AC, charged
    apply_action_color_and_morph(elc, red, green, blue, red_morph, green_morph, blue_morph, duration, TEMPO_MIN,
                 AC_CHARGING)    # Full brightness on AC, charging
    apply_action_color_and_morph(elc,0, 0, 0, 0, 0, 0, DURATION_MAX, TEMPO_MIN,
                 DC_SLEEP)       # Off on DC Sleep
    apply_action_color_and_morph(elc, int(red/2), int(green/2), int(blue/2), int(red_morph/2), int(green_morph/2), int(blue_morph/2), duration, TEMPO_MIN,
                 DC_ON)          # Half brightness on Battery
    battery_flashing(elc)  # Red flashing on battery low.
    device.reset()

def remove_animation():
    try:
        set_dim(100)
        elc, device = init_device()
        for animation in (AC_SLEEP, AC_CHARGED, AC_CHARGING, DC_SLEEP, DC_ON, DC_LOW):
            try:
                elc.remove_animation(animation)
            except usb.core.USBError:
                break

        seen_animation_ids = set()
        for _ in range(8):
            try:
                animations = elc.get_animation_count()
            except usb.core.USBError:
                break

            if animations == (0, 0):
                break

            unknown_animation = animations[1]
            if unknown_animation in (0, None) or unknown_animation in seen_animation_ids:
                break

            seen_animation_ids.add(unknown_animation)
            try:
                elc.remove_animation(unknown_animation)
            except usb.core.USBError:
                break

        try:
            device.reset()
        except usb.core.USBError:
            pass
    except usb.core.USBError:
        pass

def set_dim(level):
    elc, device = init_device()
    elc.dim(ZONES,level)
    device.reset()
