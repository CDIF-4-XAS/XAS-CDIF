#!/usr/bin/env python
"""
Read/Write XAS Data Interchange Format for Python
"""
import os
import ctypes
import ctypes.util

__version__ = '1.2.0'

from numpy import array, exp, log, sin, arcsin

PI = 3.14159265358979323846
RAD2DEG  = 180.0/PI

# from NIST.GOV CODATA:
# Planck constant over 2 pi times c: 197.3269718 (0.0000044) MeV fm
PLANCK_HC = 1973.269718 * 2 * PI # hc in eV * Ang = 12398.4193

class XDIFileStruct(ctypes.Structure):
    "emulate XDI File"
    _fields_ = [('nmetadata',     ctypes.c_long),
                ('narrays',       ctypes.c_long),
                ('npts',          ctypes.c_long),
                ('narray_labels', ctypes.c_long),
                ('nouter',         ctypes.c_long),
                ('error_lineno',  ctypes.c_long),
                ('dspacing',      ctypes.c_double),
                ('xdi_libversion',ctypes.c_char_p),
                ('xdi_version',   ctypes.c_char_p),
                ('extra_version', ctypes.c_char_p),
                ('filename',      ctypes.c_char_p),
                ('element',       ctypes.c_char_p),
                ('edge',          ctypes.c_char_p),
                ('comments',      ctypes.c_char_p),
                ('error_line',    ctypes.c_char_p),
                ('error_message', ctypes.c_char_p),
                ('array_labels',  ctypes.c_void_p),
                ('outer_label',   ctypes.c_char_p),
                ('array_units',   ctypes.c_void_p),
                ('meta_families', ctypes.c_void_p),
                ('meta_keywords', ctypes.c_void_p),
                ('meta_values',   ctypes.c_void_p),
                ('array',         ctypes.c_void_p),
                ('outer_array',   ctypes.c_void_p),
                ('outer_breakpts', ctypes.c_void_p)]

def add_dot2path():
    """add this folder to begninng of PATH environmental variable"""
    sep = ':'
    if os.name == 'nt': sep = ';'
    paths = os.environ.get('PATH','').split(sep)
    paths.insert(0, os.path.abspath(os.curdir))
    os.environ['PATH'] = sep.join(paths)


XDILIB = None
def get_xdilib():
    """make initial connection to XDI dll"""
    global XDILIB
    if XDILIB is None:
        dllpath  = ctypes.util.find_library('xdifile')
        load_dll = ctypes.cdll.LoadLibrary
        if os.name == 'nt':
            load_dll = ctypes.windll.LoadLibrary
        XDILIB = load_dll(dllpath)
        XDILIB.XDI_errorstring.restype   = ctypes.c_char_p
    return XDILIB


class XDIFileException(Exception):
    """XDI File Exception: General Errors"""
    def __init__(self, msg, **kws):
        Exception.__init__(self)
        self.msg = msg
    def __str__(self):
        return self.msg

class XDIFile(object):
    """ XAS Data Interchange Format:

    See https://github.com/XraySpectrscopy/XAS-Data-Interchange

    for further details

    >>> xdi_file = XDFIile(filename)

    Principle methods:
      read():     read XDI data file, set column data and attributes
      write(filename):  write xdi_file data to an XDI file.
    """
    _invalid_msg = "invalid data for '%s':  was expecting %s, got '%s'"

    def __init__(self, filename=None):
        self.filename = filename
        self.xdi_pyversion =  __version__
        self.xdilib = get_xdilib()
        self.comments = []
        self.rawdata = []
        self.attrs = {}
        self.status = None
        if self.filename:
            self.read(self.filename)

    def write(self, filename):
        "write out an XDI File"
        print( 'Writing XDI file not currently supported')

    def read(self, filename=None):
        """read validate and parse an XDI datafile into python structures
        """
        if filename is None and self.filename is not None:
            filename = self.filename
        pxdi = ctypes.pointer(XDIFileStruct())
        self.status = out = self.xdilib.XDI_readfile(filename, pxdi)
        if out < 0:
            msg =  self.xdilib.XDI_errorstring(out)
            self.xdilib.XDI_cleanup(pxdi, out)
            msg = 'Error reading XDIFile %s\n%s' % (filename, msg)
            raise XDIFileException(msg)

        xdi = pxdi.contents
        for attr in dict(xdi._fields_):
            setattr(self, attr, getattr(xdi, attr))
        pchar = ctypes.c_char_p
        self.array_labels = (self.narrays*pchar).from_address(xdi.array_labels)[:]
        arr_units  = (self.narrays*pchar).from_address(xdi.array_units)[:]
        self.array_units = []
        self.array_addrs = []
        for unit in arr_units:
            addr = ''
            if '||' in unit:
                unit, addr = [x.strip() for x in unit.split('||', 1)]
            self.array_units.append(unit)
            self.array_addrs.append(addr)

        mfams = (self.nmetadata*pchar).from_address(xdi.meta_families)[:]
        mkeys = (self.nmetadata*pchar).from_address(xdi.meta_keywords)[:]
        mvals = (self.nmetadata*pchar).from_address(xdi.meta_values)[:]
        self.attrs = {}
        for fam, key, val in zip(mfams, mkeys, mvals):
            fam = fam.lower()
            key = key.lower()
            if fam not in self.attrs:
                self.attrs[fam] = {}
            self.attrs[fam][key] = val

        parrays = (xdi.narrays*ctypes.c_void_p).from_address(xdi.array)[:]
        rawdata = [(xdi.npts*ctypes.c_double).from_address(p)[:] for p in parrays]

        nout = xdi.nouter
        outer, breaks = [], []
        if nout > 1:
            outer  = (nout*ctypes.c_double).from_address(xdi.outer_array)[:]
            breaks = (nout*ctypes.c_long).from_address(xdi.outer_breakpts)[:]
        for attr in ('outer_array', 'outer_breakpts', 'nouter'):
            delattr(self, attr)
        self.outer_array    = array(outer)
        self.outer_breakpts = array(breaks)


        rawdata = array(rawdata)
        rawdata.shape = (self.narrays, self.npts)
        self.rawdata = rawdata
        self._assign_arrays()
        for attr in ('nmetadata', 'narray_labels', 'meta_families',
                     'meta_keywords', 'meta_values', 'array'):
            delattr(self, attr)
        self.xdilib.XDI_cleanup(pxdi, 0)

    def _assign_arrays(self):
        """assign data arrays for principle data attributes:
           energy, angle, i0, itrans, ifluor, irefer,
           mutrans, mufluor, murefer, etc.  """

        xunits = 'eV'
        xname = None
        ix = -1
        self.rawdata = array(self.rawdata)

        for idx, name in enumerate(self.array_labels):
            dat = self.rawdata[idx,:]
            setattr(self, name, dat)
            if name in ('energy', 'angle'):
                ix = idx
                xname = name
                units = self.array_units[idx]
                if units is not None:
                    xunits = units

        # convert energy to angle, or vice versa
        monodat = {}
        if 'mono' in  self.attrs:
            monodat = self.attrs['mono']
        elif 'monochromator' in  self.attrs:
            monodat = self.attrs['monochromator']

        if ix >= 0 and 'd_spacing' in monodat:
            dspace = float(monodat['d_spacing'])
            if dspace < 0: dspace = 0.001
            omega = PLANCK_HC/(2*dspace)
            if xname == 'energy' and not hasattr(self, 'angle'):
                energy_ev = self.energy
                if xunits.lower() == 'kev':
                    energy_ev = 1000. * energy_ev
                self.angle = RAD2DEG * arcsin(omega/energy_ev)
            elif xname == 'angle' and not hasattr(self, 'energy'):
                angle_rad = self.angle
                if xunits.lower() in ('deg', 'degrees'):
                    angle_rad = angle_rad / RAD2DEG
                self.energy = omega/sin(angle_rad)

        if hasattr(self, 'i0'):
            if hasattr(self, 'itrans') and not hasattr(self, 'mutrans'):
                self.mutrans = -log(self.itrans / (self.i0+1.e-12))
            elif hasattr(self, 'mutrans') and not hasattr(self, 'itrans'):
                self.itrans  =  self.i0 * exp(-self.mutrans)
            if hasattr(self, 'ifluor') and not hasattr(self, 'mufluor'):
                self.mufluor = self.ifluor/(self.i0+1.e-12)

            elif hasattr(self, 'mufluor') and not hasattr(self, 'ifluor'):
                self.ifluor =  self.i0 * self.mufluor

        if hasattr(self, 'itrans'):
            if hasattr(self, 'irefer') and not hasattr(self, 'murefer'):
                self.murefer = -log(self.irefer / (self.itrans+1.e-12))

            elif hasattr(self, 'murefer') and not hasattr(self, 'irefer'):
                self.irefer = self.itrans * exp(-self.murefer)

if __name__ == '__main__':
    x = XDIFile(os.path.join('..', '..', 'data', 'cu_metal_rt.xdi'))

    print 'Library Version, File Version ', x.xdi_libversion, x.xdi_version

    for fam in x.attrs:
        print '==%s==' % (fam.title())
        for key in x.attrs[fam]:
            print '    %s = %s ' % (key, x.attrs[fam][key])

    print 'Comments = ',  x.comments
    print 'Energy: ', x.energy[:5]
    try:
        print 'Angle: ', x.angle[:5]
    except AttributeError:
        print 'no angle calculated!'
    print dir(x)
