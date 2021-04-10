"""Bubbles app main"""
import kivy
import kivy.graphics as kg
from kivy.properties import ListProperty
from kivy.uix.widget import Widget
kivy.require('1.9.0')

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.core.audio import SoundLoader

import random

class Bubble:
    __slots__ = ['x', 'y', 'lifetime', 'distance', 'size', 'drawsize']

    def __init__(self, width, height, x=None, y=None, size=None, distance=None):
        """Size is random if one is not provided"""
        self.x = x or random.randint(0, width)
        self.y = y or 0
        self.size = size or random.randint(1, 3)
        self.drawsize = [8, 34, 55][self.size-1]
        self.lifetime = random.randint(height / self.size, height)
        self.distance = distance or random.randint(0, 4)

    @property
    def speed(self):
        return 4 - self.size

    def burst(self):
        """Create the list from the burst"""
        if self.size == 1:
            return []  # nothing
        return [
            {'x': self.x + random.randint(-self.size * 2, self.size * 2), 'y': self.y,
             'size': self.size - 1, 'distance': self.distance}
        ] * 2


class BubbleSystem:
    def __init__(self, canvas_size, bubble_limit=40):
        # Fill the system with bubbles - leave room for large bubbles to burst
        self.limit = bubble_limit
        self.pressed = [None, None]
        self.bubbles = list()
        self.remaining = bubble_limit
        self.width = 100
        self.height = 100
        # Queue of bubbles to make from a burst
        self.create_queue = []

        self.pop_sounds = [
            SoundLoader.load("pop.wav"),
            SoundLoader.load("pop2.wav"),
            SoundLoader.load("pop3.wav"),
            SoundLoader.load("pop4.wav")
        ]

    def make_pop(self):
        random.choice(self.pop_sounds).play()

    def resize(self, size):
        self.width, self.height = size

    def update(self):
        """Update the system"""
        # if we have a queue, and space - make a bubble
        if len(self.bubbles) < self.limit:
            # priority - fixed, random
            if self.create_queue:
                # kill those too old - 12 is at least 3 frames ago.
                if len(self.create_queue) > 12:
                    self.create_queue = self.create_queue[-12:]
                # pop the oldest
                queued_item = self.create_queue[0]
                self.create_queue = self.create_queue[1:]
                # make it a bubble
                new_bubble = Bubble(self.width, self.height, **queued_item)
            else:
                # Nothing queued - go ahead and make a random one
                new_bubble = Bubble(self.width, self.height)
            self.bubbles.append(new_bubble)
        if self.pressed != [None, None]:
            # print(repr(self.pressed))
            press_coords = list(self.pressed)
            self.pressed = [None, None]
        else:
            press_coords = None
        # now update all the bubbles
        for bubble in iter(self.bubbles):
            # bubbles die at the top, or outside the canvas
            if bubble.y < 0 or bubble.y >= self.height or bubble.x > self.width:
                self.bubbles.remove(bubble)
                self.make_pop()
                continue
            # Decrement bubble lifetime
            bubble.lifetime -= 1
            if bubble.lifetime <= 0:
                # burst!
                self.make_pop()
                self.create_queue.extend(bubble.burst())
                self.bubbles.remove(bubble)
                continue
            if press_coords:
                if (bubble.x + bubble.drawsize >= press_coords[0] >= bubble.x)\
                    and (bubble.y + bubble.drawsize >= press_coords[1] >= bubble.y):
                    # burst!
                    self.create_queue.extend(bubble.burst())
                    self.make_pop()
                    self.bubbles.remove(bubble)
                    continue
            bubble.y += bubble.speed
            bubble.x += random.randint(-1, 1)


class BubbleWidget(Widget):
    bubble_count = 40
    bubble_color = (0.8, 0.9, 1, 0.7)
    background_color = (0.5, 0.7, 0.8, 1)

    def __init__(self, **kwargs):
        super(BubbleWidget, self).__init__(**kwargs)
        self.system = BubbleSystem(100, 100)
        self.bind(pos=self.update_canvas)
        self.bind(size=self.update_canvas)
        self.update_canvas()
        Clock.schedule_interval(self.frame, 1 / 30.)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.system.pressed = touch.pos
            return True
        return super(BubbleWidget, self).on_touch_down(touch)

    def update_canvas(self, *args):
        self.system.resize(self.size)

    def frame(self, *args):
        self.system.update()
        self.draw_system()

    def draw_system(self):
        self.canvas.clear()
        with self.canvas:
            kg.Color(*self.background_color)
            kg.Rectangle(pos=(0, 0), size=self.size)
            # context to draw in
            for bubble in self.system.bubbles:
                kg.Color(0, 0, 0, 1)
                kg.Ellipse(pos=(bubble.x, bubble.y), size=(bubble.drawsize, bubble.drawsize))
                kg.Color(*self.bubble_color, mode='rgba')
                kg.Ellipse(pos=(bubble.x + 1, bubble.y + 1), size=(bubble.drawsize - 2, bubble.drawsize - 2))

class BubbleApp(App):
    def build(self):
        return BubbleWidget()

if __name__ == "__main__":
    BubbleApp().run()
