#encoding: utf-8

import pandas as pd
import csv
from bs4 import BeautifulSoup as bs
import os

def preprocess(htmlpath, csvpath):
    #整合路径
    devidesigns = ['\n','1.','2.','3.','4.','5.','6.','7.','8.','9.','10.','11.','12.','13.','14.','15.','16.','17.','18.','19.','20.'
                   '(i)','(ii)','(iii)','(iv)','(v)','(vi)','(vii)',
                   '(viii)','(ix)','(x)','(xi)','(xii)','(xiii)','(xiv)','(xv)',
                   ]
    endsigns = [':',';','.']
    devidesigns = devidesigns + endsigns

    def find_all(sub, s):
        index_list = []
        index = s.find(sub)
        while index != -1:
            index_list.append(index)
            index = s.find(sub, index + 1)

        if len(index_list) > 0:
            return index_list
        else:
            return index_list

    namelist =[]
    for name in os.listdir(htmlpath):
        #print name.strip(".csv")
        namelist.append(name[0:-5])
    #print namelist

    for filename in namelist:
        #print filename
        soup = bs(open(htmlpath +filename+".html"), 'html.parser')
        #print(soup.get_text())
        ssoup = soup.get_text().encode('utf-8')
        ssoup = ssoup.decode()
        # division
        devidepoint = []
        devidepoint.append(0)
        devidepoint.append(len(ssoup)-1)
        #截取，直接find获取每个分割点
        for devidesign in devidesigns:
            #print 'find ' + devidesign + 'at'
            #print find_all(devidesign, ssoup)
            #print (devidesign)
            devidepoint = devidepoint + find_all(devidesign, ssoup)
        devidepoint.sort()
        #print devidepoint

        #去除连续的分割点，同时处理特殊分割点，比如XXX; XXX，比如XXX. XXX
        devidepointcut = []
        devidepointcut.append(devidepoint[0])
        for index in range(1,len(devidepoint)):
            #print index
            if devidepoint[index] != devidepoint[index-1] + 1:
                if ssoup[devidepoint[index]] in endsigns:
                    if ssoup[devidepoint[index]] == '.' and len(ssoup) >= devidepoint[index]+2 and ssoup[devidepoint[index]+1] == ' ':
                        #不分段，忽略这个分割点
                        devidepointcut
                    else:
                        devidepointcut.append(devidepoint[index] + 1)
                else:
                    devidepointcut.append(devidepoint[index])
            index = index +1
        #print devidepointcut

        #存放
        outcsv = open(csvpath + filename + ".csv","w")
        writer = csv.writer(outcsv)
        sentenccounter = 0
        for index in range(len(devidepointcut)-2):
            sentencecut = ssoup[devidepointcut[index]:devidepointcut[index+1]]
            #去除换行符，去除开头空格，结尾空格
            sentencecut = sentencecut.strip()
            print(sentencecut)
            if sentencecut != '':
                writer.writerow([sentenccounter, sentencecut])
                sentenccounter = sentenccounter + 1
        outcsv.close()

        #去空行
        pdcsv = pd.read_csv(csvpath + filename + ".csv",names=["ID","content"])
        pdcsv.to_csv(csvpath + filename + ".csv")


htmlpath = "/home/wufisher/Xinan/predata/"
csvpath = "/home/wufisher/Xinan/data/our_data/"
if __name__ == '__main__':
    preprocess(htmlpath,csvpath)