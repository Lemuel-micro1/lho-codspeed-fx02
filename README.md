# voyagekit

Process AIS-style vessel position logs: parse position fixes, compute the distance each vessel travelled, and flag implausible speeds between fixes.

```
python -m voyagekit summary --synthetic 20000
python -m voyagekit alerts --file positions.log
```

Run the tests with `pytest`.