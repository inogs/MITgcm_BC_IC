from commons.utils import file2stringlist

MODEL_VARS  = file2stringlist("static-data/ModelVarNames")
INTERP_VARS = file2stringlist("static-data/InterpVarNames")

for var in MODEL_VARS:
    if var not in INTERP_VARS:
        print var