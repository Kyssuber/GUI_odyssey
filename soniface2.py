'''
Class layout adapted from 
https://stackoverflow.com/questions/7546050/switch-between-two-frames-in-tkinter/7557028#7557028
'''

from midi2audio import FluidSynth
from midiutil import MIDIFile
from audiolazy import str2midi
from pygame import mixer                    #this library is what causes the loading delay methinks

import tkinter as tk
import numpy as np
import os
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

#from matplotlib import pyplot as plt      #don't use, since closing GUI doesn't close pyplot!
                                           #this does add a bit more clunkiness to the code, however.
                                           #I did not create the rules. do not sue me.

from matplotlib import figure              #see self.fig, self.ax.

import matplotlib                          #I need this for matplotlib.use. sowwee.
matplotlib.use('TkAgg')                    #strange error messages will appear otherwise.

from scipy.stats import scoreatpercentile
from scipy import spatial
from astropy.visualization import simple_norm
from astropy.io import fits
from astropy.wcs import WCS
from tkinter import font as tkFont
from tkinter import messagebox
from tkinter import filedialog
import glob

import sys
from io import BytesIO

homedir = os.getenv('HOME')

#create main window container, into which the first page will be placed.
class App(tk.Tk):
    
    def __init__(self, *args, **kwargs):          #INITIALIZE; will always run when App class is called.
        tk.Tk.__init__(self, *args, **kwargs)     #initialize tkinter; args are parameter arguments, kwargs can be dictionary arguments
        
        self.title('MIDI-chlorians: Sonification of Nearby Galaxies')
        self.geometry('980x600')
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
        self.create_menubar()      #FOR MAC USERS: WILL APPEAR ON THE *MAC MENUBAR*, NOT THE TK WINDOW.
    
    def create_menubar(self):
        
        self.menu = tk.Menu(self)

        self.filemenu = tk.Menu(self.menu, tearoff=0)
        self.filemenu.add_command(label='Load FITS file', command=self.popup_loadfits)
        self.filemenu.add_command(label='Sonification Features', command=self.popup_sonifeat)
        self.filemenu.add_command(label='Defining a Region', command=self.popup_rectline)
        self.filemenu.add_command(label='Save .wav', command=self.popup_wav)
        self.filemenu.add_command(label='Save .mp4', command=self.popup_mp4)
        self.filemenu.add_separator()
        self.filemenu.add_command(label='Exit Program', command=self.quit)
        self.menu.add_cascade(label='Help',menu=self.filemenu)
        
        self.config(menu=self.menu)
    #IN PLACE OF THIS, CREATE MULTIPLE POPUP TEXTBOX FUNCTIONS THAT DESCRIBE EACH LABEL. THIS WILL SERVE AS THE 'WRITTEN TUTORIAL' OF THE GUI. Once I record a proper video, I might also link the youtube address to each textboxes. and rather than type all text content here, I'll just create a few .txt files in the folder.
    def popup_loadfits(self):
        self.textbox1 = open(homedir+'/github/GUI_odyssey/readme_files/loadfits.txt','r').read()
        messagebox.showinfo('How to Load a FITS File',self.textbox1)
    
    def popup_sonifeat(self):
        self.textbox2 = open(homedir+'/github/GUI_odyssey/readme_files/sonifeat.txt','r').read()
        messagebox.showinfo('Sonification Features',self.textbox2)
    
    def popup_rectline(self):
        self.textbox3 = open(homedir+'/github/GUI_odyssey/readme_files/rectline.txt').read()
        messagebox.showinfo('Constraining Sonification Area',self.textbox3)
    
    def popup_wav(self):
        self.textbox4 = open(homedir+'/github/GUI_odyssey/readme_files/howtowav.txt').read()
        messagebox.showinfo('Save Sound as WAV File',self.textbox4)
    
    def popup_mp4(self):
        self.textbox5 = open(homedir+'/github/GUI_odyssey/readme_files/howtomp4.txt').read()
        messagebox.showinfo('Save Sound (with Animation!) as MP4 File',self.textbox5)
    
    def show_frame(self, cont):     #'cont' represents the controller, enables switching between frames/windows...I think.
        frame = self.frames[cont]
        frame.tkraise()   #will raise window/frame to the 'front;' if there is more than one frame, quite handy.
        
        
#inherits all from tk.Frame; will be on first window
class MainPage(tk.Frame):    
    
    def __init__(self, parent, controller):
        
        #these variables will apply to the self.drawSq function, if the user desires to use it.
        self.bound_check=None
        self.x1=None
        self.x2=None
        self.y1=None
        self.y2=None
        self.angle=0
        
        #initiate a counter to ensure that files do not overwrite one another for an individual galaxy
        #note: NEEDED FOR THE SAVE WIDGET
        self.namecounter=0
                
        #dictionary for different key signatures
        
        self.note_dict = {
           'C Major': 'C2-D2-E2-F2-G2-A2-B2-C3-D3-E3-F3-G3-A3-B3-C4-D4-E4-F4-G4-A4-B4-C5-D5-E5-F5-G5-A5-B5',
           'G Major': 'G2-A2-B2-C2-D2-E2-F#2-G3-A3-B3-C3-D3-E3-F#3-G4-A4-B4-C4-D4-E4-F#4-G5-A5-B5-C5-D5-E5-F#5',
           'D Major': 'D2-E2-F#2-G2-A2-B2-C#2-D3-E3-F#3-G3-A3-B3-C#3-D4-E4-F#4-G4-A4-B4-C#4-D5-E5-F#5-G5-A5-B5-C#5',
           'A Major': 'A2-B2-C#2-D2-E2-F#2-G#2-A3-B3-C#3-D3-E3-F#3-G#3-A4-B4-C#4-D4-E4-F#4-G#4-A5-B5-C#5-D5-E5-F#5-G#5',
           'E Major': 'E2-F#2-G#2-A2-B2-C#2-D#2-E3-F#3-G#3-A3-B3-C#3-D#3-E4-F#4-G#4-A4-B4-C#4-D#4-E5-F#5-G#5-A5-B5-C#5-D#5',
           'B Major': 'B2-C#2-D#2-E2-F#2-G#2-A#2-B3-C#3-D#3-E3-F#3-G#3-A#3-B4-C#4-D#4-E4-F#4-G#4-A#4-B5-C#5-D#5-E5-F#5-G#5-A#5',
           'F# Major': 'F#2-G#2-A#2-B2-C#2-D#2-E#2-F#3-G#3-A#3-B3-C#3-D#3-E#3-F#4-G#4-A#4-B4-C#4-D#4-E#4-F#5-G#5-A#5-B5-C#5-D#5-E#5', 
           'Gb Major': 'Gb2-Ab2-Bb2-Cb2-Db2-Eb2-F2-Gb3-Ab3-Bb3-Cb3-Db3-Eb3-F3-Gb4-Ab4-Bb4-Cb4-Db4-Eb4-F4-Gb5-Ab5-Bb5-Cb5-Db5-Eb5-F5',
           'Db Major': 'Db2-Eb2-F2-Gb2-Ab2-Bb2-C2-Db3-Eb3-F3-Gb3-Ab3-Bb3-C3-Db4-Eb4-F4-Gb4-Ab4-Bb4-C4-Db5-Eb5-F5-Gb5-Ab5-Bb5-C5',
           'Ab Major': 'Ab2-Bb2-C2-Db2-Eb2-F2-G2-Ab3-Bb3-C3-Db3-Eb3-F3-G3-Ab4-Bb4-C4-Db4-Eb4-F4-G4-Ab5-Bb5-C5-Db5-Eb5-F5-G5', 
           'Eb Major': 'Eb2-F2-G2-Ab2-Bb2-C2-D2-Eb3-F3-G3-Ab3-Bb3-C3-D3-Eb4-F4-G4-Ab4-Bb4-C4-D4-Eb5-F5-G5-Ab5-Bb5-C5-D5',
           'Bb Major': 'Bb2-C2-D2-Eb2-F2-G2-A2-Bb3-C3-D3-Eb3-F3-G3-A3-Bb4-C4-D4-Eb4-F4-G4-A4-Bb5-C5-D5-Eb5-F5-G5-A5',
           'F Major': 'F2-G2-A2-Bb2-C2-D2-E2-F3-G3-A3-Bb3-C3-D3-E3-F4-G4-A4-Bb4-C4-D4-E4-F5-G5-A5-Bb5-C5-D5-E5', 
        }
        
        #isolate the key signature names --> need for the dropdown menu
        self.keyvar_options=list(self.note_dict.keys())

        self.keyvar = tk.StringVar()
        self.keyvar.set(self.keyvar_options[2])
        
        #defines the number of rows/columns to resize when resizing the entire window.
        self.rowspan=10
        
        #define a font
        self.helv20 = tkFont.Font(family='Helvetica', size=20, weight='bold')
        
        self.textbox="In progress."
        
        #first frame...
        tk.Frame.__init__(self,parent)
        
        #NOTE: columnconfigure and rowconfigure below enable the minimization and maximization of window to also affect widget size
        
        #create frame for save widgets...y'know, to generate the .wav and HOPEFULLY the .mp4 (pending as of January 23, 2024. if the save .mp4 widget appears on the GUI, then my efforts bore fruits and I simply forgot to delete this comment)
        self.frame_save=tk.LabelFrame(self,text='Save Files',padx=5,pady=5)
        self.frame_save.grid(row=4,column=1,columnspan=5)
        for i in range(self.rowspan):
            self.frame_save.columnconfigure(i,weight=1)
            self.frame_save.rowconfigure(i,weight=1)
        
        #create display frame, which will hold the canvas and a few button widgets underneath.
        self.frame_display=tk.LabelFrame(self,text='Display',font='Vendana 15',padx=5,pady=5)
        self.frame_display.grid(row=0,column=0,rowspan=9)
        for i in range(self.rowspan):
            self.frame_display.columnconfigure(i, weight=1)
            self.frame_display.rowconfigure(i, weight=1)
        
        #create buttons frame, which currently only holds the 'save' button, 'browse' button, and entry box.
        self.frame_buttons=tk.LabelFrame(self,text='File Browser',padx=5,pady=5)
        self.frame_buttons.grid(row=0,column=1,columnspan=2)
        for i in range(self.rowspan):
            self.frame_buttons.columnconfigure(i, weight=1)
            self.frame_buttons.rowconfigure(i, weight=1)
            
        #create soni frame, which holds the event button for converting data into sound (midifile).
        #there are also heaps of text boxes with which the user can manipulate the sound conversion parameters
        self.frame_soni=tk.LabelFrame(self,text='Parameters (Click "Sonify" to play)',padx=5,pady=5)
        self.frame_soni.grid(row=8,column=2,sticky='se')
        for i in range(self.rowspan):
            self.frame_soni.columnconfigure(i, weight=1)
            self.frame_soni.rowconfigure(i, weight=1)
        
        '''
        #create value frame, which holds the event labels for the mean pixel value.
        self.frame_value=tk.LabelFrame(self,padx=5,pady=5)
        self.frame_value.grid(row=4,column=2,sticky='se')
        for i in range(self.rowspan):
            self.frame_value.columnconfigure(i, weight=1)
            self.frame_value.rowconfigure(i, weight=1)
        '''
        
        #create box frame --> check boxes for lines vs. squares when interacting with the figure canvas
        self.frame_box = tk.LabelFrame(self,text='Change Rectangle Angle',padx=5,pady=5)
        self.frame_box.grid(row=8,column=1,sticky='s')
        for i in range(self.rowspan):
            self.frame_box.columnconfigure(i, weight=1)
            self.frame_box.rowconfigure(i, weight=1)
        
        self.galaxy_to_display()
        '''
        INSERT INITIATION FUNCTIONS TO RUN HERE.
        '''
        self.initiate_vals()
        self.add_info_button()
        self.populate_soni_widget()
        self.populate_box_widget()
        self.populate_save_widget()
        self.init_display_size()
    
    def populate_box_widget(self):
        self.angle_box = tk.Entry(self.frame_box, width=15, borderwidth=2, bg='black', fg='lime green',
                                  font='Arial 20')
        self.angle_box.insert(0,'Rotation angle (deg)')
        self.angle_box.grid(row=0,column=0,columnspan=5)
        self.add_angle_buttons()
    
    def initiate_vals(self):
        self.var = tk.IntVar()
        #self.val = tk.Label(self.frame_value,text='Mean Pixel Value: ',font='Arial 18')
        #self.val.grid(row=1,column=0)
        #self.line_check = tk.Checkbutton(self.frame_value,text='Switch to Lines',
        #                                 onvalue=1,offvalue=0,command=self.change_canvas_event,
        #                                 variable=self.var,font='Arial 15')
        #self.line_check.grid(row=0,column=0)
        self.val = tk.Label(self.frame_display,text='Mean Pixel Value: ',font='Arial 18')
        self.val.grid(row=8,column=2,padx=1,pady=(3,1),sticky='e')
        self.line_check = tk.Checkbutton(self.frame_display,text='Switch to Lines',
                                         onvalue=1,offvalue=0,command=self.change_canvas_event,
                                         variable=self.var,font='Arial 18')
        self.line_check.grid(row=9,column=2,padx=1,pady=(3,1),sticky='e')
    
    def galaxy_to_display(self):
        self.path_to_im = tk.Entry(self.frame_buttons, width=35, borderwidth=2, bg='black', fg='lime green', 
                                   font='Arial 20')
        self.path_to_im.insert(0,'Type path/to/image.fits or click "Browse"')
        self.path_to_im.grid(row=0,column=0,columnspan=2)
        self.add_browse_button()
        self.add_enter_button()
    
    def populate_save_widget(self):
        self.add_save_button()
        return
    
    def populate_soni_widget(self):
        
        self.add_midi_button()
        
        #create all entry textboxes (with labels and initial values), midi button
        
        ylab = tk.Label(self.frame_soni,text='yscale').grid(row=0,column=0)
        self.y_scale_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', 
                                      font='Arial 15')
        self.y_scale_entry.insert(0,'0.5')
        self.y_scale_entry.grid(row=0,column=1,columnspan=1)
        
        vmin_lab = tk.Label(self.frame_soni,text='Min Velocity').grid(row=1,column=0)
        self.vel_min_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', 
                                      font='Arial 15')
        self.vel_min_entry.insert(0,'10')
        self.vel_min_entry.grid(row=1,column=1,columnspan=1)
        
        vmax_lab = tk.Label(self.frame_soni,text='Max Velocity').grid(row=2,column=0)
        self.vel_max_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', 
                                      font='Arial 15')
        self.vel_max_entry.insert(0,'100')
        self.vel_max_entry.grid(row=2,column=1,columnspan=1)
        
        bpm_lab = tk.Label(self.frame_soni,text='BPM').grid(row=3,column=0)
        self.bpm_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', 
                                  font='Arial 15')
        self.bpm_entry.insert(0,'35')
        self.bpm_entry.grid(row=3,column=1,columnspan=1)
        
        xminmax_lab = tk.Label(self.frame_soni,text='xmin, xmax').grid(row=4,column=0)
        self.xminmax_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green',
                                      font='Arial 15')
        self.xminmax_entry.insert(0,'x1, x2')
        self.xminmax_entry.grid(row=4,column=1,columnspan=1)
        
        key_lab = tk.Label(self.frame_soni,text='Key Signature').grid(row=5,column=0)
        self.key_menu = tk.OptionMenu(self.frame_soni, self.keyvar, *self.keyvar_options)
        self.key_menu.config(bg='black',fg='black',font='Arial 15')
        self.key_menu.grid(row=5,column=1,columnspan=1)
        
        program_lab = tk.Label(self.frame_soni,text='Instrument (0-127)').grid(row=6,column=0)
        self.program_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', 
                                      font='Arial 15')
        self.program_entry.insert(0,'0')
        self.program_entry.grid(row=6,column=1,columnspan=1)
        
        duration_lab = tk.Label(self.frame_soni,text='Duration (sec)').grid(row=7,column=0)
        self.duration_entry = tk.Entry(self.frame_soni, width=10, borderwidth=2, bg='black', fg='lime green', 
                                       font='Arial 15')
        self.duration_entry.insert(0,'1')
        self.duration_entry.grid(row=7,column=1,columnspan=1)
    
    def init_display_size(self):
        #aim --> match display frame size with that once the canvas is added
        #the idea is for consistent aestheticsTM
        self.fig = figure.Figure(figsize=(5,5))
        self.fig.subplots_adjust(left=0.06, right=0.94, top=0.94, bottom=0.06)

        self.ax = self.fig.add_subplot()
        self.im = self.ax.imshow(np.zeros(100).reshape(10,10))
        self.ax.set_title('Click "Browse" to the right to begin!',fontsize=15)
        self.text = self.ax.text(x=2.2,y=4.8,s='Your Galaxy \n Goes Here',color='red',fontsize=25)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_display) 
        
        #activate the draw square/rectangle/quadrilateral/four-sided polygon event
        self.connect_event=self.canvas.mpl_connect('button_press_event',self.drawSqRec)
        
        #add canvas 'frame'
        self.label = self.canvas.get_tk_widget()
        self.label.grid(row=0,column=0,columnspan=3,rowspan=6,sticky='nsew')
    
    def add_info_button(self):
        self.info_button = tk.Button(self.frame_display, text='Galaxy FITS Info', padx=15, pady=10, font='Ariel 20', command=self.popup)
        self.info_button.grid(row=8,column=0,sticky='w',rowspan=2)
    
    def add_save_button(self):
        self.save_button = tk.Button(self.frame_save, text='Save as WAV', padx=15, pady=10, font='Ariel 20',
                                     command=self.save_sound)
        self.save_button.grid(row=0,column=0)
    
    def add_browse_button(self):
        self.button_explore = tk.Button(self.frame_buttons ,text="Browse", padx=20, pady=10, font=self.helv20, 
                                        command=self.browseFiles)
        self.button_explore.grid(row=1,column=0)
        
    def add_enter_button(self):
        self.path_button = tk.Button(self.frame_buttons, text='Enter/Refresh', padx=20, pady=10, font=self.helv20,command=self.initiate_canvas)
        self.path_button.grid(row=1,column=1)
    
    def add_midi_button(self):
        self.midi_button = tk.Button(self.frame_soni, text='Sonify', padx=20, pady=10, font=self.helv20, 
                                     command=self.midi_setup_bar)
        self.midi_button.grid(row=8,column=0,columnspan=2)
    
    def add_angle_buttons(self):
        self.angle_button = tk.Button(self.frame_box, text='Rotate',padx=5,pady=10,font=self.helv20,
                                      command=self.create_rectangle)
        self.angle_button.grid(row=2,column=1,columnspan=3)
        self.incarrow = tk.Button(self.frame_box, text='+1',padx=1,pady=10,font='Ariel 14',
                                  command=self.increment)
        self.incarrow.grid(row=2,column=4,columnspan=1)                          
        self.decarrow = tk.Button(self.frame_box, text='-1',padx=1,pady=10,font='Ariel 14',
                                  command=self.decrement)
        self.decarrow.grid(row=2,column=0,columnspan=1)
    
    def increment(self):
        #a few lines in other functions switch self.angle from 90 (or 270) to 89.9
        #to prevent this 89.9 number from being inserted into the angle_box and then incremented/decremented, 
        #I'll just pull the self.angle float again.
        self.angle = float(self.angle_box.get())
        self.angle += 1   #increment
        self.angle_box.delete(0,tk.END)   #delete current textbox entry
        self.angle_box.insert(0,str(self.angle))   #update entry with incremented angle
        
        #automatically rotate the rectangle when + is clicked
        self.create_rectangle()
    
    def decrement(self):
        #a few lines in other functions switch self.angle from 90 (or 270) to 89.9 (for instance)
        #to prevent this number from being inserted into the angle_box and then incremented/decremented, 
        #I'll just pull the self.angle float again.
        self.angle = float(self.angle_box.get())
        self.angle -= 1   #decrement
        self.angle_box.delete(0,tk.END)   #delete current textbox entry
        self.angle_box.insert(0,str(self.angle))   #update entry with decremented angle
        
        #automatically rotate when - is clicked
        self.create_rectangle()
    
    def save_sound(self):
        
        #if self.memfile has been defined already, then save as .wav
        #notes: -file will automatically go to 'saved_wavfiles' directory
        #       -.wav will only save the most recent self.midi_file, meaning the user must click "Sonify" to 
                 #sonify their rectangle/parameter tweaks so that they might be reflected in the .wav
        
        if hasattr(self, 'midi_file'):
            
            midi_savename = os.getcwd()+'/saved_wavfiles/'+str(self.galaxy_name)+'-'+str(self.band)+'.mid'   #using our current file conventions to define self.galaxy_name (see relevant line for further details); will save file to saved_wavfile directory
            
            #write file
            with open(midi_savename,"wb") as f:
                self.midi_file.writeFile(f)
            
            wav_savename = os.getcwd()+'/saved_wavfiles/'+str(self.galaxy_name)+'-'+str(self.band)+'.wav'   
            
            fs = FluidSynth(sound_font=self.soundfont, gain=3)   #gain governs the volume of wavefile. I needed to tweak the source code of midi2audio in order to have the gain argument --> I'll give instructions somewhere for how to do so...try the github wiki. :-)
            
            if os.path.isfile(wav_savename):    
                self.namecounter+=1
                wav_savename = os.getcwd()+'/saved_wavfiles/'+str(self.galaxy_name)+'-'+str(self.band)+'-'+str(self.namecounter)+'.wav'                
            else:
                self.namecounter=0
            
            fs.midi_to_audio(midi_savename, wav_savename) 
            print('Done! Check the saved_wavfile directory.')
            
        #if user has not yet clicked "Sonify", then clicking button will activate a popup message
        else:
            self.textbox = 'Do not try to save an empty .wav file! Create a rectangle on the image canvas then click "Sonify" to generate MIDI notes.'
            self.popup()
    
    def initiate_canvas(self):
        
        #delete any and all miscellany (galaxy image, squares, lines) from the canvas (created using 
        #self.init_display_size())
        self.label.delete('all')
        self.ax.remove()
        
        self.dat = fits.getdata(str(self.path_to_im.get()))
        
        #many cutouts, especially those in the r-band, have pesky foreground stars and other artifacts, which will invariably dominate the display of the image stretch. one option is that I can grab the corresponding mask image for the galaxy and create a 'mask bool' of 0s and 1s, then multiply this by the image in order to dictate v1, v2, and the normalization *strictly* on the central galaxy pixel values. 
        
        full_filepath = str(self.path_to_im.get()).split('/')
        full_filename = full_filepath[-1]
        split_filename = full_filename.replace('.','-').split('-')   #replace .fits with -fits, then split all
        galaxyname = split_filename[0]
        galaxyband = split_filename[3]
        try:
            if str(galaxyband)=='r':
                mask_path = glob.glob('/Users/k215c316/vf_html_mask/all_input_fits/'+galaxyname+'*'+'r-mask.fits')[0]
            if galaxyband=='W3':
                mask_path = glob.glob('/Users/k215c316/vf_html_mask/all_input_fits/'+galaxyname+'*'+'wise-mask.fits')[0]
            mask_image = fits.getdata(mask_path)
            self.mask_bool = ~(mask_image>0)
        
        except:
            self.mask_bool = np.zeros((len(self.dat),len(self.dat)))+1
            print('Mask image not found; proceeded with default v1, v2, and normalization values.')
        
        v1 = scoreatpercentile(self.dat*self.mask_bool,0.5)
        v2 = scoreatpercentile(self.dat*self.mask_bool,99.9)
        norm_im = simple_norm(self.dat*self.mask_bool,'asinh', min_percent=0.5, max_percent=99.9,
                              min_cut=v1, max_cut=v2)  #'beautify' the image
        
        #self.fig = figure.Figure(figsize=(5,5))
        self.ax = self.fig.add_subplot()
        self.im = self.ax.imshow(self.dat,origin='lower',norm=norm_im)
        self.ax.set_xlim(0,len(self.dat)-1)
        self.ax.set_ylim(0,len(self.dat)-1)
        
        #trying to extract a meaningful figure title from the path information
        filename=self.path_to_im.get().split('/')[-1]  #split str into list, let delimiter=/, isolate filename
        galaxy_name=filename.split('-')[0]  #galaxy name is first item in filename split list
        band=filename.split('-')[-1].split('.')[0]  #last item in filename list is band.fits; split into two components, isolate the first
        
        self.ax.set_title(f'{galaxy_name} ({band})',fontsize=15)

        self.im_length = np.shape(self.dat)[0]
        self.ymin = int(self.im_length/2-(0.20*self.im_length))
        self.ymax = int(self.im_length/2+(0.20*self.im_length))
        self.x=self.im_length/2
        
        #initiate self.current_bar (just an invisible line...for now)
        self.current_bar, = self.ax.plot([self.im_length/2,self.im_length/2+1],
                                         [self.im_length/2,self.im_length/2+1],
                                         color='None')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_display)    
        
        #activate the draw square/rectangle/quadrilateral/four-sided polygon event
        self.connect_event=self.canvas.mpl_connect('button_press_event',self.drawSqRec)
        
        #add canvas 'frame'
        self.label = self.canvas.get_tk_widget()
        self.label.grid(row=0,column=0,columnspan=3,rowspan=6)
        
        self.galaxy_name = galaxy_name   #will need for saving .wav file...
        self.band = band                 #same rationale
        
    def change_canvas_event(self):
        
        if int(self.var.get())==0:
            self.canvas.mpl_disconnect(self.connect_event)
            self.canvas.mpl_disconnect(self.connect_event_midi)
            self.connect_event = self.canvas.mpl_connect('button_press_event',self.drawSqRec)
        if int(self.var.get())==1:
            self.canvas.mpl_disconnect(self.connect_event)
            self.connect_event = self.canvas.mpl_connect('button_press_event',self.placeBar)
            try:
                self.connect_event_midi = self.canvas.mpl_connect('button_press_event', self.midi_singlenote)
            except:
                pass
         
    #create command function to print info popup message
    def popup(self):
        messagebox.showinfo('Unconventional README.md',self.textbox)
    
    #it may not be the most efficient function, as it calculates the distances between every line coordinate and the given (x,y); however, I am not clever enough to conjure up an alternative solution presently.
    def find_closest_bar(self):
        
        #initiate distances list --> for a given (x,y), which point in every line in self.all_line_coords
        #is closest to (x,y)? this distance will be placed in the distances list.
        self.distances=[]
        
        coord=(self.x,self.y)
        
        for line in self.all_line_coords:
            tree = spatial.KDTree(line)
            result=tree.query([coord])
            self.distances.append(result[0])
        
        self.closest_line_index = np.where(np.asarray(self.distances)==np.min(self.distances))[0][0]
    
    def find_closest_mean(self,meanlist):
        
        #from https://stackoverflow.com/questions/12141150/from-list-of-integers-get-number-closest-to-a-given-value
        self.closest_mean_index = np.where(np.asarray(meanlist) == min(meanlist, key=lambda x:abs(x-float(self.mean_px))))[0][0]
        
    
    def placeBar(self, event):  
        
        self.x=event.xdata
        self.y=event.ydata
        
        #remove current bar, if applicable
        try:
            self.current_bar.remove()
        except:
            pass
        
        #if user clicks outside the image bounds, then problem-o.
        if event.inaxes:
            
            #if no rotation of rectangle, just create some vertical bars.
            if (self.angle == 0):
                
                #if x is within the rectangle bounds, all is well. 
                if (self.x<=self.xmax) & (self.x>=self.xmin):
                    pass
                else:
                    #if x is beyond the right side of the rectangle, line will be placed at rightmost end
                    if (self.x>=self.xmax):
                        self.x = self.xmax
                    
                    #if x is beyond the left side of the rectangle, line will be placed at leftmost end
                    if (self.x<=self.xmin):
                        self.x = self.xmin
                        
                n_pixels = int(self.ymax-self.ymin)   #number of pixels between ymin and ymax
                line_x = np.zeros(n_pixels)+int(self.x)
                line_y = np.linspace(self.ymin,self.ymax,n_pixels)       
                self.current_bar, = self.ax.plot(line_x,line_y,linewidth=3,color='red')

                #extract the mean pixel value from this bar
                value_list = np.zeros(n_pixels)
                for index in range(n_pixels):
                    y_coord = line_y[index]
                    px_value = self.dat[int(y_coord)][int(self.x)]   #x will be the same...again, by design.
                    value_list[index] = px_value
                mean_px = '{:.2f}'.format(np.mean(value_list))
                self.val.config(text=f'Mean Pixel Value: {mean_px}',font='Ariel 18')
                self.canvas.draw()      
            
            else:
                
                self.find_closest_bar()   #outputs self.closest_line_index
                
                line_mean = self.mean_list[self.closest_line_index]
                line_coords = self.all_line_coords[self.closest_line_index]
            
                line_xvals = np.asarray(line_coords)[:,0]
                line_yvals = np.asarray(line_coords)[:,1]
                
                self.current_bar, = self.ax.plot([line_xvals[0],line_xvals[-1]],[line_yvals[0],line_yvals[-1]],
                                                linewidth=3,color='red')

                #extract the mean pixel value from this bar
                mean_px = '{:.2f}'.format(line_mean)

                self.val.config(text=f'Mean Pixel Value: {mean_px}',font='Ariel 16')
                self.canvas.draw()
            
            self.mean_px = mean_px
            
                                           
        else:
            print('Keep inside of the bounds of either the rectangle or the image!')
            self.val.config(text='Mean Pixel Value: None', font='Ariel 16')
    
    
    ###FOR RECTANGLES --> CLICK TWICE, DICTATE INCLINATION###
    
    def func(self,x,m,b):
        return m*x+b
    
    #from https://stackoverflow.com/questions/34372480/rotate-point-about-another-point-in-degrees-python
    def rotate(self, point_to_be_rotated, center_point = (0,0)):
        angle_rad = self.angle*np.pi/180
        xnew = np.cos(angle_rad)*(point_to_be_rotated[0] - center_point[0]) - np.sin(angle_rad)*(point_to_be_rotated[1] - center_point[1]) + center_point[0]
        ynew = np.sin(angle_rad)*(point_to_be_rotated[0] - center_point[0]) + np.cos(angle_rad)*(point_to_be_rotated[1] - center_point[1]) + center_point[1]

        return (round(xnew,2),round(ynew,2))
    
    #extract x and y vertex coordinates, and the slope of the lines connecting these points
    #this function "returns" lists of (x,y) vertices, and the slopes of the rectangle perimeter lines
    #NOTE: I choose np.max(x)-np.min(x) as the number of elements comprising each equation. seems fine.
    def get_xym(self):
        
        #self.event_bounds contains the list [self.x1,self.y1,self.x2,self.y2]
        self.p1 = [self.event_bounds[0],self.event_bounds[1]]   #coordinates of first click event
        self.p2 = [self.event_bounds[2],self.event_bounds[3]]   #coordinates of second click event
        
        if self.angle%90 != 0:      #if angle is not divisible by 90, can rotate using this algorithm. 
                        
            n_spaces = int(np.abs(self.p1[0] - self.p2[0]))   #number of 'pixels' between x coordinates
            
            (xc,yc) = ((self.p1[0]+self.p2[0])/2, (self.p1[1]+self.p2[1])/2)
            one_rot = self.rotate(point_to_be_rotated = self.p1, center_point = (xc,yc))
            two_rot = self.rotate(point_to_be_rotated = self.p2, center_point = (xc,yc))
            three_rot = self.rotate(point_to_be_rotated = (self.p1[0],self.p2[1]), center_point = (xc,yc))
            four_rot = self.rotate(point_to_be_rotated = (self.p2[0],self.p1[1]), center_point = (xc,yc))

            x1 = np.linspace(one_rot[0],three_rot[0],n_spaces)
            m1 = (one_rot[1] - three_rot[1])/(one_rot[0] - three_rot[0])
            y1 = three_rot[1] + m1*(x1 - three_rot[0])

            x2 = np.linspace(one_rot[0],four_rot[0],n_spaces)
            m2 = (one_rot[1] - four_rot[1])/(one_rot[0] - four_rot[0])
            y2 = four_rot[1] + m2*(x2 - four_rot[0])

            x3 = np.linspace(two_rot[0],three_rot[0],n_spaces)
            m3 = (two_rot[1] - three_rot[1])/(two_rot[0] - three_rot[0])
            y3 = two_rot[1] + m3*(x3 - two_rot[0])

            x4 = np.linspace(two_rot[0],four_rot[0],n_spaces)
            m4 = (two_rot[1] - four_rot[1])/(two_rot[0] - four_rot[0])
            y4 = two_rot[1] + m4*(x4 - two_rot[0])

            self.x_rot = [x1,x2,x3,x4]
            self.y_rot = [y1,y2,y3,y4]
            self.m_rot = [m1,m2,m3,m4]
            self.n_spaces = n_spaces
            
            self.one_rot = one_rot
            self.two_rot = two_rot
            self.three_rot = three_rot
            self.four_rot = four_rot

        elif (self.angle/90)%2 == 0:  #if angle is divisible by 90 but is 0, 180, 360, ..., no change to rectangle
            
            n_spaces = int(np.abs(self.p1[0] - self.p2[0]))   #number of 'pixels' between x coordinates
            
            x1 = np.zeros(50)+self.p1[0]
            y1 = np.linspace(self.p2[1],self.p1[1],n_spaces)

            x2 = np.linspace(self.p1[0],self.p2[0],n_spaces)
            y2 = np.zeros(50)+self.p2[1]

            x3 = np.linspace(self.p2[0],self.p1[0],n_spaces)
            y3 = np.zeros(50)+self.p1[1]

            x4 = np.zeros(50)+self.p2[0]
            y4 = np.linspace(self.p1[1],self.p2[1],n_spaces)

            self.x_rot = [x1,x2,x3,x4]
            self.y_rot = [y1,y2,y3,y4]
            self.m_rot = [0,0,0,0]
            self.n_spaces = n_spaces
            
            self.one_rot = self.p1
            self.two_rot = self.p2
            self.three_rot = (self.p1[0],self.p2[1])
            self.four_rot = (self.p2[0],self.p1[1])

        
    def RecRot(self):
    
        self.get_xym()   #defines and initiates self.x_rot, self.y_rot, self.m_rot
                
        #create lists
        list_to_mean = []
        self.mean_list = []   #only need to initialize once
        self.all_line_coords = []   #also only need to initialize once --> will give x,y coordinates for every line
                                    #(hence the variable name).
        
        for i in range(self.n_spaces):  #for the entire n_spaces extent: 
                                        #find x range of between same-index points on opposing sides of the 
                                        #rectangle, determine the equation variables to 
                                        #connect these elements within this desired x range, 
                                        #then find this line's mean pixel value. 
                                        #proceed to next set of elements, etc.

            #points from either x4,y4 (index=3) or x1,y1 (index=0)
            #any angle which is NOT 0,180,360,etc.
            if self.angle%90 != 0:
                self.all_bars = np.zeros(self.n_spaces**2).reshape(self.n_spaces,self.n_spaces)
                xpoints = np.linspace(self.x_rot[3][i],self.x_rot[0][-(i+1)],self.n_spaces)
                b = self.y_rot[0][-(i+1)] - (self.m_rot[2]*self.x_rot[0][-(i+1)])
                ypoints = self.func(xpoints,self.m_rot[2],b)
                
                #convert xpoint, ypoint to arrays, round all elements to 2 decimal places, convert back to lists
                self.all_line_coords.append(list(zip(np.ndarray.tolist(np.round(np.asarray(xpoints),3)),
                                                np.ndarray.tolist(np.round(np.asarray(ypoints),3)))))
                
                for n in range(len(ypoints)):
                    #from the full data grid x, isolate all of values occupying the rows (xpoints) in 
                    #the column ypoints[n]
                    list_to_mean.append(self.dat[int(ypoints[n])][int(xpoints[n])])

                self.mean_list.append(np.mean(list_to_mean))
                list_to_mean = []
            
            #0,180,360,etc.
            if (self.angle/90)%2 == 0:
                xpoints = np.linspace(self.x_rot[3][i],self.x_rot[0][-(i+1)],self.n_spaces)
                b =self.y_rot[0][-(i+1)] - (self.m_rot[2]*self.x_rot[0][-(i+1)])
                ypoints = self.func(xpoints,self.m_rot[2],b)
                
                #convert xpoint, ypoint to arrays, round all elements to 2 decimal places, convert back to lists
                self.all_line_coords.append(list(zip(np.ndarray.tolist(np.round(np.asarray(xpoints),3)),
                                                np.ndarray.tolist(np.round(np.asarray(ypoints),3)))))
                
                for n in range(len(ypoints)):
                    #from the full data grid x, isolate all of values occupying the rows (xpoints) in 
                    #the column ypoints[n]
                    list_to_mean.append(self.dat[int(ypoints[n])][int(xpoints[n])])

                self.mean_list.append(np.mean(list_to_mean))
                list_to_mean = []
            
        #check if all_line_coords arranged from left to right
        #if not, sort it (flip last list to first, etc.) and reverse mean_list accordingly
        #first define coordinates of first and second "starting coordinates"
        first_coor = self.all_line_coords[0][0]
        second_coor = self.all_line_coords[1][0]
        
        #isolate the x values
        first_x = first_coor[0]
        second_x = second_coor[0]
        
        #if the first x coordinate is greater than the second, then all set. 
        #otherwise, lists arranged from right to left. fix.
        #must also flip mean_list so that the values remain matched with the correct lines
        if first_x>second_x:
            self.all_line_coords.sort()
            self.mean_list.reverse()

    def create_rectangle(self,x_one=None,x_two=None,y_one=None,y_two=None):
        
        #the "try" statement will only work if the user-input angle is a float (and not a string)
        #otherwise, angle will default to zero, meaning no rotation
        try:
            self.angle = float(self.angle_box.get())
            if (self.angle/90)%2 == 0:      #if 0,180,360,etc., no different from 0 degree rotation (no rotation)
                self.angle = 0
            if (self.angle/90)%2 == 1:      #if 90, 270, etc., just approximate to be 89.9
                self.angle = 89.9
        except:
            self.angle = 0
            self.angle_box.delete(0,tk.END)
            self.angle_box.insert(0,str(self.angle))
            
        try:
            for line in [self.line_eins,self.line_zwei,self.line_drei,self.line_vier]:
                line_to_remove = line.pop(0)
                line_to_remove.remove()
        except:
            pass
        
        if (self.angle== 0)|(isinstance(self.angle,str)):
            if x_one is not None:    
                         
                self.line_one = self.ax.plot([x_one,x_one],[y_one,y_two],color='crimson',linewidth=2)
                self.line_two = self.ax.plot([x_one,x_two],[y_one,y_one],color='crimson',linewidth=2)
                self.line_three = self.ax.plot([x_two,x_two],[y_one,y_two],color='crimson',linewidth=2)
                self.line_four = self.ax.plot([x_one,x_two],[y_two,y_two],color='crimson',linewidth=2)
                
            else:
            
                self.get_xym()   #defines and initiates self.x_rot, self.y_rot, self.m_rot

                x1,x2,x3,x4=self.one_rot[0],self.two_rot[0],self.three_rot[0],self.four_rot[0]
                y1,y2,y3,y4=self.one_rot[1],self.two_rot[1],self.three_rot[1],self.four_rot[1]

                self.line_eins = self.ax.plot([x1,x3],[y1,y3],color='crimson',linewidth=2)   #1--3
                self.line_zwei = self.ax.plot([x1,x4],[y1,y4],color='crimson',linewidth=2)   #1--4
                self.line_drei = self.ax.plot([x2,x3],[y2,y3],color='crimson',linewidth=2)   #2--3
                self.line_vier = self.ax.plot([x2,x4],[y2,y4],color='crimson',linewidth=2)   #2--4

                self.canvas.draw()

        if self.angle!=0:
            
            #a nonzero angle means the user has already created the unaltered rectangle
            #that is, the coordinates already exist in self.event_bounds (x1,x2,y1,y2)
            #these are called in get_xym
            
            self.get_xym()   #defines and initiates self.x_rot, self.y_rot, self.m_rot

            x1,x2,x3,x4=self.one_rot[0],self.two_rot[0],self.three_rot[0],self.four_rot[0]
            y1,y2,y3,y4=self.one_rot[1],self.two_rot[1],self.three_rot[1],self.four_rot[1]
                        
            self.line_eins = self.ax.plot([x1,x3],[y1,y3],color='crimson')   #1--3
            self.line_zwei = self.ax.plot([x1,x4],[y1,y4],color='crimson')   #1--4
            self.line_drei = self.ax.plot([x2,x3],[y2,y3],color='crimson')   #2--3
            self.line_vier = self.ax.plot([x2,x4],[y2,y4],color='crimson')   #2--4

            self.canvas.draw()
            
    def drawSqRec(self, event):
        
        try:
            self.angle = float(self.angle_box.get())
        except:
            self.angle = 0
            self.angle_box.delete(0,tk.END)
            self.angle_box.insert(0,str(self.angle))
        
        #collect the x and y coordinates of the click event
        #if first click event already done, then just define x2, y2. otherwise, define x1, y1.
        if (self.x1 is not None) & (self.y1 is not None):
            self.x2 = event.xdata
            self.y2 = event.ydata
        else:
            self.x1 = event.xdata
            self.y1 = event.ydata
            first_time=True
        
        #the user has clicked only the 'first' rectangle corner...
        if (self.x1 is not None) & (self.x2 is None):
            #if the corner is within the canvas, plot a dot to mark this 'first' corner
            if event.inaxes:
                self.bound_check=True
                dot = self.ax.scatter(self.x1,self.y1,color='crimson',s=10,marker='*')
                self.sq_mean_value = self.dat[int(self.x1),int(self.y1)]
                self.canvas.draw()
                #for whatever reason, placing dot.remove() here will delete the dot after the second click
                dot.remove()
        
        #if the 'first' corner is already set, then plot the rectangle and print the output mean pixel value
        #within this rectangle
        if (self.x2 is not None):
            
            #assign all event coordinates to an array
            self.event_bounds = [self.x1.copy(),self.y1.copy(),self.x2.copy(),self.y2.copy()]
            
            if event.inaxes:
                if (self.bound_check):
                    self.create_rectangle(x_one=self.x1,x_two=self.x2,y_one=self.y1,y_two=self.y2)
                    self.canvas.draw()
                    
            #reset parameters for next iteration
            self.bound_check = None
            self.x1=None
            self.x2=None
            self.y1=None
            self.y2=None
            
            #similar phenomenon as dot.remove() above.
            try:
                for line in [self.line_one,self.line_two,self.line_three,self.line_four]:
                    line_to_remove = line.pop(0)
                    line_to_remove.remove()
            except:
                pass
    
    # Function for opening the file explorer window
    def browseFiles(self):
        filename = filedialog.askopenfilename(initialdir = "/Users/k215c316/vf_html_w1/all_input_fits/", title = "Select a File", filetypes = ([("FITS Files", ".fits")]))
        self.path_to_im.delete(0,tk.END)
        self.path_to_im.insert(0,filename)        
    
##########
#the sonification-specific functions...
##########

    #typical sonification mapping function; maps value(s) from one range to another range; returns floats
    def map_value(self, value, min_value, max_value, min_result, max_result):
        result = min_result + (value - min_value)/(max_value - min_value)*(max_result - min_result)
        return result
    
    def midi_setup_bar(self):
        
        #define various quantities required for midi file generation
        self.y_scale = float(self.y_scale_entry.get())
        self.strips_per_beat = 15
        self.vel_min = int(self.vel_min_entry.get())
        self.vel_max = int(self.vel_max_entry.get())
        self.bpm = int(self.bpm_entry.get())
        self.program = int(self.program_entry.get())   #the instrument!
        self.duration = float(self.duration_entry.get())

        
        try:
            self.angle = float(self.angle_box.get())
            #if the angle angle is no different from 0 (e.g., 180, 360, etc.), just set the angle = 0.
            if (self.angle/90)%2 == 0:
                self.angle = 0
            #if angle is 90, 270, etc., just approximate as 89.9 deg (avoids many problems -- including dividing by cos(90)=0 -- and 89.9 is sufficiently close to 90 degrees)
            if (self.angle/90)%2 == 1:
                self.angle = 89.9
        except:
            self.angle = 0
            self.angle_box.delete(0,tk.END)
            self.angle_box.insert(0,str(self.angle))
        
        selected_sig = self.keyvar.get()
        self.note_names = self.note_dict[selected_sig]
        self.note_names = self.note_names.split("-")   #converts self.note_names into a proper list of note strings
        
        print(selected_sig)
        print(self.note_names)
        
        self.soundfont = homedir+'/Desktop/pkmngba.sf2'
        
        #use user-drawn rectangle in order to define xmin, xmax; ymin, ymax. if no rectangle drawn, then default to image width for x and some fraction of the height for y.
        try:
            #for the case where the angle is not rotated
            if self.angle == 0:
                
                self.xmin = int(self.event_bounds[2]) if (self.event_bounds[0]>self.event_bounds[2]) else int(self.event_bounds[0])
                self.xmax = int(self.event_bounds[0]) if (self.event_bounds[0]>self.event_bounds[2]) else int(self.event_bounds[2])
                self.ymin = int(self.event_bounds[3]) if (self.event_bounds[1]>self.event_bounds[3]) else int(self.event_bounds[1])
                self.ymax = int(self.event_bounds[1]) if (self.event_bounds[1]>self.event_bounds[3]) else int(self.event_bounds[3])
            
            #if rectangle is rotated, use rotated coordinates to find mins and maxs
            else:
                xvertices=np.array([self.one_rot[0],self.two_rot[0],self.three_rot[0],self.four_rot[0]])
                yvertices=np.array([self.one_rot[1],self.two_rot[1],self.three_rot[1],self.four_rot[1]])
                
                self.xmin = np.min(xvertices)
                self.xmax = np.max(xvertices)
                
                self.ymin = np.min(yvertices)
                self.ymax = np.max(yvertices)
                
        except:
            print('Defaulting to image parameters for xmin, xmax; ymin, ymax.')
            self.xmin=0
            self.xmax=self.im_length
            self.ymin = int(self.im_length/2-(0.20*self.im_length))
            self.ymax = int(self.im_length/2+(0.20*self.im_length))
            
        self.xminmax_entry.delete(0,tk.END)
        mean_px_min = '{:.2f}'.format(self.xmin)
        mean_px_max = '{:.2f}'.format(self.xmax)
        self.xminmax_entry.insert(0,f'{mean_px_min}, {mean_px_max}')
        
        if self.angle == 0:
            #band = self.dat[:,self.ymin:self.ymax]   #isolates pixels within horizontal band across the image from y_min to y_max
            cropped_data = self.dat[self.ymin:self.ymax, self.xmin:self.xmax]   #[rows,columns]; isolates pixels within the user-defined region
            strips = []   #create empty array for 1px strips
            mean_strip_values = []   #create empty array for mean px values of the strips
            vertical_lines = [cropped_data[:, i] for i in range(self.xmax-self.xmin)]
            
            for line in vertical_lines:
                mean_strip_values.append(np.mean(line))
            
            #for i in range(self.xmin,self.xmax):
            #    strips.append(band[i,:])   #individual vertical strips
            #    mean_strip_values[i-self.xmin] = np.mean(strips[i-self.xmin])   #the 'ydata'; i-self.xmin for correct indices (will go from 0 to self.xmax-self.xmin)
            
            self.mean_list_norot = mean_strip_values
        
        if self.angle != 0:
            self.RecRot()
            mean_strip_values = self.mean_list
    
        #rescale strip number to beats
        self.t_data = np.arange(0,len(mean_strip_values),1) / self.strips_per_beat   #convert to 'time' steps
        duration_beats=np.max(self.t_data)   #duration is end of the t_data list, or the max value in this list
        #print('Duration:',duration_beats, 'beats')
        #one beat = one quarter note
        
        y_data = self.map_value(mean_strip_values,min(mean_strip_values),max(mean_strip_values),0,1)   #normalizes values
        y_data_scaled = y_data**self.y_scale
        
        #the following converts note names into midi notes
        note_midis = [str2midi(n) for n in self.note_names]  #list of midi note numbers
        n_notes = len(note_midis)
        #print('Resolution:',n_notes,'notes')
                                                            
        #MAPPING DATA TO THE MIDI NOTES!        
        self.midi_data = []
        #for every data point, map y_data_scaled values such that smallest/largest px is lowest/highest note
        for i in range(len(self.t_data)):   #assigns midi note number to whichever y_data_scaled[i] is nearest
            note_index = round(self.map_value(y_data_scaled[i],0,1,0,len(note_midis)-1))
            self.midi_data.append(note_midis[note_index])

        #map data to note velocities (equivalent to the sound volume)
        self.vel_data = []
        for i in range(len(y_data_scaled)):
            note_velocity = round(self.map_value(y_data_scaled[i],0,1,self.vel_min,self.vel_max)) #larger values, heavier sound
            self.vel_data.append(note_velocity)
        
        self.midi_allnotes() 
        
    def midi_allnotes(self):
        
        self.create_rectangle()
        
        #create midi file object, add tempo
        self.memfile = BytesIO()   #create working memory file (allows me to play the note without saving the file...yay!)
        midi_file = MIDIFile(1) #one track
        midi_file.addTempo(track=0,time=0,tempo=self.bpm) #only one track, so track=0th track; begin at time=0, tempo is bpm
        midi_file.addProgramChange(tracknum=0, channel=0, time=0, program=self.program)
        #add midi notes to file
        for i in range(len(self.t_data)):
            midi_file.addNote(track=0, channel=0, pitch=self.midi_data[i], time=self.t_data[i], duration=self.duration, volume=self.vel_data[i])
        midi_file.writeFile(self.memfile)
        
        mixer.init()
        self.memfile.seek(0)
        mixer.music.load(self.memfile)
        mixer.music.play()
        
        self.midi_file = midi_file   #will need for saving as .wav file
        
    def midi_singlenote(self,event):
        #the setup for playing *just* one note...using the bar technique. :-)
        self.memfile = BytesIO()   #create working memory file (allows me to play the note without saving the file...yay!)
        
        midi_file = MIDIFile(1) #one track
        midi_file.addTrackName(0,0,'Note')
        midi_file.addTempo(track=0, time=0, tempo=self.bpm)
        midi_file.addProgramChange(tracknum=0, channel=0, time=0, program=self.program)
        
        #for the instance where there is no rotation
        if self.angle == 0:

            self.find_closest_mean(self.mean_list_norot)  #determine the index at which the mean_list element    
                                                          #is closest to the current bar mean outputs 
                                                          #self.closest_mean_index
        else:
            self.find_closest_mean(self.mean_list)
            
        #extract the midi and velocity notes associated with that index. 
        single_pitch = self.midi_data[self.closest_mean_index]
        single_volume = self.vel_data[self.closest_mean_index]
            
        midi_file.addNote(track=0, channel=0, pitch=single_pitch, time=self.t_data[1], duration=1, volume=single_volume)   #isolate the one note corresponding to the click event, add to midi file; the +1 is to account for the silly python notation conventions
        
        midi_file.writeFile(self.memfile)
        #with open(homedir+'/Desktop/test.mid',"wb") as f:
        #    self.midi_file.writeFile(f)
        
        mixer.init()
        self.memfile.seek(0)   #for whatever reason, have to manually 'rewind' the track in order for mixer to play
        mixer.music.load(self.memfile)
        mixer.music.play()       
        
if __name__ == "__main__":
    app = App()
    app.mainloop()
    #app.destroy()    
    
    
    #create save button which saves most recent sonification file as well as a companion text file listing the galaxy VFID and parameter values.
    #I should ALSO record a video tutorial on how to operate this doohickey.
    #also also also...animations. maybe. with save.mp4 option.
    #A "SAVE AS CHORDS BUTTON!" w1+w3 overlay. w1 lower octaves, w3 higher? not yet sure.
    #and for pete's sake, TIDY YOUR FRAMES.