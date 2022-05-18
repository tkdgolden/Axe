
import datetime
from operator import indexOf
import pandas as pd
from datetime import time

#pandas reads an excel file
print("Drag and drop the xlsx file here")
filePath = input().strip()
data = pd.read_excel(filePath, sheet_name='Schedule Summary')
df = pd.DataFrame(data, columns= ['Employee', 'Position', 'Start', 'End'])
df = df.reset_index()

print(df)

#positions that can be assigned sessions
position_set = {"ON CALL", "Axe Master 1", "Axe Master 2"}

#all the possible session start times
A = time(12, 0)
B = time(12, 30)
C = time(13, 0)
D = time(13, 15)
E = time(13, 30)
F = time(14, 0)
G = time(14, 30)
H = time(15, 0)
I = time(15, 30)
J = time(15, 45)
K = time(16, 0)
L = time(16, 30)
M = time(17, 0)
N = time(17, 15)
O = time(17, 30)
P = time(18, 0)
Q = time(18, 15)
R = time(18, 30)
S = time(19, 0)
T = time(19, 30)
U = time(19, 45)
V = time(20, 0)
W = time(20, 30)
X = time(20, 45)
Y = time(21, 0)
Z = time(22, 0)

#standard start times based on the weekday
weekday_start_times = [K, N, R, U, Y]
saturday_start_times = [A, D, G, J, M, Q, T, X, Z]
sunday_start_times = [A, D, G, J, M, Q]

#class object, holds each shift for each employee while info is being transferred from the wheniwork table into my own
class Shift:
    def __init__(self, name, start, end):
        self.name = name
        self.date = start.date()
        self.start = start.time()
        self.last = (end + datetime.timedelta(hours = -1)).time()
        self.end = end.time()
    def pft(self):
        print("Date: " + self.date.strftime("%m-%d"))
        print("Name: " + self.name)
        print("Start Time: " + self.start.strftime("%H:%M"))
        print("End Time: " + self.end.strftime("%H:%M"))

#array of all the shift objects (from wheniwork)
shift_set = []

#iterating through the wheniwork table to create shift objects and put them into the shift_set array
for index, row in df.iterrows():
    if(row['Position'] in position_set):
        shift_set.append(Shift(row['Employee'], row['Start'], row['End']))

#array of the days found in the wheniwork table
#TODO wont need this when I am using a df instead of my 3d array
days = []
for each in shift_set:
    if(each.date not in days):
        days.append(each.date)

#use the size of the above array to decide how big to build my 3d array
numdays = len(days)

#its the size of the largest (saturday has the most sessions)
arr = [[[] for n in range(len(saturday_start_times))] for r in range(numdays)]

#keeping track of what days of the week are what index
wdays = {0, 1, 2, 3, 4}
sat = 5
sun = 6

#look at each shift
for each in shift_set:
    #count the day, so that it is its own element in the 3d array
    dayindex = days.index(each.date)
    #find the day of the week of that day
    wday = each.date.weekday()
    if (wday in wdays):
        #iterate through all session times on that day
        for this in weekday_start_times:
            #if the current shift will cover the current session
            if (each.start <= this) & (this <= each.last):
                #put this employees name in the array
                if (each.name not in arr[dayindex][weekday_start_times.index(this)]):
                    arr[dayindex][weekday_start_times.index(this)].append(each.name)
    elif (wday == sat):
        for this in saturday_start_times:
            if (each.start <= this) & (this <= each.last):
                arr[dayindex][saturday_start_times.index(this)].append(each.name)
    elif (wday == sun):
        for this in sunday_start_times:
            if (each.start <= this) & (this <= each.last):
                arr[dayindex][sunday_start_times.index(this)].append(each.name)

for i, each in enumerate(arr):
    print (days[i])
    dotw = days[i].weekday()
    if (dotw in wdays):
        c = 0
        for each in weekday_start_times:
            print (each, len(arr[i][c]))
            print ("               ", arr[i][c])
            c += 1
        print ("")
    if (dotw == sat):
        c = 0
        for each in saturday_start_times:
            print (each, len(arr[i][c]))
            print ("               ", arr[i][c])
            c += 1
        print ("")
    if (dotw == sun):
        c = 0
        for each in sunday_start_times:
            print (each, len(arr[i][c]))
            print ("               ", arr[i][c])
            c +=1
        print ("")
    print ("")

