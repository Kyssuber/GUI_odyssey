#!/usr/bin/env python3

'''
Goal: create GUI plot canvas of NGC3364. Contains three 'default' color scheme button widgets in order to manipulate the data's appearance (viridis, rainbow, gray).
'''

import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from astropy.io import fits

import os
homedir=os.getenv("HOME")

#create GUI window
root = tk.Tk()

data = plt.imshow(fits.getdata(homedir+'/Desktop/maskies_ngc3364/NGC3364-custom-image-W3.fits'),origin='lower')

#plt.gcf() --> get current figure
canvas = FigureCanvasTkAgg(plt.gcf(), master=root)

change_colormap_rain = lambda: (data.set_cmap('rainbow'), canvas.draw())
change_colormap_gray = lambda: (data.set_cmap('gray'), canvas.draw())
change_colormap_viridis = lambda: (data.set_cmap('viridis'), canvas.draw())

tk.Button(master=root, text='rainbow',command=change_colormap_rain, foreground='#FF1493', height=2, width=8).place(relx=0.13,rely=0.15)
tk.Button(master=root, text='viridis',command=change_colormap_viridis, foreground='#FF1493', height=2, width=8).place(relx=0.13,rely=0.21)
tk.Button(master=root, text='gray',command=change_colormap_gray, foreground='#FF1493', height=2, width=8).place(relx=0.13,rely=0.09)

#entry widget...to enter data.
e = tk.Entry(root, width=35, borderwidth=5, bg='black',fg='lime green')
e.place(relx=0.36,rely=0.05)

change_colormap_manual = lambda: (data.set_cmap(e.get()), canvas.draw())
tk.Button(root, text='Set Manual Color Scheme', highlightbackground='white', command=change_colormap_manual).place(relx=0.42,rely=0.1)

tk.Button(master=root, text="Quit",command=root.quit,foreground='black',highlightbackground='purple').pack(side='top')

canvas.get_tk_widget().pack(fill='both', expand=1)

if __name__ == '__main__':
    root.mainloop()
    root.destroy()
