import json
import random
import datetime
from typing import Any, Dict, Iterable, List, Union
from dataclasses import dataclass, field
import math
import statistics

import more_itertools as mtools

def gen_data():
    num_points = 30*24
    today = datetime.datetime.now()

    data = []
    gen_nums = random.choices(range(num_points), k=num_points)

    for i, gen_num in enumerate(gen_nums):
        gen_date = today - datetime.timedelta(hours=num_points - i)
        data.append({
            "datetime": gen_date,
            "value": gen_num
        })
    
    return data

DAY_INDEX = [
    "sunday",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday"
]

PriceDateEntry = Dict[str, Union[float, datetime.datetime]]

class Schema:
    # current data points
    curr_val: float = None
    curr_date: datetime.datetime = None
    
    # last data point (last hour)
    prev_val: float = None
    prev_date: datetime.datetime = None

    # last day
    prev_day_val: float = None

    def output_format(self) -> Dict[str, Any]:
        raise NotImplementedError

    def hourly_update(self):
        pass

    def post_daily_update(self):
        pass

    def act(self, data: Iterable[PriceDateEntry]) -> Iterable[Dict[str, Any]]:
        
        for line in data:
            self.curr_val = line["value"]
            self.curr_date = line["datetime"]
            self.hourly_update()
            if self.prev_date is not None and self.prev_date.day != self.curr_date.day:
                yield self.output_format()
                self.post_daily_update()
                self.prev_day_val = self.prev_val

            self.prev_date = self.curr_date
            self.prev_val = self.curr_val
        
        self.hourly_update()
        yield self.output_format()


@dataclass
class Schema1(Schema):
    _min_val: float = None
    _max_val: float = None

    @property
    def day_of_week(self) -> str:
        return DAY_INDEX[self.prev_date.isoweekday() - 1]

    @property
    def change(self) -> float:
        # First day
        if self.prev_day_val is None:
            return None
        return self.prev_val - self.prev_day_val

    @property
    def direction(self) -> str:
        # First day
        if self.change is None:
            return None
        return "up" if self.change > 0 else "down" if self.change < 0 else "same"

    @property
    def high_since_start(self) -> float:
        # First day
        if self._max_val is None:
            self._max_val = self.curr_val
            return None
        
        if self.prev_val > self._max_val:
            self._max_val = self.prev_val
            return True
        
        return False

    @property
    def low_since_start(self) -> float:
        # First day
        if self._min_val is None:
            self._min_val = self.curr_val
            return None
        
        if self.prev_val < self._min_val:
            self._min_val = self.prev_val
            return True
        
        return False

    def output_format(self) -> Dict[str, Any]:
        return {
            "date": self.prev_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "price": f"{self.prev_val:0.2f}" if self.prev_val else None,
            "direction": self.direction,
            "change": f"{self.change:0.2f}" if self.change else None,
            "dayOfWeek": self.day_of_week,
            "highSinceStart": self.high_since_start,
            "lowSinceStart": self.low_since_start,
        }

@dataclass
class Schema2(Schema):
    vals: List[float] = field(default_factory=list)

    def daily_average(self):
        return statistics.mean(self.vals)
    
    def daily_variance(self):
        return statistics.variance(self.vals)

    def volatility_alert(self):
        for i in range(len(self.vals)):
            selected_vals = self.vals[:i]
            # std isn't valid for < 2 values, skip first value
            if len(selected_vals) < 2:
                continue
            
            new_mean = statistics.mean(selected_vals)
            if -1*statistics.stdev(selected_vals)*2 < selected_vals[-1] - new_mean < statistics.stdev(selected_vals)*2:
                return True

        return False

    def hourly_update(self):
        self.vals.append(self.prev_val)
        return super().hourly_update()

    def post_daily_update(self):
        self.vals = []
        return super().post_daily_update()

    def output_format(self) -> Dict[str, Any]:
        return {
            "date": self.prev_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "price": f"{self.prev_val:0.2f}" if self.prev_val else None,
            "dailyAverage": self.daily_average(),
            "dailyVariance": self.daily_variance(),
            "volatilityalert": self.volatility_alert()
        }

    # response = {
    #     "statusCode": 200,
    #     "body": json.dumps(output_vals)
    # }

if __name__ == "__main__":
    # print(download_parse_schema1(gen_data()))
    # print(list(Schema1().act(gen_data())))
    print(list(Schema2().act(gen_data())))