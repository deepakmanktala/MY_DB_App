# mutability
# List, Dictionary, Set
#
#
# Immutable
#
# Tuple, String, Float, Int


l = [10,20,30]

# indexing

a, b = l[1], l[0]

print(a,b)



# slicing

j = [1,2,3]

print(j[:2]) # start, stop, step

print(j[2:])



## List COmprehensions

# squaring numbers in a range

l = [i**2 for i in range (5)]
print(l)

k = [i**2 for i in range (5) if i%2 == 0]
print(k)

numbers = [1,2,3,4,5,6,7]

# break statement
for num in numbers:
    if num % 2 == 0:
        print(num)
        print("Even number is found ! exiting the loop")
        break
    print(num)

# pass is empty block, generally used in classes and fucntions definitions

def empty_func():
    # This will be implemented later
    print("Empty func")

print("empty funct")



# Scope local and global

x = 300

def myfunc():
    x = 200
    print(x)
    print("this is local functioon x")

print(x)

myfunc()


# -ve indexes which allows to access elements from the end of a sequence list or string

m = [1,2,3,4,5,6,7]

print(m[-1])
print(m[:-2])

# Shallow and Deep copy
a = [1,2,3]
a = b

print(b)


