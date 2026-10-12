"""Native HarfBuzz shaping and ReportLab's positioned-text adapter.

The PDF uses the same GPOS/GSUB as an installed font. No hand-adjusted tracking
or page-only kerning substitutes for the font's spacing.
"""
import ctypes as C
import ctypes.util
from pathlib import Path
from fontTools.ttLib import TTFont as OpenTypeFont
from reportlab.pdfbase.ttfonts import TTFont as PDFFont, ShapedStr, ShapeData

HB=C.CDLL(ctypes.util.find_library('harfbuzz'))
def bind(name,args,restype=C.c_void_p):
    f=getattr(HB,name);f.argtypes=args;f.restype=restype;return f
blob_create=bind('hb_blob_create',[C.c_void_p,C.c_uint,C.c_int,C.c_void_p,C.c_void_p])
face_create=bind('hb_face_create',[C.c_void_p,C.c_uint])
font_create=bind('hb_font_create',[C.c_void_p])
set_funcs=bind('hb_ot_font_set_funcs',[C.c_void_p],None)
set_scale=bind('hb_font_set_scale',[C.c_void_p,C.c_int,C.c_int],None)
buffer_create=bind('hb_buffer_create',[])
add_text=bind('hb_buffer_add_utf32',[C.c_void_p,C.POINTER(C.c_uint32),C.c_int,C.c_uint,C.c_int],None)
guess=bind('hb_buffer_guess_segment_properties',[C.c_void_p],None)
shape_run=bind('hb_shape',[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint],None)
buffer_destroy=bind('hb_buffer_destroy',[C.c_void_p],None)
font_destroy=bind('hb_font_destroy',[C.c_void_p],None)
face_destroy=bind('hb_face_destroy',[C.c_void_p],None)
blob_destroy=bind('hb_blob_destroy',[C.c_void_p],None)
class Info(C.Structure):
    _fields_=[('codepoint',C.c_uint32),('mask',C.c_uint32),('cluster',C.c_uint32),('v1',C.c_uint32),('v2',C.c_uint32)]
class Position(C.Structure):
    _fields_=[('x_advance',C.c_int32),('y_advance',C.c_int32),('x_offset',C.c_int32),('y_offset',C.c_int32),('v',C.c_uint32)]
class Feature(C.Structure):
    _fields_=[('tag',C.c_uint32),('value',C.c_uint32),('start',C.c_uint),('end',C.c_uint)]
infos=bind('hb_buffer_get_glyph_infos',[C.c_void_p,C.POINTER(C.c_uint)],C.POINTER(Info))
positions=bind('hb_buffer_get_glyph_positions',[C.c_void_p,C.POINTER(C.c_uint)],C.POINTER(Position))

class Shaper:
    def __init__(self,path):
        data=Path(path).read_bytes();self.blob=blob_create(data,len(data),0,None,None)
        self.face=face_create(self.blob,0);self.font=font_create(self.face)
        set_funcs(self.font);set_scale(self.font,1000,1000)
        self.tt=OpenTypeFont(path);self.names=self.tt.getGlyphOrder();self.cmap=self.tt.getBestCmap()
    def shape(self,text,kern=True):
        if not text:return []
        b=buffer_create();a=(C.c_uint32*len(text))(*map(ord,text))
        add_text(b,a,len(text),0,len(text));guess(b)
        features=(Feature*1)(Feature(int.from_bytes(b'kern','big'),int(kern),0,0xffffffff))
        shape_run(self.font,b,features,1);n=C.c_uint();ii=infos(b,C.byref(n));pp=positions(b,C.byref(n))
        out=[dict(gid=ii[k].codepoint,glyph=self.names[ii[k].codepoint],cluster=ii[k].cluster,
                  advance=pp[k].x_advance,y_advance=pp[k].y_advance,x=pp[k].x_offset,y=pp[k].y_offset)
             for k in range(n.value)]
        buffer_destroy(b);return out
    def width(self,text,size,kern=True):return sum(g['advance'] for g in self.shape(text,kern))*size/1000
    def close(self):font_destroy(self.font);face_destroy(self.face);blob_destroy(self.blob)

class PositionedFont(PDFFont):
    """Use ReportLab positioned runs populated by the native HarfBuzz adapter."""
    @property
    def shapable(self):return True
    @shapable.setter
    def shapable(self,value):pass
    def __init__(self,name,path):
        super().__init__(name,str(path),shapable=False)
        self.shaper=Shaper(path);self.reverse={}
        for cp,gn in self.shaper.cmap.items():self.reverse.setdefault(gn,cp)
        self.private_next=0xE100
    def positioned(self,text):
        run=self.shaper.shape(text);chars=[];data=[]
        for g in run:
            assert g['gid']!=0,('Missing PDF glyph',text,g)
            original=ord(text[g['cluster']])
            cp=original if self.shaper.cmap.get(original)==g['glyph'] else self.reverse.get(g['glyph'])
            width=self.shaper.tt['hmtx'][g['glyph']][0]
            if cp is None:
                while self.private_next in self.face.charToGlyph:self.private_next+=1
                cp=self.private_next;self.private_next+=1;self.reverse[g['glyph']]=cp
                self.face.charToGlyph[cp]=g['gid'];self.face.glyphToChar.setdefault(g['gid'],[]).append(cp)
                self.face.charWidths[cp]=width
            chars.append(chr(cp))
            data.append(ShapeData(g['cluster'],g['advance'],g['y_advance'],g['x'],g['y'],width))
        return ShapedStr(''.join(chars),data)
