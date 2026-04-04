number = 10
l = []
for i in range(number):
    print(i+1)
    if (number %(i+1)) == 0:
        l.append(i)
        i+=1
    else:
        continue
print("These are the divisors of number: " , number )
for x in l:
    print("Divisor : ", x+1)




######## ANother approach to check till Square root



number = 10
divisors = []

for i in range(1, int(number**0.5) + 1):
    if number % i == 0:
        divisors.append(i)

        if i != number // i:  # avoid duplicate for perfect squares
            divisors.append(number // i)

divisors.sort()

print("Divisors Second Approach:", divisors)



######################################################################
########Brute Force - O(N), Space complexity O(k), k would be the total number of factors

num = 20
divisors = []
for i in range(1, num + 1): ## O(N)
    if num % i == 0:
        divisors.append(i) ## O(1)
    else:
        continue
print("These are the divisors of number: " , divisors, "There are divisors", len(divisors) )
# for x in divisors:



############ OPTIMIZED SOLUTION ###############################

print ("###########################OPTMIZED SOLUTION ###########################   Time Complexity is O(N/2), O(N)")


number_2 = 30

result_2 = []

for i in range(1, number_2 // 2): ### TC is O(N/2)
    if number_2 % i == 0:
        result_2.append(i)


result_2.append(number_2) ### TC O(1)

print( "Divisors list for number",number_2, "divisors are : ",  result_2)


########### MORE Optimized Solution ####################### SQUARE ROOT APPROACH ##########

# from math import sqrt


number_3 = 99
result_3 = [] ###### SC space complxity O(k)

for i in range(1, int(number_3**0.5) + 1):  # O(sqrt(n))

    if number_3 % i == 0:
        result_3.append(i)

        if (number_3 // i) != i:   # avoid duplicate for perfect squares
            result_3.append(number_3 // i)

# sort the list
result_3.sort()  # O(n log n)

print("Divisors list for number", number_3, "divisors are:", result_3)






###########################################################################

number_4 = 120

result_4 = []

for i in range(1, int(number_4**0.5)+1 ):
    if number_4 % i == 0:
        result_4.append(i)

        if number_4 // i != i:
            result_4.append(int(number_4 // i))

result_4.sort()
print("Divisors list for number", number_4, "divisors are:", result_4)








#################

small = []
large = []

n = 120

for i in range(1, int(n**0.5) + 1):
    if n % i == 0:
        small.append(i)
        if i != n // i:
            large.append(n // i)

result = small + large[::-1]
print(result)