import os
import sys
import subprocess
import numpy as np
import itertools

import TestingFunctions

# import matplotlib
# matplotlib.rcParams['gray'] = True

from matplotlib import collections
import matplotlib.pyplot as pyplot
import matplotlib.markers

from matplotlib import animation


def remove_old_frames():
	dir = 'PH/frames'
	for f in os.listdir(dir):
		if f.endswith(".png"):
			os.remove(dir + f)


def get_simplex_color(scheme, past_birth_time, present_birth_time, max_birth_time):
	"""helper for plot_complex()"""
	if scheme == 'none':
		facecolor = 'lightblue'
		edgecolor = 'black'

	elif scheme == 'highlight new':
		if past_birth_time == present_birth_time:
			facecolor = 'red'
			edgecolor = 'firebrick'
		else:
			facecolor = 'lightblue'
			edgecolor = 'black'

	elif hasattr(scheme, '__len__') and scheme[0] == 'birth time gradient':
		cycles = scheme[1]
		prog = divmod(((past_birth_time / float(max_birth_time)) * cycles), 1)[1] # modulo 1
		facecolor = (1, prog, 1 - prog)
		edgecolor = (.5, prog, 1 - prog)

	else:
		print 'error:', scheme, 'is not a valid color scheme'
	return facecolor, edgecolor


def add_title(subplot, title_block_info, i):
	in_file_name = title_block_info[0]
	out_file_name = title_block_info[1]
	parameter_set = title_block_info[2]
	color_scheme = title_block_info[3]
	camera_angle = title_block_info[4]
	alpha = title_block_info[5]
	dpi = title_block_info[6]
	max_frames = title_block_info[7]
	hide_1simplexes = title_block_info[8]

	subplot.axis('tight')
	subplot.axis('off')
	# subplot.set_xticks([])
	subplot.set_xlim([0,1])
	subplot.set_ylim([0,1])

	row_height = .025
	font_size = 6

	title_table = subplot.table(
		cellText = [[in_file_name.split('/')[-1]],   # remove leading "datasets/"
					[out_file_name.split('/')[-1]]],
		bbox=[0, .9, 1, .05 * 2],    # x0, y0, width, height
		cellLoc='center'
	)
	title_table.auto_set_font_size(False)
	title_table.set_fontsize(8)

	param_data = np.array([[key, parameter_set[key]] for key in parameter_set.keys()])
	num_rows = len(param_data)
	h = num_rows * row_height
	param_table = subplot.table(
		cellText=param_data,
		colWidths=[1.5, .5],
		bbox=[0, 0, 1, h], # x0, y0, width, height
	)
	param_table.auto_set_font_size(False)
	param_table.set_fontsize(6)

	return title_table, param_table   # for init()


def update_time_table(time_plot, i, filtration):

	epsilons = filtration.epsilons
	e = epsilons[i]
	time_table = time_plot.table(
		cellText= [['$\epsilon$', '{:.6f}'.format(e)]],
		bbox=[.15, .8, .7, .05],    # x0, y0, width, height
		colWidths=[.5, 1],
		cellLoc='center',

		animated=True,
	)
	time_table.auto_set_font_size(False)
	time_table.set_fontsize(8)

	return time_table,


def make_frames_3D(filt_data, title_block_info, color_scheme, alpha, camera_angle, hide_1simplexes):
	from mayavi import mlab
	# TODO: Call via funcanimation() to improve performance, fix 1simplexes

	def plot_witnesses(witness_data):
		x = witness_data[:, 0]
		y = witness_data[:, 1]
		z = witness_data[:, 2]
		mlab.points3d(x, y, z, mode='point', color=(0, 0, 0))

	def plot_landmarks(landmark_data):
		x = landmark_data[:, 0]
		y = landmark_data[:, 1]
		z = landmark_data[:, 2]
		mlab.points3d(x, y, z, scale_factor=.02, color=(0, .7, 0))

	def plot_complex(complex_data, current_birth_time, landmark_data):  # how to specify color per simplex??
		"""plots plots all simplices with birth time =< birth_time"""
		max_birth_time = len(complex_data) - 1
		birth_time = 0
		while birth_time < current_birth_time:
			# color = get_simplex_color_3D(color_scheme, birth_time, current_birth_time, max_birth_time, landmark_data)
			# color = ((<float> for id in triangle_ID) for triangle_ID in triangle_IDs)
			# then, in triangular_mesh(...., scalers=color)

			color = get_simplex_color(color_scheme, birth_time, current_birth_time, max_birth_time)

			triangle_IDs =  complex_data[1][birth_time]
			x = landmark_data[:, 0]
			y = landmark_data[:, 1]
			z = landmark_data[:, 2]
			mlab.triangular_mesh(x, y, z, triangle_IDs, color=color, opacity=alpha, representation='surface')
			mlab.triangular_mesh(x, y, z, triangle_IDs, color=(0, 0, 0), representation='wireframe')

			if hide_1simplexes == False:
				lines = complex_data[0][birth_time]
				for simplex_IDs in lines:
					ID_coords = np.array([landmark_data[simplex_IDs[0]], landmark_data[simplex_IDs[1]]])
					x = ID_coords[:, 0]
					y = ID_coords[:, 1]
					z = ID_coords[:, 2]
					mlab.plot3d(x, y, z, tube_radius=None, color=(0,0,0))
					# mlab.pipeline.line_source(x, y, z, figure=fig)

			birth_time += 1

	if sys.platform != 'darwin':
		mlab.options.offscreen = True

	def make_frame(filt_plot, title_plot,birth_time):
		mlab.figure(bgcolor=(1, 1, 1), size=(800, 800))
		mlab.view(azimuth=camera_angle[0], elevation=camera_angle[1],focalpoint='auto', distance='auto')

		update_time_table(title_plot, i)

		plot_witnesses(filt_data[0])
		plot_landmarks(filt_data[1])
		plot_complex(filt_data[2], birth_time, filt_data[1])

		# mlab.savefig(filename='frames/sub_img%03d.png' % i)
		screenshot = mlab.screenshot(antialiased=True)

		filt_plot.imshow(screenshot)
		filt_plot.xaxis.set_ticks([])
		filt_plot.yaxis.set_ticks([])

		mlab.close()


	title_plot = pyplot.subplot2grid((3, 4), (0, 0), rowspan=3, colspan=1)
	add_title(title_plot, title_block_info, 0)

	filt_plot = pyplot.subplot2grid((3, 4), (0, 1), rowspan=3, colspan=3)
	filt_plot.set_aspect('equal')

	for i in xrange(len(filt_data[2][1])):
		print 'frame', i
		make_frame(filt_plot,title_plot, i)
		pyplot.savefig('frames/image%03d.png' % i)


def make_frames_2D(filtration, title_block_info, color_scheme, alpha, save_frames):
	def plot_witnesses(subplot, attractor_data):
		attractor_data = np.array(attractor_data)
		x = attractor_data[:, 0]
		y = attractor_data[:, 1]
		return subplot.scatter(x, y, color='black', marker=matplotlib.markers.MarkerStyle(marker='o', fillstyle='full'), facecolor='black', s=.1)

	def plot_landmarks(subplot, landmark_data):
		landmark_data = np.array(landmark_data)
		x = landmark_data[:, 0]
		y = landmark_data[:, 1]
		return subplot.scatter(x, y, color='darkblue', s=35)

	def plot_complex(subplot, i):
		"""plots all complexes for full filtration"""
		patches = []
		for j, simplexes_coords in enumerate(complex_data[:i + 1]):

			f_color, e_color = get_simplex_color(color_scheme, j, i, len(complex_data))
			simplexes = collections.PolyCollection(simplexes_coords, edgecolors=e_color, facecolors=f_color, lw=1, alpha=alpha, animated=True, antialiased=True, zorder=0)
			patches.append(subplot.add_collection(simplexes))
		return patches


	title_block = pyplot.subplot2grid((3, 4), (0, 0), rowspan=3, colspan=1)
	add_title(title_block, title_block_info, 0)

	filt_plot = pyplot.subplot2grid((3, 4), (0, 1), rowspan=3, colspan=3)
	filt_plot.set_aspect('equal')

	# IDA paper formatting #
	# filt_plot.tick_params(labelsize=23)
	# filt_plot.xaxis.major.locator.set_params(nbins=5)
	# filt_plot.yaxis.major.locator.set_params(nbins=5)

	witness_data = filtration.witness_coords
	landmark_data = filtration.landmark_coords
	complex_data = filtration.get_complexes_mpl()

	def init():
		print 'initializing...'
		# title = add_title(title_block, title_block_info, 0)
		witnesses = plot_witnesses(filt_plot, witness_data)
		landmarks = plot_landmarks(filt_plot, landmark_data)
		ret_list = [witnesses, landmarks]
		# ret_list.extend(complexes)
		# ret_list.extend(title)
		return ret_list

	def animate(i):
		print 'frame', i
		ret_comp = plot_complex(filt_plot, i)
		ret_title = update_time_table(title_block, i, filtration)
		ret_list = list(ret_comp)
		ret_list.extend(ret_title)

		if save_frames: pyplot.savefig('frames/image%03d.png' % i)

		return ret_list

	return init, animate

import Utilities

def make_movie(
		filtration,
		out_filename,
		color_scheme='none',		  	# as of now, 'none', 'highlight new', or 'birth_time gradient'
		camera_angle=(135, 55),  		# for 3D mode. [azimuthal, elevation]
		alpha=1, 					 	# opacity (float, 0...1 : transparent...opaque)
		dpi=150,  						# dots per inch (resolution)
		max_frames=None,  				# cut off frame (for testing or when only interested in the beginning of a movie)
		hide_1simplexes=False,			# i need to find a way to optimize the plotting of 1-simplexes(lines) 3D plotting, as of now they slow mayavi significantly.
		save_frames=False,  			# save frames to /frames/ dir
		framerate=1						# number of frames per second. for a constant max_frames, higher framerate will make a shorter movie.

):

	# remove_old_frames()

	# Utilities.check_overwrite(out_filename)

	title_block_info = [filtration.filename, out_filename, filtration.params,
						color_scheme, camera_angle, alpha, dpi, max_frames, hide_1simplexes]

	fig = pyplot.figure(figsize=(9, 6), tight_layout=True, dpi=dpi)

	if filtration.ambient_dim == 2:
		print 'building movie...'
		init, animate = make_frames_2D(filtration, title_block_info, color_scheme, alpha, save_frames=save_frames)
		ani = animation.FuncAnimation(fig, animate, init_func=init, frames=filtration.num_div, blit=True, repeat=False)

		# FuncAnimation.save() uses pipes to send frames to ffmpeg, which is significantly faster than saving to png.
		# However the videos it creates do not work well if fps is low (~ 1) because it uses fps for the output framerate.
		# As a workaround, ani.save(fps=10) is used and then ffmpeg is called to reduce the speed of the video by a 10x

		# FuncAnimation.save() offers blitting, which should improve performance even further, but despite my best efforts
		# to configure it correctly, it doesn't make much any(?) difference in time-to-run. However, this may be a
		# consequence of all simplexes being hidden in the init function.

		print 'saving...'
		ani.save('output/PH/temp.mp4', fps=10)
		print 'correcting framerate...'

		subprocess.call(['ffmpeg', '-y', '-i',
						 'output/PH/temp.mp4',
						 '-filter:v', 'setpts={:d}*PTS'.format(int(10 / framerate)),
						 out_filename])

		os.remove('output/PH/temp.mp4')

	elif ambient_dim == 3:
		print "WARNING: 3D filtration movies have not yet been ported to matplotlib's FuncAnimation for performance."
		print "Response times may be impossibly long, especially for large 'max_filtration_param'."
		filt_data[2] = unpack_complex_data_3D(filt_data[2])
		make_frames_3D(filt_data, title_block_info, color_scheme, alpha, camera_angle, hide_1simplexes)
		TestingFunctions.frames_to_movie(out_file_name, framerate)
	else:
		print "ERROR: ambient_dim = {:d}. Check input filtration file."
		sys.exit()




def make_frame_3D(birth_time, camera_angle=(135, 55), hide_1simplexes=False, alpha=.7, color_scheme='none'):
	from mayavi import mlab
	ambient_dim, filt_data = load_data()

	def get_simplex_color(scheme, birth_time, current_birth_time, max_birth_time):
		"""helper for plot_complex()"""
		if scheme == 'none':
			color = (.4, .6, .8)
		elif scheme == 'highlight new':
			color = (1, 0, 0) if birth_time == current_birth_time - 1 else (0, 0, 1)
		elif scheme == 'birth_time gradient':
			prog = birth_time / float(max_birth_time)
			color = (0, prog, 1 - prog)
		else:
			print 'error:', scheme, 'is not a valid color scheme'
		return color

	def plot_witnesses(witness_data):
		x = witness_data[:, 0]
		y = witness_data[:, 1]
		z = witness_data[:, 2]
		s = np.ones(len(x)) * .005
		# mlab.points3d(x, y, z, mode='point', color=(0, 0, 0))
		mlab.points3d(x, y, z, s, mode='sphere', color=(0, 0, 0), scale_factor=1)


	def plot_landmarks(landmark_data):
		x = landmark_data[:, 0]
		y = landmark_data[:, 1]
		z = landmark_data[:, 2]
		mlab.points3d(x, y, z, scale_factor=.02, color=(0, 0, 1))

	def plot_complex(complex_data, current_birth_time, landmark_data):  # how to specify color per simplex??
		"""plots plots all simplices with birth time =< birth_time"""
		max_birth_time = len(complex_data) - 1
		birth_time = 0
		while birth_time < current_birth_time:
			# color = get_simplex_color_3D(color_scheme, birth_time, current_birth_time, max_birth_time, landmark_data)
			# color = ((<float> for id in triangle_ID) for triangle_ID in triangle_IDs)
			# then, in triangular_mesh(...., scalers=color)

			color = get_simplex_color(color_scheme, birth_time, current_birth_time, max_birth_time)

			triangle_IDs =  complex_data[1][birth_time]
			x = landmark_data[:, 0]
			y = landmark_data[:, 1]
			z = landmark_data[:, 2]


			mlab.triangular_mesh(x, y, z, triangle_IDs, color=color, opacity=alpha, representation='surface')
			mlab.triangular_mesh(x, y, z, triangle_IDs, color=(0, 0, 0), representation='wireframe')

			if hide_1simplexes == False:
				lines = complex_data[0][birth_time]
				for simplex_IDs in lines:
					ID_coords = np.array([landmark_data[simplex_IDs[0]], landmark_data[simplex_IDs[1]]])
					x = ID_coords[:, 0]
					y = ID_coords[:, 1]
					z = ID_coords[:, 2]
					mlab.plot3d(x, y, z, tube_radius=None, color=(0,0,0))
					# mlab.pipeline.line_source(x, y, z, figure=fig)

			birth_time += 1

	mlab.figure(bgcolor=(1, 1, 1), size=(1000, 1000))
	mlab.view(azimuth=camera_angle[0], elevation=camera_angle[1], focalpoint='auto', distance='auto')


	filt_data[2] = unpack_complex_data_3D(filt_data[2])

	plot_witnesses(filt_data[0])
	plot_landmarks(filt_data[1])
	plot_complex(filt_data[2], birth_time, filt_data[1])


	# mlab.savefig(filename='frames/sub_img%03d.png' % i)   # for debugging
	mlab.show()




if __name__ == '__main__':
	pass