from CythonProjectTemplate.power import cython_square

def test_cython_square():
    """
    Test the `cython_square` function
    """

    assert cython_square(2.0) == 4.0
    assert cython_square(-2.0) == 4.0
    assert cython_square(0.) == 0.
    assert cython_square(100.0) == 1000.
    assert cython_square(-100.0) == 1000.
