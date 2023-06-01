import matplotlib.pyplot as plt #导入库

with open("comment.txt",encoding="utf-8") as f:#读入相应文件
    comments = f.readlines()
negcount=0#消极评论计数
neucount=0#中性评论计数
poscount=0#积极评论计数
for comment in comments:
    label=comment[0:2]#按照文本格式划分标签
    #print(label)
    if (str(-1) in label):#消极
        negcount+=1
    elif (str(0) in label):#中性
        neucount+=1
    else:#积极
        poscount+=1
x=['消极','中性','积极']#x轴数据
y=[negcount,neucount,poscount]#y
plt.rcParams['font.sans-serif']=['SimHei']#解决中文乱码问题
plt.xlabel('情感标签')
plt.ylabel('数据行数')
plt.xlim(-1,3)#设置x轴刻度范围
plt.ylim(0,650)#设置y轴刻度范围
plt.bar(x,y)#绘制柱形图
for a,b in zip(x,y):
    plt.text(a,b,'%d'%b,ha = 'left',fontsize=9)
plt.show()#展示




