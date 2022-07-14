#!/usr/bin/env python3


import os
import sys
import random
import subprocess
import itertools
import argparse
import pathlib
os.environ["KIVY_NO_ARGS"] = "1"
os.environ["KIVY_NO_FILELOG"] = "1"
os.environ["KIVY_NO_CONSOLELOG"] = "1"
try:
    from kivy.uix.widget import Widget
except ImportError:
    raise ImportError("This script requires Kivy to be installed.\n \
                    Run this command inside a terminal to install it:\n\
                    python -m pip install \"kivy[base]\"")
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.properties import NumericProperty
from kivy.properties import BooleanProperty
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.metrics import sp, dp
from kivy.core.window import Window
from kivy.lang import Builder


"""
__project__ = "push_swap visualizer"
__author__ = "jgreau"
__email__ = "jgreau@student.42.fr"
This python script started as a modification of Emmanuel Ruaud python push_swap 
tkinter visualizer. I ended up doing a complete rewrite using the python kivy library.
It is intended to visualize your work with the push_swap 42 Project.
You need Python3 and kivy installed.
> python -m pip install "kivy[base]"
Place the script where you want. It will look for the push_swap binary in the 
current folder if no path is specified.
Launch the script with :
> python3 pswapviz.py
or
> python3 pswapviz.py -p ../push_swap/push_swap -s 500
or
> python3 pswapviz.py -p ../push_swap/push_swap 1 3 2 8 7 5
You can adjust speed with the slider.
You can use the spacebar to start or stop the visualisation.
You can also use left and right arrow to move forward or backward.
You can use the esc key to quit
You can use a slider to skip where you want to in the move list.
Here is the full list of command line parameters :
usage: pswapviz.py [-h] [-s <size>] [-c] [-p <path>] [-g <id>] [Numbers ...]

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
"""

DEFAULT_PSWAP_PATH = 'push_swap'


KV = '''
<Label>:
    font_name: 'DejaVuSans'

<MoveLabel>
    canvas.before:
        Color:
            hsv: (0, 0, 0.7) if self.selected else (0, 0, 0.45)
        Rectangle:
            size: self.size
            pos: self.pos

<MoveScrollList>:
    viewclass: 'MoveLabel'
    do_scroll_x: False
    scroll_type: ['bars']
    scroll_wheel_distance: dp(114)
    bar_width: dp(10)
    effect_cls: "ScrollEffect"
    SelectableRecycleBoxLayout:
        id: box
        orientation: 'vertical'
        size_hint_y: None
        default_size_hint: 1, None
        default_size: 0, dp(20)
        height: self.minimum_height
        spacing: dp(2)
        multiselect: True
        touch_multiselect: False
'''


class StackRectangle:
    def __init__(self, number, rank, pos, size):
        self.number = number
        self.rank = rank
        self.rect = Rectangle(pos=pos, size=size, ttt=8)


class IterMoveList:
    def __init__(self, moves: list):
        self.moves = moves
        self.current = 0
        self.max = len(moves)

    def next(self):
        if(self.current >= self.max):
            raise StopIteration
        if self.current <= -1:
            self.current = 0
        move = (self.current, self.moves[self.current])
        self.current += 1
        return move

    def prev(self):
        if(self.current <= 0):
            raise StopIteration
        self.current -= 1
        if self.current >= self.max:
            self.current = self.max - 1
        move = (self.current, self.moves[self.current])
        return move


class SelectableRecycleBoxLayout(
    FocusBehavior, LayoutSelectionBehavior, RecycleBoxLayout
):
    """ Adds selection and focus behaviour to the view. """


class MoveLabel(RecycleDataViewBehavior, Label):
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        super(MoveLabel, self).refresh_view_attrs(rv, index, data)

    def apply_selection(self, rv, index, is_selected):
        """ Respond to the selection of items in the view. """
        self.selected = is_selected
        # if is_selected:
        #     print("selection changed to {0}".format(rv.data[index]))
        # else:
        #     print("selection removed for {0}".format(rv.data[index]))


class MoveScrollList(RecycleView):
    moves_total = 0
    selected_item = -1

    def populate(self, moves):
        self.data = [{'text': str(x)} for x in moves]
        self.move_total = len(moves)

    def clear_selection(self):
        for i in range(self.selected_item + 1):
            self.ids.box.deselect_node(i)
        self.selected_item = -1

    def select_item(self, index):
        self.selected_item = index
        self.ids.box.select_node(index)

    def deselect_item(self, index):
        self.selected_item = index
        self.ids.box.deselect_node(index)

    def scroll_to_index(self, index):
        box = self.children[0]
        pos_index = (box.default_size[1] + box.spacing) * index
        scroll = self.convert_distance_to_scroll(
            0, pos_index - (self.height * 0.5))[1]
        if scroll > 1.0:
            scroll = 1.0
        elif scroll < 0.0:
            scroll = 0.0
        self.scroll_y = 1.0 - scroll

    def convert_distance_to_scroll(self, dx, dy):
        box = self.children[0]
        wheight = box.default_size[1] + box.spacing

        if not self._viewport:
            return 0, 0
        vp = self._viewport
        vp_height = self.move_total * wheight
        if vp.width > self.width:
            sw = vp.width - self.width
            sx = dx / float(sw)
        else:
            sx = 0
        if vp_height > self.height:
            sh = vp_height - self.height
            sy = dy / float(sh)
        else:
            sy = 1
        return sx, sy


class ProgressSlider(Slider):
    def __init__(self, **kwargs):
        self.register_event_type('on_release')
        self.register_event_type('on_grab')
        super(ProgressSlider, self).__init__(**kwargs)

    def on_release(self):
        pass

    def on_grab(self):
        pass

    def on_touch_down(self, touch):
        super(ProgressSlider, self).on_touch_down(touch)
        if touch.grab_current != self and self.collide_point(*touch.pos):
            self.dispatch('on_grab')
            return False

    def on_touch_up(self, touch):
        super(ProgressSlider, self).on_touch_up(touch)
        if touch.grab_current == self and self.collide_point(*touch.pos):
            self.dispatch('on_release')
            return False


class RectDisplayWidget(Widget):
    pause_status = NumericProperty(1)
    speed_ratio = NumericProperty(5.0)
    moves_total = NumericProperty(0)
    current_move_id = NumericProperty(-1)
    gradient = NumericProperty(0)

    def __init__(self, **kwargs):
        self.stack_a = []
        self.stack_b = []
        self.stack_len = 0
        self.max, self.min = (0, 0)
        self.gradient = kwargs['gradient']
        self._resize_trigger = Clock.create_trigger(self._resize_rect, -1)
        self._move_trigger = Clock.create_trigger(self._move_rect, -1)
        super(RectDisplayWidget, self).__init__(**kwargs)
        self.bind(size=self._resize_trigger, pos=self._resize_trigger)

    def prepare(self, stack, moves_list):
        self.stack_orig = stack
        self.stack_len = len(stack)
        self.moves_list = moves_list
        self.iter_moves_list = IterMoveList(self.moves_list)
        self.moves_total = self.iter_moves_list.max
        if (self.stack_len != 0):
            self.max = max(stack)
            self.min = min(stack)
        Clock.schedule_once(self.draw_rectangles)

    def set_color(self, rank, gradient):
        if gradient == 1:
            # rainbow blue to red
            return Color((1 - rank)/1.5, 1, 0.85, mode='hsv')
        if gradient == 2:
            # rainbow purple to red gradient sympa
            return Color((1 - rank)/1.25, 1, 0.85, mode='hsv')
        if gradient == 3:
            # black and white pas lisible
            return Color(0, 0, (1 - rank)/1.5, mode='hsv')
        if gradient == 4:
            # good black and white
            return Color(0, 0, 1 - (rank/1.25), mode='hsv')
        if gradient == 5:
            # black and white reverse
            return Color(0, 0, (rank/1.5) + 0.25, mode='hsv')
        if gradient == 6:
            # red gradient to black
            return Color(1, .75, 1 - (rank/1.25), mode='hsv')
        if gradient == 7:
            # purple gradient to black
            return Color(0.75, .75, 1 - (rank/1.25), mode='hsv')
        if gradient == 8:
            # red gradient to white
            return Color(1, 1 - (rank/1.25), 1, mode='hsv')
        if gradient == 9:
            # white to purple
            return Color(0.75, (rank/1.5), 0.8, mode='hsv')
        # sunset
        c = Color((1-rank)/1.25, (rank)/1.1, (rank)/1.25, mode='hsv')
        return c

    def get_rect_pos(self, pos_x, iter_y):
        offset = (self.height / self.stack_len) - self.y
        return (pos_x, self.height - iter_y - offset)

    def get_rect_size(self, rank):
        return (10 + rank * (self.center_x - (self.center_x/5)),
                self.height / self.stack_len)

    def get_rank(self, num):
        return (num - self.min) / ((self.max - self.min) + 1)

    def draw_rectangles(self, *largs):
        offset = 0
        offset_add = self.height / self.stack_len
        if self.stack_len > 0:
            with self.canvas:
                for num in self.stack_orig:
                    rank = self.get_rank(num)
                    self.set_color(rank, self.gradient)
                    rect = StackRectangle(num, rank,
                                          self.get_rect_pos(0, offset),
                                          self.get_rect_size(rank))
                    self.stack_a.append(rect)
                    offset += offset_add

    def _resize_rect(self, *largs):
        offset = 0
        if self.stack_len > 0:
            offset_add = self.height / self.stack_len
        for item in self.stack_a:
            item.rect.pos = self.get_rect_pos(0, offset)
            item.rect.size = self.get_rect_size(item.rank)
            offset += offset_add
        offset = 0
        for item in self.stack_b:
            item.rect.pos = self.get_rect_pos(self.center_x, offset)
            item.rect.size = self.get_rect_size(item.rank)
            offset += offset_add

    def _move_rect(self, *largs):
        offset = 0
        if self.stack_len > 0:
            offset_add = self.height / self.stack_len
        for item in self.stack_a:
            item.rect.pos = self.get_rect_pos(0, offset)
            offset += offset_add
        offset = 0
        for item in self.stack_b:
            item.rect.pos = self.get_rect_pos(self.center_x, offset)
            offset += offset_add

    def do_move(self, move):
        if move == 'sa' and len(self.stack_a) >= 2:
            self.stack_a[0], self.stack_a[1] = self.stack_a[1], self.stack_a[0]
        elif move == 'sb' and len(self.stack_b) >= 2:
            self.stack_b[0], self.stack_b[1] = self.stack_b[1], self.stack_b[0]
        elif move == 'ss':
            self.do_move('sa')
            self.do_move('sb')
        elif move == 'ra' and len(self.stack_a) >= 2:
            self.stack_a.append(self.stack_a.pop(0))
        elif move == 'rb' and len(self.stack_b) >= 2:
            self.stack_b.append(self.stack_b.pop(0))
        elif move == 'rr':
            self.do_move('ra')
            self.do_move('rb')
        elif move == 'rra' and len(self.stack_a) >= 2:
            self.stack_a.insert(0, self.stack_a.pop())
        elif move == 'rrb' and len(self.stack_b) >= 2:
            self.stack_b.insert(0, self.stack_b.pop())
        elif move == 'rrr':
            self.do_move('rra')
            self.do_move('rrb')
        elif move == 'pa' and len(self.stack_b) >= 1:
            self.stack_a.insert(0, self.stack_b.pop(0))
        elif move == 'pb' and len(self.stack_a) >= 1:
            self.stack_b.insert(0, self.stack_a.pop(0))

    def do_move_rev(self, move):
        if move == 'sa':
            self.do_move('sa')
        elif move == 'sb':
            self.do_move('sb')
        elif move == 'ss':
            self.do_move('ss')
        elif move == 'ra':
            self.do_move('rra')
        elif move == 'rb':
            self.do_move('rrb')
        elif move == 'rr':
            self.do_move('rrr')
        elif move == 'rra':
            self.do_move('ra')
        elif move == 'rrb':
            self.do_move('rb')
        elif move == 'rrr':
            self.do_move('rr')
        elif move == 'pa':
            self.do_move('pb')
        elif move == 'pb':
            self.do_move('pa')

    def do_one_move(self, dt, *largs):
        try:
            move = self.iter_moves_list.next()
            self.do_move(move[1])
            App.get_running_app().move_list.select_item(move[0])
            self.current_move_id = move[0]
        except StopIteration:
            self.pause_status = 1
            self.current_move_id = self.moves_total
        self._move_trigger()
        # print('FPS: %2.4f (real draw: %d) (dt: %2.4f)' % (
        #    Clock.get_fps(), Clock.get_rfps(), dt))

    def do_one_move_rev(self, dt, *largs):
        try:
            move = self.iter_moves_list.prev()
            self.do_move_rev(move[1])
            App.get_running_app().move_list.deselect_item(move[0])
            self.current_move_id = move[0]
        except StopIteration:
            self.pause_status = 1
            self.current_move_id = -1
        self._move_trigger()
        # print('FPS: %2.4f (real draw: %d) (dt: %2.4f)' % (
        #    Clock.get_fps(), Clock.get_rfps(), dt))

    def do_multi_move(self, limit):
        try:
            count = limit - self.current_move_id
            move_list = App.get_running_app().move_list
            for _ in itertools.repeat(None, count):
                move = self.iter_moves_list.next()
                self.do_move(move[1])
                move_list.select_item(move[0])
            self.current_move_id = move[0]
        except StopIteration:
            self.current_move_id = self.moves_total
        self._move_trigger()

    def do_multi_move_rev(self, limit):
        try:
            count = self.current_move_id - limit
            move_list = App.get_running_app().move_list
            for _ in itertools.repeat(None, count):
                move = self.iter_moves_list.prev()
                self.do_move_rev(move[1])
                move_list.deselect_item(move[0])
            self.current_move_id = move[0]
        except StopIteration:
            self.current_move_id = -1
        self._move_trigger()

    def reset_stack(self, *largs):
        self.pause_status = 1
        self.stack_a = []
        self.stack_b = []
        self.canvas.clear()
        self.iter_moves_list.current = 0
        self.current_move_id = -1
        move_list = App.get_running_app().move_list
        move_list.clear_selection()
        move_list.scroll_to_index(0)
        Clock.schedule_once(self.draw_rectangles)

    def on_pause_status(self, instance, value):
        if value == 0:
            self.event_play = Clock.schedule_interval(
                self.do_one_move, 1.0/(2**self.speed_ratio))
        else:
            self.event_play.cancel()

    def on_speed_ratio(self, instance, speed_ratio):
        if self.pause_status == 0:
            self.event_play.cancel()
            self.event_play = Clock.schedule_interval(
                    self.do_one_move, 1.0/(2**self.speed_ratio))


class PushSwapVizApp(App):
    stack_size = NumericProperty()

    def build(self):
        Builder.load_string(KV)
        self.title = "push_swap vizualizer"
        self.parse_cmdline(sys.argv[1:])
        self.create_vars()
        Window.bind(on_key_up=self.key_action)
        self.rect_display = rect_display = RectDisplayWidget(size_hint=(1, 1), gradient=self.gradient)
        rect_display.bind(pause_status=self.play_updt)
        self.btn_play = Button(
            text='▶', size_hint=(.2, 1), size_hint_min_x=dp(50),
            on_press=self.pause_toggle)
        self.btn_step_rev = Button(
            text='-1◀', size_hint=(.2, 1), size_hint_min_x=dp(60),
            on_press=rect_display.do_one_move_rev)
        self.btn_step = Button(
            text='▶+1', size_hint=(.2, 1), size_hint_min_x=dp(60),
            on_press=rect_display.do_one_move)
        self.btn_reset = Button(
            text='↺ Reset', size_hint=(.25, 1), size_hint_min_x=dp(80),
            on_press=rect_display.reset_stack)
        self.slider_speed = Slider(
            min=0, max=7.2, pos_hint={'center_y': .55}, size_hint=(.5, 1),
            cursor_size=(sp(20), sp(20)),
            value=rect_display.speed_ratio, background_width=dp(24))
        self.speed_label = Label(text='Speed', size_hint=(.25, 1))
        self.slider_speed.bind(value=self.on_speed_update)
        self.progress_label = Label(text='START', size_hint=(.2, 1))
        self.moves_label = Label(text='0', size_hint=(.2, 1))
        rect_display.bind(moves_total=self.on_moves_label)
        rect_display.prepare(self.stack_orig, self.moves)
        self.slider_progress = ProgressSlider(
            min=-1, max=rect_display.moves_total, pos_hint={'center_y': .5},
            step=1, cursor_size=(dp(20), dp(20)),
            value=rect_display.current_move_id,
            value_track=True, value_track_color=[1, 0, 0, 1],
            value_track_width=dp(2), background_width=dp(24))
        rect_display.bind(current_move_id=self.update_progress_callback)
        self.slider_progress.bind(value=self.update_move_progress_callback)
        self.slider_progress.bind(on_release=self.release_progress_callback)
        self.slider_progress.bind(on_grab=self.grab_progress_callback)

        self.move_list = MoveScrollList(size_hint=(.15, 1), size_hint_max_x=dp(50))
        self.move_list.populate(self.moves)

        central_pane = BoxLayout()
        central_pane.add_widget(rect_display)
        central_pane.add_widget(self.move_list)
        progress_pane = BoxLayout(
            size_hint=(1, None), height=dp(30), spacing=dp(2))
        progress_pane.add_widget(self.progress_label)
        progress_pane.add_widget(self.slider_progress)
        progress_pane.add_widget(self.moves_label)
        ctrl_btns = BoxLayout(
            size_hint=(1, None), height=dp(30), spacing=dp(2))
        ctrl_btns.add_widget(self.btn_play)
        ctrl_btns.add_widget(self.btn_step_rev)
        ctrl_btns.add_widget(self.btn_step)
        ctrl_btns.add_widget(self.btn_reset)
        ctrl_btns.add_widget(self.speed_label)
        ctrl_btns.add_widget(self.slider_speed)
        self.root = root = BoxLayout(orientation='vertical')
        root.add_widget(central_pane)
        root.add_widget(progress_pane)
        root.add_widget(ctrl_btns)

        return root

    def update_progress_callback(self, instance, value):
        self.slider_progress.value = value
        if value == -1:
            self.progress_label.text = "START"
        elif value == self.rect_display.moves_total:
            self.progress_label.text = "END"
        else:
            self.move_list.scroll_to_index(int(value))
            self.progress_label.text = str(int(value))

    def release_progress_callback(self, instance):
        self.rect_display.pause_status = instance.pause_prev

    def grab_progress_callback(self, instance):
        instance.pause_prev = self.rect_display.pause_status
        self.rect_display.pause_status = 1

    def update_move_progress_callback(self, instance, value):
        if int(value) > self.rect_display.current_move_id:
            self.rect_display.do_multi_move(int(value))
        elif int(value) < self.rect_display.current_move_id:
            self.rect_display.do_multi_move_rev(int(value))

    def create_vars(self):
        self.create_stack()
        self.create_move_list()

    def create_stack(self):
        if not self.stack_orig:
            self.generate_nblist(self.stack_size)
        self.argv = [str(int) for int in self.stack_orig]

    def create_move_list(self):
        pswap_path = self.push_swap.resolve()
        try:
            self.moves = subprocess.run(
                [pswap_path] + self.argv, capture_output=True, check=True,
                text=True, timeout=12).stdout.splitlines()
        except FileNotFoundError:
            #self.moves = []
            print("push_swap not found! Use -p to provide a path to push_swap.")
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            print("There was an error during the execution of push_swap (segfault maybe?) with the following stack:\n")
            self.on_start()
            print("\nHere are some messages that might help you correct the error:\n")
            print(e)
            sys.exit(1)

    def generate_nblist(self, stack_size):
        if self.continuous:
            up = (stack_size // 2) + (stack_size % 2)
            down = (stack_size // 2)
            self.stack_orig = random.sample(range(-down, up), stack_size)
        else:
            self.stack_orig = random.sample(
                range(-stack_size, stack_size), stack_size)

    def on_start(self):
        print(' '.join(self.argv))

    def on_speed_update(self, instance, speed_ratio):
        self.rect_display.speed_ratio = speed_ratio

    def on_moves_label(self, instance, moves_total):
        self.moves_label.text = "{}".format(moves_total)

    def key_action(self, *args):
        # print("got a key event: %s" % list(args))
        if (args[1] == 32):
            self.pause_toggle(args[0])
        elif (args[1] == 275):
            self.rect_display.do_one_move(args[0])
        elif (args[1] == 276):
            self.rect_display.do_one_move_rev(args[0])

    def pause_toggle(self, event):
        if self.rect_display.pause_status:
            self.rect_display.pause_status = 0
        else:
            self.rect_display.pause_status = 1

    def play_updt(self, *largs):
        if self.rect_display.pause_status:
            self.btn_play.text = "▶"
        else:
            self.btn_play.text = "||"

    def valid_path(self, path):
        tmp_path = pathlib.Path(path)
        if tmp_path.exists():
            return tmp_path
        else:
            raise argparse.ArgumentTypeError(f"given Path(\'{path}\') does not exist")

    def stack_size_int(self, x):
        try:
            x = int(x)
        except ValueError:
            raise argparse.ArgumentTypeError(f"invalid int value: \'{x}\'")
        if x < 0:
            raise argparse.ArgumentTypeError("minimum stack size is 0")
        return x

    def parse_cmdline(self, argv):
        self.stack_size = 100
        self.push_swap = ""
        self.continuous = False
        parser = argparse.ArgumentParser()
        parser.add_argument('integers', metavar='Numbers', type=int, nargs='*',
                    help='A List of numbers for push_swap to sort (optional)')
        parser.add_argument("-s", "--stack-size", metavar='<size>', type=self.stack_size_int, default=100,
                    help='Size of the stack of number (ex: 3 or 5 or 100 or 500)\
                     default 100.')
        parser.add_argument("-c", "--continuous", action='store_true', default=False,
                    help='The number generated are folowing each other by a "1" increment.')
        parser.add_argument("-p", "--push-swap", metavar='<path>', type=self.valid_path,
                    help='The absolute or relative path to your push_swap binary. \
                    if the path is not specified, look for push_swap in the current dir.')
        parser.add_argument("-g", "--gradient", metavar='<id>', default='6',
                    choices=['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
                    help="Chose a color gradient to use (value between 1 and 10). \
                    1 - rainbow blue to red, 2 - rainbow purple to red, 3 - black and white dark, \
                    4 - black and white light, 5 - White to black, 6 (default) - red gradient to black, \
                    7 - purple gradient to black, 8 - red gradient to white, 9 - white to purple, 10 - sunset")
        self.cmdline_args = parser.parse_args()
        self.continuous = self.cmdline_args.continuous
        self.stack_size = self.cmdline_args.stack_size
        self.push_swap = self.cmdline_args.push_swap
        self.stack_orig = self.cmdline_args.integers
        self.gradient = self.cmdline_args.gradient
        if self.push_swap is None:
            tmp_path = pathlib.Path(DEFAULT_PSWAP_PATH)
            if tmp_path.exists():
                self.push_swap = tmp_path
            else:
                parser.print_help()
                sys.exit(1)


if __name__ == "__main__":
    PushSwapVizApp().run()
