n = 153
num = n
total = 0
number_of_digits = len(str(num))



while num > 0:
    ld = num%10
    total += ld**number_of_digits
    print(total)
    num = num // 10

if total == n:
    print("True")
else:
    print("False")















l = 1634

x = l

total_now = 0
number_of_digits = len(str(x))

while x != 0:  ######## Time Complexity TC would be O(log10 N), Space complexity is O(1)
    last_digit = x % 10
    total_now += last_digit ** number_of_digits ### O(1)
    print(total_now)
    x = x // 10

if total_now == l:
    print("True")
else:
    print("False")



