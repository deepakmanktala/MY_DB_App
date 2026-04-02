# l = [1,2,3,1]

# l = [1,1,1,3,3,4,3,2,4,2]

l = [1,2,3,4]

i = 1

for i in range(len(l)):
    if l[i-1] == l[i]:
        print ("True")
        i = i + 1
        break
    else:
        print ("False")
        break

# print ("False")

