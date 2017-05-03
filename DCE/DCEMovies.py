import DCETools
import DCEPlotter
import numpy as np
import sys

from DCEMovies_helper import remove_old_frames
from DCEMovies_helper import prep_save_worms_single, save_worms_single, prep_save_worms_double, save_worms_double
from DCEMovies_helper import get_info_manual, get_info_ideal, get_info_real

WAV_SAMPLE_RATE = 44100

def slide_window(txt_wave_file,
				 window_size=.5,    # seconds
				 step_size=.1,      # seconds
				 tau=10,
				 ds_rate=1,
				 max_frames=0,      # 0 for disabled
				 save_worms=True,
				 save_movie=True
				 ):

	if save_worms: prep_save_worms_single()


	remove_old_frames()

	worm_length = sum(1 for line in open(txt_wave_file))/WAV_SAMPLE_RATE
	num_frames = worm_length/step_size

	for i, start in enumerate(np.arange(0, worm_length, step_size)):
		print 'frame %i of %i' % (i, num_frames)

		embed_crop = [start, start + window_size]
		DCETools.embed(txt_wave_file, 'DCE/temp_data/embedded_coords.txt', embed_crop, tau, 2, WAV_SAMPLE_RATE, ds_rate=ds_rate)

		if save_worms: save_worms_single('{:d}-{}'.format(i, txt_wave_file), i,  tau, embed_crop)

		if save_movie: DCEPlotter.make_window_frame('DCE/temp_data/embedded_coords.txt', txt_wave_file, 'DCE/frames/frame%03d.png' % i, embed_crop, tau, i)

		if max_frames != 0 and i > max_frames: break


def vary_tau(txt_wave_file,
		tau_lims=(1, 15),
		tau_inc=1,
		embed_crop=(1, 2),
		ds_rate=1,
		save_worms=True,
		save_movie=True,
		m=2,
	 ):

	remove_old_frames()

	if save_worms: prep_save_worms_single()

	for i, tau in enumerate(np.arange(tau_lims[0], tau_lims[1], tau_inc)):
		print 'frame %i of %i' % (i + 1, int((tau_lims[1] - tau_lims[0]) / tau_inc))
		DCETools.embed(txt_wave_file, 'temp_data/embedded_coords.txt', embed_crop, tau, m, WAV_SAMPLE_RATE, ds_rate=ds_rate)

		if save_worms: save_worms_single('{:d}-{}'.format(i, txt_wave_file), i, tau, embed_crop)

		if save_movie: DCEPlotter.make_window_frame('temp_data/embedded_coords.txt', txt_wave_file, 'DCE/frames/frame%03d.png' % i, embed_crop, tau, i)


def compare_vary_tau(txt_wave_file1,
					 txt_wave_file2,
					 tau_lims,
					 tau_inc=1,
					 embed_crop=(1, 2),
					 ds_rate=1,
					 m=2,
					 save_worms=True,
					 save_movie=True
					 ):

	remove_old_frames()

	if save_worms: prep_save_worms_double()

	for i, tau in enumerate(np.arange(tau_lims[0], tau_lims[1], tau_inc)):
		print 'frame %i of %i' % (i + 1, int((tau_lims[1] - tau_lims[0]) / tau_inc))

		DCETools.embed(txt_wave_file1, 'temp_data/embedded_coords_comp1.txt', embed_crop, tau, m, WAV_SAMPLE_RATE, ds_rate=ds_rate)
		DCETools.embed(txt_wave_file2, 'temp_data/embedded_coords_comp2.txt', embed_crop, tau, m, WAV_SAMPLE_RATE, ds_rate=ds_rate)

		if save_worms: save_worms_double('{:d}-txt_wave_file1'.format(i), '{:d}-txt_wave_file2'.format(i), i, tau, tau, embed_crop)

		if save_movie: DCEPlotter.compare_vary_tau_frame('DCE/frames/frame%03d.png' % i, txt_wave_file1, txt_wave_file2, i, tau, embed_crop)



def compare_multi(
		dir1, dir1_base,
		dir2, dir2_base,
		tau,
		embed_crop=(1, 2),
		max_frames=89,
		m=2,
		ds_rate=1,
		save_worms=True,
		save_movie=True
	):
	"""makes frames for comparison movie: constant tau, constant, vary in files"""
	if save_worms: prep_save_worms_double()

	remove_old_frames()
	frame_idx = 0
	for i in xrange(1, max_frames):
		frame_idx += 1
		print 'frame', frame_idx
		filename1 = dir1 + "/%02d" % i + dir1_base
		filename2 = dir2 + "/%02d" % i + dir2_base

		DCETools.embed(filename1, 'temp_data/embedded_coords_comp1.txt', embed_crop, tau, m, WAV_SAMPLE_RATE, ds_rate=ds_rate)
		DCETools.embed(filename2, 'temp_data/embedded_coords_comp2.txt', embed_crop, tau, m, WAV_SAMPLE_RATE, ds_rate=ds_rate)

		if save_worms: save_worms_double(filename1, filename2, i, tau, tau, embed_crop)

		if save_movie: DCEPlotter.compare_multi_frame('DCE/frames/frame%03d.png' % frame_idx, filename1, filename2, i, tau, embed_crop)


def compare_multi_auto_tau(
		dir1, dir1_base,
		dir2, dir2_base,
		tau_T,
		tau_detect_f = True,
		embed_crop=(1, 2),
		i_lims=(1, 89),
		m=2,
		ds_rate=1,
		dpi=200,
		save_worms=True,
		save_movie=True
	):
	"""makes frames for comparison movie: proportional tau, constant, vary in files"""

	if save_worms: prep_save_worms_double()

	remove_old_frames()
	frame_idx = 0

	for i in xrange(i_lims[0], i_lims[1]):

		frame_idx += 1
		print 'frame', frame_idx
		filename1 = dir1 + "/%02d" % i + dir1_base
		filename2 = dir2 + "/%02d" % i + dir2_base

		if tau_detect_f:
			info = get_info_real(tau_T, embed_crop, i, ds_rate, WAV_SAMPLE_RATE, filename1, filename2)

			tau_1 = info['tau_1']
			tau_2 = info['tau_2']

			DCETools.embed(filename1, 'temp_data/embedded_coords_comp1.txt', embed_crop, tau_1, m, WAV_SAMPLE_RATE, ds_rate=ds_rate)
			DCETools.embed(filename2, 'temp_data/embedded_coords_comp2.txt', embed_crop, tau_2, m, WAV_SAMPLE_RATE, ds_rate=ds_rate)

			if save_worms: save_worms_double(filename1, filename2, i, tau_1, tau_2, embed_crop)

		else:
			info = get_info_ideal(tau_T, embed_crop, i, ds_rate, WAV_SAMPLE_RATE, filename1, filename2)
			tau = info['tau']

			DCETools.embed(filename1, 'temp_data/embedded_coords_comp1.txt', embed_crop, tau, m, WAV_SAMPLE_RATE, ds_rate=ds_rate)
			DCETools.embed(filename2, 'temp_data/embedded_coords_comp2.txt', embed_crop, tau, m, WAV_SAMPLE_RATE, ds_rate=ds_rate)

			if save_worms: save_worms_double(filename1, filename2, i, tau, tau, embed_crop)


		if save_movie: DCEPlotter.compare_multi_frame_new('DCE/frames/frame%03d.png' % frame_idx, filename1, filename2, i, embed_crop, info, dpi)

from PRFCompare.PRF import auto_crop


def compare_multi_auto(

		dir1, dir1_base,
		dir2, dir2_base,

		i_lims=(1, 89),

		embed_crop_1=(1, 2),    # seconds or 'auto'
		embed_crop_2=(1, 2),
		crop_auto_len=(.3),		# for when embed_crop = 'auto'

		tau='auto ideal',       # seconds 'auto detect' or 'auto ideal'
		tau_T=1/np.pi,          # tau_sec = period * tau_T

		save_worms=True,
		save_movie=True,

		ds_rate=1, dpi=200, m=2
	):
	"""makes frames for comparison movie: proportional tau, constant, vary in files"""

	if save_worms: prep_save_worms_double()

	remove_old_frames()
	frame_idx = 0

	for i in xrange(i_lims[0], i_lims[1]):

		frame_idx += 1
		print 'frame', frame_idx
		filename1 = dir1 + "/%02d" % i + dir1_base
		filename2 = dir2 + "/%02d" % i + dir2_base

		if isinstance(embed_crop_1, basestring):
			if embed_crop_1 == 'auto':
				crop_1 = auto_crop(np.loadtxt(filename1))
			else:
				print 'ERROR: embed_crop_1 not recognized.'
				crop_1 = None
		else: crop_1 = embed_crop_1

		if isinstance(embed_crop_2, basestring):
			if embed_crop_2 == 'auto':
				crop_2 = auto_crop(np.loadtxt(filename1))
			else:
				print 'ERROR: embed_crop_2 not recognized.'
				crop_2 = None
		else: crop_2 = embed_crop_2


		if not isinstance(tau, basestring):
			info = get_info_manual(tau, crop_1, crop_2, i, ds_rate, WAV_SAMPLE_RATE, filename1, filename2)
			tau_1 = tau_2 = info['tau']

		elif tau == 'auto detect':
			info = get_info_real(tau_T, crop_1, crop_2, i, ds_rate, WAV_SAMPLE_RATE, filename1, filename2)
			tau_1 = info['tau_1']
			tau_2 = info['tau_2']

		elif tau == 'auto ideal':
			info = get_info_ideal(tau_T, crop_1, crop_2, i, ds_rate, WAV_SAMPLE_RATE, filename1, filename2)
			tau_1 = tau_2 = info['tau']

		else:
			print 'ERROR: tau not recognized.'
			sys.exit()

		DCETools.embed(filename1, 'temp_data/embedded_coords_comp1.txt', embed_crop, tau_1, m, WAV_SAMPLE_RATE, ds_rate=ds_rate)
		DCETools.embed(filename2, 'temp_data/embedded_coords_comp2.txt', embed_crop, tau_2, m, WAV_SAMPLE_RATE, ds_rate=ds_rate)

		if save_worms: save_worms_double(filename1, filename2, i, tau_1, tau_2, embed_crop)

		if save_movie: DCEPlotter.compare_multi_frame_new('DCE/frames/frame%03d.png' % frame_idx, filename1, filename2, i, embed_crop, info, dpi)


