import jieba
import wordcloud
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
# 读取文本
with open("poscomment.txt",encoding="utf-8") as f:#读入相应txt文件
    s = f.read()
print(s)
content=s[4:]
ls = jieba.lcut(content) # 生成分词列表
text = ' '.join(ls) # 连接成字符串

img = Image.open("mask.png") # 打开遮罩图片
mask = np.array(img) #将图片转换为数组

stopwords = ["的","是","了"] # 去掉不需要显示的词

wc = wordcloud.WordCloud(font_path="msyh.ttc",
                         mask=mask,
                         width = 1000,
                         height = 700,
                         background_color='white',
                         max_words=100,stopwords=s)
# msyh.ttc电脑本地字体，写可以写成绝对路径
wc.generate(text) # 加载词云文本

plt.imshow(wc, interpolation='bilinear')# 用plt显示图片
plt.axis("off")  # 不显示坐标轴
plt.show() # 显示图片

wc.to_file("积极数据集词云图.png") # 保存词云文件