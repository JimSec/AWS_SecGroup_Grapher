import boto3 
import networkx as nx
from pyvis.network import Network

# Quick and dirty visualizer to create a graph of all security groups and resources in AWS environment. 

def createGraph(graph:dict):
    
    G = nx.Graph()

    for n in graph:
        #add sec group node in green
        G.add_node(n, color='green')
        for s in graph[n]:

            #print(s)
            if s not in G:
                if "ec2:" in s:
                    color = "#4169E1"
                elif "elb:" in s:
                    color = "#4B0082"
                elif "elbv2:" in s:
                    color = "#9370DB"
                elif "rds:" in s:
                    color = "#b22222"
                elif "elc:" in s:
                    color = "#D2B48C"
                elif "lambda:" in s:
                    color = "#708090"
                else:
                    color = "#000000"
                G.add_node(s, color=color)
                G.add_edge(n,s, color='green')
            else:
                G.add_edge(n,s, color='green')
        i += 1                                           

    net = Network(height='768px', width='1366px', notebook=True)
    net.from_nx(G)

    net.show("secgroup_graph.html")

def GetAllSecGroups(data):
    client = boto3.client('ec2')
    for g in client.describe_security_groups()['SecurityGroups']:
        data[g['GroupId']] = []


# tbd trim into single map function 
def MapEc2SecGroups(data):
    client = boto3.client('ec2')
    instances = client.describe_instances()

    for r in instances['Reservations']:
        for i in r['Instances']:
            #print(i['InstanceId'])
            for g in i['SecurityGroups']:
                if g['GroupId'] in data.keys():
                    data[g['GroupId']].append("ec2:"+i['InstanceId'])

def MapElasticLoadBalSecGroups(data):
    client = boto3.client('elb')
    lbs = client.describe_load_balancers()
    for i in lbs['LoadBalancerDescriptions']:
        for g in i['SecurityGroups']:
            if g in data.keys():
                data[g].append("elb:"+i['LoadBalancerName'])

    clientv2 = boto3.client('elbv2')
    lbsv2 = clientv2.describe_load_balancers()
    for i in lbsv2['LoadBalancers']:
        for g in i['SecurityGroups']:
            if g in data.keys():
                data[g].append("elbv2:"+i['LoadBalancerName'])

def MapElasticBeanstalkSecGroups(data):
    client = boto3.client('elasticbeanstalk')
    if client.describe_environments()['Environments'] == []:
        print("No ElasticBeanStalk ENV's found")

def MapRDSSecGroups(data):
    client = boto3.client('rds')
    inst = client.describe_db_instances()
    for i in inst['DBInstances']:
        #print(i['DBInstanceIdentifier'])
        if i['VpcSecurityGroups'] != []:
            for g in i['VpcSecurityGroups']:
                if g['Status'] == 'active':
                    if g['VpcSecurityGroupId'] in data.keys():
                        data[g['VpcSecurityGroupId']].append("rds:"+i['DBInstanceIdentifier'])

def MapElastiCacheSecGroups(data):
    client = boto3.client('elasticache')
    clusters = client.describe_cache_clusters()
    for i in clusters['CacheClusters']:
        if i['SecurityGroups'] != []:
            for g in i['SecurityGroups']:
                if g['Status'] == 'active':
                    if g['SecurityGroupId'] in data.keys():
                        data[g['SecurityGroupId']].append("elc:"+i['CacheClusterId'])    

def MapLambdaSecGroups(data):
    client = boto3.client('lambda')
    functions = client.list_functions()
    for i in functions['Functions']:
        if 'VpcConfig' in i.keys():
            for g in i['VpcConfig']['SecurityGroupIds']:
                data[g].append("lambda:"+i['FunctionName'])


def main():
    dataobj = {}

    # get all sec groups
    GetAllSecGroups(dataobj)

    # Populate data from all services using Sec Groups

    # EC2
    MapEc2SecGroups(dataobj)
    # EBS
    MapElasticBeanstalkSecGroups(dataobj)
    # EMR
    #TBD
    # RDS
    MapRDSSecGroups(dataobj)
    # Redshift
    #TBD
    # Elasticache
    MapElastiCacheSecGroups(dataobj)
    # CloudSearch
    #TBD
    # Elastic Load Bal
    MapElasticLoadBalSecGroups(dataobj)
    # Lambda
    MapLambdaSecGroups(dataobj)

    createGraph(dataobj)

if __name__ == '__main__':
    main()
