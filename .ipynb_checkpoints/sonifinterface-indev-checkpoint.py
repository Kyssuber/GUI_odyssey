'''
Layout adopted from https://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter/7557028#7557028
'''

import tkinter as tk
import numpy as np
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import pyplot as plt
from astropy.io import fits
from astropy.wcs import WCS
from tkinter import font as tkFont
from tkinter import messagebox
from tkinter import filedialog

homedir = os.getenv('HOME')

#create main window container, into which the first page will be placed.
class App(tk.Tk):
    
    def __init__(self, *args, **kwargs):          #INITIALIZE; will always run when App class is called.
        tk.Tk.__init__(self, *args, **kwargs)     #initialize tkinter; args are parameter arguments, kwargs can be dictionary arguments
        
        self.title('Sample Tkinter Structuring')
        self.geometry('1000x700')
        self.resizable(True,True)
        self.rowspan=10
        
        #will be filled with heaps of frames and frames of heaps. 
        container = tk.Frame(self)
        container.pack(side='top', fill='both', expand=True)     #fills entire container space
        container.grid_rowconfigure(0,weight=1)
        container.grid_columnconfigure(0,weight=1)

        ## Initialize Frames
        self.frames = {}     #empty dictionary
        frame = MainPage(container, self)   #define frame  
        self.frames[MainPage] = frame     #assign new dictionary entry {MainPage: frame}
        frame.grid(row=0,column=0,sticky='nsew')   #define where to place frame within the container...CENTER!
        for i in range(self.rowspan):
            frame.columnconfigure(i, weight=1)
            frame.rowconfigure(i, weight=1)
        
        self.show_frame(MainPage)  #a method to be defined below (see MainPage class)
    
    def show_frame(self, cont):     #'cont' represents the controller, enables switching between frames/windows...I think.
        frame = self.frames[cont]
        frame.tkraise()   #will raise window/frame to the 'front;' if there is more than one frame, quite handy.
        
        
#inherits all from tk.Frame; will be on first window
class MainPage(tk.Frame):    
    
    def __init__(self, parent, controller):
        
        #defines the number of rows/columns to resize when resizing the entire window.
        self.rowspan=10
        
        #define a font
        self.helv20 = tkFont.Font(family='Helvetica', size=20, weight='bold')
        
        self.textbox="GOAL: Interact with and generate a 2D sonified galaxy cutout. \n"
        
        #first frame...
        tk.Frame.__init__(self,parent)
        
        #create display frame, which will hold the canvas and a few button widgets underneath.
        self.frame_display=tk.LabelFrame(self,text='Display',font='Vendana 15',padx=5,pady=5)
        self.frame_display.grid(row=0,column=0,rowspan=5)
        for i in range(self.rowspan):
            self.frame_display.columnconfigure(i, weight=1)
            self.frame_display.rowconfigure(i, weight=1)
        
        #create buttons frame, which currently only holds the 'save' button and entry box.
        self.frame_buttons=tk.LabelFrame(self,text='File Browser',padx=5,pady=5)
        self.frame_buttons.grid(row=2,column=1)
        for i in range(self.rowspan):
            self.frame_buttons.columnconfigure(i, weight=1)
            self.frame_buttons.rowconfigure(i, weight=1)
            
        #create coord frame, which holds the event labels for the mean pixel value.
        self.frame_value=tk.LabelFrame(self,padx=5,pady=5)
        self.frame_value.grid(row=3,column=1,sticky='se')
        for i in range(self.rowspan):
            self.frame_value.columnconfigure(i, weight=1)
            self.frame_value.rowconfigure(i, weight=1)
        
        self.galaxy_to_display()
        '''
        INSERT FUNCTIONS TO RUN HERE.
        '''
        self.initiate_vals()
        self.add_info_button()
        
    def initiate_vals(self):
        self.val = tk.Label(self.frame_value,text='Pixel Value: ',font='Ariel 20')
        self.val.grid(row=0,column=0)
    
    def galaxy_to_display(self):
        self.path_to_im = tk.Entry(self.frame_buttons, width=35, borderwidth=2, bg='black', fg='lime green', font='Arial 20')
        self.path_to_im.insert(0,'enter path/to/image.fits')
        self.path_to_im.grid(row=0,column=0,columnspan=2)
        self.add_browse_button()
        self.add_enter_button()

    def add_info_button(self):
        self.info_button = tk.Button(self.frame_display, text='Click for Info', padx=15, pady=10, font='Ariel 20', command=self.popup)
        self.info_button.grid(row=4,column=1)
    
    def add_browse_button(self):
        self.button_explore = tk.Button(self.frame_buttons ,text="Browse", padx=20, pady=10, font=self.helv20, command=self.browseFiles)
        self.button_explore.grid(row=1,column=0)
        
    def add_enter_button(self):
        self.path_button = tk.Button(self.frame_buttons, text='Enter', padx=20, pady=10, font=self.helv20, command=self.initiate_canvas)
        self.path_button.grid(row=1,column=1)
    
    def initiate_canvas(self):
        self.dat = fits.getdata(str(self.path_to_im.get()))
        plt.figure(figsize=(5,5))
        self.im=plt.imshow(self.dat,origin='lower')
        plt.title(self.path_to_im.get(),fontsize=10)
        self.im_length = np.shape(self.dat)[0]
        self.current_bar=plt.scatter(np.linspace(self.im_length/2,self.im_length/2,100),
                               np.linspace(self.im_length/2-(0.25*self.im_length),self.im_length/2+(0.25*self.im_length),100),
                               s=3,color='None')
        self.canvas = FigureCanvasTkAgg(plt.gcf(), master=self.frame_display)    
        self.canvas.mpl_connect('button_press_event', self.placeBar)
        #add canvas 'frame'
        self.label = self.canvas.get_tk_widget()
        self.label.grid(row=0,column=0,columnspan=3,rowspan=6)
    
    #create command function to print info popup message
    def popup(self):
        messagebox.showinfo('Unconventional README.md',self.textbox)
    
    def placeBar(self, event):  
        x=event.xdata
        #if user clicks outside the image bounds, then x is NoneType. y cannot be None, by design. only need to check x.
        if x is not None:
            #re-plot bar
            line_x = np.zeros(100)+x
            line_y = np.linspace(self.im_length/2-(0.25*self.im_length),self.im_length/2+(0.25*self.im_length),100)       
            self.current_bar.remove()
            self.current_bar = plt.scatter(line_x,line_y,s=3,color='red')
            
            #extract the mean pixel value from this bar
            value_list = np.zeros(100)
            for index in range(100):
                y_coord = line_y[index]
                px_value = self.dat[int(y_coord)][int(x)]   #x will be the same...again, by design.
                value_list[index] = px_value
            mean_px = round(np.mean(value_list),3)
            self.val.config(text=f'Pixel Value: {mean_px}',font='Ariel 16')
            self.canvas.draw()
            
        else:
            print('Click inside of the image!')
            self.val.config(text='Pixel Value: None', font='Ariel 16')
    
    # Function for opening the file explorer window
    def browseFiles(self):
        filename = filedialog.askopenfilename(initialdir = "/Users/k215c316/vf_html/all_input_fits/", title = "Select a File", filetypes = ([("FITS Files", ".fits")]))
        self.path_to_im.delete(0,tk.END)
        self.path_to_im.insert(0,filename)        
        
if __name__ == "__main__":
    app = App()
    app.mainloop()
    app.destroy()