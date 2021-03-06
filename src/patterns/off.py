from patterns.default import Default
from utils.rgb import RGB


class Off(Default):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pattern_name = "Off"

    @property
    def rate(self):
        return 1000000

    @rate.setter
    def rate(self, value):
        pass

    def fill(self):
        for idx in range(self.strip_length):
            self.pixels[idx]['color'] = RGB()
