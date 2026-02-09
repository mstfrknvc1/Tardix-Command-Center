import tkinter as tk

from math import cos, sin, pi, atan2

def rgb_from_angle(angle):
    """Açıyı RGB değerine çevir"""
    r = int((cos(angle) + 1) * 127)
    g = int((cos(angle - 2*pi/3) + 1) * 127)
    b = int((cos(angle - 4*pi/3) + 1) * 127)
    return r, g, b

def click(event):
    x, y = event.x - 150, event.y - 150
    angle = (pi + (pi + -1*atan2(y, x))) % (2*pi)
    r, g, b = rgb_from_angle(angle)
    color = f'#{r:02x}{g:02x}{b:02x}'
    label.config(text=f'Seçilen renk: {color}', bg=color)

root = tk.Tk()
root.title("RGB Renk Tekerleği")

canvas = tk.Canvas(root, width=300, height=300)
canvas.pack()

# Renk çarkını çiz
for i in range(360):
    angle1 = i * pi / 180
    angle2 = (i+1) * pi / 180
    r, g, b = rgb_from_angle(angle1)
    color = f'#{r:02x}{g:02x}{b:02x}'
    canvas.create_arc(0, 0, 300, 300, start=i, extent=1, style=tk.PIESLICE, fill=color, outline='')

canvas.bind("<Button-1>", click)

label = tk.Label(root, text="Henüz renk seçilmedi", width=30, height=2)
label.pack(pady=10)

root.mainloop()
