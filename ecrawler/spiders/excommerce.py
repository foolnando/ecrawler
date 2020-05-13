# -*- coding: utf-8 -*-
import scrapy
from scrapy import signals
from scrapy.crawler import CrawlerProcess
import scipy.cluster.hierarchy as sch
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import AgglomerativeClustering 
from ecrawler.items import EcrawlerItem
import re

class ExcommerceSpider(scrapy.Spider):
    name = 'excommerce'
    allowed_domains = ['magazineluiza.com.br']
    start_urls = ['https://www.magazineluiza.com.br/']
    scoreUrl = []
    url = []
    keywords = ['entrar','cart','carrinho','login','logar',
    'faq','sac','faleconosco','fale-conosco','remacoes',
    'checkout','logout', 'checkin', 'minha-conta', 'conta', 
    'account', 'External', 'blog', 'cartao']
    entryUrl = 'https://www.magazineluiza.com.br/'



    def createMatrix(self,A,B):
        '''cria e preenche uma matriz de i linhas e j colunas'''
        matrix = []
        count=0
        for i in A:
            matrix.append([])
            for j in B:
                matrix[count].append(None)
            if(count==(len(A)-1)):
                return matrix
            else:
                count+=1

    def penalty(self,x,y):
        '''penalizacao da comparacao dos pares 1 para match, -1 para mismatch, -2 para gap'''
        if(x==y):
            return 1
        elif(x!=y and (x=="-" or y=="-")):
            return -2
        else:
            return -1

    def finalScore(self,A,B):
        '''calcula o score final do alinhamento consultando a funcao finalScore'''
        i=len(A)
        count=0
        for element in range(0,i):
            count+=self.penalty(A[element],B[element])
        return count


    def miss(self,A,B):
        i=len(A)
        missesA = ''
        missesB = ''
        for element in range(0, i):
            if(A[element]!=B[element]):
                for c in range(element, len(A)):
                    missesA+=A[c]
                for d in range(element,len(B)):
                    missesB+=B[d]

        return missesA,missesB

    def matches(self,A,B):
        i = len(A)
        word = ''
        for element in range(0,i):
            if(A[element]==B[element]):
                word += A[element]
            else:
                break
        return word


    def align(self,A,B):
        '''alinha duas sequencias'''

        #Cria a matriz F e define o valor do gap
        F=self.createMatrix(A,B)
        #GAP
        d=-2

        #preenchendo a primeira linha da matriz F
        for i in range(len(A)):
            F[i][0] = d*i
        #preenchendo a primeira coluna da matriz F
        for j in range(len(B)):
            F[0][j] = d*j

        #preenchendo as outras posicoes da matriz F com o maior valor entre as cedulas de cima, esquerda e diagonal.
        for i in range(1,len(A)):
            for j in range(1,len(B)):
                choice1 = F[i-1][j-1] + self.penalty(A[i-1],B[j-1])
                choice2 = F[i-1][j] + d
                choice3 = F[i][j-1] + d
                F[i][j] = max(choice1,choice2,choice3)

        AlignmentA=""
        AlignmentB=""

        i=len(A)-1
        j=len(B)-1
        #alinhando as sequencias A,B
        while(i>0 and j>0):
            #calcula os scores da posicao atual e de seus vizihos. Comecando da ultima posicao da matriz.
            score = F[i][j]
            scoreDiag = F[i-1][j-1]
            scoreUp = F[i][j-1]
            scoreLeft = F[i-1][j]
            if(score==scoreDiag + self.penalty(A[i-1],B[j-1])):
                if(AlignmentA=="" and AlignmentB==""):
                    AlignmentA = A[i]+AlignmentA
                    AlignmentB = B[j]+AlignmentB
                AlignmentA = A[i-1]+AlignmentA
                AlignmentB = B[j-1]+AlignmentB
                i = i-1
                j = j-1
            elif(score==scoreLeft + d):
                AlignmentA = A[i-1]+AlignmentA
                AlignmentB = "-"+AlignmentB
                i = i-1
            elif(score==scoreUp + d):
                AlignmentA = "-"+AlignmentA
                AlignmentB = B[j-1]+AlignmentB
                j = j-1
        while(i>0):
            AlignmentA = A[i-1]+AlignmentA
            AlignmentB = "-"+AlignmentB
            i = i-1
        while(j>0):
            AlignmentA = "-"+AlignmentA
            AlignmentB = B[j-1]+AlignmentB
            j = j-1

        retorno = []
        retorno.append(self.finalScore(AlignmentA,AlignmentB))
        retorno.append(len(self.matches(AlignmentA,AlignmentB)))
        return [self.finalScore(AlignmentA,AlignmentB),len(self.matches(AlignmentA,AlignmentB))]

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(ExcommerceSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider


    def spider_closed(self,spider):
        comp = 'https://www.nerdstickers.com.br/'
        if not self.scoreUrl:
            print("link has not been given a value")
        hc = AgglomerativeClustering(n_clusters = 4, affinity = 'euclidean', linkage ='ward')
        x_hc=hc.fit_predict(self.scoreUrl)
        x = np.array(self.scoreUrl)
        plt.scatter(x[x_hc==0, 0], x[x_hc==0, 1], s=100, c='red', label ='Cluster 1')
        plt.scatter(x[x_hc==1, 0], x[x_hc==1, 1], s=100, c='blue', label ='Cluster 2')
        plt.scatter(x[x_hc==2, 0], x[x_hc==2, 1], s=100, c='green', label ='Cluster 3')
        plt.scatter(x[x_hc==3, 0], x[x_hc==3, 1], s=100, c='cyan', label ='Cluster 4')
        plt.scatter(x[x_hc==4, 0], x[x_hc==4, 1], s=100, c='magenta', label ='Cluster 5')
        plt.title('Clusters of Url Score of a site (Hierarchical Clustering Model)')
        plt.xlabel('Score do alinhamento')
        plt.ylabel('minimo radical comum')
        plt.show()

        # grtst=0
        # indxGrts=0
        # for i in range(0,4):
        #     x0 = x[x_hc==i, 0], x[x_hc==i, 1]
        #     if(len(x0[0])>grtst):
        #         indxGrts=i
        #         grtst = len(x0[0])
                
        # print(grtst, indxGrts)
        # print(len(x[x_hc==0, 0]))
        # print(len(x[x_hc==1, 0]))
        # print(len(x[x_hc==2, 0]))
        # print(len(x[x_hc==3, 0]))
        # print(len(x[x_hc==4, 0]))
        
        # compx = x[x_hc==indxGrts, 0]
        # compy = x[x_hc==indxGrts, 1]

        # for g in range(0, len(self.scoreUrl)):
        #     #score = self.align(self.entryUrl,self.url[g])
        #     for i in range(grtst):
        #         if(self.scoreUrl[g][0]==compx[i] and self.scoreUrl[g][1]==compy[i]):
        #             print('path', self.url[g], 'score', self.scoreUrl[g])
        #             break

        compx0 = x[x_hc==0, 0]
        compy0 = x[x_hc==0, 1]
        print('cluster 1')
        print(len(x[x_hc==0, 0]))
        for g in range(0, len(self.scoreUrl)):
            #score = self.align(self.entryUrl,self.url[g])
            for i in range(len(x[x_hc==0, 0])):
                if(self.scoreUrl[g][0]==compx0[i] and self.scoreUrl[g][1]==compy0[i]):
                    print('path', self.url[g], 'score', self.scoreUrl[g],'cluster 1')
                    break

        compx1 = x[x_hc==1, 0]
        compy1 = x[x_hc==1, 1]
        print('cluster 2')
        print(len(x[x_hc==1, 0]))
        for g in range(0, len(self.scoreUrl)):
            #score = self.align(self.entryUrl,self.url[g])
            for i in range(len(x[x_hc==1, 0])):
                if(self.scoreUrl[g][0]==compx1[i] and self.scoreUrl[g][1]==compy1[i]):
                    print('path', self.url[g], 'score', self.scoreUrl[g], 'cluster 2')
                    break

        compx2 = x[x_hc==2, 0]
        compy2 = x[x_hc==2, 1]
        print('cluster 3')
        print(len(x[x_hc==2, 0]))
        for g in range(0, len(self.scoreUrl)):
            #score = self.align(self.entryUrl,self.url[g])
            for i in range(len(x[x_hc==2, 0])):
                if(self.scoreUrl[g][0]==compx2[i] and self.scoreUrl[g][1]==compy2[i]):
                    print('path', self.url[g], 'score', self.scoreUrl[g], 'cluster 3')
                    break

        compx3 = x[x_hc==3, 0]
        compy3 = x[x_hc==3, 1]
        print('cluster 4')
        print(len(x[x_hc==3, 0]))
        for g in range(0, len(self.scoreUrl)):
            #score = self.align(self.entryUrl,self.url[g])
            for i in range(len(x[x_hc==3, 0])):
                if(self.scoreUrl[g][0]==compx3[i] and self.scoreUrl[g][1]==compy3[i]):
                    print('path', self.url[g], 'score', self.scoreUrl[g], 'cluster 4')
                    break

        # compx4 = x[x_hc==4, 0]
        # compy4 = x[x_hc==4, 1]
        # print('cluster 5')
        # print(len(x[x_hc==4, 0]))
        # for g in range(0, len(self.scoreUrl)):
        #     #score = self.align(self.entryUrl,self.url[g])
        #     for i in range(len(x[x_hc==4, 0])):
        #         if(self.scoreUrl[g][0]==compx4[i] and self.scoreUrl[g][1]==compy4[i]):
        #             print('path', self.url[g], 'score', self.scoreUrl[g], 'cluster 5')
        #             break
        
        print('oi')
        print(len(x[x_hc==0, 0]))
        print(len(x[x_hc==1, 0]))
        print(len(x[x_hc==2, 0]))
        print(len(x[x_hc==3, 0]))
        # print(len(x[x_hc==4, 0]))
        self.parsed()
        #spider.logger.info('Spider closed: %s', spider.name)

    def parse(self, response):
        noExcepted = []
        #entryUrl = 'https://www.nerdstickers.com.br/'
        self.url.append(response.url)
        score = self.align(self.entryUrl,response.url)
        self.scoreUrl.append(score)
        if(score[1]>=10):
            links = response.xpath('//@href').extract()
            for link in links:
                for word in range(0, len(self.keywords)):
                    noExcepted = re.findall(self.keywords[word], link)
                    if(len(noExcepted)>0):
                        break
                if(len(noExcepted)==0):
                    # self.url.append(link)
                    # score = self.align(entryUrl,link)
                    # self.scoreUrl.append(score)
                    yield scrapy.Request(response.urljoin(link), callback=self.parse)
                #if(response.meta['depth'] < 4):
                    #yie3ld scrapy.Request(response.urljoin(link), callback=self.parse)
    
    def parsed(self):
        item = EcrawlerItem()
        print('tchau')
        