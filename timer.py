import cudatext as ct


class Prop:
    def __get__(self, instance, owner):
        if not instance:
            return self
        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        if instance.__dict__['_is_started']:
            raise AttributeError('First need stop timer')
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name


class Timer:
    """Perform action on timers.
    Many different timers allowed, they work at the same time,
    each uniq callback - makes new timer with its own interval.
    To stop some timer, you must specify same callback as on start.

    :param callback: Callback which is called on timer tick, see below
    :param interval: Timer delay in msec, 150 or bigger.
        Specify it only on starting (ignored on stopping)
    :param tag: Some string, if not empty, it will be parameter to callback.
        If empty, callback is called without additional params

    .. note::
        Callbacks must be declared as\\:

        .. code-block:: python

            # function
            def my(tag='', info=''):
                pass
            # method
            class Command:
                def my(self, tag='', info=''):
                    pass

    """
    callback = Prop()
    """
    :getter: Return callback
    :setter: Set callback. Must be set before start.
    """
    interval = Prop()
    """
    :getter: Return timer tick interval
    :setter: Set interval. Must be set before start.
    """
    tag = Prop()
    """
    :getter: Return tag
    :setter: Set tag. Must be set before start."""

    def __init__(self, callback=None, interval=150, tag=""):
        self._is_started = False
        self.callback = callback
        self.interval = interval
        self.tag = tag

    def start(self):
        """Start timer, for infinite ticks.
        If timer for such callback is already created, then it's restated.
        """
        self._is_started = True
        ct.timer_proc(ct.TIMER_START,
                      callback=self.callback,
                      interval=self.interval,
                      tag=self.tag)

    def start_once(self):
        """Start timer,  for single tick.
        If timer for such callback is already created, then it's restated.
        """
        self._is_started = True
        return ct.timer_proc(ct.TIMER_START_ONE,
                             callback=self.callback,
                             interval=self.interval,
                             tag=self.tag)

    def stop(self):
        """Stop timer"""
        self._is_started = False
        return ct.timer_proc(ct.TIMER_STOP,
                             callback=self.callback,
                             interval=self.interval,
                             tag=self.tag)

    def delete(self):
        """Stop timer, and delete it from list of timers.
        Usually don't use it, use only to save memory if created lot of timers
        """
        return ct.timer_proc(ct.TIMER_DELETE,
                             callback=self.callback,
                             interval=self.interval,
                             tag=self.tag)
