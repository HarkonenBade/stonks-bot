import json
import sys
from cogs.stonks import plot_multi

data = {}

for i in range(2, len(sys.argv)):
    with open(sys.argv[i]) as f:
        data[sys.argv[i]] = json.load(f)

with open(sys.argv[1], 'wb') as f:
    plot_multi(data, f)

