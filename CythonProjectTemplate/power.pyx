from CythonProjectTemplate.module.add cimport adder

def cython_square(double x):
    return x * x

def cython_add(double x, double y):
    return adder(x, y)
