import re
import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
from pytorch_pretrained import BertModel, BertTokenizer
import itertools
import pandas as pd
from sklearn.metrics import confusion_matrix, recall_score, classification_report


class Config(object):

    """配置参数"""
    def __init__(self):
        self.model_name = 'bert'
        self.class_list = ['中性','积极', '消极']          # 类别名单
        self.save_path = './Sentiment/saved_dict/bert.ckpt'        # 模型训练结果
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')   # 设备

        self.require_improvement = 1000                                 # 若超过1000batch效果还没提升，则提前结束训练
        self.num_classes = len(self.class_list)                         # 类别数
        self.num_epochs = 3                                             # epoch数
        self.batch_size = 128                                           # mini-batch大小
        self.pad_size = 32                                              # 每句话处理成的长度(短填长切)
        self.learning_rate = 5e-5                                       # 学习率
        self.bert_path = './bert_pretrain'
        self.tokenizer = BertTokenizer.from_pretrained(self.bert_path)
        self.hidden_size = 768


class Model(nn.Module):

    def __init__(self, config):
        super(Model, self).__init__()
        self.bert = BertModel.from_pretrained(config.bert_path)
        for param in self.bert.parameters():
            param.requires_grad = True
        self.fc = nn.Linear(config.hidden_size, config.num_classes)

    def forward(self, x):
        context = x[0]  # 输入的句子
        mask = x[2]  # 对padding部分进行mask，和句子一个size，padding部分用0表示，如：[1, 1, 1, 1, 0, 0]
        _, pooled = self.bert(context, attention_mask=mask, output_all_encoded_layers=False)
        out = self.fc(pooled)
        return out


PAD, CLS = '[PAD]', '[CLS]'  # padding符号, bert中综合信息符号

def clean(text):
    # text = re.sub(r"(回复)?(//)?\s*@\S*?\s*(:| |$)", " ", text)  # 去除正文中的@和回复/转发中的用户名
    # text = re.sub(r"\[\S+\]", "", text)  # 去除表情符号
    URL_REGEX = re.compile(
        r'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))',
        re.IGNORECASE)
    text = re.sub(URL_REGEX, "", text)  # 去除网址
    text = re.sub(r"\s+", " ", text)  # 合并正文中过多的空格
    return text.strip()

def load_dataset(data, config):
    pad_size = config.pad_size
    contents = []
    for line in data:
        lin = clean(line)
        token = config.tokenizer.tokenize(lin)      # 分词
        token = [CLS] + token                           # 句首加入CLS
        seq_len = len(token)
        mask = []
        token_ids = config.tokenizer.convert_tokens_to_ids(token)

        if pad_size:
            if len(token) < pad_size:
                mask = [1] * len(token_ids) + [0] * (pad_size - len(token))
                token_ids += ([0] * (pad_size - len(token)))
            else:
                mask = [1] * pad_size
                token_ids = token_ids[:pad_size]
                seq_len = pad_size
        contents.append((token_ids, int(0), seq_len, mask))
    return contents

class DatasetIterater(object):
    def __init__(self, batches, batch_size, device):
        self.batch_size = batch_size
        self.batches = batches     # data
        self.n_batches = len(batches) // batch_size
        self.residue = False  # 记录batch数量是否为整数
        if len(batches) % self.n_batches != 0:
            self.residue = True
        self.index = 0
        self.device = device

    def _to_tensor(self, datas):
        x = torch.LongTensor([_[0] for _ in datas]).to(self.device)
        y = torch.LongTensor([_[1] for _ in datas]).to(self.device)

        # pad前的长度(超过pad_size的设为pad_size)
        seq_len = torch.LongTensor([_[2] for _ in datas]).to(self.device)
        mask = torch.LongTensor([_[3] for _ in datas]).to(self.device)
        return (x, seq_len, mask), y

    def __next__(self):     # 返回下一个迭代器对象，必须控制结束条件
        if self.residue and self.index == self.n_batches:
            batches = self.batches[self.index * self.batch_size: len(self.batches)]
            self.index += 1
            batches = self._to_tensor(batches)
            return batches

        elif self.index >= self.n_batches:
            self.index = 0
            raise StopIteration
        else:
            batches = self.batches[self.index * self.batch_size: (self.index + 1) * self.batch_size]
            self.index += 1
            batches = self._to_tensor(batches)
            return batches

    def __iter__(self):     # 返回一个特殊的迭代器对象，这个迭代器对象实现了 __next__() 方法并通过 StopIteration 异常标识迭代的完成。
        return self

    def __len__(self):
        if self.residue:
            return self.n_batches + 1
        else:
            return self.n_batches


def build_iterator(dataset, config):
    iter = DatasetIterater(dataset, 1, config.device)
    return iter


def match_label(pred, config):
    label_list = config.class_list
    return label_list[pred]


def final_predict(config, model, data_iter):
    map_location = lambda storage, loc: storage
    model.load_state_dict(torch.load(config.save_path, map_location=map_location))
    model.eval()
    predict_all = np.array([])
    with torch.no_grad():
        for texts, _ in data_iter:
            outputs = model(texts)
            pred = torch.max(outputs.data, 1)[1].cpu().numpy()
            pred_label = [match_label(i, config) for i in pred]
            predict_all = np.append(predict_all, pred_label)

    return predict_all

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



def main(text):
    config = Config()
    model = Model(config).to(config.device)
    test_data = load_dataset(text, config)
    test_iter = build_iterator(test_data, config)
    result = final_predict(config, model, test_iter)
    #for i, j in enumerate(result):
        #print('text:{}'.format(text[i]))
        #print('label:{}'.format(j))
    pos_count = 0
    neu_count = 0
    neg_count = 0
    for i, j in enumerate(result):
        if j == '中性':
            neu_count += 1
        elif j == '积极':
            pos_count += 1
        else:
            neg_count += 1
        print('text:{}'.format(text[i]))
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

    flag=[]
    with open("testdoc.txt", encoding="utf-8") as f:
        comments = f.readlines()

    for comment in comments:
        label = comment[0:2]
        flag.append(label)


    cnf_matrix = confusion_matrix(flag, result)  # 计算混淆矩阵
    class_names = [-1, 0, 1]
    plt.figure()
    plot_confusion_matrix(cnf_matrix, classes=class_names, title='Confusion matrix')  # 绘制混淆矩阵
    np.set_printoptions(precision=2)
    print('Accary:', (cnf_matrix[1, 1] + cnf_matrix[0, 0]) / (
                cnf_matrix[1, 1] + cnf_matrix[0, 1] + cnf_matrix[0, 0] + cnf_matrix[1, 0]))
    print('Recall:', cnf_matrix[1, 1] / (cnf_matrix[1, 1] + cnf_matrix[1, 0]))
    print('Precision:', cnf_matrix[1, 1] / (cnf_matrix[1, 1] + cnf_matrix[0, 1]))
    print('Specificity:', cnf_matrix[0, 0] / (cnf_matrix[0, 1] + cnf_matrix[0, 0]))
    plt.show()

if __name__ == '__main__':
    test=[]
    with open("testdoc.txt", encoding="utf-8") as f:
        comments = f.readlines()

    for comment in comments:
        content = comment[3:]
        test.append(content)



    main(test)
