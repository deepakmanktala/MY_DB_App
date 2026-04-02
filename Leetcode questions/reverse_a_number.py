n = 43232221111111199999998888888888

num = n
reverse = 0

while num > 0:
    last_digit = num % 10          # extract last digit
    reverse = reverse * 10 + last_digit # build reverse number
    print(last_digit)
    num //= 10                     # remove last digit

print(reverse)