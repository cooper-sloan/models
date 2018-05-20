# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
from six.moves import xrange


def labels_from_probs(probs):
  """
  Helper function: computes argmax along last dimension of array to obtain
  labels (max prob or max logit value)
  :param probs: numpy array where probabilities or logits are on last dimension
  :return: array with same shape as input besides last dimension with shape 1
          now containing the labels
  """
  # Compute last axis index
  last_axis = len(np.shape(probs)) - 1

  # Label is argmax over last dimension
  labels = np.argmax(probs, axis=last_axis)

  # Return as np.int32
  return np.asarray(labels, dtype=np.int32)


def noisy_max(predictions, lap_scale, return_clean_votes=False):
  """
  This aggregation mechanism takes the softmax/logit output of several models
  resulting from inference on identical inputs and computes the noisy-max of
  the votes for candidate classes to select a label for each sample: it
  adds Laplacian noise to label counts and returns the most frequent label.
  :param logits: logits or probabilities for each sample
  :param lap_scale: scale of the Laplacian noise to be added to counts
  :param return_clean_votes: if set to True, also returns clean votes (without
                      Laplacian noise). This can be used to perform the
                      privacy analysis of this aggregation mechanism.
  :return: pair of result and (if clean_votes is set to True) the clean counts
           for each class per sample and the the original labels produced by
           the teachers.
  """

  # Compute labels from logits/probs and reshape array properly

  # Initialize array to hold final labels
  pred_shape = np.shape(predictions)
  result = np.zeros((pred_shape[1], pred_shape[2]))

  if return_clean_votes:
    # Initialize array to hold clean votes for each sample
    clean_votes = np.zeros((5, pred_shape[1], pred_shape[2]))

  # Parse each sample
  for i in xrange(pred_shape[1]):
    # Count number of votes assigned to each class
    if (i % 100 == 0):
      print("Aggregated results from users %s to %s" % (i-99, i))
    for j in xrange(pred_shape[2]):
      label_counts = np.bincount(predictions[:,i,j], minlength=6)[1:6]

      if return_clean_votes:
        clean_votes[:,i,j] = label_counts

      # Cast in float32 to prepare before addition of Laplacian noise
      label_counts = np.asarray(label_counts, dtype=np.float32)

      # Sample independent Laplacian noise for each class
      for item in xrange(5):
        label_counts[item] += np.random.laplace(loc=0.0, scale=float(lap_scale))

      # Result is the most frequent label
      result[i,j] = np.argmax(label_counts) + 1

  # Cast labels to np.int32 for compatibility with deep_cnn.py feed dictionaries
  result = np.asarray(result, dtype=np.int32)

  if return_clean_votes:
    # Returns several array, which are later saved:
    # result: labels obtained from the noisy aggregation
    # clean_votes: the number of teacher votes assigned to each sample and class
    return result, clean_votes
  else:
    # Only return labels resulting from noisy aggregation
    return result


def aggregation_most_frequent(predictions):
  """
  This aggregation mechanism takes the softmax/logit output of several models
  resulting from inference on identical inputs and computes the most frequent
  label. It is deterministic (no noise injection like noisy_max() above.
  :param logits: logits or probabilities for each sample
  :return:
  """

  # Initialize array to hold final labels
  pred_shape = np.shape(predictions)
  result = np.zeros((pred_shape[1], pred_shape[2]))

  # Parse each sample
  for i in xrange(pred_shape[1]):
    # Count number of votes assigned to each class
    for j in xrange(pred_shape[2]):
      label_counts = np.bincount(predictions[:,i,j], minlength=6)[1:6]

      label_counts = np.asarray(label_counts, dtype=np.int32)

      # Result is the most frequent label
      result[i,j] = np.argmax(label_counts) + 1

  return np.asarray(result, dtype=np.int32)



