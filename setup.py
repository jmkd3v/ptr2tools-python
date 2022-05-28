import setuptools


lzss_module = setuptools.Extension(
    name="lzss",
    sources=["lzss.c"],
    depends=["lzss.h"]
)


setuptools.setup(
    name="ptr2tools",
    packages=["ptr2tools"],
    version="0.0.1",
    description="tools for dealing with PaRappa The Rapper 2 game files",
    ext_modules=[lzss_module],
    license="MIT",
)
