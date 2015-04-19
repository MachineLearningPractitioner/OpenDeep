# standard libraries
import logging
# third party
import numpy
import PIL
# internal imports
from opendeep.log.logger import config_root_logger
from opendeep.data.standard_datasets.image.mnist import MNIST
from opendeep.models.multi_layer.generative_stochastic_network import GSN
from opendeep.optimization.stochastic_gradient_descent import SGD
from opendeep.optimization.adadelta import AdaDelta
from opendeep.utils.image import tile_raster_images
from opendeep.monitor.monitor import Monitor, MonitorsChannel

log = logging.getLogger(__name__)

###############################################
# MAIN METHOD FOR RUNNING DEFAULT GSN EXAMPLE #
###############################################
def main():
    ########################################
    # Initialization things with arguments #
    ########################################
    # use these arguments to get results from paper referenced above
    _train_args = {"n_epoch": 1000,  # maximum number of times to run through the dataset
                   "batch_size": 100,  # number of examples to process in parallel (minibatch)
                   "minimum_batch_size": 1,  # the minimum number of examples for a batch to be considered
                   "save_frequency": 10,  # how many epochs between saving parameters
                   "early_stop_threshold": .9995,  # multiplier for how much the train cost to improve to not stop early
                   "early_stop_length": 30,  # how many epochs to wait to see if the threshold has been reached
                   "learning_rate": .25,  # initial learning rate for SGD
                   "lr_decay": 'exponential',  # the decay function to use for the learning rate parameter
                   "lr_factor": .995,  # by how much to decay the learning rate each epoch
                   "momentum": 0.5,  # the parameter momentum amount
                   'momentum_decay': 'linear',  # how to decay the momentum each epoch (if applicable)
                   'momentum_factor': 0,  # by how much to decay the momentum (in this case not at all)
                   'nesterov_momentum': False,  # whether to use nesterov momentum update (accelerated momentum)
    }

    config_root_logger()
    log.info("Creating a new GSN")

    mnist = MNIST()
    config = {"outdir": 'outputs/gsn/mnist/'}
    gsn = GSN(config=config, layers=3, walkbacks=5, hidden_size=1000, input_size=28*28, tied_weights=True)

    recon_cost_channel = MonitorsChannel(name='cost')
    recon_cost_channel.add(Monitor('recon_cost', gsn.get_monitors()['recon_cost'], test=True))
    recon_cost_channel.add(Monitor('noisy_recon_cost', gsn.get_monitors()['noisy_recon_cost'], test=True))

    # Load initial weights and biases from file
    # params_to_load = '../../../outputs/gsn/mnist/trained_epoch_395.pkl'
    # gsn.load_params(params_to_load)

    optimizer = SGD(model=gsn, dataset=mnist, config=_train_args)
    # optimizer = AdaDelta(model=gsn, dataset=mnist, n_epoch=200, batch_size=100, learning_rate=1e-6)
    optimizer.train(monitor_channels=recon_cost_channel)

    # Save some reconstruction output images
    import opendeep.data.dataset as datasets
    n_examples = 100
    xs_test, _ = mnist.getSubset(datasets.TEST)
    xs_test = xs_test[:n_examples].eval()
    noisy_xs_test = gsn.f_noise(xs_test)
    reconstructed = gsn.run(noisy_xs_test)
    # Concatenate stuff
    stacked = numpy.vstack(
        [numpy.vstack([xs_test[i * 10: (i + 1) * 10],
                       noisy_xs_test[i * 10: (i + 1) * 10],
                       reconstructed[i * 10: (i + 1) * 10]])
         for i in range(10)])
    number_reconstruction = PIL.Image.fromarray(
        tile_raster_images(stacked, (gsn.image_height, gsn.image_width), (10, 30))
    )

    number_reconstruction.save(gsn.outdir + 'reconstruction.png')
    log.info("saved output image!")


if __name__ == '__main__':
    main()