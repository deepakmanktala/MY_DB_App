########################## 998 is the limit for recursion
##################### Base Case for Factorial N ==0 or N== 1then return 1

########## TIME COMPLEXITY is O(N) ##############
########## SPACE COMPLEXITY iS O(N) , WHICH IS FOR THE STACK SPACE ####################

def fact(N):
    if N == 0 or N == 1:
        return 1
    else:
        return N*fact(N-1)

fact(10)
print(fact(5))
print(fact(998)) ######## 998 is the limit for recursion