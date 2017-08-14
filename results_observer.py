#!/usr/bin/env python3.5

import sys
import numpy as np
from keras.datasets import mnist
from keras.models import model_from_yaml
from keras_plot import plot_images, plot_all_images, plot_confusion_matrix  # 'Library' by Daniel
from keras_utils import format_dataset  # 'Library' by Daniel


def load_model(location):
    with open(location + "/model.yaml", "r") as f:
        model = model_from_yaml(f)
    model.load_weights(location + '/weights.h5')
    return model


def observe_results(data_generator, folder=None, to_categorical=True, data_reduction=None,
                    mode=0, observe_training=False):
    """
    :param data_generator:
    :param folder:
    :param to_categorical:
    :param data_reduction: if set to a number, use only (1/data_reduction) of all data. None uses all the data
    :param mode: plotting mode (0 or 1), whether to show color in the main diagonal or not
    :param observe_training: if True, we observe results for training set, else for test set
    :return:
    """
    if folder is None:
        folder = "."

    print("Loading training and test sets ...")
    (x_train, y_train), (x_test, y_test) = data_generator()

    print("Reshaping training and test sets ...")
    train_set, test_set, input_shape, labels = format_dataset(x_train, y_train, x_test, y_test,
                                                              verbose=True, ret_labels=True,
                                                              data_reduction=data_reduction,
                                                              to_categorical=to_categorical)
    if data_reduction is not None:
        x_test = x_test[:x_test.shape[0] // data_reduction]
        y_test = y_test[:y_test.shape[0] // data_reduction]
        x_train = x_train[:x_train.shape[0] // data_reduction]
        y_train = y_train[:y_train.shape[0] // data_reduction]

    print("Loading model from {} ...".format(folder))
    model = load_model(folder)

    print("Calculating predicted labels ...")
    if observe_training:
        pred_percents = model.predict(train_set[0])
        true_labels = y_train
        examples_set = x_train
    else:
        pred_percents = model.predict(test_set[0])
        true_labels = y_test
        examples_set = x_test
    pred_labels = np.argmax(pred_percents, axis=1)
    errors_vector = (pred_labels != true_labels)
    num_errors = np.sum(errors_vector)
    size_set = pred_labels.size
    print("Results: {} errors from {} test examples (Accuracy: {})".format(num_errors, size_set,
                                                                           1 - num_errors / size_set))

    print("Drawing confusion matrix ...")
    ignore_diag = False
    max_scale_factor = 100.0
    color_by_row = True
    if mode == 0:
        ignore_diag = True
        max_scale_factor = 1.0
        color_by_row = False
    confusion_mat = plot_confusion_matrix(true_labels, pred_labels, labels,
                                          title="Confusion Matrix " + ("(Training Set)" if observe_training else "(Test Set)"),
                                          filename=None, max_scale_factor=max_scale_factor,
                                          ignore_diagonal=ignore_diag, color_by_row=color_by_row)

    print("Counting misclassified examples ...")
    errors_indices = np.argwhere(errors_vector)
    errors_by_predicted_label = dict([(label, []) for label in labels])
    errors_by_expected_label = dict([(label, []) for label in labels])

    for idx in errors_indices:
        errors_by_expected_label[true_labels[idx][0]].append(idx[0])
        errors_by_predicted_label[pred_labels[idx][0]].append(idx[0])

    print("Labels that were confused by another value:")
    for i, label in enumerate(labels):
        tp = confusion_mat[i][i]
        fp = len(errors_by_expected_label[label])
        print("    Label {}: {:>3} mistakes, {:>5} right answers => Accuracy: {}".format(label, fp, tp,
                                                                                         tp / (tp + fp)))
    print("Labels that were mistakenly chosen:")
    for i, label in enumerate(labels):
        tp = confusion_mat[i][i]
        fp = len(errors_by_predicted_label[label])
        print("    Label {}: {:>3} mistakes, {:>5} right answers => Accuracy: {}".format(label, fp, tp,
                                                                                         tp / (tp + fp)))

    while True:
        print("Welcome to the misclassified images viewer!")
        print("Use the number keys + ENTER to select the best option.")
        print("Do you want to filter by predicted value or true value?")
        print("0. Exit\n1. Filter by predicted values\n2. Filter by true values")
        num = -1
        while num < 0 or num > 3:
            try:
                num = int(input(">> "))
            except ValueError:
                num = -1
        if num == 0:
            break
        pred_notrue = num == 1
        print("Filtering by: {} Values\n".format("Predicted" if pred_notrue else "True"))
        while True:
            print("Select the label you want to filter.")
            print("0. Back")
            for i, key in enumerate(labels):
                print("{}. Label {}".format(i + 1, key))
            num = -1
            while num < 0 or num > len(labels):
                try:
                    num = int(input(">> "))
                except ValueError:
                    num = -1
            if num == 0:
                break
            print("Plotting misclassified examples for the {} label {}\n".format("predicted" if pred_notrue else "true",
                                                                                 labels[num - 1]))

            if pred_notrue:
                indices = np.array(errors_by_predicted_label[labels[num - 1]], dtype=int)
                other_labels = true_labels[indices]
                indices = indices[other_labels.argsort()]
                title_labels = true_labels[indices]
                title = "Predicted label: {}".format(labels[num - 1])
            else:
                indices = np.array(errors_by_expected_label[labels[num - 1]], dtype=int)
                other_labels = pred_labels[indices]
                indices = indices[other_labels.argsort()]
                title_labels = pred_labels[indices]
                title = "True label: {}".format(labels[num - 1])
            # plot_images(x_test[indices], labels=y_test[indices], labels2=label_test[indices],
            #             label2_description="Predicted label", fig_num=1)
            plot_all_images(examples_set[indices], labels=title_labels, labels2=None, fig_num=1,
                            title=title)


    txt = input("Press ENTER to see all the misclassified examples unsorted one by one, or q to exit. ")
    if len(txt) <= 0 or txt[0] != "q":
        # Plot test examples, and see label comparison
        show_errors_only = True
        print("Plotting {}test images ...".format("incorrectly classified " if show_errors_only else ""))
        plot_images(examples_set, labels=true_labels, labels2=pred_labels,
                    label2_description="Predicted label", show_errors_only=True, fig_num=1)


if __name__ == "__main__":
    data = mnist.load_data
    folder = None
    mode = 0
    observe_training = True
    if len(sys.argv) > 1:
        folder = sys.argv[1]
    if len(sys.argv) > 2:
        mode = int(sys.argv[2])
    if len(sys.argv) > 3:
        observe_training = bool(sys.argv[3])

    observe_results(data, folder=folder, mode=mode, observe_training=observe_training)

    """
    Expects:
        py results_observer.py
        py results_observer.py folder
        py results_observer.py folder mode
    """