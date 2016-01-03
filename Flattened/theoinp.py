#!/usr/bin/python
"""
Input generation for TheoDORE runs.
"""

import theo_header, input_options, lib_struc
import os

class write_options_theo(input_options.write_options):
    """
    Input generation with suitable defaults.
    """
    # TODO: this could optionally take information from an existing dens_ana.in file
    
    def choose_rtype(self):
        rdef = ''
        if os.path.exists('qchem.out'):
            rdef = 'qcadc'
        elif os.path.exists('geom'):
            rdef = 'colmrci'
        elif os.path.exists('molcas.rasscf.molden'):
            rdef = 'rassi'
        elif os.path.exists('coord'):
            if os.path.exists('auxbasis'):
                rdef = 'ricc2'
            else:
                rdef = 'escf'
        
        self.choose_list(
            'Type of job',
            'rtype',
        [
            ('qcadc', 'Q-Chem ADC (libwfa output)'),
            ('libwfa', 'General libwfa output'),
            ('qctddft', 'Q-Chem TDDFT'),
            ('colmcscf', 'Columbus MCSCF'),
            ('colmrci', 'Columbus MR-CI (tden analysis)'),
            ('rassi', 'Molcas RASSI'),
            ('nos', 'Read natural orbitals (Molden format) for sden analysis: Columbus, Molcas, ...'),
            ('ricc2', 'Turbomole ricc2'),
            ('escf', 'Turbomole escf'),
            ('cclib', 'Use external cclib library: Gaussian, ORCA, GAMESS, ...')
        ], rdef)
        
        # set defaults
        #   None means that the option is not applicable
        #   '' means that no default is given
        
        self['read_libwfa'] = False                
        # optionally this could be read from dens_ana.in
        if self['rtype'] == 'qcadc':
            self['rfile'] = 'qchem.out'
            self['mo_file'] = None
            self['coor_file'] = 'qchem.out'
            self['coor_format'] = 'qcout'
            self['read_libwfa'] = True
        elif self['rtype'] == 'libwfa':
            self['rfile'] = None
            self['mo_file'] = None
            self['coor_file'] = 'qchem.out'
            self['coor_format'] = 'qcout'
        elif self['rtype'] == 'qctddft':
            self['rfile'] = 'qchem.out'
            self['mo_file'] = 'qchem.mld'
            self['coor_file'] = 'qchem.out'
            self['coor_format'] = 'qcout'
        elif self['rtype'] == 'colmrci' or self['rtype'] == 'colmcscf':
            self['rfile'] = None
            self['mo_file'] = 'MOLDEN/molden_mo_mc.sp'
            self['coor_file'] = 'geom'
            self['coor_format'] = 'col'
        elif self['rtype'] == 'rassi':
            self['rfile'] = 'molcas.log'
            self['mo_file'] = 'molcas.rasscf.molden'
            self['coor_file'] = 'geom.xyz'
            self['coor_format'] = 'xyz'
        elif self['rtype'] == 'nos':
            self['rfile'] = None
            self['mo_file'] = ''
            self['coor_file'] = 'geom'
            self['coor_format'] = 'col'
        elif self['rtype'] == 'ricc2':
            self['rfile'] = 'ricc2.out'
            self['mo_file'] = 'molden.input'
            self['coor_file'] = 'coord'
            self['coor_format'] = 'tmol'
        elif self['rtype'] == 'escf':
            self['rfile'] = 'escf.out'
            self['mo_file'] = 'molden.input'
            self['coor_file'] = 'coord'
            self['coor_format'] = 'tmol'
        elif self['rtype'] == 'cclib':
            self['rfile'] = ''
            self['mo_file'] = None
            self['coor_file'] = ''
            self['coor_format'] = ''
        else:
            self['rfile'] = ''
            self['mo_file'] = ''
            self['coor_file'] = ''
            self['coor_format'] = ''
            
    def set_read_options(self):
        if 'rfile' in self:
           self.read_str('Main file to read', 'rfile', self['rfile'])
        
        # switch for libwfa
        if self['rtype'] in ['qctddft']:
            if self.read_yn('Did you run "state_analysis=True"?', 'read_libwfa', False):
                self['mo_file'] = None
                
        # switch for TDA
        if self['rtype'] in ['qctddft']:
            self.read_yn('Read TDA rather than full TDDFT results?', 'TDA', False)
        
    def choose_mo_file(self):
        if 'mo_file' not in self: return
        
        mo_str = 'MO file (Molden format)\
                      \n -> This file should ideally contain a square invertible coefficient matrix'
        self.read_str(mo_str, 'mo_file', self['mo_file'])
        
        if self['rtype'] == 'ricc2':
            print()
            print(" *** Warning: in the case of ricc2 you have to delete the line")
            print("       implicit core=   x virt=    x")
            print("     from the control file before running tm2molden.")
        
        if self['rtype'] == 'nos':
            nodir = self.ret_str('Directory with the NO files:', '.')
            print("%s contains the following files:"%nodir)
            
            lfiles = sorted(os.listdir(nodir))
            self.print_list(lfiles)
            rstr = self.ret_str('Input indices of required files (separated by spaces)\n Start with ground state.')
            noinds = [int(ino)-1 for ino in rstr.replace(',',' ').split()]

            nolist = [os.path.join(nodir,lfiles[noind]) for noind in noinds]
            self.write_option('ana_files', nolist)
            
    
    def make_at_lists(self):
        print("Fragment definition for CT nubmer analysis")
        aexpl = ['Manual input', 'Automatic generation from coordinate file (using python-openbabel)', \
                 'Leave empty and fill out later']
        ichoice = self.ret_choose_list('Mode for specifying molecular fragments (at_lists):', aexpl)
        
        if ichoice==1:
            self['at_lists'] = self.read_at_lists()
        elif ichoice==2:
            self['at_lists'] = self.file_at_lists()
        elif ichoice==3:
            self['at_lists'] = [[]]
            self.ostr += 'at_lists=\n'
            return
        
        self.check_at_lists(self['at_lists'], 2)
        
        self.ostr += 'at_lists=%s\n'%str(self['at_lists'])
            
    def read_at_lists(self):
        atl_tmp = []
        
        for ifrag in range(1, 1000):
            rstr = self.ret_str('Input the indices of the atoms belonging to fragment %i:\n(separated by spaces)'%ifrag)
            if rstr == '': break
            
            atl_tmp.append([int(iat) for iat in rstr.replace(',', ' ').split()])            
            
        return atl_tmp
            
    def file_at_lists(self):
        print("Automatic generation of at_lists partitioning ...")
        self.coor_file()
        
        struc = lib_struc.structure()
        struc.read_file(file_path=self['coor_file'], file_type=self['coor_format'])
    
        return struc.ret_partition()                
    
    def coor_file(self):
        self.read_str('Coordinate file', 'coor_file', self['coor_file'])
        self.read_str('Format of coordinate file', 'coor_format', self['coor_format'])
        
    def set_Om_desc(self):
        """
        Set the list of Omega descriptors to be computed.
        """
        Olist = ['Standard set', 'Transition metal complex', 'None']
        
        ichoice = self.ret_choose_list('Omega descriptors to be computed:', Olist, 1)
        
        if ichoice==1:
            self['prop_list'] += ['Om', 'POS', 'PR', 'CT', 'COH', 'CTnt']
        elif ichoice==2:
            self['prop_list'] += ['Om', 'POSi','POSf','PR','CT','MC','LC','MLCT','LMCT','LLCT']                    
            
    def write_prop_list(self):
        if len(self['prop_list']) == 0: return
        
        self.write_option('prop_list', self['prop_list'])
        
    def nto_ana(self):
        if self['read_libwfa']: return
        
        if self.ret_yn('Perform natural transition orbital (NTO) analysis?', True):
            self.ostr += 'comp_ntos=True\n'
            self['prop_list'] += ['PRNTO']
            self.read_yn('NTOs as Jmol script?', 'jmol_orbitals', True)
            self.read_yn('NTOs in Molden format', 'molden_orbitals', False)
            if self['molden_orbitals']:
                self.read_yn('Use alpha/beta rather then negative/positive to code for hole/particle orbitals?', 'alphabeta', False)
        else:
            self.ostr += 'comp_ntos=False\n'
            
    def exciton_ana(self):
        if self.ret_yn('Compute approximate exciton size?', True):
            self['prop_list'] += ['RMSeh']
            print("\nMolecular coordinates for exciton analysis:")
            self.coor_file()
            
        if self['rtype'] in ('qcadc','qctddft'):
            if self.ret_yn('Parse exciton information from libwfa analysis?', True):
                self['prop_list'] += ['dexc', 'dH-E', 'sigH', 'sigE', 'COV', 'Corr']
            if self.ret_yn('Parse 1DDM exciton information from libwfa analysis?', True):
                self['prop_list'] += ['sigD', 'sigA']

    def AD_ana(self):
        self.read_yn('Attachment/detachment analysis', 'AD_ana', True)
        if self['AD_ana']:
            self['prop_list'] += ['p']
            self.read_yn('NDOs as Jmol script?', 'jmol_orbitals', True)
            self.read_yn('NDOs in Molden format?', 'molden_orbitals', False)
            if self['molden_orbitals']:
                self.read_yn('Use alpha/beta rather then negative/positive to code for det./att. orbitals?', 'alphabeta', False)
        else:
            self.write_option('jmol_orbitals', 'False')
            
    def BO_ana(self):
        self.read_yn('Mayer bond order and valence analysis?', 'BO_ana', True)
            
    def ddm_parse(self):
        if self['rtype'] == 'qcadc':
            if self.ret_yn('Parse 1DDM exciton information from ADCMAN job?', True):
                self['prop_list'] += ['dD-A', 'sigD', 'sigA']
                
    def get_ncore(self):
        if self.ret_yn('Were there frozen core orbitals in the calculation?', True):
            self['ncore_dict'] = {}
            print("Please enter the irrep label and number of orbitals (separated by spaces), e.g. b1u 5")
            for iirrep in range(1, 32):
                rstr = self.ret_str('Info for irrep %i'%iirrep)
                if rstr == '': break
                
                words = rstr.split()
                
                self['ncore_dict'][words[0]] = int(words[1])
                
            self.ostr += 'ncore=%s\n'%str(self['ncore_dict'])
            
    def output_options(self):
        if self.ret_yn('Adjust detailed output options?', False):
            self.read_str('Name of the output file', 'output_file', 'summ.txt')
            op = self.ret_str('Output precision, enter as: (<digits>, <dec. digits>)', '(7,3)')
            self.write_option('output_prec', eval(op))
            self.read_str('Format for molden coefficients', 'mcfmt', '% 10E')
            
    def get_rassi_list(self):
        print("""
It is assumed that you ran a RASSI job using the TRD1 option
    and copied the TRD2* files to a directory.
Please specify this directory and choose, which files will be analyzed,
    e.g. only transitions to the ground state.
        """)
        ddir = self.ret_str('Directory with the TRD2 files:', 'TRD')
        print("%s contains the following files:"%ddir)
        
        lfiles = sorted(os.listdir(ddir))
        self.print_list(lfiles)
        rstr = self.ret_str('Input indices of required files (separated by spaces)\n')
        dinds = [int(ino)-1 for ino in rstr.replace(',',' ').split()]

        dlist = [os.path.join(ddir,lfiles[dind]) for dind in dinds]
        self.write_option('ana_files', dlist)
            
def run_theoinp():
    wopt = write_options_theo('dens_ana.in')

    wopt.choose_rtype()
    wopt.set_read_options()
    wopt.choose_mo_file()
    
    wopt['prop_list'] = []
    
    if wopt['rtype'] in ['nos']:
        dotden = False
    else:
        dotden = wopt.ret_yn('Analysis of transition density matrices?', True)
        if dotden:
            if wopt.ret_yn('Perform CT number analysis?', True):
                wopt.make_at_lists()
                wopt.set_Om_desc()
                
            wopt.nto_ana()            
                
            if wopt.ret_yn('Perform exciton analysis?', True):
                wopt.exciton_ana()
                
    if (not dotden) and (wopt['rtype'] in ['nos', 'colmcscf', 'rassi']):
        if wopt.ret_yn('Analysis of state density matrices?', True):
            wopt.read_yn('Print out Mulliken populations?', 'pop_ana', True)
            if wopt['rtype'] in ['nos']:
                if wopt.read_yn('Compute number of unpaired electrons?', 'unpaired_ana', True):
                    wopt['prop_list'] += ['nu', 'nunl']
            wopt.AD_ana()
            wopt.BO_ana()
            wopt.ddm_parse()
            
    wopt.write_prop_list()
    
    # Program specific input
    if wopt['rtype'] in ['colmrci']:
        wopt.get_ncore()
    elif wopt['rtype'] in ['rassi']:
        wopt.get_rassi_list()
    
    wopt.output_options()
    
    wopt.flush(lvprt=1, choose_file=True)
    
    if wopt['rtype'] == 'colmcscf':
        print("\nNow, please run write_den.bash to prepare the MCSCF density matrices!")
    
if __name__ == '__main__':
    theo_header.print_header('Input generation')

    run_theoinp()
