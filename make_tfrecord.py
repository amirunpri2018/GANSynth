import tensorflow as tf
import json
import sys
import os


def main(in_dir1, in_dir2, in_file, out_file):
    with tf.io.TFRecordWriter(out_file) as writer:
        with open(in_file) as file:
            ground_truth = json.load(file)
        for key, value in ground_truth.items():
            writer.write(record=tf.train.Example(features=tf.train.Features(feature=dict(
                path1=tf.train.Feature(bytes_list=tf.train.BytesList(value=[os.path.join(in_dir1, "{}.jpg".format(key)).encode("utf-8")])),
                path2=tf.train.Feature(bytes_list=tf.train.BytesList(value=[os.path.join(in_dir2, "{}.jpg".format(key)).encode("utf-8")])),
                pitch=tf.train.Feature(int64_list=tf.train.Int64List(value=[value["pitch"]])),
                source=tf.train.Feature(int64_list=tf.train.Int64List(value=[value["instrument_source"]]))
            ))).SerializeToString())


if __name__ == "__main__":
    main(*sys.argv[1:])