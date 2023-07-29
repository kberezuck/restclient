from setuptools import setup

REQUIRES = [
    'requests',
    'structlog',
    'curlify',
    'allure-pytest',

]
setup(
    name='restclient',
    version='0.0.1',
    packages=['restclient'],
    url='https://github.com/kberezuck/restclient.git',
    license='MIT',
    author='Ksenia_Berezuck',
    author_email='',
    install_requires=REQUIRES,
    description='restclient with allure and login'
)
