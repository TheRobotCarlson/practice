"""
Crypto Price data
Author: Brian Carlson
date: 2021-08-23
"""

import os
import json
import random
import datetime
from typing import Any, Dict, Iterable, List, Tuple
from dataclasses import dataclass, field
import statistics

import urllib.request

def gen_data():
    """
    Generate sample data for testing endpoint without internet / with known values
    """
    num_points = 30*24
    today = datetime.datetime.now()

    data = []
    gen_nums = random.choices(range(num_points), k=num_points)

    for i, gen_num in enumerate(gen_nums):
        gen_date = today - datetime.timedelta(hours=num_points - i)
        data.append((gen_date, float(gen_num)))

    return data

# This fetch gets cached if we put it outside the function
FETCH_URL = os.environ.get("FETCH_URL", "https://api.coinranking.com/v1/public/coin/1/history/30d")

def fetch_and_parse():
    """
    Small enough file that we have no need to stream read and we can load all in memory
    """
    url = FETCH_URL

    if url is None:
        return

    raw_file = urllib.request.urlopen(url)
    raw_json = raw_file.read()

    data = json.loads(raw_json)
    for row in data["data"]["history"]:
        # python uses second format and this is in millisecond format
        date_val =  datetime.datetime.fromtimestamp(row["timestamp"] / 1000)
        price_val = float(row["price"])
        yield date_val, price_val


PriceDateEntry = Tuple[datetime.datetime, float]

@dataclass
class DailyPriceStats:
    """
    Generalized daily price data handler. Good for hourly, daily-aggregate statistics.
    This is a base class that needs the output_format be overridden.
    """
    # current data points
    curr_val: float = None
    curr_date: datetime.datetime = None

    # last data point (last hour)
    prev_val: float = None
    prev_date: datetime.datetime = None

    # last day's SOD data point
    prev_day_val: float = None

    def output_format(self) -> Dict[str, Any]:
        """
        Format output that gets yielded on each day change by the generator
        """
        raise NotImplementedError

    def hourly_update(self):
        """
        Process ran on every data point
        """

    def post_daily_update(self):
        """
        Process ran at the end of every day cycle after output
        """

    @property
    def new_day(self):
        """
        Calculates whether the current settings are a new day or not
        """
        return self.prev_date is None or \
            (self.prev_date is not None and self.prev_date.day != self.curr_date.day)

    def act(self, data: Iterable[PriceDateEntry]) -> Iterable[Dict[str, Any]]:
        """
        Iterate over data hour by hour and emit values on each change of day and the end
        """

        for line in data:
            self.curr_date, self.curr_val = line

            # new day, emit changes and update SOD data
            if self.new_day:
                yield self.output_format()
                self.post_daily_update()
                self.prev_day_val = self.curr_val

            self.hourly_update()

            self.prev_date = self.curr_date
            self.prev_val = self.curr_val

        self.hourly_update()
        yield self.output_format()


@dataclass
class Schema1(DailyPriceStats):
    """
    Schema1 outputs data every day in the schema given in the examples below.

    >>> stats = Schema1()
    >>> generator = stats.act([\
            (datetime.datetime(2020, 1, 1 ), 1), (datetime.datetime(2020, 1, 2), 2)\
        ])
    >>> next(generator)
    {'date': '2020-01-01T00:00:00', 'price': '1.00', 'direction': None, 'change': None,\
 'dayOfWeek': 'Wednesday', 'highSinceStart': None, 'lowSinceStart': None}
    >>> next(generator)
    {'date': '2020-01-02T00:00:00', 'price': '2.00', 'direction': 'up', 'change': '1.00',\
 'dayOfWeek': 'Thursday', 'highSinceStart': True, 'lowSinceStart': False}
    """
    _min_val: float = None
    _max_val: float = None

    @property
    def day_of_week(self) -> str:
        """
        Returns the string form of the day of the week
        """
        return self.curr_date.strftime("%A")

    @property
    def change(self) -> float:
        """
        SOD to SOD change of value
        """
        # First day
        if self.prev_day_val is None:
            return None
        return self.curr_val - self.prev_day_val

    @property
    def direction(self) -> str:
        """
        SOD to SOD direction of change
        """
        # First day
        if self.change is None:
            return None
        return "up" if self.change > 0 else "down" if self.change < 0 else "same"

    @property
    def high_since_start(self) -> float:
        """
        Checks SOD to SOD highs to see if this is a high. Only evaluates SOD to SOD values.
        """
        # First day
        if self._max_val is None:
            self._max_val = self.curr_val
            return None

        if self.curr_val > self._max_val:
            self._max_val = self.curr_val
            return True

        return False

    @property
    def low_since_start(self) -> float:
        """
        Checks SOD to SOD highs to see if this is a high. Only evaluates SOD to SOD values.
        """
        # First day
        if self._min_val is None:
            self._min_val = self.curr_val
            return None

        if self.curr_val < self._min_val:
            self._min_val = self.curr_val
            return True

        return False

    def output_format(self) -> Dict[str, Any]:
        return {
            "date": self.curr_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "price": f"{self.curr_val:0.2f}",
            "direction": self.direction,
            "change": f"{self.change:0.2f}" if self.change else None,
            "dayOfWeek": self.day_of_week,
            "highSinceStart": self.high_since_start,
            "lowSinceStart": self.low_since_start,
        }

@dataclass
class Schema2(DailyPriceStats):
    """
    Schema2 outputs data every day in the schema given in the examples below.

    >>> stats = Schema2()
    >>> generator = stats.act([\
        (datetime.datetime(2020, 1, 1 ), 1), (datetime.datetime(2020, 1, 2), 2)\
    ])
    >>> next(generator)
    {'date': '2020-01-01T00:00:00', 'price': '1.00', 'dailyAverage': 1, 'dailyVariance': 0,\
 'volatilityalert': False}
    >>> next(generator)
    {'date': '2020-01-02T00:00:00', 'price': '2.00', 'dailyAverage': 1, 'dailyVariance': 0,\
 'volatilityalert': False}
    """
    vals: List[float] = field(default_factory=list)

    def daily_average(self):
        """
        Computes the average of values for the day
        """
        if len(self.vals) < 1:
            return self.curr_val

        return statistics.mean(self.vals)

    def daily_variance(self):
        """
        Computes the variance of values for the day
        """
        if len(self.vals) < 2:
            return 0

        return statistics.variance(self.vals)

    def volatility_alert(self):
        """
        Returns true/false if any price inside day is outside 2 standard deviations.

        This one is a bit more complicated since you can't just compute the standard deviation
        over the entire day's worth of values, otherwise you run the risk of lookahead bias.
        There are optimized ways to compute streaming stddev and means, but for the sake of
        simplicity, I've omitted those here. In high speed applications, those would be essential.

        For an application of this scale, the speed should hardly be noticeable.
        """
        for i in range(len(self.vals)):
            selected_vals = self.vals[:i]
            # std isn't valid for < 2 values, skip first value
            if len(selected_vals) < 2:
                continue
            std_dev = statistics.stdev(selected_vals)
            new_mean = statistics.mean(selected_vals)
            if -1*std_dev*2 < selected_vals[-1] - new_mean < std_dev*2:
                return True

        return False

    def hourly_update(self):
        self.vals.append(self.curr_val)
        return super().hourly_update()

    def post_daily_update(self):
        self.vals = []
        return super().post_daily_update()

    def output_format(self) -> Dict[str, Any]:
        return {
            "date": self.curr_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "price": f"{self.curr_val:0.2f}",
            "dailyAverage": self.daily_average(),
            "dailyVariance": self.daily_variance(),
            "volatilityalert": self.volatility_alert()
        }


def schema1_handler(event, context): # pylint: disable=unused-argument
    """
    Lambda Handler for the first schema
    """
    output_vals = list(Schema1().act(fetch_and_parse()))

    response = {
        "statusCode": 200,
        "body": json.dumps(output_vals)
    }

    return response

def schema2_handler(event, context): # pylint: disable=unused-argument
    """
    Lambda Handler for the second schema
    """
    output_vals = list(Schema2().act(fetch_and_parse()))

    response = {
        "statusCode": 200,
        "body": json.dumps(output_vals)
    }

    return response

if __name__ == "__main__":
    print(list(Schema1().act(gen_data())))
    print(list(Schema2().act(gen_data())))

    print(list(Schema1().act(fetch_and_parse())))
    print(list(Schema2().act(fetch_and_parse())))
