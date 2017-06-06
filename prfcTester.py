import sys
import numpy as np
from config import default_filtration_params as parameter_set
from PRFCompare.PRF import PRF_dist_plot, mean_PRF_dist_plots



# test = int(sys.argv[1])
test = 5

if test == 1:
	params = parameter_set
	# params = standard_parameter_set
	params.update(
		{
			'ds_rate': 50,
			'worm_length': 5000,
			'max_filtration_param':.1,
			'num_divisions': 25,
			'use_cliques': True
		}
	)

	PRF_dist_plot(
		'datasets/embedded/test_cases', 		 # input directory
		'L63_x_m2_tau', 						 # input base filename
		'base i', 								 # input filename format: 'base i or 'i base'
		'output/PRFCompare/test_1.png', 		 # output filename
		params,

		i_ref=17,
		i_arr=np.arange(2, 40, 8),

		# weight_func= lambda i, j: np.power(np.e, .1 * (j - i)) 		# exponential k = .1
		weight_func=lambda i, j: .1 * (j - i),  						# linear, k = .1

		dist_scale='none',							# 'none', 'a', or 'a + b'
		PRF_res=20,  								# num divisions

		PD_movie_int=0,  							# interval to build filt movies and PDs. 0 means no PDs or movies.

	)







if test == 2:
	params = parameter_set
	# params = standard_parameter_set
	params.update(
		{
			'ds_rate': 50,
			'worm_length': 5000,
			'max_filtration_param': -1,
			'num_divisions': 30
		}
	)

	mean_PRF_dist_plots(
		'datasets/time_series/C134C/40-C134C.txt',  # input (left)
		'datasets/time_series/C135B/40-C135B.txt',  # input (right)
		'output/PRFCompare/40_C134C_vs_C135B.png',  # out filename
		params,
		crop_1=(1, 2),			# seconds or 'auto'
		crop_2=(1, 2),			# seconds or 'auto'
		auto_crop_length=.3,	# seconds. length of windows when crop is 'auto'

		window_size=.05, 		# seconds
		num_windows=10, 		# evenly spaced
		mean_samp_num=10,  		# number of windows to use for mean

		tau=.0012,		  		# seconds
		tau_T=np.pi,			# tau_T = tau / period
		note_index=40,			# required for auto tau

		PD_movie_int=0,  		# interval to build filt movies and PDs. 0 means no PDs or movies.


	)


if test == 3:
	params = parameter_set
	# params = standard_parameter_set
	params.update(
		{
			'ds_rate': 50,
			'worm_length': 5000,
			'max_filtration_param': -10,
			'num_divisions': 30,
			'use_cliques': True,

		}
	)

	mean_PRF_dist_plots(
		'datasets/time_series/C134C/40-C134C.txt',  # input (left)
		'datasets/time_series/C135B/40-C135B.txt',  # input (right)
		'output/PRFCompare/40_C134C_vs_C135B.png',  # out filename
		params,

		crop_1=(1, 1.3),			# seconds or 'auto'
		crop_2=(1, 1.3),			# seconds or 'auto'
		auto_crop_length=.3,		# seconds. length of windows when crop is 'auto'

		window_size=.1, 			# seconds
		num_windows=6, 				# evenly spaced
		mean_samp_num=5,  			# number of windows to use for mean

		tau='auto ideal',			# seconds or 'auto ideal' or 'auto detect'
		tau_T=np.pi,				# tau_T = tau / period
		note_index=40,				# required for auto tau
		PD_movie_int=0,  			# interval to build filt movies and PDs. 0 means no PDs or movies.

	)

if test == 4:
	params = parameter_set
	# params = standard_parameter_set
	params.update(
		{
			'ds_rate': 57,
			'worm_length': 5000,
			'max_filtration_param':-5,
			'num_divisions': 20,
			'use_cliques': True
		}
	)


	PRF_dist_plot(
		'datasets/embedded/test_cases',						# input directory
		'L63_x_m2_tau',										# input base filename
		'base i',											# input filename format: 'base i or 'i base'
		'output/PRFCompare/ref_PRFC/test4_L1.png',			# output filename
		params,

		i_ref=15,
		i_arr=np.arange(10, 20, 2),

		# weight_func= lambda i, j: np.power(np.e, .1 * (j - i)) 		# exponential, k = .1
		weight_func=lambda i, j: .1 * (j - i),  						# linear, k = .1

		metric='L1',								# 'L1' (abs) or 'L2' (euclidean)
		dist_scale='a + b', 						# 'none', 'a', or 'a + b'

		PRF_res=20,									# num divisions

		PD_movie_int=0,								# interval to build filt movies and PDs. 0 means no PDs or movies.

	)

if test == 5:
	params = parameter_set
	# params = standard_parameter_set
	params.update(
		{
			'ds_rate': 30,
			'max_filtration_param': -5,
			'num_divisions': 20,
			'use_cliques': True,

		}
	)

	mean_PRF_dist_plots(
		'datasets/time_series/C134C/49-C134C.txt',  # input (left)
		'datasets/time_series/C135B/49-C135B.txt',  # input (right)
		'output/PRFCompare/mean_PRFC/test_5.png',  		# out filename
		params,

		load_saved_filtrations=False,

		crop_1='auto',					# seconds or 'auto'
		crop_2='auto',					# seconds or 'auto'
		auto_crop_length=.5,			# seconds. length of windows when crop is 'auto'

		window_size=.05, 				# seconds
		num_windows=5, 					# evenly spaced
		mean_samp_num=5,  				# number of windows to use for mean

		tau_1='auto ideal',				# seconds or 'auto ideal' or 'auto detect'
		tau_2='auto ideal',
		tau_T=np.pi,					# tau_T = tau / period
		note_index=49,					# required for auto tau

		weight_func=lambda i, j: 1,		# no weighting (constant). see test 4 for other examples

		PRF_res=50,						# num divisions

		metric='L2', 					# 'L1' (abs) or 'L2' (euclidean)
		dist_scale='none',  			# 'none', 'a', 'b', or 'a + b'
										# a is magnitude of window PRF, b is magnitude of ref PRF

		normalize_volume=True,

		PD_movie_int=0,  				# interval to build filt movies and PDs. 0 means no PDs or movies.

	)


if test == 6:
	params = parameter_set
	# params = standard_parameter_set
	params.update(
		{
			'ds_rate': 50,
			'max_filtration_param': -10,
			'num_divisions': 20,
			'use_cliques': True,

		}
	)

	mean_PRF_dist_plots(
		'datasets/embedded/L63_x_m2/L63_x_m2_tau18.txt',
		'datasets/embedded/L63_x_m2/L63_x_m2_tau35.txt',
		'output/PRFCompare/mean_PRFC/L63_tau18v35_W1000dsr50.png',  		# out filename
		params,

		load_saved_filtrations=False,

		time_units='samples',

		crop_1=(100, 20100),					# time_units or 'auto'
		crop_2=(100, 20100),					# time_units or 'auto'

		window_size= 2000, 				# time_units
		num_windows=10, 					# evenly spaced
		mean_samp_num=5,  				# number of windows to use for mean


		weight_func=lambda i, j: 1,		# no weighting (constant). see test 4 for other examples

		PRF_res=50,						# num divisions

		metric='L2', 					# 'L1' (abs) or 'L2' (euclidean)
		dist_scale='none',  			# 'none', 'a', 'b', or 'a + b'
										# a is magnitude of window PRF, b is magnitude of ref PRF

		normalize_volume=True,

		PD_movie_int=5,  				# interval to build filt movies and PDs. 0 means no PDs or movies.

	)
	
if test == 7:
	params = parameter_set
	# params = standard_parameter_set
	params.update(
		{
			'worm_length': 2000,
			'ds_rate': 10,
			'max_filtration_param': -5,
			'num_divisions': 20,
			'use_cliques': True,

		}
	)

	mean_PRF_dist_plots(
		# 'datasets/time_series/C134C/49-C134C.txt',  # input (left)
		# 'datasets/time_series/C135B/49-C135B.txt',  # input (right)
		'datasets/embedded/L63_x_m2/L63_x_m2_tau18.txt',
		'datasets/embedded/L63_x_m2/L63_x_m2_tau30.txt',
		'output/PRFCompare/mean_PRFC/L63_x_m2_tau18_v_tau30.png',  		# out filename
		params,

		load_saved_filtrations=False,

		crop_1=(1, 2),					# seconds or 'auto'
		crop_2=(1, 2),					# seconds or 'auto'
		auto_crop_length=.5,			# seconds. length of windows when crop is 'auto'

		window_size=.05, 				# seconds
		num_windows=5, 					# evenly spaced
		mean_samp_num=10,  				# number of windows to use for mean

		tau_1=.001,						# seconds or 'auto ideal' or 'auto detect'
		tau_2=.001,

		weight_func=lambda i, j: 1,  # no weighting (constant). see test 4 for other examples

		PRF_res=50,						# num divisions

		metric='L2', 					# 'L1' (abs) or 'L2' (euclidean)
		dist_scale='none',  			# 'none', 'a', 'b', or 'a + b'
										# a is magnitude of window PRF, b is magnitude of ref PRF

		normalize_volume=True,

		PD_movie_int=0,  				# interval to build filt movies and PDs. 0 means no PDs or movies.

	)