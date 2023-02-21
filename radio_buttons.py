from tkinter import *
from PIL import ImageTk, Image
from tkinter import font as tkFont  # for convenience
from tkinter import messagebox # for convenience

root = Tk()
root.title("Cabbage")

#create a font preference
helv20 = tkFont.Font(family='Helvetica', size=20, weight='bold')

txt = Label(root, text='Option Selected: ',font=helv20)
txt.pack()

modes = [
    ('Option One','Coleslaw'),
    ('Option Two','Rot Kohl'),
    ('Option Three','Bok Choy'),
    ('Option Four','Sprouts')
]

#tkinter tracks changes of r over time
r = StringVar()     #IntVar()
r.set('')

def clicked(value):
    txt.config(text=f'Option Selected: {value}',font=helv20)

for text, mode in modes:
    Radiobutton(root, text=text, variable=r, value=mode, command=lambda: clicked(r.get())).pack(anchor='w')

if __name__ == "__main__":
    root.mainloop()
    #root.destroy()