from tkinter import *
from tkinter import messagebox
from tkinter import font as tkFont

root = Tk()
root.title('')

#create a font preference
helv20 = tkFont.Font(family='Helvetica', size=20, weight='bold')

#showinfo, showwarning, showerror, askquestion, askokcancel, askyesno
def popup():
    #for askyesno --> yes == 1, no == 0
    response = messagebox.askyesno('IMMEDIATE REPSONSE REQUESTED!','Is the bagged lettuce expired?')
    if response == 1:
        Label(root,text='Expired.').pack()
    else:
        Label(root,text='Not Expired.').pack()

Button(root, text="Generate popup", font=helv20, command=popup).pack()

if __name__ == '__main__':
    root.mainloop()