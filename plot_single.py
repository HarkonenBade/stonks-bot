import json
import sys
from cogs.stonks import plot_single


with open(sys.argv[1]) as f:
    data = json.load(f)

with open(sys.argv[2], 'wb') as f:
    plot_single(data, f)

