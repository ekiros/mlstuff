from multiprocessing import Pool
from random import random
from time import sleep
import os


def info(title):
    print(title)
    print('module name:', __name__)
    print('parent process:', os.getppid())
    print('process id:', os.getpid())
    

def f(name):
    info('-->function f')
    random_val = random()
    sleep(5)
    print(f'-->hello from func f, {name} and random: {random_val}')

def g(name):
    info('-->function g')
    random_val = random()
    sleep(random_val)
    print(f'-->hello from func g, {name} and random: {random_val}')

def h(name):
    info('-->function h')
    random_val = random()
    sleep(random_val)
    print(f'-->hello from func h, {name} and random: {random_val}')


if __name__ == '__main__':

    info('main line')

    with Pool() as pool:
        _ = pool.apply_async(f, args=('blob',))
        _ = pool.apply_async(g, args=('smarty',))
        _ = pool.apply_async(h, args=('panty',))
        pool.close()
        pool.join()

    #p = Process(target=f, args=('blob',))
    #p.start()
    #p.join()