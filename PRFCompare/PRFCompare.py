from __future__ import division
import time
import subprocess
import os
import sys
from sys import platform
import itertools
import numpy as np
from os import system, chdir

from math import ceil

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.axes_grid1 import make_axes_locatable


from DCE.DCE import embed
from DCE.Plotter import plot_waveform, plot_waveform_zoom
from DCE.Tools import auto_tau

from PH.Data import Filtration
from PH.Plots import make_PD, make_PRF_plot
from PH.FiltrationMovie import make_movie

from DCE.Tools import auto_crop

from PH.TitleBox import add_filt_params_table, add_filenames_table

from PH.Plots import plot_heatmap

WAV_SAMPLE_RATE = 44100.


def clear_old_files(path, see_samples):
	old_files = os.listdir(path)
	if old_files and see_samples:
		ans = raw_input('Clear old files in ' + path + '? (y/n/q) \n')
		if ans == 'y':
			for f in old_files:
				if f != '.gitkeep':
					os.remove(path + f)
		elif ans == 'q':
			print 'goodbye'
			sys.exit()
		else:
			print 'Proceeding... conflicting files will be overwritten, otherwise old files will remain. \n'


def norm(f, metric, f_weight):

	PRF_res = len(f)
	dA = 2. / (PRF_res ** 2)		# normalize such that area of PRF domain is 1
	f_weight = f_weight(*np.meshgrid(np.linspace(0, 1, PRF_res), np.linspace(0, 1, PRF_res)))

	if metric == 'L1':
		return np.nansum(np.multiply(np.abs(f), f_weight)) * dA

	elif metric == 'L2':
		return np.sqrt(np.nansum(np.multiply(np.power(f, 2), f_weight))) * dA

	else:
		print "ERROR: metric not recognized. Use 'L1' or 'L2'."
		sys.exit()



def scale_dists(dists, norms, norm_ref, scale):
	""" helper for get_dists_from_ref """
	if scale == 'none':
		return dists

	elif scale == 'a':
		return np.true_divide(dists, norms)

	elif scale == 'b':
		return np.true_divide(dists, norm_ref)

	elif scale == 'a + b':
		return np.true_divide(dists, np.add(norms, norm_ref))

	else:
		print "ERROR: dist_scale '" + scale + "' is not recognized. Use 'none', 'a', 'b', or 'a + b'."
		sys.exit()



def get_dists_from_ref(funcs, ref_func, weight_func, metric, scale):
	dists = [norm(np.subtract(f, ref_func), metric, weight_func) for f in funcs]
	norms = [norm(f, metric, lambda i, j: 1) for f in funcs]
	norm_ref = [norm(ref_func, metric, lambda i, j: 1)] * len(dists)
	return scale_dists(dists, norms, norm_ref, scale)



def get_PRFs(
		filename, filt_params, crop_cmd, tau_cmd,
		PRF_res,
		auto_crop_length,
		time_units,
		normalize_volume,
		mean_samp_num,
		num_windows,
		window_size,
		see_samples,
		note_index,
		tau_T,
		fname=None
		):

	def show_samples(filt, i, filename):
		base_name = filename.split('/')[-1].split('.')[0]
		comp_name = '{:s}_{:d}_'.format(base_name, i)
		PD_filename = 'output/PRFCompare/mean/see_samples/' + comp_name + 'PD.png'
		PRF_filename = 'output/PRFCompare/mean/see_samples/' + comp_name + 'PRF.png'
		movie_filename = 'output/PRFCompare/mean/see_samples/' + comp_name + 'movie.mp4'

		make_PD(filt, PD_filename)
		make_PRF_plot(filt, PRF_filename, PRF_res=PRF_res)
		make_movie(filt, movie_filename)


	def crop_sig(sig_full, crop_cmd, auto_crop_len):

		crop = auto_crop(crop_cmd, sig_full, auto_crop_length, time_units=time_units)  # returns crop in seconds

		sig = sig_full[int(crop[0] * WAV_SAMPLE_RATE): int(crop[1] * WAV_SAMPLE_RATE)]

		if normalize_volume: sig = sig / np.max(sig)
		return crop, sig_full, sig


	def slice_sig(sig):
		if mean_samp_num > num_windows:
			print 'ERROR: mean_samp_num may not exceed num_windows'
			sys.exit()
		start_pts = np.floor(np.linspace(0, len(sig) - 1, num_windows, endpoint=False)).astype(int)
		windows = [np.asarray(sig[pt:pt + window_size_samp]) for pt in start_pts]
		# TODO: add normalize sub volume here
		return windows


	def embed_sigs(windows, tau):
		worms = []
		for window in windows:
			embed(window, 'PRFCompare/temp_data/temp_worm.txt', False, tau, 2)
			worm = np.loadtxt('PRFCompare/temp_data/temp_worm.txt')
			worms.append(worm)
		return worms


	def get_filtrations(worms, filename):
		print 'building filtrations'
		filts = []
		for i, worm in enumerate(worms):
			print '\n============================================='
			print filename.split('/')[-1], 'worm #', i
			print '=============================================\n'

			filt = (Filtration(worm, filt_params, filename=filename))
			filts.append(filt)

			if see_samples:
				if i % see_samples == 0:
					show_samples(filt, i, filename)

		return filts


	def get_funcs(filts, filename):
		funcs = []
		for i, filt in enumerate(filts):
			print '\n============================================='
			print filename.split('/')[-1], 'worm #', i
			print '=============================================\n'
			funcs.append(filt.get_PRF(PRF_res))
		return np.asarray(funcs)




	# ===========================================================================
	# 		MAIN: get_PRFs()
	# ===========================================================================

	if window_size:
		window_size_samp = window_size if time_units == 'samples' else int(window_size * WAV_SAMPLE_RATE)
		filt_params.update({'worm_length': window_size_samp})
	else:
		window_size_samp = filt_params['worm_length']

	if isinstance(filename, basestring):
		print 'loading', filename, '...'
		sig = np.loadtxt(filename)
	else:
		sig = filename
		filename=fname

	print 'cropping...'
	crop, sig_full, sig = crop_sig(sig, crop_cmd, auto_crop_length)
	print 'tauing...'
	f_ideal, f_disp, tau = auto_tau(tau_cmd, sig, note_index, tau_T, None, filename)


	sigs = slice_sig(sig)
	if type(sig[0]) is np.ndarray:
		dim = len(sig[0])
		print 'Input dimension: ' + str(dim) + '. Skipping embedding, dropping coords for time series.'
		worms = sigs
		sig_full = sig_full[:, 0]
	elif type(sig[0] is np.float64):
		dim = 1
		print 'Input dimension: ' + str(dim) + '. Embedding signals...'
		worms = embed_sigs(sigs, tau)

	filts = get_filtrations(worms, filename)
	funcs = get_funcs(filts, filename)

	return crop, sig_full, sig, np.asarray(funcs)



def dists_compare(
		filename_1,
		filename_2,
		out_filename,
		filt_params,

		load_saved_PRFs=False,

		time_units='seconds',

		crop_1='auto',
		crop_2='auto',
		auto_crop_length=.3,

		window_size=None,
		num_windows=10,  # per file
		mean_samp_num=5,  # per file

		tau_1=.001,
		tau_2=.001,
		tau_T=np.pi,
		note_index=None,  #

		normalize_volume=True,

		PRF_res=50,  # number of divisions used for PRF
		dist_scale='none',  # 'none', 'a', or 'a + b'
		metric='L2',  # 'L1' (abs) or 'L2' (euclidean)
		weight_func=lambda i, j: 1,

		see_samples=5

):

	clear_old_files('output/PRFCompare/mean/see_samples/', see_samples)

	crop_1_cmd, crop_2_cmd = crop_1, crop_2
	tau_1_cmd, tau_2_cmd = tau_1, tau_2

	if load_saved_PRFs:
		print 'WARNING: loading saved filtration'
		crop_1, sig_1_full, sig_1, funcs_1 = np.load('PRFCompare/funcs_1.npy')
		crop_2, sig_2_full, sig_2, funcs_2 = np.load('PRFCompare/funcs_2.npy')
	else:
		options = [
			PRF_res,
			auto_crop_length,
			time_units,
			normalize_volume,
			mean_samp_num,
			num_windows,
			window_size,
			see_samples,
			note_index,
			tau_T
		]
		crop_1, sig_1_full, sig_1, funcs_1 = get_PRFs(filename_1, filt_params, crop_1_cmd, tau_1_cmd, *options)
		crop_2, sig_2_full, sig_2, funcs_2 = get_PRFs(filename_2, filt_params, crop_2_cmd, tau_2_cmd, *options)
		np.save('PRFCompare/funcs_1.npy', (crop_1, sig_1_full, sig_1, funcs_1))
		np.save('PRFCompare/funcs_2.npy', (crop_2, sig_2_full, sig_2, funcs_2))

	funcs_1_z = funcs_1[:, 2]
	funcs_2_z = funcs_2[:, 2]

	mean_1_funcs_z = funcs_1_z[::int(ceil(num_windows / mean_samp_num))]
	mean_2_funcs_z = funcs_2_z[::int(ceil(num_windows / mean_samp_num))]

	funcs_1_avg_z = np.mean(mean_1_funcs_z, axis=0)
	funcs_2_avg_z = np.mean(mean_2_funcs_z, axis=0)

	dists_1_vs_1 = get_dists_from_ref(funcs_1_z, funcs_1_avg_z, weight_func, metric, dist_scale)
	dists_2_vs_1 = get_dists_from_ref(funcs_2_z, funcs_1_avg_z, weight_func, metric, dist_scale)
	dists_1_vs_2 = get_dists_from_ref(funcs_1_z, funcs_2_avg_z, weight_func, metric, dist_scale)
	dists_2_vs_2 = get_dists_from_ref(funcs_2_z, funcs_2_avg_z, weight_func, metric, dist_scale)


	# for plotting ref PRFs #
	ref_func_1 = funcs_1[0]  # get xx, yy
	ref_func_2 = funcs_2[0]  # get xx, yy
	ref_func_1[2] = funcs_1_avg_z
	ref_func_2[2] = funcs_2_avg_z


	arr = [
		[sig_1_full, sig_2_full],
		[crop_1, crop_2],
		[sig_1, sig_2],
		[ref_func_1, ref_func_2],
		[dists_1_vs_1, dists_2_vs_1, dists_1_vs_2, dists_2_vs_2]
	]

	return arr



def plot_dists_vs_ref(
		dir, base_filename,
		fname_format,
		out_filename,
		filt_params,

		i_ref=15,
		i_arr=np.arange(10, 20, 1),

		weight_func=lambda i, j: 1,

		metric='L2',  # 'L1' (abs) or 'L2' (euclidean)
		dist_scale='none',  # 'none', 'a', or 'a + b'

		PRF_res=50,  # number of divisions used for PRF

		load_saved_PRFs=False,

		see_samples=5,
):
	""" plots distance from reference rank function over a range of trajectories input files"""

	def plot_distances(i_ref, i_arr, dists, out_filename):
		fig = plt.figure(figsize=(10, 5))
		ax = fig.add_subplot(111)
		ax.plot(i_arr, dists)
		ax.axvline(x=i_ref, linestyle='--', color='k')
		ax.set_xlabel('$tau \quad (samples)$')
		# ax.set_ylabel('$distance \quad ({\epsilon}^2 \; \# \; holes)$')
		ax.set_ylabel('$distance$')
		ax.xaxis.set_ticks(i_arr[::2])
		ax.grid()
		ax.set_ylim(bottom=0)
		title = ax.set_title(base_filename + ' PRF distances')
		title.set_position([.5, 1.05])
		plt.savefig(out_filename)
		plt.close(fig)

	def get_in_filename(i):
		if fname_format == 'i base':
			filename = '{}/{}{}'.format(dir, i, base_filename)
		elif fname_format == 'base i':
			filename = '{}/{}{}.txt'.format(dir, base_filename, i)
		else:
			print "ERROR: invalid fname_format. Valid options: 'i base', 'base i'"
			sys.exit()
		return filename

	def show_samples(filt, i, ref=False):
		base_name = base_filename.split('/')[-1].split('.')[0]
		comp_name = '{:s}_{:d}_'.format(base_name, i)
		if ref: comp_name += '_REFERENCE_'
		PD_filename = 'output/PRFCompare/ref/see_samples/' + comp_name + 'PD.png'
		movie_filename = 'output/PRFCompare/ref/see_samples/' + comp_name + 'movie.mp4'
		PRF_filename = 'output/PRFCompare/ref/see_samples/' + comp_name + 'PRF.png'

		make_PD(filt, PD_filename)
		make_PRF_plot(filt, PRF_filename)
		make_movie(filt, movie_filename)


	def get_PRFs():
		funcs = []
		for i in i_arr:
			filename = get_in_filename(i)
			print '\n=================================================='
			print filename
			print '==================================================\n'
			filt = Filtration(filename, filt_params)
			func = filt.get_PRF(PRF_res)
			funcs.append(func)

			if see_samples:
				if i % see_samples == 0:
					show_samples(filt, i)

		return np.asarray(funcs)

	# ===================================================== #
	# 				MAIN:	plot_dists_vs_ref()				#
	# ===================================================== #

	clear_old_files('output/PRFCompare/ref/see_samples/', see_samples)

	if load_saved_PRFs:
		print 'WARNING: loading saved filtration'
		funcs = np.load('PRFCompare/funcs.npy')
		ref_func = np.load('PRFCompare/ref_func.npy')
	else:
		funcs = get_PRFs()  # also makes PDs and movies
		ref_filt = Filtration(get_in_filename(i_ref), filt_params)
		if see_samples: show_samples(ref_filt, i_ref, ref=True)
		ref_func = ref_filt.get_PRF(PRF_res)
		np.save('PRFCompare/funcs.npy', funcs)
		np.save('PRFCompare/ref_func.npy', ref_func)

	make_PRF_plot(
		ref_func,
		'output/PRFCompare/ref/PRF_REFERENCE.png',
		params=filt_params,
		in_filename='REF'
	)

	funcs_z = funcs[:, 2]
	ref_func_z = ref_func[2]
	dists = get_dists_from_ref(funcs_z, ref_func_z, weight_func, metric, dist_scale)
	plot_distances(i_ref, i_arr, dists, out_filename)



def plot_dists_vs_means(*args, **kwargs):		# see dists_compare for arg format

	def plot():
		def plot_dists_pane(ax, d, mean, crop):
			t = np.linspace(crop[0], crop[1], num_windows, endpoint=False)
			ticks = np.linspace(crop[0], crop[1], num_windows + 1, endpoint=True)
			offset = (t[1] - t[0]) / 2
			ax.plot(t + offset, d, marker='o', linestyle='None', ms=10, zorder=3)
			ax.axhline(y=mean, linestyle='--', color='forestgreen', lw=2)
			ax.grid(axis='x')
			ax.set_xticks(ticks)

		print 'plotting distances...'

		d_1_vs_1, d_2_vs_1, d_1_vs_2, d_2_vs_2 = dists
		crop_1, crop_2 = crops
		sig_1_full, sig_2_full = sigs_full
		sig_1, sig_2 = sigs

		fig = plt.figure(figsize=(18, 9), tight_layout=True)

		mean_1 = np.mean(d_1_vs_1)
		mean_2 = np.mean(d_2_vs_1)
		mean_3 = np.mean(d_1_vs_2)
		mean_4 = np.mean(d_2_vs_2)

		ax1 = fig.add_subplot(421)
		plot_dists_pane(ax1, d_1_vs_1, mean_1, crop_1)
		plt.setp(ax1.get_xticklabels(), visible=False)
		plt.setp(ax1.get_xticklines(), visible=False)
		ax1.set_ylim(bottom=0)

		ax2 = fig.add_subplot(422, sharey=ax1)
		plot_dists_pane(ax2, d_2_vs_1, mean_2, crop_2)
		plt.setp(ax2.get_yticklabels(), visible=False)
		# plt.setp(ax2.get_yticklines(), visible=False)
		plt.setp(ax2.get_xticklabels(), visible=False)
		plt.setp(ax2.get_xticklines(), visible=False)

		ax3 = fig.add_subplot(423, sharey=ax1, sharex=ax1)
		plot_dists_pane(ax3, d_1_vs_2, mean_3, crop_1)
		plt.setp(ax3.get_xticklabels(), visible=False)
		plt.setp(ax3.get_xticklines(), visible=False)

		ax4 = fig.add_subplot(424, sharey=ax1, sharex=ax2)
		plot_dists_pane(ax4, d_2_vs_2, mean_4, crop_2)
		plt.setp(ax4.get_yticklabels(), visible=False)
		# plt.setp(ax4.get_yticklines(), visible=False)

		plt.setp(ax4.get_xticklabels(), visible=False)
		plt.setp(ax4.get_xticklines(), visible=False)

		ax5 = fig.add_subplot(425, sharex=ax1)
		plot_waveform_zoom(ax5, None, crop_1, time_units=time_units, sig=sig_1)
		ax5.grid(axis='x', zorder=0)
		plt.setp(ax5.get_yticklabels(), visible=False)
		plt.setp(ax5.get_yticklines(), visible=False)



		ax6 = fig.add_subplot(426, sharex=ax2)
		plot_waveform_zoom(ax6, None, crop_2, time_units=time_units, sig=sig_2)
		ax6.grid(axis='x', zorder=0)
		plt.setp(ax6.get_yticklabels(), visible=False)
		plt.setp(ax6.get_yticklines(), visible=False)

		ylim = np.max(np.abs(np.append(ax5.get_ylim(), ax6.get_ylim())))
		ax5.set_ylim(-ylim, ylim)
		ax6.set_ylim(-ylim, ylim)

		ax7 = fig.add_subplot(427)
		plot_waveform(ax7, sig_1_full, crop_1, time_units=time_units)
		plt.setp(ax7.get_yticklabels(), visible=False)
		plt.setp(ax7.get_yticklines(), visible=False)

		ax8 = fig.add_subplot(428, sharey=ax7)
		plot_waveform(ax8, sig_2_full, crop_2, time_units=time_units)
		plt.setp(ax8.get_yticklabels(), visible=False)
		plt.setp(ax8.get_yticklines(), visible=False)

		ax1.set_title(filename_1.split('/')[-1])
		ax2.set_title(filename_2.split('/')[-1])

		del_12 = mean_2 - mean_1
		del_34 = mean_4 - mean_3

		ax1.set_ylabel(
			'\n \n ref: ' + filename_1.split('/')[-1].split('.')[0] + ' \n \n $\Delta$: {:.3f}'.format(del_12),
			rotation=0, size='large', labelpad=50)
		ax3.set_ylabel(
			'\n \n ref: ' + filename_2.split('/')[-1].split('.')[0] + ' \n \n $\Delta$: {:.3f}'.format(del_34),
			rotation=0, size='large', labelpad=50)

		plt.savefig(out_filename)

		plt.close(fig)

	filename_1, filename_2, out_filename, filt_params = args
	time_units = kwargs['time_units']
	num_windows = kwargs['num_windows']
	PRF_res = kwargs['PRF_res']

	sigs_full, crops, sigs, refs, dists = dists_compare(*args, **kwargs)

	plot()

	base_filename_1 = filename_1.split('/')[-1].split('.')[0]
	base_filename_2 = filename_2.split('/')[-1].split('.')[0]
	out_fname_1 = 'output/PRFCompare/mean/' + base_filename_1 + '_mean_PRF.png'
	out_fname_2 = 'output/PRFCompare/mean/' + base_filename_2 + '_mean_PRF.png'
	ref_func_1, ref_func_2 = refs
	make_PRF_plot(ref_func_1, out_fname_1, params=filt_params, in_filename='MEAN: ' + base_filename_1, PRF_res=PRF_res)
	make_PRF_plot(ref_func_2, out_fname_2, params=filt_params, in_filename='MEAN: ' + base_filename_2, PRF_res=PRF_res)



def plot_clusters(*args, **kwargs):

	filename_1, filename_2, out_filename,filt_params = args

	sigs_full, crops, sigs, refs, dists = dists_compare(*args, **kwargs)


	def plot():

		def add_filename_table(ax, filenames):
			ax.axis('off')
			filenames = [f.split('/')[-1] for f in filenames]  # remove leading "datasets/"
			arr = [
				['A', filenames[0]],
				['B', filenames[1]]
			]

			title_table = ax.table(
				cellText=arr,
				bbox=[0, 0, 1, 1],
				cellLoc='center',
				# rowColours=['C0', 'C1'],
				colWidths=[.5, 1]
			)

		print 'plotting clusters...'
		d_1_vs_1, d_2_vs_1, d_1_vs_2, d_2_vs_2 = dists

		fig = plt.figure(figsize=(10, 6), tight_layout=True)
		fname_ax = plt.subplot2grid((6, 10), (0, 0), rowspan=1, colspan=3)
		params_ax = plt.subplot2grid((6, 10), (2, 0), rowspan=4, colspan=3)
		plot_ax = plt.subplot2grid((6, 10), (0, 4), rowspan=6, colspan=6)

		add_filename_table(fname_ax, [filename_1, filename_2])
		add_filt_params_table(params_ax, filt_params)

		plot_ax.set_aspect('equal')
		plot_ax.set_xlabel('distance to A')
		plot_ax.set_ylabel('distance to B')

		A = [d_1_vs_1, d_1_vs_2]
		B = [d_2_vs_1, d_2_vs_2]
		plot_ax.scatter(*A, c='C0', label='A')
		plot_ax.scatter(*B, c='C1', label='B')

		plot_ax.legend()

		max_lim = np.max([plot_ax.get_xlim()[1], plot_ax.get_ylim()[1]])

		plot_ax.set_xlim([0, max_lim])
		plot_ax.set_ylim([0, max_lim])

		fig.savefig(out_filename)

	plot()


def plot_variance(
		filename,
		out_filename,
		filt_params,
		vary_param_1,
		vary_param_2,

		load_saved_PRFs=False,

		time_units='seconds',

		crop=(100, 1100),
		auto_crop_length=.3,

		num_windows=5,  # per file
		window_size=None,

		tau=.001,
		tau_T=np.pi,
		note_index=None,  #

		normalize_volume=True,

		PRF_res=50, 		 # number of divisions used for PRF
		dist_scale='none',	 # 'none', 'a', or 'a + b'
		metric='L2', 		 # 'L1' (abs) or 'L2' (euclidean)
		weight_func=lambda i, j: 1,

		see_samples=5
):
	mean_samp_num = num_windows
	if window_size:
		print 'ERROR: this function does not take window_size arg, please use worm_length filtration parameter instead'
		sys.exit()
	options = [PRF_res, auto_crop_length, time_units, normalize_volume, mean_samp_num, num_windows, window_size,
			   see_samples, note_index, tau_T]


	class VarianceData:  # all data for a fixed value of vary_param_2 -- one curve per plot
		def __init__(self):
			self.mean_PRF_norm = []
			self.variance = []
			self.scaled_variance = []
			self.pointwise_variance_norm = []
			self.functional_COV_norm = []

	def plot_trajectory(sig):
		print 'plotting trajectory...'
		fig = plt.figure(figsize=(7, 7))
		ax = fig.add_subplot(111)
		cbar = ax.scatter(sig[:,0], sig[:,1], s=.05, c=np.arange(sig.shape[0]))
		fig.colorbar(cbar)
		fig.savefig('output/PRFCompare/variance/trajectory.png')


	def get_data():

		if load_saved_PRFs:
			print 'WARNING: loading saved data'
			return np.load('PRFCompare/PRFs.npy')

		if vary_param_2:
			if vary_param_2[0] in filt_params:
				print 'loading', filename, '...'
				sig_full = np.loadtxt(filename)
				arr_2 = []
				for val_2 in vary_param_2[1]:
					filt_params.update({vary_param_2[0]: val_2})
					arr_1 = []
					for val_1 in vary_param_1[1]:
						print '============================================='
						print '============================================='
						print vary_param_1[0] + ':', val_1
						print vary_param_2[0] + ':', val_2
						print '============================================='
						print '=============================================\n'

						filt_params.update({vary_param_1[0]: val_1})

						# get PRFs at evenly spaced intervals along input -- 'prf evolution'
						ret_crop, sig_full, sig, prf_evo = get_PRFs(sig_full, filt_params, crop, tau, *options, fname=filename)
						# plot_trajectory(sig)
						# arr_1.append(prf_evo[:, 2])		# take z component only
						arr_1.append(prf_evo)
					arr_2.append(arr_1)

				prf_evos = np.asarray(arr_2)
				# array with shape (len(vary_param_2[1], len(vary_param_1[1])
				# each element is a 1D list of PRFs from regular samples of the input
				np.save('PRFCompare/PRFs.npy', prf_evos)
				return prf_evos

			else:
				print 'ERROR: currently vary_param_2 must be a filtration parameter'
				sys.exit()

	def process_data(prf_evo_array):
		print 'processing...'
		data_list = []
		for i, row in enumerate(prf_evo_array):  # for each value of vary_param_2

			data_val_2 = VarianceData()

			for j, sample_prfs in enumerate(row):	 # for each value of vary_param_1

				# see definitions for norm() and get_dists_from_ref() around lines 45 - 90

				sample_prfs_z = sample_prfs[:, 2]		# take z component only
				null_weight_func = lambda i, j: 1
				pointwise_mean = np.mean(sample_prfs_z, axis=0)					# plot as heatmap
				pmn = norm(pointwise_mean, metric, null_weight_func) 			# plot as data point
				data_val_2.mean_PRF_norm.append(pmn)

				# HOMEGROWN VARIANCE #

				dists = [norm(np.subtract(PRF, pointwise_mean), metric, weight_func) for PRF in sample_prfs_z]
				variance = np.mean(dists)										# plot as data point
				data_val_2.variance.append(variance)

				scaled_dists = get_dists_from_ref(sample_prfs_z, pointwise_mean, weight_func, metric, dist_scale)
				scaled_variance = np.mean(scaled_dists)							# plot as data point
				data_val_2.scaled_variance.append(scaled_variance)

				# POINTWISE VARIANCE #

				diffs = [PRF - pointwise_mean for PRF in sample_prfs_z]

				pointwise_variance = np.var(diffs, axis=0)						# plot as heatmap
				pvn = norm(pointwise_variance, metric, null_weight_func)		# plot as data point
				data_val_2.pointwise_variance_norm.append(pvn)

				functional_COV = pointwise_variance / pointwise_mean			# plot as heatmap
				fcovn = norm(functional_COV, metric, null_weight_func)			# plot as data point
				data_val_2.functional_COV_norm.append(fcovn)



				x, y, z, max_lim = sample_prfs[0]

				fig = plt.figure(figsize=(13, 5), tight_layout=True)
				ax1 = 		fig.add_subplot(131)
				ax2 = 		fig.add_subplot(132)
				ax3 = 		fig.add_subplot(133)
				divider = make_axes_locatable(ax3)
				c_ax = divider.append_axes('right', size='10%', pad=.2)

				plot_heatmap(ax1, c_ax, x, y, pointwise_mean)
				ax1.set_title('pointwise mean')
				plot_heatmap(ax2, c_ax, x, y, pointwise_variance)
				ax2.set_title('pointwise variance')
				plot_heatmap(ax3, c_ax, x, y, functional_COV)
				ax3.set_title('functional COV')

				fig.suptitle(filename.split('/')[-1])
				fname = '{}_{}__{}_{}.png'.format(vary_param_2[0], vary_param_2[1][i], vary_param_1[0], vary_param_1[1][j])
				fig.savefig('output/PRFCompare/variance/heatmaps/' + fname)
				plt.close(fig)



			data_list.append(data_val_2)

		return data_list

	def plot(data_list, out_filename):
		print 'plotting...'
		fig = plt.figure(figsize=(12, 8), tight_layout=True)

		label_kwargs = {
			'rotation': 0,
			'ha': 'right',
			'va': 'center',
			'labelpad': 10,
		}

		fname_ax = plt.subplot2grid((5, 10), (0, 0), rowspan=1, colspan=3)
		params_ax = plt.subplot2grid((5, 10), (1, 0), rowspan=4, colspan=3)

		ax1 = plt.subplot2grid((5, 10), (0, 3), colspan=6)
		ax2 = plt.subplot2grid((5, 10), (1, 3), colspan=6, sharex=ax1)
		ax3 = plt.subplot2grid((5, 10), (2, 3), colspan=6, sharex=ax1)
		ax4 = plt.subplot2grid((5, 10), (3, 3), colspan=6, sharex=ax1)
		ax5 = plt.subplot2grid((5, 10), (4, 3), colspan=6, sharex=ax1)

		add_filenames_table(fname_ax, [filename, out_filename])
		add_filt_params_table(params_ax, filt_params)

		ax1.set_ylabel('norm of mean', **label_kwargs)
		ax2.set_ylabel('variance', **label_kwargs)
		ax3.set_ylabel('scaled \nvariance', **label_kwargs)
		ax4.set_ylabel('norm of \npointwise \nvariance', **label_kwargs)
		ax5.set_ylabel('norm of \nfunctional COV', **label_kwargs)

		ax5.set_xlabel(vary_param_1[0])

		label_list = [vary_param_2[0] + ' = ' + str(val) for val in vary_param_2[1]]

		for i, val_2_data in enumerate(data_list):
			label = label_list[i]
			x = vary_param_1[1]
			ax1.plot(x, val_2_data.mean_PRF_norm, label=label)
			ax1.legend(loc=1)
			ax2.plot(x, val_2_data.variance)
			ax3.plot(x, val_2_data.scaled_variance)
			ax4.plot(x, val_2_data.pointwise_variance_norm)
			ax5.plot(x, val_2_data.functional_COV_norm)

		for ax in [ax1, ax2, ax3, ax4, ax5]:
			ax.grid()
			ax.set_ylim(bottom=0)

			if ax is not ax5:
				plt.setp(ax.get_xticklabels(), visible=False)
				plt.setp(ax.get_xticklines(), visible=False)

		fig.savefig(out_filename)




	# ===========================================================================
	# 		MAIN: plot_variance()
	# ===========================================================================


	prf_evo_array = get_data()
	variance_data = process_data(prf_evo_array)
	plot(variance_data, out_filename)


