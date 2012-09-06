#!/usr/bin/env python
"""
Read/Write XAS Data Interchange Format for Python
"""
import os
import ctypes
import ctypes.util

from math import pi, exp, log, sin, asin
try:
    import numpy as np
    from numpy import pi, exp, log, sin
    from numpy import arcsin as asin
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

RAD2DEG  = 180.0/pi
# from NIST.GOV CODATA:
# Planck constant over 2 pi times c: 197.3269718 (0.0000044) MeV fm
PLANCK_hc = 1973.269718 * 2 * pi # hc in eV * Ang = 12398.4193

__version__ = '1.0.0'

class XDIFileStruct(ctypes.Structure):
    "emulate XDI File"
    _fields_ = [('nmetadata',     ctypes.c_long),
                ('narrays',       ctypes.c_long),
                ('npts',          ctypes.c_long),
                ('narray_labels', ctypes.c_long),
                ('dspacing',      ctypes.c_double),
                ('xdi_libversion', ctypes.c_char_p),
                ('xdi_version',   ctypes.c_char_p),
                ('extra_version', ctypes.c_char_p),
                ('filename',      ctypes.c_char_p),
                ('element',       ctypes.c_char_p),
                ('edge',          ctypes.c_char_p),
                ('comments',      ctypes.c_char_p),
                ('array_labels',  ctypes.c_void_p),
                ('array_units',   ctypes.c_void_p),
                ('meta_families', ctypes.c_void_p),
                ('meta_keywords', ctypes.c_void_p),
                ('meta_values',   ctypes.c_void_p),
                ('array',         ctypes.c_void_p)]

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

    Principle data members:
      columns:  dict of column indices, with keys
                       'energy', 'i0', 'itrans', 'ifluor', 'irefer'
                       'mutrans', 'mufluor', 'murefer'
                 some of which may be None.
      column_data: dict of data for arrays -- same keys as
                 for columns.
    Principle methods:
      read():     read XDI data file, set column data and attributes
      write(filename):  write xdi_file data to an XDI file.

    """
    _invalid_msg = "invalid data for '%s':  was expecting %s, got '%s'"

    def __init__(self, filename=None):
        self.filename = filename
        self.xdi_pyversion =  __version__
        self.comments = []
        self.rawdata = []
        self.attrs = {}

        if self.filename:
            self.read(self.filename)


    def _warn(self, msg):
        "print a warning message"
        msg = '%s: %s' % (self.filename, msg)
        print msg

    def write(self, filename):
        "write out an XDI File"
        print 'Writing XDI file not currently supported'


    def read(self, filename=None):
        """read validate and parse an XDI datafile into python structures
        """
        if filename is None and self.filename is not None:
            filename = self.filename
        XDILIB = get_xdilib()
        
        pxdi = ctypes.pointer(XDIFileStruct())
        out = XDILIB.XDI_readfile(filename, pxdi)
        if out != 0:
            msg =  XDILIB.XDI_errorstring(out)
            msg = 'Error reading XDIFile %s\n%s' % (filename, msg)
            raise XDIFileException(msg)

        xdi = pxdi.contents
        for attr in dict(xdi._fields_):
            setattr(self, attr, getattr(xdi, attr))

        pchar = ctypes.c_char_p
        self.array_labels = (self.narrays*pchar).from_address(xdi.array_labels)[:]
        self.array_units  = (self.narrays*pchar).from_address(xdi.array_units)[:]

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

        parrays  = (xdi.narrays*ctypes.c_void_p).from_address(xdi.array)[:]
        arrays  = [(xdi.npts*ctypes.c_double).from_address(p)[:] for p in parrays]

        if HAS_NUMPY:
            arrays = np.array(arrays)
            arrays.shape = (self.narrays, self.npts)
        self.rawdata = arrays
        self._assign_arrays()

        for attr in ('nmetadata', 'narray_labels', 'meta_families',
                     'meta_keywords', 'meta_values', 'array'):
            delattr(self, attr)
            


    def _assign_arrays(self):
        """assign data arrays for principle data attributes:
           energy, angle, i0, itrans, ifluor, irefer,
           mutrans, mufluor, murefer, etc.
        """
        xunits = 'eV'
        xname = None
        ix = -1
        if HAS_NUMPY:
            self.rawdata = np.array(self.rawdata)

        for idx, name in enumerate(self.array_labels):
            if HAS_NUMPY:
                dat = self.rawdata[idx,:]
            else:
                dat = [d[idx] for d in self.rawdata]
            setattr(self, name, dat)
            if name in ('energy', 'angle'):
                ix = idx
                xname = name
                units = self.array_units[idx]
                if units is not None:
                    xunits = units

        if not HAS_NUMPY:
            self._warn('not calculating derived values -- install numpy!')
            return

        # convert energy to angle, or vice versa
        if ix >= 0 and 'd_spacing' in self.attrs['mono']:
            dspace = float(self.attrs['mono']['d_spacing'])
            omega = PLANCK_hc/(2*dspace)
            if xname == 'energy' and not hasattr(self, 'angle'):
                energy_ev = self.energy
                if xunits.lower() == 'kev':
                    energy_ev = 1000. * energy_ev
                self.angle = RAD2DEG * asin(omega/energy_ev)
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
    x = XDIFile('cu_metal_rt.xdi')
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
