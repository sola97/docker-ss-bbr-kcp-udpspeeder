import math

#在丢包率为P的情况下，n个包中至少到达m个的概率
def f0(n,m,p):
    sum=0
    for k in range(m,n+1):
        sum+=C(k,n)*math.pow(1-p,k)*math.pow(p,n-k)
    return sum

def C(n,m):
    return math.factorial(m)/(math.factorial(n)*math.factorial(m-n))

def calc(x, y, p):
    return 1-f0(x+y,x,p)

def predict_loss(fec,packet_loss):
    x,y=fec.split(":")
    pred= calc(int(x), int(y), packet_loss / 100.0) * 100
    print(f"{x}:{y} 可以将 {packet_loss}% 的丢包率降为 "+"%.2f%%"%pred)

def calc_fec_param(target_loss,origin_loss,num=20):
    str="-f"
    origin_loss/=100.0
    target_loss/=100.0
    num+=1
    map=dict()
    for x in range(1,num):
        for y in range(1,num):
            if calc(x, y, origin_loss) < target_loss:
                map[y]=x
                break
    return str+",".join(f"{map[k]}:{k}" for k in sorted(map.keys()))

if __name__ == '__main__':
    predict_loss("20:19",30)
    print(calc_fec_param(0.5,30))


