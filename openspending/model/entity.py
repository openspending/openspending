from . import base

collection = 'entity'

base.init_model_module(__name__, collection)

# entity objects probably have the following fields
#   _id
#   name
#   label
