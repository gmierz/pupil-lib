from core.utilities.MPLogger import MultiProcessingLog
from core.workers.processors.trial_processor import TrialProcessor
import core.utilities.utilities as utilities
from threading import Thread
import os
import threading
import math
import traceback
import copy

class PLibTrialWorker(Thread):
    def __init__(self, config, chunk_data=None):
        Thread.__init__(self)
        self.config = config  # Metadata about how to process the given datasets.
        self.chunk_data = chunk_data
        self.trial_num = 0

        self.initial_data = {
            'config': config,    # Metadata about how to process the given datasets.
            'chunk_data': chunk_data,
        }

        self.proc_trial_data = {}
        self.logger = MultiProcessingLog.get_logger()

    def reset_initial_data(self):
        self.initial_data = {
            'config': self.config,    # Metadata about how to process the given datasets.
            'chunk_data': self.chunk_data,
        }

    def get_baseline_start(self, data_chunk, correct_for_marker_error=False, testing=False, name='',
                           use_trial_time=False):
        # print('Getting baseline index')
        testing_passed = True
        baseline_time = abs(data_chunk['baseline_time_sec']) if not use_trial_time else \
                        abs(data_chunk['trial_time_sec'])
        srate = data_chunk['srate']
        marker_ind = data_chunk['marker_ind']

        # Having marker_time as the ideal time that is corrected
        # for the marker error allows the change to bubble through
        # this function and ensures that the baseline index is
        # chosen such that it takes into account the error. Chosing 'actual_marker_time'
        # here will result in no corrections.
        marker_time = data_chunk['marker_time']

        if testing:
            # Testing to make sure indices line up
            if data_chunk['actual_marker_time'] != data_chunk['timestamps'][marker_ind]:
                self.logger.send('CRITICAL', 'bad time: ' + '%.8f' % data_chunk['actual_marker_time'] + ' vs. ' +
                            '%.8f' % data_chunk['timestamps'][marker_ind], os.getpid(), threading.get_ident())
                raise Exception("Failed checking marker indices and times. Name: " + name)
            else:
                self.logger.send('INFO', 'good time: ' + '%.8f' % data_chunk['actual_marker_time'] + ' vs. ' +
                            '%.8f' % data_chunk['timestamps'][marker_ind], os.getpid(), threading.get_ident())

        baseline_points = int(math.ceil(baseline_time * srate))
        initial_ind = marker_ind - baseline_points
        initial_baseline_timestamp = data_chunk['timestamps'][initial_ind]
        initial_error = marker_time - initial_baseline_timestamp
        ideal_timestamp = marker_time - baseline_time
        final_timestamp = 0  # Final timestamp, before error correction
        final_data_value = 0  # Final data value
        final_ind = 0  # First data point of chunk is at this index
        final_error = 0  # Final amount of error that should be corrected for
        final_choice = 1  # Always taking previous, i.e. error is always > 0 for markertime-baselinetime

        # At the end of this conditional, we have the correct settings in the final_* fields.
        if initial_error > baseline_time and initial_error > data_chunk['error']:
            # print('Overestimated')
            for i in range(initial_ind, marker_ind):
                if data_chunk['timestamps'][i] < ideal_timestamp < data_chunk['timestamps'][i + 1]:
                    # Found where we should get the index. Always take the error which overestimates,
                    # it makes the logic for linear approximation simpler.
                    final_ind = i
                    final_timestamp = data_chunk['timestamps'][i]
                    final_data_value = data_chunk['data'][i]
                    final_error = ideal_timestamp - data_chunk['timestamps'][i]
                    break
            else:
                self.logger.send('ERROR', """Overestimated: Can't find a good timestamp,
                                        something broke.""", os.getpid(), threading.get_ident())
                raise Exception("""Overestimated: Can't find a good timestamp, something broke. Name: """ + name)
        elif data_chunk['error'] < initial_error < baseline_time:
            # print('Underestimated')
            for i in range(initial_ind + 1, 0, -1):
                if data_chunk['timestamps'][i] > ideal_timestamp > data_chunk['timestamps'][i - 1]:
                    # Found where we should get the index. Always take the error which overestimates,
                    # it makes the logic for linear approximation simpler.
                    final_ind = i - 1
                    final_timestamp = data_chunk['timestamps'][i - 1]
                    final_data_value = data_chunk['data'][i - 1]
                    final_error = ideal_timestamp - data_chunk['timestamps'][i - 1]
                    break
            else:
                self.logger.send('ERROR', """Underestimated: Can't find a good timestamp,
                                        something broke.""", os.getpid(), threading.get_ident())
                raise Exception("""Underestimated: Can't find a good timestamp, something broke. Name: """ + name)
        else:
            # print('Equal, no error.')
            final_timestamp = ideal_timestamp
            final_ind = marker_ind - baseline_points
            final_data_value = data_chunk['data'][final_ind]

        ideal_data = utilities.linear_approx(final_data_value, final_timestamp,
                                             data_chunk['data'][final_ind + 1], data_chunk['timestamps'][final_ind + 1],
                                             ideal_timestamp, error=final_error, default_val=1)

        proc_baseline_chunk = {
            'final_ind': final_ind,
            'final_timestamp': final_timestamp,
            # Negative error means that, overall, we've overestimated.
            # Positive is an underestimation.
            'total_error': final_timestamp - ideal_timestamp,
            'final_data_value': final_data_value,
            'ideal_timestamp': ideal_timestamp,
            'ideal_data': ideal_data,
            'ideal_marker_timestamp_m_ideal_timestamp': -(marker_time - ideal_timestamp),
            'final_timestamp_m_actual_mrk_ts': data_chunk['actual_marker_time'] - final_timestamp,
            'baseline_time_points': marker_ind - final_ind
        }

        if use_trial_time:
            proc_baseline_chunk['trial_time_points'] = marker_ind - final_ind

        # if testing:
        # Check if we correctly calculated the number of points.
        if data_chunk['timestamps'][final_ind + proc_baseline_chunk['baseline_time_points']] !=\
                data_chunk['actual_marker_time']:
            self.logger('CRITICAL', 'Number of trial points is incorrect.' +
                        'Expected: ' + str(data_chunk['actual_marker_time']) +
                        ' instead, we got: ' +
                        str(data_chunk['timestamps'][final_ind + proc_baseline_chunk['baseline_time_points']]),
                        os.getpid(), threading.get_ident())
            raise Exception('Number of trial points is incorrect.')

        # Correct for marker error after the intial processing.
        if correct_for_marker_error:
            print('Correcting for marker error. Not implemented yet...')

        return proc_baseline_chunk, testing_passed

    def get_trialtime_end(self, data_chunk, correct_for_marker_error=False, testing=False, name='',
                          use_baseline_time=False):
        # print('Getting trial time end')
        testing_passed = True
        trial_time = data_chunk['trial_time_sec'] if not use_baseline_time else \
                     data_chunk['baseline_time_sec']
        srate = data_chunk['srate']
        marker_ind = data_chunk['marker_ind']

        # Having marker_time as the ideal time that is corrected
        # for the marker error allows the change to bubble through
        # this function and ensures that the trial_time index is
        # chosen such that it takes into account the error. Choosing 'actual_marker_time'
        # here will result in no corrections.
        marker_time = data_chunk['marker_time']

        if testing:
            # Testing to make sure indices line up
            if data_chunk['actual_marker_time'] != data_chunk['timestamps'][marker_ind]:
                self.logger.send('CRITICAL', 'bad time: ' + '%.8f' % data_chunk['actual_marker_time'] + ' vs. ' +
                            '%.8f' % data_chunk['timestamps'][marker_ind], os.getpid(), threading.get_ident())
                testing_passed = False
                raise Exception("Failed checking marker indices and times. Name: " + name)
            else:
                self.logger.send('INFO', 'good time: ' + '%.8f' % data_chunk['actual_marker_time'] + ' vs. ' +
                            '%.8f' % data_chunk['timestamps'][marker_ind], os.getpid(), threading.get_ident())

        trial_time_points = int(math.ceil(trial_time * srate))
        initial_ind = marker_ind + trial_time_points
        initial_trial_timestamp = data_chunk['timestamps'][initial_ind]
        initial_error = initial_trial_timestamp - marker_time
        ideal_timestamp = marker_time + trial_time
        final_timestamp = 0  # Final timestamp, before error correction
        final_data_value = 0  # Final data value
        final_ind = 0  # First data point of chunk is at this index
        final_error = 0  # Final amount of error that should be corrected for
        final_choice = 0  # Always taking curr, i.e. error is always > 0 for trialtime-markertime

        # At the end of this conditional, we have the correct settings in the final_* fields.
        if initial_error > trial_time and initial_error > data_chunk['error']:
            # print('Overestimated')
            for i in range(initial_ind, marker_ind, -1):
                if data_chunk['timestamps'][i] > ideal_timestamp > data_chunk['timestamps'][i - 1]:
                    # Found where we should get the index. Always take the error which overestimates,
                    # it makes the logic for linear approximation simpler.
                    final_ind = i
                    final_timestamp = data_chunk['timestamps'][i]
                    final_data_value = data_chunk['data'][i]
                    final_error = ideal_timestamp - data_chunk['timestamps'][i]
                    break
            else:
                self.logger.send('ERROR', """Overestimated: Can't find a good timestamp,
                                        something broke.""", os.getpid(), threading.get_ident())
                raise Exception("""Overestimated: Can't find a good timestamp, something broke. Name: """ + name)
        elif data_chunk['error'] < initial_error < trial_time:
            # print('Underestimated')
            for i in range(initial_ind - 1, len(data_chunk['timestamps'])):
                # logger.send('INFO', 'curr' + str(data_chunk['timestamps'][i]) + '   next' + str(data_chunk['timestamps'][i+1]) +
                #            '    ideal_timestamp' + str(ideal_timestamp), os.getpid(), threading.get_ident())
                if data_chunk['timestamps'][i] < ideal_timestamp < data_chunk['timestamps'][i + 1]:
                    # Found where we should get the index. Always take the error which overestimates,
                    # it makes the logic for linear approximation simpler.
                    final_ind = i + 1
                    final_timestamp = data_chunk['timestamps'][i + 1]
                    final_data_value = data_chunk['data'][i + 1]
                    final_error = ideal_timestamp - data_chunk['timestamps'][i + 1]
                    break
            else:
                self.logger.send('ERROR', """Underestimated: Can't find a good timestamp,
                                        something broke.""", os.getpid(), threading.get_ident())
                raise Exception("""Underestimated: Can't find a good timestamp, something broke. Name: """ + name)
        else:
            # print('Equal, no error.')
            final_timestamp = ideal_timestamp
            final_ind = marker_ind + trial_time_points
            final_data_value = data_chunk['data'][final_ind]

        ideal_data = utilities.linear_approx(data_chunk['data'][final_ind - 1], data_chunk['timestamps'][final_ind - 1],
                                             final_data_value, final_timestamp,
                                             ideal_timestamp, error=final_error, default_val=2)

        proc_trial_chunk = {
            'final_ind': final_ind,
            'final_timestamp': final_timestamp,
            # Negative error here means that we've overestimated.
            # Positive is an underestimation.
            'total_error': ideal_timestamp - final_timestamp,
            'final_data_value': final_data_value,
            'ideal_timestamp': ideal_timestamp,
            'ideal_data': ideal_data,
            'ideal_marker_timestamp_m_ideal_timestamp': ideal_timestamp - marker_time,
            'final_timestamp_m_actual_mrk_ts': final_timestamp - data_chunk['actual_marker_time'],
            'trial_time_points': final_ind-marker_ind
        }

        if use_baseline_time:
            proc_trial_chunk['baseline_time_points'] = final_ind-marker_ind

        if testing:
            # Check if we correctly calculated the number of points.
            if data_chunk['timestamps'][final_ind-proc_trial_chunk['trial_time_points']] !=\
                    data_chunk['actual_marker_time']:
                self.logger('CRITICAL', 'Number of trial points is incorrect.' +
                            'Expected: ' + str(data_chunk['actual_marker_time']) +
                            ' instead, we got: ' +
                            str(data_chunk['timestamps'][final_ind-proc_trial_chunk['trial_time_points']]),
                            os.getpid(), threading.get_ident())
                raise Exception('Number of trial points is incorrect.')

        # Correct for marker error after the intial processing.
        if correct_for_marker_error:
            print('Correcting for marker error. Not implemented yet...')

        return proc_trial_chunk, testing_passed

    def run(self):
        testing = self.config['testing']
        deep_test = True if self.config['testing_depth'] == 'deep' else False

        # If this trial is in the yaml config, specify it's
        # configuration by replacing the current one with a new one.
        self.config = utilities.parse_yaml_for_config(self.config, self.getName())

        # Run the pre processors.
        trial_processor = None
        if self.config['trial_pre_processing']:
            trial_processor = TrialProcessor()

            for config in self.config['trial_pre_processing']:
                if config['name'] in trial_processor.pre_processing.all:
                    trial_processor.pre_processing.all[config['name']](self.initial_data, config)

        if testing and deep_test:
            self.logger.send('INFO', 'I am a trial worker. I split the trials from the dataset.',
                              os.getpid(), threading.get_ident())
            self.logger.send('INFO', self.getName(),
                             os.getpid(), threading.get_ident())
            self.logger.send('INFO', self.getName() + ': ' + 'Srate: ' + str(self.chunk_data['srate']) +
                             ' Length: ' + str(len(self.chunk_data['timestamps'])), os.getpid(), threading.get_ident())

        # Run the pre-processor functions on the trial
        # and also set whether or not any were even run.
        # for i in self.config[]

        # Logic for correctly breaking the data down goes here.
        # Only run tests in them if 'deep' testing is on.
        try:
            # If the given baseline time is given as 0 or less.
            if self.chunk_data['baseline_time_sec'] <= 0:
                proc_baseline_chunk, testing_passed = self.get_baseline_start(self.chunk_data, testing=(testing and deep_test),
                                                                              name=self.getName())
                if self.chunk_data['trial_time_sec'] >= 0:
                    proc_trial_chunk, testing_passed = self.get_trialtime_end(self.chunk_data,
                                                                              testing=(testing and deep_test),
                                                                              name=self.getName())
                else:
                    proc_trial_chunk, testing_passed = self.get_baseline_start(self.chunk_data,
                                                                               testing=(testing and deep_test),
                                                                               name=self.getName(), use_trial_time=True)
            else:
                proc_baseline_chunk, testing_passed = self.get_trialtime_end(self.chunk_data, testing=(testing and deep_test),
                                                         name=self.getName(), use_baseline_time=True)
                proc_trial_chunk, testing_passed = self.get_trialtime_end(self.chunk_data, testing=(testing and deep_test), name=self.getName())
        except Exception as e:
            self.logger.send('CRITICAL', 'Exception occurred while we were processing the trial: ' + self.getName() +
                             '\nThe exception is: \n' + traceback.format_exc(), os.getpid(), threading.get_ident())
            return None

        if testing and deep_test:
            self.logger.send('INFO', self.getName() + ':  proc_baseline_chunk: ' + str(proc_baseline_chunk),
                             os.getpid(), threading.get_ident())
            self.logger.send('INFO', self.getName() + ':  proc_trial_chunk: ' + str(proc_trial_chunk) + '  : trial',
                             os.getpid(), threading.get_ident())

        # Final_ind is inclusive, keep it.
        # So, we add one at the end to make sure we get it.
        # This part cuts out the data for any cases, and doesn't depend upon the
        # centering index of the marker.
        proc_data_chunk = self.chunk_data['data'][
                                          proc_baseline_chunk['final_ind']:proc_trial_chunk['final_ind'] + 1]
        proc_time_chunk = self.chunk_data['timestamps'][
                                          proc_baseline_chunk['final_ind']:proc_trial_chunk['final_ind'] + 1]

        actual_data_chunk = {
            'timestamps': proc_time_chunk,
            'data': proc_data_chunk
        }

        if testing:
            # Testing to make sure indices line up
            # If there is an error here, it means that cutting the data out of the chunk did not work correctly
            # and the indices do not line up.
            if actual_data_chunk['timestamps'][0] != self.chunk_data['timestamps'][proc_baseline_chunk['final_ind']]:
                self.logger.send('CRITICAL', 'bad cutout initial baseline time: ' +
                            '%.8f' % actual_data_chunk['timestamps'][0] + ' vs. ' +
                            '%.8f' % self.chunk_data['timestamps'][proc_baseline_chunk['final_ind']],
                            os.getpid(), threading.get_ident())
                testing_passed = False
            else:
                self.logger.send('INFO','good cutout initial baseline time: ' +
                            '%.8f' % actual_data_chunk['timestamps'][0] + ' vs. ' +
                            '%.8f' % self.chunk_data['timestamps'][proc_baseline_chunk['final_ind']],
                            os.getpid(), threading.get_ident())

            if actual_data_chunk['timestamps'][-1] != self.chunk_data['timestamps'][proc_trial_chunk['final_ind']]:
                self.logger.send('CRITICAL', 'bad cutout final trial time: ' +
                            '%.8f' % actual_data_chunk['timestamps'][-1] + ' vs. ' +
                            '%.8f' % self.chunk_data['timestamps'][proc_trial_chunk['final_ind']],
                            os.getpid(), threading.get_ident())
                testing_passed = False
            else:
                self.logger.send('INFO', 'good cutout final trial time: ' +
                            '%.8f' % actual_data_chunk['timestamps'][-1] + ' vs. ' +
                            '%.8f' % self.chunk_data['timestamps'][proc_trial_chunk['final_ind']],
                            os.getpid(), threading.get_ident())

            # This test will tell you if the ideal timestamps that are corrected for marker error,
            # line up properly after processing, the first and last data points will be replaced
            # by these 'ideal_*' fields. This is also why we always overestimate both ends.

            # The length of the trial, after we replace the points
            produced_ideal_time_length = proc_trial_chunk['ideal_timestamp'] - proc_baseline_chunk['ideal_timestamp']

            # The ideal times added up together, which always gives the correct time length, unless something
            # in the cutting functions broke.
            produced_sumed_ideal_length = proc_trial_chunk['ideal_marker_timestamp_m_ideal_timestamp'] - \
                                          proc_baseline_chunk['ideal_marker_timestamp_m_ideal_timestamp']

            if produced_ideal_time_length != produced_sumed_ideal_length:
                overestimated = '\n   Overestimated '
                underestimated = '\n   Underestimated '
                trial_estimation_string = overestimated + 'trial: ' + str(proc_trial_chunk['total_error']) if \
                    proc_trial_chunk['total_error'] < 0 else underestimated + 'trial: ' + str(
                    proc_trial_chunk['total_error'])
                baseline_estimation_string = overestimated + 'baseline: ' + str(proc_baseline_chunk['total_error']) \
                    if proc_baseline_chunk['total_error'] < 0 \
                    else underestimated + 'baseline: ' + str(proc_baseline_chunk['total_error'])
                self.logger.send('CRITICAL', '\nSomething broke!! :( \nIdeal time is wrong: ' +
                            '%.8f' % produced_ideal_time_length + ' vs. ' +
                            '%.8f' % produced_sumed_ideal_length + '    expected: ' +
                            str( self.chunk_data['trial_time_sec'] - self.chunk_data['baseline_time_sec']) +
                            ' Estimations:' +
                            trial_estimation_string + baseline_estimation_string, os.getpid(), threading.get_ident())
                testing_passed = False
            else:
                # This is, in essence, a second test that needs to be done visually.
                # If there are any underestimations, then the indices are incorrect, and
                # the algorithms above failed. This is because, by choice, and for ease
                # of use later, we always pick the point which slightly overestimates the result
                # to make the linear approximations more "generalized". The exception here is for 0s which
                # display underestimations.
                overestimated = '\n   Overestimated '
                underestimated = '\n   Underestimated '
                trial_estimation_string = overestimated + 'trial: ' + str(proc_trial_chunk['total_error']) if \
                    proc_trial_chunk['total_error'] < 0 else underestimated + 'trial: ' + str(
                    proc_trial_chunk['total_error'])
                baseline_estimation_string = overestimated + 'baseline: ' + str(proc_baseline_chunk['total_error']) \
                    if proc_baseline_chunk['total_error'] < 0 \
                    else underestimated + 'baseline: ' + str(proc_baseline_chunk['total_error'])
                self.logger.send('INFO', '\nSuccess! ideal time is good: ' +
                                 '%.8f' % produced_ideal_time_length + ' vs. ' +
                                 '%.8f' % produced_sumed_ideal_length + '    expected: ' +
                                 str(self.chunk_data['trial_time_sec'] - self.chunk_data['baseline_time_sec']) +
                                 '  Estimations:    ' + trial_estimation_string + baseline_estimation_string + '\n' +
                                 '  Chunk Length: data - ' + str(len(actual_data_chunk['data'])) + '  timestamps- ' +
                                 str(len(actual_data_chunk['timestamps'])),
                                 os.getpid(), threading.get_ident())
        if testing:
            if testing_passed:
                self.logger.send('INFO', self.getName() + ':  TEST-PASS  Testing passed!',
                                 os.getpid(), threading.get_ident())
            else:
                self.logger.send('CRITICAL', self.getName() + ': TEST-FAIL Testing failed, oh no! This can`t be!',
                                 os.getpid(), threading.get_ident())

        # Replace with the final or append the ideal final linearly
        # interpolated data point.
        if self.chunk_data['baseline_time_sec'] > 0:
            actual_data_chunk['timestamps'] = [proc_baseline_chunk['ideal_timestamp']] + actual_data_chunk['timestamps']
            actual_data_chunk['data'] = [proc_baseline_chunk['ideal_data']] + actual_data_chunk['data']
            proc_baseline_chunk['baseline_time_points'] += 1
        else:
            actual_data_chunk['timestamps'][0] = proc_baseline_chunk['ideal_timestamp']
            actual_data_chunk['data'][0] = proc_baseline_chunk['ideal_data']

        if testing:
            self.logger.send('INFO', 'Checking baselines new values. Two first elements: 1- ' +
                             '%.8f' % actual_data_chunk['timestamps'][0] + '  2- ' +
                             '%.8f' % actual_data_chunk['timestamps'][1],
                              os.getpid(), threading.get_ident())
            # See if we still find the marker time at the expected location.
            # First, check if the marker is contained within the chunk.
            if self.chunk_data['baseline_time_sec'] <= 0 <= self.chunk_data['trial_time_sec']:
                if actual_data_chunk['timestamps'][proc_baseline_chunk['baseline_time_points']] != \
                   self.chunk_data['actual_marker_time']:
                    self.logger.send('INFO', 'Can`t find marker timestamps,  got: ' +
                                str(actual_data_chunk['timestamps'][proc_baseline_chunk['baseline_time_points']]) +
                                ' expected: ' +
                                str(self.chunk_data['actual_marker_time']), os.getpid(), threading.get_ident)
                else:
                    self.logger.send('INFO', 'Found good marker timestamp,  got: ' +
                                str(actual_data_chunk['timestamps'][proc_baseline_chunk['baseline_time_points']]) +
                                ' expected: ' +
                                str(self.chunk_data['actual_marker_time']), os.getpid(), threading.get_ident)

        # Replace with the final or append the ideal final linearly
        # interpolated data point.
        if self.chunk_data['trial_time_sec'] < 0:
            actual_data_chunk['timestamps'] += [proc_trial_chunk['ideal_timestamp']]
            actual_data_chunk['data'] += [proc_trial_chunk['ideal_data']]
            proc_trial_chunk['trial_time_points'] += 1
        else:
            actual_data_chunk['timestamps'][-1] = proc_trial_chunk['ideal_timestamp']
            actual_data_chunk['data'][-1] = proc_trial_chunk['ideal_data']

        if testing:
            self.logger.send('INFO', 'Checking trials new values. Two final elements: before last- ' +
                             '%.8f' % actual_data_chunk['timestamps'][-2] + '  last- ' +
                             '%.8f' % actual_data_chunk['timestamps'][-1],
                             os.getpid(), threading.get_ident())
            if self.chunk_data['baseline_time_sec'] <= 0 <= self.chunk_data['trial_time_sec']:
                # See if we still find the marker time at the expected location.
                if actual_data_chunk['timestamps'][len(actual_data_chunk['timestamps']) - \
                   proc_trial_chunk['trial_time_points'] - 1] != self.chunk_data['actual_marker_time']:
                    self.logger.send('INFO', 'Can`t find marker timestamps,  got: ' +
                                     str(actual_data_chunk['timestamps'][len(actual_data_chunk['timestamps']) -
                                         proc_trial_chunk['trial_time_points'] - 1]) +
                                     ' expected: ' +
                                     str(self.chunk_data['actual_marker_time']), os.getpid(), threading.get_ident)
                else:
                    self.logger.send('INFO', 'Found good marker timestamp,  got: ' +
                                     str(actual_data_chunk['timestamps'][len(actual_data_chunk['timestamps']) -
                                         proc_trial_chunk['trial_time_points'] - 1]) +
                                     ' expected: ' +
                                     str(self.chunk_data['actual_marker_time']), os.getpid(), threading.get_ident)

        # Create the final data structure.
        self.proc_trial_data = {
            'config': {
                'proc_baseline_chunk': proc_baseline_chunk,
                'proc_trial_chunk': proc_trial_chunk,

                # Store some portions of the chunk data that was
                # given by the parent trigger worker.
                'partial_chunk_data': {i: self.chunk_data[i] for i in self.chunk_data
                                       if i != 'data' and i != 'timestamps'},

                'name': copy.deepcopy(self.getName()),
                'contains_marker': True if self.chunk_data['baseine_time_sec'] <= 0 <=
                                        self.chunk_data['trial_time_sec']
                                        else False
            },
            'trial': copy.deepcopy(actual_data_chunk),
            'trial_rmbaseline': {'data': [], 'timestamps': []},
            'trial_pc': {'data': [], 'timestamps': []}
        }

        # Run the post processors.
        if self.config['trial_post_processing']:
            if not trial_processor:
                trial_processor = TrialProcessor()

            for config in self.config['trial_post_processing']:
                if config['name'] in trial_processor.post_processing.all:
                    trial_processor.post_processing.all[config['name']](self.proc_trial_data, config)

        return self.proc_trial_data
