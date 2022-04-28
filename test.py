#!/usr/bin/env python3
"""
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

import argparse
import os
import subprocess
import sys
import time

import sequence_data_processing
from model_building.predictor import Predictor

def main():
    """
    Script used to perform regression test of the library

    This script is used to self check the library.
    #TODO: aggiorna la prossima riga
    It runs all the examples of example_configurations and checks if there is any error during their execution. Quality of the results is not analyzed nor compared with any reference
    """
    parser = argparse.ArgumentParser(description="Performs regression tests")
    parser.add_argument('-d', "--debug", help="Enable debug messages", default=False, action="store_true")
    parser.add_argument('-o', "--output", help="output folder where all the models will be stored", default="test_output")
    args = parser.parse_args()

    tests = generate_tests() #TODO: documenta variabile tests (nel senso, controlla se/come documentarla)

    try:
        os.mkdir(args.output)
    except FileExistsError:
        print(args.output+" already exists. Terminating the program...")
        sys.exit(1)

    #Perform tests
    outcomes = []
    for configuration in tests:
        test_name = configuration.pop('Name')
        output_path = args.output + '/' + test_name
        print("\n\n\nStarting "+test_name)

        try:
            if test_name == 'faas_predict':
                # Build object
                predictor_obj = Predictor(regressor_file=args.output+'/faas_test/LRRidge.pickle', output_folder=output_path, debug=args.debug)

                # Perform prediction reading from a config file
                predictor_obj.predict(config_file=configuration, mape_to_file=True)
            else:
                sequence_data_processor = sequence_data_processing.SequenceDataProcessing(configuration, debug=args.debug, output=output_path)
                sequence_data_processor.process()
        except Exception as e:
            print("Exception",e,"raised", sep=' ')
            outcomes.append(str(test_name)+" failed with exception "+str(e))
        else:
            outcomes.append(str(test_name)+" successfully run")

    #Print results
    print('\n\n\n\n\n\n\n\n\n\n\n\n*************Test Results*************')
    i = 0
    for outcome in outcomes:
        i += 1
        print(str(i)+')',outcome, sep=' ')



def generate_tests():
    tests = [
        {
            'Name': 'ernest',
            'General':{
                'run_num': 1,
                'techniques':['LRRidge'],
                'validation': 'All',
                'hp_selection': 'All',
                'y': 'y'
            },
            'DataPreparation':{
                'input_path': 'inputs/simplest.csv',
                'ernest': True,
                'rename_columns': {"x1": "cores", "x2": "datasize"}
            },
            'LRRidge':{
                'alpha': [0.1]
            }
        },
        {
            'Name': 'faas_test',
            'General':{
                'run_num': 1,
                'techniques': ['LRRidge', 'DecisionTree'],
                'hp_selection': 'KFold',
                'validation': 'HoldOut',
                'folds': 4,
                'hold_out_ratio': 0.2,
                'y': 'ave_response_time'
            },
            'DataPreparation':{
                'input_path': 'inputs/faas_test.csv',
                'inverse': ['Lambda'],
                'product_max_degree': 2,
                'product_interactions_only': True
            },
            'LRRidge':{
                'alpha': [0.02, 0.1, 1.0]
            },
            'DecisionTree':{
                'criterion': ['mse'],
                'max_depth': [3],
                'max_features': ['auto'],
                'min_samples_split': [0.01],
                'min_samples_leaf': [0.01]
            }
        },
        {
            'Name': 'faas_predict',
            'General':{
                'y': 'ave_response_time'
            },
            'DataPreparation':{
                'input_path': 'inputs/faas_predict.csv'
            }
        },
        {
            'Name': 'faas_test_sfs',
            'General':{
                'run_num': 1,
                'techniques': ['LRRidge'],
                'hp_selection': 'KFold',
                'validation': 'HoldOut',
                'folds': 4,
                'hold_out_ratio': 0.2,
                'y': 'ave_response_time'
            },
            'DataPreparation':{
                'input_path': 'inputs/faas_test.csv',
                'inverse': ['Lambda']
            },
            'FeatureSelection':{
                'method': 'SFS',
                'max_features': 3,
                'folds': 3
            },
            'LRRidge':{
                'alpha': [0.02, 0.1, 1]
            }
        },
        {
            'Name': 'faas_test_hyperopt',
            'General':{
                'run_num': 1,
                'techniques': ['LRRidge'],
                'hp_selection': 'KFold',
                'validation': 'HoldOut',
                'folds': 4,
                'hold_out_ratio': 0.2,
                'y': 'ave_response_time',
                'hyperparameter_tuning': 'Hyperopt',
                'hyperopt_max_evals': 10,
                'hyperopt_save_interval': 5
            },
            'DataPreparation':{
                'input_path': 'inputs/faas_test.csv',
                'inverse': ['Lambda']
            },
            'LRRidge':{
                'alpha': ['loguniform(0.01,1)']
            }
        },
        {
            'Name': 'faas_test_hyperopt_sfs',
            'General':{
                'run_num': 1,
                'techniques': ['LRRidge'],
                'hp_selection': 'KFold',
                'validation': 'HoldOut',
                'folds': 4,
                'hold_out_ratio': 0.2,
                'y': 'ave_response_time',
                'hyperparameter_tuning': 'Hyperopt',
                'hyperopt_max_evals': 10,
                'hyperopt_save_interval': 5
            },
            'DataPreparation':{
                'input_path': 'inputs/faas_test.csv',
                'inverse': ['Lambda']
            },
            'FeatureSelection':{
                'method': 'SFS',
                'max_features': 3,
                'folds': 3
            },
            'LRRidge':{
                'alpha': ['loguniform(0.01,1)']
            }
        },
        {
            'Name': 'faas_test_xgboost_fs',
            'General':{
                'run_num': 2,
                'techniques': ['LRRidge'],
                'hp_selection': 'KFold',
                'validation': 'HoldOut',
                'folds': 4,
                'hold_out_ratio': 0.2,
                'y': 'ave_response_time'
            },
            'DataPreparation':{
                'input_path': 'inputs/faas_test.csv',
                'inverse': ['Lambda']
            },
            'FeatureSelection':{
                'method': 'XGBoost',
                'max_features': 2,
                'XGBoost_tolerance': 0.4
            },
            'LRRidge':{
                'alpha': [0.1, 0.2]
            }
        }
    ]
    return tests

if __name__ == '__main__':
    main()
