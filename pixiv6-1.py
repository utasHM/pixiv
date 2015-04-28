# -*- coding: utf-8 -*-
import pandas as pd
from dateutil.parser import parse
from datetime import datetime
import collections
import networkx as nx

#前アカウントがBANされたっぽいので、新しくアカウントを作った。
#140930 PHSESSIDは一か月ほどで新しいものになるっぽい。。。取得しなおした。

keyword ="ドラえもん"
#SSID を取得するには、ブラウザでpixivにログイン後、cookieのpixiv.netにあるPHPSESSIDを用いる。
SSID = "4386519_3d5e81db977a6367703b5d852d12f10a" #2015年5月16日土曜日 19:33:31
preurl = "http://spapi.pixiv.net/iphone/search.php?s_mode=s_tag&word=" + keyword + "&PHPSESSID=" + SSID

# &order=date で古い順になる

#空のデータフレームを取得
frame = pd.DataFrame()

for pagenum in range(1,201):
    url = preurl + "&p=" + str(pagenum)
    df = pd.read_csv(url, header=None, encoding='utf-8')
    if len(df[0]) == 50:
        frame = frame.append(df)
        print pagenum ,
    elif len(df[0]) == 49: #タグが1つしかない作品はなぜか長さにカウントされないので。頻度は非常にまれなのでこれで十分。
        url2 = preurl + "&p=" + str(pagenum+1)
        df2 = pd.read_csv(url, header=None, encoding='utf-8')
        if len(df2[0]) ==50: #ページ途中が49個なのか、ページ最後が49個なのか確かめる。次のページがあるかどうか。
            frame = frame.append(df)
            print pagenum , 
        elif len(df2[0]) == 49:
            frame = frame.append(df)
            print pagenum ,
        else:
            frame = frame.append(df)
            print pagenum
            break
    elif len(df[0]) == 48: #タグが1つしかない作品はなぜか長さにカウントされないので。頻度は非常にまれなのでこれで十分。
        url2 = preurl + "&p=" + str(pagenum+1)
        df2 = pd.read_csv(url, header=None, encoding='utf-8')
        if len(df2[0]) ==49: #ページ途中が49個なのか、ページ最後が49個なのか確かめる。次のページがあるかどうか。
            frame = frame.append(df)
            print pagenum , 
        elif len(df2[0]) == 48:
            frame = frame.append(df)
            print pagenum ,
        else:
            frame = frame.append(df)
            print pagenum
            break 
    else:
        frame = frame.append(df)
        print pagenum
        break


frame2 = frame[[0,1,12,13]]
frame2.columns=["picID","userID","datetime","tags"]


#datetimeを日付と時間のカラムに分ける
datelist = list()
timelist = list()
for date in frame2.datetime:
    datelist.append(parse(date).date())
    timelist.append(parse(date).time())

frame2["date"] = datelist
frame2["time"] = timelist


fp = frame2.tags
cnt = collections.Counter()
for line in fp:
    tag = line.split(' ')
    for word in tag:
        cnt[word] += 1
  
#print "counts,word"
  
wordlist0 = list()
wordcount0 = list()
wordlist1 = list()
wordcount1 = list()

for word, counts in sorted(cnt.items(), key = lambda x:x[1], reverse = True): #登録された単語を頻度降順で表示
   #print str(counts) + "," + word
   wordlist0.append(word)
   wordcount0.append(counts)
   #print word + "\t" + str(counts)

#keywordおよびusers入りを一部でも含むタグをwordlistから除去(ガンダムなどシリーズものの場合、keywordは除去しないほうがいいかも??)
print u'keyword、users入りを含むタグのため、以下を除去'
for i in range(0,len(wordlist0)-1):
#タグを除去しない
#    if keyword in wordlist0[i]:
#        print i, u'番目を除去'
    if "users" in wordlist0[i]:
        print i, u'番目を除去'
    else:
        wordlist1 = wordlist1 + [wordlist0[i]]
        wordcount1 = wordcount1 + [wordcount0[i]]

#nodeのリスト、重みを作成。
d = {'Weight': pd.Series(wordcount1), 'Nodes': pd.Series(wordlist1)}
node = pd.DataFrame(d)

#1,2個しかないタグを除去。これは以下の計算には使用しない。
node2 = pd.DataFrame()
for z in range(0,len(node)-1):
    if node.iloc[z][u"Weight"] > 2:
        node2 = node2.append(node.iloc[z])
node2.to_csv(keyword.encode('cp932') + "node.csv", index=False, encoding='utf-8')

#上位200個のタグのみ選ぶ。以下の計算にはこちらを使用。
wordlist2 = list()
if len(node2) > 199: 
    wordlist2 = wordlist1[0:200]
else: #上で除去後のタグの数が200を切っているとき
    wordlist2 = wordlist1[0:len(node2)]

#タグが含まれているか2値のカラムを作る。タグ頻度上位順。
for chara in wordlist2:
    templist = []
    for tags in frame2.tags:
        if chara.encode('utf-8') in tags.encode('utf-8').split():
            templist.append(1)
        else:
            templist.append(0)
    frame2[chara.encode("utf-8")] = templist
        
#不要なカラムを削除
del frame2["tags"]
del frame2["datetime"]
frame2.to_csv(keyword.encode('cp932') + ".csv",index=False,encoding='utf-8')


#ファイルを読み込む
pixivdata = pd.read_csv(keyword.encode('cp932') + ".csv",encoding="utf-8")

#frame3から不要なカラムを消す
del pixivdata["userID"]
del pixivdata["date"]
del pixivdata["time"]

#カラム名からキャラクター名を取得
chara2 = pixivdata.columns[1:]
num = 0
charaID = list()
for x in chara2:
    charaID.append([x,num])
    num += 1

#キャラクターにIDを付与
charaID = pd.DataFrame(charaID)
charaID.columns = [u"aキャラクター",u"ID"]
#print charaID

#トランザクションデータに変換
transaction = list()
for x in range(0,len(pixivdata)):
    line = pixivdata.ix[x]
    for ctmp in chara2:
        if line[ctmp] == 1:
            transaction.append([line[u"picID"],ctmp])
transaction = pd.DataFrame(transaction)
transaction.columns = [u"picID",u"aキャラクター"]
#print transaction

#作成したキャラクターIDを付与
transaction = pd.merge(transaction, charaID, on = u"aキャラクター")

#自分自身で内部結合
pairframe = pd.merge(transaction,transaction,on = u"picID", how="inner")
#print pairframe

#重複するペアを削除
pairs = list()
for x in range(0,len(pairframe)):
    line = pairframe.ix[x]
    if line[u"ID_x"] < line[u"ID_y"]:
        pairs.append(line)
pairs = pd.DataFrame(pairs)
#print pairs

#共演した数を集計
count = pairs.groupby([u"aキャラクター_x",u"aキャラクター_y"]).count()[[u"picID"]]
#print count
count.to_csv(keyword.encode('cp932') +"edges.csv",encoding="utf-8")


#ある程度の重複頻度でカットオフ。
count2 = pd.DataFrame()
temp = pd.DataFrame()
temp = pd.read_csv(keyword.encode('cp932') + "edges.csv",encoding="utf-8")
for y in range(0,len(count)-1):
    if count.iloc[y][u"picID"] > 9:
        count2 = count2.append(temp.iloc[y])
count2.to_csv(keyword.encode('cp932') +"edges2.csv",encoding="utf-8",index=False, header=True)
#edges2.csvを使えばCytoscapeで描ける


#Gephi用のデータを作成
G=nx.Graph()
for m in range(0,len(wordlist2)-1):
    G.add_node(node2.iloc[m][u"Nodes"], size=int(node2.iloc[m][u"Weight"]))
for n in range(0,len(count2)-1):
    G.add_edge(count2.iloc[n][0], count2.iloc[n][1], weight=count2.iloc[n][u'picID'] )

nx.write_gexf(G, keyword.encode('cp932') + ".gexf", encoding='utf-8')


#参考:"http://kiito.hatenablog.com/entry/2013/12/18/124341"
#参考:"http://kiito.hatenablog.com/entry/2013/12/18/015248"