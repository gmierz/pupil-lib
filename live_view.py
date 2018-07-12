import time
import numpy as np
import copy
from matplotlib import pyplot as plt
from pylsl import StreamInlet, resolve_stream, resolve_streams

plt.ion()
graph_offset = 10
scale_changes = 4
x_max_size = 1000
BLACKLIST = [
	"Gaze Python Representation",
	"Pupil Python Representation - Eye 0",
	"Pupil Python Representation - Eye 1",
	"Notifications"
]


def create_inlets(all_streams):
	all_inlets = {}
	for streamInfo in all_streams:
		name = streamInfo.name()
		if name in BLACKLIST:
			continue
		all_inlets[name] = {}
		all_inlets[name]['inlet'] = StreamInlet(streamInfo)
		all_inlets[name]['type'] = streamInfo.type()
		if 'Gaze' in name:
			all_inlets[name + '-x'] = {}
			all_inlets[name + '-y'] = {}
	return all_inlets


def destroy_inlets(all_inlets):
	for inlet in all_inlets:
		del inlet
	return []


def add_inlet_lines(all_inlets):
	for inletname in all_inlets:
		line, = ax.plot([0], [0], 'r-') # Returns a tuple of line objects, thus the comma
		all_inlets[inletname]['line'] = line


def main():
	print("Now viewing unsynchronized data streams.")
	while True:
		all_streams = resolve_streams(wait_time=2)
		if not all_streams:
			print("No streams found, pausing for 10 seconds...")
			time.sleep(10);

		print("Found the following streams:")
		for streamInfo in all_streams:
			print("\tName: " + streamInfo.name() + " Type: " + streamInfo.type())

		all_inlets = create_inlets(all_streams)

		# Prepare the live view figure
		fig = plt.figure()
		ax = fig.add_subplot(111)
		line_objs = []
		for inletname in all_inlets:
			line, = ax.plot([0], [0], 'r-') # Returns a tuple of line objects, thus the comma
			all_inlets[inletname]['line'] = line

		data_x_range = []
		marker_x_range = []
		marker_data = {}
		pupil_data = {}

		while all_streams:
			print("plotting")
			added_a_timestamp = False
			all_inlet_keys = all_inlets.keys()
			for inletname in all_inlet_keys:
				if inletname in BLACKLIST:
					continue
				if inletname.endswith('-x') or inletname.endswith('-y'):
					continue

				inlettype = all_inlets[inletname]['type']
				if inlettype not in ('Markers', 'Pupil Capture'):
					continue

				# Get some data from this stream
				inlet = all_inlets[inletname]['inlet']
				if inlettype == 'Markers':
					all_samples = inlet.pull_chunk(timeout=0.0, max_samples=100)
					samples, timestamps = all_samples
					if samples is None:
						continue
					if timestamps is None:
						continue
					if len(samples) == 0:
						continue
					time_correction_val = float(inlet.time_correction(timeout=60))

					for count, sample in enumerate(samples):
						sample = sample[0]
						if inletname not in marker_data:
							marker_data[inletname] = {}
						if sample not in marker_data[inletname]:
							marker_data[inletname][sample] = []
						marker_data[inletname][sample].append(float(timestamps[count]) + time_correction_val)
						marker_data[inletname][sample] = marker_data[inletname][sample][-x_max_size:]
						marker_x_range.append(float(timestamps[count]) + time_correction_val)
				elif inlettype == 'Pupil Capture':
					all_samples = inlet.pull_chunk(timeout=0.0, max_samples=100)
					samples, timestamps = all_samples
					if samples is None:
						continue
					if timestamps is None:
						continue
					if len(samples) == 0:
						continue

					diameter, confidence, timestamp, norm_pos_x, norm_pos_y = samples[0]

					if diameter != -1:
						if inletname not in pupil_data:
							pupil_data[inletname] = []
						diameter_list = [float(diameter) for diameter, _, _, _, _ in samples]
						pupil_data[inletname].extend(diameter_list)
						pupil_data[inletname] = pupil_data[inletname][-x_max_size:]
					else:
						x_inletname = inletname + '-x'
						y_inletname = inletname + '-y'
						if x_inletname not in pupil_data:
							pupil_data[x_inletname] = []
							if x_inletname not in all_inlets:
								line, = ax.plot([0], [0], 'r-')
								all_inlets[x_inletname]['line'] = line
						if y_inletname not in pupil_data:
							pupil_data[y_inletname] = []
							if y_inletname not in all_inlets:
								line, = ax.plot([0], [0], 'r-')
								all_inlets[y_inletname]['line'] = line
						normposx_list = [float(normposx) for _, _, _, normposx, _ in samples]
						normposy_list = [float(normposy) for _, _, _, _, normposy in samples]
						pupil_data[x_inletname].extend(normposx_list)
						pupil_data[y_inletname].extend(normposy_list)
						pupil_data[x_inletname] = pupil_data[x_inletname][-x_max_size:]
						pupil_data[y_inletname] = pupil_data[y_inletname][-x_max_size:]

					if not added_a_timestamp:
						if timestamps:
							data_x_range.extend(timestamps)
							data_x_range = data_x_range[-x_max_size:]
							added_a_timestamp = True
			if len(data_x_range) == 0:
				if len(marker_x_range) == 0:
					plt.pause(1)
					continue
				x_range = marker_x_range
			else:
				x_range = data_x_range

			ax.clear()
			ax.plot(x_range, [0 for x in x_range])
			min_y = 0
			max_y = 0
			# Make sure all the markers are within the bounds
			new_marker_data = {}
			for inletname, samples in marker_data.items():
				new_samples = {}
				for sample_name, sample in samples.items():
					new_samples[sample_name] = [ts for ts in sample if ts >= x_range[0]]
				new_marker_data[inletname] = new_samples
			marker_data = new_marker_data

			# Plot all the data
			for count, inletname in enumerate(pupil_data):
				mean_pd = np.mean(pupil_data[inletname])
				line = all_inlets[inletname]['line']
				line.set_xdata(x_range)

				# Remove the mean from the data
				line.set_ydata(count*graph_offset + scale_changes*(pupil_data[inletname] - mean_pd))
				line.set_label(inletname)
				tmp = count*graph_offset + (pupil_data[inletname] - mean_pd)
				min_y = min(min(tmp), min_y)
				max_y = max(max(tmp), max_y)
				plt.plot(x_range, tmp, label=inletname)
			print("Awfhlawhkf")
			# Plot all the markers
			for inletname in marker_data:
				for samplename, sample in marker_data[inletname].items():
					for ts in sample:
						line_data = np.linspace(min_y, max_y, num=(max_y-min_y))
						x_dat = [ts for i in range(len(line_data))]
						#ax.axvline(ts, ymin=label=samplename)
					print("on marker " + samplename)
					print(min_y)
					print(max_y)
					print(sample)
					for ts in sample:
						if ts >=max(x_range):
							print("still too high")
							continue
						ax.axvline(ts, min_y, max_y, label=samplename, linewidth=1.0, color='k')
						plt.text(ts, max_y/2, samplename, rotation=90, verticalalignment='center')

			# Draw everything
			ax.relim()
			ax.autoscale_view(True,True,True) 
			ax.legend(loc='upper left')
			fig.canvas.draw()
			plt.draw()
			plt.pause(0.0001)
			#plt.show(block=False)
			fig.canvas.flush_events()

			# Refresh what streams are available, and create and destroy the inlets
			# as needed.
			all_streams = resolve_streams()
			for streamInfo in all_streams:
				if streamInfo.name() not in all_inlets and streamInfo.name() not in BLACKLIST:
					print("couldn't find " + streamInfo.name())
					all_inlets = destroy_inlets(all_inlets)
					all_inlets = create_inlets(all_streams)

			plt.pause(0.1)
		plt.close('all')


if __name__=="__main__":
	main()
