## sorted - retruns a new sorted list, Sorted is applicable to all the iterables though

l = [5,6,7,8,9,1,2,3,4]
j = sorted(l)

k = sorted(l, key= None , reverse=True)

print(j)

print(k)


## sort is only for lists, sort gives the same list as modified list rather than a new list


m = [10,122,2323,323,2321,2,3,4,5,6,7]

n = m.sort()

print(m)
print(n)



#### Generators return an iterators
## generators use yield instead of return
## generators remember their state between each yield


########GENERTAORS ##############

def countdown(num):
    while num > 0:
        yield num
        num -= 1

for count in countdown(6):
    print(count)