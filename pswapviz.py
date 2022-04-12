import os
import sys
import getopt
import random
import subprocess
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
        self.rect = Rectangle(pos=pos, size=size)


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
        move = self.moves[self.current]
        self.current += 1
        return move

    def prev(self):
        if(self.current <= 0):
            raise StopIteration
        self.current -= 1
        if self.current >= self.max:
            self.current = self.max - 1
        move = self.moves[self.current]
        return move


class RectDisplayWidget(Widget):
    pause_status = NumericProperty(1)

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
        self.nb_moves = len(moves_list)
        if (self.stack_len != 0):
            self.max = max(stack)
            self.min = min(stack)
        Clock.schedule_once(self.draw_rectangles)

    def set_color(self, rank):
        # c = Color((1 - rank)/1.5, 1, 0.85, mode='hsv')
        #c = Color((1 - rank)/1.25, 1, 1, mode='hsv')  # gradient sympa
        # c = Color(0, 0, (1 - rank)/1.5, mode='hsv') # black and white pas lisible
        #c = Color(0, 0, 1 - (rank/1.25), mode='hsv') # good black and white
        c = Color(0, 0, (rank/1.5) + 0.25, mode='hsv') #black and white reverse
        # c = Color(0.45, 0.5, 1 - (rank/1.25), mode='hsv') one color gradient to black
        #c = Color(((rank)/1.25) + 0.25, (1 - rank)/1.25, (1 - rank)/1.25, mode='hsv') not good
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
            self.stack_a.append(self.stack_a[0])
            del self.stack_a[0]
        elif move == 'rb' and len(self.stack_b) >= 2:
            self.stack_b.append(self.stack_b[0])
            del self.stack_b[0]
        elif move == 'rr':
            self.do_move('ra')
            self.do_move('rb')
        elif move == 'rra' and len(self.stack_a) >= 2:
            self.stack_a.insert(0, self.stack_a[-1])
            del self.stack_a[-1]
        elif move == 'rrb' and len(self.stack_b) >= 2:
            self.stack_b.insert(0, self.stack_b[-1])
            del self.stack_b[-1]
        elif move == 'rrr':
            self.do_move('rra')
            self.do_move('rrb')
        elif move == 'pa' and len(self.stack_b) >= 1:
            self.stack_a.insert(0, self.stack_b[0])
            del self.stack_b[0]
        elif move == 'pb' and len(self.stack_a) >= 1:
            self.stack_b.insert(0, self.stack_a[0])
            del self.stack_a[0]

    def do_move_rev(self, move):
        if move == 'sa':
            return self.do_move('sa')
        if move == 'sb':
            return self.do_move('sb')
        if move == 'ss':
            return self.do_move('ss')
        if move == 'ra':
            return self.do_move('rra')
        if move == 'rb':
            return self.do_move('rrb')
        if move == 'rr':
            return self.do_move('rrr')
        if move == 'rra':
            return self.do_move('ra')
        if move == 'rrb':
            return self.do_move('rb')
        if move == 'rrr':
            return self.do_move('rr')
        if move == 'pa':
            return self.do_move('pb')
        if move == 'pb':
            return self.do_move('pa')

    def do_one_move(self, dt, *largs):
        try:
            self.do_move(self.iter_moves_list.next())
        except StopIteration:
            #self.dispatch('on_end_reached')
            self.pause_status = 1
            #self.event_play.cancel()
        self._move_trigger()
        #print("bip")
        #print('FPS: %2.4f (real draw: %d) (dt: %2.4f)' % (
        #    Clock.get_fps(), Clock.get_rfps(), dt))

    def do_one_move_rev(self, dt, *largs):
        try:
            self.do_move_rev(self.iter_moves_list.prev())
        except StopIteration:
            self.pause_status = 1
            #self.dispatch('on_end_reached')
            #self.event_rev.cancel()
        self._move_trigger()
        #print('FPS: %2.4f (real draw: %d) (dt: %2.4f)' % (
        #    Clock.get_fps(), Clock.get_rfps(), dt))

    def reset_stack(self, *largs):
        self.pause_status = 1
        self.stack_a = []
        self.stack_b = []
        self.canvas.clear()
        self.iter_moves_list.current = 0
        Clock.schedule_once(self.draw_rectangles)
        #self.event_rev = Clock.schedule_interval(self.do_one_move_rev, 1.0/100.0)

    def on_pause_status(self, instance, value):
        if value == 0:
            self.event_play = Clock.schedule_interval(
                self.do_one_move, 1.0/1000.0)
        else:
            self.event_play.cancel()


class PushSwapVizApp(App):
    i = NumericProperty()
    speed = NumericProperty()
    stack_size = NumericProperty()
    total_count_var = NumericProperty()

    def build(self):
        Builder.load_string(KV)
        self.title = "push_swap vizualizer"
        self.parse_cmdline(sys.argv[1:])
        self.create_vars()
        self.rect_display = rect_display = RectDisplayWidget()
        rect_display.bind(pause_status=self.play_updt)
        self.btn_play = Button(text='▶', size_hint=(.25, 1),
                               on_press=self.pause_toggle)
        self.btn_step_rev = Button(text='-1◀', size_hint=(.25, 1),
                                   on_press=rect_display.do_one_move_rev)
        self.btn_step = Button(text='▶+1', size_hint=(.25, 1),
                               on_press=rect_display.do_one_move)
        btn_reset = Button(text='↺ Reset',
                           on_press=rect_display.reset_stack)

        layout = BoxLayout(size_hint=(1, None), height=50, spacing=5)
        layout.add_widget(self.btn_play)
        layout.add_widget(self.btn_step_rev)
        layout.add_widget(self.btn_step)
        layout.add_widget(btn_reset)
        self.root = root = BoxLayout(orientation='vertical')
        root.add_widget(rect_display)
        root.add_widget(layout)

        rect_display.prepare(self.stack_orig, self.moves)

        return root

    def create_vars(self):
        self.i = 0
        self.i_count = 0
        self.speed = 5.7
        self.create_stack()
        self.create_move_list()
        self.total_count_var = len(self.moves)

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

    def parse_cmdline(self, argv):
        self.stack_size = 100
        self.push_swap = ""
        self.continuous = False
        try:
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

    def print_usage_exit(self, status):
        print('python3 pyviz.py -- [-c] [-s <stack_size>] [-p <push_swap_path>]\n')
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
    gui = PushSwapVizApp()
    gui.run()
