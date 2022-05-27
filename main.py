#! -*- coding:utf-8 -*-
from base64 import encode
from email.policy import Policy
import os
from unittest import result
import bert_based
from nltk.parse import CoreNLPParser
from nltk.parse.corenlp import CoreNLPDependencyParser
import nltk.stem.porter as pt
import re
import csv
import numpy as np
import pandas as pd

# os.system('/home/wufisher/Xinan/open_standford_service.sh')
parser = CoreNLPParser(url='http://localhost:9000')
pos_tagger = CoreNLPParser(url='http://localhost:9000', tagtype='pos')
dep_parser = CoreNLPDependencyParser(url='http://localhost:9000')
pt_stemmer = pt.PorterStemmer()  # 波特词⼲提取器
verbs = ['access', 'assign', 'collect', 'create', 'enter', 'gather', 'import', 'obtain', 
    'observe', 'receive', 'request', 'understand', 'pick', 'pull', 'chase', 'gain', 'catch', 
    'win', 'ask','use', 'process', 'monitor', 'see', 'utilize', 'utilise', 'employ', 'take', 
    'upload', 'cache','delete','erase','keep', 'remove', 'retain', 'store', 'accumulate', 
    'hold', 'encrypt', 'encipher', 'cipher', 'save', 'maintain','reserve', 'communicate', 
    'disclose', 'reveal', 'receive', 'sell', 'send', 'view', 'share', 'transfer', 'provide', 'offer', 'render','expose', 'uncover', 'transport', 'transmit'
    ]
def tran_to_table(text):
    """
        输入：text\n

        输出：[['Third', 'JJ', '2', 'amod'],[],....]
    """
    parses, = dep_parser.raw_parse(text)
    A = parses.to_conll(4).split('\n')
    A.pop()
    B = []
    for a in A:
        B.append(a.split('\t'))
    return B

# Delete type 'Other' or 'Do Not Track'
def Del_type_other_track(Policy):
    temp = []
    for sentence in Policy:
        if sentence[2] == 'Other' or sentence[2] == 'Do Not Track':
            continue
        else:
            temp.append(sentence)
    return temp


# NLTK extract
def NLTK_extract_del_neg(Policy):
    """
        输入：政策（id, text, type）\n

        输出：删除完neg的政策（id, text, type）
    """
    # All the sentences in this policy
    temp = []
    Analyse_Policy = []
    for sentence in Policy:
        parses = dep_parser.parse(sentence[1].split())
        temp_analyse = [[(governor, dep, dependent) for governor, dep, dependent in parse.triples()] for parse in parses]
        temp_list = temp_analyse[0]
        Analyse_Policy.append(temp_list)
        temp.append(sentence)
        # All the words in this sentence
        for word in temp_list:
            if word[1] == 'neg':
                temp.pop()
                Analyse_Policy.pop()
                break
    return temp


# 通过词性标签‘ROOT’，还原root词并对照verbs表，不在则删
def del_root(Policy):
    """
        输入：政策（id, text, type）

        输出：删除完root的政策（id, text, type）
    """
    temp_policy = []
    for sentence in Policy:
        temp_policy.append(sentence)
        words = tran_to_table(sentence[1])
        for word in words:
            if word[3] == 'ROOT':
                pt_stem = pt_stemmer.stem(word[0])
                if pt_stem not in verbs:
                    temp_policy.pop()
                    break
    return temp_policy

def get_condition(Policy):
    result = []
    for sentence in Policy:
        flag = 0
        sum_str = ""
        words = tran_to_table(sentence[1])
        for word in words:
            if flag == 1 :
                sum_str += word[0] + ' '
                continue
            if word[3] == 'mark':
                flag = 1
                sum_str += word[0] + ' '
        if(len(sum_str) > 150):
            sum_str = ''
        result.append(sum_str)
    return result

def find_num(words, label):
    for word in words:
        if word[3] == label:
            return (words.index(word) + 1)
def get_collect_action(Policy):
    results = []
    for sentence in Policy:
        result = []
        words = tran_to_table(sentence[1])
        root_num = find_num(words, 'ROOT')
        for word in words:
            if word[3] == 'ROOT':
                result.append(word[0])
            if word[3] == 'conj' and int(word[2]) == root_num:
                pt_stem = pt_stemmer.stem(word[0])
                if pt_stem in verbs:
                    result.append(word[0])
        results.append(result)
    return results

# 去重复
def remove_dup(list_dup):
    list = []
    for i in list_dup:
        if i not in list:
            list.append(i)
    return list

def get_action_data_pairs(Policy, actions):
    """
        输入：政策（id, text, type）,动作（若干语句的动作集合）

        输出：政策中所有语句的隐私信息对的集合,和隐私数据主体,以及修饰过的隐私数据主体
    """
    data_mains = []
    for sentence, action in zip(Policy, actions):
        data_main_dup = []
        words = tran_to_table(sentence[1])
        for word in words:
            if (word[3] == 'nsubjpass' or word[3] == 'dobj') and words[int(word[2]) - 1][0] in action:
                data_main_dup.append(word[0])
        # 把同样等级的数据主体也找出来
        for word in words:
            if word[3] == 'conj' and words[int(word[2]) - 1][0] in data_main_dup:
                data_main_dup.append(word[0])
        # 去重复
        data_main = []
        for i in data_main_dup:
            if i not in data_main:
                data_main.append(i)
        data_mains.append(data_main)
    # print(data_mains)
    data_decorates = []
    for sentence, data_main in zip(Policy, data_mains):
        data_decorate = []
        flags = []
        words = tran_to_table(sentence[1])
        for i in range(len(data_main)):
            flags.append(0)
        for word in words:
            if (word[3] == 'amod' or word[3] == 'compound' or word[3] == 'advmod') and words[int(word[2]) - 1][0] in data_main:
                data_decorate.append(word[0] + ' ' + words[int(word[2]) - 1][0])
                flags[data_main.index(words[int(word[2]) - 1][0])] = 1
        for i in range(len(data_main)):
            if flags[i] == 0:
                data_decorate.append(data_main[i])
        data_decorates.append(data_decorate)
    # print(data_decorates)
    action_data_pairs = []
    for action, data_decorate in zip(actions, data_decorates):
        action_data_pair = []
        for a in action:
            for d in data_decorate:
                action_data_pair.append([a,d])
        action_data_pairs.append(action_data_pair)
    # print(action_data_pairs)
    return action_data_pairs, data_mains, data_decorates

def get_governors(Policy):
    """
        输入：政策（id, text, type）

        输出：政策中所有语句的主体的集合
    """
    governor_mains = []
    for sentence in Policy:
        governor_main = []
        words = tran_to_table(sentence[1])
        root_num = find_num(words, 'ROOT')
        for word in words:
            if word[3] == 'nsubj' and int(word[2]) == root_num:
                governor_main.append(word[0])
        # 把同样等级的主语主体也找出来
        for word in words:
            if word[3] == 'conj' and words[int(word[2]) - 1][0] in governor_main:
                governor_main.append(word[0])
        governor_mains.append(governor_main)
    # print(governor_mains)
    governor_decorates = []
    for sentence, governor_main in zip(Policy, governor_mains):
        governor_decorate = []
        flags = []
        words = tran_to_table(sentence[1])
        for i in range(len(governor_main)):
            flags.append(0)
        for word in words:
            if (word[3] == 'amod' or word[3] == 'compound' or word[3] == 'advmod') and words[int(word[2]) - 1][0] in governor_main:
                governor_decorate.append(word[0] + ' ' + words[int(word[2]) - 1][0])
                flags[governor_main.index(words[int(word[2]) - 1][0])] = 1
        for i in range(len(governor_main)):
            if flags[i] == 0:
                governor_decorate.append(governor_main[i])
        governor_decorates.append(governor_decorate)
    # print(governor_decorates)
    return governor_decorates
def ptint_policy_table(Policy, conditions, action_data_pairs, governors):
    # print("===============================================================")
    for sentence, condition, action_data_pair, governor in zip(Policy, conditions, action_data_pairs, governors):
        print("语句id：", sentence[0])
        print("语句type：", sentence[2])
        print(["action:",action_data_pair])
        print(["governor:",governor])
        print(["condition:",condition])
        print("===============================================================")

def extract_whole_part(Policy, datas):
    """
        输入：政策（id, text, type）, 隐私数据的主体数据

        输出：该隐私政策的所有整体部分对（[str,[]]）
    """
    rule1 = "([a-z]*), including,? (.*)"
    rule2 = "([a-z]*) includes?,? (.*)"
    rule3 = "([a-z]*) [a-z]* made of,? (.*)"
    rule4 = "([a-z]*),? such as,? (.*)"
    rule5 = "([a-z]*) contains?,? (.*)"
    rule6 = "([a-z]*) consists of,? (.*)"
    rule7 = "([a-z]*),? for example,? (.*)"
    rule8 = "([a-z]*),? for instance,? (.*)"
    rules = [rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8]
    recompiles = []
    for rule in rules:
        recompile = re.compile(rule)
        recompiles.append(recompile)
    whole_parts_pairs = []
    for sentence in Policy:
        flag_have_re_result = 0
        for recompile in recompiles:
            # print(recompile.findall(sentence[1]))
            if recompile.findall(sentence[1]) != []:
                re_result=recompile.findall(sentence[1])
                flag_have_re_result = 1
        # print("========================")
        if flag_have_re_result == 0:
            continue
        whole = re_result[0][0]
        part_temp = list(parser.tokenize(re_result[0][1]))
        part = []
        flag_sentence_over = 0
        for i in part_temp:
            if flag_sentence_over == 1:
                break
            if i != ',' and i != 'and' and i != '.':
                part.append(i)
            if i == '.' or i == ';':
                flag_sentence_over = 1

        # 判断整体是否在隐私数据里
        flag = 0
        for data in datas:
            # print(data)
            if whole in data:
                flag = 1
        words = tran_to_table(sentence[1])
        if flag == 1: # 说明是表示整体的词，则加修饰
            for word in words:
                if (word[3] == 'amod' or word[3] == 'compound' or word[3] == 'advmod') and (words[int(word[2]) - 1][0] == whole):
                    whole_decorate = word[0] + ' ' + whole
            # print(whole_decorate)
        else: # 获得句子的首个主语或宾语作为表示“整体”的单词
            for word in words:
                if  word[3] == 'dobj':
                # if (word[3] == 'nsubj' or word[3] == 'dobj'):
                    whole = word[0]
                    break
            # 补个修饰词
            flag_have_decorate = 0
            for word in words:
                if (word[3] == 'amod' or word[3] == 'compound' or word[3] == 'advmod') and (words[int(word[2]) - 1][0] == whole):
                    whole_decorate = word[0] + ' ' + whole
                    flag_have_decorate = 1
            # print(whole_decorate)
            # continue
            if flag_have_decorate == 0:
                whole_decorate = whole
        whole_parts_pairs.append([whole_decorate, part])
    return whole_parts_pairs

def get_Last_result(Policy, actions, data_decorates, whole_parts_pairs, governors, conditions):
    for data_decorate in data_decorates:
        for whole_parts_pair in whole_parts_pairs:
            if whole_parts_pair[0] in data_decorate:
                data_decorate.remove(whole_parts_pair[0])
                for new_data in whole_parts_pair[1]:
                    data_decorate.append(new_data)
    # print(data_decorates)
    # print(actions)

    action_data_pairs = []
    for action, data_decorate in zip(actions, data_decorates):
        action_data_pair = []
        for a in action:
            for d in data_decorate:
                action_data_pair.append([a,d])
        action_data_pairs.append(action_data_pair)
    # print(action_data_pairs)

    # 接下来需要对governor进行转换
    new_governors = []
    for sentence, governor in zip(Policy, governors):
        flag_governor_third = 0
        flag_governor_first = 0
        new_governor = []
        for one_governor in governor:
            if one_governor == "Third party" or one_governor == "third party":
                flag_governor_third = 1
                break
            if one_governor == "We" or one_governor == "we" or one_governor == "I" or one_governor == "my" or one_governor == "My" or one_governor == "our" or one_governor == "Our":
                flag_governor_first = 1
                break
        if flag_governor_third == 1 and flag_governor_first == 1:
            new_governor = 'First party and third party'
        elif flag_governor_third == 1:
            new_governor = 'Third party'
        elif flag_governor_first == 1:
            new_governor = 'First party'
        else:
            sentence_type = sentence[2]
            if sentence_type == 'First Party Collection/Use':
                new_governor = 'First party'
            elif sentence_type == 'Third Party Sharing/Collection':
                new_governor = 'Third party'
            else:
                new_governor = 'First party(default)'
        new_governors.append(new_governor)
    # print(new_governors)
    # print(conditions)

    # 合并结果并输出
    Last_results = []
    for action, datas, governor, condition in zip(actions, data_decorates, new_governors, conditions):
        for data in datas:
            Last_results.append([data, action, governor, condition])
    Last_results = remove_dup(Last_results)
    return Last_results, action_data_pairs, new_governors
                    
def write_into_csv(Last_results, out_file):
    fw = open(out_file, 'w')
    writer = csv.writer(fw)
    #先写入columns_name
    writer.writerow(["Privacy information","Collecting action","Collector","Condition"])
            #写入多行用writerows
    writer.writerows(Last_results)
    fw.close()

    # 中文输出
    # Last_results.insert(0, ["隐私信息","收集动作","收集方","条件"])
    # A = np.array(Last_results)
    # B = pd.DataFrame(A)
    # B.to_csv('/home/wufisher/Xinan/data/our_data/Result.csv', encoding='utf-8-sig') 


if __name__ == '__main__':
    # 输入文件为sample.csv，输出文件为predict_result.csv，返回到列表D：每行就是一个语句（id，文本，类别）
    D = bert_based.predict_to_file('/home/wufisher/Xinan/data/our_data/sample.csv', '/home/wufisher/Xinan/data/our_data/predict_result.csv')
    print("该隐私政策共划分为",len(D),"条语句")
    # ========================语句的筛选和处理========================
    print("========================语句的筛选和处理========================")
    D = Del_type_other_track(D)
    print("删除完\"Other\"和\"Do Not Track\"语句后还剩",len(D),"条语句")
    D = NLTK_extract_del_neg(D)
    print("删除完包含\"neg\"语义的语句后还剩",len(D),"条语句")
    D = del_root(D)
    print("删除完\"ROOT\"动词不在59个常用动词表里的语句后还剩",len(D),"条语句")
    # ========================隐私收集行为抽取========================
    print("========================隐私收集行为抽取========================")
    conditions = get_condition(D)
    actions = get_collect_action(D)
    action_data_pairs, datas, data_decorates = get_action_data_pairs(D, actions)
    governors = get_governors(D)
    ptint_policy_table(D, conditions, action_data_pairs, governors)

    # ========================整体与部分关系抽取========================
    print("========================整体与部分关系抽取========================")
    whole_parts_pairs = extract_whole_part(D, datas)
    print("whole_parts_pairs: ")
    for whole_parts_pair in whole_parts_pairs:
        print(whole_parts_pair)
    
    # ========================结果的整合与输出========================
    print("========================结果的整合与输出========================")
    Last_results, action_data_pairs, governors = get_Last_result(D, actions, data_decorates, whole_parts_pairs, governors, conditions)
    write_into_csv(Last_results, '/home/wufisher/Xinan/data/our_data/Last_result.csv')
    ptint_policy_table(D, conditions, action_data_pairs, governors)
