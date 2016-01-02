"""
Module for population analysis.
Currently only Mulliken style analysis is supported.
"""

import error_handler, lib_struc
import numpy

class pop_ana:
    """
    Base class for population analysis.
    """
    def ret_Deff(self, dens, mos):
        raise error_handler.PureVirtualError()
    
    def ret_pop(self, dens, mos, Deff=None):
        if Deff==None: Deff = self.ret_Deff(dens, mos)
        
        mp = numpy.zeros(mos.num_at)
        
        for ibas in xrange(mos.ret_num_bas()):
            iat = mos.basis_fcts[ibas].at_ind - 1
            mp[iat] += Deff[ibas, ibas]
            
        return mp    

class mullpop_ana(pop_ana):
    """
    Mulliken population analysis.
    """
    def ret_Deff(self, dens, mos):
        """
        Compute and return the Mulliken population.
        """
        temp = mos.CdotD(dens, trnsp=False, inv=False)  # C.DAO
        DS   = mos.MdotC(temp, trnsp=False, inv=True) # DAO.S = C.D.C^(-1)
        
        return DS

class pop_printer:
    """
    Printer for population analysis data.
    """
    def __init__(self, struc):
        self.pop_types = []
        self.pops = []
        
        self.struc = struc
        
    ## \brief Add population data    
    # \param pop_type name to be printed
    # \param pop numpy.array with data
    def add_pop(self, pop_type, pop):
        """
        Add population data to be stored in the printer class.
        """
        if pop==None: return
        
        self.pop_types.append(pop_type)
        self.pops.append(pop)
        
    def ret_table(self):
        """
        Return a table containing all the populations of interest.
        """
        if len(self.pop_types) == 0:
            return "  ... no population analysis data available."
        
        retstr = ''
        
        hstr = '%6s'%'Atom'
        for pop_type in self.pop_types:
            hstr += '%10s'%pop_type
            
        retstr += len(hstr) * '-' + "\n"
        retstr += hstr            
        retstr += "\n" + len(hstr) * '-' + "\n"
        
        for iat in xrange(len(self.pops[0])):
            if self.struc==None:
                retstr += '%6i'%(iat+1)
            else:
                retstr += '%3s%3i'%(self.struc.ret_symbol(iat+1), iat+1)
            for pop in self.pops:
                retstr += '% 10.5f'%pop[iat]
            retstr += '\n'

        retstr += len(hstr) * '-' + "\n"
        
        retstr += '%5s'%''
        for pop in self.pops:
            retstr += '% 10.5f'%pop.sum()
        
        retstr += "\n" + len(hstr) * '-' + "\n"
        
        return retstr
    