import json

S = {""}
data = []
l = []

with open('in.json') as json_file:
    data = json.load(json_file)
    #print(data)
    for x in data:
#        print(x)
#        print(x['link'])
#        print((x['link'] in S))
       if(not (x['link'] in S)):
            S.add(x['link'])
       else:
           l.append(x);

for i in range(0,len(l)):
    data.remove(l[i])

print(len(data))
    
with open('out6.json', 'w') as outfile:
    json.dump(data, outfile)
    json.dump(len(data),outfile)

