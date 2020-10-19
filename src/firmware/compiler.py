from misc.misc import *

#Hardware configurations (that can be done by VLIW instruction)
class compiler():
    # ISA
    def begin_chain(self):
        self.fu, self.mvru, self.vsru, self.vvalu, self.dp = copy(self.pass_through)
    def vv_filter(self,addr):
        self.fu.filter=1
        self.fu.addr=addr
    def m_reduce(self,axis='N'):
        if axis=='N':
            self.mvru.axis=1
        elif axis=='M':
            self.mvru.axis=2
        else:
            assert False, "Unknown axis for instruction m_reduce"
    def v_reduce(self):
        self.vsru.op=1
    def vv_add(self,addr,condition=None):
        self.vvalu.op=1
        self.vvalu.addr=addr
        if condition=="last" or condition=="notlast" or condition=="first" or condition=="notfirst" or condition is None:
            self.vvalu.cond[condition]=True
        else:
            assert False, "Condition not understood"
    def vv_mul(self,addr,condition=None):
        self.vvalu.op=2
        self.vvalu.addr=addr
        if condition=="last" or condition=="notlast" or condition=="first" or condition=="notfirst" or condition is None:
            self.vvalu.cond[condition]=True
        else:
            assert False, "Condition not understood"
    def vv_sub(self,addr,condition=None):
        self.vvalu.op=3
        self.vvalu.addr=addr
        if condition=="last" or condition=="notlast" or condition=="first" or condition=="notfirst" or condition is None:
            self.vvalu.cond[condition]=True
        else:
            assert False, "Condition not understood"
    def v_cache(self,cache_addr):
        self.vvalu.cache=1
        self.vvalu.cache_addr=cache_addr
    def v_commit(self,size=None,condition=None):
        if size is None:
            size = self.N
        self.dp.commit=1
        if size==self.N or size==self.M or size==1:
            self.dp.size=size
        else:
            assert False, "Cannot commit "+str(size)+" elements"
        if condition=="last" or condition=="notlast" or condition=="first" or condition=="notfirst" or condition is None:
            self.dp.cond[condition]=True
        else:
            assert False, "Condition not understood"
    def end_chain(self):
        self.firmware.append(copy([self.fu,self.mvru,self.vsru,self.vvalu,self.dp]))
    def compile(self):
        return self.firmware

    def __init__(self,N,M,MAX_CHAINS):
        self.N = N
        self.M = M
        self.firmware = []
        no_cond={'last':False,'notlast':False,'first':False,'notfirst':False}
        self.pass_through = [struct(filter=0,addr=0),struct(axis=0),struct(op=0),struct(op=0,addr=0,cond=copy(no_cond),cache=0,cache_addr=0),struct(commit=0,size=0,cond=copy(no_cond))]
        self.fu, self.mvru, self.vsru, self.vvalu, self.dp = self.pass_through[:]
