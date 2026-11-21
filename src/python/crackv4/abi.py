"""Pure legacy ABI declarations; import reads no data or DLL."""
import ctypes as C

def normalized(x):
 if isinstance(x,dict):return {k:normalized(v)for k,v in x.items()if k not in ('detector_ms','api_ms','call_wall_ms','frame_id','image_filename','group','return_code','read_ms')}
 if isinstance(x,list):return [normalized(v)for v in x]
 return x

class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double)]

class Image(C.Structure):_fields_=[('data',C.POINTER(C.c_uint8)),('width',C.c_int),('height',C.c_int),('stride',C.c_int64)]

class Config(C.Structure):_fields_=[('struct_size',C.c_uint32),('reference_mode',C.c_int),('ratio',C.c_double),('refine',C.c_int)]

class Experiment(C.Structure):_fields_=[('struct_size',C.c_uint32),('api_version',C.c_uint32),('flags',C.c_uint32),('max_images',C.c_uint32)]

class Result(C.Structure):
 _fields_=[('struct_size',C.c_uint32),('tip_confirmed',C.c_int),('length_confirmed',C.c_int),('root_confirmed',C.c_int),('has_candidate',C.c_int),('tip',Point),('length_px',C.c_double),('observed_length_px',C.c_double),('length_mm',C.c_double),('detector_ms',C.c_double),('api_ms',C.c_double),('temporal_hits',C.c_int),('tile_count',C.c_int)]

class Options(C.Structure):_fields_=[('struct_size',C.c_uint32),('api_version',C.c_uint32),('policy',C.c_int),('terminal',C.c_int)]

def image(a):return Image(a.ctypes.data_as(C.POINTER(C.c_uint8)),a.shape[1],a.shape[0],a.strides[0])

def points(p):return (Point*2)(*[Point(*xy)for xy in p])if p is not None else None
