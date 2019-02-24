#=================================================================================================#
# TensorFlow implementation of GANSynth
#
# original paper
# [GANSynth: Adversarial Neural Audio Synthesis]
# (https://openreview.net/pdf?id=H1xQVn09FX)
#
# based on following papers
#
# [Progressive Growing of GANs for Improved Quality, Stability, and Variation]
# (https://arxiv.org/pdf/1710.10196.pdf)
#
# [Spectral Normalization for Generative Adversarial Networks]
# (https://arxiv.org/pdf/1802.05957.pdf)
#
# [cGANs with Projection Discriminator]
# (https://arxiv.org/pdf/1802.05637.pdf)
#=================================================================================================#

import tensorflow as tf
import numpy as np
import argparse
import functools
import itertools
import pickle
from dataset import NSynth
from model import GANSynth
from network import PGGAN
from attrdict import AttrDict as Param

parser = argparse.ArgumentParser()
parser.add_argument("--model_dir", type=str, default="gan_synth_model", help="model directory")
parser.add_argument('--filenames', type=str, nargs="+", default=["nsynth_train.tfrecord"], help="tfrecords")
parser.add_argument("--batch_size", type=int, default=64, help="batch size")
parser.add_argument("--max_steps", type=int, default=1000000, help="maximum number of training steps")
parser.add_argument("--steps", type=int, default=None, help="number of test steps")
parser.add_argument('--train', action="store_true", help="with training")
parser.add_argument('--eval', action="store_true", help="with evaluation")
parser.add_argument('--predict', action="store_true", help="with prediction")
parser.add_argument("--gpu", type=str, default="0", help="gpu id")
args = parser.parse_args()

tf.logging.set_verbosity(tf.logging.INFO)

with open("pitch_counts.pickle", "rb") as f:
    pitch_counts = pickle.load(f)

pggan = PGGAN(
    min_resolutions=[2, 16],
    max_resolutions=[128, 1024],
    min_channels=32,
    max_channels=256,
    channels=2,
    apply_spectral_norm=True
)

nsynth = NSynth(
    pitch_counts=pitch_counts,
    audio_length=64000,
    sample_rate=16000,
    spectrogram_shape=[128, 1024],
    overlap=0.75,
    mel_downscale=1
)

gan_synth = GANSynth(
    discriminator=pggan.discriminator,
    generator=pggan.generator,
    real_input_fn=functools.partial(
        nsynth.real_input_fn,
        filenames=args.filenames,
        batch_size=args.batch_size,
        num_epochs=None,
        shuffle=True
    ),
    fake_input_fn=functools.partial(
        nsynth.fake_input_fn,
        latent_size=256,
        batch_size=args.batch_size
    ),
    min_resolutions=[2, 16],
    max_resolutions=[128, 1024],
    max_steps=args.max_steps,
    hyper_params=Param(
        generator_learning_rate=8e-4,
        generator_beta1=0.0,
        generator_beta2=0.99,
        discriminator_learning_rate=4e-4,  # 8e-4,
        discriminator_beta1=0.0,
        discriminator_beta2=0.99
    ),
    name=args.model_dir
)

config = tf.ConfigProto(
    gpu_options=tf.GPUOptions(
        visible_device_list=args.gpu,
        allow_growth=True
    )
)

with tf.Session(config=config) as session:

    gan_synth.initialize()
    gan_synth.train()
