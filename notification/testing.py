from re import findall
from datetime import datetime as dt, timedelta as td

strhd = '1 day, 16 hours ago'
strs = '22 seconds ago'


if 'day' and 'hours' in strhd:
	nums = findall(r'\d+', strhd)
	day = int(nums[0])
	hrs = int(nums[1])
	print(dt.now() - td(days=day, hours=hrs))
	
if 'seconds' in strs:
	nums = findall(r'\d+', strhd)
	scd = int(nums[0])
	print(dt.now() - td(seconds=scd))
