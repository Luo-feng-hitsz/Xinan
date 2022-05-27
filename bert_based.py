#! -*- coding:utf-8 -*-
# 文本分类多gpu版
# 数据集：IFLYTEK' 长文本分类 (https://github.com/CLUEbenchmark/CLUE)

import os

os.environ['TF_KERAS'] = '1'  # 必须使用tf.keras

import csv
import numpy as np
import tensorflow as tf
from bert4keras.backend import keras, K
from bert4keras.tokenizers import Tokenizer
from bert4keras.models import build_transformer_model
from bert4keras.optimizers import Adam
from bert4keras.snippets import sequence_padding, DataGenerator, to_array
from keras.layers import Lambda, Dense, Dropout
from tqdm import tqdm

num_classes = 10
maxlen = 128
batch_size = 8

# BERT base
config_path = '/home/wufisher/Xinan/data/bert/uncased_L-12_H-768_A-12/bert_config.json'
checkpoint_path = '/home/wufisher/Xinan/data/bert/uncased_L-12_H-768_A-12/bert_model.ckpt'
dict_path = '/home/wufisher/Xinan/data/bert/uncased_L-12_H-768_A-12/vocab.txt'

def load_data(filename):  # 要训练就放出来
    """加载数据
    单条格式：(文本, 标签id)
    """
    D = []
    label_id = {
        "First Party Collection/Use":0, "Third Party Sharing/Collection":1, 
        "Other":2, "User Choice/Control":3,
        "Data Security":4,"International and Specific Audiences":5,
        "User Access, Edit and Deletion":6,"Policy Change":7,
        "Data Retention":8,"Do Not Track":9
    }
    with open(filename) as f:
        f_csv = csv.reader(f)
        header = next(f_csv)
        for row in f_csv:
            text = row[2]
            label = label_id[row[3]]
            D.append((text, int(label)))
    return D


# 加载数据集  # 要训练就放出来
train_data = load_data(
    '/home/wufisher/Xinan/data/our_data/train.csv'
)
valid_data = load_data(
    '/home/wufisher/Xinan/data/our_data/test.csv'
)

# 建立分词器
tokenizer = Tokenizer(dict_path, do_lower_case=True)


class data_generator(DataGenerator):    # 要训练就放出来
    """数据生成器
    """
    def __iter__(self, random=False):
        for is_end, (text, label) in self.sample(random):
            token_ids, segment_ids = tokenizer.encode(text, maxlen=maxlen)
            yield [token_ids, segment_ids], [[label]]  # 返回一条样本


# 转换数据集   # 要训练就放出来
train_generator = data_generator(train_data, batch_size)
valid_generator = data_generator(valid_data, batch_size)

# 加载预训练模型    
bert = build_transformer_model(
    config_path=config_path,
    checkpoint_path=None,
    return_keras_model=False,
)

output = Lambda(lambda x: x[:, 0])(bert.model.output)
output = Dropout(
    rate = 0.1
)(output)
output = Dense(
    units=20
)(output)
output = Dense(
    units=10
)(output)
output = Dense(
    units=num_classes,
    activation='softmax',
    kernel_initializer=bert.initializer,
    name='Probas'
)(output)

model = keras.models.Model(bert.model.input, output)
model.compile(
    loss='sparse_categorical_crossentropy',
    optimizer=Adam(1e-5),
    metrics=['sparse_categorical_accuracy'],
)
# model.summary()   # 要训练就放出来
bert.load_weights_from_checkpoint(checkpoint_path)  # 必须最后才加载预训练权重


class Evaluator(keras.callbacks.Callback):
    """评估与保存
    """
    def __init__(self):
        self.best_val_acc = 0.

    def on_epoch_end(self, epoch, logs=None):
        val_acc = logs['sparse_categorical_accuracy']
        if val_acc > self.best_val_acc:
            self.best_val_acc = val_acc
            model.save_weights('test_model.weights')
            # model.save_weights('best_model.weights')
        print(
            u'val_acc: %.5f, best_val_acc: %.5f\n' %
            (val_acc, self.best_val_acc)
        )


def predict_to_file(in_file, out_file):
    """输出预测结果到文件
    csv -> csv
    """
    D = []
    label_id = {
        "First Party Collection/Use":0, "Third Party Sharing/Collection":1, 
        "Other":2, "User Choice/Control":3,
        "Data Security":4,"International and Specific Audiences":5,
        "User Access, Edit and Deletion":6,"Policy Change":7,
        "Data Retention":8,"Do Not Track":9
    }
    fw = open(out_file, 'w')
    with open(in_file) as fr:
        fr_csv = csv.reader(fr)
        header = next(fr_csv)
        for row in fr_csv:
            id = row[1]
            text = row[2]
            token_ids, segment_ids = tokenizer.encode(text, maxlen=maxlen)
            token_ids, segment_ids = to_array([token_ids], [segment_ids])
            label = model.predict([token_ids, segment_ids])[0].argmax()
            label_str = list (label_id.keys()) [list (label_id.values()).index (label)]
            D.append([id,text,label_str])
    writer = csv.writer(fw)
    #先写入columns_name
    writer.writerow(["id","text","type"])
            #写入多行用writerows
    writer.writerows(D)
    fw.close()
    return D


if __name__ == '__main__':

    evaluator = Evaluator()

    train_dataset = train_generator.to_dataset(
        types=[('float32', 'float32'), ('float32',)],
        shapes=[([None], [None]), ([1],)],  # 配合后面的padded_batch=True，实现自动padding
        names=[('Input-Token', 'Input-Segment'), ('Probas',)],
        padded_batch=True
    )  # 数据要转为tf.data.Dataset格式，names跟输入层/输出层的名字对应

    valid_dataset = valid_generator.to_dataset(
        types=[('float32', 'float32'), ('float32',)],
        shapes=[([None], [None]), ([1],)],  # 配合后面的padded_batch=True，实现自动padding
        names=[('Input-Token', 'Input-Segment'), ('Probas',)],
        padded_batch=True
    )  # 数据要转为tf.data.Dataset格式，names跟输入层/输出层的名字对应

    model.fit(
        train_dataset,
        steps_per_epoch=len(train_generator),
        epochs=1,
        validation_data=valid_dataset,
        validation_steps=len(valid_generator),
        callbacks=[evaluator]
    )
    # tf.saved_model.save(model, "./test_model_path")
    # # Convert the model
    # converter = tf.lite.TFLiteConverter.from_keras_model(model) # path to the SavedModel directory
    # converter.optimizations = [tf.lite.Optimize.DEFAULT]
    # tflite_model = converter.convert()

    # # Save the model.
    # with open('model.tflite', 'wb') as f:
    #     f.write(tflite_model)
else:

    model.load_weights('/home/wufisher/Xinan/data/best_model.weights')
    # predict_to_file('/home/wufisher/Xinan/data/our_data/sample.csv', 'predict_result.csv')
