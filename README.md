# Price project

## Design Decisions
- Doesn't need to be that optimized since it's such a small amount of data. Readability + maintainability > speed
- Data schema could need to be changed in the future. We should make it easy to change both the output format and to add
new computed fields
- Serverless framework is quick to setup, run, and deploy
- Automated tests would be a good next step


## To run
```
npm install -g serverless
npm i
serverless offline
```

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
