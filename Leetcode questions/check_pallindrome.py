from fontTools.misc.cython import returns

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

def check_pallindrome(num_3):
    # num_3 = 1234321
    original = num_3

    result_3 = 0
    print("Second iteration starts here")
    while num_3 > 0:
        last_digit = num_3 % 10
        result_3 =  (result_3 *10) + last_digit
        num_3 = num_3 // 10

    return original == result_3
#
# if result_3 == num_3:
#         print("It is a pallindrome")
#     else:
#         print("Not a pallindrome")

print(check_pallindrome(121))