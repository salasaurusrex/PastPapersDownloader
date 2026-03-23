------------------------------------------------------------------------

# 📊 PastPapersDownloader 📊

------------------------------------------------------------------------


## Introduction

This program uses multithreaded requests to download Past Papers for As and A, IGCSE, and O-Level classes. It's a quick method of downloading past exams. All exams are gathered from [Papa Cambridge](https://papacambridge.com/)



------------------------------------------------------------------------

## Installation requirements

```diff
+ python3
+ Access to a terminal/shell/cmd
```

#### Operating Systems it works on:
- Windows Operating Systems
- MacOSX
- Linux

### Libraries:
- The library "requests" is required for this application to function; in order to install it, enter the command `pip install requests` in the terminal/shell/cmd.

------------------------------------------------------------------------

## How to Install

#### 1. Download manually [--> here <--](https://github.com/saleguas/PastPapersDownloader/archive/master.zip)
#### *OR*
#### 2. Type in your terminal or cmd-line:
```
git clone https://github.com/saleguas/PastPapersDownloader.git
```

------------------------------------------------------------------------

## How to Use It

The instructions are simple:
1. Simply open up a terminal in the same location as the main.py file
2. Type `python main.py [COMMANDS]` and that's all!

![](media/instructions.gif)


Use the various list commands to display the syllabus codes for the classes. For example If I wanted to download AS and A level biology, I would first run:

```python
python main.py -LA
```

to list the As and A level classes, and see that Biology has the syllabus number 9700.

I would then run the following to download it:

```
python main.py -A 9700
```

The help command on the argument parser displays each command in detail:
```bash
usage: main.py [-h] [-A AICE] [-O ORDINARY] [-I IGCSE] [-LA] [-LO] [-LI]

Download Up-To-date Past Papers.

optional arguments:
  -h, --help            show this help message and exit
  -A AICE, --AICE AICE  Downloads the AICE As and A level exam with the
                        syllabus code provided. Type ALL to download all
                        exams(may take a while!).
  -O ORDINARY, --ORDINARY ORDINARY
                        Downloads the O-level exam with the syllabus code
                        provided. Type ALL to download all exams(may take a
                        while!).
  -I IGCSE, --IGCSE IGCSE
                        Downloads the IGCSE exam with the syllabus code
                        provided. Type ALL to download all exams(may take a
                        while!).
  -LA, --LISTAICE       Lists all the As and A level AICE classes with the
                        syllabus numbers.
  -LO, --LISTORDINARY   Lists all the O level classes with the syllabus
                        numbers.
  -LI, --LISTIGCSE      Lists all the IGCSE classes with the syllabus numbers.

```

------------------------------------------------------------------------
