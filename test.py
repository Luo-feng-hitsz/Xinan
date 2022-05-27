#! -*- coding:utf-8 -*-
import os
from sys import flags
from unittest import result
from nltk.parse import CoreNLPParser
from nltk.parse.corenlp import CoreNLPDependencyParser
import nltk.stem.porter as pt
import re

string = "Third party might collect and retain your name and contact address, and save your user id if the UPLOAD is clicked."

# os.system('/home/wufisher/Xinan/open_standford_service.sh')

dep_parser = CoreNLPDependencyParser(url='http://localhost:9000')
parses, = dep_parser.raw_parse(string)
# print(parses.to_conll(4))
A = parses.to_conll(4).split('\n')
A.pop()
words = []
for a in A:
    words.append(a.split('\t'))
# print(words)

actions = []
def find_root(words):
    for word in words:
        if word[3] == 'ROOT':
            return (words.index(word) + 1)
root_num = find_root(words)
for word in words:
    if word[3] == 'ROOT':
        actions.append(word[0])
    if word[3] == 'conj' and int(word[2]) == root_num:
        actions.append(word[0])
print(actions)

data_main = []
for word in words:
    if (word[3] == 'nsubjpass' or word[3] == 'dobj') and words[int(word[2]) - 1][0] in actions:
        data_main.append(word[0])
print(data_main)
for word in words:
    if word[3] == 'conj' and words[int(word[2]) - 1][0] in data_main:
        data_main.append(word[0])
print(data_main)
data_decorate = []
flags = []
for i in range(len(data_main)):
    flags.append(0)
for word in words:
    if (word[3] == 'amod' or word[3] == 'compound' or word[3] == 'advmod') and words[int(word[2]) - 1][0] in data_main:
        data_decorate.append(word[0] + ' ' + words[int(word[2]) - 1][0])
        flags[data_main.index(words[int(word[2]) - 1][0])] = 1
print(data_decorate)
for i in range(len(data_main)):
    if flags[i] == 0:
        data_decorate.append(data_main[i])
print(data_decorate)
governor_main = []
for word in words:
    if word[3] == 'nsubj' and int(word[2]) == root_num:
        governor_main.append(word[0])
for word in words:
    if word[3] == 'conj' and words[int(word[2]) - 1][0] in governor_main:
        governor_main.append(word[0])
print(governor_main)
governor_decorate = []
flags = []
for i in range(len(governor_main)):
    flags.append(0)
for word in words:
    if (word[3] == 'amod' or word[3] == 'compound' or word[3] == 'advmod') and words[int(word[2]) - 1][0] in governor_main:
        governor_decorate.append(word[0] + ' ' + words[int(word[2]) - 1][0])
        flags[governor_main.index(words[int(word[2]) - 1][0])] = 1
for i in range(len(governor_main)):
    if flags[i] == 0:
        governor_decorate.append(governor_main[i])

flag = 0
condition = ""
for word in words:
    if flag == 1 :
        condition += word[0] + ' '
        continue
    if word[3] == 'mark':
        flag = 1
        condition += word[0] + ' '

action_data_pair = []
for a in actions:
    for d in data_decorate:
        action_data_pair.append([a,d])
print("===============================================================")
print(["action:",action_data_pair])
print(["governor:",governor_decorate])
print(["condition:",condition])

a = [1,1,1,2,3,5,6,8,'str','str']
# 去重复
def remove_dup(list_dup):
    result = []
    for i in list_dup:
        if i not in result:
            result.append(i)
    return result
print(remove_dup(a))

for i in range(2,5):
    print(i)

# flag = 0
# sum_str = ""
# for word in B:
#     if flag == 1 :
#         sum_str += word[0] + ' '
#         continue
#     if word[3] == 'mark':
#         flag = 1
#         sum_str += word[0] + ' '
# print(sum_str)

                

            

# pos_tagger = CoreNLPParser(url='http://localhost:9000', tagtype='pos')
# temp = list(pos_tagger.tag('  Third party might collect and retain your name and contact address, and save your user id if the UPLOAD is clicked. '.split()))
# for line in temp:
#     print(line)

# parser = CoreNLPParser(url='http://localhost:9000')
# temp = list(parser.parse('  Third party might collect and retain your name and contact address, and save your user id if the UPLOAD is clicked. '.split()))
# print(temp)

# verbs = ['access', 'assign', 'collect', 'create', 'enter', 'gather', 'import', 'obtain', 
# 'observe', 'receive', 'request', 'understand', 'pick', 'pull', 'chase', 'gain', 'catch', 
# 'win', 'ask','use', 'process', 'monitor', 'see', 'utilize', 'utilise', 'employ', 'take', 
# 'upload', 'cache','delete','erase','keep', 'remove', 'retain', 'store', 'accumulate', 
# 'hold', 'encrypt', 'encipher', 'cipher', 'save', 'maintain','reserve', 'communicate', 
# 'disclose', 'reveal', 'receive', 'sell', 'send', 'view', 'share', 'transfer', 'provide', 'offer', 'render','expose', 'uncover', 'transport', 'transmit'
# ]

# words = ['table', 'probably', 'wolves', 'playing',
# 'is', 'dog', 'the', 'beaches', 'grounded',
# 'dreamt', 'envision']
# words.pop(1)
# print(words)
# pt_stemmer = pt.PorterStemmer()  # 波特词⼲提取器
# for word in words:
#     pt_stem = pt_stemmer.stem(word)
#     print([word,pt_stem])



