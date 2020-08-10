import re # For file identification
import os
import ctypes # For finding screen res
import tkinter as tk
from PIL import Image, ImageTk, ImageEnhance
from os import chdir, getcwd, listdir # For file view

c = {
    "leftminsize": 50,
    "rightminsize": 500,
    "maximsize": 600,
    "imagepad": 5,
    "defaultrespercent": 100,
    # reducing_gap for image to display image conversion. The lower the number the faster the conversion. 3.0 is equivelent to normal conversion.
    "previewoptimize": 2
}

ascii = [
    # The value to each key represents the percentage of brightness between the darkest pixel and the brightest. All values are the max that that symbol can represent.
    ('#', 0.1),
    ('@', 0.2),
    ('%', 0.3),
    ('?', 0.5),
    (':', 0.6),
    (',', 0.8),
    ('.', 0.87),
    ('*', 0.92)
]

class TkInterface:
    ''' Object that brings up a Tk interface allowing the user to select the images and change conversion variables. '''

    def __init__(self, endpath=None, maxsize=c["maximsize"], usefullres=True, *, sep_reduce_gap=-1):
        ''' Starts the application. It calls startTk() and updateFiles() to acheive this. At the end it starts the mainloop.
        Arguments:
            maxsize - The display size of the biggest side of an image.
            usefullres - If set to True, the program uses the full resolution of the image. With the default False, it uses the lower res displayed image.
            sep_reduce_gap - reduce_gap for image if usefullres is False. It can be -1 to not use reduce_gap, 0 to use the same as the display image, or another number that will be used for reduce_gap. '''
        global re, c

        # Setting max screensize
        try:
            global ctypes
            user32 = ctypes.windll.user32
            self.screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        except:
            self.screensize = (c["maximsize"] * 4, c["maximsize"] * 3)

        # Save destination
        if endpath:
            self.endpath = endpath
        else:
            self.endpath = r'C:\Users\Home\Desktop\Python Files\PIL\ASCII_Art'

        self.supported = re.compile(r'([.]png$)|([.]jpg$)|([.]jpeg$)')

        self.maximsize = maxsize
        self.resratio = 1
        self.usefullres = usefullres

        self.sep_reduce_gap = sep_reduce_gap

        self.startTk()
        self.updateFiles()

        self.root.mainloop()

    def startTk(self):
        ''' Method called in __init__() to initialize the application window and widgets. '''
        global tk, Image, ImageTk, getcwd, c

        self.root = tk.Tk()
        root = self.root
        root.columnconfigure(0, minsize=c["leftminsize"])
        root.columnconfigure(1, weight=1, minsize=c["rightminsize"])
        root.maxsize(self.screensize[0], self.screensize[1])

        self.leftFrm = tk.Frame(root, bg='black')
        left = self.leftFrm
        left.grid(row=0, column=0, sticky="ns")

        lefttop = tk.Frame(left, bg='black')
        lefttop.pack(fill=tk.X)
        pathback = tk.Button(lefttop, text="<", command=self.pathBackFunc)
        pathback.pack(side=tk.LEFT)
        self.pathLbl = tk.Label(lefttop, text=getcwd(), bg="black", fg='white')
        self.pathLbl.pack(side=tk.LEFT, fill=tk.X)


        right = tk.Frame(root)
        right.grid(row=0, column=1, sticky="nesw")

        self.imageLbl = tk.Label(right, text="Find and click on an image file in the file explorer on the left to start.")
        self.imageLbl.grid(row=0, column=0, columnspan=4)

        self.origdcvs = tk.Canvas(right)
        self.prepdcvs = tk.Canvas(right)

        blank = ImageTk.PhotoImage(Image.new('L', (1,1), "white"))
        column = 0
        for canvas in (self.origdcvs, self.prepdcvs):
            canvas.config(width=self.maximsize, height=self.maximsize)
            canvas.create_image((0,0), image=blank)
            canvas.grid(row=1, column=column, rowspan=2, columnspan=2, padx=c["imagepad"], pady=c["imagepad"])
            column = 2

        self.origresLbl = tk.Label(right)
        self.origresLbl.grid(row=3, column=0, columnspan=2)
        self.prepresLbl = tk.Label(right)
        self.prepresLbl.grid(row=3, column=2, columnspan=2)

        scalefrm = tk.Frame(right)
        scalefrm.columnconfigure([0, 1, 2], weight=1)
        scalefrm.grid(row=4, column=1, columnspan=2, sticky="nesw")
        self.contrastScl = tk.Scale(scalefrm, label="Contrast: ", from_=0.0, to=10.0, resolution=0.05)
        self.brightnessScl = tk.Scale(scalefrm, label="Brightness: ", from_=0.0, to=10.0, resolution=0.05)
        self.resolutionScl = tk.Scale(scalefrm, label="Resolution (%): ", from_=100, to=0, resolution=0.1)
        column = 0
        for scale in (self.contrastScl, self.brightnessScl, self.resolutionScl):
            scale.config(orient=tk.HORIZONTAL, command=self.adjust(self=self, enhancer=scale["label"]))
            scale.grid(row=0, column=column, sticky="nesw", padx=c["imagepad"], pady=c["imagepad"])
            scale.set(1)
            column += 1
        self.resolutionScl.set(100)

        resetBtn = tk.Button(right, text="Reset", command=self.resetScales)
        resetBtn.grid(row=4, column=0, sticky='nesw', padx=c["imagepad"], pady=c["imagepad"])
        convertBtn = tk.Button(right, text="Convert\n" + "(Careful with high res)", command=self.convert)
        convertBtn.grid(row=4, column=3, sticky='nesw', padx=c["imagepad"], pady=c["imagepad"])

        self.updateFiles()

    def updateFiles(self):
        ''' Updates the frame listing files in the directive. '''
        global tk, listdir

        for widget in self.leftFrm.pack_slaves()[1:]:
            # [1:] is added to skip the first element, which would be the path label and pathback button.
            widget.destroy()

        for file in listdir():
            if file.count('.') == 0:
                # File is a folder
                btn = tk.Button(self.leftFrm, text=file, command=self.folderBtn(file))
                btn.pack(fill=tk.X)
            elif self.supported.search(file.lower()):
                # File is a supported image file
                btn = tk.Button(self.leftFrm, text=file, command=self.imageBtn(file))
                btn.pack(fill=tk.X)
    def folderBtn(self, file):
        ''' Returns a function to be used as a button command to change the directive to the foler 'file'. '''
        def f(self=self, file=file):
            ''' Open Folder '''
            global chdir, getcwd
            chdir(file)
            self.pathLbl["text"] = getcwd()
            self.updateFiles()
        return f
    def imageBtn(self, file):
        ''' Returns a function that opens the image on the right frame and calls displayPrep() for it. '''

        def displayOrig(self=self, file=file):
            ''' Load image file into the program. Displays it. Calls displayPrep() to convert it to b&w. '''
            global tk, Image, ImageTk, c

            # Open
            self.origim = Image.open(file)

            # Resize
            size = self.origim.size
            ratio = size[0] / size[1]
            self.resratio = ratio

            if size[0] > size[1]:
                newsize = (self.maximsize, round(self.maximsize/ratio))
            else:
                newsize = (round(self.maximsize * ratio), self.maximsize)
            self.dimsize = newsize

            self.origdim = self.origim.resize(newsize, reducing_gap=c["previewoptimize"])

            if not self.usefullres:
                if self.sep_reduce_gap == 0:
                    self.origim = self.origdim
                elif self.sep_reduce_gap == -1:
                    self.origim = self.origim.resize(newsize)
                else:
                    try:
                        self.origim = self.origim.resize(newsize, reducing_gap=self.sep_reduce_gap)
                    except:
                        print("Error Handled: ", self.sep_reduce_gap, "is an invalid input for sep_reduce_gap. Using display image instead.")
                        self.origim = self.origdim
            self.origresLbl["text"] = "Size: " + str(self.origim.size)

            # Display
            self.imageLbl["text"] = file
            im = ImageTk.PhotoImage(self.origdim)
            self.origdcvs.delete('all')
            self.origdcvs["width"], self.origdcvs["height"] = newsize
            self.origdcvs.create_image((0,0), image=im, anchor=tk.NW)
            self.origdtkim = im

            # Prep
            self.prepdimfull = self.origdim.convert('L')
            self.prepdim = self.prepdimfull

            self.displayPrep(newsize)

        return displayOrig

    def displayPrep(self, size=None):
        ''' Converts the image to black and white and displays it. '''
        global tk, ImageTk, ImageEnhance

        try:
            im = self.prepdim
            im = ImageEnhance.Contrast(im).enhance(self.contrastScl.get())
            im = ImageEnhance.Brightness(im).enhance(self.brightnessScl.get())
            self.prepresLbl["text"] = "Size: " + str(tuple(round(num * self.resolutionScl.get() / 100) for num in self.origim.size))

            im = ImageTk.PhotoImage(im)
            self.prepdcvs.delete('all')
            if size:
                self.prepdcvs["width"], self.prepdcvs["height"] = size
            self.prepdcvs.create_image((0,0), image=im, anchor=tk.NW)
            self.prepdtkim = im

        except AttributeError:
            pass

    def resetScales(self):
        ''' Resets all Scale widgets back to their default values. Binded to the resetBtn. '''
        self.contrastScl.set(1)
        self.brightnessScl.set(1)
        self.resolutionScl.set(100)
    def adjust(null, *, self, enhancer):
        ''' Returns a function to be binded to a slider. enhancer can be 'c', 'b', or 's'. '''

        def adjOther(null=null, *, self=self):
            ''' Update prepdcvs, which in turn re enhances using all slider numbers. '''
            self.displayPrep()

        def adjResolution(null=null, *, self=self):
            ''' Downscales the image by the given percentage and then upscales it using Image.NEAREST as to not change the new resolution while changine the size. '''
            global Image

            try:
                pct = self.resolutionScl.get() / 100
                size = (round(num * pct) for num in self.dimsize)
                self.prepdim = self.prepdimfull.resize(size)
                self.prepdim = self.prepdim.resize(self.dimsize, resample=Image.NEAREST)
                self.displayPrep()
            except (AttributeError, NameError):
                pass

        if enhancer == 'Resolution (%): ':
            return adjResolution
        else:
            return adjOther

    def pathBackFunc(self):
        ''' Brings path up a folder. '''
        global chdir, getcwd

        chdir('..')
        self.pathLbl["text"] = getcwd()
        self.updateFiles()

    def convert(self):
        ''' Convert origional image to ASCII. First convert to black and white, then apply ImageEnhancers from slider values, finally change resolution and run toASCII(). '''
        global toASCII, ImageEnhance, subprocess, os

        im = self.origim.convert(mode='L')

        newsize = tuple(round(num * self.resolutionScl.get()/100) for num in im.size)
        im = im.resize(newsize)
        x = self.contrastScl.get()
        im = ImageEnhance.Contrast(im).enhance(x)
        x = self.brightnessScl.get()
        im = ImageEnhance.Brightness(im).enhance(x)

        print("FIX UP FILE SAVING SYSTEM. EXPECIALLY THE NAMING.")
        try:
            chdir(self.endpath)
        except FileNotFoundError:
            pass
        filename = self.imageLbl["text"][:-4] + ' (ASCII).txt'
        savefile = open(filename, 'w')
        savefile.write(toASCII(im))
        savefile.close()
        print('Now attempting to open the file.')
        try:
            os.system('notepad.exe ' + filename)
        except:
            print('Attempt of opening the file was futile. It only works on windows, for one thing. It\'s kinda dodgy is another thing')

        self.imageLbl["text"] = 'ASCII Art Saved!'


def toASCII(PILimage):
    ''' Algorithm to covert b&w pixel values to ASCII characters. Returns a string (with new line characters) to be saved or displayed. '''
    global ascii

    if PILimage.mode != 'L':
        raise Exception('NotLMode')

    r = PILimage.getextrema()
    rangesize = r[1]-r[0]
    width = PILimage.size[0]

    data = PILimage.getdata()


    text = []
    line = []
    xcounter = 0

    for pixel in data:
        try:
            pctval = pixel / rangesize
        except ZeroDivisionError:
            pctval = 0

        for tup in ascii:
            if pctval < tup[1]:
                char = tup[0]
                break
        else:
            char = ' '

        line.append(char)
        xcounter += 1
        if xcounter == width:
            text.append(line)
            line = []
            xcounter = 0


    endstr = ''
    for line in text:
        for char in line:
            endstr = endstr + char
        endstr = endstr + '\n'
    return endstr


if (__name__ == "__main__") | (__name__ == "runclass"):
    inter = TkInterface()
    print("Program exit.")
