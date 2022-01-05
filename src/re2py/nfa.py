from collections import namedtuple
from typing import List, Tuple
from enum import Enum
from graphviz import Digraph


def re2post(re: str) -> str:
    post = ""

    nalt = 0
    natom = 0
    Paren = namedtuple("Paren", ["nalt", "natom"])
    paren = list()

    for c in re:
        if c == "(":
            if natom > 1:
                natom -= 1
                post += "."
            p = Paren(nalt, natom)
            paren.append(p)
            nalt = 0
            natom = 0
        elif c == "|":
            if natom == 0:
                raise RuntimeError("no atom before alt '|'")
            while True:
                natom -= 1
                if natom == 0:
                    break
                post += "."
            nalt += 1
        elif c == ")":
            if len(paren) == 0:
                raise RuntimeError("no open parenthesis")
            if natom == 0:
                raise RuntimeError("no atom in parenthesis")
            while True:
                natom -= 1
                if natom == 0:
                    break
                post += "."
            while True:
                if nalt == 0:
                    break
                post += "|"
                nalt -= 1
            p = paren.pop()
            nalt = p.nalt
            natom = p.natom
            natom += 1
        elif c == "*" or c == "+" or c == "?":
            if natom == 0:
                raise RuntimeError(f"no atom before 'c'")
            post += c
        else:
            if natom > 1:
                natom -= 1
                post += "."
            post += c
            natom += 1

    if len(paren) > 0:
        raise RuntimeError("unclosed parenthesis")
    while True:
        natom -= 1
        if natom == 0:
            break
        post += "."
    while True:
        if nalt == 0:
            break
        post += "|"
        nalt -= 1

    return post


class StateType(Enum):
    OUT = 0
    SPLIT = 1
    MATCH = 2


class State:
    def __init__(self, type: StateType, id: int):
        self.type: StateType = type
        self.id: int = id
        self.lastlist: int = -1

    def __str__(self):
        if self.is_out():
            return f"OUT(ID: {self.id}, CHAR: {self.char}, NEXT: {self.out.id})"
        elif self.is_split():
            return f"SPLIT(ID: {self.id}, NEXT0: {self.out.id}, NEXT1: {self.out1.id})"
        else:
            return "MATCH"

    def is_out(self) -> bool:
        return self.type == StateType.OUT

    def is_split(self) -> bool:
        return self.type == StateType.SPLIT

    def is_match(self) -> bool:
        return self.type == StateType.MATCH

    def __name(self):
        if self.is_out():
            return f"{self.id}_{self.char}"
        elif self.is_split():
            return f"{self.id}_{self.char}"
        else:
            return f"{self.id}_match"

    def graph(self):
        stack = [self]
        pushed = set()
        graph = Digraph(format="png")
        while len(stack) > 0:
            e = stack.pop()
            if e.id in pushed:
                continue

            pushed.add(e.id)
            graph.node(f"{e.__name()}")
            if e.is_out():
                e0 = e.out
                graph.edge(f"{e.__name()}", f"{e0.__name()}")
                stack.append(e0)
            elif e.is_split():
                e0 = e.out
                graph.edge(f"{e.__name()}", f"{e0.__name()}")
                stack.append(e0)
                e1 = e.out1
                graph.edge(f"{e.__name()}", f"{e1.__name()}")
                stack.append(e1)

        return graph


class Ptrlist:
    def __init__(self, s: State, v: int):
        self.next: Ptrlist = None
        self.s: State = s
        self.v: int = v


class Frag:
    def __init__(self, s: State, ptrl: Ptrlist):
        self.start: State = s
        self.out: Ptrlist = ptrl


def patch(ptrl: Ptrlist, s: State):
    while True:
        if ptrl.v == 0:
            ptrl.s.out = s
        else:
            ptrl.s.out1 = s

        if ptrl.next is not None:
            ptrl = ptrl.next
        else:
            break


def append(ptrl1: Ptrlist, ptrl2: Ptrlist) -> Ptrlist:
    old = ptrl1
    while True:
        if ptrl1.next is not None:
            ptrl1 = ptrl1.next
        else:
            ptrl1.next = ptrl2
            break
    return old


def post2nfa(post: str):
    stack: List[Frag] = list()
    nstate = 0
    for c in post:
        if c == ".":
            e2 = stack.pop()
            e1 = stack.pop()
            patch(e1.out, e2.start)
            stack.append(Frag(e1.start, e2.out))
        elif c == "|":
            e2 = stack.pop()
            e1 = stack.pop()
            s = State(StateType.SPLIT, nstate)
            nstate += 1
            s.char = "|"
            s.out = e1.start
            s.out1 = e2.start
            stack.append(Frag(s, append(e1.out, e2.out)))
        elif c == "?":
            e = stack.pop()
            s = State(StateType.SPLIT, nstate)
            nstate += 1
            s.char = "?"
            s.out = e.start
            s.out1 = None
            stack.append(Frag(s, append(e.out, Ptrlist(s, 1))))
        elif c == "*":
            e = stack.pop()
            s = State(StateType.SPLIT, nstate)
            nstate += 1
            s.char = "*"
            s.out = e.start
            s.out1 = None
            patch(e.out, s)
            stack.append(Frag(s, Ptrlist(s, 1)))
        elif c == "+":
            e = stack.pop()
            s = State(StateType.SPLIT, nstate)
            nstate += 1
            s.char = "+"
            s.out = e.start
            s.out1 = None
            patch(e.out, s)
            stack.append(Frag(e.start, Ptrlist(s, 1)))
        else:
            s = State(StateType.OUT, nstate)
            nstate += 1
            s.char = c
            s.out = None
            stack.append(Frag(s, Ptrlist(s, 0)))
    e = stack.pop()
    assert len(stack) == 0
    match = State(StateType.MATCH, nstate)
    patch(e.out, match)
    return e.start


class SList:
    def __init__(self):
        self.s = []
        self.id = 0


def addstate(l: SList, s: State):
    if s.lastlist == l.id:
        return

    s.lastlist = l.id

    if s.is_split():
        # follow unlabeled arrows
        addstate(l, s.out)
        addstate(l, s.out1)
        return

    l.s.append(s)


def step(clist: SList, c: str):
    id = clist.id

    nlist = SList()
    nlist.id = id + 1

    for s in clist.s:
        if s.is_out() and s.char == c:
            addstate(nlist, s.out)

    return nlist


def ismatch(l: SList):
    for s in l.s:
        if s.is_match():
            return True
    return False


def match(start: State, s: str) -> Tuple[bool, List[List[int]]]:
    i = 0
    c = 0
    clist = SList()
    # SListが格納するStateは基本StateType.OUTなもののみ
    # しかし、startはStateType.Splitの可能性があるため、addstate()でこれをケアする
    addstate(clist, start)
    match_history = list()
    for c in s:
        clist = step(clist, c)
        match_history.append([s.id for s in clist.s])
    return ismatch(clist), match_history
