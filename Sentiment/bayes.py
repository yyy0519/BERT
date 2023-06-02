import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn import metrics
import joblib
import numpy as np
from sklearn.metrics import confusion_matrix, recall_score, classification_report
import matplotlib.pyplot as plt
import itertools

def read_label_txt(data_dir):
    contents = []
    labels = []
    with open(data_dir,encoding='utf-8',errors = 'ignore') as f:
        dir_labels = [line.strip() for line in f.readlines()]
        # 一定要用strip,因为原txt文件每行后面会带‘\n‘字符；

    for line in dir_labels:
        label,content=line.split('separate',1)
        contents.append(content)
        labels.append(label)

    return contents, labels

def plot_confusion_matrix(cm, classes,normalize=False,title='Confusion matrix',cmap=plt.cm.Blues):#定义绘制混淆矩阵函数
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.
    """
    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        print("Normalized confusion matrix")
    else:
        print('Confusion matrix, without normalization')
    print(cm)
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=45)
    plt.yticks(tick_marks, classes)
    fmt = '.2f' if normalize else 'd'
    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(j, i, format(cm[i, j], fmt),
                 horizontalalignment="center",
                 color="white" if cm[i, j] > thresh else "black")
    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label')



data_dir = 'data/comment.txt'
x, y = read_label_txt(data_dir)

print(x)
print(y)

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=1) #划分测试集和训练集 8:2
# 词袋模型
bow_vectorizer = CountVectorizer(max_df=0.80, min_df=2)
#贝叶斯模型
Nb = MultinomialNB()
pipe = make_pipeline(bow_vectorizer, Nb)
pipe.fit(x_train, y_train)

y_pred = pipe.predict(x_test) #预测


pos_count = 0
neu_count = 0
neg_count = 0
for i, j in enumerate(y_pred):
    if j == '0':
        neu_count += 1
    elif j == '1':
        pos_count += 1
    else:
        neg_count += 1
    print('label:{}'.format(j))

labels = ['Positive', 'Neutral', 'Negative']
values = [pos_count, neu_count, neg_count]
colors = ['#2ecc71', '#f1c40f', '#e74c3c']
explode = (0.1, 0, 0)

plt.pie(values, explode=explode, labels=labels, colors=colors,autopct='%1.1f%%', startangle=90)
total_count = pos_count + neu_count + neg_count
center_circle = plt.Circle((0, 0), 0.7, color='black', fc='white', linewidth=1.25)
plt.gcf().gca().add_artist(center_circle)
plt.title('Comment Sentiment Distribution')
plt.text(0, 0, 'Total: {}'.format(total_count), ha='center', va='center')

print(y_pred) #保存预测结果到dataframe中
cnf_matrix = confusion_matrix(y_test, y_pred)  # 计算混淆矩阵
class_names = [-1, 0, 1]
plt.figure()
plot_confusion_matrix(cnf_matrix, classes=class_names, title='Confusion matrix')  # 绘制混淆矩阵
np.set_printoptions(precision=2)
print('Accary:', (cnf_matrix[1, 1] + cnf_matrix[0, 0]) / ( cnf_matrix[1, 1] + cnf_matrix[0, 1] + cnf_matrix[0, 0] + cnf_matrix[1, 0]))
print('Recall:', cnf_matrix[1, 1] / (cnf_matrix[1, 1] + cnf_matrix[1, 0]))
print('Precision:', cnf_matrix[1, 1] / (cnf_matrix[1, 1] + cnf_matrix[0, 1]))
print('Specificity:', cnf_matrix[0, 0] / (cnf_matrix[0, 1] + cnf_matrix[0, 0]))
plt.show()

print(metrics.classification_report(y_test, y_pred)) #评估

joblib.dump(pipe, './Bayes.pkl') #保存模型

