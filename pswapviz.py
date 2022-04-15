import os
import sys
import getopt
import random
import subprocess
import itertools
import argparse
import pathlib
os.environ["KIVY_NO_ARGS"] = "1"
os.environ["KIVY_NO_FILELOG"] = "1"
#os.environ["KIVY_NO_CONSOLELOG"] = "1"
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.metrics import sp, dp
from kivy.lang import Builder
from functools import partial


KV = '''
<Label>:
    font_name: 'DejaVuSans'
'''


RELATIVE_PATH = r'push_swap'


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
        if touch.grab_current != self:
            self.dispatch('on_grab')
            return True

    def on_touch_up(self, touch):
        super(ProgressSlider, self).on_touch_up(touch)
        if touch.grab_current == self:
            self.dispatch('on_release')
            return True


class RectDisplayWidget(Widget):
    pause_status = NumericProperty(1)
    speed_ratio = NumericProperty(10.0)
    moves_total = NumericProperty(0)
    current_move_id = NumericProperty(0)

    def __init__(self, **kwargs):
        #self.register_event_type('on_end_reached')
        self.stack_a = []
        self.stack_b = []
        self.stack_len = 0
        self.max, self.min = (0, 0)
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

    def set_color(self, rank):
        # c = Color((1 - rank)/1.5, 1, 0.85, mode='hsv')
        #c = Color((1 - rank)/1.25, 1, 1, mode='hsv')  # gradient sympa
        # c = Color(0, 0, (1 - rank)/1.5, mode='hsv') # black and white pas lisible
        #c = Color(0, 0, 1 - (rank/1.25), mode='hsv') # good black and white
        #c = Color(0, 0, (rank/1.5) + 0.25, mode='hsv') #black and white reverse
        c = Color(1, .75, 1 - (rank/1.25), mode='hsv') #one color gradient to black
        #c = Color(((rank)/1.25) + 0.25, (1 - rank)/1.25, (1 - rank)/1.25, mode='hsv') #not good
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
                    self.set_color(rank)
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
            self.current_move_id = move[0]
        except StopIteration:
            #self.dispatch('on_end_reached')
            self.pause_status = 1
        self._move_trigger()
        #print('FPS: %2.4f (real draw: %d) (dt: %2.4f)' % (
        #    Clock.get_fps(), Clock.get_rfps(), dt))

    def do_one_move_rev(self, dt, *largs):
        try:
            move = self.iter_moves_list.prev()
            self.do_move_rev(move[1])
            self.current_move_id = move[0]
        except StopIteration:
            self.pause_status = 1
            #self.dispatch('on_end_reached')
        self._move_trigger()
        #print('FPS: %2.4f (real draw: %d) (dt: %2.4f)' % (
        #    Clock.get_fps(), Clock.get_rfps(), dt))

    def do_multi_move(self, limit):
        count = limit - self.current_move_id
        for _ in itertools.repeat(None, count):
            move = self.iter_moves_list.next()
            self.do_move(move[1])
        self.current_move_id = move[0]
        self._move_trigger()

    def do_multi_move_rev(self, limit):
        count = self.current_move_id - limit
        for _ in itertools.repeat(None, count):
            move = self.iter_moves_list.prev()
            self.do_move_rev(move[1])
        self.current_move_id = move[0]
        self._move_trigger()

    def reset_stack(self, *largs):
        self.pause_status = 1
        self.stack_a = []
        self.stack_b = []
        self.canvas.clear()
        self.iter_moves_list.current = 0
        self.current_move_id = 0
        Clock.schedule_once(self.draw_rectangles)
        #self.event_rev = Clock.schedule_interval(self.do_one_move_rev, 1.0/100.0)

    def on_pause_status(self, instance, value):
        if value == 0:
            self.event_play = Clock.schedule_interval(
                self.do_one_move, 1.0/self.speed_ratio)
        else:
            self.event_play.cancel()

    def on_speed_ratio(self, instance, speed_ratio):
        if self.pause_status == 0:
            self.event_play.cancel()
            self.event_play = Clock.schedule_interval(
                    self.do_one_move, 1.0/speed_ratio)


class PushSwapVizApp(App):
    stack_size = NumericProperty()

    def build(self):
        Builder.load_string(KV)
        self.title = "push_swap vizualizer"
        self.parse_cmdline(sys.argv[1:])
        self.create_vars()
        self.rect_display = rect_display = RectDisplayWidget()
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
        self.slider_speed = Slider(min=1, max=150, pos_hint={'center_y': .55},
                                   size_hint=(.5, 1), step=10,
                                   cursor_size=(sp(20), sp(20)),
                                   value=rect_display.speed_ratio,
                                   background_width=dp(24))
        self.speed_label = Label(text='Speed', size_hint=(.25, 1))
        self.slider_speed.bind(value=self.on_speed_update)
        self.progress_label = Label(text='0', size_hint=(.2, 1))
        self.moves_label = Label(text='0', size_hint=(.2, 1))
        rect_display.bind(moves_total=self.on_moves_label)
        rect_display.prepare(self.stack_orig, self.moves)
        self.slider_progress = ProgressSlider(
            min=0, max=rect_display.moves_total - 1, pos_hint={'center_y': .5},
            step=1, cursor_size=(dp(20), dp(20)),
            value_track=True, value_track_color=[1, 0, 0, 1],
            value_track_width=dp(2), background_width=dp(24))
        rect_display.bind(current_move_id=self.update_progress_callback)
        self.slider_progress.bind(value=self.update_move_progress_callback)
        self.slider_progress.bind(on_release=self.release_progress_callback)
        self.slider_progress.bind(on_grab=self.grab_progress_callback)

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
        root.add_widget(rect_display)
        root.add_widget(progress_pane)
        root.add_widget(ctrl_btns)

        return root

    def update_progress_callback(self, instance, value):
        self.slider_progress.value = value
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
        self.generate_nblist(self.stack_size)

    def create_move_list(self):
        if self.push_swap == "":
            dirname = os.path.dirname(os.path.abspath(__file__))
            PUSHS_PATH = os.path.join(dirname, RELATIVE_PATH)
        else:
            PUSHS_PATH = self.push_swap
        try:
            self.moves = \
                subprocess.run([PUSHS_PATH] + self.argv,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               text=True, timeout=12).stdout.splitlines()
        except FileNotFoundError:
            self.moves = []

    def generate_nblist(self, stack_size):
        if self.continuous:
            up = (stack_size // 2) + (stack_size % 2)
            down = (stack_size // 2)
            self.stack_orig = random.sample(range(-down, up), stack_size)
        else:
            self.stack_orig = random.sample(range(-stack_size, stack_size),
                                            stack_size)
        self.argv = [str(int) for int in self.stack_orig]

    def on_start(self):
        print(' '.join(self.argv))

    def on_speed_update(self, instance, speed_ratio):
        self.rect_display.speed_ratio = speed_ratio

    def on_moves_label(self, instance, moves_total):
        self.moves_label.text = "{}".format(moves_total)

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
            raise argparse.ArgumentTypeError(f"Given Path({path}) is not a valid path.")

    def parse_cmdline(self, argv):
        self.stack_size = 100
        self.push_swap = ""
        self.continuous = False
        parser = argparse.ArgumentParser()
        parser.add_argument('integers', metavar='Number', type=int, nargs='*',
                    help='List of custom numbers for push_swap')
        parser.add_argument("-s", "--stack-size", metavar='size', type=int, default=100,
                    help='Size of the stack of number (ex: 3 or 5 or 100 or 500)\
                     default 100.')
        parser.add_argument("-c", "--continuous", action='store_true', default=False,
                    help='The number generated are folowing each other by a "1" increment.')
        parser.add_argument("-p", "--push-swap", metavar='path', type=self.valid_path,
                    help='The absolute or relative path to your push_swap folder or binary')

        self.cmdline_args = parser.parse_args()
        print(self.cmdline_args.integers)
        print(self.cmdline_args.push_swap)
        sys.exit(2)
        """ try:
            opts, args = getopt.getopt(argv, "hcs:p:",
                                       ["help", "continous",
                                        "stack-size=", "push-swap="])
        except getopt.GetoptError:
            self.print_usage_exit(2)
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                self.print_usage_exit()
            elif opt in ("-c", "--continuous"):
                self.continuous = True
            elif opt in ("-s", "--stack-size"):
                try:
                    self.stack_size = int(arg)
                    if self.stack_size < 0:
                        self.print_usage_exit(0)
                except ValueError:
                    self.print_usage_exit(2)
            elif opt in ("-p", "--push-swap"):
                self.push_swap = arg
            else:
                self.print_usage_exit(2) """

    def print_usage_exit(self, status):
        print('python3 pyviz.py [-c] [-s <stack_size>] [-p <push_swap_path>]\n')
        print(' -h, --help')
        print('\tPrint this help dialog\n')
        print(' -c, --continuous')
        print('\tThe number generated are folowing each other by a "1" increment.')
        print('\t\t$ python3 pyviz.py -c -s 4')
        print('\tWill generate for example the sequence: 0 -1 2 1\n')
        print(' -s, --stack-size <Integer>')
        print('\tThe size of the stack of number (ex: 3 or 5 or 100 or 500)')
        print('\tIf not specified, the default is set to 100.')
        print('\t\t$ python3 pyviz.py -s 4')
        print('\tWill generate for example the sequence: 1 0 -3 -2\n')
        print(' -p, --push-swap <Path>')
        print('\tThe absolute or relative path to your push_swap binary')
        sys.exit(status)


if __name__ == "__main__":
    PushSwapVizApp().run()
