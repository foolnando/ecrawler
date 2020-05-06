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
    allowed_domains = ['chicorei.com']
    start_urls = ['https://chicorei.com/']
    scoreUrl = []
    url = []
    keywords = ['entrar','cart','carrinho','login','logar',
    'faq','sac','faleconosco','fale-conosco','remacoes',
    'checkout','logout', 'checkin', 'minha-conta', 'conta', 
    'account']
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
        if not self.scoreUrl:
            print("link has not been given a value")
        hc = AgglomerativeClustering(n_clusters = 5, affinity = 'euclidean', linkage ='ward')
        y_hc=hc.fit_predict(self.scoreUrl)
        y = np.array(self.scoreUrl)
        plt.scatter(y[y_hc==0, 0], y[y_hc==0, 1], s=100, c='red', label ='Cluster 1')
        plt.scatter(y[y_hc==1, 0], y[y_hc==1, 1], s=100, c='blue', label ='Cluster 2')
        plt.scatter(y[y_hc==2, 0], y[y_hc==2, 1], s=100, c='green', label ='Cluster 3')
        plt.scatter(y[y_hc==3, 0], y[y_hc==3, 1], s=100, c='cyan', label ='Cluster 4')
        plt.scatter(y[y_hc==4, 0], y[y_hc==4, 1], s=100, c='magenta', label ='Cluster 5')
        plt.title('Clusters of Customers (Hierarchical Clustering Model)')
        plt.xlabel('Score do alinhamento')
        plt.ylabel('minimo radical comum')
        plt.show()
        print('path', self.url[0], 'score', self.scoreUrl[0])
        print('oi')
        self.parsed()
        #spider.logger.info('Spider closed: %s', spider.name)

    def parse(self, response):
        noExcepted = []
        entryUrl = 'https://chicorei.com/'
        # self.url.append(response.url)
        # score = self.align(entryUrl,response.url)
        # self.scoreUrl.append(score)
        links = response.xpath('//@href').extract()
        for link in links:
            for word in range(0, len(self.keywords)):
                noExcepted = re.findall(self.keywords[word], link)
                if(len(noExcepted)>0):
                    break
            if(len(noExcepted)==0):
                self.url.append(response.url)
                score = self.align(entryUrl,response.url)
                self.scoreUrl.append(score)
            #if(response.meta['depth'] < 4):
                #yie3ld scrapy.Request(response.urljoin(link), callback=self.parse)
    
    def parsed(self):
        item = EcrawlerItem()
        print('tchau')
        