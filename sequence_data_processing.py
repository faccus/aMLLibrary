#!/usr/bin/env python3
"""
Copyright 2019 Marjan Hosseini
Copyright 2019 Marco Lattuada

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import ast
import configparser as cp
import logging
import os
import pprint
import random
import shutil
import sys
import time

import matplotlib
matplotlib.use('Agg')
#pylint: disable=wrong-import-position

import data_preparation.data_loading
import data_preparation.inversion
import data_preparation.normalization
import model_building.model_building
import regression_inputs

class SequenceDataProcessing:
    """
    main class

    Attributes
    ----------
    _data_preprocessing_list: list of DataPreparation
        The list of steps to be executed for data preparation

    _model_building: ModelBuilding
        The object which performs the actual model buidling

    _random_generator: RandomGenerator
        The random generator used in the whole application
    """

    _data_preprocessing_list = []

    _model_building = None

    _random_generator = None

    def __init__(self, args):
        """
        Parameters
        ----------
        args: argparse
            The arguments parsed at command line
        """

        configuration_file = args.configuration_file
        self.random_generator = random.Random(args.seed)
        self.debug = args.debug
        if self.debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        #Check if the configuration file exists
        if not os.path.exists(configuration_file):
            self.logger.error("%s does not exist", configuration_file)
            sys.exit(-1)

        self.conf = cp.ConfigParser()
        self.conf.optionxform = str
        self.conf.read(configuration_file)
        self.conf['General']['configuration_file'] = args.configuration_file
        self.conf['General']['output'] = args.output
        self.conf['General']['seed'] = str(args.seed)
        self.parameters = {}
        self.get_parameters(configuration_file)

        #Check if output path already exist
        if os.path.exists(args.output):
            self.logger.error("%s already exists", args.output)
            sys.exit(1)
        os.mkdir(self.parameters['General']['output'])
        shutil.copyfile(args.configuration_file, os.path.join(args.output, 'configuration_file.ini'))
        self.conf.write(open(os.path.join(args.output, "enriched_configuration_file.ini"), 'w'))

        #Check if the number of runs is 1; multiple runs are not supported in the current version
        if self.parameters['General']['run_num'] > 1:
            self.logger.error("Multiple runs not yet supported")
            sys.exit(1)

        #FIXME: this boolean variable must be set to true if there is not any explicit definition of train or test in the configuration file
        #random_test_selection = True

        #Adding read on input to data preprocessing step
        self._data_preprocessing_list.append(data_preparation.data_loading.DataLoading(self.parameters))

        #Check if scaling has to be applied globally; if yes, add the step to the list
        #if self.parameters['General']['run_num'] == 1 or not random_test_selection:
        #    self._data_preprocessing_list.append(data_preparation.normalization.Normalization(self.parameters))

        #Adding inverted features if required
        if self.parameters['DataPreparation']['inverse']:
            self._data_preprocessing_list.append(data_preparation.inversion.Inversion(self.parameters))

        self._model_building = model_building.model_building.ModelBuilding(self.random_generator.random())

    def get_parameters(self, configuration_file):
        """
        Gets the parameters from the config file named parameters.ini and put them into a dictionary
        named parameters

        Parameters
        ----------
        configuration_file : string
            The name of the file containing the configuration
        """
        self.parameters = {}

        for section in self.conf.sections():
            self.parameters[section] = {}
            for item in self.conf.items(section):
                try:
                    self.parameters[section][item[0]] = ast.literal_eval(item[1])
                except (ValueError, SyntaxError):
                    self.parameters[section][item[0]] = item[1]

        self.logger.debug(pprint.pformat(self.parameters, width=1))

    def process(self):

        """the main code"""
        start = time.time()

        self.logger.info("Start of the algorithm")

        self.logger.info("Starting experimental campaign")
        # performs reading data, drops irrelevant columns
        #initial_df = self.preliminary_data_processing.process(self.parameters)
        #logging.info("Loaded and cleaned data")

        # performs inverting of the columns and adds combinatorial terms to the df
        #ext_df = self.data_preprocessing.process(initial_df, self.parameters)
        #logging.info("Preprocessed data")


        data_processing_inputs = None

        for data_preprocessing in self._data_preprocessing_list:
            self.logger.info("Executing %s", data_preprocessing.get_name())
            data_processing_inputs = data_preprocessing.process(data_processing_inputs)
            self.logger.debug("Current data frame is:\n%s", data_processing_inputs.to_string())

        preprocessed_inputs = regression_inputs.RegressionInputs(data_processing_inputs, data_processing_inputs.index.values.tolist(), data_processing_inputs.index.values.tolist(), self.parameters['Features']['Extended_feature_names'], self.parameters['General']['y'])

        self.logger.debug(str(preprocessed_inputs))

        self._model_building.process(self.parameters, preprocessed_inputs)

        end = time.time()
        execution_time = str(end-start)
        print("Execution Time : " + execution_time)
