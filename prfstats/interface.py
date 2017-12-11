import os
import numpy as np

from data import dists_to_ref, filt_set, distance, prf_set, NormalPRF
from _plot_variance.data import pointwise_stats, scaler_stats
from plots import dists_to_means_fig, clusters_fig, dists_to_ref_fig
from _plot_variance.plots import variance_fig, heatmaps_figs
from prfstats.helpers import parse_load_save_cmd
from prfstats.plots import weight_functions_figs, dual_roc_fig
from data import mean_dists_compare
from prfstats.data import L2Classifier, roc_data
from plots import samples as plot_samples
from signals import Trajectory
from utilities import print_title, clear_dir
from phomology import Filtration



def plot_dists_to_ref(
		path,
		out_filename,
		filt_params,
		i_ref,
		i_arr,
		weight_func=None,
		load_filts=False,
		save_filts=True,
		samples=False,
		quiet=True,

):
	"""
	Take a set of trajectories as text files with one specified as the
	reference, compute a prf for each, plot the L2 distance from each prf
	to the reference prf.

	Parameters
	----------
	path : str
		format-ready string. example: to use a set of files named
		``traj00.txt``, ``traj01.txt``, ``traj02.txt``, etc, located in
		``path/to/files``, use ``'path/to/files/traj{:02d}.txt'``
	out_filename : str
		path/filename for plot output
	filt_params : dict
		see :py:func:`phomology.build_filtration.build_filtration`
	i_ref : int
		the reference prf is generated from ``path.format(i_ref)``
	i_arr : array of ints
		prfs are generated from ``[path.format(i) for i in i_arr]``
	weight_func : lambda, optional
		weight function applied to all prfs before computing distances\n
		default : None
	load_filts : bool or str, optional
		If ``True``, loads filtration set generated by previous run. If a filename,
		loads filtration set from specified file.\n
		default: ``False``
	save_filts : bool or str, optional
		if ``True``, saves the filtration set such that ``load_filts=True``
		may	be used in subsequent runs.\n
		if a filename, saves filtration set to specified file.\n
		default: ``True``
	samples : dict or int, optional
		If of the form ``{'interval': i, 'filt_step': j}``, plots persistence
		diagram, persistence rank function, and ``j``-th step of filtration for
		every ``i``-th input file.
		If of the form ``{'interval': i}`` or simply ``i``, plots persistence
		diagram, persistence rank function, and full filtration movie for every
		``i``-th input file.\n
		These plots are saved to ``output/prfstats/samples/``\n
		default: ``False``
	quiet : bool, optional
		less terminal output\n
		default: ``True``

	Returns
	-------
	1-d array
		distances to reference prf

	"""
	if load_filts:
		if isinstance(load_filts, basestring):
			saved = np.load(load_filts)
		else:
			saved = np.load('prfstats/data/filts.npy')
		ref_filt, filts = saved

	else:
		filts = []
		for i in i_arr:
			fname = path.format(i)
			print_title(fname)
			traj = Trajectory(fname)
			filts.append(
				Filtration(traj, filt_params, silent=quiet, save=False)
			)
		ref_traj = Trajectory(path.format(i_ref))
		ref_filt = Filtration(ref_traj, filt_params, silent=quiet, save=False)
		if save_filts:
			if isinstance(save_filts, basestring):
				np.save(save_filts, [ref_filt, filts])
			else:
				np.save('prfstats/data/filts.npy', [ref_filt, filts])
	filts = np.array(filts)

	prfs = [NormalPRF(f.prf()) for f in filts]
	ref_prf = NormalPRF(ref_filt.prf())
	[prf.set_weight(weight_func) for prf in prfs + [ref_prf]]

	dists = dists_to_ref(prfs, ref_prf)
	base_filename = path.split('/')[-1]
	dists_to_ref_fig(base_filename, i_ref, i_arr, dists, out_filename)

	dir_ = 'output/prfstats/samples'
	if clear_dir(dir_):
		plot_samples(filts, samples, dir_)

	return dists


def plot_dists_to_means(
		traj1,
		traj2,
		out_filename,
		filt_params,
		weight_func=None,
		samples=False,
		load_filts=False,
		save_filts=True,
		quiet=True
	):
	"""
	Take two pre-windowed ``Trajectory``\ s, generate prf for all windows, find
	mean prf for each ``Trajecetory``, plot distances from prfs to mean prf.

	Parameters
	----------
	traj1: Trajectory
		Must be pre-windowed. This is accomplished by initializing with the
		 ``num_windows`` parameter, calling the ``slice`` method, or using
		 ``TimeSeries.embed()``.
	traj2: Trajectory
		see `traj1`
	out_filename: str
		Path/filename for plot output. Should probably end with ``.png``.
	filt_params: dict
		See :py:func:`phomology.build_filtration.build_filtration`
	weight_func: lambda, optional
		Weight function applied to all prfs before doing statistics\n
		default : ``None``
	load_filts : bool or 2-tuple of str, optional
		If ``True``, loads filtration sets generated by previous run. If a
		tuple of filenames, loads filtration sets from specified files.\n
		default: ``False``
	save_filts : bool or 2-tuple of str, optional
		If ``True``, saves the filtration sets such that ``load_filts=True``
		may	be used in subsequent runs. If a tuple of filenames, saves
		filtration sets to specified files.\n
		default: ``True``
	samples : dict or int, optional
		If of the form ``{'interval': i, 'filt_step': j}``, plots persistence
		diagram, persistence rank function, and jrd step of filtration for
		every ith input file. If of the form ``{'interval': i}`` or simply
		``i``, plots persistence diagram, persistence rank function, and full
		filtration movie for every ith input file.\n
		These plots are saved to ``output/prfstats/samples/``\n
		default: ``False``
	quiet : bool, optional
		less terminal output\n
		default: ``True``

	Returns
	-------
	2d array
		``[dists_1_vs_1, dists_2_vs_1, dists_1_vs_2, dists_2_vs_2]``
	"""

	load_cmd_1, load_cmd_2 = parse_load_save_cmd(load_filts)
	save_cmd_1, save_cmd_2 = parse_load_save_cmd(save_filts)

	filts1 = filt_set(
		traj1,
		filt_params,
		load=load_cmd_1,
		save=save_cmd_1,
		quiet=quiet,
	    fid=1
	)
	filts2 = filt_set(
		traj2,
		filt_params,
		load=load_cmd_2,
		save=save_cmd_1,
		quiet=quiet,
	    fid=2
	)

	prfs1 = prf_set(filts1, weight_func)
	prfs2 = prf_set(filts2, weight_func)

	refs, dists = mean_dists_compare(prfs1, prfs2)

	dists_to_means_fig(refs, dists, traj1, traj2, out_filename)

	dir_ = 'output/prfstats/samples'
	if clear_dir(dir_):
		plot_samples(filts1, samples, dir_)
		plot_samples(filts2, samples, dir_)

	return dists



def plot_clusters(
		traj1,
		traj2,
		out_filename,
		filt_params,
		weight_func=None,
		samples=False,
		load_filts=False,
		save_filts=True,
		quiet=True
):
	"""
	Just like :py:func:`plot_dists_to_means` except distances are plotted in a
	more succinct manner.
	"""

	load_cmd_1, load_cmd_2 = parse_load_save_cmd(load_filts)
	save_cmd_1, save_cmd_2 = parse_load_save_cmd(save_filts)

	filts1 = filt_set(
		traj1,
		filt_params,
		load=load_cmd_1,
		save=save_cmd_1,
		quiet=quiet,
		fid=1
	)
	filts2 = filt_set(
		traj2,
		filt_params,
		load=load_cmd_2,
		save=save_cmd_1,
		quiet=quiet,
		fid=2
	)

	prfs1 = prf_set(filts1, weight_func)
	prfs2 = prf_set(filts2, weight_func)

	refs, dists = mean_dists_compare(prfs1, prfs2)

	clusters_fig(dists, filt_params, traj1.name, traj2.name, out_filename)

	dir_ = 'output/prfstats/samples'
	if clear_dir(dir_):
		plot_samples(filts1, samples, dir_)
		plot_samples(filts2, samples, dir_)

	return dists


def plot_rocs(
		traj1, traj2,
		out_filename,
		filt_params,
		k,
		vary_param=None,
		weight_func=None,
		load_filts=False,
		save_filts=True,
		samples=False,
		quiet=True,
):
	"""
	Take two pre-windowed ``Trajectories``, generate prf for all windows, take
	half of prfs from each set of windows ('every other') to train two
	``L2Classifiers``s, use other half of prfs to test, report results as ROC
	curves.

	Parameters
	----------
	traj1: Trajectory
		Must be pre-windowed. This is accomplished by initializing with the
		 ``num_windows`` parameter, calling the ``slice`` method, or using
		 ``TimeSeries.embed()``.
	traj2: Trajectory
		see `traj1`
	out_filename: str
		Path/filename for plot output. Should probably end with ``.png``.
	filt_params: dict
		See :py:func:`phomology.build_filtration.build_filtration`
	k: 1-d array of float
		parameterizes true and false positive rates, determines thresholds
	weight_func: lambda, optional
		Weight function applied to all prfs before doing statistics\n
		default : ``None``
	vary_param: 2-tuple, optional
		``(p, (val1, val2, val3, ...)`` where ``p`` is a string -- either
		``'weight_func'`` or any filtration parameter
		(see :py:func:`build_filtration`)
		default: ``None``
	load_filts : bool or 2-tuple of str, optional
		If ``True``, loads filtration sets generated by previous run. If a
		tuple of filenames, loads filtration sets from specified files.\n
		default: ``False``
	save_filts : bool or 2-tuple of str, optional
		If ``True``, saves the filtration sets such that ``load_filts=True``
		may	be used in subsequent runs. If a tuple of filenames, saves
		filtration sets to specified files.\n
		default: ``True``
	samples : dict or int, optional
		If of the form ``{'interval': i, 'filt_step': j}``, plots persistence
		diagram, persistence rank function, and jrd step of filtration for
		every ith input file. If of the form ``{'interval': i}`` or simply
		``i``, plots persistence diagram, persistence rank function, and full
		filtration movie for every ith input file.\n
		These plots are saved to ``output/prfstats/samples/``\n
		default: ``False``
	quiet : bool, optional
		less terminal output\n
		default: ``True``

	Returns
	-------
	array
		roc data for both classifiers

	"""
	load_cmd_1, load_cmd_2 = parse_load_save_cmd(load_filts)
	save_cmd_1, save_cmd_2 = parse_load_save_cmd(save_filts)

	filts1 = filt_set(
		traj1,
		filt_params,
		vary_param,
		load=load_cmd_1,
		save=save_cmd_1,
		quiet=quiet,
	    fid=1
	)
	filts2 = filt_set(
		traj2,
		filt_params,
		vary_param,
		load=load_cmd_2,
		save=save_cmd_2,
		quiet=quiet,
		fid=2
	)


	prfs1 = prf_set(filts1, weight_func, vary_param)
	prfs2 = prf_set(filts2, weight_func, vary_param)

	data = []

	if vary_param is None: prfs1, prfs2 = [prfs1], [prfs2]
	for prfs1_, prfs2_ in zip(prfs1, prfs2):
		train1, test1 = prfs1_[1::2], prfs1_[::2]
		train2, test2 = prfs2_[1::2], prfs2_[::2]

		print 'training classifiers...'
		clf1 = L2Classifier(train1)
		clf2 = L2Classifier(train2)

		print 'running tests...'
		k_arr = np.arange(*k)
		roc1 = roc_data(clf1, test1, test2, k_arr)
		roc2 = roc_data(clf2, test2, test1, k_arr)

		data.append([roc1, roc2])

	dual_roc_fig(data, k, traj1, traj2, out_filename, vary_param)

	dir_ = 'output/prfstats/samples'
	if clear_dir(dir_):
		plot_samples(filts1, samples, dir_, vary_param)
		plot_samples(filts2, samples, dir_, vary_param)

	return data


def plot_variance(
		traj,
		out_filename,
		filt_params,
		vary_param_1,
		vary_param_2=None,
		legend_labels_1=None,       # ('axis', ('tick 1', 'tick2', 'tick3'))
		legend_labels_2=None,       # ('legend 1', 'legend 2', 'legend 3')
		weight_func=None,
		samples=False,
		quiet=True,
		annot_hm=False,
		load_filts=False,
		save_filts=True,
		heatmaps=True
):
	"""
	Take pre-windowed ``Trajectory``, compute prf for all windows for a range
	of one or two `vary_param`s, compute various statistics on prfs per
	vary_params, plot results.

	Parameters
	----------
	traj: Trajectory
		Must be pre-windowed. This is accomplished by initializing with the
		 ``num_windows`` parameter, calling the ``slice`` method, or using
		 ``TimeSeries.embed()``.
	out_filename: str
		Path/filename for plot output. Should probably end with ``.png``.
	filt_params: dict
		See :py:func:`phomology.build_filtration.build_filtration`
	vary_param_1: tuple
		``(p, (val1, val2, val3, ...)`` where ``p`` is a string -- either
		``'weight_func'`` or any filtration parameter
		(see :py:func:`build_filtration`)
	vary_param_2: tuple, optional
		see `vary_param_1`
		default: ``None``
	legend_labels_1: tuple of str, optional
		Labels for use when a vary_param_1 is ``'weight_func'`` or to
		otherwise override. \n
		``(('axis', ('tick 1', 'tick2', 'tick3'))``
	legend_labels_2: tuple of str, optional
		Labels for use when a vary_param_2 is ``'weight_func'``, or to
		otherwise override.\n
		``('legend 1', 'legend 2', 'legend 3')``
	weight_func: lambda, optional
		Weight function applied to all prfs before doing statistics\n
		default : ``None``
	samples: dict or int, optional
		If of the form ``{'interval': i, 'filt_step': j}``, plots persistence
		diagram, persistence rank function, and jrd step of filtration for
		every ith input file. If of the form ``{'interval': i}`` or simply
		``i``, plots persistence diagram, persistence rank function, and full
		filtration movie for every ith input file.\n
		These plots are saved to ``output/prfstats/samples/``\n
		default: ``False``
	quiet: bool, optional
		less terminal output\n
		default: True
	annot_hm: bool, optional
		Annotate heatmaps -- may be broken\n
		default: True
	load_filts : bool or 2-tuple of str, optional
		If ``True``, loads filtration sets generated by previous run. If a
		tuple of filenames, loads filtration sets from specified files.\n
		default: ``False``
	save_filts : bool or 2-tuple of str, optional
		If ``True``, saves the filtration sets such that ``load_filts=True``
		may	be used in subsequent runs. If a tuple of filenames, saves
		filtration sets to specified files.\n
		default: ``True``
	heatmaps: bool, optional
		If ``True``, plot pointwise stats to ``output/prfstats/heatmaps``.\n
		default: ``True``


	Returns
	-------
	array
		scaler statistics

	"""
	out_dir, out_filename = os.path.split(out_filename)
	in_dir, in_fname = os.path.split(traj.fname)


	weight_functions_figs(
		vary_param_1,
		vary_param_2,
		legend_labels_1,
		legend_labels_2,
		weight_func,
		filt_params,
		out_dir
	)


	filts = filt_set(
		traj,
		filt_params,
		vary_param_1,
		vary_param_2,
	    load=load_filts,
		save=save_filts,
	    quiet=quiet
	)

	prfs = prf_set(filts, weight_func, vary_param_1, vary_param_2)
	pointw_data = pointwise_stats(prfs, vary_param_1, vary_param_2)
	scaler_data = scaler_stats(prfs, pointw_data, vary_param_1, vary_param_2)

	variance_fig(
		scaler_data,
		filt_params,
		vary_param_1,
		vary_param_2,
		out_filename,
		legend_labels_1,
		legend_labels_2,
		traj.fname
	)
	if heatmaps:
		heatmaps_figs(
			pointw_data,
			vary_param_1,
			vary_param_2,
			legend_labels_1,
			legend_labels_2,
			out_dir,
			in_fname,
			annot_hm
		)

	dir_ = 'output/prfstats/samples'
	if clear_dir(dir_):
		plot_samples(filts, samples, dir_, vary_param_1, vary_param_2 )

	return scaler_data


def pairwise_mean_dists(
		traj,
		filt_params,
		vary_param_1,
		vary_param_2,
		weight_func=None,
		samples=False,
		quiet=True,
		load_filts=False,
		save_filts=True,
):
	"""

	Parameters
	----------
	traj: Trajectory
		Must be pre-windowed. This is accomplished by initializing with the
		 ``num_windows`` parameter, calling the ``slice`` method, or using
		 ``TimeSeries.embed()``.
	filt_params: dict
		See :py:func:`phomology.build_filtration.build_filtration`
	vary_param_1: tuple
		``(p, (val1, val2, val3, ...)`` where ``p`` is a string -- either
		``'weight_func'`` or any filtration parameter
		(see :py:func:`build_filtration`)
	vary_param_2: tuple, optional
		see `vary_param_1`
		default: ``None``
	weight_func: lambda, optional
		Weight function applied to all prfs before doing statistics\n
		default : ``None``
	samples: dict or int, optional
		If of the form ``{'interval': i, 'filt_step': j}``, plots persistence
		diagram, persistence rank function, and jrd step of filtration for
		every ith input file. If of the form ``{'interval': i}`` or simply
		``i``, plots persistence diagram, persistence rank function, and full
		filtration movie for every ith input file.\n
		These plots are saved to ``output/prfstats/samples/``\n
		default: ``False``
	load_filts : bool or 2-tuple of str, optional
		If ``True``, loads filtration sets generated by previous run. If a
		tuple of filenames, loads filtration sets from specified files.\n
		default: ``False``
	save_filts : bool or 2-tuple of str, optional
		If ``True``, saves the filtration sets such that ``load_filts=True``
		may	be used in subsequent runs. If a tuple of filenames, saves
		filtration sets to specified files.\n
		default: ``True``
	quiet: bool, optional
		less terminal output\n
		default: True
	Returns
	-------
	2-d array
		distances

	"""
	filts = filt_set(
		traj,
		filt_params,
		vary_param_1,
		vary_param_2,
		load=load_filts,
		save=save_filts,
		quiet=quiet,
	)

	prfs = prf_set(filts, weight_func, vary_param_1, vary_param_2)

	means = np.empty(prfs.shape[:-1], dtype=object)

	for idx in np.ndindex(*means.shape):
		mean = NormalPRF.mean(prfs[idx])
		means[idx] = mean

	dists = np.zeros((means.shape[0] - 1, means.shape[1]))
	for i in range(means.shape[0] - 1):
		for j in range(means.shape[1]):
			d = distance(means[i, j], means[i + 1, j])
			dists[i, j] = d

	dir_ = 'output/prfstats/samples'
	if clear_dir(dir_):
		plot_samples(filts, samples, dir_, vary_param_1, vary_param_2 )

	return dists
