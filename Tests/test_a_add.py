from CythonProjectTemplate.power import cython_add


def test_cython_square():
    """
    Test the `cython_add` function and, by extension, the sub-module `add.pyx`.
    """

    assert cython_add(1.0, 1.0) == 2.0
    assert cython_add(1.0, -1.0) == 0.0
    assert cython_add(1000., -0.001) == 999.999
    assert cython_add(0., 0.) == 0.
