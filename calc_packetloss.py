import math

#在丢包率为P的情况下，n个包中至少到达m个的概率
def f0(n,m,p):
    sum=0
    for k in range(m,n+1):
        sum+=C(k,n)*math.pow(1-p,k)*math.pow(p,n-k)
    return sum

def C(n,m):
    return math.factorial(m)/(math.factorial(n)*math.factorial(m-n))

def f(x,y,p):
    return 1-f0(x+y,x,p)


if __name__ == '__main__':
    packet_loss=0.3
    FEC="15:15"
    x,y=FEC.split(":")
    print("%.20f%%"%(f(int(x),int(y),packet_loss)*100))