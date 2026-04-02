n = 12345667

num = n
# last_digit = 0
result = 0
while num > 0:
    ld = num %10
    # last_digit = last_digit * 10 + num % 10
    result = result * 10 + ld
    num //= 10

if result == n:
    print("It is a pallindrome")
else:
    print("Not a pallindrome")


#########Time Complexity  is BIG O (log10(N))
######## Space Complexity - only 2 variable which is constant space O(1)
