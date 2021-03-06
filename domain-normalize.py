# coding=utf-8
import pprint

from provisioning import generateTrafficClasses

from initopt import *
from generatePath import *
from predicates import nullPredicate

from topology import Topology
from traffic import TrafficMatrix


import cplex
from cplex.exceptions import CplexError
import math
import copy

from VN import *

def shortest_path():
    ispNets = []
    cpTopo = Topology('CP_network', './data/topologies/simple.graphml')
    isp_num = 2
    for i in range(isp_num):
        ispNets.append(IspNetwork('Abilene', './data/topologies/Abilene.graphml'))

    trafficMatrix = {}
    for i in range(isp_num):
        trafficMatrix[i] = ispNets[i].egress_volume([0, 1], cpTopo)

    cpNet = CpNetwork('CP_network', './data/topologies/simple.graphml')
    pptc = cpNet.calc_path_sp(trafficMatrix)
    ingress_bw_dict = {}
    for i in range(isp_num):
        ingress_bw_dict[i] = {}
    for tc, paths in pptc.iteritems():
        ingress = tc.src
        if ingress in ingress_bw_dict[tc.network_id]:
            ingress_bw_dict[tc.network_id][ingress] += tc.allocate_bw
        else:
            ingress_bw_dict[tc.network_id][ingress] = tc.allocate_bw
    for id, bw_dict in ingress_bw_dict.iteritems():
        print "isp network id:{}".format(id)
        for egress, bw in bw_dict.iteritems():
            print "egress:{} bw:{}".format(egress, bw)       
    

def sum():
    ispNets = []
    cpTopo = Topology('CP_network', './data/topologies/simple.graphml')
    isp_num = 2
    for i in range(isp_num):
        ispNets.append(IspNetwork('Abilene', './data/topologies/Abilene.graphml'))

    trafficMatrix = {}
    for i in range(isp_num):
        trafficMatrix[i] = ispNets[i].egress_all(10000, cpTopo)

    cpNet = CpNetwork('CP_network', './data/topologies/simple.graphml')
    egress_bw_dict = cpNet.calc_path_sum(10000, trafficMatrix, isp_num)
    for id, bw_dict in egress_bw_dict.iteritems():
        print "isp network id:{}".format(id)
        for egress, bw in bw_dict.iteritems():
            print "egress:{} bw:{}".format(egress, bw)

def TE():
    # ==============
    # Let's generate some example data;
    # ==============
    #net = CpNetwork('Abilene', './data/topologies/Abilene.graphml', './data/tm/Abilene.tm')
    #net.egress_sum()

    
    #sum()
    shortest_path()
    return

    # ==============
    # Optimization
    # ==============
    pptc = initOptimization(ie_path_map, topo, trafficClasses)
    maxmin_fair_allocate(trafficClasses, linkcaps, pptc, norm_list, False)

        
    print "calculating fairness index..."

    pptc_1 = initOptimization(ie_path_map_1, topo, trafficClasses_1)
    maxmin_fair_allocate(trafficClasses_1, linkcaps, pptc_1, norm_list)

    pptc_2 = initOptimization(ie_path_map_2, topo, trafficClasses_2)
    maxmin_fair_allocate(trafficClasses_2, linkcaps, pptc_2, norm_list)

    
    s_1 = 0.0
    s_2 = 0.0
    s1_num = 0
    s2_num = 0
    for tc in pptc:
        if tc in trafficClasses_1:
            for tc1 in pptc_1:
                if tc.src == tc1.src and tc.dst == tc1.dst: 
                    print 'tc:{} tc1:{}'.format(tc.allocate_bw, tc1.allocate_bw)
                    if tc1.allocate_bw == 0:
                        tc1.allocate_bw = 0.1
                    s_1 += tc.allocate_bw / tc1.allocate_bw
                    s1_num += 1
                    break
        elif tc in trafficClasses_2:
            for tc2 in pptc_2:
                if tc.src == tc2.src and tc.dst == tc2.dst:
                    if tc2.allocate_bw == 0:
                        tc2.allocate_bw = 0.1
                    s_2 += tc.allocate_bw / tc2.allocate_bw
                    s2_num += 1
                    break
    s_1 = s_1 / s1_num
    s_2 = s_2 / s2_num
    print 's1:{} s2:{}'.format(s_1, s_2)
    


    g1 = copy.deepcopy(pptc_1)
    g2 = copy.deepcopy(pptc_2)
    
    for tc1 in pptc_1:
        if tc1.calc_flag == 1:
            continue
        for path1 in pptc_1[tc1]:
            for tc2 in pptc_2:
                if tc2.calc_flag == 1:
                    continue
                for path2 in pptc_2[tc2]:
                    links1 = path1.getLinks()
                    links2 = path2.getLinks()
                    if set(links1).intersection(links2):
                        g1[copy.deepcopy(tc2)] = copy.deepcopy(pptc_2[tc2])
                        g2[copy.deepcopy(tc1)] = copy.deepcopy(pptc_1[tc1])
                        flag = 1
                        tc2.calc_flag = 1
                        tc1.calc_flag = 1

    maxmin_fair_allocate(g1.keys(), linkcaps, g1, norm_list)
    maxmin_fair_allocate(g2.keys(), linkcaps, g2, norm_list)
   
    
    u_1 = 0.0
    u_2 = 0.0
    u1_num = 0
    u2_num = 0

    for tc1 in g1:
        for tc in pptc:
                if tc.src == tc1.src and tc.dst == tc1.dst: 
                    print 'tc:{} tc1:{}'.format(tc.allocate_bw, tc1.allocate_bw)
                    u_1 += min({tc.allocate_bw / tc1.allocate_bw, 1})
                    u1_num += 1
                    break
    for tc2 in g2:
        for tc in pptc:
            if tc.src == tc2.src and tc.dst == tc2.dst:
                u_2 += min({tc.allocate_bw / tc2.allocate_bw, 1})
                u2_num += 1
                break

    u_1 = u_1 / u1_num
    u_2 = u_2 / u2_num
    print 'u1:{} u2:{}'.format(u_1, u_2)

                
    netstat_1 = s_1 / u_1
    netstat_2 = s_2 / u_2
    
    u = (netstat_1 * v1_sum + netstat_2 * v2_sum) / (v1_sum + v2_sum)
    print u
    gfi = math.sqrt((pow(netstat_1 - u, 2) * v1_sum + pow(netstat_2 - u, 2) * v2_sum) / (v1_sum + v2_sum))
    print gfi
        


if __name__ == "__main__":
    TE()
