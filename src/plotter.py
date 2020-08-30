import multiprocessing as mp
import logging
from matplotlib import pyplot as plt

logger = logging.getLogger()

def plotter(inP: mp.Queue):
  logger.info('PLOTTER_PROCESS started.')

  logger.info('PLOTTER_PROCESS finished.')
