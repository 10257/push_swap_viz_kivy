# push_swap_viz_kivy
A push_swap visualizer in python using the kivy library

This python script started as a modification of o-reo python push_swap 
tkinter visualizer. It is now a complete rewrite using the [kivy library](https://kivy.org/)
It is intended to visualize your work with the push_swap 42 Project.
You need Python3 and kivy installed.
You can install it with Brew.

```
python3 -m pip install "kivy[base]"
```

Place the script where you want. It will look for the ``push_swap`` binary in the 
current folder if no path is specified.

Launch the script with :
```
python3 pswapviz.py
python3 pswapviz.py -p ../push_swap/push_swap -s 500
python3 pswapviz.py -p ../push_swap/push_swap 1 3 2 8 7 5
```
![pswapviz](https://user-images.githubusercontent.com/4463409/178237182-2c559b7d-a8ad-4b8e-a042-53df358cc17d.png)

- You can adjust speed with the slider.
- You can use the spacebar to start or stop the visualisation.
- You can also use left and right arrow to move forward or backward.
- You can use a slider to skip where you want to in the move list.

Here is the full list of command line parameters :
```
python3 pswapviz.py [-h] [-s <size>] [-c] [-p <path>] [-g <id>] [Numbers ...]


positional arguments:
  Numbers               A List of numbers for push_swap to sort (optional)

optional arguments:
  -h, --help            show this help message and exit
  -s <size>, --stack-size <size>
                        Size of the stack of number (ex: 3 or 5 or 100 or 500) default 100.
  -c, --continuous      The number generated are folowing each other by a "1" increment.
  -p <path>, --push-swap <path>
                        The absolute or relative path to your push_swap binary. 
                        if the path is not specified, look for push_swap in the current dir.
  -g <id>, --gradient <id>
                        Chose a color gradient to use (value between 1 and 10). 
                        1 - rainbow blue to red,
                        2 - rainbow purple to red,
                        3 - black and white dark,
                        4 - black and white light,
                        5 - White to black,
                        6 (default) - red gradient to black,
                        7 - purple gradient to black,
                        8 - red gradient to white,
                        9 - white to purple, 
                        10 - sunset
```