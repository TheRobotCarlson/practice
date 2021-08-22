# Price project

## Questions
- schema1 & 2 - "price"? price at eod / available window? - carries over
- schema1 - direction, difference between SOD and EOD or just EOD and EOD?
- schema1 - high + low since start - just EOD or anytime during the day? 

## Specification
```
schema1 = {
    "date": "{date}",
    "price": "{value}",
    "direction": "up/down/same",
    "change": "amount",
    "dayOfWeek": "name",
    "highSinceStart": "true/false",
    "lowSinceStart": "true/false",
}
```
- one entry per day at "00:00:00"
- results ordered by oldest date first
- "date" in format "2019-03-17T00:00:00"
- "price" in 2 decimal dollars
- "direction" is direction of price change since previous day in the list, first day can be na (up, down, same)
- change is price diff between current and previous day
- dayofweek is name of the day
- highSinceStart true/false if highest since start, na for first
- lowSinceStart true/false if highest since start, na for first

```
schema2 = {
    "date": "{date}",
    "price": "{value}",
    "dailyAverage": "{value}",
    "dailyVariance": "{value}",
    "volatilityAlert": "true/false",
}
```
- one entry per day
- result ordered by oldest day first
- "date" in format "2019-03-17T00:00:00"
- "price" in 2 decimal points
- "dailyAverage" average of all entries for that day
- "dailyVariance" variance of all entries for that day
- volatilityalert (true/false) if any price that day is outside 2 standard deviations



## Progress
- [ ] stream read json from endpoint vs tempfile download + iterate
- [ ] rest api endpoint
- [ ] schema1 calculation - bulk
- [ ] schema2 calculation - bulk
- [ ] unit tests
- [ ] integration - serverless
- [ ] github actions + deploy
- [ ] schema1 calculation - streaming
- [ ] schema2 calculation - streaming
- [ ] unit tests
- [ ] date range queries
- [ ] parse + cache date ranges
- [ ] unit tests + offline testing