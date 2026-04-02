from fontTools.misc.cython import returns

n = 676832999999999

num = int(n)
ct = 0
while num > 0:
    num //= 10
    ct += 1
    # return ct
# return ct
print(ct)


########Logrithimic approach###################
num = 12213111221
from math import *

def count_digits(num):
    print(int(log10(num)) + 1)

    return int((log10(num)) + 1)
    # print(int(log10(num)) + 1)
    # if num == 0:
    #     return 0
    # elif num % 10 == 0:
    #     return 1
    # else:
    #     return count_digits(num // 10) + count_digits(num % 10)

count_digits(num)




################THIRD APPROACH - USING STRING########################

num = 111111122222222222222222222223333333333333

def count_digits_using_str(num):

    print (len(str(abs(num))))

    return len(str(abs(num)))

count_digits_using_str(num)