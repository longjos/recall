from setuptools import setup, find_packages

version = '1.0.0-pre-3'
setup(
    name='recall',
    version=version,
    description='CQRS Library for Python',
    author='Doug Hurst',
    author_email='dalan.hurst@gmail.com',
    maintainer='Doug Hurst',
    license='MIT',
    url='https://github.com/dalanhurst/recall',
    packages=find_packages('src', exclude=['ez_setup', 'examples', 'tests']),
    package_dir={'': 'src'},
    download_url='http://pypi.python.org/packages/source/r/recall/recall-%s.tar.gz' % version,
    include_package_data=True,
    package_data={'': ['requirements.txt']},
    install_requires=[
        item for item in
        open("requirements.txt").read().split("\n")
        if item],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python']
)
