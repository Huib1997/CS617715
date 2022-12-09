# -*- coding: utf-8 -*-
"""
Created on Sat Dec  3 14:02:35 2022

@author: Huib
"""

import json
import numpy as np
import regex as re
import random 
import time
import math
import matplotlib.pyplot as plt
#%% 1. Function to determine all b and r values for a certain number of permutations

def Divisible(permutation):
    divisible = []
    for i in range(1,permutation+1):
        if permutation % i == 0:
            divisible.append(i)
    return divisible


#%% 2. Function to devide a list of numbers in two lists of numbers, train and test

def Bootstrap(all_tvs):
    tvs = len(all_tvs)
    train  = set()
    test   = set(range(0,tvs))
    for nr in range(tvs):
        random = np.random.randint(0,tvs)
        train.add(random)
        try:
            test.remove(random)
        except:
            pass
    

    return train, test
        
    
 #%% 3. Function on ab-hashing

def hfunc(x,a,b):
    value = (a + b*x) % prime_ab_hash
    return value  

#%% 4. Function on Jaccard Similarity

def jaccard_binary(x,y):
    """A function for finding the similarity between two binary vectors"""
    intersection = np.logical_and(x, y)
    union = np.logical_or(x, y)
    similarity = intersection.sum() / float(union.sum())
    return similarity

#%% 5. Parameter Definition 

permutations = 680
prime_ab_hash = 1297
a_max = 1000
b_max = 1000
bootstraps = 5
tcheck = [0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95]

#%% 6. Data loading and cleaning
 
raw_file = open('TVs-all-merged.json')

tvs = json.load(raw_file)

for tv in tvs:
    for field in tvs[tv]:
        field['title'] = field['title'].lower()
        field['title'] = field['title'].replace("inches","inch")
        field['title'] = field['title'].replace("-inch","inch")          
        field['title'] = field['title'].replace(" inch","inch") 
        field['title'] = field['title'].replace("\" " ,"inch ")
        field['title'] = field['title'].replace("\'" ,"inch ")
        
        field['title'] = field['title'].replace("("," ")
        field['title'] = field['title'].replace(")"," ")
        field['title'] = field['title'].replace(" /"," ")
        field['title'] = field['title'].replace(", "," ")
        
        field['title'] = field['title'].replace("HZ","hz")
        field['title'] = field['title'].replace("hertz","hz")
        field['title'] = field['title'].replace(" hertz","hz")
        field['title'] = field['title'].replace("-hz","hz")
        field['title'] = field['title'].replace(" hz","hz")
        field['title'] = field['title'].replace("Hz","hz")
           
#%% 7. Seperating titlewords and filtering out model words        

all_words = set()
for tv in tvs:
    for field in tvs[tv]:
        all_words.update(field['title'].split(' '))
         
model_words = []
for word in all_words:
    x = (re.search("[a-zA-Z0-9]*(([0-9]+[^0-9, ]+)|([^0-9, ]+[0-9]+))[a-zA-Z0-9]*", word))
    if x:
        model_words.append(word)

#%% 8. Creating dictionaries to fill title words, id, shop and the binary vector per tv              
all_tvs = []        
for tv_id in tvs:
        for field in tvs[tv_id]:
            all_tvs.append(dict())
            all_tvs[-1]['title_words'] = field['title'].split(' ')
            all_tvs[-1]['id'] = tv_id
            if 'newegg.com' in all_tvs[-1]['title_words']:
                all_tvs[-1]['brand'] = field['featuresMap']['Brand']
            
            all_tvs[-1]['shop']= field['shop'] 
            all_tvs[-1]['binary_list'] = []
            for word in model_words:
                x = word in all_tvs[-1]['title_words']
                if x :
                    all_tvs[-1]['binary_list'].append(1)
                else :
                    all_tvs[-1]['binary_list'].append(0)

tvnr = len(all_tvs)
#%% 9. Adding the brand names to model words

brands = set()
for tv in range(tvnr):
    
    if 'newegg.com' in all_tvs[tv]['title_words']: 
        brand = all_tvs[tv]['brand'].lower().split()
        brands.add(brand[0])
    else:
        brands.add(all_tvs[tv]['title_words'][0].lower())
        
model_words = model_words + list(brands)    

#%% 10. Creating the charactermatrix containing all binary vectors 
first_matrix = []            
        
for tv in all_tvs:
    first_matrix.append(np.array(tv.get('binary_list')))
       
        

#%% 11. Creating the random order of rows per permutation 

permutation = []
for n in range(permutations):
    perm = []
    a = random.randint(1,a_max)
    b = random.randint(1,b_max)  
    i = 0  
    for row in first_matrix[0]:
        perm.append(hfunc(i,a,b))
        i = i + 1
    permutation.append(perm)

#%% 12. Creating the signature matrix

signature_matrix = []
for perm in permutation:
    lolly = []
    for tv in all_tvs:
        lolly.append(float ("inf"))
    signature_matrix.append(lolly)

for i in range(1291):
    for n in range(tvnr):
        if first_matrix[n][i]==1:
            for p in range(permutations):
                if permutation[p][i] < signature_matrix[p][n]:
                    signature_matrix[p][n] = permutation[p][i]    
    
     
                        
#%% 13. Making the bands, hashing them and bootstrapping to find t_c per (band,row)-pair


PC_list = []
PQ_list = []
F1_list = []
FR_list = []

bandnr = [34, 40, 68, 85, 136, 170, 340]
F1_everything = []


for bands in bandnr:
    print(bands)
    bandrows = permutations // bands
    hashed_vectors = []
    for tv in range(tvnr):
        tel = 0 
        lijst = []
        for band in range(bands):
            stringnr = str()
            for bandrow in range(bandrows):
                stringnr += str(signature_matrix[tel][tv])
                tel+=1
            stringvalue = int(stringnr)
            stringvalue = stringvalue % 123456789123456789
            lijst.append(stringvalue)    
        hashed_vectors.append(lijst)  
               

    F1_ts = []
    for b in range(bootstraps):    
        train, test = Bootstrap(all_tvs) 
        
        counter = 0
        for product1 in train:
            for product2 in train:
                if product2 > product1:
                    if all_tvs[product1]['id'] == all_tvs[product2]['id']:
                        counter += 1
                    
        F1_old = 0;
        for t in tcheck:
            candidate_pairs = []
            candidate_pairs_selected = []
            candidate_pairs_match = []
            
            for product1 in train:
                for product2 in train:
                    if product2 > product1:
                        for band in range(bands):
                            if all_tvs[product1]['shop'] != all_tvs[product2]['shop']:
                                if hashed_vectors[product1][band] == hashed_vectors[product2][band]:
                                    Jaccard = jaccard_binary(all_tvs[product1]['binary_list'],all_tvs[product2]['binary_list'])
                                    candidate_pairs.append([product1, product2,Jaccard])
                                    break
                        
                      
            candidate_size = (len(candidate_pairs))            
            for candidate in range(len(candidate_pairs)):
                if candidate_pairs[candidate][2] >=t:
                    candidate_pairs_selected.append(candidate_pairs[candidate]) 
                    if all_tvs[candidate_pairs[candidate][0]]['id'] == all_tvs[candidate_pairs[candidate][1]]['id']:
                        candidate_pairs_match.append(candidate_pairs[candidate])
        
            PQ = len(candidate_pairs_match)/len(candidate_pairs_selected)
            PC = len(candidate_pairs_match)/counter
            
            F1 = 2*PQ*PC/(PQ+PC) 
            if F1 > F1_old:
                F1_t = t 
                print(F1)
            F1_old = F1
        F1_ts.append(F1_t)
        print(F1_t)
    F1_everything.append(F1_ts)    
        
#%% 14. Bootstrapping again over all (band,row) pairs and their maximizing value of tc

bandnr = Divisible(permutations)
Scores = []

for bands in bandnr:
    t = 0.65
    if bands == 34:
        t = 0.75
    print(bands)
    bandrows = permutations // bands
    hashed_vectors = []
    for tv in range(tvnr):
        tel = 0 
        lijst = []
        for band in range(bands):
            stringnr = str()
            for bandrow in range(bandrows):
                stringnr += str(signature_matrix[tel][tv])
                tel+=1
            stringvalue = int(stringnr)
            stringvalue = stringvalue % 123456789123456789
            lijst.append(stringvalue)    
        hashed_vectors.append(lijst)  
            
    PQ_b = []
    PC_b = []
    F1_b = []
    FR_b = []                   
    for b in range(bootstraps):        
        train, test = Bootstrap(all_tvs) 
        golden_standard = []
        counter = 0
        for product1 in train:
            for product2 in train:
                if product2 > product1:
                    if all_tvs[product1]['id'] == all_tvs[product2]['id']:
                        counter += 1    
        
        
        F1_old = 0;
        candidate_pairs = []
        candidate_pairs_selected = []
        candidate_pairs_match = []
        
        for product1 in train:
            for product2 in train:
                if product2 > product1:
                    for band in range(bands):
                        if all_tvs[product1]['shop'] != all_tvs[product2]['shop']:
                            if hashed_vectors[product1][band] == hashed_vectors[product2][band]:
                                Jaccard = jaccard_binary(all_tvs[product1]['binary_list'],all_tvs[product2]['binary_list'])
                                candidate_pairs.append([product1, product2,Jaccard])
                                break
                    
                  
        candidate_size = (len(candidate_pairs))            
        for candidate in range(len(candidate_pairs)):
            if candidate_pairs[candidate][2] >=t:
                candidate_pairs_selected.append(candidate_pairs[candidate]) 
                if all_tvs[candidate_pairs[candidate][0]]['id'] == all_tvs[candidate_pairs[candidate][1]]['id']:
                    candidate_pairs_match.append(candidate_pairs[candidate])
    
        PQ = len(candidate_pairs_match)/len(candidate_pairs_selected)
        PC = len(candidate_pairs_match)/counter
        F1 = 2*PQ*PC/(PQ+PC) 
        FR = len(candidate_pairs) / (len(train)*(len(train)-1)/2)
        
        PQ_b.append(PQ)
        PC_b.append(PC)
        F1_b.append(F1)
        FR_b.append(FR)
    
   
    PQ_m = max(PQ_b)
    PC_m = max(PC_b)
    F1_m = max(F1_b)  
    FR_m = max(FR_b)
    
    
    PQ_a = sum(PQ_b)/bootstraps
    PC_a = sum(PC_b)/bootstraps
    F1_a = sum(F1_b)/bootstraps  
    FR_a = sum(FR_b)/bootstraps

    print(F1_m)
    print(F1_a)
    Scores.append([PQ_a,PC_a,F1_a,FR_a])
    
    
        
#%% 15. Plotting results

PQ_plot = []
PC_plot = []
F1_plot = []
FR_plot = []


for i in range(len(Scores)):
    PQ_plot.append(Scores[i][0])
    PC_plot.append(Scores[i][1])
    F1_plot.append(Scores[i][2])
    FR_plot.append(Scores[i][3])
                   

#plt.plot(FR_plot, F1_plot)
plt.plot(FR_plot, PQ_plot)
#plt.plot(FR_list,F1_list)







