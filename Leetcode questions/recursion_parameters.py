################# RECURSION WITH PARAMETERS #######################################

def func(x,N):
    if N==0:
        return
    print(x)
    func(x,N-1)

func(20,5)

'''
def func(x,N):
    if N==0:
        return
    print(x)
    Reursion TREE
    func(20,5) --> func(20,4) ---> func(20,3) --> func(20,2) ---> func(20,1) --> func(20,0)
    and reverse of the functions 
    '''