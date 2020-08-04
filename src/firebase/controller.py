import logging
import time

from firebase.connector import FireBaseConnector
from patterns import Patterns
from rgb import RGB

fire_logger = logging.getLogger("fire_logger")

# since the firebase updater will call the listener a lot
# during the slider value change, we need a way to skip too frequent updates.
# with the frequency function the call to the listener will be
# skipped if there was a previous call less than '__call_resolution' seconds before

__last_call = time.time()
__call_resolution = 0.1


def frequency(listener):
    """
    Decoratorr to skip call to the firebase listener
    :param listener:
    :return:
    """

    def wrap(*args):
        # get the global time of the last call
        global __last_call
        # check that the last call was made after tot secs
        if time.time() - __last_call > __call_resolution:
            # if yes call the listener and update time
            ret = listener(*args)
            __last_call = time.time()
            return ret
        # else skip

    return wrap


class FireBaseController(FireBaseConnector):
    """
    Controller for the firebase databse.
    Extends the FireBaseConnector to allow modification of the pixels in both pc or rpi mode
    """

    def __init__(self, credential_path, database_url, handler, pixels, debug=None):

        # dummy pattern to avoid exception
        self.pattern = Patterns['Steady'](rate=10, handler=handler, pixels=pixels)

        super().__init__(credential_path=credential_path, database_url=database_url, debug=debug)

        self.handler = handler(pixels)
        self.pixels = pixels

        # choose correct pattern and start it
        cur_pattern = self.get_cur_pattern()
        rate = self.get_rate()
        rgba = self.get_rgba()
        self.pattern = Patterns[cur_pattern](rate=rate, color=rgba, handler=self.handler, pixels=pixels)
        self.pattern.start()

    def close(self):
        super().close()
        self.pattern.close()
        self.handler.close()

    @frequency
    def listener_method(self, event):
        """
        Main listener, called when db is updated
        :param event: dict
        :return: None
        """

        if not super(FireBaseController, self).listener_method(event):
            return

        to_log = f"{event.event_type}\n{event.path}\n{event.data}"
        fire_logger.debug(to_log)

        path = event.path
        data=event.data

        if "rate" in path:
            self.pattern.set_rate(data)

        # stop and restart pattern if required
        elif "cur_pattern" in path:
            # get values
            pattern_choice = data
            rate = self.get_rate()
            rgba = self.get_rgba()
            # stop and restart
            self.pattern.close()
            self.pattern = Patterns[pattern_choice](rate=rate, color=rgba, handler=self.handler, pixels=self.pixels)
            self.pattern.color_all(RGB())
            self.pattern.start()

        # update rgba
        elif "RGBA" in path:
            self.floor_rgba(path,data)

        # update pattern attributes
        elif "pattern_attributes" in path:
            self.ps_attrs_getter(path, data)

        else:
            raise NotImplementedError(f"No such field for {event.path}")

    def ps_attrs_getter(self,path, data):
        """
        Converts and updates values from db
        :param key: str, name of db variable AND of class attribute
        :param data: str, data to convert
        :return:
        """

        pattern=path.split("/")[2]
        modifier= path.split("/")[3]

        # check that the values to modify are indeed of the current pattern
        assert self.pattern.pattern_name == pattern
        # and update pattern
        self.pattern.update_args(**{modifier:data})

    def floor_rgba(self, path ,data):
        """
        Update RGBA values taking them from the database
        :return:
        """
        # get the rgba attribute to update
        rgb_attr=path.split("/")[-1]

        # if is random
        if rgb_attr == "random":
            # update the randomize_color attribute of pattern
            self.pattern.update_args(randomize_color=bool(data))
        else:
            # if is r,g,b,a, update just the value in the dictionary
            self.pattern.color.__dict__[rgb_attr]=int(data)


