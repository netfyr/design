"""Small native Brotli adapter for reproducible WOFF2 packaging.

Uses the installed reference Brotli library; contains no font data. Install
the ordinary Python brotli package instead when native libraries are absent.
"""
import ctypes as C
import ctypes.util

MODE_GENERIC, MODE_TEXT, MODE_FONT = 0, 1, 2
_enc=C.CDLL(ctypes.util.find_library('brotlienc'))
_dec=C.CDLL(ctypes.util.find_library('brotlidec'))
_max=_enc.BrotliEncoderMaxCompressedSize
_max.argtypes=[C.c_size_t];_max.restype=C.c_size_t
_compress=_enc.BrotliEncoderCompress
_compress.argtypes=[C.c_int,C.c_int,C.c_int,C.c_size_t,C.c_void_p,C.POINTER(C.c_size_t),C.c_void_p]
_compress.restype=C.c_int
_decompress=_dec.BrotliDecoderDecompress
_decompress.argtypes=[C.c_size_t,C.c_void_p,C.POINTER(C.c_size_t),C.c_void_p]
_decompress.restype=C.c_int

def compress(data,mode=MODE_GENERIC,quality=11,lgwin=22):
    size=C.c_size_t(_max(len(data)))
    out=C.create_string_buffer(size.value)
    if not _compress(quality,lgwin,mode,len(data),data,C.byref(size),out):
        raise RuntimeError('Native Brotli encoder failed')
    return out.raw[:size.value]

def decompress(data):
    for capacity in (max(4096,len(data)*8),max(65536,len(data)*32),64*1024*1024):
        size=C.c_size_t(capacity);out=C.create_string_buffer(capacity)
        status=_decompress(len(data),data,C.byref(size),out)
        if status==1:return out.raw[:size.value]
        if status!=3:raise RuntimeError('Native Brotli decoder rejected data')
    raise RuntimeError('Brotli decoded data exceeds adapter limit')
