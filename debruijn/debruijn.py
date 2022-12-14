#!/bin/env python3
# -*- coding: utf-8 -*-
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    A copy of the GNU General Public License is available at
#    http://www.gnu.org/licenses/gpl-3.0.html

"""Perform assembly based on debruijn graph."""

import argparse
import os
import sys
import networkx as nx
import matplotlib
from operator import itemgetter
import random
random.seed(9001)
from random import randint
import statistics
import matplotlib.pyplot as plt
matplotlib.use("Agg")
import textwrap

__author__ = "Crystal Renaud"
__copyright__ = "Universite Paris Diderot"
__credits__ = ["Crystal Renaud"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "Cerystal Renaud"
__email__ = "crystal.renaud@orange.fr"
__status__ = "Developpement"

def isfile(path):
    """Check if path is an existing file.
      :Parameters:
          path: Path to the file
    """
    if not os.path.isfile(path):
        if os.path.isdir(path):
            msg = "{0} is a directory".format(path)
        else:
            msg = "{0} does not exist.".format(path)
        raise argparse.ArgumentTypeError(msg)
    return path


def get_arguments():
    """Retrieves the arguments of the program.
      Returns: An object that contains the arguments
    """
    # Parsing arguments
    parser = argparse.ArgumentParser(description=__doc__, usage=
                                     "{0} -h"
                                     .format(sys.argv[0]))
    parser.add_argument('-i', dest='fastq_file', type=isfile,
                        required=True, help="Fastq file")
    parser.add_argument('-k', dest='kmer_size', type=int,
                        default=22, help="k-mer size (default 22)")
    parser.add_argument('-o', dest='output_file', type=str,
                        default=os.curdir + os.sep + "contigs.fasta",
                        help="Output contigs in fasta file")
    parser.add_argument('-f', dest='graphimg_file', type=str,
                        help="Save graph as image (png)")
    return parser.parse_args()


def read_fastq(fastq_file):
    with open(fastq_file, 'r') as filling:
        for file in filling: 
            yield next(filling).strip() #strip pour enlever 
            next(filling)
            next(filling)


def cut_kmer(read, kmer_size):
    for i in range(len(read)):
        if (i + kmer_size) <= len(read) :
            yield read[i : (i + kmer_size)]


def build_kmer_dict(fastq_file, kmer_size):
    dico = {}
    for i in read_fastq(fastq_file): 
        for kmer in cut_kmer(i, kmer_size):
            if kmer in dico: 
                dico[kmer] = dico[kmer] + 1
            else: 
                dico[kmer] = dico.get(kmer, 1)
    return dico            


def build_graph(kmer_dict):
    graph = nx.DiGraph()
    for kmer in kmer_dict:
        graph.add_edge(kmer[0 : -1], kmer[1: ], weight = kmer_dict[kmer])
    return graph


def remove_paths(graph, path_list, delete_entry_node, delete_sink_node):
    for path in path_list:
        if not delete_entry_node :
            path = path[1:]
        if not delete_sink_node :
            path = path[:-1]
        graph.remove_nodes_from(path)
    return graph


def std(data):
    std = statistics.stdev(data)
    return std


def select_best_path(graph, path_list, path_length, weight_avg_list, 
                     delete_entry_node=False, delete_sink_node=False):

    if std(weight_avg_list) > 0:
        del path_list[weight_avg_list.index(max(weight_avg_list))]
    elif std(path_length) > 0:
        del path_list[path_length.index(max(path_length))]
    else :
        del path_list[randint(0, len(path_list))]
    
    graph = remove_paths(graph, path_list, delete_entry_node, delete_sink_node)
    return graph


def path_average_weight(graph, path):
    mean_weight = statistics.mean([d["weight"] for (u, v, d) in graph.subgraph(path).edges(data=True)])
    return mean_weight

def solve_bubble(graph, ancestor_node, descendant_node):
    paths = list(nx.all_simple_paths(graph, ancestor_node, descendant_node))
    weight_avg_list = [path_average_weight(graph, i) for i in paths]
    path_length = [len(i) for i in paths]
    return select_best_path(graph, paths, path_length, weight_avg_list)

def simplify_bubbles(graph):
    bubble = False 
    for node in graph:
        list_preds = list(graph.predecessors(node))
        if len(list_preds) > 1:
            for i,first_pred in enumerate(list_preds):
                list_second_preds = list_preds[:i]+list_preds[i+1:]
                for second_pred in list_second_preds:
                    ancestor_node = nx.lowest_common_ancestor(graph, first_pred, second_pred)
                    if ancestor_node:
                        bubble = True
                        break
        if bubble == True:
            break
    if bubble:
        graph = simplify_bubbles(solve_bubble(graph,ancestor_node, node))

    return graph

def solve_entry_tips(graph, starting_nodes):
    pass

def solve_out_tips(graph, ending_nodes):
    pass

def get_starting_nodes(graph):
    node = []
    for i in graph.nodes():
        if not list(graph.predecessors(i)): #si il n'y a pas de pr??d??cesseur ??a va dans la liste
            node.append(i)
    return node


def get_sink_nodes(graph):
    node_s = []
    for i in graph.nodes():
        if not list(graph.successors(i)): #si il n'y a pas de successeur ??a va dans la liste
            node_s.append(i)
    return node_s

def get_contigs(graph, starting_nodes, ending_nodes):
    contigs_list  = []
    for start in starting_nodes :
        for end in ending_nodes: 
            for path in nx.all_simple_paths(graph, start, end):
                cont = path[0]
                for node in path[1:]:
                    cont = cont + node [-1]
                contig_size = len(cont)
                contigs_list.append((cont, contig_size))
    
    return contigs_list
                


def save_contigs(contigs_list, output_file):
    with open(output_file, "w") as file:
        for i in range(len(contigs_list)):
            file.write(">contig_" + str(i) + " len=" + str(contigs_list[i][1]) +
             "\n" + textwrap.fill((contigs_list[i][0]), width=80) + "\n")
       

def fill(text, width=80):
    """Split text with a line return to respect fasta format"""
    return os.linesep.join(text[i:i+width] for i in range(0, len(text), width))

def draw_graph(graph, graphimg_file):
    """Draw the graph
    """                                    
    fig, ax = plt.subplots()
    elarge = [(u, v) for (u, v, d) in graph.edges(data=True) if d['weight'] > 3]
    #print(elarge)
    esmall = [(u, v) for (u, v, d) in graph.edges(data=True) if d['weight'] <= 3]
    #print(elarge)
    # Draw the graph with networkx
    #pos=nx.spring_layout(graph)
    pos = nx.random_layout(graph)
    nx.draw_networkx_nodes(graph, pos, node_size=6)
    nx.draw_networkx_edges(graph, pos, edgelist=elarge, width=6)
    nx.draw_networkx_edges(graph, pos, edgelist=esmall, width=6, alpha=0.5, 
                           edge_color='b', style='dashed')
    #nx.draw_networkx(graph, pos, node_size=10, with_labels=False)
    # save image
    plt.savefig(graphimg_file)


def save_graph(graph, graph_file):
    """Save the graph with pickle
    """
    with open(graph_file, "wt") as save:
            pickle.dump(graph, save)


#==============================================================
# Main program
#==============================================================
def main():
    """
    Main program function
    """
    # Get arguments
    args = get_arguments()

    # Fonctions de dessin du graphe
    # A decommenter si vous souhaitez visualiser un petit 
    # graphe
    # Plot the graph
    # if args.graphimg_file:
    #     draw_graph(graph, args.graphimg_file)
    # Save the graph in file
    # if args.graph_file:
    #     save_graph(graph, args.graph_file)


if __name__ == '__main__':
    main()
