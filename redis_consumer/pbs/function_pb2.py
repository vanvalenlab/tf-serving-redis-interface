# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: function.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='function.proto',
  package='tensorflow.serving',
  syntax='proto3',
  serialized_options=_b('\370\001\001'),
  serialized_pb=_b('\n\x0e\x66unction.proto\x12\x12tensorflow.serving\"*\n\x0c\x46unctionSpec\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0c\n\x04type\x18\x02 \x01(\tB\x03\xf8\x01\x01\x62\x06proto3')
)




_FUNCTIONSPEC = _descriptor.Descriptor(
  name='FunctionSpec',
  full_name='tensorflow.serving.FunctionSpec',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='tensorflow.serving.FunctionSpec.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='type', full_name='tensorflow.serving.FunctionSpec.type', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=38,
  serialized_end=80,
)

DESCRIPTOR.message_types_by_name['FunctionSpec'] = _FUNCTIONSPEC
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

FunctionSpec = _reflection.GeneratedProtocolMessageType('FunctionSpec', (_message.Message,), dict(
  DESCRIPTOR = _FUNCTIONSPEC,
  __module__ = 'function_pb2'
  # @@protoc_insertion_point(class_scope:tensorflow.serving.FunctionSpec)
  ))
_sym_db.RegisterMessage(FunctionSpec)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)