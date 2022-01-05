from re2py import re2post, post2nfa
import argparse


def plot(re, ofile):
    nfa = post2nfa(re2post(re))
    graph = nfa.graph()
    graph.render(ofile)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("re")
    parser.add_argument("ofile")
    args = parser.parse_args()
    re = args.re
    ofile = args.ofile
    plot(re, ofile)
