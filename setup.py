from distutils.core import setup

setup(
    name='tasbot-spring',
    version='0.2.2',
    author=['Rene Milk','Andrea Piras','Tiziano'],
    author_email=['koshi@springlobby.info','braindamage@springlobby.info',''],
    packages=['tasbot'] ,
    scripts=['bot_runner_example.py'],
    url='https://github.com/renemilk/tasbot',
    license='LICENSE.txt',
    description='extensible bot library for the spring server protocol',
    long_description=open('README.txt').read(),
    data_files=[('./','Main.conf.example')]
)
