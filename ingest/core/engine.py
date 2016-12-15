# Copyright 2016 The Johns Hopkins University Applied Physics Laboratory
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
import time
import sys
from ingest.core.config import Configuration, ConfigFileError
from six.moves import input
import logging
import datetime
import json
from ndlib.ndtype import *
from ndingest.ndbucket.tilebucket import TileBucket
from ndingest.settings.settings import Settings
settings = Settings.load()

class Engine(object):
    def __init__(self, config_file=None, backend_api_token=None, ingest_job_id=None):
        """
        A class to implement the core upload client workflow engine

        Args:
            config_file (str): Absolute path to a config file
            ingest_job_id (int): ID of the ingest job you want to work on
            backend_api_token (str): The authorization token for the Backend if used

        """
        self.config = None
        self.msg_wait_iterations = 20  # Each iteration waits for 10 seconds for incoming messages
        self.backend = None
        self.validator = None
        self.tile_processor = None
        self.path_processor = None
        self.backend_api_token = backend_api_token
        self.credential_create_time = None

        # Properties of ingest after creation
        self.credentials = None
        self.ingest_job_id = ingest_job_id
        self.upload_job_queue = None
        self.job_status = 0
        self.tile_bucket = None
        self.job_params = None
        self.tile_count = 0

        if config_file:
            self.load_configuration(config_file)

    def load_configuration(self, config_file):
        """
        Method to load a configuration file and setup the workflow engine
        Args:
            config_file (str): Absolute path to a config file

        Returns:
            None
        """
        try:
            with open(config_file, 'r') as file_handle:
                config_data = json.load(file_handle)
        except ValueError as _:
            # Bad json file
            raise ConfigFileError(
                "Malformed JSON in Ingest Configuration File.  Please double check contents and try again")
        except IOError as _:
            # File not found - python2/3 are different for missing files so us OSError
            raise ConfigFileError(
                "Ingest Configuration File not found.  Double check the provided path: {}".format(config_file))
        except OSError as _:
            # File not found - python2/3 are different for missing files so us OSError
            raise ConfigFileError(
                "Ingest Configuration File not found.  Double check the provided path: {}".format(config_file))

        # Load Config file and validate
        self.config = Configuration(config_data)
        self.config.load_plugins()

        # Get backend
        self.backend = self.config.get_backend(self.backend_api_token)

        # Get validator and set config
        self.validator = self.config.get_validator()
        self.validator.schema = self.config.schema

        # Setup tile processor
        self.tile_processor = self.config.tile_processor_class
        self.tile_processor.setup(self.config.get_tile_processor_params())

        # Setup path processor
        self.path_processor = self.config.path_processor_class
        self.path_processor.setup(self.config.get_path_processor_params())

    def setup(self, log_file=None):
        """Method to setup the Engine by finishing configuring subclasses and validating the schema"""
        if not log_file:
            log_file = 'ingest_log{}.log'.format(datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))

        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(levelname)-8s %(message)s',
                            datefmt='%m-%d %H:%M',
                            filename=log_file,
                            filemode='a')
        logging.getLogger('ingest-client').addHandler(logging.StreamHandler())
        logger = logging.getLogger('ingest-client')

        msgs = self.validator.validate()

        for msg in msgs["info"]:
            logger.info(msg)

        if msgs["error"]:
            for msg in msgs["error"]:
                logger.info(msg)
            raise Exception("Validation Failed: {}".format(" - ".join(msgs["error"])))

        return msgs["question"]

    def create_job(self):
        """
        Method to create an ingest job

        Args:

        Returns:
            None


        """
        self.ingest_job_id = self.backend.create(self.config.config_data)

        logger = logging.getLogger('ingest-client')
        logger.info("CREATED INGEST JOB: {}".format(self.ingest_job_id))

    def join(self):
        """
        Method to join an ingest job upload

        Job Status: {0: Preparing, 1: Uploading, 2: Complete}

        Args:


        Returns:
            None


        """
        self.job_status, self.nd_proj = self.backend.join(self.ingest_job_id)
        # self.job_status, self.credentials, self.upload_job_queue, self.tile_bucket, self.job_params, self.tile_count = self.backend.join(self.ingest_job_id)

        # Set cred time
        self.credential_create_time = datetime.datetime.now()

        logger = logging.getLogger('ingest-client')
        logger.info("JOINED INGEST JOB: {}".format(self.ingest_job_id))

    def cancel(self):
        """
        Method to cancel an ingest job

        Args:

        Returns:
            None


        """
        self.backend.cancel(self.ingest_job_id)

    def run(self):
        """Method to run the upload loop

        Returns:

        """
        # Set up logger
        logger = logging.getLogger('ingest-client')

        # Make sure you are joined
        # if not self.credentials:
            # msg = "Cannot start ingest engine.  Credentials not successfully received from the ingest service."
            # logger.error(msg)
            # raise Exception(msg)
        
        # if self.job_status == INGEST_STATUS_COMPLETE:
            # msg = "Ingest job already completed. Skipping ingest engine start."
            # logger.info(msg)
            # raise Exception(msg)

        # Do some work
        exiting = False
        wait_cnt = 0
        while True:
            try:
                # Get a task
                for message_id, receipt_handle, message_body in self.backend.get_task():

<<<<<<< HEAD
                  if not message_body:
                    time.sleep(10)
                    wait_cnt += 1
                    if wait_cnt == 1:
                      sys.stdout.write("Waiting for up to 3minutes for upload tasks to appear.")
                      sys.stdout.flush()
                      continue
                    elif wait_cnt < self.msg_wait_iterations:
                      sys.stdout.write(".")
                      sys.stdout.flush()
                      continue
                    else:
                      break
                  wait_cnt = 0

                  # Call path processor
                  filename = self.path_processor.process(message_body["x_tile"], message_body["y_tile"], message_body["z_tile"], message_body["t_tile"])

                  # Call tile processor
                  tile_handle = self.tile_processor.process(filename, message_body["x_tile"], message_body["y_tile"], message_body["z_tile"], message_body["t_tile"])

                  try:
                      tile_handle.seek(0)
                      tile_bucket = TileBucket(self.nd_proj.project_name, endpoint_url=settings.S3_ENDPOINT)
                      response = tile_bucket.putObject(tile_handle, self.nd_proj.channel_name, self.nd_proj.resolution, message_body['x_tile'], message_body['y_tile'], message_body['z_tile'], message_id, receipt_handle)
                      logger.info("Successfully wrote file: {}".format(response.key))

                  except Exception as e:
                      logger.error("Upload Failed -  X:{} Y:{} Z:{} T:{} - {}".format(message_body["x_tile"], message_body["y_tile"], message_body["z_tile"], message_body["t_tile"], e))

            except KeyboardInterrupt:
                # Make sure they want to stop this client
                quit_run = False
                while True:
                    quit_uploading = input("Are you sure you want to quit uploading? (y/n)")
                    if quit_uploading.lower() == "y":
                        quit_run = True
                        break
                    elif quit_uploading.lower() == "n":
                        print("Continuing...")
                        break
                    else:
                        print("Enter 'y' or 'n' for 'yes' or 'no'")

                if quit_run:
                    print("Stopping upload engine.")
                    exiting = True
                    break

        if not exiting:
            logger.info("No more tasks remaining.")
